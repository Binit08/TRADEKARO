# API Reference

| Field          | Value                                  |
|----------------|----------------------------------------|
| **Project**    | TradeKaro — NLconverter                |
| **Doc Type**   | API Reference                          |
| **Version**    | 1.0.0                                  |
| **Author**     | TradeKaro Team                         |
| **Last Updated** | 2026-09-02                           |

---

## Overview

The NLconverter backend exposes a REST API via FastAPI on port **8000**. All endpoints (except `/health`) require authentication.

> **Live API Docs**: When running locally, visit `http://localhost:8000/docs` for the auto-generated Swagger UI, or `http://localhost:8000/openapi.json` for the raw OpenAPI schema.

### Base URL

```
http://localhost:8000
```

### Authentication

All protected endpoints require **both**:

| Mechanism         | Header                       | Description                                |
|-------------------|------------------------------|--------------------------------------------|
| API Key           | `X-API-Key: <your-api-key>`  | Static key from `API_KEY` env var          |
| Bearer JWT        | `Authorization: Bearer <jwt>` | Supabase JWT token (user identity)         |

### Rate Limiting

- **Window**: Configurable via `RATE_LIMIT_DURATION` (default: 60 seconds)
- **Max requests per window**: Configurable via `MAX_REQUESTS_PER_DURATION` (default: 10)
- **Scope**: Per client IP address
- **Response on exceed**: `429 Too Many Requests`

---

## Health Check

### `GET /health`

Check if the server is running.

| Field        | Value       |
|--------------|-------------|
| Auth         | None        |
| Rate Limited | No          |

**Response** `200 OK`:
```json
{"status": "ok"}
```

---

## Strategy Endpoints

### `POST /api/strategy`

Generate a strategy by running the 7-stage compilation pipeline: Semantic Resolution → Compilation → Schema Validation → AST Generation → AST Validation → Audit.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Request Body** (`StrategyRequest`):

| Field                 | Type                | Required | Default      | Description                                    |
|-----------------------|---------------------|----------|--------------|------------------------------------------------|
| `prompt`              | `string`            | ✅       |              | Natural language strategy (max 10,000 chars)   |
| `name`                | `string \| null`    |          | `null`       | Strategy name                                  |
| `tag`                 | `string \| null`    |          | `null`       | Strategy tag                                   |
| `description`         | `string \| null`    |          | `null`       | Strategy description                           |
| `market_type`         | `"equity" \| "futures"` |      | `"equity"`   | Market type — selects appropriate JSON Schema  |
| `semantic_resolutions` | `Resolution[] \| null` |      | `null`       | Pre-resolved semantic terms (skips resolver)   |
| `execution_context`   | `object \| null`    |          | `null`       | Universe, timeframe, position_side, stocks     |

`Resolution` object:

| Field        | Type     | Description                        |
|--------------|----------|------------------------------------|
| `source`     | `string` | The original term from the prompt  |
| `resolution` | `string` | The selected canonical resolution  |

**Response — Success** `200 OK`:
```json
{
  "status": "ok",
  "id": 42,
  "prompt": "Buy when RSI drops below 30",
  "canonical_json": { ... },
  "ast_json": { ... },
  "_meta": {
    "request_id": "a1b2c3d4",
    "stage_timings": {
      "Stage 2: Semantic Resolver": 1.234,
      "Stage 3: Compiler": 2.567
    },
    "token_usage": {
      "promptTokenCount": 2500,
      "candidatesTokenCount": 200,
      "totalTokenCount": 2700
    }
  }
}
```

**Response — Semantic Approval Required** `200 OK`:
```json
{
  "status": "semantic_approval",
  "approval_items": [
    {
      "type": "assumed",
      "source": "RSI",
      "candidates": ["RSI", "Relative Strength Index"],
      "confidence": 0.65
    }
  ],
  "current_strategy": "Buy when RSI drops below 30"
}
```

**Error Responses**:

| Status | Condition                                   |
|--------|---------------------------------------------|
| `400`  | Schema validation or AST validation failed  |
| `403`  | Invalid API key                              |
| `422`  | Prompt too long or invalid execution context |
| `429`  | Rate limit exceeded                          |
| `500`  | LLM error or internal failure                |

---

### `GET /api/strategy/{strategy_id}`

Fetch a single strategy by ID. Only returns strategies owned by the authenticated user.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Path Parameters**: `strategy_id` (integer)

