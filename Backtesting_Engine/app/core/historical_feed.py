"""Historical replay feed engine.

This module implements `HistoricalReplayFeed`, a production-oriented
replay engine that consumes a list of `MarketEvent` and yields them
sequentially without any future leakage.

Constraints:
- Single-asset only
- Historical replay only (no live, no ticks, no sessions)
- Synchronous, single-threaded
"""
from datetime import datetime
from typing import Iterator, List, Optional, Dict
from dataclasses import asdict

from app.data.market_event import MarketEvent


class HistoricalReplayFeed:
    """Replay a historical list of `MarketEvent` sequentially.

    The feed exposes the current position via `current_idx`,
    `current_time`, and `current_event`. Use `stream()` to iterate
    through the events without future leakage.

    Example:
        events = loader.load()
        feed = HistoricalReplayFeed(events)
        for candle in feed.stream():
            print(candle.timestamp, candle.close)
    """

    def __init__(self, events: List[MarketEvent], dedup_strategy: str = "last"):
        """Create a new replay feed.

        Args:
            events: Pre-loaded list of MarketEvent. They will be sorted
                by `timestamp` to guarantee chronological replay. A copy
                of the list is kept to avoid mutating caller data.
            dedup_strategy: Strategy for handling duplicate events with the same
                (symbol, timestamp). Options:
                - "first": keep the first event encountered in chronological order.
                - "last": keep the last event encountered (default).
                - "raise": raise a ValueError if duplicates are found.
                
                The default is "last" to preserve the latest (most recent) OHLCV occurrence
                recorded for the given candle timestamp.
        """
        if dedup_strategy not in ("first", "last", "raise"):
            raise ValueError(f"Invalid dedup_strategy: {dedup_strategy}")

        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        seen_keys = set()
        duplicates = []
        for event in sorted_events:
            key = (event.symbol, event.timestamp)
            if key in seen_keys:
                duplicates.append(event.timestamp)
            seen_keys.add(key)

        if duplicates:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(
                "Duplicate market event timestamps found: %s",
                [t.isoformat() if hasattr(t, "isoformat") else str(t) for t in duplicates]
            )
            if dedup_strategy == "raise":
                raise ValueError(
                    f"Duplicate market events detected for timestamps: "
                    f"{[t.isoformat() if hasattr(t, 'isoformat') else str(t) for t in duplicates]}"
                )
        
        seen = {}
        for event in sorted_events:
            key = (event.symbol, event.timestamp)
            if dedup_strategy == "first":
                if key not in seen:
                    seen[key] = event
            else:
                seen[key] = event
            
        self._events = list(seen.values())
        
        dropped = len(sorted_events) - len(self._events)
        if dropped > 0:
            import logging
            logging.getLogger(__name__).warning(
                "Dropped %d duplicate market events (symbol, timestamp) in HistoricalReplayFeed.",
                dropped
            )

        # Index of the last returned event. Starts at -1 (nothing processed).
        self.current_idx: int = -1

        # Convenience attributes updated while replaying.
        self.current_time: Optional[datetime] = None
        self.current_event: Optional[MarketEvent] = None

    def __len__(self) -> int:
        return len(self._events)

    def has_next(self) -> bool:
        """Return True if there is at least one event left to consume."""
        return (self.current_idx + 1) < len(self._events)

    def peek(self) -> Optional[MarketEvent]:
        """Return the next event without consuming it.

        Returns:
            The next `MarketEvent` if available, otherwise `None`.
        """
        next_idx = self.current_idx + 1
        if next_idx < len(self._events):
            return self._events[next_idx]
        return None

    def reset(self) -> None:
        """Reset the feed to the beginning.

        After reset, `current_idx` is -1 and `current_event`/`current_time`
        are cleared.
        """
        self.current_idx = -1
        self.current_event = None
        self.current_time = None

    def get_progress(self) -> Dict[str, int]:
        """Return a small progress summary.

        Returns:
            A dict with `processed` and `remaining` counts.
        """
        processed = max(0, self.current_idx + 1)
        remaining = len(self._events) - processed
        return {"processed": processed, "remaining": remaining}

    def stream(self) -> Iterator[MarketEvent]:
        """Generator that yields `MarketEvent` sequentially.

        The replay guarantees no future leakage: when an event is yielded,
        the feed's public state (`current_idx`, `current_time`,
        `current_event`) refers only to that event or earlier.

        Yields:
            MarketEvent: next candle in chronological order.
        """
        # Iterate until no more events remain.
        while self.has_next():
            # Move forward one event and update internal state.
            self.current_idx += 1
            self.current_event = self._events[self.current_idx]
            self.current_time = self.current_event.timestamp

            # Yield the event to the caller. The caller receives only the
            # current candle; peek/has_next should be used to inspect
            # upcoming data without consuming.
            yield self.current_event

    # Small helper for debugging / introspection
    def to_dict(self) -> Dict:
        """Return a shallow dict describing the feed state."""
        return {
            "total": len(self._events),
            "current_idx": self.current_idx,
            "current_time": getattr(self.current_time, "isoformat", lambda: None)(),
            "current_event": asdict(self.current_event) if self.current_event else None,
        }
