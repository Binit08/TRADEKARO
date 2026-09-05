"""Trade Simulation and Order Models.

Simulates market execution, fills orders, applies slippage/commissions,
and tracks the lifecycle from Order -> Fill -> Position -> Trade.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Union


from app.data.market_event import MarketEvent
from app.execution.fees import FeeModel
from app.execution.order import Order
from app.execution.slippage import SlippageModel
from app.execution.trade import Trade
from app.signal.models import SignalType


class ExecutionEngine:
    """Historical execution engine with market, limit, and stop fills."""

    def __init__(
        self,
        qty: float = 100.0,
        fee_model: Optional[FeeModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        fee_rate: float = 0.0,
        fixed_fee: float = 0.0,
        min_fee: float = 0.0,
        slippage_bps: float = 0.0,
        multiplier: float = 1.0,
        margin: float = 0.0,
    ) -> None:
        self.qty = float(qty)
        self.fee_model = fee_model or FeeModel(rate=fee_rate, fixed=fixed_fee, min_fee=min_fee)
        self.slippage_model = slippage_model or SlippageModel(bps=slippage_bps)
        self.pending_orders: List[Order] = []
        self.trade_history: List[Trade] = []
        self.multiplier = float(multiplier)
        self.margin = float(margin)

    @staticmethod
    def _normalize_signal(signal: Union[str, SignalType]) -> SignalType:
        if isinstance(signal, SignalType):
            return signal
        return SignalType(str(signal).upper())

    def configure_costs(
        self,
        *,
        fee_rate: Optional[float] = None,
        fixed_fee: Optional[float] = None,
        min_fee: Optional[float] = None,
        slippage_bps: Optional[float] = None,
        volume_impact_bps_per_pct_adv: Optional[float] = None,
        multiplier: Optional[float] = None,
        margin: Optional[float] = None,
    ) -> None:
        """Update commission/slippage models for a run."""
        if fee_rate is not None or fixed_fee is not None or min_fee is not None:
            self.fee_model = FeeModel(
                rate=float(fee_rate if fee_rate is not None else self.fee_model.rate),
                fixed=float(fixed_fee if fixed_fee is not None else self.fee_model.fixed),
                min_fee=float(min_fee if min_fee is not None else self.fee_model.min_fee),
            )
        if slippage_bps is not None or volume_impact_bps_per_pct_adv is not None:
            current_bps = self.slippage_model.bps if slippage_bps is None else float(slippage_bps)
            current_impact = (
                getattr(self.slippage_model, "volume_impact_bps_per_pct_adv", 0.0)
                if volume_impact_bps_per_pct_adv is None
                else float(volume_impact_bps_per_pct_adv)
            )
            self.slippage_model = SlippageModel(bps=current_bps, volume_impact_bps_per_pct_adv=current_impact)
        
        if multiplier is not None:
            self.multiplier = float(multiplier)
        if margin is not None:
            self.margin = float(margin)

    def submit_order(
        self,
        *,
        signal: Union[str, SignalType],
        candle: MarketEvent,
        qty: Optional[float] = None,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        intent: str = "ENTRY",
        reason: Optional[str] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[Order]:
        """Create a pending order from a signal at signal-candle time."""
        normalized = self._normalize_signal(signal)
        if normalized == SignalType.HOLD:
            return None

        order = Order(
            signal=normalized.value,
            created_time=candle.timestamp,
            symbol=candle.symbol,
            qty=float(qty) if qty is not None else None,
            order_type=str(order_type).upper(),
            limit_price=float(limit_price) if limit_price is not None else None,
            stop_price=float(stop_price) if stop_price is not None else None,
            intent=str(intent).upper(),
            reason=reason,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="PENDING",
        )
        self.pending_orders.append(order)
        return order

    def submit_signal(self, signal: Union[str, SignalType], candle: MarketEvent, **kwargs) -> Optional[Order]:
        """Backward-compatible signal submission helper."""
        return self.submit_order(signal=signal, candle=candle, **kwargs)

    def _reference_price(self, order: Order, candle: MarketEvent) -> Optional[float]:
        """Return the pre-slippage fill price if this order is triggered."""
        order_type = str(order.order_type).upper()
        side = str(order.signal).upper()

        if order_type == "MARKET":
            return float(candle.open)

        if order_type == "LIMIT":
            if order.limit_price is None:
                return None
            limit_price = float(order.limit_price)
            if side == SignalType.BUY.value and float(candle.low) <= limit_price:
                return limit_price
            if side == SignalType.SELL.value and float(candle.high) >= limit_price:
                return limit_price
            return None

        if order_type == "STOP":
            if order.stop_price is None:
                return None
            stop_price = float(order.stop_price)
            if side == SignalType.BUY.value and float(candle.high) >= stop_price:
                return max(stop_price, float(candle.open))
            if side == SignalType.SELL.value and float(candle.low) <= stop_price:
                return min(stop_price, float(candle.open))
            return None

        raise ValueError(f"Unknown order type: {order.order_type}")

    def create_fill(
        self,
        *,
        symbol: str,
        side: str,
        reference_price: float,
        timestamp,
        qty: Optional[float] = None,
        volume: Optional[float] = None,
        order_type: str = "MARKET",
        intent: str = "ENTRY",
        reason: Optional[str] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_created_time: Optional[datetime] = None,
    ) -> Trade:
        """Create an executed fill with slippage and commission applied."""
        fill_qty = float(qty if qty is not None else self.qty)
        fill_price = self.slippage_model.apply(float(reference_price), side, volume=volume, qty=fill_qty)
        notional = fill_price * fill_qty
        fee = self.fee_model.calculate(notional=notional, qty=fill_qty, price=fill_price)
        slippage_cost = self.slippage_model.cost(reference_price, fill_price, fill_qty)

        trade = Trade(
            symbol=symbol,
            side=str(side).upper(),
            entry_price=fill_price,
            qty=fill_qty,
            entry_time=timestamp,
            status="OPEN",
            fees=fee,
            slippage=slippage_cost,
            order_type=str(order_type).upper(),
            intent=str(intent).upper(),
            entry_reason=reason,
            stop_loss=stop_loss,
            take_profit=take_profit,
            order_created_time=order_created_time,
            multiplier=self.multiplier,
            margin=self.margin,
        )
        return trade

    def execute(self, next_candle: MarketEvent) -> Optional[Trade]:
        """Execute the oldest fillable pending order for this candle."""
        if not self.pending_orders:
            return None

        for order in list(self.pending_orders):
            if order.symbol != next_candle.symbol:
                continue
            # Guard: any order created during candle t may only fill on candle t+1 or later
            if not (next_candle.timestamp > order.created_time):
                continue

            reference_price = self._reference_price(order, next_candle)
            if reference_price is None:
                continue

            self.pending_orders.remove(order)
            order.status = "FILLED"
            fill = self.create_fill(
                symbol=next_candle.symbol,
                side=order.signal,
                reference_price=reference_price,
                timestamp=next_candle.timestamp,
                qty=order.qty,
                volume=getattr(next_candle, "volume", None),
                order_type=order.order_type,
                intent=order.intent,
                reason=order.reason,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit,
                order_created_time=order.created_time,
            )
            self.trade_history.append(fill)
            return fill

        return None

    def execute_all(self, next_candle: MarketEvent) -> List[Trade]:
        """Execute every fillable pending order for this candle."""
        fills: List[Trade] = []
        orders_to_fill = []

        # Snapshot pass: identify triggered orders
        for order in list(self.pending_orders):
            if order.symbol != next_candle.symbol:
                continue
            # Guard: any order created during candle t may only fill on candle t+1 or later
            if not (next_candle.timestamp > order.created_time):
                continue

            reference_price = self._reference_price(order, next_candle)
            if reference_price is not None:
                orders_to_fill.append((order, reference_price))

        # Execution pass
        for order, reference_price in orders_to_fill:
            if order in self.pending_orders:
                self.pending_orders.remove(order)
                order.status = "FILLED"
                fill = self.create_fill(
                    symbol=next_candle.symbol,
                    side=order.signal,
                    reference_price=reference_price,
                    timestamp=next_candle.timestamp,
                    qty=order.qty,
                    volume=getattr(next_candle, "volume", None),
                    order_type=order.order_type,
                    intent=order.intent,
                    reason=order.reason,
                    stop_loss=order.stop_loss,
                    take_profit=order.take_profit,
                    order_created_time=order.created_time,
                )
                self.trade_history.append(fill)
                fills.append(fill)

        return fills

    def execute_market_orders_at_close(self, candle: MarketEvent) -> List[Trade]:
        """Execute any pending MARKET orders that were created precisely at this candle's timestamp.
        Fills them at the candle's close price, completely bypassing the next-candle rule.
        """
        fills: List[Trade] = []
        orders_to_fill = []

        # Snapshot pass: identify market orders created strictly on this candle
        for order in list(self.pending_orders):
            if order.symbol != candle.symbol:
                continue
            if order.created_time != candle.timestamp:
                continue
            if str(order.order_type).upper() != "MARKET":
                continue

            reference_price = float(candle.close)
            orders_to_fill.append((order, reference_price))

        # Execution pass
        for order, reference_price in orders_to_fill:
            if order in self.pending_orders:
                self.pending_orders.remove(order)
                order.status = "FILLED"
                fill = self.create_fill(
                    symbol=candle.symbol,
                    side=order.signal,
                    reference_price=reference_price,
                    timestamp=candle.timestamp,
                    qty=order.qty,
                    volume=getattr(candle, "volume", None),
                    order_type=order.order_type,
                    intent=order.intent,
                    reason=order.reason,
                    stop_loss=order.stop_loss,
                    take_profit=order.take_profit,
                    order_created_time=order.created_time,
                )
                self.trade_history.append(fill)
                fills.append(fill)

        return fills

    def get_trade_history(self) -> List[Trade]:
        """Return executed fills."""
        return list(self.trade_history)

    def reset(self) -> None:
        """Clear all pending orders and fill history."""
        self.pending_orders.clear()
        self.trade_history.clear()
