"""Tests for the typed signal evaluator."""

import pytest
from app.signal.evaluator import SignalEvaluator
from app.signal.models import SignalType
from app.ast.nodes import (
    OperationNode, EntryNode, ComparisonNode, MarketReferenceNode,
    IndicatorNode, IndicatorConfig, CrossNode, ExitNode, ConstantNode
)


def test_evaluator_buy_signal():
    # CLOSE > SMA(52)
    entry = EntryNode(
        condition=ComparisonNode(
            operator="GREATER_THAN",
            left=MarketReferenceNode(data_type="CLOSE"),
            right=IndicatorNode(config=IndicatorConfig(indicator_type="SMA", period=52))
        )
    )
    operation = OperationNode(entry_nodes=[entry], exit_nodes=[])
    
    evaluator = SignalEvaluator()
    market_data = {"CLOSE": 150.0}
    indicators = {"SMA_TIMEPERIOD=52": 120.0}
    
    signal = evaluator.evaluate(operation, indicators, market_data)
    assert signal.signal == SignalType.BUY


def test_evaluator_hold_signal():
    # CLOSE > SMA(52)
    entry = EntryNode(
        condition=ComparisonNode(
            operator="GREATER_THAN",
            left=MarketReferenceNode(data_type="CLOSE"),
            right=IndicatorNode(config=IndicatorConfig(indicator_type="SMA", period=52))
        )
    )
    operation = OperationNode(entry_nodes=[entry], exit_nodes=[])
    
    evaluator = SignalEvaluator()
    market_data = {"CLOSE": 100.0}
    indicators = {"SMA_TIMEPERIOD=52": 120.0}  # False
    
    signal = evaluator.evaluate(operation, indicators, market_data)
    assert signal.signal == SignalType.HOLD


def test_evaluator_sell_signal():
    # CLOSE < SMA(52)
    exit_node = ExitNode(
        condition=ComparisonNode(
            operator="LESS_THAN",
            left=MarketReferenceNode(data_type="CLOSE"),
            right=IndicatorNode(config=IndicatorConfig(indicator_type="SMA", period=52))
        )
    )
    operation = OperationNode(entry_nodes=[], exit_nodes=[exit_node])
    
    evaluator = SignalEvaluator()
    market_data = {"CLOSE": 100.0}
    indicators = {"SMA_TIMEPERIOD=52": 120.0}
    
    signal = evaluator.evaluate(operation, indicators, market_data)
    assert signal.signal == SignalType.SELL


def test_evaluator_cross_above():
    # CLOSE crosses above SMA(52)
    entry = EntryNode(
        condition=CrossNode(
            cross_type="ABOVE",
            left=MarketReferenceNode(data_type="CLOSE"),
            right=IndicatorNode(config=IndicatorConfig(indicator_type="SMA", period=52))
        )
    )
    operation = OperationNode(entry_nodes=[entry], exit_nodes=[])
    evaluator = SignalEvaluator()
    
    # Previous state (t-1): CLOSE=90, SMA=100 (Below)
    evaluator.previous_state = {
        "MARKET_CLOSE": 90.0,
        "SMA_TIMEPERIOD=52": 100.0
    }
    
    # Current state (t): CLOSE=110, SMA=105 (Above)
    market_data = {"CLOSE": 110.0}
    indicators = {"SMA_TIMEPERIOD=52": 105.0}
    
    signal = evaluator.evaluate(operation, indicators, market_data)
    assert signal.signal == SignalType.BUY
    
    # Check state was updated
    assert evaluator.previous_state["MARKET_CLOSE"] == 110.0
    assert evaluator.previous_state["SMA_TIMEPERIOD=52"] == 105.0


def test_evaluator_constant_node():
    # CLOSE > 100
    entry = EntryNode(
        condition=ComparisonNode(
            operator="GREATER_THAN",
            left=MarketReferenceNode(data_type="CLOSE"),
            right=ConstantNode(value=100.0)
        )
    )
    operation = OperationNode(entry_nodes=[entry], exit_nodes=[])
    evaluator = SignalEvaluator()
    
    assert evaluator.evaluate(operation, {}, {"CLOSE": 105.0}).signal == SignalType.BUY
    assert evaluator.evaluate(operation, {}, {"CLOSE": 95.0}).signal == SignalType.HOLD

