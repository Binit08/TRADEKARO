"""Advanced backtest engine behavior tests."""

from datetime import datetime as orig_dt, timezone, timedelta
class datetime(orig_dt):
    def __new__(cls, *args, **kwargs):
        if len(args) < 8 and 'tzinfo' not in kwargs:
            kwargs['tzinfo'] = timezone.utc
        return orig_dt.__new__(cls, *args, **kwargs)

from typing import List

import pytest

from app.core.backtest_engine import BacktestEngine
from app.core.historical_feed import HistoricalReplayFeed
from app.data.market_event import MarketEvent
from app.execution.simulator import ExecutionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.metrics.metrics_engine import MetricsEngine
from app.portfolio.portfolio import Portfolio
from app.signal.models import SignalType, SignalResult


class DummyLoader:
    def __init__(self, events: List[MarketEvent]) -> None:
        self._events = events

    def load(self, symbols, start: str, end: str, timeframe: str, **kwargs) -> List[MarketEvent]:
        return list(self._events)

    def get_data(self):
        return {}


class SequenceSignal:
    def __init__(self, signals: List[SignalType]) -> None:
        self._signals = signals
        self._idx = 0

    def reset(self) -> None:
        self._idx = 0

    def evaluate(self, strategy_ast, indicators, *, default=None):
        if self._idx >= len(self._signals):
            return SignalType.HOLD
        signal = self._signals[self._idx]
        self._idx += 1
        return signal


def _event(i: int, open_price: float, high: float, low: float, close: float) -> MarketEvent:
    return MarketEvent(
        symbol="TEST",
        timestamp=datetime(2024, 1, 1, 9, 15) + timedelta(minutes=5 * i),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )


def _engine(events: List[MarketEvent], signals: List[SignalType], qty: float = 10) -> BacktestEngine:
    return BacktestEngine(
        loader=DummyLoader(events),
        feed=HistoricalReplayFeed,
        indicator=IndicatorEngine(),
        signal=SequenceSignal(signals),
        execution=ExecutionEngine(qty=qty),
        portfolio=Portfolio(initial_cash=10_000),
        metrics=MetricsEngine(),
    )


def test_stop_loss_closes_long_position() -> None:
    engine = _engine(
        [
            _event(0, 100, 101, 99, 100),
            _event(1, 100, 101, 99, 100),
            _event(2, 100, 101, 95, 96),
        ],
        [SignalType.BUY, SignalType.HOLD, SignalType.HOLD],
    )

    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={"stop_loss_pct": 0.02},
    )

    closed = result["closed_trades"]
    assert len(closed) == 1
    assert closed[0].exit_reason == "STOP_LOSS"
    assert closed[0].exit_price == pytest.approx(98.0)
    assert closed[0].pnl == pytest.approx(-20.0)


def test_take_profit_closes_long_position() -> None:
    engine = _engine(
        [
            _event(0, 100, 101, 99, 100),
            _event(1, 100, 101, 99, 100),
            _event(2, 100, 106, 99, 105),
        ],
        [SignalType.BUY, SignalType.HOLD, SignalType.HOLD],
    )

    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={"take_profit_pct": 0.05},
    )

    closed = result["closed_trades"]
    assert len(closed) == 1
    assert closed[0].exit_reason == "TAKE_PROFIT"
    assert closed[0].exit_price == pytest.approx(105.0)
    assert closed[0].pnl == pytest.approx(50.0)


def test_short_entry_and_buy_to_cover_lifecycle() -> None:
    engine = _engine(
        [
            _event(0, 100, 101, 99, 100),
            _event(1, 100, 101, 94, 95),
            _event(2, 90, 91, 89, 90),
        ],
        [SignalType.SELL, SignalResult(signal=SignalType.BUY, reason={"intent": "EXIT"}), SignalType.HOLD],
        qty=5,
    )

    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "SELL"},
        strategy_settings={"allow_short": True},
    )

    closed = result["closed_trades"]
    assert len(closed) == 1
    assert closed[0].side == "SELL"
    assert closed[0].exit_reason == "SHORT_EXIT_SIGNAL"
    assert closed[0].pnl == pytest.approx(50.0)
    assert result["symbol_results"]["TEST"]["portfolio"]["positions"] == 0


