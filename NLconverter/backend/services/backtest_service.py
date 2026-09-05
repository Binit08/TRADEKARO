import json
import os
import urllib.request
import urllib.error
import logging
import time
import uuid
from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.db.models import BrokerCredentials, User, BacktestRecord
from backend.api.schemas import ProxyBacktestRequest
from backend.services.utils import map_symbol, get_instrument_token
from backend.api.security import decrypt_secret
from kiteconnect import KiteConnect

logger = logging.getLogger("nlconverter")


class BacktestEngineClient:
    """Client for communicating with the external Backtesting Engine."""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv("BACKTEST_ENGINE_URL", "http://127.0.0.1:8002")
        self.api_key = api_key or os.getenv("BACKTEST_ENGINE_API_KEY", "secret_token")

    def _make_request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        req_body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                err_dict = json.loads(body)
                detail = err_dict.get("detail", body)
            except Exception:
                detail = body
            logger.error("Backtesting Engine returned HTTP %d: %s", e.code, detail)
            return {"error": f"Backtesting Engine returned HTTP {e.code}: {detail}"}
        except urllib.error.URLError as e:
            logger.error("Failed to connect to Backtesting Engine: %s", e)
            return {"error": f"Failed to connect to Backtesting Engine: {e}"}
        except Exception as e:
            logger.error("Error calling Backtesting Engine: %s", e)
            return {"error": f"Error calling Backtesting Engine: {e}"}

    def run_backtest(self, payload: dict) -> dict:
        return self._make_request("/api/v1/run_backtest", payload)

    def run_paper_trade(self, payload: dict) -> dict:
        return self._make_request("/api/v1/run_paper_trade", payload)


