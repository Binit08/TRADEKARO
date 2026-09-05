import pytest
from unittest.mock import Mock, patch
from app.session.session_manager import SessionManager
from app.session.paper_trade_session import PaperTradeSession
from app.domain.session import SessionStatus

def test_session_manager_add_and_get():
    manager = SessionManager()
    
    mock_engine = Mock()
    session = PaperTradeSession("test_id", mock_engine, ["RELIANCE"], {}, {}, None)
    
    manager.add_session(session)
    retrieved = manager.get_session("test_id")
    
    assert retrieved is session
    assert manager.get_session("unknown") is None

def test_session_manager_list():
    manager = SessionManager()
    
    session1 = PaperTradeSession("id1", Mock(), ["RELIANCE"], {}, {}, None)
    session2 = PaperTradeSession("id2", Mock(), ["TCS"], {}, {}, None)
    
    manager.add_session(session1)
    manager.add_session(session2)
    
    sessions = manager.list_sessions()
    assert sessions == {"id1": SessionStatus.CREATED, "id2": SessionStatus.CREATED}

def test_session_manager_stop():
    manager = SessionManager()
    session = PaperTradeSession("test_id", Mock(), ["RELIANCE"], {}, {}, None)
    manager.add_session(session)
    
    assert session.status == SessionStatus.CREATED
    result = manager.stop_session("test_id")
    
    assert result is True
    assert session.status == SessionStatus.STOPPED
    assert session.cancel_event.is_set()

def test_session_start():
    session = PaperTradeSession("test_id", Mock(), ["RELIANCE"], {}, {}, None)
    
    with patch("threading.Thread") as mock_thread:
        session.start()
        
        assert session.status == SessionStatus.RUNNING
        assert mock_thread.call_count == 2
