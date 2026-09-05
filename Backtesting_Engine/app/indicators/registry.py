"""Indicator Registry for dynamically discovering TA-Lib indicators."""

from typing import Dict, List

import talib
from talib import abstract

from app.indicators.metadata import IndicatorMetadata
from app.indicators.exceptions import UnsupportedIndicatorError


class IndicatorRegistry:
    """Discovers and catalogs all available indicators from TA-Lib."""

    def __init__(self):
        self._registry: Dict[str, IndicatorMetadata] = {}
        self._initialize_registry()

    def _initialize_registry(self) -> None:
        """Scan TA-Lib and pre-populate the metadata registry."""
        functions = talib.get_functions()
        for func_name in functions:
            try:
                func = abstract.Function(func_name)
                info = func.info
                
                # Extract input names dynamically
                # info['input_names'] is usually OrderedDict([('price', 'close')]) or similar
                inputs = []
                for val in info.get("input_names", {}).values():
                    if isinstance(val, str):
                        inputs.append(val)
                    elif isinstance(val, (list, tuple)):
                        inputs.extend(val)
                
                metadata = IndicatorMetadata(
                    name=info.get("name", func_name).upper(),
                    group=info.get("group", "Unknown"),
                    display_name=info.get("display_name", func_name),
                    required_inputs=inputs,
                    parameters=info.get("parameters", {}),
                    output_names=info.get("output_names", ["real"])
                )
                self._registry[metadata.name] = metadata
            except Exception:
                # Silently skip any functions that abstract cannot parse
                continue

    def get_metadata(self, name: str) -> IndicatorMetadata:
        """Retrieve metadata for a specific indicator.
        
        Raises:
            UnsupportedIndicatorError: If the indicator is not found.
        """
        name = name.strip().upper()
        if name not in self._registry:
            raise UnsupportedIndicatorError(f"Unsupported indicator: {name}")
        return self._registry[name]

    def is_supported(self, name: str) -> bool:
        """Check if an indicator is supported by the registry."""
        return name.strip().upper() in self._registry

    def get_all_supported(self) -> List[str]:
        """Return a list of all supported indicator names."""
        return list(self._registry.keys())

# Create a global singleton registry for the engine to use
registry = IndicatorRegistry()
