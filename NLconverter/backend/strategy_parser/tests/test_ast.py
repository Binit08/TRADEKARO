"""Tests for deterministic Canonical JSON -> AST compilation."""

import tempfile
import unittest
from pathlib import Path

from backend.strategy_parser.ast import (
    ASTBuildError,
    ASTBuilder,
    ASTDebugger,
    ASTSerializer,
    ASTValidator,
)


class TestASTBuilder(unittest.TestCase):
    """AST builder tests."""

    def setUp(self):
        self.builder = ASTBuilder()

    def test_rsi_comparison_ast(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "LESS_THAN",
                    "operand_1": {
                        "type": "indicator",
                        "indicator_type": "RSI",
                        "parameters": {"period": 14},
                    },
                    "operand_2": {"type": "constant", "value": 30},
                }
            }
        }

        ast = self.builder.build(strategy, strategy_id="rsi")
        condition = ast.entry_node.children[0]

        self.assertEqual(ast.entry_node.node_type, "ENTRY")
        self.assertEqual(condition.node_type, "LESS_THAN")
        self.assertEqual(condition.children[0].node_type, "INDICATOR")
        self.assertEqual(condition.children[0].indicator_config.indicator_type, "RSI")
        self.assertEqual(condition.children[1].value, 30)

    def test_macd_greater_than_zero_ast(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "GT",
                    "operand_1": {
                        "type": "indicator",
                        "indicator_type": "MACD",
                        "parameters": {"fast": 12, "slow": 26, "signal": 9},
                        "property": "histogram",
                    },
                    "operand_2": {"type": "constant", "value": 0},
                }
            }
        }

        ast = self.builder.build(strategy, strategy_id="macd")
        condition = ast.entry_node.children[0]

        self.assertEqual(condition.node_type, "GREATER_THAN")
        self.assertEqual(condition.children[0].indicator_config.output_property, "histogram")
        self.assertEqual(condition.children[1].value, 0)

    def test_indicator_reference_resolves_from_settings_json(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "LESS_THAN",
                    "operand_1": {
                        "type": "indicator",
                        "indicator_ref": "rsi_ref",
                    },
                    "operand_2": {"type": "constant", "value": 30},
                }
            }
        }
        settings = {
            "signals": {
                "indicators": [
                    {
                        "id": "rsi_ref",
                        "indicator_type": "RSI",
                        "parameters": {"period": 14},
                        "timeframe": "1D",
                    }
                ]
            }
        }

        ast = self.builder.build(strategy, strategy_id="rsi_settings", settings_json=settings)
        condition = ast.entry_node.children[0]

        self.assertEqual(condition.node_type, "LESS_THAN")
        self.assertEqual(condition.children[0].node_type, "INDICATOR")
        self.assertEqual(condition.children[0].indicator_config.indicator_type, "RSI")
        self.assertEqual(condition.children[0].indicator_config.parameters["period"], 14)
        self.assertEqual(condition.children[0].indicator_config.timeframe, "1D")

    def test_multi_timeframe_strategy_support(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "CROSS_ABOVE",
                    "operand_1": {
                        "type": "indicator",
                        "indicator_ref": "rsi_daily",
                    },
                    "operand_2": {
                        "type": "indicator",
                        "indicator_ref": "rsi_hourly",
                    },
                }
            }
        }
        
        settings = {
            "execution_context": {
                "timeframe": "1D"  
            },
            "signals": {
                "indicators": [
                    {
                        "id": "rsi_daily",
                        "indicator_type": "RSI",
                        "timeframe": "1D",
                    },
                    {
                        "id": "rsi_hourly",
                        "indicator_type": "RSI",
                        "timeframe": "1H",
                    }
                ]
            }
        }

        ast = self.builder.build(strategy, strategy_id="mtf", settings_json=settings)
        cross = ast.entry_node.children[0]

        self.assertEqual(cross.node_type, "CROSS_ABOVE")
        self.assertEqual(cross.children[0].indicator_config.timeframe, "1D")
        self.assertEqual(cross.children[1].indicator_config.timeframe, "1H")

    def test_ema_cross_above_ast(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "CROSS_ABOVE",
                    "operand_1": {
                        "type": "indicator",
                        "indicator_type": "EMA",
                        "parameters": {"period": 50},
                    },
                    "operand_2": {
                        "type": "indicator",
                        "indicator_type": "EMA",
                        "parameters": {"period": 200},
                    },
                }
            }
        }

        ast = self.builder.build(strategy, strategy_id="ema_cross")
        cross = ast.entry_node.children[0]

        self.assertEqual(cross.node_type, "CROSS_ABOVE")
        self.assertEqual(cross.cross_type, "ABOVE")
        self.assertEqual(cross.children[0].indicator_config.parameters["period"], 50)
        self.assertEqual(cross.children[1].indicator_config.parameters["period"], 200)

    def test_abs_arithmetic_operand_single_object(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "LESS_THAN",
                    "operand_1": {
                        "type": "ARITHMETIC",
                        "operator": "ABS",
                        "operand": {
                            "type": "indicator",
                            "indicator_type": "MACD",
                            "property": "histogram",
                        },
                    },
                    "operand_2": {"type": "constant", "value": 0},
                }
            }
        }

        ast = self.builder.build(strategy, strategy_id="abs_operand")
        condition = ast.entry_node.children[0]

        self.assertEqual(condition.node_type, "LESS_THAN")
        self.assertEqual(condition.children[0].node_type, "ABS")
        self.assertEqual(condition.children[0].children[0].node_type, "INDICATOR")
        self.assertEqual(condition.children[0].children[0].indicator_config.output_property, "histogram")

    def test_nested_and_or_not_strategy(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "AND",
                    "children": [
                        {
                            "type": "OR",
                            "children": [
                                {
                                    "type": "LESS_THAN",
                                    "operand_1": {
                                        "type": "indicator",
                                        "indicator_type": "RSI",
                                        "parameters": {"period": 14},
                                    },
                                    "operand_2": {"type": "constant", "value": 30},
                                },
                                {
                                    "type": "GREATER_THAN",
                                    "operand_1": {
                                        "type": "indicator",
                                        "indicator_type": "MACD",
                                        "parameters": {"fast": 12, "slow": 26, "signal": 9},
                                        "property": "histogram",
                                    },
                                    "operand_2": {"type": "constant", "value": 0},
                                },
                            ],
                        },
                        {
                            "type": "NOT",
                            "child": {
                                "type": "SESSION",
                                "sessions": ["PRE_MARKET"],
                            },
                        },
                    ],
                }
            }
        }

        ast = self.builder.build(strategy, strategy_id="nested")
        counts = ASTDebugger.node_count(ast)

        self.assertEqual(ast.entry_node.children[0].node_type, "AND")
        self.assertEqual(counts["OR"], 1)
        self.assertEqual(counts["NOT"], 1)
        self.assertEqual(counts["SESSION"], 1)

    def test_strategy_with_stop_loss_and_take_profit(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "GREATER_THAN",
                    "operand_1": {
                        "type": "market_data",
                        "data_type": "close",
                    },
                    "operand_2": {
                        "type": "indicator",
                        "indicator_type": "SMA",
                        "parameters": {"period": 20},
                    },
                }
            },
            "risk": {
                "stop_loss": {"type": "PERCENTAGE", "value": 2.0},
                "take_profit": {"type": "PERCENTAGE", "value": 5.0},
            },
        }

        ast = self.builder.build(strategy, strategy_id="risk")

        self.assertEqual(ast.risk_node.node_type, "RISK")
        self.assertEqual([child.node_type for child in ast.risk_node.children], ["STOP_LOSS", "TAKE_PROFIT"])
        self.assertEqual(ast.risk_node.children[0].config.stop_loss_type, "PERCENTAGE")
        self.assertEqual(ast.risk_node.children[1].config.take_profit_type, "PERCENTAGE")

    def test_ast_generation_is_deterministic(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "GT",
                    "operand_1": {"type": "indicator", "indicator_type": "RSI"},
                    "operand_2": {"type": "constant", "value": 50},
                }
            }
        }

        first = ASTSerializer.to_json(ASTBuilder().build(strategy, strategy_id="det"))
        second = ASTSerializer.to_json(ASTBuilder().build(strategy, strategy_id="det"))

        self.assertEqual(first, second)

    def test_serializer_round_trips_versioned_json_and_file(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "CROSS_ABOVE",
                    "operand_1": {"type": "market_data", "data_type": "close"},
                    "operand_2": {
                        "type": "indicator",
                        "indicator_type": "EMA",
                        "parameters": {"period": 50},
                    },
                }
            },
            "risk": {
                "portfolio_constraints": {
                    "max_drawdown": 10.0,
                    "max_daily_loss": 5000,
                    "max_open_trades": 3,
                    "capital_allocation": 50.0,
                }
            },
        }
        ast = self.builder.build(strategy, strategy_id="roundtrip")
        expected = ASTSerializer.to_dict(ast)

        loaded = ASTSerializer.from_json(ASTSerializer.to_json(ast, include_version=True))
        self.assertEqual(ASTSerializer.to_dict(loaded), expected)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ast.json"
            ASTSerializer.to_file(ast, str(path))
            self.assertEqual(ASTSerializer.to_dict(ASTSerializer.from_file(str(path))), expected)

    def test_invalid_operand_error_includes_source_path(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "GREATER_THAN",
                    "operand_1": {"type": "indicator"},
                    "operand_2": {"type": "constant", "value": 0},
                }
            }
        }

        with self.assertRaises(ASTBuildError) as error:
            self.builder.build(strategy, strategy_id="bad")

        self.assertIn("conditions.entry.operand_1", str(error.exception))

    def test_validator_accepts_complete_ast(self):
        strategy = {
            "conditions": {
                "entry": {
                    "type": "GT",
                    "operand_1": {"type": "indicator", "indicator_type": "RSI"},
                    "operand_2": {"type": "constant", "value": 50},
                }
            }
        }

        ast = self.builder.build(strategy, strategy_id="valid")
        is_valid, errors = ASTValidator.validate(ast)

        self.assertTrue(is_valid, errors)

    def test_multiple_operations_linked_exits_ast(self):
        strategy = {
            "operation": [
                {
                    "entry": [
                        {
                            "type": "LESS_THAN",
                            "operand_1": {
                                "type": "indicator",
                                "indicator_type": "RSI",
                            },
                            "operand_2": {"type": "constant", "value": 30},
                        }
                    ],
                    "exit": [
                        {
                            "type": "GREATER_THAN",
                            "operand_1": {
                                "type": "indicator",
                                "indicator_type": "RSI",
                            },
                            "operand_2": {"type": "constant", "value": 70},
                        }
                    ]
                },
                {
                    "entry": [
                        {
                            "type": "CROSS_ABOVE",
                            "operand_1": {"type": "market_data", "data_type": "close"},
                            "operand_2": {
                                "type": "indicator",
                                "indicator_type": "EMA",
                            },
                        }
                    ],
                    "exit": [
                        {
                            "type": "CROSS_BELOW",
                            "operand_1": {"type": "market_data", "data_type": "close"},
                            "operand_2": {
                                "type": "indicator",
                                "indicator_type": "EMA",
                            },
                        }
                    ]
                }
            ]
        }

        ast = self.builder.build(strategy, strategy_id="multi_op")
        
        # Verify StrategyRootNode has 2 operation nodes
        self.assertEqual(len(ast.operation_nodes), 2)
        
        # Verify first operation
        op_1 = ast.operation_nodes[0]
        self.assertEqual(len(op_1.entry_nodes), 1)
        self.assertEqual(len(op_1.exit_nodes), 1)
        self.assertEqual(op_1.entry_nodes[0].children[0].node_type, "LESS_THAN")
        self.assertEqual(op_1.exit_nodes[0].children[0].node_type, "GREATER_THAN")
        
        # Verify second operation
        op_2 = ast.operation_nodes[1]
        self.assertEqual(len(op_2.entry_nodes), 1)
        self.assertEqual(len(op_2.exit_nodes), 1)
        self.assertEqual(op_2.entry_nodes[0].children[0].node_type, "CROSS_ABOVE")
        self.assertEqual(op_2.exit_nodes[0].children[0].node_type, "CROSS_BELOW")

        # Verify backward compatibility fields are None on root when using operations to avoid duplicate traversal
        self.assertIsNone(ast.entry_node)
        self.assertIsNone(ast.exit_node)

        # Verify serialization round-trips correctly
        serialized = ASTSerializer.to_dict(ast)
        self.assertIn("operation_nodes", serialized)
        self.assertEqual(len(serialized["operation_nodes"]), 2)
        
        deserialized = ASTSerializer.from_dict(serialized)
        self.assertEqual(len(deserialized.operation_nodes), 2)
        self.assertEqual(deserialized.operation_nodes[0].node_type, "OPERATION")


if __name__ == "__main__":
    unittest.main()

    def test_sequence_node_ast(self):
        canonical_json = {
            "operation": [
                {
                    "entry": [
                        {
                            "type": "SEQUENCE",
                            "direction": "BACKWARD",
                            "count": 5,
                            "condition": {
                                "type": "GREATER_THAN",
                                "operand_1": {
                                    "type": "market_data",
                                    "data_type": "CLOSE"
                                },
                                "operand_2": {
                                    "type": "market_data",
                                    "data_type": "OPEN"
                                }
                            }
                        }
                    ],
                    "exit": []
                }
            ],
            "risk": {},
            "signals": {}
        }
        
        builder = ASTBuilder()
        root = builder.build(canonical_json)
        
        entry_node = root.operation_nodes[0].entry_nodes[0]
        # The child of the ENTRY node should be the SEQUENCE node
        seq_node = entry_node.children[0]
        
        assert seq_node.node_type == "SEQUENCE"
        assert seq_node.count == 5
        assert seq_node.direction == "BACKWARD"
        
        # Check that its child is the GREATER_THAN condition
        condition_node = seq_node.children[0]
        assert condition_node.node_type == "GREATER_THAN"
        assert condition_node.children[0].node_type == "MARKET_REFERENCE"
