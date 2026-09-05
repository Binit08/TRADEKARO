"""Session manager for paper trading."""
import logging
from typing import Dict, Optional

from app.session.paper_trade_session import PaperTradeSession

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages active paper trading sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, PaperTradeSession] = {}
        
    def add_session(self, session: PaperTradeSession) -> None:
        """Register a new session."""
        self._sessions[session.session_id] = session
        
    def get_session(self, session_id: str) -> Optional[PaperTradeSession]:
        """Retrieve a session by its ID."""
        return self._sessions.get(session_id)
        
    def list_sessions(self) -> Dict[str, str]:
        """List all sessions and their current statuses."""
        return {sid: sess.status for sid, sess in self._sessions.items()}
        
    def stop_session(self, session_id: str) -> bool:
        """Stop a running session."""
        session = self.get_session(session_id)
        if session:
            session.stop()
            logger.info(f"Session {session_id} stopped via manager.")
            return True
        return False
        
    def remove_session(self, session_id: str) -> bool:
        """Remove a session from the manager if it is stopped."""
        session = self.get_session(session_id)
        if session:
            # Optionally check if status is STOPPED or FAILED before popping
            self._sessions.pop(session_id, None)
            return True
        return False

# Global instance for FastAPI usage
session_manager = SessionManager()
