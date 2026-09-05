from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, defer

from backend.db.database import get_db
from backend.db.models import StrategyRecord, User
from backend.api.schemas import StrategyRequest
from backend.api.dependencies import verify_api_key, check_rate_limit
from backend.api.deps import get_current_user
from backend.services.strategy_service import generate_strategy_response
from backend.strategy_parser.ast import ASTBuildError

router = APIRouter(dependencies=[Depends(check_rate_limit)])

@router.post("/strategy")
def create_strategy(
    payload: StrategyRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    try:
        return generate_strategy_response(payload, db, user_id=current_user.id)
    except ASTBuildError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/strategy/{strategy_id}")
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
):
    try:
        strategy = db.query(StrategyRecord).filter(
            StrategyRecord.id == strategy_id,
            StrategyRecord.user_id == current_user.id
        ).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "status": "ok",
            "id": strategy.id,
            "name": strategy.name,
            "tag": strategy.tag,
            "description": strategy.description,
            "prompt": strategy.prompt,
            "canonical_json": strategy.canonical_json,
            "ast_json": strategy.ast_json,
            "execution_context": strategy.execution_context,
            "created_at": strategy.created_at,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/strategies")
def get_strategies(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0,
):
    try:
        query = db.query(StrategyRecord).filter(StrategyRecord.user_id == current_user.id)
        query = query.options(
            defer(StrategyRecord.logs),
            defer(StrategyRecord.execution_context)
        )
        total_count = query.count()
        strategies = (
            query.order_by(StrategyRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        has_more = (offset + limit) < total_count
        return {
            "status": "ok",
            "has_more": has_more,
            "total_count": total_count,
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "tag": s.tag,
                    "description": s.description,
                    "prompt": s.prompt,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "canonical_json": s.canonical_json,
                    "ast_json": s.ast_json,
                    "execution_context": None,
                    "logs": None,
                }
                for s in strategies
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
