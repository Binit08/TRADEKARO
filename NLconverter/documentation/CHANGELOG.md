# Changelog

All notable changes to the TradeKaro NLconverter project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Core Pipeline**: 7-stage deterministic strategy parser pipeline (Semantic Resolver → Compiler → Schema Validator → AST Builder → AST Validator → Auditor).
- **RAG Subsystem**: DuckDB-powered hybrid retrieval (VSS + FTS) via `sentence-transformers` for entity disambiguation.
- **Frontend App**: Next.js 15 UI with Strategy Editor, Execution Context form, and Backtest configuration.
- **Security Proxy**: Next.js server-side API routes to shield the `X-API-Key` from the browser.
- **Auth**: Supabase JWT authentication integration with automatic local user provisioning.
- **Database**: SQLAlchemy models for `users`, `strategies`, and `backtests` with SQLite/PostgreSQL support and Alembic migrations.
- **Broker Integration**: Zerodha Kite API auth flow, instrument fetching, futures mapping, and live portfolio positions.
- **Market Support**: Equity and Futures schemas and execution contexts.
- **Charts**: Recharts for equity/drawdown curves and Lightweight Charts for TradingView-style OHLC visualization.
- **Paper Trading**: Integration with the Backtesting Engine to start live data paper trade sessions.
- **Typo Normalization**: RapidFuzz integration for fuzzy matching user prompts against the knowledge base.
- **Observability**: Sentry SDK integration for backend error monitoring.
- **Docker**: `Dockerfile.backend` for containerized deployment of the FastAPI service.

### Changed
- **Architecture**: Deprecated the binary "Blocker Detector" in favor of the granular RAG "Semantic Resolver" (parsed/assumed/unparsed).
- **Storage**: Migrated primary strategy and backtest persistence from DuckDB/Parquet to SQLAlchemy (RDBMS) for better relational integrity and Supabase compatibility.

### Fixed
- UI layout adjustments for the AI Clarification modal and Strategy Summary tabs.
- Cross-origin resource sharing (CORS) configurations for backend-frontend communication.
- Token limits and temperature adjustments for deterministic JSON output from the Gemini API.

---

*(Note: Prior development history is captured in git logs, but this document serves as the baseline for all features present at the launch of the `ast-enhance` branch integration).*
