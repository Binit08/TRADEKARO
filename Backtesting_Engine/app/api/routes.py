from fastapi import APIRouter, HTTPException, Depends, status, Request, WebSocket, WebSocketDisconnect
from app.api.models import BacktestRequest, BacktestResponse, OHLCCandle, PaperTradeRequest
from app.core.backtest_engine import BacktestEngine
from app.core.historical_feed import HistoricalReplayFeed
from app.data.loader import MarketDataLoader
from app.execution.simulator import ExecutionEngine
from app.indicators.indicator_engine import IndicatorEngine
from app.metrics.metrics_engine import MetricsEngine
from app.portfolio.portfolio import Portfolio
from app.signal.signal_engine import SignalEngine
from app.config.settings import StrategySettings
from app.reports.trade_log import trades_to_dataframe

import pandas as pd
import math
import time
import os
import hmac
import logging
import traceback
import threading
from cachetools import TTLCache

if "BACKTEST_API_TOKEN" not in os.environ and "PYTEST_CURRENT_TEST" not in os.environ:
    raise RuntimeError("BACKTEST_API_TOKEN environment variable is not set")

router = APIRouter()

# Parse TRUSTED_PROXIES from environment variable
trusted_proxies_env = os.getenv("TRUSTED_PROXIES", "")
if trusted_proxies_env:
    TRUSTED_PROXIES = [ip.strip() for ip in trusted_proxies_env.split(",") if ip.strip()]
else:
    TRUSTED_PROXIES = []

# Bounded, thread-safe cache for rate limiting per client IP
_RATE_LIMIT_CACHE = TTLCache(maxsize=10000, ttl=60)
_RATE_LIMIT_LOCK = threading.Lock()

def get_client_ip(request: Request) -> str:
    """Extract client IP address from the request.

    Note that the X-Forwarded-For parsing is single-hop only; for multi-hop,
    the operator must configure trusted proxies as a list ordered from outermost to innermost.
    """
    direct_ip = request.client.host if request.client else "unknown"
    if TRUSTED_PROXIES and direct_ip in TRUSTED_PROXIES:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            parts = [p.strip() for p in xff.split(",")]
            if parts:
                return parts[0]
    return direct_ip

def check_rate_limit(request: Request):
    """Check request rate limit per client IP.

    Note: We keep both the inline timestamp filter and the TTLCache container:
    - The inline filter handles within-list expiry (removing timestamps older than 60 seconds).
    - The TTLCache handles cross-IP eviction (cleaning up entire inactive IP entries from memory).
    """
    client_ip = get_client_ip(request)
    now = time.time()
    with _RATE_LIMIT_LOCK:
        history = _RATE_LIMIT_CACHE.get(client_ip, [])
        history = [t for t in history if now - t < 60]
        if len(history) >= 10:
            raise HTTPException(status_code=429, detail="Too many requests")
        history.append(now)
        _RATE_LIMIT_CACHE[client_ip] = history

