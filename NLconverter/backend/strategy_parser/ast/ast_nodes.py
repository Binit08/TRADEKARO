"""
AST node definitions for deterministic trading strategy structure.

These classes are pure data containers. They intentionally do not fetch data,
calculate indicators, evaluate conditions, or execute trades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union


# ============================================================================
# METADATA
# ============================================================================


@dataclass
class ASTNodeMetadata:
    """Metadata for deterministic tracking and versioning."""

    version: str = "1.0.0"
    created_at: str = ""
    source_path: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# BASE NODE
# ============================================================================


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    node_id: str
    children: List["ASTNode"] = field(default_factory=list)
    metadata: Optional[ASTNodeMetadata] = None
    node_type: str = field(default="AST_NODE", init=False)

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = ASTNodeMetadata()


# ============================================================================
# CORE STRATEGY NODES
# ============================================================================


@dataclass
class VariableAssignmentNode(ASTNode):
    """Assigns a value to a variable when a condition is met.
    The condition is stored in children[0], and the value is stored in children[1].
    """

    variable_name: str = ""
    node_type: str = field(default="VARIABLE_ASSIGNMENT", init=False)


@dataclass
class VariableReferenceNode(ASTNode):
    """Reference to a memory variable."""

    variable_name: str = ""
    node_type: str = field(default="VARIABLE_REFERENCE", init=False)


@dataclass
class StrategyRootNode(ASTNode):
    """Root of a strategy AST."""

    strategy_id: str = ""
    entry_node: Optional[ASTNode] = None
    exit_node: Optional[ASTNode] = None
    risk_node: Optional[ASTNode] = None
    filter_nodes: List[ASTNode] = field(default_factory=list)
    variable_nodes: List[VariableAssignmentNode] = field(default_factory=list)
    operation_nodes: List[OperationNode] = field(default_factory=list)
    node_type: str = field(default="STRATEGY_ROOT", init=False)


@dataclass
class OperationNode(ASTNode):
    """An operation grouping entries and exits that belong together."""

    entry_nodes: List[ASTNode] = field(default_factory=list)
    exit_nodes: List[ASTNode] = field(default_factory=list)
    node_type: str = field(default="OPERATION", init=False)


@dataclass
class EntryNode(ASTNode):
    """Entry condition wrapper. The condition tree is stored in children."""

    node_type: str = field(default="ENTRY", init=False)


@dataclass
class ExitNode(ASTNode):
    """Exit condition wrapper. The condition tree is stored in children."""

    node_type: str = field(default="EXIT", init=False)


@dataclass
class RiskNode(ASTNode):
    """Risk management wrapper. Risk declarations are stored in children."""

    node_type: str = field(default="RISK", init=False)


@dataclass
class FilterNode(ASTNode):
    """Pre-condition/filter wrapper. The filter tree is stored in children."""

    node_type: str = field(default="FILTER", init=False)


# ============================================================================
# LOGICAL OPERATORS
# ============================================================================


@dataclass
class AndNode(ASTNode):
    """Logical AND."""

    node_type: str = field(default="AND", init=False)


@dataclass
class OrNode(ASTNode):
    """Logical OR."""

    node_type: str = field(default="OR", init=False)


@dataclass
class NotNode(ASTNode):
    """Logical NOT."""

    node_type: str = field(default="NOT", init=False)


@dataclass
class NotEqualNode(ASTNode):
    """Not equal comparison (A != B)."""

    node_type: str = field(default="NOT_EQUAL", init=False)


@dataclass
class SequenceNode(ASTNode):
    """Sequence condition spanning multiple candles."""

    direction: str = "BACKWARD"
    count: int = 1
    node_type: str = field(default="SEQUENCE", init=False)


@dataclass
class FollowedByNode(ASTNode):
    """Path dependency (State Machine) node."""

    max_bars_between: Optional[int] = None
    node_type: str = field(default="FOLLOWED_BY", init=False)


# ============================================================================
# COMPARISON OPERATORS
# ============================================================================


@dataclass
class ComparisonNode(ASTNode):
    """Generic comparison node."""

    operator: str = ""
    lookback_periods: int = 0
    node_type: str = field(default="COMPARISON", init=False)


@dataclass
class GreaterThanNode(ComparisonNode):
    """Greater-than comparison."""

    operator: str = field(default="GREATER_THAN", init=False)
    node_type: str = field(default="GREATER_THAN", init=False)


@dataclass
class LessThanNode(ComparisonNode):
    """Less-than comparison."""

    operator: str = field(default="LESS_THAN", init=False)
    node_type: str = field(default="LESS_THAN", init=False)


@dataclass
class GreaterEqualNode(ComparisonNode):
    """Greater-than-or-equal comparison."""

    operator: str = field(default="GREATER_THAN_EQUAL", init=False)
    node_type: str = field(default="GREATER_THAN_EQUAL", init=False)


@dataclass
class LessEqualNode(ComparisonNode):
    """Less-than-or-equal comparison."""

    operator: str = field(default="LESS_THAN_EQUAL", init=False)
    node_type: str = field(default="LESS_THAN_EQUAL", init=False)


@dataclass
class EqualNode(ComparisonNode):
    """Equality comparison."""

    operator: str = field(default="EQUAL", init=False)
    node_type: str = field(default="EQUAL", init=False)


@dataclass
class NotEqualNode(ComparisonNode):
    """Inequality comparison."""

    operator: str = field(default="NOT_EQUAL", init=False)
    node_type: str = field(default="NOT_EQUAL", init=False)


# ============================================================================
# CROSS NODES
# ============================================================================


@dataclass
class CrossNode(ASTNode):
    """Generic cross node."""

    cross_type: str = ""
    lookback_periods: int = 1
    node_type: str = field(default="CROSS", init=False)


@dataclass
class CrossAboveNode(CrossNode):
    """Crosses above."""

    cross_type: str = field(default="ABOVE", init=False)
    node_type: str = field(default="CROSS_ABOVE", init=False)


@dataclass
class CrossBelowNode(CrossNode):
    """Crosses below."""

    cross_type: str = field(default="BELOW", init=False)
    node_type: str = field(default="CROSS_BELOW", init=False)


# ============================================================================
# ARITHMETIC NODES
# ============================================================================


@dataclass
class ArithmeticNode(ASTNode):
    """Generic arithmetic operation."""

    operator: str = ""
    node_type: str = field(default="ARITHMETIC", init=False)


@dataclass
class AddNode(ArithmeticNode):
    """Addition."""

    operator: str = field(default="ADD", init=False)
    node_type: str = field(default="ADD", init=False)


@dataclass
class SubtractNode(ArithmeticNode):
    """Subtraction."""

    operator: str = field(default="SUBTRACT", init=False)
    node_type: str = field(default="SUBTRACT", init=False)


@dataclass
class MultiplyNode(ArithmeticNode):
    """Multiplication."""

    operator: str = field(default="MULTIPLY", init=False)
    node_type: str = field(default="MULTIPLY", init=False)


@dataclass
class DivideNode(ArithmeticNode):
    """Division."""

    operator: str = field(default="DIVIDE", init=False)
    node_type: str = field(default="DIVIDE", init=False)


@dataclass
class MinNode(ArithmeticNode):
    """Minimum."""

    operator: str = field(default="MIN", init=False)
    node_type: str = field(default="MIN", init=False)


@dataclass
class MaxNode(ArithmeticNode):
    """Maximum."""

    operator: str = field(default="MAX", init=False)
    node_type: str = field(default="MAX", init=False)


@dataclass
class AbsNode(ArithmeticNode):
    """Absolute value."""

    operator: str = field(default="ABS", init=False)
    node_type: str = field(default="ABS", init=False)


# ============================================================================
# REFERENCE NODES
# ============================================================================


@dataclass
class IndicatorConfig:
    """Configuration for any indicator type."""

    indicator_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_property: str = "value"
    timeframe: str = "1d"
    input_node: Optional[ASTNode] = None


@dataclass
class IndicatorNode(ASTNode):
    """Generic indicator reference node."""

    indicator_config: Optional[IndicatorConfig] = None
    node_type: str = field(default="INDICATOR", init=False)


@dataclass
class ConstantNode(ASTNode):
    """Literal constant node."""

    value: Union[float, int, bool, str, None] = None
    node_type: str = field(default="CONSTANT", init=False)


@dataclass
class MarketReferenceNode(ASTNode):
    """OHLCV or derived market data reference."""

    data_type: str = ""
    lookback_periods: int = 0
    timeframe: str = "1d"
    node_type: str = field(default="MARKET_REFERENCE", init=False)


@dataclass
class PatternConfig:
    """Configuration for any pattern type."""

    pattern_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    lookback_periods: int = 50


@dataclass
class PatternNode(ASTNode):
    """Generic pattern reference node."""

    pattern_config: Optional[PatternConfig] = None
    node_type: str = field(default="PATTERN", init=False)


# ============================================================================
# RISK MANAGEMENT NODES
# ============================================================================


@dataclass
class StopLossConfig:
    """Stop-loss declaration."""

    stop_loss_type: str
    value: Optional[float] = None
    reference: str = "entry_price"
    direction: Optional[str] = None
    atr_multiple: Optional[float] = None
    price_level: Optional[float] = None
    indicator_ref: Optional[str] = None
    trailing: bool = False


@dataclass
class StopLossNode(ASTNode):
    """Stop-loss configuration node."""

    config: Optional[StopLossConfig] = None
    node_type: str = field(default="STOP_LOSS", init=False)


@dataclass
class TakeProfitConfig:
    """Take-profit declaration."""

    take_profit_type: str
    value: Optional[float] = None
    target_indicator: Optional[str] = None
    price_level: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    indicator_ref: Optional[str] = None


@dataclass
class TakeProfitNode(ASTNode):
    """Take-profit configuration node."""

    config: Optional[TakeProfitConfig] = None
    node_type: str = field(default="TAKE_PROFIT", init=False)


@dataclass
class PositionSizeConfig:
    """Position sizing declaration."""

    size_type: str
    value: Optional[float] = None
    max_size: Optional[float] = None
    min_size: Optional[float] = None


@dataclass
class PositionSizeNode(ASTNode):
    """Position sizing node."""

    config: Optional[PositionSizeConfig] = None
    node_type: str = field(default="POSITION_SIZE", init=False)


@dataclass
class TrailingStopNode(ASTNode):
    """Trailing stop declaration."""

    trail_amount: Optional[float] = None
    trail_type: str = "PERCENTAGE"
    reference: str = "highest_price"
    indicator_ref: Optional[str] = None
    node_type: str = field(default="TRAILING_STOP", init=False)


@dataclass
class MultipleNode(ASTNode):
    """Multiple/Multiplier for risk parameters."""

    value: float = 1.0
    node_type: str = field(default="MULTIPLE", init=False)


@dataclass
class ReferenceIndicatorNode(ASTNode):
    """Reference indicator for stop loss / take profit."""

    indicator_ref: str = ""
    node_type: str = field(default="REFERENCE_INDICATOR", init=False)


@dataclass
class RiskRewardNode(ASTNode):
    """Risk/reward ratio declaration."""

    ratio: float = 2.0
    node_type: str = field(default="RISK_REWARD", init=False)


# ============================================================================
# TIME-BASED NODES
# ============================================================================


@dataclass
class TimeNode(ASTNode):
    """Time-of-day declaration."""

    start_time: str = ""
    end_time: str = ""
    timezone: Optional[str] = None
    node_type: str = field(default="TIME", init=False)


@dataclass
class DateNode(ASTNode):
    """Date range declaration."""

    start_date: str = ""
    end_date: str = ""
    node_type: str = field(default="DATE", init=False)


@dataclass
class SessionNode(ASTNode):
    """Market session declaration."""

    sessions: List[str] = field(default_factory=list)
    node_type: str = field(default="SESSION", init=False)


@dataclass
class DayOfWeekNode(ASTNode):
    """Day-of-week declaration."""

    days: List[int] = field(default_factory=list)
    node_type: str = field(default="DAY_OF_WEEK", init=False)


# ============================================================================
# PORTFOLIO-LEVEL NODES
# ============================================================================


@dataclass
class MaxDrawdownNode(ASTNode):
    """Maximum drawdown declaration."""

    max_drawdown_percent: Optional[float] = None
    node_type: str = field(default="MAX_DRAWDOWN", init=False)


@dataclass
class MaxDailyLossNode(ASTNode):
    """Maximum daily loss declaration."""

    max_loss_amount: Optional[float] = None
    node_type: str = field(default="MAX_DAILY_LOSS", init=False)


@dataclass
class MaxOpenTradesNode(ASTNode):
    """Maximum open trades declaration."""

    max_trades: Optional[int] = None
    node_type: str = field(default="MAX_OPEN_TRADES", init=False)


@dataclass
class CapitalAllocationNode(ASTNode):
    """Capital allocation declaration."""

    allocation_percent: Optional[float] = None
    node_type: str = field(default="CAPITAL_ALLOCATION", init=False)


# ============================================================================
# NODE REGISTRY
# ============================================================================


class ASTNodeRegistry:
    """Registry for built-in and extension node types."""

    _registry: Dict[str, Type[ASTNode]] = {}
    _aliases: Dict[str, str] = {
        "GT": "GREATER_THAN",
        ">": "GREATER_THAN",
        "LT": "LESS_THAN",
        "<": "LESS_THAN",
        "GTE": "GREATER_THAN_EQUAL",
        ">=": "GREATER_THAN_EQUAL",
        "GREATER_EQUAL": "GREATER_THAN_EQUAL",
        "LTE": "LESS_THAN_EQUAL",
        "<=": "LESS_THAN_EQUAL",
        "LESS_EQUAL": "LESS_THAN_EQUAL",
        "EQ": "EQUAL",
        "==": "EQUAL",
        "NEQ": "NOT_EQUAL",
        "!=": "NOT_EQUAL",
        "SUB": "SUBTRACT",
        "MUL": "MULTIPLY",
        "DIV": "DIVIDE",
        "MARKET_DATA": "MARKET_REFERENCE",
    }

    @classmethod
    def normalize(cls, node_type: str) -> str:
        """Normalize node type aliases into canonical names."""
        normalized = str(node_type).upper()
        return cls._aliases.get(normalized, normalized)

    @classmethod
    def register(
        cls,
        node_type: str,
        node_class: Type[ASTNode],
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Register a node class, optionally with aliases."""
        canonical_type = cls.normalize(node_type)
        cls._registry[canonical_type] = node_class
        for alias in aliases or []:
            cls._aliases[str(alias).upper()] = canonical_type

    @classmethod
    def get(cls, node_type: str) -> Optional[Type[ASTNode]]:
        """Get a node class by node type."""
        return cls._registry.get(cls.normalize(node_type))

    @classmethod
    def require(cls, node_type: str) -> Type[ASTNode]:
        """Get a node class or raise a clear error."""
        node_class = cls.get(node_type)
        if node_class is None:
            raise ValueError(f"Unknown AST node type: {node_type}")
        return node_class

    @classmethod
    def list_all(cls) -> Dict[str, Type[ASTNode]]:
        """List registered canonical node types."""
        return dict(cls._registry)

    @classmethod
    def list_aliases(cls) -> Dict[str, str]:
        """List registered aliases."""
        return dict(cls._aliases)


