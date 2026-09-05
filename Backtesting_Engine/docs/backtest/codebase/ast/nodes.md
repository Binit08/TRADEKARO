# Nodes

## What it is
The `nodes.py` module implements the core Nodes functionality. It defines key architectural components including `IndicatorConfig`, `PatternConfig`, `BaseNode`, `IndicatorNode`, `PatternNode`, `ArithmeticNode`, `MarketReferenceNode`, `ConstantNode`, `VariableAssignmentNode`, `VariableReferenceNode`, `ComparisonNode`, `CrossNode`, `SequenceNode`, `LogicNode`, `EntryNode`, `ExitNode`, `OperationNode`, `StrategyRootNode`.

**Overview**: In-memory typed AST definitions for the Backtesting Engine.

## Why it exists
To maintain strict separation of concerns within the `ast` domain, this module isolates the Nodes logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.ast.nodes
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