**Response** `200 OK`:
```json
{
  "status": "ok",
  "id": 42,
  "name": "RSI Strategy",
  "tag": "momentum",
  "description": "...",
  "prompt": "Buy when RSI drops below 30",
  "canonical_json": { ... },
  "ast_json": { ... },
  "execution_context": { ... },
  "created_at": "2026-09-01T10:00:00"
}
```

**Error**: `404 Not Found` if strategy doesn't exist or belongs to another user.

---

### `GET /api/strategies`

List all strategies for the authenticated user with pagination.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Query Parameters**:

| Param    | Type  | Default | Description            |
|----------|-------|---------|------------------------|
| `limit`  | `int` | `10`    | Number of results      |
| `offset` | `int` | `0`     | Pagination offset      |

**Response** `200 OK`:
```json
{
  "status": "ok",
  "has_more": true,
  "total_count": 25,
  "strategies": [
    {
      "id": 42,
      "name": "RSI Strategy",
      "tag": "momentum",
      "description": "...",
      "prompt": "Buy when RSI drops below 30",
      "status": "ok",
      "created_at": "2026-09-01T10:00:00",
      "canonical_json": { ... },
      "ast_json": { ... },
      "execution_context": null,
      "logs": null
    }
  ]
}
```

> **Note**: `logs` and `execution_context` fields are deferred (not loaded from DB) for performance.

---

## Backtest Endpoints

### `POST /api/backtest`

Run a backtest by proxying the request to the Backtesting Engine (port 8002). Persists results in the database.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Request Body** (`ProxyBacktestRequest`):

| Field                     | Type            | Required | Default        | Validation                        |
|---------------------------|-----------------|----------|----------------|-----------------------------------|
| `strategy_ast`            | `object`        | ✅       |                | The AST JSON to execute           |
| `start`                   | `string`        | ✅       |                | YYYY-MM-DD, must be before `end`  |
| `end`                     | `string`        | ✅       |                | YYYY-MM-DD                        |
| `timeframe`               | `string`        | ✅       |                | One of: `1m`, `2m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1wk`, `1mo` |
| `initial_cash`            | `float`         | ✅       |                | Must be positive                  |
| `symbol`                  | `string \| null` |         |                | Single symbol (e.g., "RELIANCE")  |
| `symbols`                 | `string[] \| null` |       |                | Multi-symbol list                 |
| `exchange`                | `string`        |          | `"NSE"`        | Exchange code                     |
| `strategy_id`             | `int \| null`   |          |                | Link to strategy record           |
| `position_size`           | `float`         |          | `1.0`          | Must be positive                  |
| `position_size_type`      | `string`        |          | `"fixed_qty"`  | `"fixed_qty"` or `"percent_equity"` |
| `commission_rate`         | `float`         |          | `0.0001`       | Non-negative                      |
| `slippage_bps`            | `float`         |          | `2.0`          | Non-negative                      |
| `allow_short`             | `bool`          |          | `false`        |                                   |
| `position_side`           | `string \| null` |         |                | Trade direction constraint        |
| `close_on_opposite_signal` | `bool`         |          | `true`         |                                   |
| `market_type`             | `string`        |          | `"equity"`     |                                   |
| `multiplier`              | `float \| null` |          |                | Futures contract multiplier       |
| `margin`                  | `float \| null` |          |                | Futures margin                    |
| `expiry`                  | `string \| null` |         |                | Futures expiry date               |

**Response** `200 OK`:
```json
{
  "backtest_id": 15,
  "metrics": { "net_pnl": 12500, "return_pct": 12.5, "win_rate": 0.65, ... },
  "equity_curve": [{"time": "2025-01-01", "value": 100000, "benchmark_value": 100000}, ...],
  "drawdown_curve": [{"time": "2025-01-01", "drawdownPct": 0}, ...],
  "trades": [
    {"symbol": "RELIANCE", "side": "LONG", "entry_time": "...", "exit_time": "...", "qty": 10, "entry_price": 2500, "exit_price": 2600, "pnl": 1000, "return_pct": 4.0}
  ],
  "ohlc_data": [...]
}
```

---

### `GET /api/backtests`

List all backtests for the authenticated user with pagination.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Query Parameters**: `limit` (default 10), `offset` (default 0)

