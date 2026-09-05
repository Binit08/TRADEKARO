<div align="center">
  <h1>🚀 TRADEKARO</h1>
  <p><strong>AI-Powered Algorithmic Trading Platform</strong></p>
  
  <p>
    <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Frontend-Next.js-black?style=for-the-badge&logo=next.js" alt="Next.js" /></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" /></a>
    <a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/AI-Google_Gemini-4285F4?style=for-the-badge&logo=google" alt="Google Gemini" /></a>
    <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql" alt="PostgreSQL" /></a>
  </p>
</div>

<br />

**TradeKaro** is an advanced AI-powered algorithmic trading platform that turns natural-language trading ideas into validated, backtestable, and paper-tradable strategies. 

It helps traders move from an idea to an executable strategy **without writing trading code**. Users can describe their strategy in natural language, validate the generated strategy, backtest it on historical data, screen the market, and run it in paper trading.

---

## ✨ Key Features

*   **🗣️ Natural-Language Strategy Creation** — Describe entry, exit, indicators, and risk rules without writing code.
*   **🧠 AI Strategy Generation** — Uses an AI pipeline to convert trader intent into a structured strategy.
*   **📚 RAG-Based Grounding** — Retrieves relevant trading terminology and knowledge to reduce AI hallucinations.
*   **✅ Strict Validation** — Generated strategies are validated against predefined schemas before execution.
*   **🌳 Strategy AST** — Converts validated strategies into a structured Abstract Syntax Tree for deterministic execution.
*   **📈 Historical Backtesting** — Replay historical market data and evaluate strategy performance.
*   **🛡️ Look-Ahead Bias Protection** — Signals generated at candle `t` cannot execute until `t+1` or later.
*   **⚙️ Realistic Execution Simulation** — Supports slippage, commissions, latency, and partial-fill modelling.
*   **📝 Paper Trading** — Runs validated strategies against live market events without placing real orders.
*   **🔍 Market Screening** — Find instruments matching strategy conditions.
*   **⚡ Real-Time Updates** — Redis and WebSockets provide low-latency trading-state updates.
*   **📊 Portfolio Analytics** — Analyze P&L, drawdown, Sharpe ratio, win rate, profit factor, and trade history.
*   **🔗 Multi-Broker Integration** — Supports broker market-data and trading integrations such as Zerodha Kite and Binance.

---

## 🏗️ System Architecture

The ecosystem seamlessly blends a high-performance web interface, an intelligent LLM-powered parser, and a rigorous execution engine.

### 🧩 Core Repositories

| Repository | Stack | Description |
| :--- | :--- | :--- |
| **[`NLconverter`](./NLconverter)** | Next.js / FastAPI / Gemini | The AI-driven bridge. It provides the UI for strategy creation and uses Gemini LLM + RAG to securely translate unstructured text into validated AST structures. |
| **[`Backtesting_Engine`](./Backtesting_Engine)** | Python / FastAPI / Pandas-TA | The core execution engine. Handles historical backtesting, strict AST parsing, order management, realistic simulation, and live paper-trading. |

---

## 🚀 Getting Started

Follow these steps to launch the entire TradeKaro ecosystem locally.

### 1️⃣ Configure API Keys

The AI parser relies on the Google Gemini API. Navigate to the `NLconverter` directory to set up your environment:

```bash
cd NLconverter
cp .env.example .env
```

Open `.env` and insert your API key:
```ini
GOOGLE_GEMINI_API_KEY=your_actual_google_gemini_api_key_here
```

Similarly, configure any broker API keys or database credentials inside the `Backtesting_Engine` environment files.

### 2️⃣ Boot the Ecosystem

We provide a unified startup script inside `NLconverter` to initialize the Frontend, the Backend, and the Backtesting Engine simultaneously.

```bash
cd NLconverter
chmod +x start_services.sh
./start_services.sh
```

#### 🌐 Active Services

Once started, the following services will be available:

*   **🖥️ User Interface (Next.js):** [http://localhost:3000](http://localhost:3000)
*   **🧠 NL API Gateway (FastAPI):** [http://localhost:8000](http://localhost:8000)
*   **⚙️ Backtest Engine (FastAPI):** [http://localhost:8002](http://localhost:8002)

---

## 📚 Comprehensive Documentation

Explore our extensive documentation suites located in each respective component:

*   **NLconverter Docs:** [`/NLconverter/documentation`](./NLconverter/documentation/) — PRDs, Architecture, Security, and UI User Guides.
*   **Backtesting Engine Docs:** [`/Backtesting_Engine/docs`](./Backtesting_Engine/docs/) — Execution modeling, AST schema definitions, and API routes.

---
<div align="center">
  <sub>Built with ❤️ by the TradeKaro Team.</sub>
</div>
