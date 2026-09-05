"""Domain events for the paper trading architecture."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TickEvent:
    """Represents a raw tick from the exchange."""
    event_id: str
    session_id: str
    instrument_token: int
    symbol: str
    timestamp: datetime
    last_price: float
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    sequence_number: Optional[int] = None
    is_warmup: bool = False


@dataclass(frozen=True)
class CandleEvent:
    """Represents a completed aggregated candle."""
    event_id: str
    session_id: str
    instrument_token: int
    symbol: str
    timeframe: str  # e.g., '1m', '5m'
    timestamp: datetime  # Open time of the candle
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    sequence_number: Optional[int] = None
    is_warmup: bool = False
    is_completed: bool = True


@dataclass(frozen=True)
class PortfolioUpdateEvent:
    """Represents an update to the portfolio state."""
    event_id: str
    session_id: str
    timestamp: datetime
    cash: float
    unrealized_pnl: float
    realized_pnl: float
    total_equity: float
    sequence_number: Optional[int] = None
    is_warmup: bool = False


@dataclass(frozen=True)
class PositionUpdateEvent:
    """Represents an update to an individual position."""
    event_id: str
    session_id: str
    symbol: str
    timestamp: datetime
    quantity: float
    average_entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    sequence_number: Optional[int] = None
    is_warmup: bool = False


@dataclass(frozen=True)
class SessionStatusEvent:
    """Represents a change in the paper trading session lifecycle."""
    event_id: str
    session_id: str
    timestamp: datetime
    status: str
    message: Optional[str] = None