def get_current_user(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = parts[1]
    
    expected_token = os.environ.get("BACKTEST_API_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500, detail="API Token not configured on server")
        
    if not hmac.compare_digest(token, expected_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

def verify_token(request: Request):
    get_current_user(request)

@router.get("/health")
def health():
    return {"status": "ok"}

def create_backtest_engine(
    initial_cash: float,
    settings: StrategySettings,
    loader: MarketDataLoader,
) -> BacktestEngine:
    """Factory to construct a fresh, independent BacktestEngine instance per request.
    
    HARD REQUIREMENT: Per-request construction is mandatory to prevent cross-request
    state pollution and concurrency issues, as the engine and its internal subcomponents
    (Portfolio, SignalEngine, execution, metrics) are stateful and not thread-safe.
    """
    return BacktestEngine(
        loader=loader,
        feed=HistoricalReplayFeed,
        indicator=IndicatorEngine(),
        signal=SignalEngine(),
        execution=ExecutionEngine(qty=1.0),
        portfolio=Portfolio(initial_cash=initial_cash),
        metrics=MetricsEngine(),
        indicator_configs=[],
        settings=settings,
    )

@router.post("/api/v1/run_backtest", response_model=BacktestResponse, dependencies=[Depends(check_rate_limit), Depends(verify_token)])
def run_backtest(req: BacktestRequest):
    # HARD REQUIREMENT: Fresh engine and dependencies must be constructed per request
    # to prevent cross-tenant/cross-request state pollution and concurrency issues.
    loader = MarketDataLoader()
    
    settings = StrategySettings(
        position_size_type=req.position_size_type,
        position_size=req.position_size,
        commission_rate=req.commission_rate,
        slippage_bps=req.slippage_bps,
        allow_short=req.allow_short,
        close_on_opposite_signal=req.close_on_opposite_signal,
        execution_mode=req.execution_mode,
        market_type=req.market_type,
        multiplier=req.multiplier,
        margin=req.margin,
        expiry=req.expiry,
    )
    
    engine = create_backtest_engine(
        initial_cash=req.initial_cash,
        settings=settings,
        loader=loader,
    )
    
    symbols = req.symbols if req.symbols else [req.symbol]

    try:
        result = engine.run(
            symbols=symbols,
            start=req.start.isoformat(),
            end=req.end.isoformat(),
            timeframe=req.timeframe,
            strategy_ast=req.strategy_ast,
            broker=req.broker.model_dump() if req.broker else None,
        )
    except TimeoutError as e:
        logging.getLogger(__name__).error("TimeoutError in run_backtest: %s", traceback.format_exc())
        raise HTTPException(status_code=504, detail="Backtest execution timed out.")
    except RuntimeError as e:
        error_msg = str(e)
        logging.getLogger(__name__).error("RuntimeError in run_backtest: %s", traceback.format_exc())
        if "Failed to download data" in error_msg or "Failed to load data" in error_msg or "returned no data" in error_msg or "active futures" in error_msg:
            raise HTTPException(status_code=400, detail="Data not available for backtesting for the selected dates or symbol.")
        
        if "Strategy AST has no operation nodes" in error_msg or "NLconverter evaluation failed" in error_msg:
            raise HTTPException(status_code=400, detail=f"Invalid Strategy: {error_msg}")
            
        raise HTTPException(status_code=502, detail=f"Engine Error: {error_msg}")
    except ValueError as e:
        logging.getLogger(__name__).error("ValueError in run_backtest: %s", traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Configuration Error: {str(e)}")
    except Exception as e:
        logging.getLogger(__name__).error("Exception in run_backtest: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
        
    dfs = loader.get_data()
    ohlc_data = {}
    indicators_data = {}
    close_prices = {}
    first_close = None
    
    for sym, df in dfs.items():
        sym_ohlc = []
        sym_inds = {}
        
        # Pre-initialize indicator structures based on _indicators_data keys
        if hasattr(engine, 'indicators') and sym in engine.indicators:
            indicator_dict = engine.indicators[sym]._indicators_data
            for key, val in indicator_dict.items():
                if isinstance(val, dict):
                    for sub_key in val.keys():
                        sym_inds[f"{key}_{sub_key}"] = []
                else:
                    sym_inds[key] = []
                    
        if not df.empty:
            for idx_num, row in enumerate(df.itertuples()):
                ts = row.timestamp
                if pd.isna(ts):
                    continue
                time_val = ts.strftime("%Y-%m-%d") if req.timeframe.lower() == "1d" else int(ts.timestamp())
                close_val = float(row.close)
                sym_ohlc.append(OHLCCandle(
                    time=str(time_val),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=close_val
                ))
                
                # Add indicator data
                if hasattr(engine, 'indicators') and sym in engine.indicators:
                    indicator_dict = engine.indicators[sym]._indicators_data
                    for key, val in indicator_dict.items():
                        if isinstance(val, dict):
                            for sub_key, sub_val in val.items():
                                if idx_num < len(sub_val):
                                    v = sub_val[idx_num]
                                    if not pd.isna(v) and not math.isnan(v) and not math.isinf(v):
                                        sym_inds[f"{key}_{sub_key}"].append({"time": str(time_val), "value": float(v)})
                        else:
                            if idx_num < len(val):
                                v = val[idx_num]
                                if not pd.isna(v) and not math.isnan(v) and not math.isinf(v):
                                    sym_inds[key].append({"time": str(time_val), "value": float(v)})
                                    
                if sym == symbols[0]:
                    close_prices[ts] = close_val
                    if first_close is None and not pd.isna(close_val):
                        first_close = close_val
        ohlc_data[sym] = sym_ohlc
        indicators_data[sym] = sym_inds
            
    metrics = dict(result["metrics"])
    for k, v in metrics.items():
        if isinstance(v, float):
            if math.isinf(v) or math.isnan(v):
                metrics[k] = None

    if "symbol_results" in result:
        for sym, sym_data in result["symbol_results"].items():
            sym_eq_curve = []
            if "equity_curve" in sym_data:
                max_eq = req.initial_cash
                for point in sym_data["equity_curve"]:
                    dt = point.get("timestamp")
                    if dt is None:
                        continue
                    time_val = dt.strftime("%Y-%m-%d") if req.timeframe.lower() == "1d" else int(dt.timestamp())
                    eq_val = float(point.get("equity", 0.0))
                    
                    if eq_val > max_eq:
                        max_eq = eq_val
                    dd_pct = ((max_eq - eq_val) / max_eq) * 100.0 if max_eq > 0 else 0.0
                    
                    sym_eq_curve.append({
                        "time": str(time_val),
                        "value": eq_val,
                        "cash": float(point.get("cash", 0.0)),
                        "drawdown": dd_pct
                    })
                sym_data["equity_curve"] = sym_eq_curve
                
            # Replace NaNs in metrics
            if "metrics" in sym_data:
                for k, v in sym_data["metrics"].items():
                    if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
                        sym_data["metrics"][k] = None
            
            # Remove unsanitized trade_report from sym_data as it contains pd.Timestamp
            # The root trades list already contains all sanitized trades
            if "trade_report" in sym_data:
                del sym_data["trade_report"]
                        
        metrics["symbol_results"] = result["symbol_results"]

    trades = []
    # Extract trades directly from the engine result, handling either trade_report (dicts) or trades (Trade objects)
    raw_trades = result.get("trade_report") or result.get("trades") or []
    if raw_trades:
        # If it's already a list of dicts (from trade_report)
        if isinstance(raw_trades[0], dict):
            trade_df = pd.DataFrame(raw_trades)
        else:
            trade_df = trades_to_dataframe(raw_trades)
            
        for col in ["entry_time", "exit_time"]:
            if col in trade_df.columns:
                if req.timeframe.lower() == "1d":
                    trade_df[col] = pd.to_datetime(trade_df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                else:
                    trade_df[col] = pd.to_datetime(trade_df[col], errors="coerce").apply(
                        lambda x: int(x.timestamp()) if pd.notnull(x) else None
                    )
        # Convert any NaT, NaN, pd.NA to None for JSON serialization
        trade_df = trade_df.astype(object).where(pd.notna(trade_df), None)
        trades = trade_df.to_dict(orient="records")

    equity_curve = []
    drawdown_curve = []
    monthly_data = {}

    for point in result["equity_curve"]:
        dt = point["timestamp"]
        if dt is None:
            continue
        time_val = dt.strftime("%Y-%m-%d") if req.timeframe.lower() == "1d" else int(dt.timestamp())
        
        eq_val = float(point["equity"])
        cash_val = float(point["cash"])
        
        # Benchmark Value
        benchmark_val = req.initial_cash
        if dt in close_prices and first_close:
            benchmark_val = req.initial_cash * (close_prices[dt] / first_close)
            
        equity_curve.append({
            "time": str(time_val),
            "value": eq_val,
            "cash": cash_val,
            "benchmark_value": benchmark_val
        })
        
        # Drawdown Curve
        drawdown_curve.append({
            "time": str(time_val),
            "drawdownPct": -point["drawdown_pct"]
        })
        
        # Track monthly data (overwrite with the latest value for that month)
        monthly_data[(dt.year, dt.month)] = eq_val

    # Calculate Monthly Returns
    monthly_returns = []
    sorted_months = sorted(monthly_data.keys())
    prev_equity = req.initial_cash
    for year, month in sorted_months:
        end_eq = monthly_data[(year, month)]
        ret_pct = ((end_eq - prev_equity) / prev_equity) * 100.0 if prev_equity > 0 else 0.0
        monthly_returns.append({
            "year": year,
            "month": month,
            "returnPct": ret_pct
        })
        prev_equity = end_eq

    raw_warnings = result.get("warnings", [])
    sanitized_warnings = []
    for w in raw_warnings:
        w_str = str(w)
        w_lower = w_str.lower()
        # Drop warnings containing file paths, internal class structures/paths, or stack frames
        has_filepath = (".py" in w_lower or "/" in w_str or "\\" in w_str)
        has_classname = any(cls in w_lower for cls in ["app.portfolio", "app.core", "app.signal", "app.execution", "app.metrics", "<class", "object at"])
        has_stackframe = any(term in w_lower for term in ["traceback", "stack frame", "line ", "tb_next", "frame object", "exception:"])
        
        if not (has_filepath or has_classname or has_stackframe):
            sanitized_warnings.append(w_str)
        else:
            sanitized_warnings.append("EVAL_ERROR")

    # Deduplicate while preserving order
    seen_warn = set()
    final_warnings = []
    for w in sanitized_warnings:
        if w not in seen_warn:
            seen_warn.add(w)
            final_warnings.append(w)

    return BacktestResponse(
        metrics=metrics,
        trades=trades,
        equity_curve=equity_curve,
        drawdown_curve=drawdown_curve,
        monthly_returns=monthly_returns,
        ohlc_data=ohlc_data,
        indicators_data=indicators_data,
        warnings=final_warnings
    )

# --- Paper Trading Routes ---
import uuid
import asyncio
from app.core.paper_engine import PaperTradingEngine
from app.market_data.live_feed import LiveKiteFeed
from app.market_data.binance_feed import BinanceLiveFeed
from app.execution.paper_simulator import PaperExecutionEngine
from app.session.session_manager import session_manager
from app.session.paper_trade_session import PaperTradeSession
from app.ast.indicator_extractor import IndicatorExtractor

# Note: WebSocket subscribers are temporarily kept in a separate dict until EventBus is implemented
_WS_SUBSCRIBERS = {}

@router.post("/api/v1/run_paper_trade", dependencies=[Depends(verify_token)])
async def run_paper_trade(req: PaperTradeRequest, request: Request):
    check_rate_limit(request)
    
    session_id = req.session_id or str(uuid.uuid4())
    is_recovery = bool(req.session_id)
    
    api_key = ""
    access_token = ""
    if req.broker and req.broker.broker_name == "kite":
        api_key = req.broker.credentials.get("api_key", "")
        access_token = req.broker.credentials.get("access_token", "")

    # Initialize Feed and Execution
    timeframe_mins = int(req.timeframe.replace("m", "")) if "m" in req.timeframe else 1
    import json
    with open("strategy_ast_dump.json", "w") as f:
        json.dump(req.strategy_ast, f, indent=2)
        
    from app.ast.indicator_extractor import IndicatorExtractor
    configs = IndicatorExtractor.gather_indicator_configs(req.strategy_ast, [])
    max_lookback = IndicatorExtractor.get_max_lookback(configs)
    
    from app.market_data.factory import BrokerAdapterFactory
    # Default to kite for backwards compatibility if broker dict is missing
    if req.broker:
        broker_dict = req.broker.model_dump() if hasattr(req.broker, 'model_dump') else req.broker.dict()
    else:
        if req.exchange and req.exchange.upper() == "CRYPTO":
            broker_dict = {"broker_name": "binance", "credentials": {}}
        else:
            broker_dict = {
                "broker_name": "kite",
                "credentials": {"api_key": api_key, "access_token": access_token}
            }
        
    feed = BrokerAdapterFactory.get_live_feed_adapter(
        broker=broker_dict,
        symbols=req.symbols,
        timeframe_minutes=timeframe_mins,
        session_id=session_id,
        warmup_candles=max_lookback
    )
    
    # The new adapter interface encapsulates the instrument_tokens/symbol_map mapping.
    # In a fully fleshed out adapter, it will use `req.symbols` to resolve tokens internally.

    configs = IndicatorExtractor.gather_indicator_configs(req.strategy_ast, [])
    max_lookback = IndicatorExtractor.get_max_lookback(configs)
    
    if req.exchange and req.exchange.upper() == "CRYPTO":
        feed = BinanceLiveFeed(
            symbols=req.symbols,
            timeframe_minutes=timeframe_mins,
            session_id=session_id,
            warmup_candles=max_lookback
        )
    else:
        api_key = req.broker.credentials.get("api_key") if req.broker else ""
        access_token = req.broker.credentials.get("access_token") if req.broker else ""
        feed = LiveKiteFeed(
            api_key=api_key,
            access_token=access_token,
            instrument_tokens=req.instrument_tokens,
            symbol_map=req.symbol_map,
            timeframe_minutes=timeframe_mins,
            session_id=session_id,
            warmup_candles=max_lookback
        )
    execution = PaperExecutionEngine(
        qty=req.position_size,
        multiplier=1.0,
        margin=req.margin or 0.0,
    )
    
    # We pass None for loader since it's not used in paper trading prepare_run
    from app.store.redis_store import redis_store
    redis_store.clear_session(session_id)
    
    engine = PaperTradingEngine(
        loader=None,
        feed=feed,
        indicator=IndicatorEngine(),
        signal=SignalEngine(),
        execution=execution,
        portfolio=Portfolio(initial_cash=req.initial_cash),
        metrics=MetricsEngine()
    )
    
    import asyncio
    loop = asyncio.get_running_loop()
    
    # Create the session wrapper
    session = PaperTradeSession(
        session_id=session_id,
        engine=engine,
        symbols=req.symbols,
        strategy_ast=req.strategy_ast,
        strategy_settings={
            "execution_mode": req.execution_mode,
            "allow_short": req.allow_short,
            "close_on_opposite_signal": req.close_on_opposite_signal,
            "market_type": req.market_type,
            "position_size_type": req.position_size_type,
            "position_size": req.position_size,
        },
        on_update_callback=None,
        loop=loop
    )
    
    session_manager.add_session(session)
    
    if not is_recovery:
        from app.db.database import AsyncSessionLocal
        from app.persistence.repository import PaperTradingRepository
        async with AsyncSessionLocal() as db_session:
            repo = PaperTradingRepository(db_session)
            await repo.create_session(
                session_id=session_id,
                symbols=req.symbols,
                strategy_config=req.strategy_ast
            )
            await db_session.commit()
            

    if is_recovery:
        from app.db.database import AsyncSessionLocal
        from app.persistence.repository import PaperTradingRepository
        from app.domain.orders import OrderFill
        
        async def get_domain_fills():
            async with AsyncSessionLocal() as db_session:
                repo = PaperTradingRepository(db_session)
                db_fills = await repo.get_all_fills(session_id)
                domain_fills = []
                for f in db_fills:
                    domain_fills.append(OrderFill(
                        fill_id=f.fill_id,
                        session_id=f.session_id,
                        order_intent_id=f.order_intent_id,
                        symbol=f.symbol,
                        timestamp=f.timestamp,
                        side=f.side,
                        filled_quantity=float(f.filled_qty),
                        filled_price=float(f.filled_price),
                        fees=float(f.fees),
                        slippage=float(f.slippage)
                    ))
                return domain_fills
                
        historical_fills = await get_domain_fills()
        
        # 1. Initialize EventBus & Models early without starting feed
        session.start(start_feed=False)
        
        # 2. Recover State
        session.recover(historical_fills)
        
        # 3. TODO: Fast-forward candles from last checkpoint to now.
        # For now, skip indicators rewarming based on user prompt.
        
        # 4. Start Feed
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Session {session_id} recovery done, starting feed.")
        
        # Finish starting
        session.start_feed()
        
    else:
        # Normal Start
        session.start()
        
    return {"message": "Paper trading started", "session_id": session_id}


@router.get("/api/v1/paper_trade/{session_id}/history")
async def get_paper_trade_history(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Phase 13: Fetch from RedisStore instead of coupled object
    from app.store.redis_store import redis_store
    candles = redis_store.get_all_candles(session_id)
    fills = redis_store.get_all_fills(session_id)
    port_state = redis_store.get_latest_portfolio_state(session_id)
    
    # Map filled_price to price for frontend compatibility
    processed_fills = []
    for f in fills:
        from dataclasses import asdict
        f_dict = f if isinstance(f, dict) else asdict(f)
        if "filled_price" in f_dict and "price" not in f_dict:
            f_dict["price"] = f_dict["filled_price"]
        processed_fills.append(f_dict)
    
    return {
        "history": {
            "candles": candles,
            "fills": processed_fills,
            "portfolio": port_state
        }
    }

@router.websocket("/api/v1/ws/paper_trade/{session_id}")
async def paper_trade_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    from app.store.redis_store import redis_store
    import asyncio
    import json
    from dataclasses import asdict
    
    loop = asyncio.get_running_loop()
    event = asyncio.Event()
    redis_store.register_notifier(session_id, loop, event)
    
    try:
        # Prevent replaying old data that was already fetched via the HTTP /history endpoint
        last_candle_idx = len(redis_store.get_all_candles(session_id))
        last_fill_idx = len(redis_store.get_all_fills(session_id))
        
        while True:
            await event.wait()
            event.clear()
            
            # 1. Poll the store
            candles = redis_store.get_all_candles(session_id)
            fills = redis_store.get_all_fills(session_id)
            port = redis_store.get_latest_portfolio_state(session_id)
            
            updates = []
            
            # 2. Extract new items since last poll
            if len(candles) > last_candle_idx:
                for c in candles[last_candle_idx:]:
                    updates.append({"type": "CANDLE_UPDATE", "data": asdict(c) if hasattr(c, "__dataclass_fields__") else c})
                last_candle_idx = len(candles)
            elif candles:
                # Always push the latest in-progress candle so the UI bounces
                c = candles[-1]
                updates.append({"type": "CANDLE_UPDATE", "data": asdict(c) if hasattr(c, "__dataclass_fields__") else c})
                
            if len(fills) > last_fill_idx:
                for f in fills[last_fill_idx:]:
                    f_dict = f if isinstance(f, dict) else asdict(f)
                    if "filled_price" in f_dict and "price" not in f_dict:
                        f_dict["price"] = f_dict["filled_price"]
                    updates.append({"type": "FILL_UPDATE", "data": f_dict})
                last_fill_idx = len(fills)
                
            if port:
                updates.append({"type": "PORTFOLIO_UPDATE", "data": asdict(port) if hasattr(port, "__dataclass_fields__") else port})
                
            # 3. Push to browser
            for u in updates:
                # Need to handle datetime serialization
                await websocket.send_json(json.loads(json.dumps(u, default=str)))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.getLogger(__name__).error(f"WebSocket error: {e}")
    finally:
        redis_store.unregister_notifier(session_id, loop, event)

@router.get("/api/v1/paper_trade/{session_id}/status")
async def get_paper_trade_status(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not hasattr(session, "portfolio") or not session.portfolio:
        return {"status": "initializing"}
        
    equity = session.portfolio.get_equity()
    active_positions_count = len([p for p in session.portfolio.positions.values() if p.qty != 0])
    
    portfolios_state = {
        "aggregate": {
            "cash": session.portfolio.cash,
            "equity": equity,
            "positions": {p_sym: p.qty for p_sym, p in session.portfolio.positions.items() if p.qty != 0}
        }
    }
        
    return {
        "status": session.status,
        "portfolios": portfolios_state,
        "trades_executed": len(session.portfolio.fill_history),
        "aggregate_pnl": equity - session.portfolio.initial_cash,
        "active_positions_count": active_positions_count
    }
    
@router.post("/api/v1/paper_trade/{session_id}/stop")
async def stop_paper_trade(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session_manager.stop_session(session_id)
    return {"message": "Session stopped", "session_id": session_id}

@router.get("/api/v1/paper_trade/sessions")
async def list_paper_trade_sessions():
    sessions = []
    for sid, sess in session_manager._sessions.items():
        sessions.append({
            "session_id": sid,
            "status": sess.status,
            "symbols": sess.symbols,
            "start_time": getattr(sess, "start_time", None),
        })
    return {"sessions": sessions}
