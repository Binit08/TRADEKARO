import os
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import User

security = HTTPBearer()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Decodes the Supabase JWT to extract the user ID.
    If the user does not exist in our database, it creates a new user record.
    """
    token = credentials.credentials
    supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
    
    try:
        if not supabase_jwt_secret:
            # For local dev without secret, just extract payload without verification
            # WARNING: In production, MUST verify signature with SUPABASE_JWT_SECRET
            payload = jwt.decode(token, options={"verify_signature": False})
        else:
            payload = jwt.decode(
                token,
                supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            
        # Fetch or create user in our DB
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
            
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
