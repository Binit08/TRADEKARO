# Release Deployment Checklist

This checklist documents the twelve critical deployment blockers identified during the system review. It serves as a release gate to ensure safety, reliability, and accuracy before deploying to any environment.

> [!IMPORTANT]
> **Internet-Facing Deployment Gate**: Do not enable the `/api/v1/run_backtest` endpoint on any internet-facing host until items **#2**, **#11**, **#17**, and **#18** are resolved and verified.
>
> **Real-Money Trading Gate**: Do not run any backtests against real-money decisions until items **#3**, **#4**, **#5**, **#6**, **#7**, **#8**, **#10**, and **#13** are resolved and verified.

---

## Internet-Facing Host Blockers (Required for Public Deployment)

### [x] Blocker #2: Same-Candle Execution Leak (Look-Ahead Bias)
*   **Description**: Order fills occurred on the same candle the signal was generated, leading to look-ahead bias.
*   **Mitigation**:
    *   Enforced the invariant that orders created during candle `t` may only fill on candle `t+1` or later.
    *   Applied strict `>` time check inside `ExecutionEngine.execute()`.
    *   Limit orders only execute at the limit price (no open price improvement rewarding).
    *   Stop orders fill with adverse gap-down/gap-up slippage (`max(stop, open)` for BUY, `min(stop, open)` for SELL).
