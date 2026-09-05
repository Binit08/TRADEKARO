import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from app.market_data.live_feed import LiveKiteFeed
from app.domain.events import TickEvent

def test_live_kite_feed_emits_tick_event():
    emitted_ticks = []
    
    def on_tick(tick: TickEvent):
        emitted_ticks.append(tick)
        
    feed = LiveKiteFeed(
        api_key="dummy",
        access_token="dummy",
        instrument_tokens=[738561],
        symbol_map={738561: "RELIANCE"},
        session_id="test_sess",
        on_tick=on_tick
    )
    
    # Simulate a Kite tick
    kite_ticks = [
        {"instrument_token": 738561, "last_price": 2500.5, "volume_traded": 1500}
    ]
    
    feed._on_ticks(None, kite_ticks)
    
    assert len(emitted_ticks) == 1
    tick = emitted_ticks[0]
    
    assert tick.session_id == "test_sess"
    assert tick.symbol == "RELIANCE"
    assert tick.last_price == 2500.5
    assert tick.volume == 1500
    assert tick.event_id is not None
    assert isinstance(tick.timestamp, datetime)
    
    # Ensure backward compatibility market event (candle) is in the internal queue
    # The candle won't be completed until timeframe minutes elapse, but the tracking dict is initialized.
    assert 738561 in feed._current_candles
    c = feed._current_candles[738561]
    assert c["open"] == 2500.5
