import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.db.models import User, BrokerCredentials
from backend.api.deps import get_current_user, get_db
import logging

try:
    from kiteconnect import KiteConnect
except ImportError:
    KiteConnect = None

router = APIRouter(prefix="/auth/kite", tags=["Kite Auth"])
logger = logging.getLogger(__name__)

class KiteCallbackRequest(BaseModel):
    request_token: str

@router.get("/url")
def get_kite_login_url(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the Kite Connect login URL.
    """
    broker = db.query(BrokerCredentials).filter(
        BrokerCredentials.user_id == current_user.id,
        BrokerCredentials.is_active == True,
        BrokerCredentials.broker_name == "kite"
    ).first()

    if not broker or not broker.credentials.get("api_key"):
        raise HTTPException(status_code=400, detail="Kite broker not configured. Please add it in settings.")
        
    api_key = broker.credentials.get("api_key")
        
    if not KiteConnect:
        raise HTTPException(status_code=500, detail="kiteconnect library not installed")
        
    kite = KiteConnect(api_key=api_key)
    return {"login_url": kite.login_url()}


@router.post("/callback")
def handle_kite_callback(
    data: KiteCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Legacy callback endpoint. The frontend uses /api/v1/brokers/session for BYOK.
    This is kept for backward compatibility if needed, but redirects to the new logic.
    """
    raise HTTPException(
        status_code=400, 
        detail="This endpoint is deprecated. Use /api/v1/brokers/session instead."
    )


@router.get("/status")
def get_kite_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Checks if the user has a valid Kite session.
    Kite access tokens expire daily at 6:00 AM IST.
    """
    broker = db.query(BrokerCredentials).filter(
        BrokerCredentials.user_id == current_user.id,
        BrokerCredentials.is_active == True,
        BrokerCredentials.broker_name == "kite"
    ).first()

    if not broker or not broker.credentials.get("access_token") or not broker.credentials.get("login_time"):
        return {"is_connected": False}
        
    login_time_str = broker.credentials.get("login_time")
    try:
        login_time = datetime.fromisoformat(login_time_str)
    except ValueError:
        return {"is_connected": False}

    # Convert UTC times to IST (UTC + 5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.utcnow() + ist_offset
    login_time_ist = login_time + ist_offset
        
    # If the current date in IST is greater than the login date in IST, it has expired at midnight
    if login_time_ist.date() < now_ist.date():
        return {"is_connected": False, "reason": "Token expired at midnight IST"}
        
    return {"is_connected": True}
