# Fees

## What it is
The `fees.py` module implements the core Fees functionality. It defines key architectural components including `FeeModel`, `NoFeeModel`.

**Overview**: Fee calculations for simulated order fills.

## Why it exists
To maintain strict separation of concerns within the `execution` domain, this module isolates the Fees logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`calculate_fee`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.execution.fees
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
