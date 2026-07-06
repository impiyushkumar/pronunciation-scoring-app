# -----------------------------------------------------------------------
# Rate limiting — IP-based, in-memory (no Redis needed for single instance)
# -----------------------------------------------------------------------

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.models import ErrorResponse
from app.config import settings

# Create limiter with IP-based key
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom 429 response — clean error, no stack traces."""
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error="rate_limited",
            message="Too many requests. Please wait a moment and try again.",
            detail=str(exc.detail),
        ).model_dump(),
    )
