import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.models import User, BrokerCredentials
from backend.api.deps import get_current_user
from backend.db.database import get_db
from backend.api.security import decrypt_secret

try:
    from kiteconnect import KiteConnect
except ImportError:
    KiteConnect = None

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/positions")
def get_kite_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches the live net positions for the user from Kite.
    """
    # Find active kite broker
    active_broker = db.query(BrokerCredentials).filter(
        BrokerCredentials.user_id == current_user.id,
        BrokerCredentials.is_active == True,
        BrokerCredentials.broker_name == "kite"
    ).first()
    
    api_key = None
    access_token = None
    
    if active_broker:
        api_key = active_broker.credentials.get("api_key")
        access_token = active_broker.credentials.get("access_token")
        if access_token:
            access_token = decrypt_secret(access_token)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Kite not connected"
        )
        
    if not api_key:
        raise HTTPException(status_code=500, detail="Kite API Key not configured for this user")
        
    if not KiteConnect:
        raise HTTPException(status_code=500, detail="kiteconnect library not installed")
        
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    
    try:
        # Fetch positions
        # Note: 'net' positions include overnight positions + day positions
        positions = kite.positions()
        net_positions = positions.get("net", [])
        
        # Format the data for the frontend
        formatted_positions = []
        for pos in net_positions:
            qty = pos.get("quantity", 0)
            
            # If quantity is 0, it means the position is closed. 
            # We might still want to show it for intraday P&L, but often it's skipped.
            # Let's include it so users can see closed intraday trades in the panel.
            
            ltp = pos.get("last_price", 0)
            buy_price = pos.get("buy_price", 0)
            sell_price = pos.get("sell_price", 0)
            
            pnl = pos.get("pnl", 0)
            
            # Calculate approx percentage change based on average price
            avg_price = pos.get("average_price", 0)
            pnl_pct = 0
            if avg_price > 0 and qty != 0:
                pnl_pct = (pnl / (avg_price * abs(qty))) * 100
                
            formatted_positions.append({
                "symbol": pos.get("tradingsymbol", ""),
                "qty": qty,
                "ltp": ltp,
                "pnl": pnl,
                "pnlPct": pnl_pct,
                "isUp": pnl >= 0
            })
            
        return {"status": "success", "positions": formatted_positions}
        
    except Exception as e:
        logger.error(f"Error fetching Kite positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to fetch portfolio from Kite: {str(e)}"
        )
