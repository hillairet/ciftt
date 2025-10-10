import pytest

from github.data import NewIssue, UpdatedIssue


class TestBodyFieldDecoding:
    """Test that body field properly decodes escape sequences regardless of alias used."""

    def test_body_alias_with_newlines(self):
        """Test that 'body' alias properly decodes \\n to newlines."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'body': 'Line 1\\nLine 2\\nLine 3'
        })

        assert issue.body == 'Line 1\nLine 2\nLine 3'
        assert '\n' in issue.body
        assert '\\n' not in issue.body

    def test_lowercase_description_alias_with_newlines(self):
        """Test that 'description' alias properly decodes \\n to newlines."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'description': 'Line 1\\nLine 2\\nLine 3'
        })

        assert issue.body == 'Line 1\nLine 2\nLine 3'
        assert '\n' in issue.body
        assert '\\n' not in issue.body

    def test_capitalized_description_alias_with_newlines(self):
        """Test that 'Description' alias properly decodes \\n to newlines."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'Description': 'Line 1\\nLine 2\\nLine 3'
        })

        assert issue.body == 'Line 1\nLine 2\nLine 3'
        assert '\n' in issue.body
        assert '\\n' not in issue.body

    def test_body_with_tabs_and_returns(self):
        """Test that other escape sequences like \\t and \\r are also decoded."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'Description': 'Column1\\tColumn2\\r\\nLine 2'
        })

        assert '\t' in issue.body
        assert '\r' in issue.body
        assert '\n' in issue.body
        assert '\\t' not in issue.body
        assert '\\r' not in issue.body
        assert '\\n' not in issue.body

    def test_body_with_complex_markdown(self):
        """Test decoding with complex markdown content including code blocks."""
        markdown_content = '# Title\\n\\n```json\\n{\\n  "key": "value"\\n}\\n```'

        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'Description': markdown_content
        })

        expected = '# Title\n\n```json\n{\n  "key": "value"\n}\n```'
        assert issue.body == expected

    def test_body_without_escape_sequences(self):
        """Test that normal text without escape sequences works fine."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'Description': 'Just a simple description'
        })

        assert issue.body == 'Just a simple description'

    def test_body_none_value(self):
        """Test that None body value is handled correctly."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue'
        })

        assert issue.body is None

    def test_body_empty_string(self):
        """Test that empty string body value is handled correctly."""
        issue = NewIssue.model_validate({
            'Title': 'Test Issue',
            'Description': ''
        })

        assert issue.body == ''


class TestUpdatedIssueBodyDecoding:
    """Test that UpdatedIssue also properly decodes escape sequences in body field."""

    def test_updated_issue_body_decoding(self):
        """Test that UpdatedIssue body field also decodes escape sequences."""
        issue = UpdatedIssue.model_validate({
            'issue_number': 123,
            'Description': 'Updated content\\nwith newlines'
        })

        assert issue.body == 'Updated content\nwith newlines'
        assert '\n' in issue.body
        assert '\\n' not in issue.body

    def test_updated_issue_optional_body(self):
        """Test that UpdatedIssue works without body field."""
        issue = UpdatedIssue.model_validate({
            'issue_number': 123,
            'Title': 'Updated Title'
        })

        assert issue.body is None
        assert issue.title == 'Updated Title'


class TestNewIssueValidation:
    """Test NewIssue model validation."""

    def test_new_issue_requires_title(self):
        """Test that NewIssue requires a title."""
        with pytest.raises(Exception):  # Pydantic validation error
            NewIssue.model_validate({
                'Description': 'No title provided'
            })

    def test_new_issue_with_all_aliases(self):
        """Test creating NewIssue with multiple field aliases."""
        issue = NewIssue.model_validate({
            'Title': 'Test Title',
            'Description': 'Test description\\nwith newlines',
            'Labels': 'bug, feature',
            'Assignees': 'user1, user2'
        })

        assert issue.title == 'Test Title'
        assert 'Test description\nwith newlines' == issue.body
        assert issue.labels == ['bug', 'feature']
        assert issue.assignees == ['user1', 'user2']
