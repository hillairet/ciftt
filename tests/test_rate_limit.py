import logging
from time import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from ciftt.github.rate_limit import RateLimitMixin


class TestRateLimitClass(RateLimitMixin):
    pass


class TestHandleRateLimit:
    def test_primary_rate_limit_detected(self):
        rate_limiter = TestRateLimitClass()
        response = Mock()
        response.status_code = 403
        response.text = "Rate limit exceeded"
        response.headers = {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": str(int(time()) + 10),
        }

        request_func = Mock(return_value={"result": "success"})

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep:
            result = rate_limiter.handle_rate_limit(
                response, "GET", "/test", request_func
            )

            mock_sleep.assert_called_once()
            assert mock_sleep.call_args[0][0] > 0
            request_func.assert_called_once_with("GET", "/test")
            assert result == {"result": "success"}

    def test_secondary_rate_limit_detected(self):
        rate_limiter = TestRateLimitClass()
        response = Mock()
        response.status_code = 403
        response.text = "You have exceeded a secondary rate limit"

        request_func = Mock(return_value={"result": "success"})

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep:
            result = rate_limiter.handle_rate_limit(
                response, "GET", "/test", request_func
            )

            mock_sleep.assert_called_once_with(5)
            request_func.assert_called_once_with("GET", "/test")
            assert result == {"result": "success"}


class TestHandlePrimaryRateLimit:
    def test_wait_until_reset_time(self):
        rate_limiter = TestRateLimitClass()
        current_time = time()
        reset_time = int(current_time + 30)

        response = Mock()
        response.headers = {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": str(reset_time),
        }

        request_func = Mock(return_value={"data": "test"})

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep, patch(
            "ciftt.github.rate_limit.time", return_value=current_time
        ):
            result = rate_limiter._handle_primary_rate_limit(
                response, "GET", "/repos/test", request_func
            )

            expected_wait = reset_time - current_time + 1
            mock_sleep.assert_called_once_with(expected_wait)
            request_func.assert_called_once_with("GET", "/repos/test")
            assert result == {"data": "test"}

    def test_no_wait_when_remaining_not_zero(self):
        rate_limiter = TestRateLimitClass()

        response = Mock()
        response.headers = {
            "x-ratelimit-remaining": "100",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": str(int(time()) + 30),
        }
        response.raise_for_status = Mock(side_effect=Exception("No rate limit"))

        request_func = Mock()

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep:
            with pytest.raises(Exception, match="No rate limit"):
                rate_limiter._handle_primary_rate_limit(
                    response, "GET", "/repos/test", request_func
                )

            mock_sleep.assert_not_called()
            request_func.assert_not_called()

    def test_raise_for_status_when_no_reset_time(self):
        rate_limiter = TestRateLimitClass()

        response = Mock()
        response.headers = {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": "0",
        }
        response.raise_for_status = Mock(side_effect=Exception("HTTP Error"))

        request_func = Mock()

        with pytest.raises(Exception, match="HTTP Error"):
            rate_limiter._handle_primary_rate_limit(
                response, "GET", "/repos/test", request_func
            )

    def test_handle_with_kwargs(self):
        rate_limiter = TestRateLimitClass()
        current_time = time()
        reset_time = int(current_time + 10)

        response = Mock()
        response.headers = {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-limit": "60",
            "x-ratelimit-reset": str(reset_time),
        }

        request_func = Mock(return_value={"result": "ok"})

        with patch("ciftt.github.rate_limit.sleep"), patch(
            "ciftt.github.rate_limit.time", return_value=current_time
        ):
            result = rate_limiter._handle_primary_rate_limit(
                response,
                "POST",
                "/repos/test",
                request_func,
                data={"key": "value"},
                headers={"Auth": "token"},
            )

            request_func.assert_called_once_with(
                "POST", "/repos/test", data={"key": "value"}, headers={"Auth": "token"}
            )
            assert result == {"result": "ok"}


