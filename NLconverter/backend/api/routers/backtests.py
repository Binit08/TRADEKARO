import time
import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, defer

from backend.db.database import get_db
from backend.db.models import BacktestRecord, User, BrokerCredentials
from backend.api.schemas import ProxyBacktestRequest
from backend.api.dependencies import verify_api_key, check_rate_limit
from backend.api.deps import get_current_user
from backend.services.backtest_service import BacktestService

router = APIRouter(dependencies=[Depends(check_rate_limit)])
logger = logging.getLogger("nlconverter")

@router.post("/backtest")
def proxy_backtest(
    payload: ProxyBacktestRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    try:
        service = BacktestService(db, current_user)
        return service.execute_backtest(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/backtests")
def list_backtests(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0,
):
    try:
        query = db.query(BacktestRecord).filter(BacktestRecord.user_id == current_user.id)
        query = query.options(
            defer(BacktestRecord.ohlc_data),
            defer(BacktestRecord.trades),
            defer(BacktestRecord.equity_curve),
            defer(BacktestRecord.drawdown_curve)
        )
        total_count = query.count()
        backtests = (
            query.order_by(BacktestRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        has_more = (offset + limit) < total_count
        return {
            "status": "ok",
            "has_more": has_more,
            "total_count": total_count,
            "data": [
                {
                    "id": bt.id,
                    "symbol": bt.symbol,
                    "timeframe": bt.timeframe,
                    "start_date": bt.start_date,
                    "end_date": bt.end_date,
                    "initial_cash": bt.initial_cash,
                    "position_size": bt.position_size,
                    "position_size_type": bt.position_size_type,
                    "commission_rate": bt.commission_rate,
                    "slippage_bps": bt.slippage_bps,
                    "allow_short": bt.allow_short,
                    "close_on_opposite_signal": bt.close_on_opposite_signal,
                    "exchange": bt.exchange,
                    "position_side": bt.position_side,
                    "market_type": bt.market_type,
                    "multiplier": bt.multiplier,
                    "margin": bt.margin,
                    "expiry": bt.expiry,
                    "strategy_ast": bt.strategy_ast,
                    "metrics": bt.metrics,
                    "net_profit": bt.metrics.get("net_pnl", 0) if isinstance(bt.metrics, dict) else 0,
                    "total_return": bt.metrics.get("return_pct", 0) if isinstance(bt.metrics, dict) else 0,
                    "win_rate": bt.metrics.get("win_rate", 0) if isinstance(bt.metrics, dict) else 0,
                    "total_trades": bt.metrics.get("total_trades", 0) if isinstance(bt.metrics, dict) else 0,
                    "status": bt.status,
                    "created_at": bt.created_at.isoformat() if bt.created_at else None,
                }
                for bt in backtests
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/backtests/{backtest_id}")
def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    bt = db.query(BacktestRecord).filter(
        BacktestRecord.id == backtest_id,
        BacktestRecord.user_id == current_user.id
    ).first()
    
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return {
        "status": "ok",
        "data": {
            "id": bt.id,
            "symbol": bt.symbol,
            "timeframe": bt.timeframe,
            "start_date": bt.start_date,
            "end_date": bt.end_date,
            "initial_cash": bt.initial_cash,
            "position_size": bt.position_size,
            "position_size_type": bt.position_size_type,
            "commission_rate": bt.commission_rate,
            "slippage_bps": bt.slippage_bps,
            "allow_short": bt.allow_short,
            "close_on_opposite_signal": bt.close_on_opposite_signal,
            "strategy_ast": bt.strategy_ast,
            "metrics": bt.metrics,
            "net_profit": bt.metrics.get("net_pnl", 0) if bt.metrics else 0,
            "total_return": bt.metrics.get("return_pct", 0) if bt.metrics else 0,
            "win_rate": bt.metrics.get("win_rate", 0) if bt.metrics else 0,
            "equity_curve": bt.equity_curve,
            "drawdown_curve": bt.drawdown_curve,
            "trades": bt.trades,
            "ohlc_data": bt.ohlc_data,
            "status": bt.status,
            "created_at": bt.created_at.isoformat() if bt.created_at else None,
        },
    }
