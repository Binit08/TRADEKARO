import os
import time
from collections import defaultdict
from fastapi import Request, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

_api_key = os.getenv("API_KEY")
if not _api_key:
    raise RuntimeError(
        "FATAL: API_KEY environment variable is not set. "
        "Set it in backend/.env or export it before starting the server."
    )

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != _api_key:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

# Rate limiting
RATE_LIMIT_DURATION = int(os.getenv("RATE_LIMIT_DURATION", "60"))
MAX_REQUESTS_PER_DURATION = int(os.getenv("MAX_REQUESTS_PER_DURATION", "300"))
ip_request_counts: dict = defaultdict(list)

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if len(ip_request_counts) > 1000:
        stale_ips = [ip for ip, times in ip_request_counts.items() if not times or now - times[-1] > RATE_LIMIT_DURATION]
        for ip in stale_ips:
            if ip in ip_request_counts:
                del ip_request_counts[ip]

    ip_request_counts[client_ip] = [
        t for t in ip_request_counts[client_ip] if now - t < RATE_LIMIT_DURATION
    ]

    if len(ip_request_counts[client_ip]) >= MAX_REQUESTS_PER_DURATION:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    ip_request_counts[client_ip].append(now)