class BacktestService:
    """Service to handle Backtest business logic, broker injection, and DB operations."""

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.engine_client = BacktestEngineClient()

    def _attach_broker_credentials(self, payload_dict: dict, broker_name: str = None) -> dict:
        if broker_name:
            active_broker = self.db.query(BrokerCredentials).filter(
                BrokerCredentials.user_id == self.current_user.id,
                BrokerCredentials.broker_name == broker_name
            ).first()
        else:
            active_broker = self.db.query(BrokerCredentials).filter(
                BrokerCredentials.user_id == self.current_user.id,
                BrokerCredentials.is_active == True
            ).first()
        
        if active_broker:
            creds = dict(active_broker.credentials) if active_broker.credentials else {}
            
            if creds.get("access_token"):
                creds["access_token"] = decrypt_secret(creds["access_token"])
            if creds.get("api_secret"):
                creds["api_secret"] = decrypt_secret(creds["api_secret"])

            payload_dict["broker"] = {
                "broker_name": active_broker.broker_name,
                "credentials": creds
            }
        return payload_dict

    def _normalize_trades(self, raw_trades: list, default_symbol: str) -> list:
        normalized = []
        for t in raw_trades:
            normalized.append({
                "symbol": t.get("symbol", default_symbol),
                "side": "LONG" if t.get("side", "").upper() in ("BUY", "LONG") else "SHORT",
                "entry_time": t.get("entry_time"),
                "exit_time": t.get("exit_time"),
                "qty": t.get("qty", t.get("size", 0)),
                "entry_price": t.get("entry_price", 0),
                "exit_price": t.get("exit_price"),
                "pnl": t.get("pnl"),
                "return_pct": t.get("return_pct"),
            })
        return normalized

    def _normalize_equity(self, raw_equity: list) -> list:
        normalized = []
        for p in raw_equity:
            normalized.append({
                "time": p.get("time") or p.get("date"),
                "value": p.get("value") or p.get("equity"),
                "benchmark_value": p.get("benchmark_value")
            })
        return normalized

    def _normalize_drawdown(self, raw_dd: list) -> list:
        normalized = []
        for p in raw_dd:
            normalized.append({
                "time": p.get("time") or p.get("date"),
                "drawdownPct": p.get("drawdownPct") or p.get("drawdown", 0)
            })
        return normalized

    def execute_backtest(self, payload: ProxyBacktestRequest) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())[:8]
        sym_str = ",".join(payload.symbols) if payload.symbols else payload.symbol
        logger.info("[%s] Backtest requested: %s %s %s->%s", request_id, sym_str, payload.timeframe, payload.start, payload.end)

        t0 = time.time()
        payload_dict = payload.model_dump()
        payload_dict = self._attach_broker_credentials(payload_dict, payload.broker_name)

        if payload.symbol:
            payload_dict["symbol"] = map_symbol(payload.symbol, payload.exchange)
        if payload.symbols:
            payload_dict["symbols"] = [map_symbol(s.strip(), payload.exchange) for s in payload.symbols]
            
        # Map timeframes for the backtesting engine which expects '60m' instead of '1h'
        if payload_dict.get("timeframe") == "1h":
            payload_dict["timeframe"] = "60m"
            
        result = self.engine_client.run_backtest(payload_dict)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        elapsed = round(time.time() - t0, 3)
        logger.info("[%s] Backtest completed in %.3fs", request_id, elapsed)

        normalized_trades = self._normalize_trades(result.get("trades") or result.get("trade_report") or [], sym_str)
        normalized_equity = self._normalize_equity(result.get("equity_curve") or [])
        normalized_dd = self._normalize_drawdown(result.get("drawdown_curve") or [])
            
        result["trades"] = normalized_trades
        result["equity_curve"] = normalized_equity
        result["drawdown_curve"] = normalized_dd
        
        is_multi_symbol = payload.symbols and len(payload.symbols) > 1
        
        if not is_multi_symbol and isinstance(result.get("ohlc_data"), dict):
            # For backward compatibility with single-symbol charts
            result["ohlc_data"] = result["ohlc_data"].get(payload.symbol) or list(result["ohlc_data"].values())[0] if result["ohlc_data"] else []

        db_sym_str = sym_str
        if len(db_sym_str) > 47:
            db_sym_str = db_sym_str[:47] + "..."

        db_record = BacktestRecord(
            strategy_id=payload.strategy_id,
            user_id=self.current_user.id,
            symbol=db_sym_str,
            timeframe=payload.timeframe,
            start_date=payload.start,
            end_date=payload.end,
            exchange=payload.exchange,
            position_side=payload.position_side,
            initial_cash=payload.initial_cash,
            position_size=payload.position_size,
            position_size_type=payload.position_size_type,
            commission_rate=payload.commission_rate,
            slippage_bps=payload.slippage_bps,
            allow_short=payload.allow_short,
            close_on_opposite_signal=payload.close_on_opposite_signal,
            market_type=payload.market_type,
            multiplier=payload.multiplier,
            margin=payload.margin,
            expiry=payload.expiry,
            strategy_ast=payload.strategy_ast,
            metrics={
                **result.get("metrics", {}),
                "monthly_returns": result.get("monthly_returns"),
                "total_trades": len(normalized_trades),
                "symbol_results": result.get("symbol_results")
            },
            equity_curve=normalized_equity,
            drawdown_curve=normalized_dd,
            trades=normalized_trades,
            ohlc_data=result.get("ohlc_data"),
            status="ok",
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)

        return {**result, "backtest_id": db_record.id}

    def execute_paper_trade(self, payload: Any) -> Dict[str, Any]:
        mapped_symbols = [s.strip() for s in payload.symbols]
        
        payload_dict = {
            "symbols": mapped_symbols,
            "timeframe": payload.timeframe,
            "strategy_ast": payload.strategy_ast,
            "initial_cash": payload.initial_cash,
            "position_size": payload.position_size,
            "exchange": payload.exchange,
        }

        payload_dict = self._attach_broker_credentials(payload_dict, payload.broker_name)

        active_broker = None
        if payload_dict.get("broker"):
            active_broker = payload_dict["broker"].get("broker_name")

        if payload.exchange.upper() == "CRYPTO":
            payload_dict.update({
                "kite_api_key": "crypto_mock_key",
                "kite_access_token": "crypto_mock_token",
                "instrument_tokens": [],
                "symbol_map": {hash(s): s for s in mapped_symbols},
                "market_type": "crypto",
            })
        else:
            if not active_broker:
                raise HTTPException(status_code=400, detail="No broker connection found.")
                
            mapped_symbols = [map_symbol(sym, payload.exchange) for sym in mapped_symbols]
            instrument_tokens = []
            symbol_map = {}
            
            if active_broker == "kite":
                creds = payload_dict["broker"].get("credentials", {})
                kite_api_key = creds.get("api_key")
                kite_access_token = creds.get("access_token")
                
                if not kite_api_key or not kite_access_token:
                    raise HTTPException(status_code=400, detail="Incomplete Kite credentials.")
                
                kite = KiteConnect(api_key=kite_api_key)
                kite.set_access_token(kite_access_token)
                
                for sym in mapped_symbols:
                    token = get_instrument_token(kite, sym, payload.exchange)
                    if not token:
                        raise HTTPException(status_code=400, detail=f"Could not resolve instrument token for symbol: {sym}")
                    instrument_tokens.append(token)
                    symbol_map[token] = sym

            payload_dict.update({
                "symbols": mapped_symbols,
                "instrument_tokens": instrument_tokens,
                "symbol_map": symbol_map,
                "market_type": "equity",
            })
            
            if active_broker == "kite":
                creds = payload_dict["broker"].get("credentials", {})
                payload_dict["kite_api_key"] = creds.get("api_key")
                payload_dict["kite_access_token"] = creds.get("access_token")
        
        result = self.engine_client.run_paper_trade(payload_dict)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
