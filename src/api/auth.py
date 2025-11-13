"""API key authentication for FastAPI."""
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from src.utils.config import settings
from src.utils.logger import log


# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    Args:
        api_key: API key from header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        log.warning("Request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-API-Key header.",
        )

    # Check if API key is valid
    valid_keys = settings.api_keys_list

    if api_key not in valid_keys:
        log.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    log.debug(f"API key validated: {api_key[:10]}...")
    return api_key


class APIKeyDependency:
    """Dependency for API key authentication."""

    def __init__(self, required: bool = True):
        """
        Initialize API key dependency.

        Args:
            required: Whether API key is required (for optional auth)
        """
        self.required = required

    async def __call__(self, api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
        """Validate API key."""
        if not self.required and not api_key:
            return None

        return await verify_api_key(api_key)
