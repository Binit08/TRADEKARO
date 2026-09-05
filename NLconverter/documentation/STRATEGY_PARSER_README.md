# Trading Strategy Parser

Convert natural language trading strategies into executable Canonical JSON using an LLM.

## Overview

The Trading Strategy Parser takes a user's natural language description of a trading strategy and converts it into a structured Canonical JSON format that can be executed by downstream trading systems.

### Architecture

```
User Prompt
    ↓
System Prompt + Schema + User Input
    ↓
LLM (Gemini API)
    ↓
Raw JSON Response
    ↓
Validation & Parsing
    ↓
Canonical JSON Object
```

## Features

✅ **Clean Architecture** - Modular, type-hinted, well-organized code
✅ **Comprehensive Validation** - Multi-level JSON and schema validation
✅ **Error Handling** - Detailed error reporting for debugging
✅ **Type Hints** - Full type annotations throughout
✅ **Dataclasses** - Strong typing with Python dataclasses
✅ **LLM Integration** - Google Gemini API integration
✅ **Extensive Tests** - 26 comprehensive test cases

## Project Structure

```
strategy_parser/
├── prompts/
│   └── strategy_parser_system_prompt.txt    # System prompt for LLM
│
├── schemas/
│   └── canonical_schema.json                # Canonical schema template
│
├── parser/
│   ├── __init__.py                          # Package exports
│   ├── llm_client.py                        # Gemini API client
│   ├── strategy_parser.py                   # Main parser class
│   └── validator.py                         # Validation logic
│
├── examples/
│   └── example_usage.py                     # Usage example
│
└── tests/
    ├── __init__.py
    └── test_parser.py                       # Comprehensive test suite
```

## Installation

### Prerequisites

- Python 3.8+
- Google Gemini API key

### Setup

1. **Clone/Navigate to repository**
```bash
cd /Users/binit/NLconverter
```

2. **Ensure .env file exists with API key**
```bash
echo "GOOGLE_GEMINI_API_KEY=your_api_key_here" > .env
```

3. **Install dependencies** (if any are required)
```bash
# No external dependencies required beyond Python stdlib
```

## Usage

### Basic Usage

```python
from backend.strategy_parser import StrategyParser, load_dotenv

# Load environment variables
load_dotenv(".env")

# Initialize parser
parser = StrategyParser()

# Parse a trading strategy
user_strategy = "Buy when RSI < 30, sell when RSI > 70"
result = parser.parse_strategy(user_strategy)

# Result is a dictionary with canonical JSON structure
print(result["compilation_status"]["state"])  # "success" or "partial"
print(result["signals"]["indicators"])         # List of indicators
print(result["conditions"]["entry"])           # Entry conditions
print(result["risk"]["stop_loss"])             # Stop loss configuration
```

### Advanced Usage

```python
from backend.strategy_parser import StrategyParser, LLMConfig

# Custom LLM configuration
config = LLMConfig(
    api_key="your_key",
    model="gemini-2.0-pro",
    temperature=0.1,
    max_output_tokens=10000
)

# Custom file paths
parser = StrategyParser(
    system_prompt_path="./custom_prompt.txt",
    schema_path="./custom_schema.json",
    llm_config=config
)

result = parser.parse_strategy("Your strategy description")
```

## API Reference

### StrategyParser

Main class for parsing trading strategies.

```python
class StrategyParser:
    def __init__(
        self,
        system_prompt_path: Optional[str] = None,
        schema_path: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None
    )
    
    def parse_strategy(self, user_prompt: str) -> Dict[str, Any]
```

**Parameters:**
- `system_prompt_path`: Path to system prompt file (default: `./prompts/strategy_parser_system_prompt.txt`)
- `schema_path`: Path to canonical schema (default: `./schemas/canonical_schema.json`)
- `llm_config`: LLM configuration (default: uses `GOOGLE_GEMINI_API_KEY` env var)

**Returns:** Parsed strategy as dictionary with structure:

```json
{
  "compilation_status": {
    "state": "success",
    "blockers_count": 0,
    "assumptions_count": 0,
    "blocking_fields": []
  },
  "signals": {
    "indicators": [
      {
        "id": "indicator_1",
        "name": "SMA",
        "params": {"period": 20}
      }
    ]
  },
  "conditions": {
    "entry": {
      "id": "entry_root",
      "type": "AND",
      "children": [],
      "parse_status": {...}
    },
    "exit": {
      "id": "exit_root",
      "type": "AND",
      "children": [],
      "parse_status": {...}
    }
  },
  "risk": {
    "stop_loss": {
      "type": "percentage",
      "value": 2.0,
      "parse_status": {...}
    },
    "take_profit": {
      "type": "ratio",
      "risk_reward_ratio": 2.0,
      "parse_status": {...}
    }
  }
}
```

### LLMClient

Low-level client for Gemini API communication.

```python
class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None)
    
    def call(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None
    ) -> str
```

### LLMConfig

Configuration for LLM client.

```python
@dataclass
class LLMConfig:
    api_key: str
    model: str = "gemini-2.5-flash"
    temperature: float = 0.2
    max_output_tokens: int = 8000
    timeout: int = 30
```

### StrategyValidator

Validates parsed strategies.

