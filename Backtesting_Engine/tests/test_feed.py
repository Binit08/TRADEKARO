"""Tests for the HistoricalReplayFeed engine.

These tests exercise sequential replay, state updates, peeking,
resetting, and progress reporting using three mock candles for a
single symbol `RELIANCE.NS` at 09:15, 09:20 and 09:25.

Note: tests are written to match the current `HistoricalReplayFeed`
behaviour in `app/core/historical_feed.py` (reset resets to the
beginning so `current_idx == -1` after `reset()`). If you prefer
`current_idx` to be 0 after reset, update the implementation
accordingly and adjust these assertions.
"""
from datetime import datetime
from typing import List

import pytest

from app.data.market_event import MarketEvent
from app.core.historical_feed import HistoricalReplayFeed


def _make_event(time_str: str, close: float) -> MarketEvent:
    """Helper to create a MarketEvent with symbol RELIANCE.NS."""
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


@pytest.fixture
def sample_events() -> List[MarketEvent]:
    return [
        _make_event("2020-01-01T09:15:00", 103.0),
        _make_event("2020-01-01T09:20:00", 104.0),
        _make_event("2020-01-01T09:25:00", 105.0),
    ]


def test_sequential_replay_and_timestamps(sample_events):
    """Feed.stream() should yield closes in chronological order and
    timestamps must be returned sequentially without skipping."""
    feed = HistoricalReplayFeed(sample_events)

    closes = []
    timestamps = []
    for candle in feed.stream():
        closes.append(candle.close)
        timestamps.append(candle.timestamp)

    assert closes == [103.0, 104.0, 105.0]

    # Ensure timestamps are exactly those provided and in order
    assert timestamps[0].time().strftime("%H:%M") == "09:15"
    assert timestamps[1].time().strftime("%H:%M") == "09:20"
    assert timestamps[2].time().strftime("%H:%M") == "09:25"


def test_current_state_updates_and_progress(sample_events):
    """Verify `current_idx`, `current_time`, `current_event` update
    during replay and that `get_progress()` returns expected values."""
    feed = HistoricalReplayFeed(sample_events)

    # Initially
    assert feed.current_idx == -1
    assert feed.current_time is None
    assert feed.current_event is None
    assert feed.has_next() is True
    assert feed.get_progress() == {"processed": 0, "remaining": 3}

    # Consume first event and check progress
    gen = feed.stream()
    first = next(gen)
    assert first.close == 103.0
    assert feed.current_idx == 0
    assert feed.current_event is first
    assert feed.current_time == first.timestamp
    assert feed.get_progress() == {"processed": 1, "remaining": 2}

    # Consume remaining events
    second = next(gen)
    third = next(gen)
    assert second.close == 104.0
    assert third.close == 105.0

    # After finishing
    assert feed.has_next() is False
    assert feed.get_progress() == {"processed": 3, "remaining": 0}


def test_peek_does_not_advance_pointer(sample_events):
    """peek() must return the next event without advancing the feed."""
    feed = HistoricalReplayFeed(sample_events)

    assert feed.current_idx == -1
    next_event = feed.peek()
    assert next_event is not None
    assert next_event.close == 103.0

    # current_idx should be unchanged
    assert feed.current_idx == -1

    # After peek, consuming should still return the same first event
    first = next(feed.stream())
    assert first.close == 103.0


def test_reset_and_replay_again(sample_events):
    """Replay to the end, reset the feed, and replay again.

    After reset the feed should be at the initial state (`current_idx == -1`,
    `current_time is None`) and iteration should produce the same sequence.
    """
    feed = HistoricalReplayFeed(sample_events)

    # Consume all
    list(feed.stream())
    assert feed.has_next() is False

    # Reset to beginning
    feed.reset()
    assert feed.current_idx == -1
    assert feed.current_time is None

    # Replay again and ensure same sequence
    closes = [c.close for c in feed.stream()]
    assert closes == [103.0, 104.0, 105.0]


def test_get_progress_mid_and_end(sample_events):
    """Validate get_progress() in the middle and at the end of replay."""
    feed = HistoricalReplayFeed(sample_events)

    gen = feed.stream()
    _ = next(gen)  # processed 1
    assert feed.get_progress() == {"processed": 1, "remaining": 2}

    # finish
    list(gen)
    assert feed.get_progress() == {"processed": 3, "remaining": 0}


def test_integration_example_prints_timestamps_and_closes(sample_events, capsys):
    """Integration-style example: iterate and print timestamp and close.

    This test demonstrates example usage and asserts the printed output
    contains the expected times and close values.
    """
    feed = HistoricalReplayFeed(sample_events)

    for candle in feed.stream():
        print(candle.timestamp.time().strftime("%H:%M"), int(candle.close))

    captured = capsys.readouterr()
    lines = [l.strip() for l in captured.out.strip().splitlines()]
    assert lines == ["09:15 103", "09:20 104", "09:25 105"]
