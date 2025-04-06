import logging
import sys
from collections import deque
from time import sleep, time
from typing import Any, Deque, Dict, Optional
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
    
    def update_issue(self, owner: str, repo: str, issue_number: int, issue_update: UpdatedIssue) -> dict:
        """Update an existing issue in the specified repository."""
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}"
        
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
            method=method,
            url=urljoin(self.url, endpoint),
            headers=headers,
            **kwargs
        )
        
        # Check for successful status code (2xx)
        if not 200 <= response.status_code < 300:
            logging.error(
                f"GitHub API {method} {endpoint} request failed: "
                f"Status: {response.status_code}\n{response.text}"
            )
            # Don't exit the program, raise an exception instead
            response.raise_for_status()
            
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