def test_evaluator_sequence_node():
    from app.ast.nodes import SequenceNode, ComparisonNode, MarketReferenceNode
    from app.signal.evaluator import SignalEvaluator

    evaluator = SignalEvaluator()
    
    # Condition: CLOSE > OPEN
    close_ref = MarketReferenceNode(data_type="CLOSE", lookback_periods=0, timeframe="1m")
    open_ref = MarketReferenceNode(data_type="OPEN", lookback_periods=0, timeframe="1m")
    cond = ComparisonNode(operator="GREATER_THAN", left=close_ref, right=open_ref)
    
    # Sequence: 3 consecutive candles where CLOSE > OPEN
    seq_node = SequenceNode(direction="BACKWARD", condition=cond, count=3)
    
    # Provide history by evaluating dummy ASTs (to populate evaluator history)
    # We'll just call evaluator._eval_node to push to history directly?
    # No, history is updated in evaluate() but we can manually populate it
    evaluator.history.append(({}, {"OPEN": 100, "CLOSE": 90}))  # Candle 1: down
    evaluator.history.append(({}, {"OPEN": 100, "CLOSE": 110})) # Candle 2: up
    evaluator.history.append(({}, {"OPEN": 100, "CLOSE": 110})) # Candle 3: up
    evaluator.history.append(({}, {"OPEN": 100, "CLOSE": 110})) # Candle 4: up
    
    # Check at offset 0 (which evaluates index 0, 1, 2 = candles 4, 3, 2 in history)
    # wait, idx = current_offset + offset.
    # length of history = 4. len(history) - 1 = 3.
    # self.history[-(idx+1)] is used for market reference.
    # For offset=0 (current), total_lookback = 0 + 0 = 0 -> history[-1]
    # For offset=1, total_lookback = 1 + 0 = 1 -> history[-2]
    # For offset=2, total_lookback = 2 + 0 = 2 -> history[-3]
    
    result = evaluator._eval_node(seq_node, current_offset=0)
    assert result is True
    
    # If we evaluate at offset=1, it checks history[-2], history[-3], history[-4]
    # history[-4] is Candle 1 which is down (90 > 100 is False)
    result_prev = evaluator._eval_node(seq_node, current_offset=1)
    assert result_prev is False


def test_previous_state_setter_does_not_grow_history() -> None:
    from app.ast.nodes import OperationNode
    dummy_op = OperationNode(entry_nodes=[], exit_nodes=[])
    evaluator = SignalEvaluator()
    
    assert len(evaluator.history) == 0
    
    # 1. First set of previous_state when history is empty should append
    evaluator.previous_state = {"MARKET_CLOSE": 100.0}
    assert len(evaluator.history) == 1
    
    # 2. Second set of previous_state should REPLACE the last item, not append
    evaluator.previous_state = {"MARKET_CLOSE": 105.0}
    assert len(evaluator.history) == 1
    assert evaluator.previous_state["MARKET_CLOSE"] == 105.0
    
    # 3. Running evaluate should grow history by exactly one
    len_before = len(evaluator.history)
    evaluator.evaluate(dummy_op, {}, {"CLOSE": 110.0})
    assert len(evaluator.history) == len_before + 1
    
    # 4. Modifying previous_state now should still replace the last item (length unchanged)
    evaluator.previous_state = {"MARKET_CLOSE": 115.0}
    assert len(evaluator.history) == len_before + 1
    assert evaluator.previous_state["MARKET_CLOSE"] == 115.0
    
    # 5. Running evaluate again should grow history by exactly one
    len_before = len(evaluator.history)
    evaluator.evaluate(dummy_op, {}, {"CLOSE": 120.0})
    assert len(evaluator.history) == len_before + 1
    
    # 6. Modifying previous_state and evaluating multiple times to guarantee exactly one increase per evaluate()
    for i in range(5):
        len_before = len(evaluator.history)
        evaluator.previous_state = {"MARKET_CLOSE": 130.0 + i}
        assert len(evaluator.history) == len_before
        evaluator.evaluate(dummy_op, {}, {"CLOSE": 140.0 + i})
        assert len(evaluator.history) == len_before + 1



