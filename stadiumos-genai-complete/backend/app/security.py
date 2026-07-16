"""
Security controls for StadiumOS GenAI.

Implements, deliberately in one auditable module:
  1. A sliding-window in-memory rate limiter (per client IP).
  2. Security response headers (CSP, HSTS, X-Content-Type-Options, ...).
  3. A request body size guard.
  4. Admin-route API-key authentication (constant-time compare).
  5. A lightweight prompt-injection / jailbreak heuristic filter applied to
     any free-text field before it is interpolated into an AI prompt.

None of this replaces a production WAF / API gateway, but it establishes a
defense-in-depth baseline appropriate for a hackathon-grade deployable
service. See docs/SECURITY.md for the full threat model and what is
explicitly out of scope.
"""
from __future__ import annotations

import hmac
import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# 1. Rate limiting
# ---------------------------------------------------------------------------
_request_log: Dict[str, Deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    # Respect a trusted proxy header if present (e.g. behind a load
    # balancer) but fall back to the direct peer address.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request) -> None:
    now = time.monotonic()
    key = _client_key(request)
    window = settings.rate_limit_window_seconds
    bucket = _request_log[key]

    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= settings.rate_limit_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
        )
    bucket.append(now)


# ---------------------------------------------------------------------------
# 2. Security headers middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
        )
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


# ---------------------------------------------------------------------------
# 3. Request body size guard
# ---------------------------------------------------------------------------
class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return _json_error(413, "Request body too large.")
        return await call_next(request)


def _json_error(status_code: int, message: str):
    from starlette.responses import JSONResponse
    return JSONResponse(status_code=status_code, content={"detail": message})


# ---------------------------------------------------------------------------
# 4. Admin auth
# ---------------------------------------------------------------------------
def require_admin_key(request: Request) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin routes are disabled on this deployment.")
    supplied = request.headers.get("x-admin-key", "")
    if not hmac.compare_digest(supplied, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key.")


# ---------------------------------------------------------------------------
# 5. Prompt-injection heuristic filter
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|previous|the) instructions", re.I),
    re.compile(r"you are now (in )?(dan|developer mode|jailbreak)", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"reveal (your|the) (prompt|instructions|api key)", re.I),
    re.compile(r"<\s*script", re.I),
]


def sanitize_user_text(text: str) -> str:
    """Strip obvious prompt-injection / XSS payloads before templating.

    This is a heuristic, defense-in-depth layer — not a substitute for
    treating the model's own output as untrusted on the way back out
    (the frontend already escapes all rendered text for that reason).
    """
    cleaned = text
    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub("[removed]", cleaned)
    # Collapse excessive whitespace/newlines used to bury instructions.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
