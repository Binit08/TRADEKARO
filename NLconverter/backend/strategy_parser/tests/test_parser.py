"""Test suite for strategy parser."""

import json
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from backend.strategy_parser.parser import (
    StrategyParser,
    StrategyValidator,
    LLMClient,
    LLMConfig,
    ValidationError,
    load_dotenv
)

# Load environment variables from .env file
load_dotenv(".env")
os.environ["GOOGLE_GEMINI_API_KEY"] = "mock_key"


class TestStrategyValidator(unittest.TestCase):
    """Tests for StrategyValidator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = StrategyValidator()

    def test_validate_json_valid(self):
        """Test validation of valid JSON."""
        valid_json = '{"key": "value", "number": 42}'
        self.assertTrue(self.validator.validate_json(valid_json))
        self.assertEqual(len(self.validator.errors), 0)

    def test_validate_json_invalid(self):
        """Test validation of invalid JSON."""
        invalid_json = '{"key": "value", invalid}'
        self.assertFalse(self.validator.validate_json(invalid_json))
        self.assertGreater(len(self.validator.errors), 0)

    def test_validate_strategy_valid(self):
        """Test validation of complete valid strategy."""
        strategy = {
            "signals": {
                "indicators": []
            },
            "operation": [
                {
                    "entry": [],
                    "exit": []
                }
            ],
            "risk": {
                "stop_loss": {},
                "take_profit": {},
                "trailing_stop": {},
                "risk_reward": {}
            }
        }
        self.assertTrue(self.validator.validate_strategy(strategy))

    def test_validate_strategy_missing_fields(self):
        """Test validation fails with missing required fields."""
        strategy = {
            "signals": {
                "indicators": []
            }
        }
        self.assertFalse(self.validator.validate_strategy(strategy))
        error_messages = self.validator.get_error_messages()
        self.assertTrue(any("is a required property" in msg for msg in error_messages))

    def test_validate_strategy_wrong_types(self):
        """Test validation fails with wrong field types."""
        strategy = {
            "signals": "should be dict",  # Wrong type
            "operation": [
                {
                    "entry": [],
                    "exit": []
                }
            ],
            "risk": {
                "stop_loss": {},
                "take_profit": {},
                "trailing_stop": {},
                "risk_reward": {}
            }
        }
        self.assertFalse(self.validator.validate_strategy(strategy))
        error_messages = self.validator.get_error_messages()
        self.assertTrue(any("signals" in msg for msg in error_messages))

    def test_error_messages_formatting(self):
        """Test error messages are properly formatted."""
        strategy = {
            "signals": {"indicators": []}
        }
        self.validator.validate_strategy(strategy)
        messages = self.validator.get_error_messages()
        self.assertTrue(any("operation" in msg for msg in messages))


class TestLLMClient(unittest.TestCase):
    """Tests for LLMClient."""

    def test_llm_config_defaults(self):
        """Test LLMConfig default values."""
        config = LLMConfig(api_key="test_key")
        self.assertEqual(config.api_key, "test_key")
        self.assertEqual(config.model, "gemini-3.1-flash-lite")
        self.assertEqual(config.temperature, 0.2)
        self.assertEqual(config.max_output_tokens, 8000)
        self.assertEqual(config.timeout, 30)

    def test_llm_client_missing_api_key(self):
        """Test LLMClient raises error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                LLMClient()

    def test_llm_client_with_config(self):
        """Test LLMClient initialization with config."""
        config = LLMConfig(api_key="test_key", model="custom-model")
        client = LLMClient(config)
        self.assertEqual(client.config.api_key, "test_key")
        self.assertEqual(client.config.model, "custom-model")

    def test_llm_client_url_building(self):
        """Test LLM client builds correct URL."""
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)
        url = client._build_url()
        self.assertIn("generativelanguage.googleapis.com", url)
        self.assertIn("models/gemini-3.1-flash-lite", url)
        self.assertIn("key=test_key", url)


