# Equity Curve

## What it is
The `equity_curve.py` module implements the core Equity Curve functionality.

**Overview**: Equity curve reporting.

## Why it exists
To maintain strict separation of concerns within the `reports` domain, this module isolates the Equity Curve logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (`equity_curve_to_dataframe`, `export_equity_curve_to_csv`).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.reports.equity_curve
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
