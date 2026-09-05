"""Metadata definitions for the indicator registry."""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class IndicatorMetadata:
    """Represents the signature and metadata of a technical indicator."""
    
    name: str
    group: str
    display_name: str
    required_inputs: List[str]  # e.g., ['close'] or ['high', 'low', 'close']
    parameters: Dict[str, Any]  # Default parameters e.g., {'timeperiod': 14}
    output_names: List[str]     # e.g., ['macd', 'macdsignal', 'macdhist'] or ['real']