```python
class StrategyValidator:
    def validate_json(self, json_str: str) -> bool
    def validate_structure(self, strategy: Dict) -> bool
    def validate_strategy(self, strategy: Dict) -> bool
    def get_errors(self) -> List[ValidationError]
    def get_error_messages(self) -> List[str]
```

## Canonical Schema

The output follows this structure:

### compilation_status
Status of compilation process and any blockers or assumptions.

```json
{
  "state": "success|partial|failed",
  "blockers_count": 0,
  "assumptions_count": 0,
  "blocking_fields": ["field1", "field2"]
}
```

### signals
Technical indicators used in the strategy.

```json
{
  "indicators": [
    {
      "id": "unique_id",
      "name": "SMA",
      "params": {"period": 20}
    }
  ]
}
```

### conditions
Entry and exit conditions.

```json
{
  "entry": {
    "id": "entry_root",
    "type": "AND|OR|NOT",
    "children": [],
    "parse_status": {...}
  },
  "exit": {
    "id": "exit_root",
    "type": "AND|OR|NOT",
    "children": [],
    "parse_status": {...}
  }
}
```

### risk
Risk management parameters.

```json
{
  "stop_loss": {
    "type": "percentage|price|atr",
    "value": 2.0,
    "parse_status": {...}
  },
  "take_profit": {
    "type": "ratio|price",
    "value": null,
    "risk_reward_ratio": 2.0,
    "parse_status": {...}
  }
}
```

## Testing

### Run All Tests

```bash
python3 -m pytest strategy_parser/tests/test_parser.py -v
```

### Test Coverage

The test suite includes:
- **Validator Tests** (12 tests) - JSON validation, structure validation, field type checking
- **LLM Client Tests** (4 tests) - Configuration, URL building, error handling
- **Parser Tests** (7 tests) - Parser initialization, prompt building, strategy parsing
- **Integration Tests** (3 tests) - End-to-end validation, schema structure, file existence

### Run Specific Test

```bash
python3 -m pytest strategy_parser/tests/test_parser.py::TestStrategyValidator -v
```

## Error Handling

### Validation Errors

```python
try:
    result = parser.parse_strategy("Buy signal")
except ValueError as e:
    print(f"Validation error: {e}")
```

### LLM Errors

```python
try:
    result = parser.parse_strategy("Strategy")
except RuntimeError as e:
    print(f"LLM error: {e}")
```

### File Not Found Errors

```python
try:
    parser = StrategyParser(system_prompt_path="/nonexistent/path")
except FileNotFoundError as e:
    print(f"File error: {e}")
```

## Example

```python
#!/usr/bin/env python3
from backend.strategy_parser import StrategyParser, load_dotenv

load_dotenv(".env")
parser = StrategyParser()

strategy = """
Buy when:
- Price crosses above 20-day SMA
- RSI is between 50 and 70
- Volume > 1M

Sell when:
- Price falls below 20-day SMA
- RSI > 80

Stop loss: 2% below entry
Take profit: 3:1 risk/reward
"""

result = parser.parse_strategy(strategy)

print(f"Status: {result['compilation_status']['state']}")
print(f"Entry conditions: {result['conditions']['entry']}")
print(f"Risk management: {result['risk']}")
```

## System Prompt

The LLM is guided by a system prompt that ensures:
- JSON-only output (no markdown, explanations, or comments)
- Strict schema compliance
- Field preservation from user intent
- Assumption and blocker tracking
- Deterministic values

See `strategy_parser/prompts/strategy_parser_system_prompt.txt` for the full prompt.

## Validation Rules

The validator enforces:

1. **Valid JSON** - Responses must be valid JSON
2. **Required Top-Level Fields** - `compilation_status`, `signals`, `conditions`, `risk`
3. **Required Nested Fields** - Each object has required fields (e.g., `compilation_status` needs `state`, `blockers_count`)
4. **Type Checking** - Fields must be correct types (strings, numbers, lists, booleans)
5. **Parse Status** - All major sections include parse status with confidence scores

## Troubleshooting

### API Key Not Found
```
RuntimeError: GOOGLE_GEMINI_API_KEY is not set
```
**Solution:** Create `.env` file with API key or pass `LLMConfig` explicitly.

### Invalid JSON Response
```
ValueError: LLM response is not valid JSON
```
**Solution:** Check LLM model and temperature settings. Lower temperature (0.1-0.3) produces more deterministic JSON.

### Missing Required Fields
```
ValueError: Strategy validation failed
```
**Solution:** Ensure LLM response includes all required fields. Increase `max_output_tokens` if response is truncated.

## Performance

- **Parsing Time**: ~1-5 seconds (depends on LLM latency)
- **Validation Time**: <100ms
- **Model**: Gemini 2.5 Flash (fast, cost-effective)
- **Tokens**: ~2000-5000 per request (depending on strategy complexity)

## Future Enhancements

- [ ] Support for multiple LLM providers (OpenAI, Anthropic, Ollama)
- [ ] Strategy caching and versioning
- [ ] Interactive strategy refinement
- [ ] Real-time backtesting integration
- [ ] Strategy similarity matching
- [ ] Multi-language support

## License

MIT

## Contributing

Contributions welcome! Please ensure:
1. All tests pass (`pytest strategy_parser/tests/test_parser.py`)
2. Type hints on all functions
3. Docstrings on public methods
4. New tests for new functionality

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review test cases for usage patterns
3. Check LLM response in error messages
4. Verify .env file and API key validity
