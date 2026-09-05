#!/usr/bin/env python3
"""Run the full strategy pipeline: natural language -> canonical JSON -> AST."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add the project root (parent of 'backend') to sys.path so 'backend.x' imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.strategy_parser import load_dotenv
from backend.strategy_parser.parser.llm_client import LLMClient
from backend.strategy_parser.parser.strategy_parser import StrategyParser
from backend.strategy_parser.parser.validator import StrategyValidator
from backend.strategy_parser.ast import (
    ASTBuildError,
    ASTBuilder,
    ASTDebugger,
    ASTSerializer,
    ASTValidator as CoreASTValidator,
)
from backend.strategy_parser.pipeline import (
    BlockerDetector,
    SemanticResolver,
    StrategyCompiler,
    SchemaValidator,
    ASTGenerator,
    ASTValidatorStep,
    Auditor,
    PipelineOrchestrator,
)


DEFAULT_STRATEGY = """
Buy when RSI drops below 30 on daily timeframe and MACD histogram crosses above zero.
Sell when RSI rises above 70.
Use a 2% stop loss and take profit at 3:1 risk/reward.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a trading strategy into Canonical JSON and AST."
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--strategy",
        help="Natural-language strategy text to send to the LLM.",
    )
    input_group.add_argument(
        "--strategy-file",
        help="Path to a text file containing natural-language strategy text.",
    )
    input_group.add_argument(
        "--canonical-json",
        help="Path to existing Canonical JSON. Skips the LLM call.",
    )
    parser.add_argument(
        "--deterministic-schema",
        help="Path to deterministic schema JSON with timeframe, market type, etc.",
    )
    parser.add_argument(
        "--settings-json",
        help="Deprecated alias for --deterministic-schema.",
    )
    parser.add_argument(
        "--strategy-id",
        default="demo_strategy",
        help="Strategy id used in the AST root.",
    )
    parser.add_argument(
        "--canonical-out",
        default="parsed_strategy_output.json",
        help="Where to save Canonical JSON.",
    )
    parser.add_argument(
        "--ast-out",
        default="strategy_ast_output.json",
        help="Where to save versioned AST JSON.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print output only; do not write output files.",
    )
    parser.add_argument(
        "--ast-json",
        action="store_true",
        help="Also print full serialized AST JSON.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in non-interactive headless mode.",
    )
    return parser.parse_args()


def load_strategy_text(args: argparse.Namespace) -> str:
    if args.strategy:
        return args.strategy
    if args.strategy_file:
        return Path(args.strategy_file).read_text(encoding="utf-8")
    return DEFAULT_STRATEGY.strip()



