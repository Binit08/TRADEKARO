"""Signal engine models and enums."""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class SignalResult:
    """Structured signal result."""
    signal: SignalType
    reason: Dict[str, Any] | None = None
