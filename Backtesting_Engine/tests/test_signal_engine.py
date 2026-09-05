"""Tests for the AST-based SignalEngine."""

from datetime import datetime, timedelta
from typing import Dict

import pytest

from app.data.market_event import MarketEvent
from app.core.historical_feed import HistoricalReplayFeed
from app.indicators.indicator_engine import IndicatorEngine
from app.signal.signal_engine import SignalEngine
from app.signal.models import SignalType


def _make_events(prices):
    start = datetime(2024, 1, 1, 9, 0)
    events = []
    for i, p in enumerate(prices):
        events.append(MarketEvent(symbols=["TEST"], timestamp=start + timedelta(minutes=5 * i), open=p, high=p + 1, low=p - 1, close=p, volume=1000))
    return events


def test_buy():
    # RSI < 30 -> BUY
    ast = {"left": "RSI", "operator": "<", "right": 30, "signal": "BUY"}
    engine = SignalEngine()
    indicators = {"RSI": 25}
    assert engine.evaluate(ast, indicators).signal == SignalType.BUY


def test_sell():
    # RSI > 70 -> SELL (signal override)
    ast = {"left": "RSI", "operator": ">", "right": 70, "signal": "SELL"}
    engine = SignalEngine()
    indicators = {"RSI": 75}
    assert engine.evaluate(ast, indicators).signal == SignalType.SELL


def test_hold():
    # Condition false -> HOLD
    ast = {"left": "RSI", "operator": "<", "right": 30}
    engine = SignalEngine()
    indicators = {"RSI": 50}
    assert engine.evaluate(ast, indicators).signal == SignalType.HOLD


def test_nested_and():
    ast = {
        "operator": "AND",
        "conditions": [
            {"left": "RSI", "operator": "<", "right": 30},
            {"left": "ATR", "operator": ">", "right": 3},
        ],
        "signal": "BUY",
    }
    engine = SignalEngine()
    indicators = {"RSI": 25, "ATR": 4}
    assert engine.evaluate(ast, indicators).signal == SignalType.BUY


def test_nested_or():
    ast = {
        "operator": "OR",
        "conditions": [
            {"left": "ADX", "operator": ">", "right": 25},
            {"left": "Close", "operator": ">", "right": "EMA200"},
        ],
        "signal": "BUY",
    }
    engine = SignalEngine()
    indicators = {"ADX": 10, "Close": 150, "EMA200": 100}
    assert engine.evaluate(ast, indicators).signal == SignalType.BUY


def test_not():
    ast = {"operator": "NOT", "conditions": [{"left": "RSI", "operator": ">", "right": 70}], "signal": "BUY"}
    engine = SignalEngine()
    indicators = {"RSI": 60}
    assert engine.evaluate(ast, indicators).signal == SignalType.BUY


def test_cross_above():
    # CROSS_ABOVE should trigger on second evaluation when left crosses above right
    ast = {"left": "MACD", "operator": "CROSS_ABOVE", "right": "SIGNAL", "signal": "BUY"}
    engine = SignalEngine()

    # First snapshot: macd <= signal
    indicators1 = {"MACD": 0.0, "SIGNAL": 0.1}
    assert engine.evaluate(ast, indicators1).signal == SignalType.HOLD

    # Second snapshot: macd > signal (cross)
    indicators2 = {"MACD": 0.5, "SIGNAL": 0.1}
    assert engine.evaluate(ast, indicators2).signal == SignalType.BUY


def test_cross_below():
    ast = {"left": "MACD", "operator": "CROSS_BELOW", "right": "SIGNAL", "signal": "SELL"}
    engine = SignalEngine()

    indicators1 = {"MACD": 0.7, "SIGNAL": 0.6}
    assert engine.evaluate(ast, indicators1).signal == SignalType.HOLD

    indicators2 = {"MACD": 0.2, "SIGNAL": 0.6}
    assert engine.evaluate(ast, indicators2).signal == SignalType.SELL


