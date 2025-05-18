import logging
import sys
from time import sleep, time
from typing import Dict, Callable, Any


class RateLimitMixin:
    """Mixin class for handling API rate limits."""
    
    _endpoint_retry_counts: Dict[str, int] = {}
    
    def handle_rate_limit(self, response, method: str, endpoint: str, request_func: Callable, **kwargs) -> dict:
        """Handle rate limit exceeded response by waiting and retrying."""
        # https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api#about-secondary-rate-limits
        if (
            response.status_code == 403
            and "secondary rate limit" in response.text.lower()
        ):
            return self._handle_secondary_rate_limit(
                response, method, endpoint, request_func, **kwargs
            )

        # Handle primary rate limit
        return self._handle_primary_rate_limit(response, method, endpoint, request_func, **kwargs)

    def _handle_primary_rate_limit(self, response, method: str, endpoint: str, request_func: Callable, **kwargs) -> dict:
        """Handle GitHub's primary rate limit by waiting until the reset time."""
        reset_time = int(response.headers.get("x-ratelimit-reset", 0))
        remaining = int(response.headers.get("x-ratelimit-remaining", 0))
        limit = int(response.headers.get("x-ratelimit-limit", 60))

        if remaining == 0 and reset_time > 0:
            current_time = time()
            wait_time = reset_time - current_time + 1  # Add 1 second buffer

            if wait_time > 0:
                logging.warning(
                    f"GitHub API rate limit exceeded ({limit} requests). "
                    f"Waiting for {wait_time:.1f} seconds until reset."
                )
                sleep(wait_time)

                return request_func(method, endpoint, **kwargs)

        # If we can't determine when to retry or something else is wrong
        response.raise_for_status()

    def _handle_secondary_rate_limit(
        self, response, method: str, endpoint: str, request_func: Callable, **kwargs
    ) -> dict:
        """Handle GitHub's secondary rate limit with exponential backoff."""
        # Start with a base wait time (e.g., 5 seconds)
        wait_time = 5

        # Get the current retry count for this endpoint
        retry_count = self._endpoint_retry_counts.get(endpoint, 0)

        # Implement exponential backoff with a maximum wait time
        if retry_count > 0:
            # Exponential backoff: wait_time = base_time * 2^retry_count
            wait_time = min(wait_time * (2**retry_count), 60)  # Max 60 seconds

        print(
            f"🚨 GitHub secondary rate limit hit for {endpoint}. "
            f"Waiting for {wait_time} seconds before retry #{retry_count + 1}."
        )
        sleep(wait_time)

        # Update retry count and try again
        self._endpoint_retry_counts[endpoint] = retry_count + 1

        if retry_count < 5:  # Maximum 5 retries
            return request_func(method, endpoint, **kwargs)
        else:
            print("🔥 Maximum retry attempts reached for secondary rate limit")
            print("  Stopping CIFTT due to persistent rate limiting")
            sys.exit(1)  # Exit the program with error code 1
            
    def update_rate_limits(self, headers):
        """Update rate limit information from response headers."""
        try:
            remaining = int(headers.get("x-ratelimit-remaining", 0))
            limit = int(headers.get("x-ratelimit-limit", 0))
            reset_time = int(headers.get("x-ratelimit-reset", 0))

            if limit > 0:
                # Only log when we're getting close to the limit
                if remaining < limit * 0.1:  # Less than 10% remaining
                    current_time = time()
                    reset_in = max(0, reset_time - current_time)
                    logging.warning(
                        f"GitHub API rate limit warning: {remaining}/{limit} "
                        f"requests remaining. Resets in {reset_in:.1f} seconds."
                    )
        except (ValueError, TypeError):
            logging.warning("Couldn't parse the rate limit headers!")
    
    def reset_retry_count(self, endpoint: str):
        """Reset the retry count for a specific endpoint."""
        if endpoint in self._endpoint_retry_counts:
            self._endpoint_retry_counts[endpoint] = 0
