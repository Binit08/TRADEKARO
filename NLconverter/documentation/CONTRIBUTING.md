# Contributing Guide

| Field          | Value                                  |
|----------------|----------------------------------------|
| **Project**    | TradeKaro — NLconverter                |
| **Doc Type**   | Contributing Guide                     |
| **Version**    | 1.0.0                                  |
| **Author**     | TradeKaro Team                         |
| **Last Updated** | 2026-09-02                           |

---

## 1. Prerequisites

| Tool       | Minimum Version | Purpose                        |
|------------|----------------|--------------------------------|
| Python     | 3.11+          | Backend runtime                |
| Node.js    | 18+            | Frontend runtime               |
| npm        | 9+             | Frontend package manager       |
| Git        | 2.x            | Version control                |
| SQLite     | 3.x            | Default local database (built into Python) |

---

## 2. Local Development Setup

### 2.1 Clone the Repository

```bash
git clone https://github.com/TradeKaro/NLconverter.git
cd NLconverter
```

### 2.2 Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your Google Gemini API key, API_KEY, and other secrets
```

Required environment variables (see [DEPLOYMENT.md](./DEPLOYMENT.md) for full reference):
- `GOOGLE_GEMINI_API_KEY` — Google Gemini API key
- `API_KEY` — Backend API key for `X-API-Key` header validation

### 2.3 Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local  # or create .env.local manually
# Add BACKEND_URL and BACKEND_API_KEY
```

### 2.4 Running the Full Stack

The easiest way to start all three services (Frontend, Backend, Backtesting Engine):

```bash
./start_services.sh
```

This starts:
| Service            | Port | Command                                            |
|--------------------|------|----------------------------------------------------|
| Frontend           | 3000 | `npm run dev` (Next.js with Turbopack)              |
| NLconverter Backend | 8000 | `uvicorn main:app --reload --port 8000`            |
| Backtesting Engine | 8002 | `uvicorn app.api.server:app --reload --port 8002`  |

Or start services individually:

```bash
# Backend only
cd backend && source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend only
cd frontend && npm run dev
```

---

## 3. Branching Strategy

### Active Branches

| Branch         | Purpose                          |
|----------------|----------------------------------|
| `main`         | Production-ready releases        |
| `ast-enhance`  | AST enhancements (current dev)   |
| `front`        | Frontend development             |
| `kite`         | Kite broker integration          |
| `latest2`      | Latest feature integration       |
| `new`          | Experimental features            |
| `open`         | Open development                 |

### Workflow

1. Create a feature branch from `ast-enhance` (or the current active development branch)
2. Use descriptive branch names: `feature/rag-improvements`, `fix/backtest-normalization`, `docs/api-reference`
3. Make small, focused commits
4. Open a Pull Request against the source branch

---

## 4. Commit Conventions

Use clear, descriptive commit messages. Recommended prefixes:

| Prefix    | Purpose                         | Example                                  |
|-----------|--------------------------------|------------------------------------------|
| `feat:`   | New feature                    | `feat: add futures schema support`       |
| `fix:`    | Bug fix                        | `fix: backtest normalization for multi-symbol` |
| `docs:`   | Documentation changes           | `docs: add API reference`                |
| `refactor:` | Code restructuring           | `refactor: extract pipeline stages`      |
| `test:`   | Adding or updating tests        | `test: add AST builder edge cases`       |
| `chore:`  | Build/config/tool changes       | `chore: update requirements.txt`         |

---

## 5. Code Style

### Python (Backend)

- **Type hints**: Required on all public function signatures
- **Docstrings**: Required on all public classes and methods (Google-style or reStructuredText)
- **Logging**: Use the `logging` module with `logger = logging.getLogger("nlconverter")`
- **Imports**: Standard library → third-party → local, separated by blank lines
- **Line length**: 120 characters max (soft limit)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### TypeScript (Frontend)

- **Strict mode**: Enabled via `tsconfig.json`
- **Interfaces**: Prefer `interface` over `type` for object shapes
- **Components**: Functional components with hooks
- **File naming**: `PascalCase.tsx` for components, `camelCase.ts` for utilities

---

## 6. How To: Add a New Indicator to the RAG Knowledge Base

The RAG knowledge base is a DuckDB database at `backend/data/knowledge_base.duckdb`. To add a new indicator:

