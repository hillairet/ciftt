import logging
import sys
from collections import deque
from time import sleep, time
from typing import Any, Deque, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

from github.data import NewIssue, UpdatedIssue

ONE_MIN = 60


class GitHubClient(BaseModel):
    api_key: str
    url: str = "https://api.github.com/"
    _api_requests_counter: int = 0
    _api_calls: Deque = deque()
    _api_rate_limit_per_min: int = 100

    def create_issue(self, owner: str, repo: str, issue: NewIssue) -> dict:
        """Create a new issue in the specified repository."""
        endpoint = f"repos/{owner}/{repo}/issues"

        # Convert the NewIssue model to a dictionary for the API request
        data = issue.model_dump(exclude_none=True)

        return self._post_request(endpoint, data)

    def update_issue(self, owner: str, repo: str, issue_update: UpdatedIssue) -> dict:
        """Update an existing issue in the specified repository."""
        endpoint = f"repos/{owner}/{repo}/issues/{issue_update.issue_number}"

        # Convert the UpdatedIssue model to a dictionary for the API request
        # Exclude None values to only update specified fields
        data = issue_update.model_dump(exclude_none=True)

        return self._patch_request(endpoint, data)

    def _get_request(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request to the GitHub API."""
        if params is None:
            params = {}
        return self._request("GET", endpoint, params=params)

    def _post_request(self, endpoint: str, data: dict) -> dict:
        """Make a POST request to the GitHub API."""
        return self._request("POST", endpoint, json=data)

    def _patch_request(self, endpoint: str, data: dict) -> dict:
        """Make a PATCH request to the GitHub API."""
        return self._request("PATCH", endpoint, json=data)

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make a request to the GitHub API with rate limiting."""
        self._throttle_api_calls()

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.api_key}",
        }

        response = requests.request(
            method=method, url=urljoin(self.url, endpoint), headers=headers, **kwargs
        )

        # Check for successful status code (2xx)
        if not 200 <= response.status_code < 300:
            logging.error(
                f"GitHub API {method} {endpoint} request failed: "
                f"Status: {response.status_code}\n{response.text}"
            )
            # Handle rate limit exceeded (429)
            if response.status_code in [429, 403]:
                return self._handle_rate_limit(response, method, endpoint, **kwargs)
            # Don't exit the program, raise an exception instead
            response.raise_for_status()

        # Update rate limit info from headers
        self._update_rate_limits(response.headers)

        return response.json()

    def _throttle_api_calls(self):
        """Throttle API calls to stay within rate limits."""
        current_time = time()

        # Remove calls that are older than the 1-minute window
        while self._api_calls and (current_time - self._api_calls[0]) > ONE_MIN:
            self._api_calls.popleft()

        if len(self._api_calls) >= self._api_rate_limit_per_min:
            # If 100 calls have been made in the last 60 seconds,
            # sleep until it's safe to make a new call
            time_to_wait = ONE_MIN - (current_time - self._api_calls[0])
            logging.info(
                f"GitHub API rate limit reached. Sleeping for {time_to_wait:.2f} seconds."
            )
            sleep(time_to_wait)
            # Remove the oldest call after sleeping
            self._api_calls.popleft()

        # Add the current time to the deque
        self._api_calls.append(current_time)

    def _handle_rate_limit(self, response, method, endpoint, **kwargs) -> dict:
        """Handle rate limit exceeded response by waiting and retrying."""
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        limit = int(response.headers.get("X-RateLimit-Limit", 60))

        if remaining == 0 and reset_time > 0:
            current_time = time()
            wait_time = reset_time - current_time + 1  # Add 1 second buffer

            if wait_time > 0:
                logging.warning(
                    f"GitHub API rate limit exceeded ({limit} requests). "
                    f"Waiting for {wait_time:.1f} seconds until reset."
                )
                sleep(wait_time)

                # Retry the request after waiting
                return self._request(method, endpoint, **kwargs)

        # If we can't determine when to retry or something else is wrong
        response.raise_for_status()

    def _update_rate_limits(self, headers):
        """Update rate limit information from response headers."""
        try:
            remaining = int(headers.get("X-RateLimit-Remaining", 0))
            limit = int(headers.get("X-RateLimit-Limit", 0))
            reset_time = int(headers.get("X-RateLimit-Reset", 0))

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
            # If we can't parse the headers, just continue
            pass
            
    def get_all_issues(self, owner: str, repo: str, state: str = "open") -> list:
        """
        Fetch all issues from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            
        Returns:
            List of issue dictionaries
        """
        endpoint = f"repos/{owner}/{repo}/issues"
        params = {"state": state, "per_page": 100}
        
        all_issues = []
        page = 1
        
        while True:
            params["page"] = page
            issues = self._get_request(endpoint, params)
            
            if not issues:
                break
                
            all_issues.extend(issues)
            page += 1
            
            # If we got fewer issues than the page size, we've reached the end
            if len(issues) < 100:
                break
        
        return all_issues

    def get_issues_by_numbers(self, owner: str, repo: str, issue_numbers: list) -> list:
        """
        Fetch specific issues from a GitHub repository by their numbers.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_numbers: List of issue numbers to fetch
            
        Returns:
            List of issue dictionaries
        """
        all_issues = []
        for issue_num in issue_numbers:
            try:
                endpoint = f"repos/{owner}/{repo}/issues/{issue_num}"
                issue = self._get_request(endpoint)
                all_issues.append(issue)
            except Exception as e:
                logging.warning(f"Failed to fetch issue #{issue_num}: {e}")
        
        return all_issues
