"""Order model for execution engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """Represents a pending order created from a trading signal."""

    signal: str
    created_time: datetime
    symbol: str
    qty: Optional[float] = None
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    intent: str = "ENTRY"
    reason: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str = "PENDING"
