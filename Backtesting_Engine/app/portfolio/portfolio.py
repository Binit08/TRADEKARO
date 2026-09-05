"""Portfolio engine for production-oriented historical backtesting.

The portfolio consumes executed `Trade` objects and market candles to track:
- cash
- equity
- realized/unrealized PnL
- drawdown
- open/closed position counts

Constraints for V1:
- no margin interest / borrow fees
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.data.market_event import MarketEvent
from app.execution.trade import Trade
from app.portfolio.position import Position
from app.portfolio.state import PortfolioState


class Portfolio:
    """Portfolio accounting engine.

    Example:
        trade = Trade(symbol="RELIANCE", side="BUY", entry_price=104, qty=100, entry_time=...)
        portfolio = Portfolio(initial_cash=100000)
        portfolio.open_position(trade)
        portfolio.mark_to_market(candle)
        print(portfolio.summary())
    """

    def __init__(self, initial_cash: float = 100000, short_margin_pct: float = 0.5) -> None:
        self.initial_cash = float(initial_cash)
        self._initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.collateral: float = 0.0
        self.short_margin_pct = float(short_margin_pct)
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.fill_history: List[Trade] = []
        self.equity_history: List[float] = []
        self.equity_timestamps: List[Optional[datetime]] = []
        self.cash_history: List[float] = []

        self.realized_pnl: float = 0.0
        self.unrealized_pnl: float = 0.0
        self.fees_paid: float = 0.0
        self.closed_positions: int = 0

        self._max_equity: float = self.initial_cash
        self._drawdown: float = 0.0

    def reset(self) -> None:
        """Reset portfolio accounting to initial cash and no positions."""
        self.cash = self._initial_cash
        self.collateral = 0.0
        self.positions.clear()
        self.trade_history.clear()
        self.fill_history.clear()
        self.equity_history = []
        self.equity_timestamps = []
        self.cash_history = []
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.fees_paid = 0.0
        self.closed_positions = 0
        self._max_equity = self._initial_cash
        self._drawdown = 0.0
    def _recalc_unrealized(self) -> float:
        """Recalculate aggregate unrealized PnL from open positions."""
        total = 0.0
        for position in self.positions.values():
            if position.side.upper() == "SHORT":
                total += (position.entry_price - position.current_price) * position.qty * position.multiplier
            else:
                total += (position.current_price - position.entry_price) * position.qty * position.multiplier
        self.unrealized_pnl = total
        return self.unrealized_pnl

    def _recalc_equity(self, timestamp: Optional[datetime] = None) -> float:
        """Recalculate total equity.

        We use the following accounting convention:
        equity = cash + collateral + sum(LONG_position.current_price * LONG_position.qty)
                 - sum(SHORT_position.current_price * SHORT_position.qty)
        """
        position_value = 0.0
        for position in self.positions.values():
            if position.side.upper() == "SHORT":
                signed_value = - (position.current_price * position.qty * position.multiplier)
            else:
                signed_value = position.current_price * position.qty * position.multiplier
            position_value += signed_value
            
            # If it's a futures contract (margin > 0), the position value does not add its full notional to equity.
            # Instead, equity = cash + collateral + unrealized_pnl.
            # For backward compatibility with the existing formula, we subtract the notional value if it's a future
            # so that only the PnL is reflected, since `collateral` holds the margin.
            if position.margin > 0:
                position_value -= signed_value
                position_value += position.unrealized_pnl

        equity = self.cash + self.collateral + position_value

        if timestamp is not None and self.equity_timestamps and self.equity_timestamps[-1] == timestamp:
            self.equity_history[-1] = float(equity)
            self.cash_history[-1] = float(self.cash)
        else:
            self.equity_history.append(float(equity))
            self.equity_timestamps.append(timestamp)
            self.cash_history.append(float(self.cash))
        if equity > self._max_equity:
            self._max_equity = equity

        # drawdown in percent from historical max equity
        if self._max_equity > 0:
            self._drawdown = ((self._max_equity - equity) / self._max_equity) * 100.0
        else:
            self._drawdown = 0.0

        return float(equity)


    def open_position(self, trade: Trade) -> Position:
        """Open or add to a long/short position from an entry fill."""
        entry_side = trade.side.upper()
        if entry_side not in {"BUY", "SELL"}:
            raise ValueError("Position entry side must be BUY or SELL")

        qty = float(trade.qty)
        if qty <= 0:
            raise ValueError("Position quantity must be positive")

        position_side = "LONG" if entry_side == "BUY" else "SHORT"
        multiplier = getattr(trade, "multiplier", 1.0)
        margin_per_lot = getattr(trade, "margin", 0.0)
        notional = float(trade.entry_price) * qty * multiplier
        entry_fee = float(getattr(trade, "fees", 0.0) or 0.0)

        if margin_per_lot > 0:
            # Futures trading logic
            margin_requirement = margin_per_lot * qty
            total_cost = margin_requirement + entry_fee
            if total_cost > self.cash:
                raise ValueError("Insufficient cash for margin requirement")
            self.cash -= total_cost
            self.collateral += margin_requirement
        else:
            # Equity trading logic
            if position_side == "LONG":
                total_cost = notional + entry_fee
                if total_cost > self.cash:
                    raise ValueError("Insufficient cash to open long position")
                self.cash -= total_cost
            else:
                margin_requirement = notional * float(self.short_margin_pct)
                if margin_requirement > self.cash:
                    raise ValueError("Insufficient collateral to open short position")
                self.cash -= margin_requirement + entry_fee
                self.collateral += margin_requirement + notional


        self.fees_paid += entry_fee
        self.fill_history.append(trade)

        existing = self.positions.get(trade.symbol)
        if existing is not None:
            if existing.side != position_side:
                raise ValueError("Cannot add to a position in the opposite direction")

            total_qty = existing.qty + qty
            existing.entry_price = ((existing.entry_price * existing.qty) + (float(trade.entry_price) * qty)) / total_qty
            existing.qty = total_qty
            existing.current_price = float(trade.entry_price)
            existing.entry_fee += entry_fee
            existing.entries += 1
            existing.stop_loss = trade.stop_loss if trade.stop_loss is not None else existing.stop_loss
            existing.take_profit = trade.take_profit if trade.take_profit is not None else existing.take_profit

            add_on_trade = Trade(
                symbol=trade.symbol,
                side=entry_side,
                entry_price=float(trade.entry_price),
                qty=qty,
                entry_time=trade.entry_time,
                status="OPEN",
                fees=entry_fee,
                entry_fee=entry_fee,
                slippage=float(getattr(trade, "slippage", 0.0) or 0.0),
                order_type=getattr(trade, "order_type", "MARKET"),
                intent="ENTRY",
                position_side=position_side,
                entry_reason=getattr(trade, "entry_reason", None),
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit,
                lifecycle_first_entry_price=float(existing.lifecycle_first_entry_price),
                first_entry_time=existing.first_entry_time,
                original_entry_price=float(trade.entry_price),
                order_created_time=getattr(trade, "order_created_time", None),
            )
            self.trade_history.append(add_on_trade)
            existing.trade_indices.append(len(self.trade_history) - 1)

            self._recalc_unrealized()
            return existing

        lifecycle_trade = Trade(
            symbol=trade.symbol,
            side=entry_side,
            entry_price=float(trade.entry_price),
            qty=qty,
            entry_time=trade.entry_time,
            status="OPEN",
            fees=entry_fee,
            entry_fee=entry_fee,
            slippage=float(getattr(trade, "slippage", 0.0) or 0.0),
            order_type=getattr(trade, "order_type", "MARKET"),
            intent="ENTRY",
            position_side=position_side,
            entry_reason=getattr(trade, "entry_reason", None),
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            lifecycle_first_entry_price=float(trade.entry_price),
            first_entry_time=trade.entry_time,
            original_entry_price=float(trade.entry_price),
            order_created_time=getattr(trade, "order_created_time", None),
        )
        self.trade_history.append(lifecycle_trade)

        position = Position(
            symbol=trade.symbol,
            qty=qty,
            entry_price=float(trade.entry_price),
            entry_time=trade.entry_time,
            current_price=float(trade.entry_price),
            unrealized_pnl=0.0,
            side=position_side,
            entry_fee=entry_fee,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            entry_reason=getattr(trade, "entry_reason", None),
            trade_index=len(self.trade_history) - 1,
            trade_indices=[len(self.trade_history) - 1],
            status="OPEN",
            lifecycle_first_entry_price=float(trade.entry_price),
            first_entry_time=trade.entry_time,
            multiplier=multiplier,
            margin=margin_per_lot,
        )
        self.positions[trade.symbol] = position

        self._recalc_unrealized()
        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_time: datetime,
        exit_fee: float = 0.0,
        exit_reason: str | None = None,
        exit_order_type: str | None = None,
        slippage: float = 0.0,
    ) -> Trade:
        """Close an existing position and realize PnL."""
        if symbol not in self.positions:
            raise ValueError("No open position for symbol")

        position = self.positions[symbol]
        exit_price = float(exit_price)
        exit_fee = float(exit_fee or 0.0)

        if position.margin > 0:
            # Futures closing logic
            if position.side.upper() == "SHORT":
                gross_pnl = (position.entry_price - exit_price) * position.qty * position.multiplier
            else:
                gross_pnl = (exit_price - position.entry_price) * position.qty * position.multiplier
            
            margin_released = position.margin * position.qty
            self.positions.pop(symbol)
            self.collateral -= margin_released
            self.cash += margin_released + gross_pnl - exit_fee
        else:
            # Equity closing logic
            if position.side.upper() == "SHORT":
                gross_pnl = (position.entry_price - exit_price) * position.qty * position.multiplier
                cover_cost = exit_price * position.qty * position.multiplier
                if cover_cost + exit_fee > self.cash + self.collateral:
                    raise ValueError("Insufficient cash or collateral to close short position")
                
                margin_released = (position.entry_price * position.qty * position.multiplier) * float(self.short_margin_pct)
                notional_released = position.entry_price * position.qty * position.multiplier
                total_collateral_released = margin_released + notional_released
                
                self.positions.pop(symbol)
                self.collateral -= total_collateral_released
                self.cash += total_collateral_released - cover_cost - exit_fee
            else:
                gross_pnl = (exit_price - position.entry_price) * position.qty * position.multiplier
                proceeds = exit_price * position.qty * position.multiplier
                self.positions.pop(symbol)
                self.cash += proceeds - exit_fee

        total_fees = float(position.entry_fee) + exit_fee
        realized = gross_pnl - total_fees
        self.realized_pnl += realized
        self.fees_paid += exit_fee

        if position.trade_indices:
            # We distribute the exit PnL and exit fee proportionally to each entry fill
            for idx in position.trade_indices:
                trade = self.trade_history[idx]
                trade_weight = trade.qty / position.qty
                trade.exit_price = exit_price
                trade.exit_time = exit_time
                
                if position.side.upper() == "SHORT":
                    trade_gross_pnl = (trade.entry_price - exit_price) * trade.qty * position.multiplier
                else:
                    trade_gross_pnl = (exit_price - trade.entry_price) * trade.qty * position.multiplier
                    
                trade_exit_fee = exit_fee * trade_weight
                
                trade.gross_pnl = trade_gross_pnl
                trade.status = "CLOSED"
                trade.exit_fee = trade_exit_fee
                trade.fees = trade.entry_fee + trade_exit_fee
                trade.slippage += float(slippage or 0.0) * trade_weight
                trade.pnl = trade_gross_pnl - trade.fees
                trade.exit_reason = exit_reason
                trade.exit_order_type = exit_order_type
                
            trade = self.trade_history[position.trade_indices[-1]] # Return the last closed trade object to fulfill the return signature
        else:
            trade = Trade(
                symbol=symbol,
                side="SELL" if position.side.upper() == "SHORT" else "BUY",
                entry_price=position.entry_price,
                qty=position.qty,
                entry_time=position.entry_time,
                exit_price=exit_price,
                exit_time=exit_time,
                status="CLOSED",
                # Note: trade.fees represents total round-trip fees (entry_fee + exit_fee)
                fees=total_fees,
                entry_fee=float(position.entry_fee),
                exit_fee=exit_fee,
                pnl=realized,
                position_side=position.side,
                exit_reason=exit_reason,
                exit_order_type=exit_order_type,
                lifecycle_first_entry_price=position.lifecycle_first_entry_price,
                first_entry_time=position.first_entry_time,
                original_entry_price=position.lifecycle_first_entry_price,
            )
            self.trade_history.append(trade)

        self.closed_positions += 1

        self._recalc_unrealized()
        return trade

    def mark_to_market(self, candle: MarketEvent) -> None:
        """Mark open position(s) to current candle close price.

        Updates current price, unrealized PnL, and equity.
        """
        position = self.positions.get(candle.symbol)
        if position is not None:
            position.current_price = float(candle.close)
            if position.side.upper() == "SHORT":
                position.unrealized_pnl = (position.entry_price - position.current_price) * position.qty * position.multiplier
            else:
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.qty * position.multiplier

        self._recalc_unrealized()
        self._recalc_equity(candle.timestamp)

    def get_equity(self) -> float:
        """Return latest portfolio equity."""
        if not self.equity_history:
            return float(self.cash)
        return float(self.equity_history[-1])

    def get_cash(self) -> float:
        """Return available cash."""
        return float(self.cash)

    def get_unrealized_pnl(self) -> float:
        """Return aggregate unrealized PnL."""
        return float(self.unrealized_pnl)

    def get_realized_pnl(self) -> float:
        """Return aggregate realized PnL."""
        return float(self.realized_pnl)

    def get_drawdown(self) -> float:
        """Return current drawdown percentage from max equity."""
        return float(self._drawdown)

    def state(self) -> PortfolioState:
        """Return a typed snapshot of current portfolio state."""
        return PortfolioState(
            cash=self.get_cash(),
            equity=self.get_equity(),
            realized_pnl=self.get_realized_pnl(),
            unrealized_pnl=self.get_unrealized_pnl(),
            drawdown=self.get_drawdown(),
            open_positions=len(self.positions),
            closed_positions=self.closed_positions,
        )

    def summary(self) -> Dict[str, float | int]:
        """Return dict summary used by reports and tests."""
        s = self.state()
        return {
            "cash": s.cash,
            "equity": s.equity,
            "realized_pnl": s.realized_pnl,
            "unrealized_pnl": s.unrealized_pnl,
            "fees_paid": self.fees_paid,
            "drawdown": s.drawdown,
            "positions": s.open_positions,
            "closed_positions": self.closed_positions,
        }

    def equity_curve(self) -> List[Dict[str, float | int | datetime | None]]:
        """Return timestamped equity curve records."""
        curve = []
        running_max = self.initial_cash
        for idx, equity in enumerate(self.equity_history):
            if equity > running_max:
                running_max = equity
            dd_pct = ((running_max - equity) / running_max) * 100.0 if running_max > 0 else 0.0
            
            curve.append({
                "step": idx,
                "timestamp": self.equity_timestamps[idx] if idx < len(self.equity_timestamps) else None,
                "equity": float(equity),
                "cash": self.cash_history[idx] if idx < len(self.cash_history) else self.cash,
                "drawdown_pct": float(dd_pct),
            })
        return curve
