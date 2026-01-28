"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import tempfile


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_settings(temp_data_dir):
    """Create mock settings for testing."""
    from worksection_mcp.config import Settings

    return Settings(
        worksection_client_id="test_client_id",
        worksection_client_secret="test_client_secret",
        worksection_account_url="https://test.worksection.com",
        worksection_redirect_uri="http://localhost:8080/oauth/callback",
        worksection_scopes="projects_read,tasks_read",
        token_storage_path=temp_data_dir / "tokens",
        file_cache_path=temp_data_dir / "files",
        token_encryption_key="test_encryption_key_32_bytes_long!",
    )


@pytest.fixture
def mock_oauth_manager():
    """Create a mock OAuth2 manager."""
    manager = MagicMock()
    manager.ensure_authenticated = AsyncMock()
    manager.get_valid_token = AsyncMock(return_value="test_access_token")
    return manager


@pytest.fixture
def mock_worksection_client(mock_oauth_manager):
    """Create a mock Worksection client."""
    client = MagicMock()
    client.oauth = mock_oauth_manager
    client.get = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def sample_project():
    """Sample project data from Worksection API."""
    return {
        "id": "12345",
        "name": "Test Project",
        "status": "active",
        "page": "/project/12345/",
        "date_start": "2024-01-01",
        "date_end": "2024-12-31",
    }


@pytest.fixture
def sample_task():
    """Sample task data from Worksection API."""
    return {
        "id": "67890",
        "name": "Test Task",
        "status": "open",
        "priority": 5,
        "project": {"id": "12345", "name": "Test Project"},
        "user_from": {"id": "111", "name": "John Doe"},
        "user_to": {"id": "222", "name": "Jane Doe"},
        "date_added": "2024-06-01 10:00:00",
        "date_end": "2024-06-15",
    }


@pytest.fixture
def sample_comment():
    """Sample comment data from Worksection API."""
    return {
        "id": "99999",
        "text": "This is a test comment",
        "date_added": "2024-06-01 12:00:00",
        "user_from": {"id": "111", "name": "John Doe"},
        "files": [],
    }


@pytest.fixture
def sample_user():
    """Sample user data from Worksection API."""
    return {
        "id": "111",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "status": "active",
    }
