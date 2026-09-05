# Main

## What it is
The `main.py` file is the primary entry point for the NLconverter FastAPI backend, responsible for initializing the server, connecting to the database, and mounting the API routers.

## Why it exists
As the central nervous system of the middleware, this file configures global middleware (CORS, Authentication checks) and ensures the SQLAlchemy database engine is fully connected before accepting frontend requests.

## Data Flow
1. Reads environment variables (Supabase keys, DB URLs).
2. Triggers `Base.metadata.create_all(bind=engine)` to ensure SQL tables exist.
3. Mounts the `/api/backtests` and `/api/strategies` routers.
4. Starts the Uvicorn server on port 8000, listening for Next.js frontend traffic.

## Source Code Reference

::: backend.main
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
