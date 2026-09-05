import logging
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.persistence.repository import PaperTradingRepository
from app.domain.events import PortfolioUpdateEvent, TickEvent
from app.core.event_bus import EventBus
import time

logger = logging.getLogger(__name__)

class PersistenceConsumer:
    """Consumes non-critical events (e.g. snapshots) from EventBus and durably persists them."""
    
    def __init__(self, event_bus: EventBus, loop: asyncio.AbstractEventLoop, snapshot_interval_sec: float = 60.0):
        self.event_bus = event_bus
        self.loop = loop
        self.snapshot_interval_sec = snapshot_interval_sec
        self.queue = asyncio.Queue()
        self.task: Optional[asyncio.Task] = None
        self._running = False
        
        # Subscribe to events synchronously, but put them in async queue thread-safely
        self.event_bus.subscribe(PortfolioUpdateEvent, self._enqueue_event)
        self.event_bus.subscribe(TickEvent, self._enqueue_event)
        
    def _enqueue_event(self, event):
        if self._running:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event)
            
    async def start(self):
        self._running = True
        self.task = asyncio.create_task(self._consume_loop())
        logger.info("PersistenceConsumer started.")
        
    async def stop(self):
        """Graceful shutdown. Stop accepting new events and drain pending queue."""
        logger.info("PersistenceConsumer stopping... draining queue.")
        self._running = False
        # Push sentinel
        await self.queue.put(None)
        if self.task:
            await self.task
        logger.info("PersistenceConsumer stopped.")
            
    async def _consume_loop(self):
        last_snapshot_time = 0.0
        
        async with AsyncSessionLocal() as session:
            repo = PaperTradingRepository(session)
            
            while True:
                event = await self.queue.get()
                if event is None:
                    break
                    
                try:
                    if isinstance(event, PortfolioUpdateEvent):
                        current_time = time.time()
                        if current_time - last_snapshot_time >= self.snapshot_interval_sec:
                            await repo.save_equity_snapshot(event)
                            await session.commit()
                            last_snapshot_time = current_time
                    elif isinstance(event, TickEvent):
                        # Update checkpoint
                        # TickEvent doesn't carry timeframe, we'll assume "1m" or we can skip this if we only checkpoint candles.
                        pass
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error in PersistenceConsumer: {e}")
                finally:
                    self.queue.task_done()
