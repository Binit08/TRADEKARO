"""Tests for execution engine V1.

Signal
  -> pending order on signal candle
  -> execution on next candle open
  -> trade recorded in history
"""

from datetime import datetime as orig_dt, timezone, timedelta
class datetime(orig_dt):
    def __new__(cls, *args, **kwargs):
        if len(args) < 8 and 'tzinfo' not in kwargs:
            kwargs['tzinfo'] = timezone.utc
        return orig_dt.__new__(cls, *args, **kwargs)

from app.data.market_event import MarketEvent
from app.core.backtest_engine import BacktestEngine
from app.core.historical_feed import HistoricalReplayFeed
from app.execution.simulator import ExecutionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.metrics.metrics_engine import MetricsEngine
from app.portfolio.portfolio import Portfolio
from app.signal.models import SignalType
from app.signal.signal_engine import SignalEngine


def _candle(ts: datetime, open_price: float) -> MarketEvent:
	"""Create deterministic candle fixture."""
	return MarketEvent(
		symbol="RELIANCE",
		timestamp=ts,
		open=open_price,
		high=open_price + 1,
		low=open_price - 1,
		close=open_price,
		volume=1000,
	)


def test_buy_execution() -> None:
	"""BUY at 09:15 should execute at next candle (09:20) open."""
	engine = ExecutionEngine()

	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 103)
	next_candle = _candle(datetime(2024, 1, 1, 9, 20), 104)

	engine.submit_signal(SignalType.BUY, signal_candle)
	trade = engine.execute(next_candle)

	assert trade is not None
	assert trade.side == "BUY"
	assert trade.entry_price == 104
	assert trade.entry_time == datetime(2024, 1, 1, 9, 20)
	assert trade.qty == 100


def test_hold() -> None:
	"""HOLD should not create an order or trade."""
	engine = ExecutionEngine()
	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 103)

	order = engine.submit_signal(SignalType.HOLD, signal_candle)
	trade = engine.execute(_candle(datetime(2024, 1, 1, 9, 20), 104))

	assert order is None
	assert trade is None


def test_pending_order() -> None:
	"""BUY should create a pending order (not immediate execution)."""
	engine = ExecutionEngine()
	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 103)

	order = engine.submit_signal("BUY", signal_candle)

	assert order is not None
	assert len(engine.pending_orders) == 1
	assert engine.pending_orders[0].status == "PENDING"
	assert engine.pending_orders[0].created_time == datetime(2024, 1, 1, 9, 15)


def test_history() -> None:
	"""Executed trades should be stored in history."""
	engine = ExecutionEngine()
	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 103)
	next_candle = _candle(datetime(2024, 1, 1, 9, 20), 104)

	engine.submit_signal("BUY", signal_candle)
	engine.execute(next_candle)

	history = engine.get_trade_history()
	assert len(history) == 1
	assert history[0].entry_price == 104


def test_reset() -> None:
	"""Reset should clear orders and history."""
	engine = ExecutionEngine()
	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 103)
	next_candle = _candle(datetime(2024, 1, 1, 9, 20), 104)

	engine.submit_signal("BUY", signal_candle)
	engine.execute(next_candle)

	assert len(engine.pending_orders) == 0
	assert len(engine.trade_history) == 1

	engine.reset()

	assert len(engine.pending_orders) == 0
	assert len(engine.trade_history) == 0


def test_multi_symbol_execution_matches_symbol_only() -> None:
	"""Orders for other symbols should not be executed on a different symbol's candle."""
	engine = ExecutionEngine()

	# create two signal candles for different symbols
	signal_candle_a = MarketEvent(
		symbol="RELIANCE",
		timestamp=datetime(2024, 1, 1, 9, 15),
		open=103,
		high=104,
		low=102,
		close=103,
		volume=1000,
	)

	signal_candle_b = MarketEvent(
		symbol="TCS",
		timestamp=datetime(2024, 1, 1, 9, 15),
		open=203,
		high=205,
		low=202,
		close=204,
		volume=1500,
	)

	# submit signals for both symbols
	engine.submit_signal("BUY", signal_candle_a)
	engine.submit_signal("BUY", signal_candle_b)

	# execute on RELIANCE next candle -> should only fill RELIANCE order
	next_candle_a = MarketEvent(
		symbol="RELIANCE",
		timestamp=datetime(2024, 1, 1, 9, 20),
		open=104,
		high=105,
		low=103,
		close=104,
		volume=1100,
	)

	trade_a = engine.execute(next_candle_a)
	assert trade_a is not None
	assert trade_a.symbol == "RELIANCE"

	# one order (TCS) should remain pending
	assert len(engine.pending_orders) == 1
	assert engine.pending_orders[0].symbol == "TCS"

	# execute on TCS candle -> should fill remaining order
	next_candle_b = MarketEvent(
		symbol="TCS",
		timestamp=datetime(2024, 1, 1, 9, 20),
		open=205,
		high=206,
		low=204,
		close=205,
		volume=1200,
	)

	trade_b = engine.execute(next_candle_b)
	assert trade_b is not None
	assert trade_b.symbol == "TCS"
	assert len(engine.pending_orders) == 0


