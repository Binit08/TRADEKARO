from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable, Any
from app.data.market_event import MarketEvent
from app.domain.events import TickEvent, CandleEvent

class HistoricalDataAdapter(ABC):
    """Abstract Base Class for historical data fetching."""
    
    @abstractmethod
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize with broker-specific credentials."""
        pass
        
    @abstractmethod
    def fetch_historical(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str, 
        timeframe: str = "1d",
        market_type: str = "equity",
        expiry: Optional[str] = None,
        warmup_bars: int = 0
    ) -> List[MarketEvent]:
        """Fetch historical data and normalize it into MarketEvent objects."""
        pass

class LiveFeedAdapter(ABC):
    """Abstract Base Class for live streaming market data."""
    
    @abstractmethod
    def __init__(
        self, 
        credentials: Dict[str, Any],
        symbols: List[str],
        timeframe_minutes: int = 1,
        session_id: str = "default_session",
        warmup_candles: int = 0,
        on_tick: Optional[Callable[[TickEvent], None]] = None,
        on_candle: Optional[Callable[[CandleEvent], None]] = None
    ):
        """Initialize the live feed with credentials and callbacks."""
        pass
        
    @abstractmethod
    def start(self):
        """Start the live feed connection (e.g., connect to WebSocket)."""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop the live feed connection."""
        pass
