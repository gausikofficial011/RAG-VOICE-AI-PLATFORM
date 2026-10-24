"""
Security Middleware & Rate Limiting
Enforces HTTP security headers, request ID propagation, and IP rate limiting.
"""

from typing import Dict, List
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = 120):
        self.rpm = requests_per_minute
        self.hits: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        if client_ip not in self.hits:
            self.hits[client_ip] = [now]
            return True

        # Keep timestamps within the 60s sliding window
        valid_hits = [t for t in self.hits[client_ip] if t > window_start]
        self.hits[client_ip] = valid_hits

        if len(valid_hits) < self.rpm:
            self.hits[client_ip].append(now)
            return True
        return False


rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        # Exempt health checks
        if request.url.path.startswith("/api/health"):
            return await call_next(request)

        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down and try again later.",
                    },
                },
            )
        return await call_next(request)
