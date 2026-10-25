"""HTTP controls, bounded login throttling and metadata-only audit events."""
import asyncio
from collections import deque
import json
import logging
import threading
import time
from uuid import uuid4
from starlette.responses import JSONResponse

logger = logging.getLogger("tourshield.audit")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
HEADERS = {
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    "referrer-policy": "no-referrer",
    "permissions-policy": "geolocation=(), camera=(), microphone=()",
    "cache-control": "no-store",
    "pragma": "no-cache",
}
DOCS_CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


class LoginLimiter:
    """Single-process sliding window, keyed by actual network peer, not XFF."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.buckets = {}

    def reset(self):
        with self.lock:
            self.buckets.clear()

    def check(self, key):
        now = self.clock()
        with self.lock:
            expired = [k for k, v in self.buckets.items() if not v or v[-1] <= now - 60]
            for item in expired:
                del self.buckets[item]
            if key not in self.buckets and len(self.buckets) >= 10000:
                return False, 60
            bucket = self.buckets.setdefault(key, deque())
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= 5:
                return False, max(1, int(60 - (now - bucket[0])) + 1)
            bucket.append(now)
            return True, 0


login_limiter = LoginLimiter()


class WebSecurity:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid4())
        status = 500
        started = False

        async def secure_send(message):
            nonlocal status, started
            if message["type"] == "http.response.start":
                started = True
                status = message["status"]
                names = {k.encode() for k in HEADERS}
                headers = [(k,v) for k,v in message.get("headers", []) if k.lower() not in names]
                values = dict(HEADERS)
                if scope["path"] == "/docs":
                    values["content-security-policy"] = DOCS_CSP
                headers += [(k.encode(),v.encode()) for k,v in values.items()]
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        async def reject(code, detail, extra=None):
            await JSONResponse({"detail": detail}, status_code=code, headers=extra)(scope, receive, secure_send)

        try:
            if scope["method"] == "POST" and scope["path"] == "/auth/token":
                peer = (scope.get("client") or ("unknown", 0))[0]
                allowed, retry = login_limiter.check(peer)
                if not allowed:
                    return await reject(429, "Limite de autenticação excedido", {"Retry-After": str(retry)})
            chunks = []
            length = 0
            if scope["method"] in {"POST", "PUT", "PATCH"}:
                try:
                    async with asyncio.timeout(10):
                        while True:
                            message = await receive()
                            if message["type"] == "http.disconnect":
                                return
                            chunk = message.get("body", b"")
                            length += len(chunk)
                            if length > 16384:
                                return await reject(413, "Corpo excede 16 KiB")
                            chunks.append(chunk)
                            if not message.get("more_body", False):
                                break
                except TimeoutError:
                    return await reject(408, "Tempo de leitura excedido")
                delivered = False

                async def replay():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
                    return await receive()
                await self.app(scope, replay, secure_send)
            else:
                await self.app(scope, receive, secure_send)
        except Exception:
            if started:
                raise
            await reject(500, "Erro interno")
        finally:
            route = getattr(scope.get("route"), "path", "unmatched")
            logger.info(json.dumps({"event": "http_response", "request_id": request_id,
                                    "method": scope["method"], "route": route, "status": status}))
