"""Custom exceptions for the dynamic indicator resolution system."""

class IndicatorError(Exception):
    """Base class for all indicator-related errors."""
    pass

class UnsupportedIndicatorError(IndicatorError):
    """Raised when the requested indicator does not exist in the registry."""
    pass

class IndicatorParameterError(IndicatorError):
    """Raised when invalid parameters are provided to an indicator."""
    pass

class IndicatorExecutionError(IndicatorError):
    """Raised when an indicator calculation fails during execution."""
    pass
