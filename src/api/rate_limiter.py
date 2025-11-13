"""Rate limiting for API endpoints."""
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.utils.config import settings
from src.utils.logger import log


def get_api_key(request: Request) -> str:
    """
    Extract API key from request for rate limiting.

    Args:
        request: FastAPI request object

    Returns:
        API key or IP address as identifier
    """
    api_key = request.headers.get("X-API-Key")

    if api_key:
        return f"api_key:{api_key}"

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(
    key_func=get_api_key,
    default_limits=[f"{settings.rate_limit_per_hour}/hour"],
    storage_uri="memory://",
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors.

    Args:
        request: FastAPI request object
        exc: Rate limit exception

    Returns:
        HTTP 429 error response
    """
    log.warning(
        f"Rate limit exceeded for {get_api_key(request)}: {exc.detail}"
    )

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"You have exceeded the rate limit of {settings.rate_limit_per_hour} requests per hour",
            "retry_after": "3600 seconds"
        }
    )
