# Trade Report

## What it is
The `trade_report.py` module implements the core Trade Report functionality. It defines key architectural components including `ReportBuilder`.

## Why it exists
To maintain strict separation of concerns within the `reports` domain, this module isolates the Trade Report logic. This prevents monolithic spaghetti code and ensures that components can be tested and mocked independently.

## Data Flow
1. The module is initialized or invoked by upstream services.
2. Data is processed primarily through the main operational methods (internal methods).
3. Results are returned to the caller or state is mutated internally.

## Source Code Reference

::: app.reports.trade_report
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
