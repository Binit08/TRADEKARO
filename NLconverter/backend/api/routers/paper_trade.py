import logging
import os
import urllib.request
import urllib.error
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.db.database import get_db
from backend.db.models import User, BrokerCredentials
from backend.api.dependencies import check_rate_limit, verify_api_key
from backend.api.deps import get_current_user
from backend.services.utils import map_symbol, get_instrument_token
from backend.services.backtest_service import BacktestService

router = APIRouter(dependencies=[Depends(check_rate_limit)])
logger = logging.getLogger("nlconverter")

class ProxyPaperTradeRequest(BaseModel):
    broker_name: Optional[str] = None
    symbols: List[str]
    timeframe: str = "1m"
    strategy_ast: Dict[str, Any]
    exchange: str = "NSE"
    initial_cash: float = 100000.0
    position_size: float = 1.0

@router.post("/paper_trade/start")
def proxy_start_paper_trade(
    payload: ProxyPaperTradeRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    try:
        service = BacktestService(db, current_user)
        return service.execute_paper_trade(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/paper_trade/sessions")
def proxy_list_paper_trade_sessions(
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    base_url = os.getenv("BACKTEST_ENGINE_URL", "http://127.0.0.1:8002").rstrip("/")
    url = f"{base_url}/api/v1/paper_trade/sessions"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {os.getenv('BACKTEST_ENGINE_API_KEY', 'secret_token')}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except Exception as e:
        logger.error(f"Failed to fetch sessions from Backtesting Engine: {e}")
        raise HTTPException(status_code=502, detail="Could not retrieve paper trade sessions.")

@router.get("/paper_trade/{session_id}/status")
def proxy_paper_trade_status(
    session_id: str,
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    base_url = os.getenv("BACKTEST_ENGINE_URL", "http://127.0.0.1:8002").rstrip("/")
    url = f"{base_url}/api/v1/paper_trade/{session_id}/status"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {os.getenv('BACKTEST_ENGINE_API_KEY', 'secret_token')}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=502, detail="Upstream engine error")
    except Exception as e:
        logger.error(f"Failed to fetch paper trade status: {e}")
        raise HTTPException(status_code=502, detail="Could not retrieve paper trade status.")

@router.post("/paper_trade/{session_id}/stop")
def proxy_paper_trade_stop(
    session_id: str,
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    base_url = os.getenv("BACKTEST_ENGINE_URL", "http://127.0.0.1:8002").rstrip("/")
    url = f"{base_url}/api/v1/paper_trade/{session_id}/stop"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {os.getenv('BACKTEST_ENGINE_API_KEY', 'secret_token')}",
            "Content-Length": "0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except Exception as e:
        logger.error(f"Failed to stop paper trade: {e}")
        raise HTTPException(status_code=502, detail="Could not stop paper trade.")

@router.get("/paper_trade/{session_id}/history")
def proxy_paper_trade_history(
    session_id: str,
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    base_url = os.getenv("BACKTEST_ENGINE_URL", "http://127.0.0.1:8002").rstrip("/")
    url = f"{base_url}/api/v1/paper_trade/{session_id}/history"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {os.getenv('BACKTEST_ENGINE_API_KEY', 'secret_token')}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except Exception as e:
        logger.error(f"Failed to fetch paper trade history: {e}")
        raise HTTPException(status_code=502, detail="Could not retrieve paper trade history.")