**Response** `200 OK`:
```json
{
  "status": "ok",
  "has_more": false,
  "total_count": 5,
  "data": [
    {
      "id": 15,
      "symbol": "RELIANCE",
      "timeframe": "1d",
      "start_date": "2025-01-01",
      "end_date": "2025-06-30",
      "initial_cash": 100000,
      "net_profit": 12500,
      "total_return": 12.5,
      "win_rate": 0.65,
      "total_trades": 20,
      "status": "ok",
      "created_at": "2026-09-01T10:00:00"
    }
  ]
}
```

> **Note**: `ohlc_data`, `trades`, `equity_curve`, and `drawdown_curve` are deferred for performance.

---

### `GET /api/backtests/{backtest_id}`

Fetch a single backtest with full data (equity curve, trades, OHLC data).

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Path Parameters**: `backtest_id` (integer)

**Response** `200 OK`: Full backtest data including `equity_curve`, `drawdown_curve`, `trades`, `ohlc_data`.

**Error**: `404 Not Found` if backtest doesn't exist or belongs to another user.

---

## Instrument Endpoints

### `GET /api/instruments`

Fetch the full list of NSE equity instruments from the Kite API. Results are cached in-memory.

| Field        | Value       |
|--------------|-------------|
| Auth         | None        |
| Rate Limited | No          |

**Response** `200 OK`:
```json
{
  "status": "ok",
  "instruments": [
    {"value": "RELIANCE", "label": "Reliance Industries"},
    {"value": "TCS", "label": "Tata Consultancy Services"}
  ]
}
```

---

### `GET /api/futures`

Fetch NFO futures instruments with expiry details from the Kite API. Results are cached in-memory.

| Field        | Value       |
|--------------|-------------|
| Auth         | None        |
| Rate Limited | No          |

**Response** `200 OK`:
```json
{
  "status": "ok",
  "data": [
    {
      "name": "NIFTY",
      "type": "INDEX",
      "expiries": [
        {"date": "2026-09-25", "lot_size": 25, "tradingsymbol": "NIFTY26SEP25FUT"}
      ]
    }
  ]
}
```

---

## Kite Auth Endpoints

### `GET /api/auth/kite/url`

Get the Zerodha Kite Connect login URL for the authenticated user.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | Bearer JWT                   |

**Response** `200 OK`:
```json
{"login_url": "https://kite.zerodha.com/connect/login?..."}
```

---

### `POST /api/auth/kite/callback`

Exchange a Kite request token for an access token and save it to the user profile.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | Bearer JWT                   |

**Request Body**:

| Field            | Type     | Required | Description              |
|------------------|----------|----------|--------------------------|
| `request_token`  | `string` | ✅       | Token from Kite callback |

**Response** `200 OK`:
```json
{"status": "success", "message": "Kite connected successfully"}
```

---

### `GET /api/auth/kite/status`

Check if the user has a valid (non-expired) Kite session. Tokens expire daily at midnight IST.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | Bearer JWT                   |

**Response** `200 OK`:
```json
{"is_connected": true}
```

or

```json
{"is_connected": false, "reason": "Token expired at midnight IST"}
```

---

## Portfolio Endpoints

### `GET /api/portfolio/positions`

Fetch the user's live net positions from Kite Connect.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | Bearer JWT                   |

**Response** `200 OK`:
```json
{
  "status": "success",
  "positions": [
    {
      "symbol": "RELIANCE",
      "qty": 10,
      "ltp": 2550.50,
      "pnl": 505.0,
      "pnlPct": 1.98,
      "isUp": true
    }
  ]
}
```

**Error**: `401` if Kite not connected.

---

## Paper Trade Endpoints

### `POST /api/paper_trade/start`

Start a paper trade session using the user's Kite access token for live market data.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |
| Rate Limited | Yes                          |

**Request Body** (`ProxyPaperTradeRequest`):

| Field          | Type       | Required | Default  | Description                    |
|----------------|-----------|----------|----------|--------------------------------|
| `symbols`      | `string[]` | ✅       |          | List of trading symbols        |
| `timeframe`    | `string`   |          | `"1m"`   | Chart timeframe                |
| `strategy_ast` | `object`   | ✅       |          | The AST JSON to execute        |
| `exchange`     | `string`   |          | `"NSE"`  | Exchange code                  |

**Error**: `400` if Kite access token not found (broker not connected).

---

### `GET /api/paper_trade/sessions`

List active paper trade sessions from the Backtesting Engine.

| Field        | Value                        |
|--------------|------------------------------|
| Auth         | X-API-Key + Bearer JWT       |

**Response**: Proxied from Backtesting Engine `GET /api/v1/paper_trade/sessions`.
