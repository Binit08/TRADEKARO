# Loader

## What it is
The `loader.py` module implements the core Loader functionality. It defines key architectural components including `ASTLoadError`, `StrategyLoader`.

**Overview**: AST Loader.

## Why it exists
To maintain strict separation of concerns within the `ast` domain, this module isolates the Loader logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.ast.loader
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
