"""Fee calculations for simulated order fills."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeModel:
    """Simple percentage-plus-fixed commission model.

    Args:
        rate: Percentage fee as a decimal. For example, ``0.001`` is 10 bps.
        fixed: Flat fee charged on every fill.
        min_fee: Minimum fee charged when a fill has non-zero notional.
    """

    rate: float = 0.0
    fixed: float = 0.0
    min_fee: float = 0.0

    def calculate(self, notional: float, qty: float | None = None, price: float | None = None) -> float:
        """Return the fee for a fill."""
        del qty, price
        notional = abs(float(notional))
        if notional == 0:
            return 0.0

        fee = notional * float(self.rate) + float(self.fixed)
        if self.min_fee > 0:
            fee = max(fee, float(self.min_fee))
        return float(fee)


class NoFeeModel(FeeModel):
    """Explicit zero-fee model."""

    def __init__(self) -> None:
        super().__init__(rate=0.0, fixed=0.0, min_fee=0.0)


def calculate_fee(
    notional: float,
    *,
    rate: float = 0.0,
    fixed: float = 0.0,
    min_fee: float = 0.0,
) -> float:
    """Convenience wrapper for one-off fee calculations."""
    return FeeModel(rate=rate, fixed=fixed, min_fee=min_fee).calculate(notional)
