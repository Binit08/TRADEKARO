"""Slippage calculations for simulated order fills."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional



@dataclass(frozen=True)
class SlippageModel:
    """Apply basis-point slippage to a fill price, incorporating fixed bps and volume impact.

    Positive slippage bps makes buys fill above the reference price and sells
    fill below it.
    """

    bps: float = 0.0
    volume_impact_bps_per_pct_adv: float = 0.0

    def apply(self, price: float, side: str, volume: Optional[float] = None, qty: float = 0.0) -> float:
        """Return a side-aware slipped fill price."""
        price = float(price)
        pct_adv = 0.0
        if volume is not None and volume > 0.0:
            pct_adv = (abs(qty) / float(volume)) * 100.0

        factor = (abs(float(self.bps)) + abs(float(self.volume_impact_bps_per_pct_adv)) * pct_adv) / 10_000.0
        normalized_side = str(side).upper()

        if normalized_side == "BUY":
            return price * (1.0 + factor)
        if normalized_side == "SELL":
            return price * (1.0 - factor)
        return price

    def cost(self, reference_price: float, fill_price: float, qty: float) -> float:
        """Return absolute slippage cost for a fill."""
        return abs(float(fill_price) - float(reference_price)) * abs(float(qty))


class NoSlippageModel(SlippageModel):
    """Explicit zero-slippage model."""

    def __init__(self) -> None:
        super().__init__(bps=0.0, volume_impact_bps_per_pct_adv=0.0)


def apply_slippage(
    price: float,
    side: str,
    *,
    bps: float = 0.0,
    volume_impact_bps_per_pct_adv: float = 0.0,
    volume: Optional[float] = None,
    qty: float = 0.0,
) -> float:
    """Convenience wrapper for one-off slippage calculations."""
    return SlippageModel(
        bps=bps,
        volume_impact_bps_per_pct_adv=volume_impact_bps_per_pct_adv,
    ).apply(price, side, volume=volume, qty=qty)
