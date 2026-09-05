import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from dataclasses import asdict

from app.db.models import PaperSession, PaperOrder, PaperFill, PaperPosition, PaperEquitySnapshot, PaperSessionCheckpoint
from app.domain.orders import OrderIntent, OrderFill
from app.domain.events import PortfolioUpdateEvent, TickEvent, CandleEvent

logger = logging.getLogger(__name__)

class PaperTradingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_session(self, session_id: str, symbols: List[str], strategy_config: Dict) -> None:
        stmt = insert(PaperSession).values(
            session_id=session_id,
            symbols=symbols,
            strategy_config=strategy_config,
            status="CREATED"
        ).on_conflict_do_nothing()
        await self.session.execute(stmt)
        
    async def save_order_intent(self, intent: OrderIntent) -> None:
        """Idempotent insert of an OrderIntent."""
        stmt = insert(PaperOrder).values(
            order_intent_id=intent.order_intent_id,
            session_id=intent.session_id,
            symbol=intent.symbol,
            side=intent.side,
            qty=intent.quantity,
            order_type=intent.order_type,
            reason=intent.reason,
            limit_price=intent.limit_price,
            stop_price=intent.stop_price,
            status="PENDING"
        ).on_conflict_do_nothing()
        await self.session.execute(stmt)
        
    async def commit_fill_transaction(self, fill: OrderFill, position_qty: float, position_avg_price: float) -> bool:
        """Atomically persist a fill, update the order, and upsert the position."""
        try:
            # 1. Insert Fill (Idempotent)
            stmt_fill = insert(PaperFill).values(
                fill_id=fill.fill_id,
                session_id=fill.session_id,
                order_intent_id=fill.order_intent_id,
                symbol=fill.symbol,
                side=fill.side,
                filled_qty=fill.filled_quantity,
                filled_price=fill.filled_price,
                fees=fill.fees,
                slippage=fill.slippage,
                timestamp=fill.timestamp
            ).on_conflict_do_nothing()
            
            result = await self.session.execute(stmt_fill)
            
            # If nothing was inserted, this fill was a duplicate/replay. We can safely abort.
            if result.rowcount == 0:
                logger.warning(f"Fill {fill.fill_id} already exists. Ignoring duplicate.")
                await self.session.rollback()
                return False
                
            # 2. Update Order Status
            stmt_order = update(PaperOrder).where(
                PaperOrder.order_intent_id == fill.order_intent_id
            ).values(status="FILLED")
            await self.session.execute(stmt_order)
            
            # 3. Upsert Position
            # We determine net side based on qty. If qty > 0 it's LONG, if < 0 it's SHORT, if 0 it's FLAT.
            # But the portfolio object tracks absolute qty and a 'side' string.
            pos_side = "LONG" if position_qty > 0 else ("SHORT" if position_qty < 0 else "FLAT")
            
            stmt_pos = insert(PaperPosition).values(
                session_id=fill.session_id,
                symbol=fill.symbol,
                side=pos_side,
                qty=abs(position_qty),
                avg_entry_price=position_avg_price
            ).on_conflict_do_update(
                index_elements=['session_id', 'symbol'],
                set_={
                    'side': pos_side,
                    'qty': abs(position_qty),
                    'avg_entry_price': position_avg_price,
                    'updated_at': fill.timestamp # approx
                }
            )
            
            # 4. If qty is 0 (FLAT), we could delete or just set qty=0. The upsert sets qty=0 which is fine.
            
            await self.session.execute(stmt_pos)
            
            # Commit the whole transaction
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to commit atomic fill transaction: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[PaperSession]:
        stmt = select(PaperSession).where(PaperSession.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_fills(self, session_id: str) -> List[PaperFill]:
        stmt = select(PaperFill).where(PaperFill.session_id == session_id).order_by(PaperFill.timestamp)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_orders(self, session_id: str) -> List[PaperOrder]:
        stmt = select(PaperOrder).where(PaperOrder.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
        
    async def get_positions(self, session_id: str) -> List[PaperPosition]:
        stmt = select(PaperPosition).where(PaperPosition.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
        
    async def get_checkpoints(self, session_id: str) -> List[PaperSessionCheckpoint]:
        stmt = select(PaperSessionCheckpoint).where(PaperSessionCheckpoint.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_equity_snapshot(self, snapshot: PortfolioUpdateEvent) -> None:
        stmt = insert(PaperEquitySnapshot).values(
            session_id=snapshot.session_id,
            timestamp=snapshot.timestamp,
            cash=snapshot.cash,
            unrealized_pnl=snapshot.unrealized_pnl,
            realized_pnl=snapshot.realized_pnl,
            total_equity=snapshot.total_equity
        )
        await self.session.execute(stmt)
        
    async def update_checkpoint(self, session_id: str, instrument_token: int, timeframe: str, timestamp) -> None:
        stmt = insert(PaperSessionCheckpoint).values(
            session_id=session_id,
            instrument_token=instrument_token,
            timeframe=timeframe,
            last_processed_timestamp=timestamp
        ).on_conflict_do_update(
            index_elements=['session_id', 'instrument_token'],
            set_={'last_processed_timestamp': timestamp}
        )
        await self.session.execute(stmt)