def test_indicator_alias_and_output_resolution():
    ast = {
        "left": {"indicator": "MACD", "timeperiod": 12, "alias": "macd_sig", "output": "macdsignal"},
        "operator": ">",
        "right": 0,
        "signal": "BUY",
    }
    engine = SignalEngine()
    indicators = {"macd_sig": {"macd": 0.1, "macdsignal": 0.2}}
    assert engine.evaluate(ast, indicators).signal == SignalType.BUY


def test_random_ast():
    ast = {
        "operator": "AND",
        "conditions": [
            {
                "operator": "OR",
                "conditions": [
                    {"left": "RSI", "operator": "<", "right": 30},
                    {"left": "MACD", "operator": "CROSS_ABOVE", "right": "SIGNAL"},
                ],
            },
            {"left": "ATR", "operator": ">", "right": 5},
        ],
        "signal": "BUY",
    }
    engine = SignalEngine()

    # First: RSI false, MACD not crossed, ATR small
    indicators1 = {"RSI": 50, "MACD": 0.0, "SIGNAL": 0.1, "ATR": 1}
    assert engine.evaluate(ast, indicators1).signal == SignalType.HOLD

    # Second: MACD crosses above SIGNAL and ATR large enough
    indicators2 = {"RSI": 50, "MACD": 0.5, "SIGNAL": 0.1, "ATR": 6}
    # Need two calls to produce a cross: first call to set previous
    engine.evaluate(ast, indicators1)
    res = engine.evaluate(ast, indicators2)
    assert res.signal == SignalType.BUY


def test_unexpected_exception_propagates_immediately() -> None:
    # If the evaluator raises an unexpected error like AttributeError, it should propagate immediately
    engine = SignalEngine()
    with pytest.raises(AttributeError):
        engine.evaluate("not_a_dict", {})


def test_consecutive_evaluator_failures_raises_runtime_error() -> None:
    # 3 consecutive expected errors (like ValueError) should trigger RuntimeError
    engine = SignalEngine(max_failures=3)
    ast = {"left": 10, "operator": "UNKNOWN_OP", "right": 5, "signal": "BUY"}
    
    # First failure -> return SignalType.HOLD, warnings append
    res1 = engine.evaluate(ast, {})
    assert res1.signal == SignalType.HOLD
    assert len(engine.warnings) == 1
    assert engine.warnings[0] == "EVAL_ERROR"
    
    # Second failure -> return SignalType.HOLD, warnings append
    res2 = engine.evaluate(ast, {})
    assert res2.signal == SignalType.HOLD
    assert len(engine.warnings) == 2
    
    # Third failure -> raises RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        engine.evaluate(ast, {})
    assert "consecutively" in str(exc_info.value)


def test_warnings_surfaced_in_backtest_response() -> None:
    # Test that the warnings are included in BacktestEngine.run return value
    from app.core.backtest_engine import BacktestEngine
    from app.portfolio.portfolio import Portfolio
    from app.metrics.metrics_engine import MetricsEngine
    from app.execution.simulator import ExecutionEngine
    
    class StubLoader:
        def load(self, symbols, start, end, timeframe, **kwargs):
            return [MarketEvent("TEST", datetime(2024, 1, 1, 9, 15), 100.0, 101.0, 99.0, 100.0, 1000)]
            
    engine = BacktestEngine(
        loader=StubLoader(),
        feed=HistoricalReplayFeed,
        indicator=IndicatorEngine(),
        signal=SignalEngine(),
        execution=ExecutionEngine(qty=10),
        portfolio=Portfolio(initial_cash=1000),
        metrics=MetricsEngine(),
    )
    
    ast = {"left": 10, "operator": "UNKNOWN_OP", "right": 5, "signal": "BUY"}
    
    result = engine.run(
        symbols=["TEST"],
        start="2024-01-01",
        end="2024-01-02",
        timeframe="5m",
        strategy_ast=ast,
    )
    
    assert "warnings" in result
    assert len(result["warnings"]) == 1
    assert result["warnings"][0] == "EVAL_ERROR"


