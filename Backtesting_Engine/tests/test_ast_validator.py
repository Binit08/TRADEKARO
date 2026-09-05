"""Unit tests for AST validator recursively validating node types and paths."""
import pytest
from app.ast.validator import validate

def test_legacy_flat_ast_passes():
    # Legacy flat AST does not contain top-level "ast" key
    legacy_ast = {
        "operator": "AND",
        "conditions": [
            {"left": "EMA", "operator": "<", "right": 102}
        ],
        "signal": "BUY"
    }
    # Should pass without raising exceptions
    validate(legacy_ast)

def test_valid_hierarchical_ast_passes():
    valid_ast = {
        "schema_version": "1.0.0",
        "execution_context": {
            "symbol": "AAPL",
            "timeframe": "1D"
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
                                    "node_type": "CROSS_ABOVE",
                                    "children": [
                                        {
                                            "node_type": "MARKET_REFERENCE",
                                            "data_type": "CLOSE"
                                        },
                                        {
                                            "node_type": "CONSTANT",
                                            "value": 100.0
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "exit_nodes": []
                }
            ],
            "variable_nodes": []
        }
    }
    # Should pass
    validate(valid_ast)

def test_non_dict_ast_raises():
    with pytest.raises(ValueError, match="AST must be a dictionary"):
        validate([1, 2, 3]) # type: ignore

def test_non_dict_ast_core_raises():
    with pytest.raises(ValueError, match="'ast' field must be a dictionary"):
        validate({"ast": "not-a-dict"})

def test_invalid_node_type_raises_with_path():
    ast_with_invalid_node = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [
                                {
                                    "node_type": "INVALID_NODE_TYPE", # Offending node
                                    "children": []
                                }
                            ]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    expected_path = "ast.operation_nodes\\[0\\].entry_nodes\\[0\\].children\\[0\\]"
    with pytest.raises(ValueError, match=f"Unsupported node_type: INVALID_NODE_TYPE at '{expected_path}'"):
        validate(ast_with_invalid_node)

def test_non_dict_node_raises_with_path():
    ast_with_non_dict_node = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [
                                "this-is-a-string-instead-of-dict" # Offending child
                            ]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    expected_path = "ast.operation_nodes\\[0\\].entry_nodes\\[0\\].children\\[0\\]"
    with pytest.raises(ValueError, match=f"Node at '{expected_path}' must be a dictionary"):
        validate(ast_with_non_dict_node)

def test_invalid_node_properties_raises():
    # 1. operation_nodes is not a list
    ast1 = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "operation_nodes": "not-a-list"
        }
    }
    with pytest.raises(ValueError, match="'operation_nodes' must be a list at 'ast'"):
        validate(ast1)

    # 2. SEQUENCE node missing condition
    ast2 = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": [
                                {
                                    "node_type": "SEQUENCE" # missing condition
                                }
                            ]
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    expected_path = "ast.operation_nodes\\[0\\].entry_nodes\\[0\\].children\\[0\\]"
    with pytest.raises(ValueError, match=f"SEQUENCE node missing 'condition' at '{expected_path}'"):
        validate(ast2)

    # 3. children not a list
    ast3 = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "operation_nodes": [
                {
                    "node_type": "OPERATION",
                    "entry_nodes": [
                        {
                            "node_type": "ENTRY",
                            "children": "not-a-list"
                        }
                    ],
                    "exit_nodes": []
                }
            ]
        }
    }
    expected_path = "ast.operation_nodes\\[0\\].entry_nodes\\[0\\]"
    with pytest.raises(ValueError, match=f"'children' must be a list at '{expected_path}'"):
        validate(ast3)
