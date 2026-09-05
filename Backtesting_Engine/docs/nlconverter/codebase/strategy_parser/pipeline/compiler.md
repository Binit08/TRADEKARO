# Compiler

## What it is
The `compiler.py` module implements the core Compiler functionality. It defines key architectural components including `StrategyCompiler`.

## Why it exists
To maintain strict separation of concerns within the `strategy_parser` domain, this module isolates the Compiler logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.strategy_parser.pipeline.compiler
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
