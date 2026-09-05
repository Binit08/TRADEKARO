from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from kiteconnect import KiteConnect
from backend.api.security import encrypt_secret, decrypt_secret

from ..deps import get_current_user, get_db
from ...db.models import User, BrokerCredentials

router = APIRouter()

class BrokerCredentialsCreate(BaseModel):
    broker_name: str
    credentials: Dict[str, Any]

class BrokerCredentialsResponse(BaseModel):
    id: int
    broker_name: str
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True

@router.post("/", response_model=BrokerCredentialsResponse)
def add_broker(
    broker_data: BrokerCredentialsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Encrypt api_secret before storing
    creds = broker_data.credentials.copy()
    if "api_secret" in creds:
        creds["api_secret"] = encrypt_secret(creds["api_secret"])

    # Check if a credential for this broker already exists
    existing = db.query(BrokerCredentials).filter(
        BrokerCredentials.user_id == current_user.id,
        BrokerCredentials.broker_name == broker_data.broker_name
    ).first()
    
    if existing:
        existing.credentials = creds
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return {
            "id": existing.id,
            "broker_name": existing.broker_name,
            "is_active": existing.is_active,
            "created_at": existing.created_at.isoformat()
        }
        
    # Deactivate others
    db.query(BrokerCredentials).filter(BrokerCredentials.user_id == current_user.id).update({"is_active": False})
    
    new_cred = BrokerCredentials(
        user_id=current_user.id,
        broker_name=broker_data.broker_name,
        credentials=creds,
        is_active=True
    )
    db.add(new_cred)
    db.commit()
    db.refresh(new_cred)
    
    return {
        "id": new_cred.id,
        "broker_name": new_cred.broker_name,
        "is_active": new_cred.is_active,
        "created_at": new_cred.created_at.isoformat()
    }

@router.get("/", response_model=List[BrokerCredentialsResponse])
def get_brokers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    creds = db.query(BrokerCredentials).filter(BrokerCredentials.user_id == current_user.id).all()
    return [
        {
            "id": c.id,
            "broker_name": c.broker_name,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat()
        } for c in creds
    ]

@router.put("/{broker_id}/active", response_model=BrokerCredentialsResponse)
def set_active_broker(
    broker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = db.query(BrokerCredentials).filter(
        BrokerCredentials.id == broker_id,
        BrokerCredentials.user_id == current_user.id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Broker not found")
        
    # Deactivate all
    db.query(BrokerCredentials).filter(BrokerCredentials.user_id == current_user.id).update({"is_active": False})
    
    target.is_active = True
    db.commit()
    db.refresh(target)
    
    return {
        "id": target.id,
        "broker_name": target.broker_name,
        "is_active": target.is_active,
        "created_at": target.created_at.isoformat()
    }

@router.delete("/{broker_id}")
def delete_broker(
    broker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = db.query(BrokerCredentials).filter(
        BrokerCredentials.id == broker_id,
        BrokerCredentials.user_id == current_user.id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Broker not found")
        
    db.delete(target)
    db.commit()
    return {"status": "success"}

class SessionRequest(BaseModel):
    request_token: str

@router.post("/session")
def generate_broker_session(
    req: SessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find active kite broker
    active_broker = db.query(BrokerCredentials).filter(
        BrokerCredentials.user_id == current_user.id,
        BrokerCredentials.is_active == True,
        BrokerCredentials.broker_name == "kite"
    ).first()
    
    if not active_broker:
        raise HTTPException(status_code=400, detail="No active Kite broker connection found.")
        
    api_key = active_broker.credentials.get("api_key")
    api_secret = active_broker.credentials.get("api_secret")
    if api_secret:
        api_secret = decrypt_secret(api_secret)
    
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Missing API Key or API Secret for Kite connection.")
        
    try:
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(req.request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        # Update credentials
        new_creds = active_broker.credentials.copy()
        new_creds["access_token"] = encrypt_secret(access_token)
        
        # In SQLAlchemy, updating a JSON column requires assigning a new dict or using flag_modified
        from sqlalchemy.orm.attributes import flag_modified
        active_broker.credentials = new_creds
        flag_modified(active_broker, "credentials")
        
        db.commit()
        return {"status": "success", "message": "Access token successfully generated and saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{broker_id}/login")
def broker_login_redirect(
    broker_id: int,
    db: Session = Depends(get_db)
):
    # Note: Cannot easily use Depends(get_current_user) because this is a top-level browser redirect.
    # We will just look up the broker by ID. It's safe since it just redirects to Kite with the API key.
    broker = db.query(BrokerCredentials).filter(BrokerCredentials.id == broker_id).first()
    if not broker or broker.broker_name != "kite":
        raise HTTPException(status_code=404, detail="Broker not found or not Kite")
        
    api_key = broker.credentials.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing API Key")
        
    kite_url = f"https://kite.trade/connect/login?v=3&api_key={api_key}"
    return RedirectResponse(url=kite_url)
