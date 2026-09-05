"""Tests for the typed AST loader."""

import pytest
from app.ast.loader import StrategyLoader, ASTLoadError
from app.ast.nodes import (
    StrategyRootNode, OperationNode, EntryNode, LogicNode, ComparisonNode,
    IndicatorNode, MarketReferenceNode, ConstantNode
)


def test_load_valid_strategy_bundle():
    raw_json = {
        "schema_version": "1.0.0",
        "execution_context": {
            "symbol": "RELIANCE.NS",
            "timeframe": "1D",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "capital_per_trade": {"amount": 50000},
            "position_side": "LONG",
            "order_type": "MARKET",
            "max_concurrent_positions": 1
        },
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "strategy_id": "test_strat",
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
                                            "node_type": "MARKET_REFERENCE",
                                            "data_type": "CLOSE",
                                            "lookback_periods": 0
                                        },
                                        {
                                            "node_type": "INDICATOR",
                                            "indicator_config": {
                                                "indicator_type": "SMA",
                                                "parameters": {"period": 52}
                                            }
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
    bundle = loader.load_from_json(raw_json)

    assert bundle.schema_version == "1.0.0"
    assert bundle.execution_context.symbol == "RELIANCE.NS"
    assert bundle.execution_context.capital == 50000.0

    ast = bundle.ast
    assert isinstance(ast, StrategyRootNode)
    assert ast.strategy_id == "test_strat"
    assert len(ast.operation_nodes) == 1

    op = ast.operation_nodes[0]
    assert isinstance(op, OperationNode)
    assert len(op.entry_nodes) == 1
    assert len(op.exit_nodes) == 0

    entry = op.entry_nodes[0]
    assert isinstance(entry, EntryNode)
    
    comp = entry.condition
    assert isinstance(comp, ComparisonNode)
    assert comp.operator == "GREATER_THAN"

    assert isinstance(comp.left, MarketReferenceNode)
    assert comp.left.data_type == "CLOSE"
    assert comp.left.lookback_periods == 0

    assert isinstance(comp.right, IndicatorNode)
    assert comp.right.config.indicator_type == "SMA"
    assert comp.right.config.period == 52


def test_missing_ast_raises_error():
    loader = StrategyLoader()
    with pytest.raises(ASTLoadError, match="Missing 'ast' root block"):
        loader.load_from_json({"execution_context": {}})


def test_missing_execution_context_provides_empty():
    loader = StrategyLoader()
    # Missing execution_context shouldn't raise, but it will raise on the invalid AST
    with pytest.raises(ASTLoadError, match="Unsupported node_type"):
        loader.load_from_json({"ast": {}})
