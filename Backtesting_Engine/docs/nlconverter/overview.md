# Natural Language Converter (NLconverter)

## Introduction

The NLconverter is a sophisticated middleware and frontend application designed to bridge the gap between human intuition and machine-executable trading logic. 

Instead of forcing users to learn Python, Pandas, or proprietary scripting languages (like PineScript), the NLconverter allows users to type strategies in plain English. For example:
> *"Buy AAPL when the 14-period RSI crosses below 30. Sell when the RSI crosses above 70, with a 5% stop loss."*

The NLconverter securely processes this request, interfaces with a Large Language Model (Google Gemini), and transforms the sentence into a strictly typed **JSON Abstract Syntax Tree (AST)**.

---

## Architectural Deep Dive

The NLconverter is a full-stack application living entirely separately from the Backtesting Engine. It is composed of three primary layers:

### 1. The Presentation Layer (Next.js Frontend)
Located in `NLconverter/frontend`, this is a modern React application utilizing Next.js for server-side rendering and routing.

**Key Responsibilities:**
- **Strategy Builder UI**: A chat-like interface where users can input their natural language strategies.
- **Visualizer**: Uses advanced charting libraries (like Lightweight Charts) to render the exact equity curves, drawdowns, and historical entry/exit markers directly onto candlestick charts.
- **Parameter Configuration**: Provides modals and sidebars to define the Execution Context (slippage, commission, margin, initial capital, date ranges).

### 2. The API Layer (FastAPI Backend)
Located in `NLconverter/backend`, this is the orchestration brain of the converter.

**Key Responsibilities:**
- **Prompt Engineering Engine**: The backend does not simply pass the user's string to Gemini. It wraps the user's request in an extensive, heavily engineered prompt. This prompt forces the LLM to adhere perfectly to our proprietary JSON AST schema, preventing hallucinated variables or non-existent indicators.
- **Proxy/Gateway**: Once the AST is generated and validated, this backend securely proxies the backtest request to the Core Backtesting Engine running on Port 8002 over an internal network, bypassing the need to expose the execution engine to the public internet.
- **Data Normalization**: The raw outputs from the Backtesting Engine are highly dense. The API layer normalizes trade data (e.g., standardizing `LONG`/`SHORT` nomenclature) before shipping the JSON payload to the frontend.

### 3. The Persistence Layer (Database)
The NLconverter backend manages state via a SQL database (PostgreSQL/SQLite) orchestrated via SQLAlchemy.

**Key Entities:**
- **`User`**: Handles authentication linking via Supabase and stores encrypted broker API keys (e.g., Zerodha Kite tokens).
- **`StrategyRecord`**: Stores the raw human prompt *and* the resulting JSON AST. This immutable pairing is critical; if the LLM updates its model weights, we have a historical record of what prompt generated what AST.
- **`BacktestRecord`**: The holy grail of reproducibility. It stores **all** simulation inputs (slippage, margin, exact AST, timeframe) alongside **all** simulation outputs (trades, equity curve, metrics). This guarantees that historical backtests can be audited identically years later.

---

## The Request Lifecycle (NL to Execution)

Understanding the data flow is critical for extending the system.

1. **Ingestion**: User clicks "Run Backtest" on the Next.js UI.
2. **Translation**: The FastAPI backend routes the text to `backend.services.strategy_service`.
3. **LLM Generation**: A secure API call is made to Google Gemini via HTTP. The LLM replies with a JSON payload.
4. **Validation Check**: The backend checks the payload against `app/ast/validator.py` logic to ensure structural integrity (e.g., ensuring `node_type` is valid, and children are correctly formatted).
5. **Execution Orchestration**: The backend calls `backend.services.backtest_service`, making an authenticated POST request to `http://localhost:8002/api/v1/run_backtest`.
6. **Persistence**: The backend awaits the massive JSON response from Port 8002, saves the entire payload into the `BacktestRecord` table via SQLAlchemy, and yields the ID to the frontend.

---

## Security & Failure Handling

### Injection Attacks (RCE Prevention)
The most critical design decision in the NLconverter is the absolute refusal to use `eval()` or dynamic Python execution. Traditional algorithmic platforms that accept code strings are vulnerable to Remote Code Execution (RCE). 
By forcing the LLM to output a passive data structure (a JSON AST) rather than executable code, the system physically cannot execute malicious server commands.

### Hallucination Management
LLMs hallucinate. If Gemini invents a technical indicator (e.g., "SuperTrendPro"), the AST Validator acts as a hard gate. If a `node_type` or `indicator_name` is not strictly defined in our schema, the backend rejects the AST, logs the error, and prompts the user to rephrase their request.
