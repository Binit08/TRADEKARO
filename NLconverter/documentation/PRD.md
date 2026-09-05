# Project Requirements Document (PRD)

| Field          | Value                                  |
|----------------|----------------------------------------|
| **Project**    | TradeKaro — NLconverter                |
| **Doc Type**   | Product Requirements Document          |
| **Version**    | 1.0.0                                  |
| **Author**     | TradeKaro Team                         |
| **Last Updated** | 2026-09-02                           |

---

## 1. Executive Summary

TradeKaro NLconverter is an AI-powered bridge that translates human-readable trading strategy descriptions (natural language) into a strict, deterministic JSON Abstract Syntax Tree (AST) that can be executed by the TradeKaro Backtesting Engine. The system targets Indian equity and futures markets (NSE / NFO) and provides an end-to-end workflow: write a strategy in plain English → AI compiles it to structured logic → validate against strict schemas → generate an AST → run backtests → visualize results.

---

## 2. Problem Statement

Retail and algorithmic traders describe strategies in subjective, ambiguous natural language (e.g., *"Buy when RSI drops below 30 and MACD crosses above zero"*). Execution engines, however, require perfectly structured, deterministic instruction sets. Manually converting strategies into code is error-prone, time-consuming, and requires programming expertise.

NLconverter eliminates this gap by using an AI-driven compilation pipeline that:
1. Parses natural language into structured Canonical JSON
2. Resolves ambiguous terminology via a RAG-backed semantic layer
3. Compiles the result into a deterministic AST that any compatible backtesting engine can execute

---

## 3. Target Users

| Persona             | Description                                                      |
|----------------------|------------------------------------------------------------------|
| **Retail Quant Trader** | Wants to test trading ideas without writing code               |
| **Strategy Researcher** | Needs rapid iteration on strategy hypotheses                   |
| **Internal Backtest Team** | Uses NLconverter as the input layer for the Backtesting Engine |
| **Platform Developer** | Extends the AST schema, indicators, or pipeline stages          |

---

## 4. Scope

### In Scope
- Natural language to Canonical JSON conversion via Google Gemini LLM
- 7-stage deterministic compilation pipeline
- RAG-based entity disambiguation (DuckDB + sentence-transformers)
- JSON Schema validation (Draft 2020-12)
- AST generation, validation, serialization, and versioning
- Backtest proxy to external Backtesting Engine
- Paper trading via Kite Connect live data
- Strategy CRUD with persistent database storage
- User authentication via Supabase JWT
- Kite Connect broker integration (instruments, futures, positions)
- Multi-symbol and multi-timeframe backtesting support
- Equity and Futures market types
- Web-based frontend with strategy editor, backtest configuration, and results visualization

### Out of Scope (Future Roadmap)
- Heuristics engine for translating abstract concepts (support/resistance, liquidity sweeps) to math — see [NL_LIMITATIONS.md](./NL_LIMITATIONS.md) §3.A
- Interactive LLM clarification flow — see [NL_LIMITATIONS.md](./NL_LIMITATIONS.md) §3.B
- Advanced pattern recognition microservice — see [NL_LIMITATIONS.md](./NL_LIMITATIONS.md) §3.C
- Native multi-timeframe indicator resolution overrides — see [NL_LIMITATIONS.md](./NL_LIMITATIONS.md) §3.D
- Path-dependent state tracking (dynamic variables, loops) — see [NL_LIMITATIONS.md](./NL_LIMITATIONS.md) §2
- Reinforcement learning layer on top of backtesting engine
- Named strategy library (STRAT_001 through STRAT_009) — `TODO: not yet implemented`
- Options trading support
- Multiple LLM provider support (OpenAI, Anthropic, Ollama)

---

## 5. Functional Requirements

