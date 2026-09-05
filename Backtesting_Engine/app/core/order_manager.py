from typing import Dict, Any, Optional
import logging
from app.config.settings import StrategySettings
from app.execution.simulator import ExecutionEngine
from app.portfolio.portfolio import Portfolio
from app.execution.trade import Trade
from app.data.market_event import MarketEvent
from app.risk.position import PositionSizer
from app.signal.models import SignalType
from app.risk.stoploss import evaluate_protective_exit

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self, execution: ExecutionEngine, portfolios: Dict[str, Portfolio], run_warnings: list):
        self.execution = execution
        self.portfolios = portfolios
        self.run_warnings = run_warnings

    @staticmethod
    def _normalize_pct(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        pct = float(value)
        if pct < 0.0 or pct > 1.0:
            raise ValueError("Percentage values must be in the range [0.0, 1.0]")
        return pct

    def apply_protective_levels(self, fill: Trade, settings: StrategySettings) -> None:
        if fill.intent != "ENTRY":
            return
        side = fill.side.upper()
        entry = float(fill.entry_price)
        stop_pct = self._normalize_pct(settings.stop_loss_pct)
        target_pct = self._normalize_pct(settings.take_profit_pct)
        if fill.stop_loss is None:
            if settings.stop_loss_price is not None:
                fill.stop_loss = float(settings.stop_loss_price)
            elif stop_pct is not None:
                fill.stop_loss = entry * (1.0 - stop_pct) if side == "BUY" else entry * (1.0 + stop_pct)
        if fill.take_profit is None:
            if settings.take_profit_price is not None:
                fill.take_profit = float(settings.take_profit_price)
            elif target_pct is not None:
                fill.take_profit = entry * (1.0 + target_pct) if side == "BUY" else entry * (1.0 - target_pct)

    def process_fill(self, fill: Trade, settings: StrategySettings, candle: Optional[MarketEvent] = None) -> Optional[Trade]:
        protective_fill = None
        if fill.intent == "EXIT":
            try:
                self.portfolios[fill.symbol].close_position(
                    symbol=fill.symbol,
                    exit_price=fill.entry_price,
                    exit_time=fill.entry_time,
                    exit_fee=float(getattr(fill, "fees", 0.0) or 0.0),
                    exit_reason=fill.entry_reason,
                    exit_order_type=fill.order_type,
                    slippage=float(getattr(fill, "slippage", 0.0) or 0.0),
                )
            except ValueError as e:
                position = self.portfolios[fill.symbol].positions.get(fill.symbol)
                pos_str = str(position) if position is not None else "None"
                logger.error("Close position failed: symbol=%s error=%s position_state=%s", fill.symbol, str(e), pos_str)
                self.run_warnings.append(f"Failed to close position for {fill.symbol} due to insufficient capital/collateral: {str(e)}. Position remains open.")
                raise
        else:
            self.apply_protective_levels(fill, settings)
            try:
                self.portfolios[fill.symbol].open_position(fill)
            except ValueError:
                fill.status = "REJECTED"
                try:
                    self.execution.trade_history.remove(fill)
                except ValueError:
                    pass
                raise
            if candle is not None:
                protective_fill = self.process_protective_exit(candle, settings)
        return protective_fill

    def process_protective_exit(self, candle: MarketEvent, settings: StrategySettings) -> Optional[Trade]:
        if candle.symbol not in self.portfolios:
            return None
        position = self.portfolios[candle.symbol].positions.get(candle.symbol)
        if position is None:
            return None
        assume_sl_wins = getattr(settings, "assume_sl_wins", True)
        exit_request = evaluate_protective_exit(position, candle, assume_sl_wins=assume_sl_wins)
        if exit_request is None:
            return None
        fill = self.execution.create_fill(
            symbol=candle.symbol,
            side=exit_request.side,
            reference_price=exit_request.price,
            timestamp=candle.timestamp,
            qty=position.qty,
            order_type=exit_request.order_type,
            intent="EXIT",
            reason=exit_request.reason,
            order_created_time=position.entry_time,
        )
        self.process_fill(fill, settings)
        return fill

    def _can_pyramid(self, symbol: str, side: SignalType, settings: StrategySettings) -> bool:
        if symbol not in self.portfolios:
            return True
        position = self.portfolios[symbol].positions.get(symbol)
        if position is None:
            return True
        position_side = "LONG" if side.value == SignalType.BUY.value else "SHORT"
        if position.side != position_side:
            return False
        return position.entries < int(settings.pyramiding)

    def _submit_entry(self, side: SignalType, candle: MarketEvent, settings: StrategySettings, reason: str) -> None:
        reference_price = float(candle.close)
        if candle.symbol not in self.portfolios:
            return
        position = self.portfolios[candle.symbol].positions.get(candle.symbol)
        existing_qty = position.qty if position is not None and position.side == ("LONG" if side.value == SignalType.BUY.value else "SHORT") else 0.0
        pyramid_index = position.entries if position else 0
        total_layers = int(settings.pyramiding) + 1
        sizer = PositionSizer(
            mode=settings.position_size_type,
            value=settings.position_size,
            commission_rate=settings.commission_rate or 0.0,
            lot_size=getattr(settings, "lot_size", 1.0),
        )
        qty = sizer.size(
            default_qty=self.execution.qty,
            cash=self.portfolios[candle.symbol].get_cash(),
            equity=self.portfolios[candle.symbol].get_equity(),
            price=reference_price,
            existing_qty=existing_qty,
            pyramid_index=pyramid_index,
            total_layers=total_layers,
        )
        if qty <= 0:
            return
        self.execution.submit_order(
            signal=side,
            candle=candle,
            qty=qty,
            order_type=settings.order_type,
            limit_price=settings.limit_price,
            stop_price=settings.stop_price,
            intent="ENTRY",
            reason=reason,
        )

    def _submit_exit(self, side: SignalType, candle: MarketEvent, settings: StrategySettings, reason: str) -> None:
        if candle.symbol not in self.portfolios:
            return
        position = self.portfolios[candle.symbol].positions.get(candle.symbol)
        if position is None:
            return
        self.execution.submit_order(
            signal=side,
            candle=candle,
            qty=position.qty,
            order_type=settings.order_type,
            limit_price=settings.limit_price,
            stop_price=settings.stop_price,
            intent="EXIT",
            reason=reason,
        )

    def submit_signal_order(self, signal_result: Any, candle: MarketEvent, settings: StrategySettings) -> None:
        from app.signal.models import SignalType, SignalResult
        
        if isinstance(signal_result, SignalResult):
            signal = signal_result.signal
            intent = signal_result.reason.get("intent") if signal_result.reason else None
        else:
            signal = signal_result
            intent = None

        if signal == SignalType.HOLD:
            return
        if candle.symbol not in self.portfolios:
            return
        position = self.portfolios[candle.symbol].positions.get(candle.symbol)
        
        if intent == "ENTRY":
            if signal == SignalType.BUY:
                if position is None:
                    self._submit_entry(signal, candle, settings, "BUY_SIGNAL")
                elif position.side == "SHORT" and settings.close_on_opposite_signal:
                    self._submit_exit(signal, candle, settings, "SHORT_EXIT_SIGNAL")
                    self._submit_entry(signal, candle, settings, "BUY_SIGNAL")
                elif position.side == "LONG" and self._can_pyramid(candle.symbol, SignalType.BUY, settings):
                    self._submit_entry(signal, candle, settings, "PYRAMID_BUY")
            elif signal == SignalType.SELL:
                if position is None:
                    if settings.allow_short:
                        self._submit_entry(signal, candle, settings, "SHORT_SIGNAL")
                elif position.side == "LONG" and settings.close_on_opposite_signal:
                    self._submit_exit(signal, candle, settings, "LONG_EXIT_SIGNAL")
                    if settings.allow_short:
                        self._submit_entry(signal, candle, settings, "SHORT_SIGNAL")
                elif position.side == "SHORT" and self._can_pyramid(candle.symbol, SignalType.SELL, settings):
                    self._submit_entry(signal, candle, settings, "PYRAMID_SELL")
            return
            
        if intent == "EXIT":
            if signal == SignalType.SELL and position is not None and position.side == "LONG":
                self._submit_exit(signal, candle, settings, "LONG_EXIT_SIGNAL")
            elif signal == SignalType.BUY and position is not None and position.side == "SHORT":
                self._submit_exit(signal, candle, settings, "SHORT_EXIT_SIGNAL")
            return
            
        # Legacy fallback
        if signal == SignalType.BUY:
            if position is None:
                self._submit_entry(signal, candle, settings, "BUY_SIGNAL")
                return
            if position.side == "SHORT" and settings.close_on_opposite_signal:
                self._submit_exit(signal, candle, settings, "SHORT_EXIT_SIGNAL")
                self._submit_entry(signal, candle, settings, "BUY_SIGNAL")
                return
            if position.side == "LONG" and self._can_pyramid(candle.symbol, SignalType.BUY, settings):
                self._submit_entry(signal, candle, settings, "PYRAMID_BUY")
            return
        if signal == SignalType.SELL:
            if position is None:
                if settings.allow_short:
                    self._submit_entry(signal, candle, settings, "SHORT_SIGNAL")
                return
            if position.side == "LONG" and settings.close_on_opposite_signal:
                self._submit_exit(signal, candle, settings, "LONG_EXIT_SIGNAL")
                if settings.allow_short:
                    self._submit_entry(signal, candle, settings, "SHORT_SIGNAL")
                return
            if position.side == "SHORT" and self._can_pyramid(candle.symbol, SignalType.SELL, settings):
                self._submit_entry(signal, candle, settings, "PYRAMID_SELL")