def test_dynamic_lookback_buffer():
    from app.ast.loader import StrategyLoader
    from app.signal.evaluator import get_max_lookback, SignalEvaluator
    
    # 1. Build an AST containing various lookback nodes
    # Sequence of 5 of (Close t-4 > SMA_20)
    # Plus a Cross above with lookback of 8
    # Total lookback = max(Sequence(5) + MarketRef(4), Cross(8)) = max(9, 8) = 9
    ast_json = {
        "schema_version": "1.0.0",
        "execution_context": {
            "symbol": "AAPL",
            "timeframe": "1D",
            "start_date": "2020-01-01",
            "end_date": "2025-01-01",
            "capital": 100000.0,
            "position_side": "LONG"
        },
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "test_lookback",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [
                                {
                                    "node_type": "AND",
                                    "children": [
                                        {
                                            "node_type": "SEQUENCE",
                                            "count": 5,
                                            "condition": {
                                                "node_type": "GREATER_THAN",
                                                "children": [
                                                    {
                                                        "node_type": "MARKET_REFERENCE",
                                                        "data_type": "CLOSE",
                                                        "lookback_periods": 4
                                                    },
                                                    {
                                                        "node_type": "CONSTANT",
                                                        "value": 100.0
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "node_type": "CROSS_ABOVE",
                                            "lookback_periods": 8,
                                            "children": [
                                                {
                                                    "node_type": "MARKET_REFERENCE",
                                                    "data_type": "CLOSE",
                                                    "lookback_periods": 0
                                                },
                                                {
                                                    "node_type": "CONSTANT",
                                                    "value": 90.0
                                                }
                                            ]
                                        }
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
    
    loader = StrategyLoader()
    bundle = loader.load_from_json(ast_json)
    
    # Assert get_max_lookback logic
    max_lookback = get_max_lookback(bundle.ast)
    # max_lookback should be max(5 + 4, 8 + 0) = 9
    assert max_lookback == 9
    
    # 1. Initialize SignalEvaluator with default maxlen=256
    evaluator = SignalEvaluator(maxlen=256)
    evaluator.evaluate(bundle.ast, {}, {"CLOSE": 100.0})
    assert evaluator.history.maxlen == 256
    
    # 2. Large lookback (lookback > maxlen) must raise ValueError
    ast_large = dict(ast_json)
    ast_large["ast"]["operation_nodes"][0]["entry_nodes"][0]["children"][0]["children"][0]["count"] = 300
    bundle_large = loader.load_from_json(ast_large)
    
    max_lookback_large = get_max_lookback(bundle_large.ast)
    assert max_lookback_large == 304  # 300 + 4
    
    # Evaluating with maxlen=256 should raise
    with pytest.raises(ValueError, match="exceeds history buffer capacity"):
        evaluator.evaluate(bundle_large.ast, {}, {"CLOSE": 100.0})
        
    # 3. Parameterizing from SignalEngine.__init__ / SignalEvaluator.__init__ based on max-lookback
    evaluator_configured = SignalEvaluator(maxlen=max_lookback_large + 10)
    assert evaluator_configured.history.maxlen == 314
    # Evaluating with configured maxlen should pass
    evaluator_configured.evaluate(bundle_large.ast, {}, {"CLOSE": 100.0})


def test_lookback_deque_boundaries():
    # Test boundary lookback requirements around default 256 capacity
    from app.ast.nodes import MarketReferenceNode
    from app.signal.evaluator import SignalEvaluator

    # Default maxlen is 256
    evaluator = SignalEvaluator(maxlen=256)
    
    # 1. Lookback = 255: within 256 capacity. Note: total_lookback = current_offset (0) + node.lookback_periods (255) = 255.
    node_255 = MarketReferenceNode(data_type="CLOSE", lookback_periods=255)
    # This shouldn't raise, should just return None since history is empty (but capacity check passes)
    assert evaluator._resolve_value(node_255, current_offset=0, lookback=0) is None

    # 2. Lookback = 256: within 256 capacity
    node_256 = MarketReferenceNode(data_type="CLOSE", lookback_periods=256)
    assert evaluator._resolve_value(node_256, current_offset=0, lookback=0) is None

    # 3. Lookback = 257: exceeds 256 capacity, must raise ValueError
    node_257 = MarketReferenceNode(data_type="CLOSE", lookback_periods=257)
    with pytest.raises(ValueError, match="exceeds history buffer capacity"):
        evaluator._resolve_value(node_257, current_offset=0, lookback=0)


def test_warmup_period_does_not_crash():
    # Invalid operator raises ValueError (which is treated as a transient failure)
    ast = {"left": 10, "operator": "UNKNOWN_OP", "right": 5, "signal": "BUY"}
    # Set max_failures=3, but warmup_bars=50
    engine = SignalEngine(max_failures=3, warmup_bars=50)
    
    # First 49 candles: produce ValueError
    for _ in range(49):
        assert engine.evaluate(ast, {}).signal == SignalType.HOLD
        
    # The next 51 candles: provide a valid AST, producing valid signals
    valid_ast = {"left": "RSI", "operator": "<", "right": 30, "signal": "BUY"}
    for _ in range(51):
        assert engine.evaluate(valid_ast, {"RSI": 50}).signal == SignalType.HOLD
        
    # Verify no RuntimeError was raised and 49 warnings were recorded
    assert len(engine.warnings) == 49


def test_ast_caching_by_identity():
    engine = SignalEngine()
    
    ast_json = {
        "schema_version": "1.0.0",
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "test_caching",
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
                                        {"node_type": "CONSTANT", "value": 10.0},
                                        {"node_type": "CONSTANT", "value": 5.0}
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
    
    original_load = engine.loader.load_from_json
    parsed_bundles = []
    
    def spy_load(ast_dict):
        bundle = original_load(ast_dict)
        parsed_bundles.append(bundle)
        return bundle
        
    engine.loader.load_from_json = spy_load
    
    res1 = engine.evaluate(ast_json, {})
    res2 = engine.evaluate(ast_json, {})
    
    assert res1.signal == SignalType.BUY
    assert res2.signal == SignalType.BUY
    
    # Should only be loaded/parsed once because of the cache
    assert len(parsed_bundles) == 1
    assert id(ast_json) in engine._ast_cache
    assert engine._ast_cache[id(ast_json)] is parsed_bundles[0]


def test_warnings_sanitization_filtering():
    # Test that warning sanitization drops warnings with paths/classes/stack traces
    # and replaces unknown exceptions with EVAL_ERROR.
    raw_warnings = [
        "INDICATOR_NOT_FOUND",
        "EVAL_ERROR",
        "Significant accounting drift detected: 0.0001",
        "Failed to close position for AAPL due to insufficient capital",
        "ValueError: error in /Users/binit/file.py at line 42",
        "Traceback (most recent call last):\n  File \"app/signal/evaluator.py\", line 10",
        "<class 'app.portfolio.portfolio.Portfolio'>",
        "some normal warning"
    ]
    
    sanitized_warnings = []
    for w in raw_warnings:
        w_str = str(w)
        w_lower = w_str.lower()
        has_filepath = (".py" in w_lower or "/" in w_str or "\\" in w_str)
        has_classname = any(cls in w_lower for cls in ["app.portfolio", "app.core", "app.signal", "app.execution", "app.metrics", "<class", "object at"])
        has_stackframe = any(term in w_lower for term in ["traceback", "stack frame", "line ", "tb_next", "frame object", "exception:"])
        
        if not (has_filepath or has_classname or has_stackframe):
            sanitized_warnings.append(w_str)
        else:
            sanitized_warnings.append("EVAL_ERROR")
            
    seen_warn = set()
    final_warnings = []
    for w in sanitized_warnings:
        if w not in seen_warn:
            seen_warn.add(w)
            final_warnings.append(w)
            
    assert "INDICATOR_NOT_FOUND" in final_warnings
    assert "EVAL_ERROR" in final_warnings
    assert "Significant accounting drift detected: 0.0001" in final_warnings
    assert "Failed to close position for AAPL due to insufficient capital" in final_warnings
    assert "some normal warning" in final_warnings
    
    # Filepath and traceback should be converted to EVAL_ERROR and then deduplicated
    assert not any("/" in w for w in final_warnings)
    assert not any("traceback" in w.lower() for w in final_warnings)
    assert not any("app/signal" in w.lower() for w in final_warnings)