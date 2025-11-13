"""Retry logic with exponential backoff for HTTP requests."""
import asyncio
from typing import Optional, Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import httpx
from src.utils.config import settings
from src.utils.logger import log


# Define retry decorator for HTTP requests
def create_retry_decorator():
    """Create a retry decorator with configured settings."""
    return retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(
            multiplier=settings.retry_delay,
            min=settings.retry_delay,
            max=30
        ),
        retry=retry_if_exception_type((
            httpx.HTTPError,
            httpx.TimeoutException,
            httpx.ConnectError,
            asyncio.TimeoutError,
        )),
        before_sleep=before_sleep_log(log, "WARNING"),
        after=after_log(log, "INFO"),
    )


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    method: str = "GET",
    **kwargs
) -> Optional[httpx.Response]:
    """
    Fetch URL with automatic retry logic.

    Args:
        client: HTTP client
        url: URL to fetch
        method: HTTP method (default: GET)
        **kwargs: Additional arguments for the request

    Returns:
        Response object or None if all retries failed
    """
    @create_retry_decorator()
    async def _fetch():
        log.debug(f"Fetching {url}")
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    try:
        return await _fetch()
    except Exception as e:
        log.error(f"Failed to fetch {url} after {settings.max_retries} retries: {e}")
        return None


class RetryableHTTPClient:
    """HTTP client with built-in retry logic."""

    def __init__(self, timeout: int = None, max_concurrent: int = None):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent requests
        """
        self.timeout = timeout or settings.request_timeout
        self.max_concurrent = max_concurrent or settings.max_concurrent_requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=self.max_concurrent,
                max_connections=self.max_concurrent * 2
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def get(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """
        Perform GET request with retry logic and concurrency control.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for the request

        Returns:
            Response object or None if request failed
        """
        async with self.semaphore:
            return await fetch_with_retry(self.client, url, "GET", **kwargs)

    async def fetch_multiple(
        self,
        urls: list,
        callback: Optional[Callable] = None
    ) -> list:
        """
        Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch
            callback: Optional callback function to process each response

        Returns:
            List of responses or callback results
        """
        tasks = []
        for url in urls:
            task = self._fetch_and_process(url, callback)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                log.error(f"Task failed with exception: {result}")
            elif result is not None:
                valid_results.append(result)

        return valid_results

    async def _fetch_and_process(
        self,
        url: str,
        callback: Optional[Callable] = None
    ) -> Any:
        """
        Fetch URL and optionally process with callback.

        Args:
            url: URL to fetch
            callback: Optional callback function

        Returns:
            Response or callback result
        """
        response = await self.get(url)
        if response and callback:
            if asyncio.iscoroutinefunction(callback):
                return await callback(response)
            else:
                return callback(response)
        return response