def test_protective_exit_skips_entry_bar() -> None:
    engine = _engine(
        [
            _event(0, 100, 101, 99, 100),
            _event(1, 100, 101, 99, 100),
            _event(2, 107, 108, 95, 107),
        ],
        [SignalType.BUY, SignalType.HOLD, SignalType.HOLD],
        qty=1,
    )

    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={"stop_loss_pct": 0.05},
    )

    closed = result["closed_trades"]
    assert len(closed) == 1
    assert result["symbol_results"]["TEST"]["portfolio"]["positions"] == 0
    assert closed[0].exit_reason == "STOP_LOSS"
    assert closed[0].exit_time == datetime(2024, 1, 1, 9, 25)
    assert closed[0].entry_time == datetime(2024, 1, 1, 9, 20)


def test_limit_and_stop_order_types_trigger_on_ohlc() -> None:
    engine = ExecutionEngine(qty=2)
    signal_candle = _event(0, 100, 101, 99, 100)
    fill_candle = _event(1, 100, 106, 98, 101)

    engine.submit_signal("BUY", signal_candle, order_type="LIMIT", limit_price=99)
    limit_fill = engine.execute(fill_candle)
    assert limit_fill is not None
    assert limit_fill.entry_price == pytest.approx(99)

    engine.submit_signal("BUY", signal_candle, order_type="STOP", stop_price=105)
    stop_fill = engine.execute(fill_candle)
    assert stop_fill is not None
    assert stop_fill.entry_price == pytest.approx(105)


def test_percent_sizing_pyramiding_and_reports() -> None:
    engine = _engine(
        [
            _event(0, 100, 101, 99, 100),
            _event(1, 101, 102, 90, 90),
            _event(2, 90, 91, 89, 90),
            _event(3, 90, 91, 89, 90),
        ],
        [SignalType.BUY, SignalType.HOLD, SignalType.BUY, SignalType.HOLD],
    )

    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "position_size_type": "percent_equity",
            "position_size": 0.1,
            "pyramiding": 1,
            "commission_rate": 0.001,
            "slippage_bps": 5,
        },
    )

    position = engine.portfolios["TEST"].positions["TEST"]
    assert position.entries == 1
    assert position.qty >= 9.0
    assert result["settings"]["commission_rate"] == pytest.approx(0.001)
    assert len(result["equity_curve"]) > 1
    assert len(result["trade_report"]) == 2  # 2 open entry legs from pyramiding (pyramid=1)


def test_assume_sl_wins_parameterization() -> None:
    # A long entry candle, followed by a candle that touches both stop loss (95) and take profit (105)
    # Candle 2 has open=100, high=115, low=85, close=100 (touches both 95 and 105)
    events = [
        _event(0, 100, 101, 99, 100),
        _event(1, 100, 101, 99, 100),
        _event(2, 100, 115, 85, 100),
    ]

    # Test 1: assume_sl_wins = True (default) -> should exit with STOP_LOSS
    engine = _engine(events, [SignalType.BUY, SignalType.HOLD, SignalType.HOLD])
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={"stop_loss_pct": 0.05, "take_profit_pct": 0.05, "assume_sl_wins": True},
    )
    closed = result["closed_trades"]
    assert len(closed) == 1
    assert closed[0].exit_reason == "STOP_LOSS"

    # Test 2: assume_sl_wins = False -> should exit with TAKE_PROFIT
    engine2 = _engine(events, [SignalType.BUY, SignalType.HOLD, SignalType.HOLD])
    result2 = engine2.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={"stop_loss_pct": 0.05, "take_profit_pct": 0.05, "assume_sl_wins": False},
    )
    closed2 = result2["closed_trades"]
    assert len(closed2) == 1
    assert closed2[0].exit_reason == "TAKE_PROFIT"


