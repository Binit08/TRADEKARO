"""Execution context and Strategy Bundle models.

These classes hold the non-AST runtime metadata provided by the JSON contract.
"""

from dataclasses import dataclass
from typing import Optional

from app.ast.nodes import StrategyRootNode


@dataclass(frozen=True)
class ExecutionContext:
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    capital: float
    position_side: str            # "LONG", "SHORT", "BOTH"
    order_type: str               # "MARKET", "LIMIT", etc.
    max_concurrent_positions: int


@dataclass(frozen=True)
class StrategyBundle:
    schema_version: str
    ast: StrategyRootNode
    execution_context: ExecutionContext
