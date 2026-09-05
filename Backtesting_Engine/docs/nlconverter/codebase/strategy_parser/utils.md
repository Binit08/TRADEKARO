# Utils

## What it is
The `utils.py` module implements the core Utils functionality.

## Why it exists
To maintain strict separation of concerns within the `strategy_parser` domain, this module isolates the Utils logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`load_dotenv`, `strip_code_fences`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: backend.strategy_parser.utils
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