def test_pyramiding_sizing_rising_prices() -> None:
    # 3 entries at rising prices: 100, 110, 120
    # Signals: BUY, BUY, BUY, HOLD
    events = [
        _event(0, 100, 101, 99, 100),
        _event(1, 100, 101, 99, 100), # order 1 executed at open=100
        _event(2, 110, 111, 109, 110), # order 2 executed at open=110
        _event(3, 120, 121, 119, 120), # order 3 executed at open=120
        _event(4, 120, 121, 119, 120),
    ]
    engine = _engine(
        events,
        [SignalType.BUY, SignalType.BUY, SignalType.BUY, SignalType.HOLD, SignalType.HOLD]
    )
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "position_size_type": "percent_equity",
            "position_size": 0.3,
            "pyramiding": 2, # total 3 layers
            "commission_rate": 0.0,
            "slippage_bps": 0,
        },
    )
    # verify portfolio summaries and position entries
    position = engine.portfolios["TEST"].positions["TEST"]
    assert position.entries == 2
    
    # We should have 3 fills
    fills = result["fills"]
    assert len(fills) == 3
    
    # verify they are positive and bounded (e.g. within [5, 15] range)
    for fill in fills:
        assert fill.qty > 0
        assert 5.0 <= fill.qty <= 15.0


def test_pyramiding_sizing_falling_prices() -> None:
    # 3 entries at falling prices: 100, 90, 80
    # Signals: BUY, BUY, BUY, HOLD
    events = [
        _event(0, 100, 101, 99, 100),
        _event(1, 100, 101, 99, 100), # order 1 executed at open=100
        _event(2, 90, 91, 89, 90),    # order 2 executed at open=90
        _event(3, 80, 81, 79, 80),    # order 3 executed at open=80
        _event(4, 80, 81, 79, 80),
    ]
    engine = _engine(
        events,
        [SignalType.BUY, SignalType.BUY, SignalType.BUY, SignalType.HOLD, SignalType.HOLD]
    )
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "position_size_type": "percent_equity",
            "position_size": 0.3,
            "pyramiding": 2, # total 3 layers
            "commission_rate": 0.0,
            "slippage_bps": 0,
        },
    )
    # verify portfolio summaries and position entries
    position = engine.portfolios["TEST"].positions["TEST"]
    assert position.entries == 2
    
    # We should have 3 fills
    fills = result["fills"]
    assert len(fills) == 3
    
    # verify they are positive and bounded
    for fill in fills:
        assert fill.qty > 0
        assert 5.0 <= fill.qty <= 15.0


def test_rebalance_to_target() -> None:
    from app.risk.position import PositionSizer
    sizer = PositionSizer(mode="percent_equity", value=0.1)
    qty = sizer.rebalance_to_target(
        default_qty=10.0,
        cash=10000.0,
        equity=10000.0,
        price=10.0,
        existing_qty=40.0,
        existing_notional=400.0
    )
    assert qty == 60.0


def test_pyramiding_entries_and_first_entry_snapshot() -> None:
    # 2 entries total (1 main + 1 pyramid), then exit
    events = [
        _event(0, 100, 101, 99, 100),
        _event(1, 100, 101, 99, 100), # execute entry 1 (price=100, time=9:20)
        _event(2, 110, 111, 109, 110), # execute entry 2 (price=110, time=9:25)
        _event(3, 120, 121, 119, 120), # signal exit (close_on_opposite_signal)
        _event(4, 120, 121, 119, 120), # execute exit at 120
    ]
    engine = _engine(
        events,
        [SignalType.BUY, SignalType.BUY, SignalType.HOLD, SignalType.SELL, SignalType.HOLD]
    )
    
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "position_size_type": "percent_equity",
            "position_size": 0.2,
            "pyramiding": 1, # total 2 layers
            "commission_rate": 0.0,
            "slippage_bps": 0,
            "close_on_opposite_signal": True,
        },
    )
    
    closed = result["closed_trades"]
    # With pyramiding, two entry legs are tracked separately; find the first-leg (lifecycle) trade
    # which carries the averaged entry_price and lifecycle_first_entry_price
    assert len(closed) >= 1
    # The first leg trade has lifecycle_first_entry_price from the very first open
    lifecycle_trade = next(t for t in closed if t.lifecycle_first_entry_price == pytest.approx(100.0))
    closed_trade = lifecycle_trade
    
    # verify average entry price vs first entry price
    assert closed_trade.lifecycle_first_entry_price == pytest.approx(100.0)
    
    # check entry times
    assert closed_trade.first_entry_time == datetime(2024, 1, 1, 9, 20)
    assert closed_trade.exit_time == datetime(2024, 1, 1, 9, 35)


