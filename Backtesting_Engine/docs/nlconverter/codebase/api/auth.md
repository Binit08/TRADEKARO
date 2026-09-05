# Auth

## What it is
The `auth.py` module handles JSON Web Token (JWT) verification, specifically integrating with Supabase to validate user identity.

## Why it exists
To prevent unauthorized access to the trading platform and protect sensitive API keys (like Kite Connect tokens) stored in the database, every protected endpoint requires a valid JWT. This module ensures that only authenticated users can run backtests or save strategies.

## Data Flow
1. A request arrives with an `Authorization: Bearer <token>` header.
2. The `get_current_user` dependency intercepts the request.
3. Validates the JWT signature against the Supabase secret.
4. Extracts the `user_id` from the token payload.
5. Queries the database to fetch the corresponding `User` model and injects it into the route handler.

## Source Code Reference

::: backend.api.auth
    options:
      show_root_heading: false
      show_source: true
      heading_level: 3
