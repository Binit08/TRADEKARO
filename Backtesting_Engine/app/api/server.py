"""Backtesting Engine API Server.

This server provides API endpoints for running backtests and exposing metrics.

Under production deployments:
- Configure host, port, and reload via environment variables:
  - `API_HOST` (default: `127.0.0.1` for local-only binding)
  - `API_PORT` (default: `8002`)
  - `API_RELOAD` (default: `false` to disable hot-reloading)
- Secure production deployment expectation:
  - A reverse proxy (such as Nginx, Caddy, or an AWS ALB) must handle SSL/TLS termination,
    public binding (`0.0.0.0`), client rate limiting, and proxy requests locally to `127.0.0.1`.
"""
import os
import contextvars
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import datetime
import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.routes import router
from app.api.log_patch import add_exception_handler
from app.metrics.prometheus import KITE_RETRIES

# Define a ContextVar to store request ID across async request context
request_id_var = contextvars.ContextVar("request_id", default="")

class RequestIDFilter(logging.Filter):
    """Logging filter to inject request_id from contextvars into each log record."""
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON Formatter to format log records in structured JSON format."""
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["request_id"] = getattr(record, "request_id", "")

def setup_logging():
    log_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s %(request_id)s")
    log_handler.setFormatter(formatter)
    
    # Add RequestIDFilter to the handler
    log_handler.addFilter(RequestIDFilter())
    
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.INFO)
    
    # Propagate and clear handlers for standard loggers to make them structured
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        l = logging.getLogger(logger_name)
        l.handlers = []
        l.propagate = True

setup_logging()

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    print(f"[DEBUG] Initializing Sentry with DSN: {sentry_dsn[:15]}...")
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENVIRONMENT", "production"),
        send_default_pii=True,
        debug=True,  # Added to print internal Sentry SDK logs
    )
else:
    print("[DEBUG] SENTRY_DSN is NOT set! Sentry will not be initialized.")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    from app.db.database import engine
    await engine.dispose()
    print("Database engine disposed.")

app = FastAPI(title="Backtesting Engine API", lifespan=lifespan)

add_exception_handler(app)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that injects an X-Request-ID header into log records and response headers."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)

app.add_middleware(RequestIDMiddleware)

# Reject startup if the env var is unset
if "BACKTEST_API_TOKEN" not in os.environ and "PYTEST_CURRENT_TEST" not in os.environ:
    raise RuntimeError("BACKTEST_API_TOKEN environment variable is not set")

# Configure CORS origins from configuration / environment variable
cors_origins_raw = os.getenv("BACKTEST_CORS_ORIGINS", "")
if cors_origins_raw:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
else:
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Credentials can only be allowed when origins are concrete (no wildcards)
ALLOW_CREDENTIALS = "*" not in CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Expose prometheus metrics (request count, latency, error rate)
Instrumentator().instrument(app).expose(app)

app.include_router(router)

if __name__ == "__main__":
    import os
    import uvicorn
    
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8002"))
    reload = os.getenv("API_RELOAD", "false").lower() in ("true", "1", "t", "yes")
    
    uvicorn.run("app.api.server:app", host=host, port=port, reload=reload)
