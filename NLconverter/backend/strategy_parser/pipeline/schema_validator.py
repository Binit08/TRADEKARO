from typing import Dict, Any, Tuple

from backend.strategy_parser.parser.validator import StrategyValidator


class SchemaValidator:
    """
    Validates Canonical JSON.
    Detects invalid indicator parameters, invalid ranges, missing required fields, unsupported operators.
    """

    def __init__(self, validator: StrategyValidator):
        self.validator = validator

    def validate(self, canonical_json: Dict[str, Any]) -> Tuple[bool, list[str]]:
        """
        Returns (is_valid, list_of_errors)
        """
        is_valid = self.validator.validate_strategy(canonical_json)
        errors = self.validator.get_error_messages()
        return is_valid, errors
