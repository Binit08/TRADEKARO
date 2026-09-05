# Semantic Resolver

## What it is
The `semantic_resolver.py` module implements the core Semantic Resolver functionality. It defines key architectural components including `ApprovalItem`, `ResolverResult`, `SemanticResolver`.

## Why it exists
To maintain strict separation of concerns within the `strategy_parser` domain, this module isolates the Semantic Resolver logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.strategy_parser.pipeline.semantic_resolver
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
