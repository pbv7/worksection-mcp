"""Tests for rate limiter."""

import time

import pytest

from worksection_mcp.client.rate_limiter import AdaptiveRateLimiter, RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality."""

    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test that rate limiter enforces 1 req/sec."""
        limiter = RateLimiter(requests_per_second=1.0)

        start = time.monotonic()

        # Make 3 requests
        for _ in range(3):
            await limiter.acquire()

        elapsed = time.monotonic() - start

        # Should take at least 2 seconds (3 requests with 1 sec interval)
        assert elapsed >= 1.9  # Small margin for timing

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test rate limiter as context manager."""
        limiter = RateLimiter(requests_per_second=10.0)  # Faster for testing

        async with limiter:
            pass  # Should not raise

    @pytest.mark.asyncio
    async def test_high_rate(self):
        """Test with higher rate limit."""
        limiter = RateLimiter(requests_per_second=100.0)

        start = time.monotonic()

        for _ in range(10):
            await limiter.acquire()

        elapsed = time.monotonic() - start

        # Should be fast with 100 req/sec
        assert elapsed < 0.5


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiter functionality."""

    @pytest.mark.asyncio
    async def test_backoff_on_rate_limit(self):
        """Test that rate limiter backs off on 429."""
        limiter = AdaptiveRateLimiter(requests_per_second=1.0)

        initial_interval = limiter.min_interval

        # Record rate limit
        limiter.record_rate_limit()

        # Interval should have increased
        assert limiter.min_interval > initial_interval

    @pytest.mark.asyncio
    async def test_recovery_on_success(self):
        """Test that rate limiter recovers after sustained success."""
        limiter = AdaptiveRateLimiter(
            requests_per_second=1.0,
            backoff_factor=2.0,
        )

        # First, trigger backoff
        limiter.record_rate_limit()
        backed_off_interval = limiter.min_interval

        # Record many successes (more than recovery threshold)
        for _ in range(15):
            limiter.record_success()

        # Interval should have recovered
        assert limiter.min_interval < backed_off_interval

    @pytest.mark.asyncio
    async def test_max_backoff(self):
        """Test that backoff doesn't exceed max."""
        limiter = AdaptiveRateLimiter(
            requests_per_second=1.0,
            backoff_factor=2.0,
            max_backoff=10.0,
        )

        # Record many rate limits
        for _ in range(10):
            limiter.record_rate_limit()

        # Interval should not exceed max_backoff
        assert limiter.min_interval <= 10.0

    @pytest.mark.asyncio
    async def test_retry_after_header(self):
        """Test handling of Retry-After header."""
        limiter = AdaptiveRateLimiter(requests_per_second=1.0)

        # Record rate limit with retry-after
        limiter.record_rate_limit(retry_after=5.0)

        # Interval should be at least 5 seconds
        assert limiter.min_interval >= 5.0