| ID       | Requirement                                    | Component                  | Status       |
|----------|-----------------------------------------------|----------------------------|-------------|
| FR-001   | Accept natural language strategy input via web UI | Frontend — `NaturalLanguageEditor.tsx` | ✅ Implemented |
| FR-002   | Parse NL to Canonical JSON via Google Gemini LLM | `strategy_parser.py`, `llm_client.py` | ✅ Implemented |
| FR-003   | Disambiguate trading jargon via RAG (DuckDB VSS + FTS) | `semantic_resolver.py`, `retriever.py` | ✅ Implemented |
| FR-004   | Classify terms as parsed / assumed / unparsed with confidence scores | `semantic_resolver.py` → `ApprovalItem` | ✅ Implemented |
| FR-005   | Present ambiguous terms to user for resolution (UI modal) | `AIClarificationModal.tsx` | ✅ Implemented |
| FR-006   | Validate Canonical JSON against JSON Schema (Draft 2020-12) | `validator.py`, `EQUITY_SCHEMA.json`, `FUTURES_SCHEMA.json` | ✅ Implemented |
| FR-007   | Generate deterministic AST from Canonical JSON (rule-based, no LLM) | `ast_builder.py`, `ast_nodes.py` | ✅ Implemented |
| FR-008   | Validate AST structural integrity | `ast_utils.py` → `ASTValidator` | ✅ Implemented |
| FR-009   | Audit AST for final integrity checks | `auditor.py` | ✅ Implemented |
| FR-010   | Serialize AST to versioned JSON | `ast_serializer.py` → `ASTSerializer` | ✅ Implemented |
| FR-011   | Proxy backtest requests to external Backtesting Engine | `backtest_service.py` → `run_backtest_api()` | ✅ Implemented |
| FR-012   | Persist strategies with status tracking (ok/error/blocked/semantic_approval) | `models.py` → `StrategyRecord` | ✅ Implemented |
| FR-013   | Persist backtests with full reproducibility inputs and outputs | `models.py` → `BacktestRecord` | ✅ Implemented |
| FR-014   | Authenticate users via Supabase JWT with auto user creation | `deps.py` → `get_current_user()` | ✅ Implemented |
| FR-015   | Connect to Zerodha Kite broker (login, token exchange, session status) | `auth.py` — Kite auth router | ✅ Implemented |
| FR-016   | Fetch live NSE instruments list from Kite API | `instruments.py` → `GET /api/instruments` | ✅ Implemented |
| FR-017   | Fetch NFO futures with expiry details from Kite API | `instruments.py` → `GET /api/futures` | ✅ Implemented |
| FR-018   | Fetch live portfolio positions from Kite | `portfolio.py` → `GET /api/portfolio/positions` | ✅ Implemented |
| FR-019   | Start paper trade session with live market data | `paper_trade.py` → `POST /api/paper_trade/start` | ✅ Implemented |
| FR-020   | Support equity and futures market types with separate schemas | `schemas.py` → `MarketType` enum, schema config | ✅ Implemented |
| FR-021   | Validate execution context (universe, timeframe, position_side, stocks) | `strategy_service.py` → `_validate_execution_context()` | ✅ Implemented |
| FR-022   | Normalize typos in user prompts via fuzzy matching (RapidFuzz) | `normalizer.py` → `TypoNormalizer` | ✅ Implemented |
| FR-023   | Support multi-symbol backtesting | `backtests.py` — `symbols` field in `ProxyBacktestRequest` | ✅ Implemented |
| FR-024   | Visualize backtest results (equity curve, drawdown, trades, OHLC) | Frontend — Recharts, Lightweight Charts | ✅ Implemented |
| FR-025   | List strategy history with pagination | `strategies.py` → `GET /api/strategies` | ✅ Implemented |
| FR-026   | List backtest history with pagination | `backtests.py` → `GET /api/backtests` | ✅ Implemented |

---

## 6. Non-Functional Requirements

