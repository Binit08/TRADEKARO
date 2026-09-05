"""Tests for the NLconverter AST schema path.

Covers:
- MARKET_REFERENCE resolution (current + lookback)
- INDICATOR resolution from indicator_config
- AND / OR logic gate evaluation
- entry_nodes → BUY, exit_nodes → SELL, neither → HOLD
- execution_context auto-apply (Option A)
- Full AST from strategy_ast_output.json
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest

from app.signal.signal_engine import SignalEngine
from app.signal.models import SignalType
from app.signal.evaluator import evaluate_ast_node, EvaluatorState
from app.config.settings import StrategySettings


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_market_data(close=100.0, high=105.0, low=95.0, open_=100.0, volume=1000.0):
    return {"CLOSE": close, "HIGH": high, "LOW": low, "OPEN": open_, "VOLUME": volume}


def _market_ref_node(data_type: str, lookback: int = 0) -> Dict[str, Any]:
    return {
        "node_type": "MARKET_REFERENCE",
        "data_type": data_type,
        "lookback_periods": lookback,
        "timeframe": "1D",
    }


def _indicator_node(indicator_type: str, period: int, output_property: str = "value") -> Dict[str, Any]:
    return {
        "node_type": "INDICATOR",
        "indicator_config": {
            "indicator_type": indicator_type,
            "output_property": output_property,
            "parameters": {"period": period},
            "timeframe": "1D",
        },
    }


def _comparison_node(node_type: str, left: Dict, right: Dict) -> Dict[str, Any]:
    return {"node_type": node_type, "children": [left, right]}


def _and_node(*children) -> Dict[str, Any]:
    return {"node_type": "AND", "children": list(children)}


def _or_node(*children) -> Dict[str, Any]:
    return {"node_type": "OR", "children": list(children)}


def _entry_node(logic_node: Dict) -> Dict[str, Any]:
    return {"node_type": "ENTRY", "children": [logic_node]}


def _exit_node(logic_node: Dict) -> Dict[str, Any]:
    return {"node_type": "EXIT", "children": [logic_node]}


def _nlconverter_ast(entry_nodes: list, exit_nodes: list) -> Dict[str, Any]:
    return {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "test_strategy",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": entry_nodes,
                    "exit_nodes": exit_nodes,
                }
            ],
            "filter_nodes": [],
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# evaluate_ast_node unit tests
# ─────────────────────────────────────────────────────────────────────────────


class TestMarketReferenceResolution:
    def test_close_current_bar(self):
        node = _market_ref_node("CLOSE", lookback=0)
        state = EvaluatorState(previous={})
        market_data = _make_market_data(close=150.0)
        # Wrap in GREATER_THAN to actually invoke the operand resolver
        gt_node = _comparison_node("GREATER_THAN", node, _market_ref_node("OPEN", 0))
        assert evaluate_ast_node(gt_node, {}, state, {"CLOSE": 150.0, "OPEN": 100.0}) is True

    def test_high_lookback_minus_one(self):
        """lookback_periods=-1 should read previous bar from state.previous."""
        prev_high_node = _market_ref_node("HIGH", lookback=-1)
        curr_high_node = _market_ref_node("HIGH", lookback=0)
        # previous HIGH = 110, current HIGH = 105 → previous > current → True
        state = EvaluatorState(previous={"MARKET_HIGH": 110.0})
        gt_node = _comparison_node("GREATER_THAN", prev_high_node, curr_high_node)
        assert evaluate_ast_node(gt_node, {}, state, {"HIGH": 105.0}) is True

    def test_missing_market_data_returns_false(self):
        node = _market_ref_node("CLOSE", lookback=0)
        gt_node = _comparison_node("GREATER_THAN", node, _market_ref_node("OPEN", 0))
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(gt_node, {}, state, None) is False


class TestIndicatorResolution:
    def test_sma_value_resolved(self):
        ind_node = _indicator_node("SMA", 52)
        close_node = _market_ref_node("CLOSE", 0)
        # CLOSE (150) > SMA(52) (120) → True
        gt_node = _comparison_node("GREATER_THAN", close_node, ind_node)
        state = EvaluatorState(previous={})
        indicators = {"SMA_TIMEPERIOD=52": 120.0}
        assert evaluate_ast_node(gt_node, indicators, state, {"CLOSE": 150.0}) is True

    def test_sma_value_resolved_false(self):
        ind_node = _indicator_node("SMA", 52)
        close_node = _market_ref_node("CLOSE", 0)
        gt_node = _comparison_node("GREATER_THAN", close_node, ind_node)
        state = EvaluatorState(previous={})
        indicators = {"SMA_TIMEPERIOD=52": 200.0}
        assert evaluate_ast_node(gt_node, indicators, state, {"CLOSE": 150.0}) is False

    def test_missing_indicator_returns_false(self):
        ind_node = _indicator_node("EMA", 20)
        close_node = _market_ref_node("CLOSE", 0)
        gt_node = _comparison_node("GREATER_THAN", close_node, ind_node)
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(gt_node, {}, state, {"CLOSE": 150.0}) is False


class TestLogicGates:
    def _always_true(self) -> Dict[str, Any]:
        """GREATER_THAN node that is always true: 100 > 50."""
        return _comparison_node(
            "GREATER_THAN",
            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 0},
            {"node_type": "MARKET_REFERENCE", "data_type": "LOW", "lookback_periods": 0},
        )

    def _always_false(self) -> Dict[str, Any]:
        """LESS_THAN node that is always false: 100 < 50."""
        return _comparison_node(
            "LESS_THAN",
            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 0},
            {"node_type": "MARKET_REFERENCE", "data_type": "LOW", "lookback_periods": 0},
        )

    def test_and_all_true(self):
        node = _and_node(self._always_true(), self._always_true())
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(node, {}, state, {"CLOSE": 100.0, "LOW": 50.0}) is True

    def test_and_one_false(self):
        node = _and_node(self._always_true(), self._always_false())
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(node, {}, state, {"CLOSE": 100.0, "LOW": 50.0}) is False

    def test_or_one_true(self):
        node = _or_node(self._always_false(), self._always_true())
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(node, {}, state, {"CLOSE": 100.0, "LOW": 50.0}) is True

    def test_or_all_false(self):
        node = _or_node(self._always_false(), self._always_false())
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(node, {}, state, {"CLOSE": 100.0, "LOW": 50.0}) is False

    def test_not_true_becomes_false(self):
        node = {"node_type": "NOT", "children": [self._always_true()]}
        state = EvaluatorState(previous={})
        assert evaluate_ast_node(node, {}, state, {"CLOSE": 100.0, "LOW": 50.0}) is False


# ─────────────────────────────────────────────────────────────────────────────
# SignalEngine — NLconverter schema integration tests
# ─────────────────────────────────────────────────────────────────────────────


def _buy_condition_ast() -> Dict[str, Any]:
    """CLOSE > SMA(52): entry condition."""
    return _nlconverter_ast(
        entry_nodes=[
            _entry_node(
                _comparison_node(
                    "GREATER_THAN",
                    _market_ref_node("CLOSE"),
                    _indicator_node("SMA", 52),
                )
            )
        ],
        exit_nodes=[],
    )


def _sell_condition_ast() -> Dict[str, Any]:
    """EXIT when CLOSE < SMA(52)."""
    return _nlconverter_ast(
        entry_nodes=[],
        exit_nodes=[
            _exit_node(
                _comparison_node(
                    "LESS_THAN",
                    _market_ref_node("CLOSE"),
                    _indicator_node("SMA", 52),
                )
            )
        ],
    )


def _both_conditions_ast() -> Dict[str, Any]:
    """Both entry and exit defined."""
    return _nlconverter_ast(
        entry_nodes=[
            _entry_node(
                _comparison_node("GREATER_THAN", _market_ref_node("CLOSE"), _indicator_node("SMA", 52))
            )
        ],
        exit_nodes=[
            _exit_node(
                _comparison_node("LESS_THAN", _market_ref_node("CLOSE"), _indicator_node("SMA", 52))
            )
        ],
    )


class TestSignalEngineNLconverterSchema:
    def test_entry_nodes_true_returns_buy(self):
        engine = SignalEngine()
        ast = _buy_condition_ast()
        indicators = {"SMA_TIMEPERIOD=52": 100.0}
        market_data = _make_market_data(close=120.0)
        assert engine.evaluate(ast, indicators, market_data=market_data).signal == SignalType.BUY

    def test_entry_nodes_false_returns_hold(self):
        engine = SignalEngine()
        ast = _buy_condition_ast()
        indicators = {"SMA_TIMEPERIOD=52": 150.0}
        market_data = _make_market_data(close=120.0)
        assert engine.evaluate(ast, indicators, market_data=market_data).signal == SignalType.HOLD

    def test_exit_nodes_true_returns_sell(self):
        engine = SignalEngine()
        ast = _sell_condition_ast()
        indicators = {"SMA_TIMEPERIOD=52": 150.0}
        market_data = _make_market_data(close=120.0)
        assert engine.evaluate(ast, indicators, market_data=market_data).signal == SignalType.SELL

    def test_exit_nodes_false_returns_hold(self):
        engine = SignalEngine()
        ast = _sell_condition_ast()
        indicators = {"SMA_TIMEPERIOD=52": 100.0}
        market_data = _make_market_data(close=120.0)
        assert engine.evaluate(ast, indicators, market_data=market_data).signal == SignalType.HOLD

    def test_entry_evaluated_before_exit(self):
        """When both entry and exit would fire, entry (BUY) wins."""
        # Both conditions True simultaneously — entry always checked first
        engine = SignalEngine()
        # entry: CLOSE > SMA  and  exit: CLOSE < SMA — can't both be true
        # so build a pathological: entry: CLOSE > LOW (always true), exit: CLOSE > LOW (always true)
        ast = _nlconverter_ast(
            entry_nodes=[
                _entry_node(
                    _comparison_node("GREATER_THAN", _market_ref_node("CLOSE"), _market_ref_node("LOW"))
                )
            ],
            exit_nodes=[
                _exit_node(
                    _comparison_node("GREATER_THAN", _market_ref_node("CLOSE"), _market_ref_node("LOW"))
                )
            ],
        )
        market_data = _make_market_data(close=120.0, low=90.0)
        assert engine.evaluate(ast, {}, market_data=market_data).signal == SignalType.BUY

    def test_empty_operation_nodes_returns_hold(self):
        ast = {"ast": {"node_type": "STRATEGY_ROOT", "operation_nodes": [], "filter_nodes": []}}
        engine = SignalEngine()
        assert engine.evaluate(ast, {}, market_data=_make_market_data()).signal == SignalType.HOLD

    def test_market_data_stored_in_previous_for_next_bar(self):
        """After evaluation, market data appears in previous_indicators for next bar lookback."""
        engine = SignalEngine()
        ast = _nlconverter_ast(entry_nodes=[], exit_nodes=[])
        market_data = _make_market_data(close=150.0, high=160.0)
        engine.evaluate(ast, {}, market_data=market_data)
        assert engine.previous_indicators.get("MARKET_CLOSE") == pytest.approx(150.0)
        assert engine.previous_indicators.get("MARKET_HIGH") == pytest.approx(160.0)


# ─────────────────────────────────────────────────────────────────────────────
# execution_context → StrategySettings (Option A)
# ─────────────────────────────────────────────────────────────────────────────


class TestExecutionContextAutoApply:
    def test_from_execution_context_basic(self):
        ctx = {
            "order_type": "MARKET",
            "capital_per_trade": {"amount": 100000, "currency": "INR"},
            "position_side": "LONG",
            "max_concurrent_positions": 5,
        }
        settings = StrategySettings.from_execution_context(ctx)
        assert settings.order_type == "MARKET"
        assert settings.position_size == pytest.approx(100000.0)
        assert settings.position_size_type == "cash"
        assert settings.allow_short is False
        assert settings.pyramiding == 4  # 5 - 1

    def test_from_execution_context_short_side(self):
        ctx = {"position_side": "SHORT", "capital_per_trade": {"amount": 50000}}
        settings = StrategySettings.from_execution_context(ctx)
        assert settings.allow_short is True
        assert settings.position_size == pytest.approx(50000.0)

    def test_execution_context_merges_into_base(self):
        base = StrategySettings(commission_rate=0.001, slippage_bps=5.0)
        ctx = {"order_type": "LIMIT", "capital_per_trade": {"amount": 200000}}
        settings = StrategySettings.from_execution_context(ctx, base=base)
        assert settings.order_type == "LIMIT"
        assert settings.commission_rate == pytest.approx(0.001)  # kept from base
        assert settings.position_size == pytest.approx(200000.0)

    def test_auto_apply_via_ast_bundle(self):
        """execution_context embedded in the AST dict is auto-applied by BacktestEngine."""
        from app.core.backtest_engine import BacktestEngine
        from app.core.historical_feed import HistoricalReplayFeed
        from app.data.market_event import MarketEvent
        from app.execution.simulator import ExecutionEngine
        from app.indicators.indicator_engine import IndicatorEngine
        from app.metrics.metrics_engine import MetricsEngine
        from app.portfolio.portfolio import Portfolio

        class _FixedLoader:
            def load(self, *a, **kw):
                base = datetime(2024, 1, 1)
                return [
                    MarketEvent("TEST", base + timedelta(days=i), 100, 101, 99, 100, 1000)
                    for i in range(5)
                ]

        engine = BacktestEngine(
            loader=_FixedLoader(),
            feed=HistoricalReplayFeed,
            indicator=IndicatorEngine(),
            signal=SignalEngine(),
            execution=ExecutionEngine(qty=1.0),
            portfolio=Portfolio(initial_cash=500000.0),
            metrics=MetricsEngine(),
        )

        ast_bundle = {
            "ast": {
                "node_type": "STRATEGY_ROOT",
                "operation_nodes": [{"node_type": "OPERATION", "entry_nodes": [], "exit_nodes": []}],
                "filter_nodes": [],
            },
            "execution_context": {
                "order_type": "MARKET",
                "capital_per_trade": {"amount": 100000, "currency": "INR"},
                "position_side": "LONG",
                "max_concurrent_positions": 5,
            },
        }

        result = engine.run(["TEST"], "2024-01-01", "2024-12-31", "1d", ast_bundle)
        # Settings should have been auto-applied; position_size = 100000
        assert result["settings"]["position_size"] == pytest.approx(100000.0)
        assert result["settings"]["position_size_type"] == "cash"


# ─────────────────────────────────────────────────────────────────────────────
# Full NLconverter AST from strategy_ast_output.json
# ─────────────────────────────────────────────────────────────────────────────


class TestFullNLconverterAstFromFile:
    """Load the real strategy_ast_output.json from the NLconverter repo and
    verify the signal engine can evaluate it without raising errors."""

    NLCONVERTER_AST_PATH = Path("/Users/binit/NLconverter/backend/strategy_ast_output.json")

    @pytest.mark.skipif(
        not NLCONVERTER_AST_PATH.exists(),
        reason="NLconverter strategy_ast_output.json not found",
    )
    def test_evaluates_without_error(self):
        with self.NLCONVERTER_AST_PATH.open("r", encoding="utf-8") as fh:
            ast = json.load(fh)

        engine = SignalEngine()
        # Simulate an indicator snapshot for the SMA(52) referenced in the AST
        indicators = {"SMA_TIMEPERIOD=52": 100.0}

        # Bar where CLOSE > SMA(52) and today's HIGH > yesterday's HIGH
        market_data = _make_market_data(close=120.0, high=130.0)

        # Warm up previous state (yesterday HIGH = 115)
        engine.previous_indicators["MARKET_HIGH"] = 115.0

        signal = engine.evaluate(ast, indicators, market_data=market_data)
        # CLOSE(120) > SMA(130=no, 100=yes) and HIGH[0](130) > HIGH[-1](115) → should be BUY
        assert signal.signal in {SignalType.BUY, SignalType.SELL, SignalType.HOLD}

    @pytest.mark.skipif(
        not NLCONVERTER_AST_PATH.exists(),
        reason="NLconverter strategy_ast_output.json not found",
    )
    def test_buy_signal_when_conditions_met(self):
        """Both entry conditions (CLOSE > SMA, HIGH[-1] > HIGH[0]) should yield BUY.

        The AST's second condition compares HIGH with lookback=-1 (left) vs
        HIGH with lookback=0 (right), meaning: yesterday's high > today's high.
        """
        with self.NLCONVERTER_AST_PATH.open("r", encoding="utf-8") as fh:
            ast = json.load(fh)

        engine = SignalEngine()
        indicators = {"SMA_SOURCE=close_TIMEPERIOD=52": 100.0}  # CLOSE(120) > SMA(100) ✓
        market_data = _make_market_data(close=120.0, high=100.0)  # today HIGH = 100
        engine.previous_indicators["MARKET_HIGH"] = 130.0  # yesterday HIGH = 130 > today ✓

        signal = engine.evaluate(ast, indicators, market_data=market_data)
        assert signal.signal == SignalType.BUY

    @pytest.mark.skipif(
        not NLCONVERTER_AST_PATH.exists(),
        reason="NLconverter strategy_ast_output.json not found",
    )
    def test_hold_signal_when_conditions_not_met(self):
        """CLOSE < SMA should yield HOLD (entry false, no exit defined)."""
        with self.NLCONVERTER_AST_PATH.open("r", encoding="utf-8") as fh:
            ast = json.load(fh)

        engine = SignalEngine()
        indicators = {"SMA_TIMEPERIOD=52": 200.0}  # CLOSE(120) > SMA(200) ✗ — first condition fails
        market_data = _make_market_data(close=120.0, high=130.0)

        signal = engine.evaluate(ast, indicators, market_data=market_data)
        assert signal.signal == SignalType.HOLD
