# Testing Strategy

| Field          | Value                                  |
|----------------|----------------------------------------|
| **Project**    | TradeKaro — NLconverter                |
| **Doc Type**   | Testing Strategy                       |
| **Version**    | 1.0.0                                  |
| **Author**     | TradeKaro Team                         |
| **Last Updated** | 2026-09-02                           |

---

## 1. Test Pyramid

NLconverter follows a standard test pyramid approach:

1. **Unit Tests (Fast, Isolated)**: Validating individual AST builders, schema constraints, RAG normalizers, and JSON parsing logic.
2. **Integration Tests (Medium, Connected)**: Testing the full 7-stage pipeline with a mocked LLM, database session behavior, and endpoint routing.
3. **End-to-End (E2E) Tests (Slow, Full System)**: Testing the frontend UI interacting with the backend and backtesting engine. *(Note: E2E testing is `TODO: not yet implemented`)*

---

## 2. Backend Testing (`pytest`)

The backend test suite is located in `backend/tests/` and `backend/strategy_parser/tests/`.

### 2.1 Running Tests

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ strategy_parser/tests/ -v
```

### 2.2 What to Test Per Component

| Component | Test Focus |
|-----------|------------|
| **StrategyParser** | Ensure correct compilation status states (success, semantic_approval). |
| **Validator** | Verify that invalid Canonical JSON is rejected (missing fields, wrong types, nested condition failures). |
| **AST Builder** | Test rule-based conversion from Canonical JSON to AST nodes. Verify nested logic (AND/OR). |
| **SemanticResolver** | Test threshold gating: verify terms > 0.03 RRF score become `parsed` or `assumed`, and below become `unparsed`. |
| **LLM Client** | Test connection handling, retries, timeout management, and JSON extraction from markdown fences. |
| **API Routers** | Test endpoint status codes (200, 400, 401, 403, 404, 422), rate limiting, and API key validation. |

### 2.3 Mocking Strategy

When testing the compilation pipeline, **never make real calls to the Google Gemini API**. Real calls introduce latency, cost, and non-determinism.

Instead, mock the `LLMClient.call()` method using `unittest.mock`:

```python
from unittest.mock import patch

@patch("backend.strategy_parser.parser.llm_client.LLMClient.call")
def test_strategy_parsing(mock_llm_call):
    # Setup mock response
    mock_llm_call.return_value = '{"signals": {...}, "operation": [...], "risk": {...}}'
    
    # Run test
    parser = StrategyParser()
    result = parser.parse_strategy("Buy RSI < 30")
    
    assert result["compilation_status"]["state"] == "success"
```

Database interactions in API tests should use an in-memory SQLite database (`sqlite:///:memory:`) configured via test dependencies.

### 2.4 Test Data Management

Use JSON fixture files for complex inputs (like large Canonical JSON examples or raw ASTs). Store these in `backend/tests/fixtures/`.

Avoid hardcoding 200-line JSON strings in test files. Load them dynamically:

```python
import json
import os

def load_fixture(name: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "fixtures", f"{name}.json")
    with open(path, "r") as f:
        return json.load(f)
```

---

## 3. Frontend Testing

> [!WARNING]
> Frontend testing (Jest, React Testing Library, Cypress/Playwright) is currently `TODO: not yet implemented`.

When implemented, the frontend testing strategy should focus on:
1. **Component Tests**: Verifying the `NaturalLanguageEditor` captures input, and `AIClarificationModal` renders dynamic RAG candidates.
2. **State Management**: Testing the Zustand `backtestStore` updates correctly on API responses.
3. **API Proxying**: Ensuring Next.js API routes correctly inject the `BACKEND_API_KEY` before forwarding requests to FastAPI.

---

## 4. Coverage Guidance

While 100% test coverage is rarely practical, the following paths are **critical** and must maintain high coverage:

1. **Schema Validation**: Every rule in `EQUITY_SCHEMA.json` and `FUTURES_SCHEMA.json` should have a passing and failing test case in `test_parser.py`.
2. **AST Generation**: Every node registered in `ASTNodeRegistry` must be instantiated and serialized in tests.
3. **Execution Context Merging**: Ensuring `timeframe` and `universe` map correctly from user configuration into the final AST.
4. **Auth & Security**: Tests must verify that requests without `X-API-Key` or `Authorization: Bearer` are rejected with `403` or `401`.
