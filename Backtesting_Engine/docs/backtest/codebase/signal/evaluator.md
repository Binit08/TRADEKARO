# Evaluator

## What it is
The `evaluator.py` module implements the core Evaluator functionality. It defines key architectural components including `EvaluatorState`, `SignalEvaluator`.

**Overview**: Signal Evaluator.

## Why it exists
To maintain strict separation of concerns within the `signal` domain, this module isolates the Evaluator logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`evaluate_node`, `evaluate_ast_node`, `get_max_lookback`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.signal.evaluator
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
