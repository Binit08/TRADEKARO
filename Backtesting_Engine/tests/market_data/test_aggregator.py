import pytest
from datetime import datetime, timezone, timedelta
from app.market_data.aggregator import CandleAggregator
from app.domain.events import TickEvent

def test_candle_aggregator_emits_candle():
    emitted_candles = []
    
    def on_candle(candle):
        emitted_candles.append(candle)
        
    aggregator = CandleAggregator(timeframe_minutes=1, on_candle=on_candle)
    
    start_time = datetime(2024, 1, 1, 9, 15, 0, tzinfo=timezone.utc)
    
    # Tick 1: Starts the candle
    aggregator.on_tick(TickEvent(
        event_id="t1",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=start_time,
        last_price=100.0,
        volume=100
    ))
    
    assert len(emitted_candles) == 0
    
    # Tick 2: Inside the candle (updates High/Low)
    aggregator.on_tick(TickEvent(
        event_id="t2",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=start_time + timedelta(seconds=30),
        last_price=105.0, # New High
        volume=200
    ))
    
    assert len(emitted_candles) == 0
    
    # Tick 3: Inside the candle
    aggregator.on_tick(TickEvent(
        event_id="t3",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=start_time + timedelta(seconds=45),
        last_price=95.0, # New Low
        volume=300
    ))
    
    assert len(emitted_candles) == 0
    
    # Tick 4: 60 seconds passed - Closes the candle
    aggregator.on_tick(TickEvent(
        event_id="t4",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=start_time + timedelta(seconds=60),
        last_price=102.0, # Close price of old candle and Open of new candle
        volume=400
    ))
    
    assert len(emitted_candles) == 1
    candle = emitted_candles[0]
    
    assert candle.symbol == "RELIANCE"
    assert candle.open == 100.0
    assert candle.high == 105.0
    assert candle.low == 95.0
    assert candle.close == 102.0
    assert candle.volume == 400
    
    # Verify aggregator reset
    assert aggregator._current_candles["RELIANCE"]["open"] == 102.0
    assert aggregator._current_candles["RELIANCE"]["start_time"] == start_time + timedelta(seconds=60)