| ID       | Requirement                                | Target                                                      |
|----------|-------------------------------------------|-------------------------------------------------------------|
| NFR-001  | LLM response latency                      | 1–5 seconds per strategy parse *(illustrative — replace with real targets)* |
| NFR-002  | API rate limiting                          | Configurable per IP (default: 10 requests / 60 seconds)     |
| NFR-003  | CORS security                              | Configurable allowed origins, localhost fallback             |
| NFR-004  | Authentication                             | Supabase JWT + X-API-Key header for all protected routes    |
| NFR-005  | SSRF prevention                            | URL domain validation on outbound LLM calls                 |
| NFR-006  | Error monitoring                           | Sentry SDK integration with PII enabled                     |
| NFR-007  | Structured logging                         | Python `logging` module with `[request_id]` correlation     |
| NFR-008  | Database portability                       | SQLite (local dev) / PostgreSQL (production) via `DATABASE_URL` |
| NFR-009  | Database connection resilience             | Connection pooling, `pool_pre_ping`, keepalives (PostgreSQL) |
| NFR-010  | Containerization                           | Docker support via `Dockerfile.backend`                     |
| NFR-011  | Stateless backend                          | No server-side session state; all state in DB or JWT        |
| NFR-012  | Schema versioning                          | AST serialization includes `_version_info.ast_schema_version` |

---

## 7. User Stories

| ID    | As a…                 | I want to…                                          | So that…                                          |
|-------|----------------------|-----------------------------------------------------|--------------------------------------------------|
| US-001 | Retail trader        | Write my strategy in plain English                  | I don't need to learn programming                |
| US-002 | Retail trader        | See which terms the AI understood vs assumed         | I can correct misinterpretations before backtesting |
| US-003 | Retail trader        | Run a backtest on my strategy over historical data   | I can evaluate my strategy's performance          |
| US-004 | Retail trader        | View equity curve, drawdown, and trade-by-trade results | I can assess risk and return                   |
| US-005 | Retail trader        | Connect my Zerodha account                          | I can paper trade with live market data           |
| US-006 | Strategy researcher  | Iterate rapidly on strategy variations              | I can compare multiple approaches                 |
| US-007 | Strategy researcher  | View the generated AST                              | I can verify the AI correctly interpreted my logic |
| US-008 | Platform developer   | Register new AST node types                         | I can extend the strategy language                |
| US-009 | Platform developer   | Add new indicators to the RAG knowledge base        | The AI can recognize new trading concepts         |

---

## 8. Success Metrics

> [!NOTE]
> **(Illustrative — replace with real targets once baseline data is available)**

| Metric                              | Target          |
|-------------------------------------|-----------------|
| Strategy parse success rate          | *(fill in)*     |
| Average parse-to-backtest latency    | *(fill in)*     |
| Schema validation pass rate          | *(fill in)*     |
| AST generation success rate          | *(fill in)*     |
| User retention (weekly active users) | *(fill in)*     |
| Strategies created per user per week | *(fill in)*     |

---

## 9. Risks

| Risk                                 | Severity | Mitigation                                          |
|--------------------------------------|----------|-----------------------------------------------------|
| LLM non-determinism across calls     | High     | Low temperature (0.2), strict system prompt, schema lock |
| Schema coverage gaps (new indicator types) | Medium | Generic `IndicatorNode` + extensible RAG knowledge base |
| Market data provider dependency (Kite) | Medium  | Abstracted via `map_symbol()` / `get_instrument_token()` helpers |
| Prompt injection / adversarial input | Medium   | System prompt is immutable; user input is isolated from schema |
| DuckDB RAG knowledge base staleness  | Low      | Manual curation; planned automated refresh pipeline  |

---

## 10. Glossary

| Term                   | Definition                                                                    |
|------------------------|-------------------------------------------------------------------------------|
| **AST**                | Abstract Syntax Tree — deterministic, tree-structured representation of a strategy |
| **Canonical JSON**     | The intermediate JSON output from the LLM, conforming to the canonical schema |
| **Execution Context**  | User-provided settings (universe, timeframe, position_side, stocks) that parameterize a strategy |
| **RAG**                | Retrieval-Augmented Generation — enriching LLM prompts with retrieved knowledge |
| **RRF**                | Reciprocal Rank Fusion — algorithm to merge rankings from dense (VSS) and sparse (FTS) search |
| **Blocker**            | A strategy element that prevents deterministic compilation (deprecated in favor of RAG) |
| **Semantic Resolution** | The process of classifying trading terms as parsed (high confidence), assumed (needs confirmation), or unparsed (unknown) |
| **Knowledge Doc**      | An atomic document in the RAG knowledge base representing a single concept (indicator, term, strategy) |
| **Pipeline Stage**     | One of the 7 sequential processing steps from user prompt to validated AST    |
