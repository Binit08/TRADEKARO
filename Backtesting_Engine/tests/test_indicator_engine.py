"""Production tests for dynamic TA-Lib IndicatorEngine."""

from datetime import datetime, timedelta
from typing import List

import pytest

talib = pytest.importorskip("talib")

from app.data.market_event import MarketEvent
from app.indicators.indicator_engine import IndicatorEngine


def _candle(ts: datetime, price: float) -> MarketEvent:
    """Create a deterministic candle for indicator testing."""
    return MarketEvent(
        symbol="RELIANCE.NS",
        timestamp=ts,
        open=price - 0.4,
        high=price + 0.6,
        low=price - 0.8,
        close=price,
        volume=1000.0 + price,
    )


def _seed_engine(engine: IndicatorEngine, n: int = 300) -> None:
    """Seed engine with synthetic upward candles to satisfy long windows."""
    start = datetime(2024, 1, 1, 9, 15)
    for i in range(n):
        engine.update(_candle(start + timedelta(minutes=5 * i), 100.0 + (0.2 * i)))


def test_available_indicators() -> None:
    engine = IndicatorEngine()
    indicators = engine.available()
    assert isinstance(indicators, list)
    assert len(indicators) > 100
    assert "RSI" in indicators
    assert "EMA" in indicators
    assert "MACD" in indicators
    assert "BBANDS" in indicators


def test_rsi_ready() -> None:
    engine = IndicatorEngine()
    _seed_engine(engine, n=50)
    out = engine.compute("RSI", timeperiod=14)
    assert out is not None
    assert out["name"] == "RSI"
    assert isinstance(out["value"], float)


def test_ema_ready() -> None:
    engine = IndicatorEngine()
    _seed_engine(engine, n=260)
    out = engine.compute("EMA", timeperiod=200)
    assert out is not None
    assert out["name"] == "EMA"
    assert isinstance(out["value"], float)


def test_compute_many() -> None:
    engine = IndicatorEngine()
    _seed_engine(engine, n=260)

    result = engine.compute_many(
        [
            {"name": "RSI", "timeperiod": 14},
            {"name": "EMA", "timeperiod": 200},
            {"name": "ATR", "timeperiod": 14},
        ]
    )

    assert "RSI" in result
    assert "EMA" in result
    assert "ATR" in result
    assert isinstance(result["RSI"], float)
    assert isinstance(result["EMA"], float)
    assert isinstance(result["ATR"], float)


def test_none_before_ready() -> None:
    engine = IndicatorEngine()
    _seed_engine(engine, n=10)

    rsi_14 = engine.compute("RSI", timeperiod=14)
    ema_200 = engine.compute("EMA", timeperiod=200)

    assert rsi_14 is None
    assert ema_200 is None


def test_macd() -> None:
    engine = IndicatorEngine()
    _seed_engine(engine, n=120)
    out = engine.compute("MACD")
    assert out is not None
    assert out["name"] == "MACD"
    assert isinstance(out["value"], dict)
    assert "macd" in out["value"]
    assert "macdsignal" in out["value"]
    assert "macdhist" in out["value"]


def test_bbands() -> None:
    engine = IndicatorEngine()
    _seed_engine(engine, n=60)
    out = engine.compute("BBANDS")
    assert out is not None
    assert out["name"] == "BBANDS"
    assert isinstance(out["value"], dict)
    assert "upperband" in out["value"]
    assert "middleband" in out["value"]
    assert "lowerband" in out["value"]


def test_compute_all_is_constant_per_bar() -> None:
    import time
    from app.core.backtest_engine import BacktestEngine
    from app.core.historical_feed import HistoricalReplayFeed
    from app.portfolio.portfolio import Portfolio
    from app.execution.simulator import ExecutionEngine
    from app.metrics.metrics_engine import MetricsEngine
    from app.signal.signal_engine import SignalEngine
    
    # Generate 1000 candles
    start = datetime(2024, 1, 1, 9, 15)
    events = [
        MarketEvent(
            symbol="TEST",
            timestamp=start + timedelta(minutes=5 * i),
            open=100.0 + 0.1 * i,
            high=101.0 + 0.1 * i,
            low=99.0 + 0.1 * i,
            close=100.0 + 0.1 * i,
            volume=1000.0
        )
        for i in range(1000)
    ]
    
    class TimeStubLoader:
        def load(self, symbols, start, end, timeframe, **kwargs):
            return events
            
    engine = BacktestEngine(
        loader=TimeStubLoader(),
        feed=HistoricalReplayFeed,
        indicator=IndicatorEngine(),
        signal=SignalEngine(),
        execution=ExecutionEngine(qty=10),
        portfolio=Portfolio(initial_cash=10000),
        metrics=MetricsEngine(),
    )
    
    ast = {
        "schema_version": "1.0.0",
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "benchmark",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [
                                {
                                    "node_type": "GREATER_THAN",
                                    "children": [
                                        {
                                            "node_type": "INDICATOR",
                                            "indicator_config": {
                                                "indicator_type": "RSI",
                                                "parameters": {"period": 14}
                                            }
                                        },
                                        {
                                            "node_type": "INDICATOR",
                                            "indicator_config": {
                                                "indicator_type": "SMA",
                                                "parameters": {"period": 20}
                                            }
                                        }
                                    ]
                                },
                                {
                                    "node_type": "GREATER_THAN",
                                    "children": [
                                        {
                                            "node_type": "INDICATOR",
                                            "indicator_config": {
                                                "indicator_type": "EMA",
                                                "parameters": {"period": 50}
                                            }
                                        },
                                        {
                                            "node_type": "INDICATOR",
                                            "indicator_config": {
                                                "indicator_type": "MACD",
                                                "parameters": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
                                            }
                                        }
                                    ]
                                },
                                {
                                    "node_type": "GREATER_THAN",
                                    "children": [
                                        {
                                            "node_type": "INDICATOR",
                                            "indicator_config": {
                                                "indicator_type": "BBANDS",
                                                "parameters": {"timeperiod": 20}
                                            }
                                        },
                                        {"node_type": "CONSTANT", "value": 10.0}
                                    ]
                                }
                            ]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    
    t_start = time.perf_counter()
    engine.run(
        symbols=["TEST"],
        start="2024-01-01",
        end="2024-01-02",
        timeframe="5m",
        strategy_ast=ast,
    )
    t_end = time.perf_counter()
    elapsed = t_end - t_start
    
    print(f"Elapsed time for 1000-bar, 5-indicator backtest: {elapsed * 1000:.2f}ms")
    assert elapsed < 0.5, f"Expected backtest to complete in < 500ms, took {elapsed * 1000:.2f}ms"


def test_custom_indicator_lacks_interface_raises_error() -> None:
    from app.core.backtest_engine import BacktestEngine
    
    class DummyIndicator:
        pass
        
    engine = BacktestEngine(
        loader=None,
        feed=None,
        indicator=DummyIndicator(),
        signal=None,
        execution=None,
        portfolio=None,
        metrics=None,
    )
    
    with pytest.raises(AttributeError, match="Custom indicator engine must implement"):
        engine.run(
            symbols=["TEST"],
            start="2024-01-01",
            end="2024-01-02",
            timeframe="5m",
            strategy_ast={},
        )