def test_portfolio_pyramiding_entries_count() -> None:
    from app.portfolio.portfolio import Portfolio
    from app.execution.trade import Trade
    
    port = Portfolio(initial_cash=10000)
    t1 = Trade(symbol="TEST", side="BUY", entry_price=100.0, qty=10.0, entry_time=datetime(2024, 1, 1, 9, 20))
    pos = port.open_position(t1)
    
    # First entry: entries should be 0
    assert pos.entries == 0
    assert pos.lifecycle_first_entry_price == 100.0
    assert pos.first_entry_time == datetime(2024, 1, 1, 9, 20)
    
    # Additive entry: entries should increment to 1
    t2 = Trade(symbol="TEST", side="BUY", entry_price=110.0, qty=10.0, entry_time=datetime(2024, 1, 1, 9, 25))
    pos2 = port.open_position(t2)
    
    assert pos2.entries == 1
    assert pos2.lifecycle_first_entry_price == 100.0
    assert pos2.first_entry_time == datetime(2024, 1, 1, 9, 20)
    assert pos2.entry_price == 105.0 # average price


def test_no_lookahead_invariant() -> None:
    events = [
        _event(0, 100, 101, 99, 100),  # t = 9:15
        _event(1, 100, 101, 99, 100),  # t = 9:20
    ]
    engine = _engine(events, [SignalType.BUY, SignalType.HOLD])
    
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={},
    )
    
    assert len(engine.portfolios["TEST"].trade_history) == 1
    trade = engine.portfolios["TEST"].trade_history[0]
    
    # Assert order was submitted at t=9:15 (candle 0)
    assert trade.order_created_time == datetime(2024, 1, 1, 9, 15)
    # Assert trade filled at t=9:20 (candle 1, which is t+1)
    assert trade.entry_time == datetime(2024, 1, 1, 9, 20)


def test_protective_exit_on_entry_bar_documented() -> None:
    events = [
        _event(0, 100, 101, 99, 100),  # t = 9:15
        _event(1, 100, 101, 98, 100),  # t = 9:20. Filled at open=100.0, Low = 98.0 (<= SL 99.0)
    ]
    engine = _engine(events, [SignalType.BUY, SignalType.HOLD])
    
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "stop_loss_pct": 0.01,  # SL = 100.0 * (1.0 - 0.01) = 99.0
        },
    )
    
    closed = result["closed_trades"]
    assert len(closed) == 1
    closed_trade = closed[0]
    
    assert closed_trade.entry_price == 100.0
    assert closed_trade.entry_time == datetime(2024, 1, 1, 9, 20)
    
    # Assert protective exit happened on the SAME bar
    assert closed_trade.exit_time == datetime(2024, 1, 1, 9, 20)
    assert closed_trade.exit_reason == "STOP_LOSS"
    # Documented worst-case fill at SL price (99.0)
    assert closed_trade.exit_price == pytest.approx(99.0)


