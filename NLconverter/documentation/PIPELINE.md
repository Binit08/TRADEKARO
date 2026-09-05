# Prompt to AST Workflow

This repository supports a complete workflow from a natural-language strategy prompt to a deterministic AST.

## 1. Prepare your environment

- Create `.env` in the repository root.
- Add your Gemini API key or other required environment variables.
- Do not commit `.env`; it is ignored by `.gitignore`.

Example `.env`:

```text
GOOGLE_GEMINI_API_KEY=your_real_google_gemini_api_key_here
```

## 2. Provide a strategy prompt or canonical JSON

You can either:

- pass a natural-language prompt with `--strategy`
- pass a text file with `--strategy-file`
- pass an existing canonical JSON file with `--canonical-json`

Example strategy prompt:

```bash
python3 strategy_to_ast.py --strategy "Buy when RSI drops below 30 and MACD crosses above zero." --ast-json
```

Example canonical JSON file:

```bash
python3 strategy_to_ast.py --canonical-json path/to/strategy.json --ast-json
```

## 3. Optionally provide application settings JSON

If your AST builder should resolve indicators or defaults from application settings, use `--settings-json`.

Example `settings.json`:

```json
{
  "signals": {
    "indicators": [
      {
        "id": "rsi_ref",
        "indicator_type": "RSI",
        "parameters": { "period": 14 },
        "timeframe": "1D",
        "output_property": "value"
      }
    ]
  },
  "default_timeframe": "1D",
  "default_output_property": "value"
}
```

Run with settings:

```bash
python3 strategy_to_ast.py --strategy "Buy when RSI drops below 30" --settings-json settings.json --ast-json
```

## 4. The build pipeline

The pipeline is:

1. `strategy_to_ast.py` loads environment variables from `.env`.
2. It converts the prompt into canonical JSON using `StrategyParser`.
3. It loads optional settings JSON from `--settings-json`.
4. It passes canonical JSON and settings JSON into `ASTBuilder.build(...)`.
5. The AST builder recursively constructs a deterministic AST.
6. The AST is validated with `ASTValidator`.
7. The AST is serialized with `ASTSerializer` and optionally saved to `strategy_ast_output.json`.

## 5. Example full command

```bash
python3 strategy_to_ast.py \
  --strategy "Buy when RSI drops below 30 on daily timeframe and MACD histogram crosses above zero." \
  --settings-json settings.json \
  --ast-json
```

## 6. Output files

- `parsed_strategy_output.json`: the canonical JSON representation
- `strategy_ast_output.json`: the serialized AST JSON

## 7. Notes

- The AST builder is deterministic and rule-based.
- The builder does not evaluate the strategy or execute trades.
- Both the strategy JSON and settings JSON remain unchanged.