class TestHandleSecondaryRateLimit:
    def test_first_retry_waits_5_seconds(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {}

        response = Mock()
        request_func = Mock(return_value={"data": "ok"})

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep:
            result = rate_limiter._handle_secondary_rate_limit(
                response, "GET", "/test", request_func
            )

            mock_sleep.assert_called_once_with(5)
            assert rate_limiter._endpoint_retry_counts["/test"] == 1
            assert result == {"data": "ok"}

    def test_exponential_backoff(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {"/test": 2}

        response = Mock()
        request_func = Mock(return_value={"data": "ok"})

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep:
            result = rate_limiter._handle_secondary_rate_limit(
                response, "GET", "/test", request_func
            )

            expected_wait = 5 * (2**2)
            mock_sleep.assert_called_once_with(expected_wait)
            assert rate_limiter._endpoint_retry_counts["/test"] == 3
            assert result == {"data": "ok"}

    def test_max_wait_time_capped_at_60_seconds(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {"/test": 4}

        response = Mock()
        request_func = Mock(return_value={"data": "ok"})

        with patch("ciftt.github.rate_limit.sleep") as mock_sleep:
            result = rate_limiter._handle_secondary_rate_limit(
                response, "GET", "/test", request_func
            )

            expected_wait = min(5 * (2**4), 60)
            mock_sleep.assert_called_once_with(expected_wait)
            assert rate_limiter._endpoint_retry_counts["/test"] == 5
            assert result == {"data": "ok"}

    def test_exits_after_max_retries(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {"/test": 5}

        response = Mock()
        request_func = Mock()

        with patch("ciftt.github.rate_limit.sleep"), patch("sys.exit") as mock_exit:
            rate_limiter._handle_secondary_rate_limit(
                response, "GET", "/test", request_func
            )

            mock_exit.assert_called_once_with(1)
            request_func.assert_not_called()

    def test_passes_kwargs_to_request_func(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {}

        response = Mock()
        request_func = Mock(return_value={"result": "success"})

        with patch("ciftt.github.rate_limit.sleep"):
            result = rate_limiter._handle_secondary_rate_limit(
                response,
                "POST",
                "/test",
                request_func,
                json={"data": "test"},
                headers={"Auth": "Bearer token"},
            )

            request_func.assert_called_once_with(
                "POST", "/test", json={"data": "test"}, headers={"Auth": "Bearer token"}
            )
            assert result == {"result": "success"}


class TestUpdateRateLimits:
    def test_log_warning_when_limit_below_10_percent(self, caplog):
        rate_limiter = TestRateLimitClass()
        current_time = time()
        reset_time = int(current_time + 3600)

        headers = {
            "x-ratelimit-remaining": "40",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": str(reset_time),
        }

        with caplog.at_level(logging.WARNING), patch(
            "ciftt.github.rate_limit.time", return_value=current_time
        ):
            rate_limiter.update_rate_limits(headers)

            assert "40/5000 requests remaining" in caplog.text
            assert "Resets in" in caplog.text

    def test_no_log_when_limit_above_10_percent(self, caplog):
        rate_limiter = TestRateLimitClass()
        current_time = time()
        reset_time = int(current_time + 3600)

        headers = {
            "x-ratelimit-remaining": "4500",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": str(reset_time),
        }

        with caplog.at_level(logging.WARNING):
            rate_limiter.update_rate_limits(headers)

            assert "requests remaining" not in caplog.text

    def test_handle_missing_headers(self, caplog):
        rate_limiter = TestRateLimitClass()
        headers = {}

        with caplog.at_level(logging.WARNING):
            rate_limiter.update_rate_limits(headers)

            assert caplog.text == ""

    def test_handle_invalid_header_values(self, caplog):
        rate_limiter = TestRateLimitClass()
        headers = {
            "x-ratelimit-remaining": "invalid",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": "not-a-number",
        }

        with caplog.at_level(logging.WARNING):
            rate_limiter.update_rate_limits(headers)

            assert "Couldn't parse the rate limit headers" in caplog.text

    def test_calculate_reset_time_correctly(self, caplog):
        rate_limiter = TestRateLimitClass()
        current_time = time()
        reset_time = int(current_time + 120)

        headers = {
            "x-ratelimit-remaining": "100",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-reset": str(reset_time),
        }

        with caplog.at_level(logging.WARNING), patch(
            "ciftt.github.rate_limit.time", return_value=current_time
        ):
            rate_limiter.update_rate_limits(headers)

            assert "100/5000" in caplog.text
            assert "Resets in 1" in caplog.text


class TestResetRetryCount:
    def test_reset_existing_endpoint(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {"/test": 5, "/other": 3}

        rate_limiter.reset_retry_count("/test")

        assert rate_limiter._endpoint_retry_counts["/test"] == 0
        assert rate_limiter._endpoint_retry_counts["/other"] == 3

    def test_reset_nonexistent_endpoint(self):
        rate_limiter = TestRateLimitClass()
        rate_limiter._endpoint_retry_counts = {"/other": 3}

        rate_limiter.reset_retry_count("/test")

        assert "/test" not in rate_limiter._endpoint_retry_counts
        assert rate_limiter._endpoint_retry_counts["/other"] == 3
