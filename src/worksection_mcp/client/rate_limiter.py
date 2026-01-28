"""Rate limiter for API requests."""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter.

    Worksection API allows 1 request per second.
    This implementation ensures we don't exceed that limit.
    """

    def __init__(self, requests_per_second: float = 1.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time: float = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request.

        This will wait if necessary to maintain the rate limit.
        """
        async with self._lock:
            now = time.monotonic()
            time_since_last = now - self._last_request_time
            wait_time = self.min_interval - time_since_last

            if wait_time > 0:
                logger.debug(f"Rate limit: waiting {wait_time:.3f}s")
                await asyncio.sleep(wait_time)

            self._last_request_time = time.monotonic()

    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts based on server responses.

    If we receive 429 (Too Many Requests), we back off.
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        backoff_factor: float = 2.0,
        max_backoff: float = 60.0,
    ):
        """Initialize adaptive rate limiter.

        Args:
            requests_per_second: Initial maximum requests per second
            backoff_factor: Multiplier for backoff on rate limit errors
            max_backoff: Maximum backoff time in seconds
        """
        super().__init__(requests_per_second)
        self.base_interval = self.min_interval
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self._consecutive_successes = 0
        self._recovery_threshold = 10

    def record_success(self) -> None:
        """Record a successful request."""
        self._consecutive_successes += 1
        # Gradually recover rate after sustained success
        if self._consecutive_successes >= self._recovery_threshold:
            if self.min_interval > self.base_interval:
                self.min_interval = max(
                    self.base_interval,
                    self.min_interval / self.backoff_factor,
                )
                logger.info(f"Rate limit recovered to {1/self.min_interval:.2f} req/s")
                self._consecutive_successes = 0

    def record_rate_limit(self, retry_after: float | None = None) -> None:
        """Record a rate limit response.

        Args:
            retry_after: Retry-After header value in seconds
        """
        self._consecutive_successes = 0

        if retry_after:
            self.min_interval = max(self.min_interval, retry_after)
        else:
            self.min_interval = min(
                self.max_backoff,
                self.min_interval * self.backoff_factor,
            )

        logger.warning(
            f"Rate limited, backing off to {1/self.min_interval:.2f} req/s"
        )