*   **Regression Tests**:
    *   [test_order_not_filled_on_same_candle](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_execution.py#L213-L227) in `tests/test_execution.py`
    *   [test_limit_and_stop_pricing_details](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_execution.py#L229-L267) in `tests/test_execution.py`

### [x] Blocker #11: API DoS Vulnerabilities and Input Validation
*   **Description**: Lack of input limits, thread-unsafe rate limiter, and oversized AST parsing allowed resource exhaustion.
*   **Mitigation**:
    *   Replaced in-memory rate limiter with thread-safe `cachetools.TTLCache` (LRU bound) and secure client IP resolution (respecting `X-Forwarded-For` only for trusted proxies).
    *   Added Pydantic models with strict bounds checking: symbol length (max 16), valid date objects, initial cash (`gt=0, le=1e10`), commission, and slippage.
    *   Constrained `strategy_ast` to a maximum JSON size (256 KB) and validated recursively against schema.
    *   Wrapped backtest execution in a worker pool (`run_in_executor`) with a hard `60s` timeout limit.
*   **Regression Tests**:
    *   `test_strategy_ast_size_limit_rejection`, `test_strategy_ast_schema_rejection` in [test_api_security.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_security.py#L85-L101)
    *   `test_rate_limiter_limit_and_reset`, `test_trusted_proxy_header` in [test_api_security.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_security.py#L102-L136)
    *   `test_timeout_execution` in [test_api_security.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_security.py#L156-L181)
    *   `test_ast_recursion_depth_limit`, `test_ast_node_count_limit` in [test_api_security.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_security.py#L343-L460)

### [x] Blocker #17: Protective Stop Loss Same-Candle Guard Leak
*   **Description**: Protective stop-loss (SL) or take-profit (TP) checks were bypassed on the entry candle, leaking execution information.
*   **Mitigation**:
    *   Removed `candle.timestamp == position.entry_time` guard in `evaluate_protective_exit()`.
    *   Immediately invoked `_process_protective_exit` right after opening positions on the entry bar in `BacktestEngine._process_fill()` to catch same-candle breach.
*   **Regression Tests**:
    *   [test_entry_candle_protective_exit](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_backtest.py#L196-L278) in `tests/test_backtest.py`

### [x] Blocker #18: API Token Authorization and CORS Allow-List Security
*   **Description**: API authentication used a hardcoded `Bearer secret_token` and CORS allowed wildcards (`*`) with credentials enabled.
*   **Mitigation**:
    *   Removed `secret_token` literal completely from routes, utilities, and tests.
    *   Verify token headers securely using dynamic environment variable `BACKTEST_API_TOKEN` and constant-time validation (`hmac.compare_digest`).
    *   Reject server startup immediately if the token is unset in non-test mode.
    *   Configure CORS with an explicit concrete allow-list (from `BACKTEST_CORS_ORIGINS` or secure defaults) and disable credentials when using wildcards.
*   **Regression Tests**:
    *   [test_api_auth.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_auth.py) (all tests)

---

## Real-Money Decisions Blockers (Required for Production Trading)

### [x] Blocker #3: Double-Counting Capital on Shorts
*   **Description**: Cash and collateral were double-counted during short entries and exits.
*   **Mitigation**:
    *   Deducted margin and fees from cash and added margin + proceeds to collateral upon short entry.
    *   MTM valuation: position value contributes `-(current_price * qty) + short_proceeds`.
    *   On close, collateral is released, and buy cover costs + fees are deducted.
*   **Regression Tests**:
    *   [test_short_accounting_entry](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_portfolio.py#L107-L132) in `tests/test_portfolio.py`

### [x] Blocker #4: Mutating Pending Orders During Iteration
*   **Description**: Modifying `self.pending_orders` during order execution iteration shifted list indices, skipping subsequent orders.
*   **Mitigation**:
    *   Collected orders using a snapshot copy `list(self.pending_orders)` before processing.
    *   ValueError during fill processing no longer silently rejects orders but propagates or excludes failed fills with structured logging.
*   **Regression Tests**:
    *   [test_execute_multiple_pending_orders](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_execution.py#L269-L298) in `tests/test_execution.py`
    *   [test_rejected_short_fill_is_not_recorded_in_history](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_execution.py#L174-L211) in `tests/test_execution.py`

### [x] Blocker #5: Pyramiding Position Sizing
*   **Description**: PositionSizer subtracted `existing_notional` at current prices, leading to incorrect sizing on pyramid entries.
*   **Mitigation**:
    *   Introduced `pyramid_index` parameter in `PositionSizer.size()`.
    *   Size each layer as a fresh, independent fraction of equity/cash rather than subtracting `existing_notional`.
    *   Isolated legacy rebalancing semantics to `rebalance_to_target()`.
*   **Regression Tests**:
    *   [test_pyramiding_sizing_rising_prices](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_backtest_advanced.py#L262-L302) in `tests/test_backtest_advanced.py`
    *   [test_pyramiding_sizing_falling_prices](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_backtest_advanced.py#L304-L344) in `tests/test_backtest_advanced.py`
    *   [test_rebalance_to_target](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_backtest_advanced.py#L346-L358) in `tests/test_backtest_advanced.py`

### [x] Blocker #6: Pyramiding Counter desync
*   **Description**: Additive branches failed to increment `position.entries`, leading to stale `_can_pyramid` checks.
*   **Mitigation**:
    *   Bumps `position.entries` on every additive fill.
    *   Normalised side argument types using `SignalType`.
    *   Maintained original entry price/time snapshots (`first_entry_price`, `first_entry_time`) in closed-trade logs.
*   **Regression Tests**:
    *   [test_pyramiding_entries_and_first_entry_snapshot](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_backtest_advanced.py#L360-L402) in `tests/test_backtest_advanced.py`
    *   [test_portfolio_pyramiding_entries_count](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_backtest_advanced.py#L404-L426) in `tests/test_backtest_advanced.py`

### [x] Blocker #7: Swallow of Evaluator Exceptions in SignalEngine
*   **Description**: Swallowing exceptions and returning `HOLD` masked critical strategy code bugs.
*   **Mitigation**:
    *   Narrowed catches to `KeyError`, `ValueError`, and `TypeError`. Re-raised all other exceptions.
    *   streak-based error threshold: fails fast and crashes on persistent errors.
    *   Surfaced error logs/warnings in `BacktestResponse` so API clients see strategy issues.
*   **Regression Tests**:
    *   [test_unexpected_exception_propagates_immediately](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_signal_engine.py#L148-L153) in `tests/test_signal_engine.py`
    *   [test_consecutive_evaluator_failures_raises_runtime_error](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_signal_engine.py#L155-L175) in `tests/test_signal_engine.py`
    *   [test_warnings_surfaced_in_backtest_response](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_signal_engine.py#L177-L211) in `tests/test_signal_engine.py`

### [x] Blocker #8: O(N²) Indicator Recomputations
*   **Description**: Indicator calculations ran over full history per candle, creating quadratic overhead.
*   **Mitigation**:
    *   Optimized path to O(N) by pre-computing technical indicators once over the full loaded DataFrame, then indexing snapshots in the replay loop.
*   **Regression Tests**:
    *   [test_runtime_feed_to_indicator_pipeline](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_indicator_runtime.py#L57-L142) in `tests/test_indicator_runtime.py`
    *   Dynamic TA-Lib tests in [test_indicator_engine.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_indicator_engine.py)

### [x] Blocker #10: Un-normalized Columns, Timezones and Cache Versioning
*   **Description**: Kite API returned un-normalized data which desynced on re-read, and missing tz bounds.
*   **Mitigation**:
    *   Regex symbol validation including indices.
    *   Explicit column selection, lowercase normalization before CSV save.
    *   Converted boundary date filters to UTC timezone-aware.
    *   Added cached file suffix versioning (`_VERSION`). Jittered exponential backoff for downloads.
*   **Regression Tests**:
    *   [test_market_data_loader_load_from_fixture](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_data_loader.py#L79-L116) in `tests/test_data_loader.py`
    *   [test_market_data_loader_intraday_dst](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_data_loader.py#L118-L166) in `tests/test_data_loader.py`

### [x] Blocker #13: Inconsistent Drawdown Baselines
*   **Description**: Metrics engine and API endpoints computed drawdowns with different baseline formulas.
*   **Mitigation**:
    *   Consolidated drawdown percentage calculation into `Portfolio.equity_curve()` as the single source of truth.
    *   Removed arbitrary placeholder sentinels from history.
    *   Metrics engine validates that initial equity is strictly positive.
*   **Regression Tests**:
    *   [test_drawdown_consistency](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_security.py#L183-L242) in `tests/test_api_security.py`
    *   [test_metrics_engine_non_positive_initial_equity](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_api_security.py#L244-L251) in `tests/test_api_security.py`

---

## Build and Stub Files Verification
*   **[x] Blocker #1**: Applications crash due to missing `fetch_historical` in `app/data/loader.py`.
    *   *Mitigation*: Implemented parquet downloader and cleaned up stale unused stub files in portfolio, risk, indicators, metrics, and reports.
    *   *Tests*: `test_fetch_historical_success`, `test_fetch_historical_failure` in [test_data_loader.py](file:///Users/krishbajoria/Desktop/BackTesting/Backtesting_Engine/tests/test_data_loader.py#L9-L77)
