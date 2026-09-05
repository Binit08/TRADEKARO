import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent / ".env")

# Add project root directory to sys.path to resolve imports from 'backend' package
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import instruments, strategies, backtests, portfolio, paper_trade, brokers
from backend.api import auth

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("nlconverter")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
)

cors_origins_raw = os.getenv("CORS_ORIGINS", "")
if cors_origins_raw:
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
else:
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]

ALLOW_CREDENTIALS = "*" not in cors_origins

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# ---------------------------------------------------------------------------
# API Routing
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(brokers.router, prefix="/api/brokers", tags=["brokers"])
app.include_router(instruments.router, prefix="/api", tags=["instruments"])
app.include_router(strategies.router, prefix="/api", tags=["strategies"])
app.include_router(backtests.router, prefix="/api", tags=["backtests"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(paper_trade.router, prefix="/api", tags=["paper_trade"])
