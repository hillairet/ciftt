import logging
from pathlib import Path
from typing import Dict, Literal
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

from ciftt.github.client_utils import _extract_project_fields
from ciftt.github.data import (
    IssueNodeInfo,
    NewIssue,
    ProjectFieldUpdateResult,
    ProjectFieldValue,
    ProjectInfo,
    ProjectItemResult,
    UpdatedIssue,
)
from ciftt.github.rate_limit import RateLimitMixin


# Load GraphQL queries
def _load_graphql_query(filename: str) -> str:
    """Load a GraphQL query from the queries directory."""
    return Path(__file__).parent.joinpath("queries", filename).read_text()


PROJECT_FIELDS_QUERY = _load_graphql_query("project_fields.graphql")
GET_PROJECT_ITEM_INFO_QUERY = _load_graphql_query("get_project_item_info.graphql")
UPDATE_PROJECT_FIELD_MUTATION = _load_graphql_query("update_project_field.graphql")
VALIDATE_PROJECT_QUERY = _load_graphql_query("validate_project.graphql")
GET_ISSUE_NODE_ID_QUERY = _load_graphql_query("get_issue_node_id.graphql")
ADD_PROJECT_ITEM_MUTATION = _load_graphql_query("add_project_item.graphql")


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

    def _request(
        self, method: str, endpoint: str, return_headers: bool = False, **kwargs
    ) -> dict:
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
                    response,
                    method,
                    endpoint,
                    self._request,
                    return_headers=return_headers,
                    **kwargs,
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

                result[issue_number] = _extract_project_fields(issue, field_names)

            except Exception as e:
                logging.warning(
                    f"Failed to fetch project fields for issue #{issue_number}: {e}"
                )
                continue

        return result

    def get_project_item_info(self, owner: str, repo: str, issue_number: int) -> dict:
        """
        Get project item ID and field information for an issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Dictionary containing project item info and field definitions
        """
        variables = {"owner": owner, "repo": repo, "issueNumber": issue_number}

        response = self.execute_graphql(GET_PROJECT_ITEM_INFO_QUERY, variables)

        if "data" not in response or "repository" not in response["data"]:
            raise ValueError(f"Failed to get project info for issue #{issue_number}")

        issue = response["data"]["repository"]["issue"]
        if not issue:
            raise ValueError(f"Issue #{issue_number} not found")

        return issue

    def update_project_field(
        self, project_id: str, item_id: str, field_id: str, value: ProjectFieldValue
    ) -> dict:
        """
        Update a project field value for a specific project item.

        Args:
            project_id: GitHub project ID
            item_id: Project item ID
            field_id: Field ID to update
            value: ProjectFieldValue Pydantic model with the field value

        Returns:
            Response from the GraphQL mutation
        """
        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": value.model_dump(exclude_unset=True),
        }

        response = self.execute_graphql(UPDATE_PROJECT_FIELD_MUTATION, variables)

        if "errors" in response:
            error_msg = ", ".join([error["message"] for error in response["errors"]])
            raise ValueError(f"Failed to update project field: {error_msg}")

        return response

    def update_issue_project_fields(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        project_fields: Dict[str, str],
        project_number: str,
    ) -> ProjectFieldUpdateResult:
        """
        Update project fields for a specific issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            project_fields: Dictionary of field names to values
            project_number: Project number to update fields for

        Returns:
            ProjectFieldUpdateResult with update results for each field
        """
        from ciftt.github.client_utils import _extract_project_info_for_updates

        if not project_fields:
            return ProjectFieldUpdateResult()

        # Get project information for this issue
        issue_data = self.get_project_item_info(owner, repo, issue_number)
        projects_info = _extract_project_info_for_updates(issue_data)

        if not projects_info:
            raise ValueError(f"Issue #{issue_number} is not in any GitHub Projects")

        updated_fields = {}
        errors = {}

        # Find and validate the target project
        target_project_info = self._find_target_project(
            projects_info, project_number, issue_number
        )

        project_id = target_project_info["project_id"]
        item_id = target_project_info["item_id"]
        available_fields = target_project_info["fields"]

        # Update all project fields
        self._update_project_fields(
            project_fields,
            available_fields,
            project_id,
            item_id,
            project_number,
            updated_fields,
            errors,
        )

        return ProjectFieldUpdateResult(updated_fields=updated_fields, errors=errors)

    def _update_project_fields(
        self,
        project_fields: Dict[str, str],
        available_fields: dict,
        project_id: str,
        item_id: str,
        project_number: str,
        updated_fields: dict,
        errors: dict,
    ) -> None:
        """
        Update all project fields for an issue.

        Args:
            project_fields: Dictionary of field names to values to update
            available_fields: Available fields in the project
            project_id: GitHub project ID
            item_id: Project item ID
            project_number: Project number for error messages
            updated_fields: Dictionary to store successfully updated fields
            errors: Dictionary to store field update errors
        """
        from ciftt.github.client_utils import _format_project_field_value

        for field_name, field_value in project_fields.items():
            if field_name not in available_fields:
                errors[field_name] = (
                    f"Field '{field_name}' not found in project #{project_number}"
                )
                continue

            field_info = available_fields[field_name]
            field_id = field_info["id"]
            field_type = field_info["dataType"]
            field_options = field_info.get("options", [])
            field_iterations = field_info.get("iterations", [])

            try:
                # Format the value for GraphQL API
                formatted_value = _format_project_field_value(
                    field_type, field_value, field_options, field_iterations
                )

                if formatted_value is None:
                    continue  # Skip empty values

                # Update the field
                self.update_project_field(
                    project_id, item_id, field_id, formatted_value
                )
                updated_fields[field_name] = field_value

            except Exception as e:
                errors[field_name] = str(e)

    def _find_target_project(
        self, projects_info: dict, project_number: str, issue_number: int
    ) -> dict:
        """
        Find and validate the target project from available projects.

        Args:
            projects_info: Dictionary of available projects
            project_number: Target project number to find
            issue_number: Issue number for error messages

        Returns:
            Project info dictionary for the target project

        Raises:
            ValueError: If target project is not found
        """
        for _project_title, project_info in projects_info.items():
            if str(project_info.get("project_number")) == str(project_number):
                return project_info

        # Target project not found - build helpful error message
        available_numbers = [
            str(info.get("project_number", "unknown"))
            for info in projects_info.values()
        ]
        raise ValueError(
            f"Issue #{issue_number} is not in project #{project_number}. "
            f"Available projects: {', '.join(available_numbers)}"
        )

    def validate_project_exists(self, owner: str, project_number: str) -> ProjectInfo:
        """
        Validate that a GitHub project exists and is accessible.

        Args:
            owner: Project owner (user or organization)
            project_number: Project number (as string)

        Returns:
            ProjectInfo model with project information if found

        Raises:
            ValueError: If project is not found or not accessible
        """
        variables = {"owner": owner, "number": int(project_number)}

        response = self.execute_graphql(VALIDATE_PROJECT_QUERY, variables)

        # GraphQL may return errors for user/org fields that don't exist, but we want to check both
        data = response.get("data", {})

        # Check if we have any data at all (if completely failed, data would be None/empty)
        if not data and "errors" in response:
            error_msg = ", ".join([error["message"] for error in response["errors"]])
            raise ValueError(f"Failed to validate project: {error_msg}")

        # Check if project exists under user or organization
        project_info = None
        project_type = None

        if data.get("organization") and data["organization"].get("projectV2"):
            project_info = data["organization"]["projectV2"]
            project_type = "organization"
        elif data.get("user") and data["user"].get("projectV2"):
            project_info = data["user"]["projectV2"]
            project_type = "user"

        if not project_info:
            raise ValueError(
                f"Project {owner}/{project_number} not found or not accessible. "
                f"Please check:\n"
                f"  - Project exists and number is correct\n"
                f"  - You have access to the project\n"
                f"  - Token has 'project' scope"
            )

        return ProjectInfo(
            id=project_info["id"],
            title=project_info["title"],
            number=project_info["number"],
            url=project_info["url"],
            owner=owner,
            type=project_type,
        )

    def get_project_field_definitions(
        self, owner: str, project_number: str
    ) -> Dict[str, Dict]:
        """
        Get project field definitions for validation.

        Args:
            owner: Project owner (user or organization)
            project_number: Project number (as string)

        Returns:
            Dictionary mapping field names to their definitions
        """
        # Use the same query as validate_project_exists to get project info
        variables = {"owner": owner, "number": int(project_number)}
        response = self.execute_graphql(VALIDATE_PROJECT_QUERY, variables)

        data = response.get("data", {})
        project_info = None

        if data.get("organization") and data["organization"].get("projectV2"):
            project_info = data["organization"]["projectV2"]
        elif data.get("user") and data["user"].get("projectV2"):
            project_info = data["user"]["projectV2"]

        if not project_info:
            raise ValueError(f"Project {owner}/{project_number} not found")

        # Extract field definitions
        field_definitions = {}
        fields = project_info.get("fields", {}).get("nodes", [])

        for field in fields:
            field_name = field.get("name")
            if field_name:
                field_def = {
                    "id": field.get("id"),
                    "dataType": field.get("dataType"),
                    "options": field.get("options", []),
                }

                # Handle iteration fields
                if field.get("configuration") and field["configuration"].get(
                    "iterations"
                ):
                    field_def["iterations"] = field["configuration"]["iterations"]

                field_definitions[field_name] = field_def

        return field_definitions

    def get_issue_node_id(
        self, owner: str, repo: str, issue_number: int
    ) -> IssueNodeInfo:
        """
        Get the node ID and basic information for an issue.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            IssueNodeInfo model with issue information

        Raises:
            ValueError: If issue is not found or not accessible
        """
        variables = {"owner": owner, "repo": repo, "issueNumber": issue_number}

        response = self.execute_graphql(GET_ISSUE_NODE_ID_QUERY, variables)

        if "errors" in response:
            error_msg = ", ".join([error["message"] for error in response["errors"]])
            raise ValueError(f"Failed to get issue info: {error_msg}")

        data = response.get("data", {})
        if not data or not data.get("repository") or not data["repository"].get("issue"):
            raise ValueError(
                f"Issue {owner}/{repo}#{issue_number} not found or not accessible"
            )

        issue_data = data["repository"]["issue"]
        return IssueNodeInfo(
            id=issue_data["id"],
            number=issue_data["number"],
            title=issue_data["title"],
            url=issue_data["url"],
        )

    def add_issue_to_project(
        self, project_id: str, issue_id: str, issue_number: int, issue_url: str
    ) -> ProjectItemResult:
        """
        Add an issue to a GitHub Project v2 board.

        Args:
            project_id: Project node ID (starts with PVT_)
            issue_id: Issue node ID
            issue_number: Issue number (for result tracking)
            issue_url: Issue URL (for result tracking)

        Returns:
            ProjectItemResult model with the result

        Raises:
            ValueError: If the operation fails
        """
        variables = {"projectId": project_id, "contentId": issue_id}

        response = self.execute_graphql(ADD_PROJECT_ITEM_MUTATION, variables)

        if "errors" in response:
            error_msg = ", ".join([error["message"] for error in response["errors"]])
            raise ValueError(f"Failed to add issue to project: {error_msg}")

        data = response.get("data", {})
        if not data or not data.get("addProjectV2ItemById"):
            raise ValueError("Failed to add issue to project: No data returned")

        item = data["addProjectV2ItemById"]["item"]
        return ProjectItemResult(
            item_id=item["id"], issue_number=issue_number, issue_url=issue_url
        )
