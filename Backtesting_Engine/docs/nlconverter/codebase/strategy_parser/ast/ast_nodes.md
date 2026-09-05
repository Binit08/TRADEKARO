# Ast Nodes

## What it is
The `ast_nodes.py` module implements the core Ast Nodes functionality. It defines key architectural components including `ASTNodeMetadata`, `ASTNode`, `VariableAssignmentNode`, `VariableReferenceNode`, `StrategyRootNode`, `OperationNode`, `EntryNode`, `ExitNode`, `RiskNode`, `FilterNode`, `AndNode`, `OrNode`, `NotNode`, `NotEqualNode`, `SequenceNode`, `ComparisonNode`, `GreaterThanNode`, `LessThanNode`, `GreaterEqualNode`, `LessEqualNode`, `EqualNode`, `NotEqualNode`, `CrossNode`, `CrossAboveNode`, `CrossBelowNode`, `ArithmeticNode`, `AddNode`, `SubtractNode`, `MultiplyNode`, `DivideNode`, `MinNode`, `MaxNode`, `AbsNode`, `IndicatorConfig`, `IndicatorNode`, `ConstantNode`, `MarketReferenceNode`, `PatternConfig`, `PatternNode`, `StopLossConfig`, `StopLossNode`, `TakeProfitConfig`, `TakeProfitNode`, `PositionSizeConfig`, `PositionSizeNode`, `TrailingStopNode`, `MultipleNode`, `ReferenceIndicatorNode`, `RiskRewardNode`, `TimeNode`, `DateNode`, `SessionNode`, `DayOfWeekNode`, `MaxDrawdownNode`, `MaxDailyLossNode`, `MaxOpenTradesNode`, `CapitalAllocationNode`, `ASTNodeRegistry`.

**Overview**: AST node definitions for deterministic trading strategy structure.

## Why it exists
To maintain strict separation of concerns within the `strategy_parser` domain, this module isolates the Ast Nodes logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.strategy_parser.ast.ast_nodes
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
