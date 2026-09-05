#!/usr/bin/env python3
"""
AST Example - Demonstrate AST building from Canonical JSON
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.strategy_parser.ast import (
    ASTBuilder,
    ASTSerializer,
    ASTValidator,
    ASTDebugger,
    ASTAnalyzer,
)


def example_rsi_strategy():
    """Example 1: Simple RSI > 30 strategy"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple RSI > 30 Strategy")
    print("="*80)
    
    canonical_json = {
        "conditions": {
            "entry": {
                "type": "GT",
                "operand_1": {
                    "type": "indicator",
                    "indicator_type": "RSI",
                    "parameters": {"period": 14},
                    "property": "value"
                },
                "operand_2": {
                    "type": "constant",
                    "value": 30
                }
            },
            "exit": {
                "type": "LT",
                "operand_1": {
                    "type": "indicator",
                    "indicator_type": "RSI",
                    "parameters": {"period": 14},
                    "property": "value"
                },
                "operand_2": {
                    "type": "constant",
                    "value": 70
                }
            }
        }
    }
    
    # Build AST
    builder = ASTBuilder()
    ast_root = builder.build(canonical_json, strategy_id="rsi_simple")
    
    print("\n✓ AST built successfully")
    print(f"Root node: {ast_root.node_type} ({ast_root.node_id})")
    print(f"Entry node: {ast_root.entry_node.node_type if ast_root.entry_node else None}")
    print(f"Exit node: {ast_root.exit_node.node_type if ast_root.exit_node else None}")
    
    # Validate
    is_valid, errors = ASTValidator.validate(ast_root)
    print(f"\n✓ Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # Print tree
    print("\n--- AST Tree Structure ---")
    ASTDebugger.print_tree(ast_root)
    
    # Print stats
    ASTDebugger.print_stats(ast_root)
    
    # Metrics
    ASTAnalyzer.print_metrics(ast_root)
    
    # Serialize
    print("\n--- Serialized JSON ---")
    ast_dict = ASTSerializer.to_dict(ast_root)
    print(json.dumps(ast_dict, indent=2, default=str)[:500] + "...")
    
    return ast_root


def example_ema_crossover():
    """Example 2: EMA crossover strategy"""
    print("\n" + "="*80)
    print("EXAMPLE 2: EMA Crossover (EMA50 > EMA200)")
    print("="*80)
    
    canonical_json = {
        "conditions": {
            "entry": {
                "type": "CROSS_ABOVE",
                "operand_1": {
                    "type": "indicator",
                    "indicator_type": "EMA",
                    "parameters": {"period": 50},
                    "property": "value"
                },
                "operand_2": {
                    "type": "indicator",
                    "indicator_type": "EMA",
                    "parameters": {"period": 200},
                    "property": "value"
                },
                "lookback_periods": 1
            }
        }
    }
    
    builder = ASTBuilder()
    ast_root = builder.build(canonical_json, strategy_id="ema_crossover")
    
    print("\n✓ AST built successfully")
    print("\n--- AST Tree Structure ---")
    ASTDebugger.print_tree(ast_root)
    
    ASTDebugger.print_stats(ast_root)
    
    return ast_root


def example_complex_nested():
    """Example 3: Complex nested strategy"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Complex Nested Strategy (RSI < 30 AND MACD > 0)")
    print("="*80)
    
    canonical_json = {
        "conditions": {
            "entry": {
                "type": "AND",
                "children": [
                    {
                        "type": "LT",
                        "operand_1": {
                            "type": "indicator",
                            "indicator_type": "RSI",
                            "parameters": {"period": 14},
                            "property": "value"
                        },
                        "operand_2": {"type": "constant", "value": 30}
                    },
                    {
                        "type": "CROSS_ABOVE",
                        "operand_1": {
                            "type": "indicator",
                            "indicator_type": "MACD",
                            "parameters": {"fast": 12, "slow": 26, "signal": 9},
                            "property": "histogram"
                        },
                        "operand_2": {"type": "constant", "value": 0}
                    }
                ]
            }
        },
        "risk": {
            "stop_loss": {
                "type": "PERCENTAGE",
                "value": 2.0,
                "reference": "entry_price"
            },
            "take_profit": {
                "type": "RISK_REWARD",
                "value": 3.0,
                "risk_reward_ratio": 3.0
            }
        }
    }
    
    builder = ASTBuilder()
    ast_root = builder.build(canonical_json, strategy_id="complex_nested")
    
    print("\n✓ AST built successfully")
    print("\n--- AST Tree Structure ---")
    ASTDebugger.print_tree(ast_root)
    
    ASTDebugger.print_stats(ast_root)
    ASTAnalyzer.print_metrics(ast_root)
    
    # Generate Mermaid diagram
    print("\n--- Mermaid Diagram ---")
    mermaid = ASTDebugger.to_mermaid(ast_root, "Complex Strategy")
    print(mermaid)
    
    return ast_root


def example_with_risk_management():
    """Example 4: Strategy with risk management"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Strategy with Risk Management")
    print("="*80)
    
    canonical_json = {
        "conditions": {
            "entry": {
                "type": "GT",
                "operand_1": {
                    "type": "indicator",
                    "indicator_type": "RSI",
                    "parameters": {"period": 14},
                    "property": "value"
                },
                "operand_2": {"type": "constant", "value": 50}
            }
        },
        "risk": {
            "stop_loss": {
                "type": "PERCENTAGE",
                "value": 2.0
            },
            "take_profit": {
                "type": "PERCENTAGE",
                "value": 5.0
            },
            "position_size": {
                "type": "PERCENTAGE_OF_CAPITAL",
                "value": 1.0,
                "max_size": 10000,
                "min_size": 100
            },
            "portfolio_constraints": {
                "max_drawdown": 10.0,
                "max_daily_loss": 5000,
                "max_open_trades": 5
            }
        }
    }
    
    builder = ASTBuilder()
    ast_root = builder.build(canonical_json, strategy_id="with_risk")
    
    print("\n✓ AST built successfully")
    print("\n--- AST Tree Structure ---")
    ASTDebugger.print_tree(ast_root)
    
    ASTDebugger.print_stats(ast_root)
    
    # Full serialization
    print("\n--- Full Serialized AST ---")
    ast_dict = ASTSerializer.to_dict(ast_root)
    print(json.dumps(ast_dict, indent=2, default=str))
    
    return ast_root


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("AST ARCHITECTURE - COMPLETE EXAMPLES")
    print("="*80)
    
    try:
        # Run examples
        example_rsi_strategy()
        example_ema_crossover()
        example_complex_nested()
        example_with_risk_management()
        
        print("\n" + "="*80)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