def load_deterministic_schema(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    det_path = getattr(args, "deterministic_schema", None) or getattr(args, "settings_json", None)
    if det_path is None:
        return None
    path = Path(det_path)
    if not path.exists():
        raise FileNotFoundError(f"Deterministic schema file not found: {path}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    _validate_deterministic_schema(schema)
    return schema


def _validate_deterministic_schema(schema: Dict[str, Any]) -> None:
    """Validate deterministic schema values at load time."""
    ctx = schema.get("execution_context")
    if ctx is None:
        raise ValueError("Deterministic schema must contain 'execution_context'")
    if not isinstance(ctx, dict):
        raise ValueError("'execution_context' must be an object")

    # max_concurrent_positions: positive integer, 1–100
    mcp = ctx.get("max_concurrent_positions")
    if mcp is not None:
        if not isinstance(mcp, int) or isinstance(mcp, bool):
            raise ValueError(f"max_concurrent_positions must be an integer, got {type(mcp).__name__}")
        if mcp < 1 or mcp > 100:
            raise ValueError(f"max_concurrent_positions must be between 1 and 100, got {mcp}")

    # capital_per_trade.amount: positive number
    cpt = ctx.get("capital_per_trade")
    if isinstance(cpt, dict):
        amount = cpt.get("amount")
        if amount is not None and (not isinstance(amount, (int, float)) or amount <= 0):
            raise ValueError(f"capital_per_trade.amount must be a positive number, got {amount}")

    # timeframe: allowed values
    valid_timeframes = {"1m", "5m", "15m", "30m", "1h", "4h", "1D", "1W", "1M"}
    tf = ctx.get("timeframe")
    if tf is not None and tf not in valid_timeframes:
        raise ValueError(f"timeframe must be one of {sorted(valid_timeframes)}, got '{tf}'")

    # position_side: allowed values
    valid_sides = {"LONG", "SHORT", "BOTH"}
    ps = ctx.get("position_side")
    if ps is not None and ps not in valid_sides:
        raise ValueError(f"position_side must be one of {sorted(valid_sides)}, got '{ps}'")

    # order_type: allowed values
    valid_orders = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"}
    ot = ctx.get("order_type")
    if ot is not None and ot not in valid_orders:
        raise ValueError(f"order_type must be one of {sorted(valid_orders)}, got '{ot}'")


def save_outputs(
    canonical_json: Dict[str, Any],
    ast_json: str,
    canonical_path: str,
    ast_path: str,
) -> None:
    Path(canonical_path).write_text(
        json.dumps(canonical_json, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    Path(ast_path).write_text(ast_json, encoding="utf-8")


def print_canonical(canonical_json: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("CANONICAL JSON")
    print("=" * 80)
    print(json.dumps(canonical_json, indent=2, sort_keys=True))


def build_ast(
    canonical_json: Dict[str, Any],
    strategy_id: str,
    deterministic_schema: Optional[Dict[str, Any]] = None,
):
    builder = ASTBuilder()
    return builder.build(
        canonical_json,
        strategy_id=strategy_id,
        deterministic_schema=deterministic_schema,
    )


def main() -> int:
    args = parse_args()

    # Make .env path absolute relative to the script's directory
    backend_dir = Path(__file__).parent
    load_dotenv(str(backend_dir / ".env"))

    strategy_text = load_strategy_text(args)
    deterministic_schema = load_deterministic_schema(args)

    print("=" * 80)
    print("NATURAL LANGUAGE STRATEGY")
    print("=" * 80)
    print(strategy_text.strip())

    try:
        # Initialize pipeline components
        llm_client = LLMClient()
        blocker_detector = BlockerDetector(llm_client)
        semantic_resolver = SemanticResolver(llm_client)
        
        strategy_parser = StrategyParser()
        compiler = StrategyCompiler(strategy_parser)
        
        schema_validator = SchemaValidator(StrategyValidator())
        ast_generator = ASTGenerator(ASTBuilder())
        ast_validator = ASTValidatorStep()
        auditor = Auditor()
        
        orchestrator = PipelineOrchestrator(
            blocker_detector=blocker_detector,
            semantic_resolver=semantic_resolver,
            compiler=compiler,
            schema_validator=schema_validator,
            ast_generator=ast_generator,
            ast_validator=ast_validator,
            auditor=auditor
        )

        # Run pipeline
        ast, canonical_json, status = orchestrator.run(strategy_text, args.strategy_id, deterministic_schema, headless=args.headless)

        print_canonical(canonical_json)

        print("\n" * 2 + "=" * 80)
        print("AST TREE")
        print("=" * 80)
        ASTDebugger.print_tree(ast)

        ast_json = ASTSerializer.to_json(ast, include_version=True)
        if args.ast_json:
            print("\n" + "=" * 80)
            print("AST JSON")
            print("=" * 80)
            print(ast_json)

        if not args.no_save:
            save_outputs(canonical_json, ast_json, args.canonical_out, args.ast_out)
            print("\n" + "=" * 80)
            print("SAVED OUTPUTS")
            print("=" * 80)
            print(f"Canonical JSON: {args.canonical_out}")
            print(f"AST JSON:       {args.ast_out}")

        return 0

    except ASTBuildError as exc:
        print("\nAST build failed.")
        print(str(exc))
        print(
            "\nThe LLM may have produced a node outside the AST vocabulary. "
            "Move risk events such as stop-loss/take-profit into the 'risk' section, "
            "or add a registered AST extension for that node type."
        )
        return 1
    except Exception as exc:
        print(f"\nPipeline failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