def test_rejected_short_fill_is_not_recorded_in_history() -> None:
	class StubLoader:
		def __init__(self, events):
			self.events = events

		def load(self, symbols, start, end, timeframe, **kwargs):
			return self.events

	loader = StubLoader([
		_candle(datetime(2024, 1, 1, 9, 15), 100),
		_candle(datetime(2024, 1, 1, 9, 20), 101),
	])

	engine = BacktestEngine(
		loader=loader,
		feed=HistoricalReplayFeed,
		indicator=IndicatorEngine(),
		signal=SignalEngine(),
		execution=ExecutionEngine(qty=50),
		portfolio=Portfolio(initial_cash=1000, short_margin_pct=0.5),
		metrics=MetricsEngine(),
	)

	strategy_ast = {"left": 1, "operator": ">", "right": 0, "signal": "SELL"}
	result = engine.run(
		symbols=["RELIANCE"],
		start="2024-01-01",
		end="2024-01-02",
		timeframe="5m",
		strategy_ast=strategy_ast,
		strategy_settings={"allow_short": True, "short_margin_pct": 0.5},
	)

	assert len(result["fills"]) == 0
	assert len(engine.execution.trade_history) == 0
	assert result["symbol_results"]["RELIANCE"]["portfolio"]["positions"] == 0
	assert result["symbol_results"]["RELIANCE"]["metrics"]["closed_trades"] == 0


def test_order_not_filled_on_same_candle() -> None:
	"""An order submitted on candle t must NOT be filled on candle t."""
	engine = ExecutionEngine()
	candle_t = _candle(datetime(2024, 1, 1, 9, 15), 103)

	engine.submit_signal(SignalType.BUY, candle_t)

	# Try to execute on the same candle t
	trade = engine.execute(candle_t)

	# Verify that the trade is NOT executed on the same candle
	assert trade is None
	assert len(engine.pending_orders) == 1
	assert engine.pending_orders[0].status == "PENDING"


def test_limit_and_stop_pricing_details() -> None:
	"""Limit orders fill at limit price only (not open), and stop orders fill with adverse gap slippage."""
	import pytest
	engine = ExecutionEngine(qty=1)

	# 1. Limit order BUY: open (95) is better than limit_price (99)
	# Should fill at 99, not 95
	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 100)
	fill_candle = _candle(datetime(2024, 1, 1, 9, 20), 95) # open=95, high=96, low=94, close=95

	engine.submit_order(signal=SignalType.BUY, candle=signal_candle, order_type="LIMIT", limit_price=99.0)
	fill = engine.execute(fill_candle)
	assert fill is not None
	assert fill.entry_price == pytest.approx(99.0)

	# Reset
	engine.reset()

	# 2. Stop order BUY with gap-up: open (107) is higher than stop_price (105)
	# Should fill at 107 (max(stop_price, open))
	fill_candle_gap_up = _candle(datetime(2024, 1, 1, 9, 20), 107) # open=107, high=108, low=106, close=107

	engine.submit_order(signal=SignalType.BUY, candle=signal_candle, order_type="STOP", stop_price=105.0)
	fill = engine.execute(fill_candle_gap_up)
	assert fill is not None
	assert fill.entry_price == pytest.approx(107.0)

	# Reset
	engine.reset()

	# 3. Stop order SELL with gap-down: open (93) is lower than stop_price (95)
	# Should fill at 93 (min(stop_price, open))
	fill_candle_gap_down = _candle(datetime(2024, 1, 1, 9, 20), 93) # open=93, high=94, low=92, close=93

	engine.submit_order(signal=SignalType.SELL, candle=signal_candle, order_type="STOP", stop_price=95.0)
	fill = engine.execute(fill_candle_gap_down)
	assert fill is not None
	assert fill.entry_price == pytest.approx(93.0)


def test_execute_multiple_pending_orders() -> None:
	"""Submitting multiple pending orders and executing them on the same candle should execute all of them without index shifting/skipping."""
	engine = ExecutionEngine()
	signal_candle = _candle(datetime(2024, 1, 1, 9, 15), 100)
	next_candle = _candle(datetime(2024, 1, 1, 9, 20), 101) # open=101, high=102, low=100

	# Submit multiple orders on the signal candle
	engine.submit_order(signal=SignalType.BUY, candle=signal_candle, order_type="MARKET", qty=10)
	engine.submit_order(signal=SignalType.BUY, candle=signal_candle, order_type="LIMIT", limit_price=105.0, qty=20)
	engine.submit_order(signal=SignalType.BUY, candle=signal_candle, order_type="MARKET", qty=30)

	assert len(engine.pending_orders) == 3

	# Execute all on the next candle
	fills = engine.execute_all(next_candle)

	# All should be executed successfully on the next candle
	assert len(fills) == 3
	assert len(engine.pending_orders) == 0

	# Verify each trade details
	assert fills[0].qty == 10
	assert fills[0].entry_price == 101 # market open
	assert fills[1].qty == 20
	assert fills[1].entry_price == 105 # limit price
	assert fills[2].qty == 30
	assert fills[2].entry_price == 101 # market open

	assert len(engine.get_trade_history()) == 3




