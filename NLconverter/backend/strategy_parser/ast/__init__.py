"""
AST (Abstract Syntax Tree) Module for Trading Strategies

Converts Canonical JSON (LLM output) → AST (deterministic, rule-based structure)
No evaluation logic - pure data representation for backtesting engine.
"""

from .ast_nodes import (
    ASTNode,
    ASTNodeMetadata,
    StrategyRootNode,
    EntryNode,
    ExitNode,
    RiskNode,
    FilterNode,
    AndNode,
    OrNode,
    NotNode,
    ComparisonNode,
    GreaterThanNode,
    LessThanNode,
    GreaterEqualNode,
    LessEqualNode,
    EqualNode,
    NotEqualNode,
    CrossNode,
    CrossAboveNode,
    CrossBelowNode,
    ArithmeticNode,
    AddNode,
    SubtractNode,
    MultiplyNode,
    DivideNode,
    MinNode,
    MaxNode,
    AbsNode,
    IndicatorConfig,
    IndicatorNode,
    ConstantNode,
    MarketReferenceNode,
    PatternConfig,
    PatternNode,
    StopLossConfig,
    StopLossNode,
    TakeProfitConfig,
    TakeProfitNode,
    PositionSizeConfig,
    PositionSizeNode,
    TrailingStopNode,
    RiskRewardNode,
    TimeNode,
    DateNode,
    SessionNode,
    DayOfWeekNode,
    MaxDrawdownNode,
    MaxDailyLossNode,
    MaxOpenTradesNode,
    CapitalAllocationNode,
    ASTNodeRegistry,
)

from .ast_builder import ASTBuilder, ASTBuildError

from .ast_serializer import ASTSerializer, ASTVersionManager

from .ast_utils import ASTValidator, ASTDebugger, ASTAnalyzer, ASTMetrics, iter_structural_children

__all__ = [
    # Base
    "ASTNode",
    "ASTNodeMetadata",
    
    # Core
    "StrategyRootNode",
    "EntryNode",
    "ExitNode",
    "RiskNode",
    "FilterNode",
    
    # Logical
    "AndNode",
    "OrNode",
    "NotNode",
    
    # Comparison
    "ComparisonNode",
    "GreaterThanNode",
    "LessThanNode",
    "GreaterEqualNode",
    "LessEqualNode",
    "EqualNode",
    "NotEqualNode",
    
    # Cross
    "CrossNode",
    "CrossAboveNode",
    "CrossBelowNode",
    
    # Arithmetic
    "ArithmeticNode",
    "AddNode",
    "SubtractNode",
    "MultiplyNode",
    "DivideNode",
    "MinNode",
    "MaxNode",
    "AbsNode",
    
    # References
    "IndicatorConfig",
    "IndicatorNode",
    "ConstantNode",
    "MarketReferenceNode",
    "PatternConfig",
    "PatternNode",
    
    # Risk
    "StopLossConfig",
    "StopLossNode",
    "TakeProfitConfig",
    "TakeProfitNode",
    "PositionSizeConfig",
    "PositionSizeNode",
    "TrailingStopNode",
    "RiskRewardNode",
    
    # Time
    "TimeNode",
    "DateNode",
    "SessionNode",
    "DayOfWeekNode",
    
    # Portfolio
    "MaxDrawdownNode",
    "MaxDailyLossNode",
    "MaxOpenTradesNode",
    "CapitalAllocationNode",
    
    # Registry
    "ASTNodeRegistry",
    
    # Builder
    "ASTBuilder",
    "ASTBuildError",
    
    # Serializer
    "ASTSerializer",
    "ASTVersionManager",
    
    # Utils
    "ASTValidator",
    "ASTDebugger",
    "ASTAnalyzer",
    "ASTMetrics",
    "iter_structural_children",
]