class TestStrategyParser(unittest.TestCase):
    """Tests for StrategyParser."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.test_dir = Path(__file__).parent.parent
        cls.prompt_file = cls.test_dir / "prompts" / "strategy_parser_system_prompt.txt"
        cls.schema_file = cls.test_dir / "schemas" / "canonical_schema.json"

    def test_strategy_parser_initialization(self):
        """Test StrategyParser initialization with default paths."""
        parser = StrategyParser(
            system_prompt_path=str(self.prompt_file),
            schema_path=str(self.schema_file)
        )
        self.assertIsNotNone(parser._full_system_prompt)
        self.assertIsNotNone(parser.canonical_schema)
        self.assertIsInstance(parser.canonical_schema, dict)

    def test_strategy_parser_missing_prompt_file(self):
        """Test StrategyParser raises error for missing prompt file."""
        with self.assertRaises(FileNotFoundError):
            StrategyParser(
                system_prompt_path="/nonexistent/path/prompt.txt",
                schema_path=str(self.schema_file)
            )

    def test_strategy_parser_missing_schema_file(self):
        """Test StrategyParser raises error for missing schema file."""
        with self.assertRaises(FileNotFoundError):
            StrategyParser(
                system_prompt_path=str(self.prompt_file),
                schema_path="/nonexistent/path/schema.json"
            )

    def test_build_prompt(self):
        """Test prompt building logic via the system prompt."""
        parser = StrategyParser(
            system_prompt_path=str(self.prompt_file),
            schema_path=str(self.schema_file)
        )
        full_prompt = parser._full_system_prompt
        
        self.assertIn("Canonical Schema", full_prompt)
        self.assertIn("Strict Validation Schema", full_prompt)

    @patch("backend.strategy_parser.parser.strategy_parser.LLMClient.call")
    def test_parse_strategy_success(self, mock_call):
        """Test successful strategy parsing."""
        valid_response = json.dumps({
            "signals": {"indicators": []},
            "operation": [
                {
                    "entry": [],
                    "exit": []
                }
            ],
            "risk": {
                "stop_loss": {},
                "take_profit": {},
                "trailing_stop": {},
                "risk_reward": {}
            }
        })
        mock_call.return_value = valid_response

        parser = StrategyParser(
            system_prompt_path=str(self.prompt_file),
            schema_path=str(self.schema_file)
        )
        result = parser.parse_strategy("Buy SMA crossover")

        self.assertIsInstance(result, dict)
        self.assertIn("signals", result)
        self.assertIn("operation", result)
        self.assertIn("risk", result)
        mock_call.assert_called_once()

    @patch("backend.strategy_parser.parser.strategy_parser.LLMClient.call")
    def test_parse_strategy_invalid_json(self, mock_call):
        """Test parsing fails on invalid JSON."""
        mock_call.return_value = "not valid json {"

        parser = StrategyParser(
            system_prompt_path=str(self.prompt_file),
            schema_path=str(self.schema_file)
        )
        with self.assertRaises(ValueError):
            parser.parse_strategy("Buy SMA crossover")

    @patch("backend.strategy_parser.parser.strategy_parser.LLMClient.call")
    def test_parse_strategy_missing_fields(self, mock_call):
        """Test parsing fails when required fields are missing."""
        invalid_response = json.dumps({
            "risk": {}
        })
        mock_call.return_value = invalid_response

        parser = StrategyParser(
            system_prompt_path=str(self.prompt_file),
            schema_path=str(self.schema_file)
        )
        with self.assertRaises(ValueError):
            parser.parse_strategy("Buy SMA crossover")


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.test_dir = Path(__file__).parent.parent
        cls.prompt_file = cls.test_dir / "prompts" / "strategy_parser_system_prompt.txt"
        cls.schema_file = cls.test_dir / "schemas" / "canonical_schema.json"

    def test_validator_detects_all_errors(self):
        """Test validator catches all validation errors."""
        validator = StrategyValidator()
        
        invalid_strategies = [
            {},  # Empty
            {"signals": {"indicators": []}},  # Missing fields
            {
                "signals": "wrong type",  # Wrong type
                "operation": [{"entry": [], "exit": []}],
                "risk": {"stop_loss": {}, "take_profit": {}, "trailing_stop": {}, "risk_reward": {}}
            }
        ]

        for strategy in invalid_strategies:
            validator = StrategyValidator()
            result = validator.validate_strategy(strategy)
            self.assertFalse(result, f"Should have detected errors in {strategy}")
            self.assertGreater(len(validator.get_errors()), 0)

    def test_schema_file_structure(self):
        """Test canonical schema file has expected structure."""
        with open(self.schema_file, "r") as f:
            schema = json.load(f)

        self.assertIn("signals", schema)
        self.assertIn("operation", schema)
        self.assertIn("risk", schema)

    def test_prompt_file_exists_and_not_empty(self):
        """Test system prompt file exists and contains content."""
        self.assertTrue(self.prompt_file.exists())
        with open(self.prompt_file, "r") as f:
            content = f.read()
        self.assertGreater(len(content), 0)
        self.assertIn("Trading Strategy Compiler", content)


if __name__ == "__main__":
    unittest.main()
