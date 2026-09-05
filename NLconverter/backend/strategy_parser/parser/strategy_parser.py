"""Trading strategy parser that converts natural language to canonical JSON."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .llm_client import LLMClient, LLMConfig
from ..utils import load_dotenv, strip_code_fences
from .validator import StrategyValidator


class StrategyParser:
    """Parser for converting natural language trading strategies to canonical JSON."""

    def __init__(
        self,
        system_prompt_path: Optional[Union[str, Path]] = None,
        schema_path: Optional[Union[str, Path]] = None,
        strategy_schema_path: Optional[Union[str, Path]] = None,
        llm_config: Optional[LLMConfig] = None
    ):
        """
        Initialize the strategy parser.
        
        Args:
            system_prompt_path: Path to system prompt file
            schema_path: Path to canonical schema JSON file
            llm_config: LLM configuration
            
        Raises:
            FileNotFoundError: If prompt or schema files not found
            RuntimeError: If LLM configuration is invalid
        """
        # Determine default paths relative to this file
        current_dir = Path(__file__).parent.parent
        
        if system_prompt_path is None:
            system_prompt_path = current_dir / "prompts" / "strategy_parser_system_prompt.txt"
        if schema_path is None:
            schema_path = current_dir / "schemas" / "canonical_schema.json"

        base_system_prompt = self._load_text_file(system_prompt_path)
        self.canonical_schema = self._load_json_file(schema_path)
        
        if strategy_schema_path is None:
            # Default to EQUITY_SCHEMA for backward compatibility
            # For futures strategies, explicitly pass strategy_schema_path parameter
            strategy_schema_path = current_dir / "schemas" / "EQUITY_SCHEMA.json"
        self.pure_schema = self._load_json_file(strategy_schema_path)

        
        # Fix 6: Pre-build system prompt with schemas embedded once.
        # This avoids inlining ~17KB of schema into every user prompt,
        # reducing repeated token bloat significantly.
        schema_str = json.dumps(self.canonical_schema, indent=2)
        pure_schema_str = json.dumps(self.pure_schema, indent=2)
        self._full_system_prompt = (
            f"{base_system_prompt}\n\n"
            f"## Canonical Schema (output MUST follow this exactly)\n"
            f"{schema_str}\n\n"
            f"## Strict Validation Schema (PURE_SCHEMA)\n"
            f"The output MUST also satisfy these validation rules and data types:\n"
            f"{pure_schema_str}"
        )
        
        self.llm_client = LLMClient(llm_config)
        self.validator = StrategyValidator(schema_path=Path(strategy_schema_path))

    def parse_strategy(self, user_prompt: str, rag_context: str = "") -> Dict[str, Any]:
        """
        Parse a user's natural language trading strategy into canonical JSON.
        
        Args:
            user_prompt: The user's strategy description
            rag_context: Optional string containing verified RAG definitions
            
        Returns:
            Parsed strategy as a dictionary
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If LLM call fails or response is not valid JSON
        """
        # Fix 6: Schemas are in system prompt; user prompt is lean
        user_message = (
            f"Convert this trading strategy to valid canonical JSON. "
            f"Output JSON only, no explanation.\n\n"
        )
        
        if rag_context:
            user_message += f"## RAG Context (Strict Definitions)\n{rag_context}\n\n"
            
        user_message += f"## User Strategy\n{user_prompt}"

        # Call LLM with pre-built system prompt containing schemas
        response, token_usage = self.llm_client.call(
            user_prompt=user_message,
            system_prompt=self._full_system_prompt,
            return_metrics=True
        )

        # Strip markdown code fences if present (LLM sometimes wraps JSON in ```json ... ```)
        response = strip_code_fences(response)

        # Validate JSON
        if not self.validator.validate_json(response):
            raise ValueError(
                f"LLM response is not valid JSON: {response}\n"
                f"Errors: {self.validator.get_error_messages()}"
            )

        # Parse JSON
        strategy = json.loads(response)

        # Validate structure
        if not self.validator.validate_strategy(strategy):
            raise ValueError(
                f"Strategy validation failed: {self.validator.get_error_messages()}"
            )
            
        strategy["_token_usage"] = token_usage

        return strategy

    # _build_prompt removed — Fix 6 moved schema context to system prompt
    # to avoid repeating ~17KB of schema in every user prompt.

    @staticmethod
    def _load_text_file(path: Union[str, Path]) -> str:
        """
        Load text from a file.
        
        Args:
            path: Path to file
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file not found
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _load_json_file(path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load JSON from a file.
        
        Args:
            path: Path to file
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            FileNotFoundError: If file not found
            json.JSONDecodeError: If file is not valid JSON
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


