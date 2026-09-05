"""Domain session models for the paper trading architecture."""
from enum import Enum


class SessionStatus(str, Enum):
    """Lifecycle states of a PaperTradeSession."""
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    WARMING_UP = "WARMING_UP"
    CONNECTING = "CONNECTING"
    RUNNING = "RUNNING"
    RECONNECTING = "RECONNECTING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
