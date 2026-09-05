"""Domain order models for the paper trading architecture."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class OrderIntent:
    """Represents an intention to place an order from Strategy or Risk engine.
    
    This is strictly an intent and must be simulated by the execution engine.
    It is idempotent based on `order_intent_id`.
    """
    order_intent_id: str
    session_id: str
    symbol: str
    timestamp: datetime
    side: str  # 'BUY' or 'SELL'
    quantity: float
    order_type: str  # 'MARKET', 'LIMIT', 'SL', etc.
    reason: str  # 'STRATEGY_ENTRY', 'STRATEGY_EXIT', 'STOP_LOSS', 'TAKE_PROFIT', 'TRAILING_STOP', 'MANUAL_EXIT'
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    sequence_number: Optional[int] = None


@dataclass(frozen=True)
class OrderFill:
    """Represents a simulated fill resulting from an OrderIntent."""
    fill_id: str
    session_id: str
    order_intent_id: str
    symbol: str
    timestamp: datetime
    side: str
    filled_quantity: float
    filled_price: float
    fees: float
    slippage: float
    sequence_number: Optional[int] = None