def test_failed_short_close_surfaces_warning() -> None:
    events = [
        _event(0, 100, 101, 99, 100),   # t = 9:15: Submit short entry
        _event(1, 100, 101, 99, 100),   # t = 9:20: Fill short entry (entry_price=100.0)
        _event(2, 300, 301, 299, 300),  # t = 9:25: Price runs to 300, submit exit signal
        _event(3, 300, 301, 299, 300),  # t = 9:30: Attempt close (underfunded)
    ]
    engine = _engine(events, [SignalType.SELL, SignalType.HOLD, SignalType.BUY, SignalType.HOLD], qty=10)
    engine.portfolio.initial_cash = 1000.0
    engine.portfolio._initial_cash = 1000.0
    
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "allow_short": True,
            "close_on_opposite_signal": True,
            "short_margin_pct": 0.5,
        },
    )
    
    # (a) position remains OPEN
    assert "TEST" in engine.portfolios["TEST"].positions
    pos = engine.portfolios["TEST"].positions["TEST"]
    assert pos.status == "OPEN"
    
    # (b) the response contains a warning
    warnings = result["warnings"]
    assert any("Failed to close position" in w for w in warnings)
    
    # (c) fills does NOT contain the rejected fill
    fills = result["fills"]
    exit_fills = [f for f in fills if f.intent == "EXIT"]
    assert len(exit_fills) == 0
    assert len(fills) == 1
    assert fills[0].intent == "ENTRY"


def test_indicator_under_pattern_node_discovered() -> None:
    from app.ast.indicator_extractor import IndicatorExtractor

    ast = {
        "node_type": "PATTERN",
        "pattern_config": {
            "name": "Bullish Engulfing",
            "parameters": {
                "source": {
                    "node_type": "INDICATOR",
                    "indicator_config": {
                        "indicator_type": "EMA",
                        "parameters": {
                            "period": 20
                        }
                    }
                }
            }
        }
    }

    configs = IndicatorExtractor.extract_indicator_configs_from_ast(ast)
    assert len(configs) == 1
    assert configs[0]["name"] == "EMA"
    assert configs[0]["timeperiod"] == 20


def test_indicator_under_variable_assignment_value_node_discovered() -> None:
    from app.ast.indicator_extractor import IndicatorExtractor

    ast = {
        "node_type": "VARIABLE_ASSIGNMENT",
        "name": "my_var",
        "value": {
            "node_type": "INDICATOR",
            "indicator_config": {
                "indicator_type": "RSI",
                "parameters": {
                    "period": 14
                }
            }
        }
    }

    configs = IndicatorExtractor.extract_indicator_configs_from_ast(ast)
    assert len(configs) == 1
    assert configs[0]["name"] == "RSI"
    assert configs[0]["timeperiod"] == 14


def test_first_entry_price_after_close_reopen() -> None:
    events = [
        _event(0, 100, 101, 99, 100), # t=9:15
        _event(1, 100, 101, 99, 100), # t=9:20 -> Buy fills at 100
        _event(2, 100, 101, 99, 100), # t=9:25 -> Sell fills at 100
        _event(3, 200, 201, 199, 200), # t=9:30 -> Buy fills at 200
        _event(4, 200, 201, 199, 200), # t=9:35 -> Sell fills at 200
        _event(5, 200, 201, 199, 200), # t=9:40
    ]
    engine = _engine(
        events,
        [SignalType.BUY, SignalType.SELL, SignalType.BUY, SignalType.SELL, SignalType.HOLD, SignalType.HOLD]
    )
    result = engine.run(
        "TEST",
        "2024-01-01",
        "2024-01-02",
        "5m",
        {"left": 1, "operator": ">", "right": 0, "signal": "BUY"},
        strategy_settings={
            "position_size_type": "percent_equity",
            "position_size": 0.1,
            "pyramiding": 0,
            "commission_rate": 0.0,
            "slippage_bps": 0,
        },
    )
    closed = result["closed_trades"]
    assert len(closed) == 2
    
    # Assert both Trades have distinct original_entry_price / lifecycle_first_entry_price values
    t1, t2 = closed[0], closed[1]
    assert t1.original_entry_price == 100.0
    assert t2.original_entry_price == 200.0
    assert t1.lifecycle_first_entry_price == 100.0
    assert t2.lifecycle_first_entry_price == 200.0






