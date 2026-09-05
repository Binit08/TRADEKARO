"""Direct test runner for HistoricalReplayFeed (no pytest required).

This script runs a subset of the pytest-style tests programmatically
so it can be executed in environments without `pytest` installed.
"""
import sys
from datetime import datetime

from app.data.market_event import MarketEvent
from app.core.historical_feed import HistoricalReplayFeed


def _make_event(time_str: str, close: float) -> MarketEvent:
    ts = datetime.fromisoformat(time_str)
    return MarketEvent(
        symbol="RELIANCE.NS",
        timestamp=ts,
        open=close - 0.5,
        high=close + 0.5,
        low=close - 1.0,
        close=close,
        volume=1000.0,
    )


def run():
    events = [
        _make_event("2020-01-01T09:15:00", 103.0),
        _make_event("2020-01-01T09:20:00", 104.0),
        _make_event("2020-01-01T09:25:00", 105.0),
    ]

    feed = HistoricalReplayFeed(events)

    # Sequential replay
    closes = [c.close for c in feed.stream()]
    assert closes == [103.0, 104.0, 105.0], f"unexpected closes: {closes}"

    feed.reset()

    # State updates and progress
    gen = feed.stream()
    first = next(gen)
    assert feed.current_idx == 0
    assert feed.current_event is first
    assert feed.get_progress() == {"processed": 1, "remaining": 2}

    # Peek
    feed.reset()
    nxt = feed.peek()
    assert nxt.close == 103.0
    assert feed.current_idx == -1

    # finish and check has_next
    list(feed.stream())
    assert feed.has_next() is False

    # reset and replay again
    feed.reset()
    assert feed.current_idx == -1
    assert feed.current_time is None
    list(feed.stream())

    print("All direct feed tests passed")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as e:
        print("Test failed:", e)
        sys.exit(1)
    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(2)
    sys.exit(0)
