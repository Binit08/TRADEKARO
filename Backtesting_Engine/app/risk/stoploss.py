"""Protective stop-loss and take-profit logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.data.market_event import MarketEvent
from app.portfolio.position import Position


@dataclass(frozen=True)
class ProtectiveExit:
    """A generated exit fill request from a protective level."""

    side: str
    price: float
    reason: str
    order_type: str


def evaluate_protective_exit(
    position: Position, candle: MarketEvent, assume_sl_wins: bool = True
) -> Optional[ProtectiveExit]:
    """Return a stop-loss/take-profit exit when the candle touches a level.

    If both stop-loss (SL) and take-profit (TP) levels are touched in one candle:
    - If assume_sl_wins is True, the stop-loss wins (conservative/worst-case assumption).
    - If assume_sl_wins is False, the take-profit wins.
    This is parameterized so that users can opt for the worst-case fill assumption (SL wins).
    """
    side = str(position.side).upper()
    stop = position.stop_loss
    target = position.take_profit

    if side == "LONG":
        stop_touched = stop is not None and float(candle.low) <= float(stop)
        target_touched = target is not None and float(candle.high) >= float(target)

        if stop_touched and target_touched:
            if assume_sl_wins:
                price = float(candle.open) if float(candle.open) <= float(stop) else float(stop)
                return ProtectiveExit(side="SELL", price=price, reason="STOP_LOSS", order_type="STOP")
            else:
                price = float(candle.open) if float(candle.open) >= float(target) else float(target)
                return ProtectiveExit(side="SELL", price=price, reason="TAKE_PROFIT", order_type="LIMIT")

        if stop_touched:
            price = float(candle.open) if float(candle.open) <= float(stop) else float(stop)
            return ProtectiveExit(side="SELL", price=price, reason="STOP_LOSS", order_type="STOP")

        if target_touched:
            price = float(candle.open) if float(candle.open) >= float(target) else float(target)
            return ProtectiveExit(side="SELL", price=price, reason="TAKE_PROFIT", order_type="LIMIT")

    if side == "SHORT":
        stop_touched = stop is not None and float(candle.high) >= float(stop)
        target_touched = target is not None and float(candle.low) <= float(target)

        if stop_touched and target_touched:
            if assume_sl_wins:
                price = float(candle.open) if float(candle.open) >= float(stop) else float(stop)
                return ProtectiveExit(side="BUY", price=price, reason="STOP_LOSS", order_type="STOP")
            else:
                price = float(candle.open) if float(candle.open) <= float(target) else float(target)
                return ProtectiveExit(side="BUY", price=price, reason="TAKE_PROFIT", order_type="LIMIT")

        if stop_touched:
            price = float(candle.open) if float(candle.open) >= float(stop) else float(stop)
            return ProtectiveExit(side="BUY", price=price, reason="STOP_LOSS", order_type="STOP")

        if target_touched:
            price = float(candle.open) if float(candle.open) <= float(target) else float(target)
            return ProtectiveExit(side="BUY", price=price, reason="TAKE_PROFIT", order_type="LIMIT")

    return None

