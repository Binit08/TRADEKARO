"""Trade model for execution engine.

`Trade.pnl` is realized PnL net of fees and slippage. `gross_pnl` is the
pre-fee, pre-slippage PnL amount.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    """Represents an executed trade in the backtest.

    Note: `slippage` is informational. The actual price impact is already embedded
    in the `entry_price` (and `exit_price` if applicable).

    Fees Semantics:
    - When the position is OPEN, `fees` contains entry-only fees.
    - When the position is CLOSED, `fees` contains the total round-trip fees (entry_fee + exit_fee).

    Attributes:
        lifecycle_first_entry_price: First entry of the CURRENT open position, reset on close+reopen.
    """

    symbol: str
    side: str
    entry_price: float
    qty: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    status: str = "OPEN"
    fees: float = 0.0
    slippage: float = 0.0
    pnl: Optional[float] = None
    gross_pnl: Optional[float] = None
    order_type: str = "MARKET"
    exit_order_type: Optional[str] = None
    intent: str = "ENTRY"
    position_side: Optional[str] = None
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_created_time: Optional[datetime] = None
    lifecycle_first_entry_price: Optional[float] = None
    first_entry_time: Optional[datetime] = None
    original_entry_price: Optional[float] = None
    entry_fee: Optional[float] = None
    exit_fee: Optional[float] = None
    multiplier: float = 1.0
    margin: float = 0.0



