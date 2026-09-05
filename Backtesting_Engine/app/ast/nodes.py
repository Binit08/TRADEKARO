"""In-memory typed AST definitions for the Backtesting Engine.

These dataclasses represent the strict JSON contract expected from the
NLconverter, but typed safely for the Backtesting Engine's signal evaluator.
There is zero dependency on NLconverter's internal classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Any, Dict


@dataclass(frozen=True)
class IndicatorConfig:
    indicator_type: str
    period: Optional[int] = None
    output_property: str = "value"
    timeframe: str = "1D"
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_node: Optional['ASTNode'] = None
    
    @property
    def key(self) -> str:
        """Canonical cache key for the indicator engine."""
        base = self.indicator_type.strip().upper()
        normalized: Dict[str, Any] = {}
        for k, v in self.parameters.items():
            if k == "period" or k == "timeperiod":
                normalized["timeperiod"] = v
            else:
                normalized[k.lower()] = v
        if self.period is not None:
            normalized["timeperiod"] = self.period
            
        if not normalized:
            return base
            
        parts = [f"{k.upper()}={normalized[k]}" for k in sorted(normalized)]
        return f"{base}_{'_'.join(parts)}"


@dataclass(frozen=True)
class PatternConfig:
    pattern_type: str
    lookback_periods: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)


# --- Base Node Type (Marker) ---
class BaseNode:
    pass


# --- Leaf Nodes ---
@dataclass(frozen=True)
class IndicatorNode(BaseNode):
    config: IndicatorConfig
    lookback_periods: int = 0


@dataclass(frozen=True)
class PatternNode(BaseNode):
    config: PatternConfig


@dataclass(frozen=True)
class ArithmeticNode(BaseNode):
    operator: str
    children: List[BaseNode]


@dataclass(frozen=True)
class MarketReferenceNode(BaseNode):
    data_type: str
    lookback_periods: int = 0
    timeframe: str = "1D"


@dataclass(frozen=True)
class ConstantNode(BaseNode):
    value: Union[float, str]


@dataclass(frozen=True)
class VariableAssignmentNode(BaseNode):
    variable_name: str
    condition: BaseNode
    value_node: BaseNode


@dataclass(frozen=True)
class VariableReferenceNode(BaseNode):
    variable_name: str


# --- Comparison & Cross Nodes ---
@dataclass(frozen=True)
class ComparisonNode(BaseNode):
    operator: str  # "GREATER_THAN", "LESS_THAN", "EQUAL", "NOT_EQUAL", "GREATER_EQUAL", "LESS_EQUAL"
    left: BaseNode
    right: BaseNode
    lookback_periods: int = 0


@dataclass(frozen=True)
class CrossNode(BaseNode):
    cross_type: str  # "ABOVE" or "BELOW"
    left: BaseNode
    right: BaseNode
    lookback_periods: int = 1


@dataclass(frozen=True)
class SequenceNode(BaseNode):
    condition: BaseNode
    count: int
    direction: str = "BACKWARD"
    aggregate: Optional[Dict[str, Any]] = None



@dataclass(frozen=True)
class FollowedByNode(BaseNode):
    max_bars_between: Optional[int]
    setup_condition: BaseNode
    trigger_condition: BaseNode

# --- Logic Nodes ---
@dataclass(frozen=True)
class LogicNode(BaseNode):
    operator: str  # "AND", "OR", "NOT"
    children: List[BaseNode]


# --- Structural/Container Nodes ---
@dataclass(frozen=True)
class EntryNode(BaseNode):
    condition: BaseNode


@dataclass(frozen=True)
class ExitNode(BaseNode):
    condition: BaseNode


@dataclass(frozen=True)
class FilterNode(BaseNode):
    condition: BaseNode


@dataclass(frozen=True)
class OperationNode(BaseNode):
    entry_nodes: List[EntryNode]
    exit_nodes: List[ExitNode]


@dataclass(frozen=True)
class StrategyRootNode(BaseNode):
    strategy_id: str
    operation_nodes: List[OperationNode]
    variable_nodes: List[VariableAssignmentNode] = field(default_factory=list)
    filter_nodes: List[FilterNode] = field(default_factory=list)


# A type alias for convenience in type hinting
ASTNode = Union[
    IndicatorNode,
    PatternNode,
    MarketReferenceNode,
    ConstantNode,
    ComparisonNode,
    CrossNode,
    SequenceNode,
    FollowedByNode,
    LogicNode,
    EntryNode,
    ExitNode,
    FilterNode,
    OperationNode,
    StrategyRootNode,
    VariableAssignmentNode,
    VariableReferenceNode,
]