def _register_builtin_nodes() -> None:
    for node_type, node_class in {
        # Core
        "STRATEGY_ROOT": StrategyRootNode,
        "OPERATION": OperationNode,
        "ENTRY": EntryNode,
        "EXIT": ExitNode,
        "RISK": RiskNode,
        "FILTER": FilterNode,
        "VARIABLE_ASSIGNMENT": VariableAssignmentNode,
        "VARIABLE_REFERENCE": VariableReferenceNode,
        # Logical
        "AND": AndNode,
        "OR": OrNode,
        "NOT": NotNode,
        "NOT_EQUAL": NotEqualNode,
        "SEQUENCE": SequenceNode,
        "FOLLOWED_BY": FollowedByNode,
        # Comparison
        "COMPARISON": ComparisonNode,
        "GREATER_THAN": GreaterThanNode,
        "LESS_THAN": LessThanNode,
        "GREATER_THAN_EQUAL": GreaterEqualNode,
        "LESS_THAN_EQUAL": LessEqualNode,
        "EQUAL": EqualNode,
        "NOT_EQUAL": NotEqualNode,
        # Cross
        "CROSS": CrossNode,
        "CROSS_ABOVE": CrossAboveNode,
        "CROSS_BELOW": CrossBelowNode,
        # Arithmetic
        "ARITHMETIC": ArithmeticNode,
        "ADD": AddNode,
        "SUBTRACT": SubtractNode,
        "MULTIPLY": MultiplyNode,
        "DIVIDE": DivideNode,
        "MIN": MinNode,
        "MAX": MaxNode,
        "ABS": AbsNode,
        # References
        "INDICATOR": IndicatorNode,
        "CONSTANT": ConstantNode,
        "MARKET_REFERENCE": MarketReferenceNode,
        "PATTERN": PatternNode,
        # Risk
        "STOP_LOSS": StopLossNode,
        "TAKE_PROFIT": TakeProfitNode,
        "TRAILING_STOP": TrailingStopNode,
        "POSITION_SIZE": PositionSizeNode,
        "RISK_REWARD": RiskRewardNode,
        "MULTIPLE": MultipleNode,
        "REFERENCE_INDICATOR": ReferenceIndicatorNode,
        # Time
        "TIME": TimeNode,
        "DATE": DateNode,
        "SESSION": SessionNode,
        "DAY_OF_WEEK": DayOfWeekNode,
        # Portfolio
        "MAX_DRAWDOWN": MaxDrawdownNode,
        "MAX_DAILY_LOSS": MaxDailyLossNode,
        "MAX_OPEN_TRADES": MaxOpenTradesNode,
        "CAPITAL_ALLOCATION": CapitalAllocationNode,
    }.items():
        ASTNodeRegistry.register(node_type, node_class)


_register_builtin_nodes()
