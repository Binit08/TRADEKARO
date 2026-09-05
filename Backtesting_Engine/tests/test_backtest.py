"""Integration tests for the unified backtest engine."""

from datetime import datetime as orig_dt, timezone, timedelta
class datetime(orig_dt):
    def __new__(cls, *args, **kwargs):
        if len(args) < 8 and 'tzinfo' not in kwargs:
            kwargs['tzinfo'] = timezone.utc
        return orig_dt.__new__(cls, *args, **kwargs)

from typing import List, Dict, Any

import pytest

from app.core.backtest_engine import BacktestEngine
from app.core.historical_feed import HistoricalReplayFeed
from app.data.market_event import MarketEvent
from app.data.loader import MarketDataLoader
from app.execution.simulator import ExecutionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.metrics.metrics_engine import MetricsEngine
from app.portfolio.portfolio import Portfolio
from app.signal.signal_engine import SignalEngine
from app.config.settings import StrategySettings


talib = pytest.importorskip("talib")


class DummyLoader(MarketDataLoader):
    """Loader that returns synthetic market data for tests."""

    def __init__(self, events: List[MarketEvent]) -> None:
        self._events = events

    def load(self, symbols: List[str], start: str, end: str, timeframe: str, **kwargs) -> List[MarketEvent]:
        return list(self._events)
        
    def get_data(self) -> Dict[str, Any]:
        return {}


def _generate_trending_events(count: int = 40, start_price: float = 100.0) -> List[MarketEvent]:
    events: List[MarketEvent] = []
    base_time = datetime(2024, 1, 1, 9, 15)
    for i in range(count):
        price = start_price + i
        timestamp = base_time + timedelta(minutes=5 * i)
        events.append(
            MarketEvent(
                symbol="RELIANCE.NS",
                timestamp=timestamp,
                open=price,
                high=price + 1.0,
                low=price - 1.0,
                close=price,
                volume=1000.0,
            )
        )
    return events


def _build_backtest_engine(events: List[MarketEvent], indicator_configs: List[Dict[str, Any]]) -> BacktestEngine:
    loader = DummyLoader(events)
    feed = HistoricalReplayFeed
    indicator = IndicatorEngine()
    signal = SignalEngine()
    execution = ExecutionEngine(qty=10.0)
    portfolio = Portfolio(initial_cash=100000.0)
    metrics = MetricsEngine()
    return BacktestEngine(
        loader=loader,
        feed=feed,
        indicator=indicator,
        signal=signal,
        execution=execution,
        portfolio=portfolio,
        metrics=metrics,
        indicator_configs=indicator_configs,
    )


def test_full_run() -> None:
    """Full pipeline should return portfolio, metrics, and trades."""
    events = _generate_trending_events()
    engine = _build_backtest_engine(
        events,
        indicator_configs=[{"name": "EMA", "timeperiod": 3}],
    )

    strategy_ast = {
        "operator": "AND",
        "conditions": [
            {"left": "EMA", "operator": "<", "right": 102},
        ],
        "signal": "BUY"
    }

    result = engine.run(
        symbols=["RELIANCE.NS"],
        start="2024-01-01",
        end="2024-02-01",
        timeframe="5m",
        strategy_ast=strategy_ast,
    )

    assert "portfolio" in result
    assert "metrics" in result
    assert "trades" in result
    assert isinstance(result["trades"], list)
    assert isinstance(result["portfolio"], dict)
    assert isinstance(result["metrics"], dict)


def test_trade_generation() -> None:
    """The backtest engine should generate at least one trade for a strategy."""
    events = _generate_trending_events(count=50)
    engine = _build_backtest_engine(
        events,
        indicator_configs=[{"name": "EMA", "timeperiod": 3}],
    )

    strategy_ast = {
        "operator": "AND",
        "conditions": [
            {"left": "EMA", "operator": "<", "right": 104},
        ],
        "signal": "BUY"
    }

    result = engine.run(
        symbols=["RELIANCE.NS"],
        start="2024-01-01",
        end="2024-03-01",
        timeframe="5m",
        strategy_ast=strategy_ast,
    )

    assert len(result["trades"]) >= 1


