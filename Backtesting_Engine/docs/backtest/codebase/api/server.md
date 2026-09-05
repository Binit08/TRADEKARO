# Server

## What it is
The `server.py` file initializes the FastAPI application instance for the Core Backtesting Engine, binding together the API routes, exception handlers, and CORS middleware.

## Why it exists
To run as a microservice, the core engine needs a robust HTTP server. This file acts as the Uvicorn entry point, providing the foundational FastAPI wrapper that allows the NLconverter to communicate securely with the execution sandbox.

## Data Flow
1. FastAPI `app` is instantiated with custom metadata (Title, Version).
2. CORS middleware is configured to allow internal network traffic.
3. The `backtest_router` is included under the `/api/v1` prefix.
4. Uvicorn boots the server and listens on port 8002.

## Source Code Reference

::: app.api.server
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
