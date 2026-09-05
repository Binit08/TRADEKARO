# Validator

## What it is
The `validator.py` module implements the core Validator functionality.

**Overview**: AST validation logic.

## Why it exists
To maintain strict separation of concerns within the `ast` domain, this module isolates the Validator logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`validate`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.ast.validator
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
