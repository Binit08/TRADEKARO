# Trading Strategy Parser - Quick Start Guide

## 5-Minute Setup

### 1. Verify Installation
```bash
cd /Users/binit/NLconverter
python3 -c "from backend.strategy_parser import StrategyParser; print('✓ Parser ready')"
```

### 2. Verify Tests Pass
```bash
python3 -m pytest strategy_parser/tests/test_parser.py -q
```

Expected output: `26 passed`

### 3. Use the Parser

```python
from backend.strategy_parser import StrategyParser, load_dotenv

# Load environment
load_dotenv(".env")

# Create parser
parser = StrategyParser()

# Parse strategy
result = parser.parse_strategy(
    "Buy when RSI < 30, sell when RSI > 70, 2% stop loss"
)

# Check result
print(result["compilation_status"]["state"])  # Should be "success"
```

## Core Components

| File | Purpose |
|------|---------|
| `llm_client.py` | Gemini API communication |
| `strategy_parser.py` | Main parsing logic |
| `validator.py` | JSON/schema validation |
| `test_parser.py` | 26 comprehensive tests |

## Key Classes

### StrategyParser
```python
parser = StrategyParser()
result = parser.parse_strategy(user_prompt)
```

### LLMClient
```python
client = LLMClient(config)
response = client.call(user_prompt, system_prompt)
```

### StrategyValidator
```python
validator = StrategyValidator()
is_valid = validator.validate_strategy(strategy_dict)
errors = validator.get_error_messages()
```

## Common Tasks

### Parse a Simple Strategy
```python
from backend.strategy_parser import StrategyParser, load_dotenv

load_dotenv(".env")
parser = StrategyParser()

strategy = "Buy SMA(20) > SMA(50), sell on RSI > 70"
result = parser.parse_strategy(strategy)
```

### Handle Errors
```python
from backend.strategy_parser import StrategyParser

parser = StrategyParser()

try:
    result = parser.parse_strategy("Buy signal")
except ValueError as e:
    print(f"Validation failed: {e}")
except RuntimeError as e:
    print(f"LLM error: {e}")
```

### Use Custom Configuration
```python
from backend.strategy_parser import StrategyParser, LLMConfig

config = LLMConfig(
    api_key="your_key",
    temperature=0.1,  # More deterministic
    max_output_tokens=8000
)

parser = StrategyParser(llm_config=config)
```

### Access Parsed Data
```python
result = parser.parse_strategy("Strategy description")

# Compilation status
status = result["compilation_status"]["state"]
blockers = result["compilation_status"]["blockers_count"]

# Signals (technical indicators)
indicators = result["signals"]["indicators"]

# Trading logic
entry = result["conditions"]["entry"]
exit_cond = result["conditions"]["exit"]

# Risk management
stop_loss = result["risk"]["stop_loss"]
take_profit = result["risk"]["take_profit"]
```

## Validation Output

When validation fails, you get detailed errors:

```
compilation_status.state: state must be a string
compilation_status.blockers_count: blockers_count must be an integer
conditions: Missing required field: entry
```

## Environment Setup

### 1. .env File
```bash
cat > .env << 'EOF'
GOOGLE_GEMINI_API_KEY=your_api_key_here
EOF
```

### 2. Verify API Key
```bash
python3 -c "
from backend.strategy_parser import load_dotenv
import os
load_dotenv('.env')
print('✓ API Key loaded' if os.getenv('GOOGLE_GEMINI_API_KEY') else '✗ Not found')
"
```

## Running Tests

### Run all tests
```bash
python3 -m pytest strategy_parser/tests/test_parser.py -v
```

### Run specific test class
```bash
python3 -m pytest strategy_parser/tests/test_parser.py::TestStrategyValidator -v
```

### Run with coverage
```bash
python3 -m pytest strategy_parser/tests/test_parser.py --cov=strategy_parser
```

## Expected JSON Output

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
        "id": "sma_1",
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
      "parse_status": {
        "state": "parsed",
        "confidence": 0.95,
        "message": "Entry condition parsed successfully"
      }
    }
  },
  "risk": {
    "stop_loss": {
      "type": "percentage",
      "value": 2.0,
      "parse_status": {
        "state": "parsed",
        "confidence": 1.0,
        "message": ""
      }
    }
  }
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API key not found | Set `GOOGLE_GEMINI_API_KEY` in .env |
| Invalid JSON response | Lower temperature to 0.1 |
| Missing fields | Increase `max_output_tokens` |
| Timeout errors | Check internet connection |
| Import errors | Verify you're in correct directory |

## Next Steps

1. ✅ Verify everything works with the tests
2. ✅ Try parsing a simple strategy
3. ✅ Inspect the canonical JSON output
4. ✅ Check error handling with invalid input
5. ✅ Review `examples/example_usage.py` for more patterns

## Resources

- **Full Documentation**: See `STRATEGY_PARSER_README.md`
- **Test Examples**: See `strategy_parser/tests/test_parser.py`
- **System Prompt**: See `strategy_parser/prompts/strategy_parser_system_prompt.txt`
- **Schema Template**: See `strategy_parser/schemas/canonical_schema.json`

## Support

For more details, see the comprehensive README or check test cases for usage examples.
