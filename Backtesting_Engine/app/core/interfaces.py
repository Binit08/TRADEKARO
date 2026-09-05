"""Core abstractions and protocols for Dependency Inversion."""

from typing import Iterator, Protocol
from app.data.market_event import MarketEvent


class FeedProtocol(Protocol):
    """Protocol defining the required interface for market feeds."""
    
    def stream(self) -> Iterator[MarketEvent]:
        """Stream market events sequentially."""
        ...
        
    def reset(self) -> None:
        """Reset the feed to its initial state."""
        ...
