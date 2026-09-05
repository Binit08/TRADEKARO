"""Validation utilities for trading strategy parsing using JSON Schema."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import jsonschema
from jsonschema import Draft202012Validator


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str  # "error" or "warning"


class StrategyValidator:
    """Validates parsed trading strategies against PURE_SCHEMA.JSON."""

    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize the validator and load the JSON Schema."""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

        if schema_path is None:
            current_dir = Path(__file__).parent.parent
            schema_path = current_dir / "schemas" / "EQUITY_SCHEMA.json"

        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
        self.validator = Draft202012Validator(self.schema)

    def validate_json(self, json_str: str) -> bool:
        """
        Validate that a string is valid JSON.
        
        Args:
            json_str: The JSON string to validate
            
        Returns:
            True if valid JSON, False otherwise
        """
        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(
                ValidationError(
                    field="root",
                    message=f"Invalid JSON: {str(e)}",
                    severity="error"
                )
            )
            return False

    def validate_strategy(self, strategy: Dict[str, Any]) -> bool:
        """
        Perform comprehensive validation of strategy using JSON Schema.
        
        Args:
            strategy: The parsed strategy dictionary
            
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        if not isinstance(strategy, dict):
            self.errors.append(
                ValidationError(
                    field="root",
                    message="Strategy must be a dictionary",
                    severity="error"
                )
            )
            return False

        # Run jsonschema validation
        schema_errors = sorted(self.validator.iter_errors(strategy), key=lambda e: e.path)
        for err in schema_errors:
            # Format the JSON path nicely, e.g., "operation[0].entry[0].type"
            path_parts = []
            for item in err.path:
                if isinstance(item, int):
                    path_parts.append(f"[{item}]")
                else:
                    if path_parts:
                        # Avoid double dots for lists
                        if path_parts[-1].startswith("["):
                            path_parts.append(item)
                        else:
                            path_parts.append(f".{item}")
                    else:
                        path_parts.append(item)
            field_path = "".join(path_parts) if path_parts else "root"

            self.errors.append(
                ValidationError(
                    field=field_path,
                    message=err.message,
                    severity="error"
                )
            )

        return len(self.errors) == 0

    def get_errors(self) -> List[ValidationError]:
        """Get all validation errors."""
        return self.errors

    def get_warnings(self) -> List[ValidationError]:
        """Get all validation warnings."""
        return self.warnings

    def get_error_messages(self) -> List[str]:
        """Get formatted error messages."""
        return [f"{e.field}: {e.message}" for e in self.errors]

    def get_warning_messages(self) -> List[str]:
        """Get formatted warning messages."""
        return [f"{e.field}: {e.message}" for e in self.warnings]
