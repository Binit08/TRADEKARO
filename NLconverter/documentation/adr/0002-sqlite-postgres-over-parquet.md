# 0002 - SQLite/PostgreSQL Over Parquet for Primary Storage

* **Status:** Accepted
* **Date:** 2026-09-02
* **Authors:** TradeKaro Team

## Context

The application needs to persist three primary entities: Users, Strategies, and Backtest results. 

Early architectural designs considered using DuckDB and Parquet files for all data storage, driven by the heavy analytical nature of backtest results (OHLC data, equity curves) and the use of Polars for data processing.

However, as the application evolved to include user authentication (Supabase), strategy management, and complex relationships (a user owns strategies; a strategy has many backtests), the storage requirements shifted heavily toward OLTP (Online Transaction Processing).

## Decision

We will use a traditional RDBMS (**SQLite** for local development, **PostgreSQL** for production) accessed via **SQLAlchemy** for primary data storage, rather than Parquet/DuckDB.

DuckDB is retained strictly as the embedded vector database for the RAG knowledge base, completely isolated from application state.

## Consequences

### Positive

* **Relational Integrity:** Foreign keys ensure that strategies and backtests are strictly tied to authenticated users.
* **Supabase Integration:** Supabase provides PostgreSQL out of the box, aligning our auth provider with our database provider.
* **Migrations:** Alembic provides a robust, standardized way to handle schema migrations over time, which is difficult to manage with raw Parquet files.
* **Concurrency:** PostgreSQL handles concurrent writes from multiple API requests flawlessly, whereas local DuckDB/Parquet writes require careful lock management.

### Negative

* **Data Size Limitations:** Storing large JSON blobs (OHLC data, tick-by-tick trades) in PostgreSQL `JSON` columns is less efficient than columnar Parquet.
* **Mitigation:** We mitigate this by using SQLAlchemy's `deferred()` column loading, ensuring that large data arrays are only fetched from the database when explicitly viewing a specific backtest detail page, keeping list queries fast.
