from datetime import datetime as orig_dt, timezone, timedelta
class datetime(orig_dt):
    def __new__(cls, *args, **kwargs):
        if len(args) < 8 and 'tzinfo' not in kwargs:
            kwargs['tzinfo'] = timezone.utc
        return orig_dt.__new__(cls, *args, **kwargs)

from app.data.market_event import MarketEvent
from app.core.historical_feed import HistoricalReplayFeed


def make_event(ts_str: str, close: float) -> MarketEvent:
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return MarketEvent(symbol="TEST", timestamp=dt, open=close - 1, high=close + 1, low=close - 2, close=close, volume=1000)


def test_stream_and_progress():
    # Create three chronological events
    events = [
        make_event("2020-01-01T09:15:00", 103.0),
        make_event("2020-01-01T09:20:00", 104.0),
        make_event("2020-01-01T09:25:00", 105.0),
    ]

    feed = HistoricalReplayFeed(events)

    # Before consuming any event
    assert feed.get_progress() == {"processed": 0, "remaining": 3}
    assert feed.has_next() is True
    assert feed.peek().close == 103.0

    closes = []
    for candle in feed.stream():
        # during iteration, current_event should match candle
        assert feed.current_event is candle
        closes.append(candle.close)

    assert closes == [103.0, 104.0, 105.0]

    # After finishing
    assert feed.has_next() is False
    assert feed.get_progress() == {"processed": 3, "remaining": 0}

    # Reset and stream again
    feed.reset()
    assert feed.get_progress() == {"processed": 0, "remaining": 3}


def test_peek_and_empty():
    events = [make_event("2020-01-01T09:15:00", 110.0)]
    feed = HistoricalReplayFeed(events)

    assert feed.peek() is not None
    assert feed.peek().close == 110.0

    # Consume
    next(feed.stream())
    assert feed.has_next() is False
    assert feed.peek() is None


def test_deduplication(caplog):
    import logging
    # T1 occurs twice: E1 and E2.
    # E2 occurs later, so it should override E1.
    events = [
        make_event("2020-01-01T09:15:00", 100.0),
        make_event("2020-01-01T09:15:00", 102.0),
        make_event("2020-01-01T09:20:00", 105.0),
    ]

    with caplog.at_level(logging.WARNING):
        feed = HistoricalReplayFeed(events)
        assert len(feed) == 2
        assert "Dropped 1 duplicate market events" in caplog.text

    candles = list(feed.stream())
    assert len(candles) == 2
    assert candles[0].close == 102.0
    assert candles[1].close == 105.0


def test_dedup_strategy_first_last_raise():
    events = [
        make_event("2020-01-01T09:15:00", 100.0),
        make_event("2020-01-01T09:15:00", 102.0),
        make_event("2020-01-01T09:20:00", 105.0),
    ]
    
    # test "first"
    feed_first = HistoricalReplayFeed(events, dedup_strategy="first")
    assert len(feed_first) == 2
    candles_first = list(feed_first.stream())
    assert candles_first[0].close == 100.0
    
    # test "last"
    feed_last = HistoricalReplayFeed(events, dedup_strategy="last")
    assert len(feed_last) == 2
    candles_last = list(feed_last.stream())
    assert candles_last[0].close == 102.0
    
    # test "raise"
    import pytest
    with pytest.raises(ValueError, match="Duplicate market events detected"):
        HistoricalReplayFeed(events, dedup_strategy="raise")

