# Deployment Guide

| Field          | Value                                  |
|----------------|----------------------------------------|
| **Project**    | TradeKaro — NLconverter                |
| **Doc Type**   | Deployment Guide                       |
| **Version**    | 1.0.0                                  |
| **Author**     | TradeKaro Team                         |
| **Last Updated** | 2026-09-02                           |

---

## 1. Overview

The NLconverter system consists of three main services:
1. **Frontend**: Next.js application (Port 3000)
2. **Backend**: FastAPI application (Port 8000)
3. **Backtesting Engine**: Separate FastAPI application (Port 8002)

## 2. Local Development

### 2.1 The `start_services.sh` Script

The easiest way to run the entire stack locally is using the provided `start_services.sh` script in the root directory.

```bash
./start_services.sh
```

**What this script does:**
1. Starts the **Backtesting Engine** on port 8002 (requires the `Backtesting_Engine` directory to be located at `../../BackTesting/Backtesting_Engine` relative to the script).
2. Starts the **NLconverter Backend** on port 8000.
3. Starts the **NLconverter Frontend** (Next.js) on port 3000.
4. Traps `SIGINT` (Ctrl+C) to gracefully shut down all background processes when you exit.

### 2.2 Manual Startup

If you need to start services individually for debugging:

**Backend:**
```bash
cd backend
source .venv/bin/activate  # or venv/bin/activate
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Backtesting Engine:**
```bash
cd ../../BackTesting/Backtesting_Engine
source .venv/bin/activate
uvicorn app.api.server:app --reload --port 8002 --host 0.0.0.0
```

---

## 3. Docker Deployment

The repository includes a Dockerfile for the backend service.

### 3.1 Backend Dockerfile (`Dockerfile.backend`)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Building and Running

```bash
# Build the image
docker build -f Dockerfile.backend -t nlconverter-backend .

# Run the container
# Note: You must pass required environment variables
docker run -p 8000:8000 \
  -e GOOGLE_GEMINI_API_KEY=your_key \
  -e API_KEY=your_backend_key \
  nlconverter-backend
```

> [!WARNING]
> **No Docker Compose or Kubernetes:** Currently, there is no `docker-compose.yml` or Kubernetes manifests provided for a full-stack deployment. Deploying the frontend and backtesting engine via Docker is `TODO: not yet implemented`.

---

## 4. Environment Variables Reference

### 4.1 Backend (`backend/.env`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_GEMINI_API_KEY` | Key for Google Gemini LLM | ✅ | |
| `API_KEY` | Shared secret for backend API access (`X-API-Key`) | ✅ | |
| `DATABASE_URL` | SQLAlchemy connection string | | `sqlite:///./sql_app.db` |
| `SUPABASE_JWT_SECRET` | Secret to verify Supabase JWTs | | (Skips verification if empty) |
| `KITE_API_KEY` | Zerodha Kite API key | | |
| `KITE_API_SECRET` | Zerodha Kite API secret | | |
| `RATE_LIMIT_DURATION` | Rate limit window in seconds | | `60` |
| `MAX_REQUESTS_PER_DURATION` | Max requests per IP in window | | `10` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins | | `http://localhost:3000` |
| `SENTRY_DSN` | DSN for Sentry error tracking | | |

### 4.2 Frontend (`frontend/.env.local`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BACKEND_URL` | URL of the FastAPI backend | | `http://127.0.0.1:8000` |
| `BACKEND_API_KEY` | Shared secret (must match backend's `API_KEY`) | ✅ | |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | ✅ | |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase public anonymous key | ✅ | |

### 4.3 Backtesting Engine Integration

The `start_services.sh` script automatically injects:
- `BACKTEST_API_TOKEN` into the Backtesting Engine environment.
- `BACKTEST_ENGINE_API_KEY` into the NLconverter Backend environment.

These must match for the proxy requests to succeed.

---

## 5. Database Setup & Migrations

The backend uses SQLAlchemy and Alembic for database management.

### 5.1 Initialization

By default, the backend will create a SQLite database (`sql_app.db`) in the `backend/` directory if no `DATABASE_URL` is provided.

For production (PostgreSQL), set `DATABASE_URL=postgresql://user:pass@host:port/dbname`.

### 5.2 Alembic Migrations

If you make changes to the SQLAlchemy models in `backend/db/models.py`, you must generate and apply a migration:

```bash
cd backend

# Generate a new migration script
alembic revision --autogenerate -m "Add new column to strategy"

# Apply the migration to the database
alembic upgrade head
```

---

## 6. CI/CD Pipeline

The repository uses GitHub Actions for Continuous Integration.

### 6.1 Workflows (`.github/workflows/ci.yml`)

The current CI workflow runs on pushes and pull requests to the `main` branch.

**Jobs:**
- `test`: Runs on `ubuntu-latest`.
- **Purpose**: Currently only verifies that the `GOOGLE_GEMINI_API_KEY` secret is configured in the repository.

> [!NOTE]
> **CI/CD Gaps:** The current CI workflow does *not* run the `pytest` test suite, lint the frontend code, or build Docker images. Automated deployment (CD) is `TODO: not yet implemented`.