def test_metrics() -> None:
    """Metrics should include core performance values after the run."""
    events = _generate_trending_events(count=50)
    engine = _build_backtest_engine(
        events,
        indicator_configs=[{"name": "EMA", "timeperiod": 3}],
    )

    strategy_ast = {
        "operator": "AND",
        "conditions": [
            {"left": "EMA", "operator": "<", "right": 104},
        ],
        "signal": "BUY"
    }

    result = engine.run(
        symbols=["RELIANCE.NS"],
        start="2024-01-01",
        end="2024-03-01",
        timeframe="5m",
        strategy_ast=strategy_ast,
    )

    metrics = result["metrics"]
    assert "total_trades" in metrics
    assert "net_pnl" in metrics
    assert "return_pct" in metrics
    assert isinstance(metrics["total_trades"], int)
    assert isinstance(metrics["net_pnl"], float)


def test_portfolio_update() -> None:
    """Portfolio summary should update after backtest execution."""
    events = _generate_trending_events(count=50)
    engine = _build_backtest_engine(
        events,
        indicator_configs=[{"name": "EMA", "timeperiod": 3}],
    )

    strategy_ast = {
        "operator": "AND",
        "conditions": [
            {"left": "EMA", "operator": "<", "right": 104},
        ],
        "signal": "BUY"
    }

    result = engine.run(
        symbols=["RELIANCE.NS"],
        start="2024-01-01",
        end="2024-03-01",
        timeframe="5m",
        strategy_ast=strategy_ast,
    )

    portfolio = result["portfolio"]
    assert "cash" in portfolio
    assert "equity" in portfolio
    assert portfolio["cash"] >= 0
    assert portfolio["equity"] >= 0


def test_entry_candle_protective_exit() -> None:
    """The backtest engine should check and trigger a protective exit on the entry candle."""
    base_time = datetime(2024, 1, 1, 9, 15)
    events = [
        # Candle 0: entry signal fires
        MarketEvent(
            symbol="RELIANCE.NS",
            timestamp=base_time,
            open=100.0,
            high=102.0,
            low=98.0,
            close=100.0,
            volume=1000.0,
        ),
        # Candle 1: entry fills at open (100.0), low is 94.0 (breaches 95.0 stop-loss)
        MarketEvent(
            symbol="RELIANCE.NS",
            timestamp=base_time + timedelta(minutes=5),
            open=100.0,
            high=102.0,
            low=94.0,
            close=98.0,
            volume=1000.0,
        ),
    ]

    strategy_ast = {
        "operator": "AND",
        "conditions": [
            {"left": 1, "operator": ">", "right": 0},
        ],
        "signal": "BUY"
    }

    loader = DummyLoader(events)
    feed = HistoricalReplayFeed
    indicator = IndicatorEngine()
    signal = SignalEngine()
    execution = ExecutionEngine(qty=10.0)
    portfolio = Portfolio(initial_cash=100000.0)
    metrics = MetricsEngine()
    
    settings = StrategySettings(
        position_size_type="fixed_qty",
        position_size=10.0,
        stop_loss_pct=0.05,  # 5% SL -> stop price = 95.0
        assume_sl_wins=True,
    )

    engine = BacktestEngine(
        loader=loader,
        feed=feed,
        indicator=indicator,
        signal=signal,
        execution=execution,
        portfolio=portfolio,
        metrics=metrics,
        settings=settings,
    )

    result = engine.run(
        symbols=["RELIANCE.NS"],
        start="2024-01-01",
        end="2024-03-01",
        timeframe="5m",
        strategy_ast=strategy_ast,
    )

    trades = result["trades"]
    assert len(trades) == 2
    
    entry_fill = trades[0]
    exit_fill = trades[1]
    
    assert entry_fill.intent == "ENTRY"
    assert entry_fill.entry_price == 100.0
    assert entry_fill.entry_time == base_time + timedelta(minutes=5)
    
    assert exit_fill.intent == "EXIT"
    assert exit_fill.entry_reason == "STOP_LOSS"
    assert exit_fill.entry_price == 95.0
    assert exit_fill.entry_time == base_time + timedelta(minutes=5)
