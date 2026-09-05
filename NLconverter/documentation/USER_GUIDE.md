# User Guide

| Field          | Value                                  |
|----------------|----------------------------------------|
| **Project**    | TradeKaro — NLconverter                |
| **Doc Type**   | User Guide                             |
| **Version**    | 1.0.0                                  |
| **Author**     | TradeKaro Team                         |
| **Last Updated** | 2026-09-02                           |

---

## 1. Getting Started

Welcome to TradeKaro! The NLconverter platform allows you to design algorithmic trading strategies using plain English and instantly test them against historical or live market data.

### 1.1 Logging In

1. Open the application in your browser (default: `http://localhost:3000`).
2. You will be redirected to the Supabase login page.
3. Authenticate using your email/password or SSO provider.
4. Once logged in, you will land on the **Dashboard**, where you can see your recent strategies and backtests.

### 1.2 Connecting Your Broker (Zerodha Kite)

To trade live or use Paper Trading with real-time data, you must connect your Zerodha account:
1. Navigate to the **Profile** or **Settings** section in the sidebar.
2. Click **Connect to Kite**.
3. You will be redirected to Zerodha's login page.
4. Enter your credentials and authorize the TradeKaro app.
5. You will be redirected back, and your session will be active until midnight.

---

## 2. Writing a Strategy Prompt

The **Strategy Editor** is where you describe your trading rules. Be clear and specific.

### 2.1 Prompt Structure

A good strategy prompt typically contains three sections:
1. **Entry Rules**: When to buy (or short).
2. **Exit Rules**: When to sell (or cover).
3. **Risk Management**: Stop loss, take profit, and position sizing.

**Example Prompt**:
> "Buy when the 14-period RSI crosses above 30 and the MACD line is above the signal line. Sell when RSI crosses below 70. Set a stop loss at 2% below the entry price and a take profit at a 2:1 risk-reward ratio."

### 2.2 Supported Indicators and Patterns

The AI understands hundreds of trading terms via its RAG knowledge base. Common indicators include:
- **Momentum**: RSI, MACD, Stochastic
- **Trend**: SMA, EMA, SuperTrend, ADX
- **Volatility**: Bollinger Bands, ATR, Keltner Channels
- **Custom**: Knoxville Divergence

### 2.3 Condition Types

You can use complex logic in your descriptions:
- **Comparisons**: "greater than", "less than", "equal to"
- **Crossovers**: "crosses above", "crosses below"
- **Sequences**: "consecutive green candles", "rallied continuously for 5 days"
- **Temporal**: "only between 10:00 AM and 2:30 PM", "on Fridays"

---

## 3. Understanding Semantic Resolution

When you click **Generate Strategy**, the AI analyzes your prompt. It classifies trading terms into three categories:

1. 🟢 **Parsed (High Confidence)**: The AI perfectly understood the term (e.g., "RSI" → Relative Strength Index). No action needed.
2. 🟡 **Assumed (Ambiguous)**: The AI found multiple possible meanings. For example, if you say "Moving Average", it might assume "Simple Moving Average (SMA)", but it wants you to confirm.
3. 🔴 **Unparsed (Unknown)**: The AI doesn't recognize the term in its knowledge base.

### 3.1 The AI Clarification Modal

If any terms are **Assumed** or **Unparsed**, the **AI Clarification Modal** will pop up before the strategy is compiled.
- For assumed terms, select the correct interpretation from the dropdown list.
- Once you resolve the ambiguities, click **Confirm & Compile** to proceed.

---

## 4. Reading Strategy Output

Once compiled, you will see the **Strategy Summary** panel.

1. **Validation Status**: A green checkmark ✅ indicates the strategy was successfully converted into executable code (the AST).
2. **Canonical JSON**: This tab shows the structured representation of your rules (Indicators, Entry, Exit, Risk).
3. **AST**: This tab shows the highly technical Abstract Syntax Tree that the Backtesting Engine will execute. (You usually don't need to read this).

---

## 5. Running a Backtest

With a compiled strategy, click **Run Backtest** to test it on historical data.

### 5.1 Configuration

Fill out the Backtest Configuration Form:
- **Symbol(s)**: Select one or more instruments (e.g., `RELIANCE`, `NIFTY 50`).
- **Market Type**: Choose Equity or Futures.
- **Timeframe**: Select the chart interval (e.g., `1m`, `5m`, `1d`).
- **Date Range**: Set the Start Date and End Date.
- **Initial Capital**: Starting cash (e.g., `100000`).
- **Position Size**: Configure how much capital to risk per trade.

Click **Start Backtest**.

### 5.2 Reading Results

When the backtest completes, you will see:
- **Metrics Dashboard**: Net P&L, Win Rate, Total Return %, Max Drawdown, Total Trades.
- **Equity Curve Chart**: Visualizes your portfolio value over time against a buy-and-hold benchmark.
- **Drawdown Chart**: Shows the depth of peak-to-trough losses.
- **Trade List**: A chronological table of every entry and exit, including prices and individual trade P&L.
- **OHLC Chart**: (If enabled) A TradingView-style candlestick chart plotting the entries and exits directly on the price action.

---

## 6. Paper Trading

Paper Trading allows you to forward-test your strategy with live market data without risking real money.

1. Ensure your Zerodha Kite account is connected (required for live data).
2. On your compiled strategy, click **Paper Trade**.
3. Select the symbols and timeframe.
4. Click **Start Paper Trading Session**.
5. You can monitor active paper trades in the **Paper Trading Dashboard**.

---

## 7. Current Limitations

Please be aware of the following system limits:
- **Subjective Concepts**: Terms like "liquidity sweep", "order block", or "support zone" cannot be compiled unless you define them mathematically.
- **Multi-Timeframe Logic**: Checking a 1-day indicator on a 5-minute chart within the same strategy is not currently supported.
- **Dynamic Variables**: The system cannot store path-dependent state (e.g., "count the number of red candles since the last crossover and buy if the count is prime").

For a full list of technical limitations, see [NL_LIMITATIONS.md](./NL_LIMITATIONS.md).

---

## 8. FAQ

**Q: Why did my strategy fail to compile?**
A: Ensure you are clearly defining entry and exit conditions. If the AI cannot deterministically map your words to mathematical rules, compilation will fail.

**Q: Can I trade Options?**
A: Currently, only Equities (NSE) and Futures (NFO) are supported. Options support is on the roadmap.

**Q: Where does the market data come from?**
A: The system fetches historical and live instrument data via your connected Zerodha Kite API account.
