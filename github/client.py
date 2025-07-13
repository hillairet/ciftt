import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

from github.client_utils import extract_project_fields
from github.data import NewIssue, UpdatedIssue
from github.rate_limit import RateLimitMixin

# Load GraphQL queries
PROJECT_FIELDS_QUERY = (
    Path(__file__).parent.joinpath("queries", "project_fields.graphql").read_text()
)


class GitHubClient(BaseModel, RateLimitMixin):
    api_key: str
    url: str = "https://api.github.com/"

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

    def get_all_issues(
        self, owner: str, repo: str, state: Literal["open", "closed", "all"] = "open"
    ) -> list:
        """Fetch all issues from a GitHub repository."""
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
        """Fetch specific issues from a GitHub repository by their numbers."""
        all_issues = []
        for issue_num in issue_numbers:
            try:
                endpoint = f"repos/{owner}/{repo}/issues/{issue_num}"
                issue = self._get_request(endpoint)
                all_issues.append(issue)
            except Exception as e:
                logging.warning(f"Failed to fetch issue #{issue_num}: {e}")

        return all_issues

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

    def _request(self, method: str, endpoint: str, return_headers: bool = False, **kwargs) -> dict:
        """Make a request to the GitHub API with rate limiting."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.api_key}",
        }

        response = requests.request(
            method=method, url=urljoin(self.url, endpoint), headers=headers, **kwargs
        )

        # Check for successful status code (2xx)
        if not 200 <= response.status_code < 300:
            # Handle rate limit exceeded (429)
            if response.status_code in [429, 403]:
                return self.handle_rate_limit(
                    response, method, endpoint, self._request, return_headers=return_headers, **kwargs
                )
            logging.error(
                f"GitHub API {method} {endpoint} request failed: "
                f"Status: {response.status_code}\n{response.text}"
            )
            # Don't exit the program, raise an exception instead
            response.raise_for_status()

        # Reset retry count for this endpoint on success
        self.reset_retry_count(endpoint)

        # Update rate limit info from headers
        self.update_rate_limits(response.headers)

        if return_headers:
            return response.json(), response.headers
        return response.json()

    def execute_graphql(self, query: str, variables: dict = None) -> dict:
        """Execute a GraphQL query against the GitHub API."""
        if variables is None:
            variables = {}

        endpoint = "graphql"
        data = {"query": query, "variables": variables}

        return self._post_request(endpoint, data)

    def get_project_fields_for_issues(
        self, owner: str, repo: str, issue_numbers: list, field_names: list
    ) -> dict:
        """
        Fetch project fields for specific issues using GraphQL.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_numbers: List of issue numbers
            field_names: List of project field names to fetch

        Returns:
            Dictionary mapping issue numbers to their project fields
        """
        result = {}

        # Fetch project fields for each issue individually
        for issue_number in issue_numbers:
            variables = {"owner": owner, "repo": repo, "issueNumber": issue_number}

            try:
                response = self.execute_graphql(PROJECT_FIELDS_QUERY, variables)

                # Process the response to extract the requested fields
                if "data" not in response or "repository" not in response["data"]:
                    continue

                issue = response["data"]["repository"]["issue"]
                if not issue:
                    continue

                result[issue_number] = extract_project_fields(issue, field_names)

            except Exception as e:
                logging.warning(
                    f"Failed to fetch project fields for issue #{issue_number}: {e}"
                )
                continue

        return result
