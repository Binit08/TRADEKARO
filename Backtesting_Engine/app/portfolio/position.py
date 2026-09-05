"""Position model for portfolio accounting."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Position:
    """Represents an open long position in the portfolio.

    Attributes:
        lifecycle_first_entry_price: First entry of the CURRENT open position, reset on close+reopen.
    """

    symbol: str
    qty: float
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    side: str = "LONG"
    entry_fee: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None
    entry_reason: str | None = None
    multiplier: float = 1.0
    margin: float = 0.0
    trade_index: int = -1
    trade_indices: List[int] = field(default_factory=list)
    entries: int = 0
    status: str = "OPEN"
    lifecycle_first_entry_price: float | None = None
    first_entry_time: datetime | None = None
