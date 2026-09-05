"""Runtime integration tests validating Feed → IndicatorEngine pipeline.

This test creates synthetic market data (250 candles), replays them through
HistoricalReplayFeed, updates IndicatorEngine with each candle, and validates
that all indicators compute correctly at runtime.

Architecture:

    MarketEvent[] (synthetic data)
       ↓
    HistoricalReplayFeed
       ↓
    IndicatorEngine
       ↓
    Indicators (RSI, EMA, MACD, BBANDS, ATR, etc.)
"""

from datetime import datetime, timedelta
from typing import List

import pytest

talib = pytest.importorskip("talib")

from app.data.market_event import MarketEvent
from app.core.historical_feed import HistoricalReplayFeed
from app.indicators.indicator_engine import IndicatorEngine


def _generate_synthetic_events(count: int = 250, start_price: float = 100.0) -> List[MarketEvent]:
    """Generate synthetic OHLCV candles for testing.

    Each candle's close price increments by +1.0 from the previous candle.
    Timestamps are spaced 5 minutes apart starting from 2024-01-01T00:00:00.
    """
    events: List[MarketEvent] = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)

    for i in range(count):
        price = start_price + i
        ts = base_time + timedelta(minutes=5 * i)

        event = MarketEvent(
            symbol="TEST",
            timestamp=ts,
            open=price,
            high=price + 1.0,
            low=price - 1.0,
            close=price,
            volume=1000.0,
        )
        events.append(event)

    return events


def test_runtime_feed_to_indicator_pipeline() -> None:
    """Integration test: Feed → IndicatorEngine pipeline validation.

    1. Create synthetic 250 candles (prices 100 to 349).
    2. Feed through HistoricalReplayFeed.
    3. Update IndicatorEngine with each candle.
    4. Validate indicators are available and compute correctly.
    """
    # Step 1: Generate synthetic data
    events = _generate_synthetic_events(count=250, start_price=100.0)
    print(f"\n[1/6] Generated {len(events)} synthetic candles (prices 100 → 349)")

    # Step 2: Initialize Feed and Indicator Engine
    feed = HistoricalReplayFeed(events)
    indicator = IndicatorEngine()
    print(f"[2/6] Initialized HistoricalReplayFeed and IndicatorEngine")

    # Step 3: Replay feed and update indicators
    candles_processed = 0
    for candle in feed.stream():
        indicator.update(candle)
        candles_processed += 1
    print(f"[3/6] Replayed {candles_processed} candles through indicator engine")

    # Step 4: Test indicator availability
    available = indicator.available()
    print(f"[4/6] TA-Lib indicators available: {len(available)}")
    print(f"      First 20: {available[:20]}")
    assert len(available) > 100, f"Expected >100 indicators, got {len(available)}"

    # Step 5: Test RSI
    rsi_result = indicator.compute("RSI", timeperiod=14)
    assert rsi_result is not None, "RSI should be ready after 250 candles"
    assert rsi_result["name"] == "RSI"
    assert isinstance(rsi_result["value"], float)
    print(f"[5/6] RSI(14): {rsi_result['value']:.2f}")

    # Step 6: Test EMA(200)
    ema_result = indicator.compute("EMA", timeperiod=200)
    assert ema_result is not None, "EMA(200) should be ready after 250 candles"
    assert ema_result["name"] == "EMA"
    assert isinstance(ema_result["value"], float)
    print(f"      EMA(200): {ema_result['value']:.2f}")

    # Step 7: Test MACD
    macd_result = indicator.compute("MACD")
    assert macd_result is not None, "MACD should be ready after 250 candles"
    assert macd_result["name"] == "MACD"
    assert isinstance(macd_result["value"], dict)
    assert "macd" in macd_result["value"]
    assert "macdsignal" in macd_result["value"]
    assert "macdhist" in macd_result["value"]
    print(f"      MACD: {macd_result['value']}")

    # Step 8: Test BBANDS
    bbands_result = indicator.compute("BBANDS")
    assert bbands_result is not None, "BBANDS should be ready after 250 candles"
    assert bbands_result["name"] == "BBANDS"
    assert isinstance(bbands_result["value"], dict)
    assert "upperband" in bbands_result["value"]
    assert "middleband" in bbands_result["value"]
    assert "lowerband" in bbands_result["value"]
    print(f"      BBANDS: {bbands_result['value']}")

    # Step 9: Test ATR
    atr_result = indicator.compute("ATR", timeperiod=14)
    assert atr_result is not None, "ATR should be ready after 250 candles"
    assert atr_result["name"] == "ATR"
    assert isinstance(atr_result["value"], float)
    print(f"      ATR(14): {atr_result['value']:.2f}")

    # Step 10: Test compute_many()
    batch_result = indicator.compute_many(
        [
            {"name": "RSI", "timeperiod": 14},
            {"name": "EMA", "timeperiod": 200},
            {"name": "ATR", "timeperiod": 14},
        ]
    )
    assert "RSI" in batch_result, "RSI missing from batch compute"
    assert "EMA" in batch_result, "EMA missing from batch compute"
    assert "ATR" in batch_result, "ATR missing from batch compute"
    print(f"[6/6] compute_many() result: {batch_result}")

    print("\n✓ Loader → Feed → Indicator Engine VALIDATED")
