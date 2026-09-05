# Example Usage

## What it is
The `example_usage.py` module implements the core Example Usage functionality.

**Overview**: AST Example - Demonstrate AST building from Canonical JSON

## Why it exists
To maintain strict separation of concerns within the `strategy_parser` domain, this module isolates the Example Usage logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`example_rsi_strategy`, `example_ema_crossover`, `example_complex_nested`, `example_with_risk_management`, `main`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.strategy_parser.ast.example_usage
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