1. **Create a `KnowledgeDoc` entry** with the indicator's canonical name, aliases, embedding text, and metadata:

```python
from backend.strategy_parser.rag.models import KnowledgeDoc

doc = KnowledgeDoc(
    id="ind_supertrend",
    type="indicator",
    canonical_name="SuperTrend",
    aliases=["super trend", "supertrend indicator", "ST"],
    maps_to_field="indicator",
    embedding_text="SuperTrend is a trend-following indicator that uses ATR to calculate dynamic support and resistance levels. It flips between bullish and bearish states based on price crossing the SuperTrend line.",
    metadata={"default_params": {"period": 10, "multiplier": 3.0}}
)
```

2. **Insert into DuckDB** with the embedding vector:

```python
from backend.strategy_parser.rag.embedding import GeminiEmbeddingClient

client = GeminiEmbeddingClient()
vec = client.embed_text(doc.embedding_text)

import duckdb
conn = duckdb.connect("backend/data/knowledge_base.duckdb")
conn.execute("""
    INSERT INTO knowledge_docs (id, type, canonical_name, aliases, maps_to_field, embedding_text, metadata, vec)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (doc.id, doc.type, doc.canonical_name, doc.aliases, doc.maps_to_field, doc.embedding_text, json.dumps(doc.metadata), vec))
conn.close()
```

3. **No code changes needed** — the `HybridRetriever` and `SemanticResolver` will automatically discover the new indicator on the next query.

---

## 7. How To: Add a New AST Node Type

1. **Define the node class** in `backend/strategy_parser/ast/ast_nodes.py`:

```python
@dataclass
class CustomPatternNode(ASTNode):
    """Node representing a custom pattern detection."""
    pattern_config: dict = field(default_factory=dict)
    
    @property
    def node_type(self) -> str:
        return "CUSTOM_PATTERN"
```

2. **Register the node** in the `ASTNodeRegistry`:

```python
ASTNodeRegistry.register("CUSTOM_PATTERN", CustomPatternNode)
```

3. **Add a builder function** in `backend/strategy_parser/ast/ast_builder.py`:

```python
def _build_custom_pattern(self, data: dict, path: str) -> CustomPatternNode:
    return CustomPatternNode(
        pattern_config=data.get("pattern_config", {}),
        metadata=ASTNodeMetadata(source_path=path)
    )
```

4. **Register the builder**:

```python
builder.register_condition_builder("CUSTOM_PATTERN", builder._build_custom_pattern)
```

5. **Update exports** in `backend/strategy_parser/ast/__init__.py`

6. **Add tests** in `backend/strategy_parser/tests/`

---

## 8. How To: Add a Strategy Template

`TODO: Strategy template system not yet implemented. See PRD.md §4 — Out of Scope.`

---

## 9. ADR Process

Architecture Decision Records are stored in `documentation/adr/`. See the [ADR README](./adr/README.md) for the process and index.

When making a significant architectural decision:
1. Copy `documentation/adr/template.md` to `documentation/adr/NNNN-title.md`
2. Fill in Context, Decision, Status, and Consequences
3. Add the ADR to the index in `documentation/adr/README.md`
4. Reference the ADR in your PR description

---

## 10. Pull Request Process

1. **Branch**: Create a feature branch from the active development branch
2. **Implement**: Write code following the style guidelines above
3. **Test**: Ensure existing tests pass — `python -m pytest backend/tests/ -v`
4. **Document**: Update relevant documentation if your change affects APIs, schemas, or architecture
5. **PR**: Open a Pull Request with:
   - Clear title and description
   - Link to related issues (if any)
   - ADR reference (if applicable)
   - Screenshot/recording for UI changes
6. **Review**: Address review feedback
7. **Merge**: Squash and merge (preferred) or regular merge

---

## 11. Docstring Expectations

All public classes and functions must have docstrings. Preferred format:

```python
def process_strategy(self, payload: StrategyRequest) -> dict:
    """
    Execute the full 7-stage strategy compilation pipeline.
    
    Args:
        payload: The strategy request containing prompt, execution context,
                 and optional semantic resolutions.
    
    Returns:
        Dictionary with status, strategy ID, canonical JSON, and AST JSON.
    
    Raises:
        HTTPException: If validation fails at any pipeline stage.
        ASTBuildError: If AST generation encounters an unrecoverable error.
    """
```
