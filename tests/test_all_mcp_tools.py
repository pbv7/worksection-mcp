#!/usr/bin/env python3
"""
Comprehensive test script for ALL Worksection MCP tools.

This script:
1. Initializes the MCP server with all registered tools
2. Authenticates and extracts test IDs from production data
3. Tests every MCP tool with appropriate parameters
4. Validates responses have expected structure
5. Provides detailed pass/fail results

Usage:
    # Use first available project
    uv run python tests/test_all_mcp_tools.py

    # Specify project name
    uv run python tests/test_all_mcp_tools.py --project "My Project"

    # Specify a "rich" task (has comments, files, images) for comprehensive testing
    uv run python tests/test_all_mcp_tools.py --rich-task "12345678"

    # Verbose mode - show args, response preview, and validation details
    uv run python tests/test_all_mcp_tools.py -v

    # Use environment variables
    TEST_PROJECT_NAME="My Project" uv run python tests/test_all_mcp_tools.py
    TEST_RICH_TASK="12345678" uv run python tests/test_all_mcp_tools.py
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from typing import Any, ClassVar, cast

# Add src to path
sys.path.insert(0, "src")

from fastmcp import FastMCP

from worksection_mcp.auth import OAuth2Manager
from worksection_mcp.cache import FileCache
from worksection_mcp.client import WorksectionClient
from worksection_mcp.config import get_settings
from worksection_mcp.tools import register_all_tools


class MCPToolTester:
    """Comprehensive MCP tool tester."""

    # Validation rules for tool responses
    # Each rule can have:
    #   required_fields: list of fields that must exist
    #   any_of_fields: at least one of these fields must exist
    #   status_values: valid values for status field
    #   data_is_list: data field must be a list
    #   data_is_dict: data field must be a dict
    #   field_is_list: list of root fields that must be lists
    #   field_is_dict: list of root fields that must be dicts
    #   field_values: dict of field -> allowed values
    #   min_size: minimum value for size_bytes field
    #   min_items: minimum number of items in data list (for rich task validation)
    #   min_total_files: minimum value for total_files field (for rich task validation)
    VALIDATION_RULES: ClassVar[dict[str, dict[str, Any]]] = {
        # System tools
        "health_check": {
            "required_fields": ["status", "api_base_url", "account_url"],
            "status_values": ["ok", "healthy"],
        },
        "get_webhooks": {"required_fields": ["status"], "allow_error": True},
        # List tools - expect data array
        "get_projects": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_tasks": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_users": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_task_tags": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_task_tag_groups": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_project_tags": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_project_tag_groups": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_comments": {
            "required_fields": ["status", "data", "total_count", "returned_count", "truncated"],
            "data_is_list": True,
        },
        "get_contacts": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_contact_groups": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_costs": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_user_groups": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_project_groups": {"required_fields": ["status", "data"], "data_is_list": True},
        "get_project_files": {"required_fields": ["status", "data"], "data_is_list": True},
        # Single item tools - expect data object
        "get_project": {"required_fields": ["status", "data"], "data_is_dict": True},
        "get_task": {"required_fields": ["status", "data"], "data_is_dict": True},
        "get_user": {"required_fields": ["status", "data"], "data_is_dict": True},
        "get_current_user": {"required_fields": ["status", "data"], "data_is_dict": True},
        "get_project_team": {"required_fields": ["status", "data"]},
        # Task detail tools
        "get_task_subtasks": {"required_fields": ["status"]},
        "get_task_relations": {"required_fields": ["status"]},
        "get_task_subscribers": {"required_fields": ["status"]},
        "get_task_discussion": {"required_fields": ["task_id", "comments"]},
        # Task with tags - special response format
        "get_task_with_tags": {"required_fields": ["status", "task_id", "tags", "tag_names"]},
        # User tools
        "get_user_assignments": {"required_fields": ["user_id", "tasks"]},
        # File tools - expect specific fields
        "download_file": {"required_fields": ["file_id", "size_bytes"], "min_size": 1},
        "get_file_as_base64": {
            "required_fields": ["file_id", "base64_content", "size_bytes", "mime_type", "is_image"],
            "min_size": 1,
        },
        "get_file_content": {
            "required_fields": [
                "file_id",
                "mime_type",
                "content_type",
                "text_content",
                "is_readable",
            ]
        },
        "get_task_files": {"required_fields": ["status"]},
        "get_all_task_attachments": {"required_fields": ["task_id", "total_files"]},
        "list_image_attachments": {
            "required_fields": ["image_count"],
            "any_of_fields": ["task_id", "project_id"],
        },
        # Analytics tools - expect computed fields
        "get_project_stats": {"required_fields": ["project_id"]},
        "get_team_workload_summary": {
            "required_fields": ["project_id", "members", "total_members"]
        },
        "get_overdue_tasks": {"required_fields": ["tasks", "count"]},
        "get_tasks_by_status": {"required_fields": ["project_id", "status", "tasks", "count"]},
        "get_tasks_by_priority": {"required_fields": ["project_id", "priority", "tasks", "count"]},
        # Time tracking tools
        "get_costs_total": {"required_fields": ["project_id"]},
        "get_user_workload": {"required_fields": ["user_id"]},
        "get_project_time_report": {
            "required_fields": ["project_id", "totals", "entries"],
            "field_is_dict": ["totals", "entries"],
        },
        # Timer tools
        "get_timers": {"required_fields": ["status"]},
        "get_my_timer": {"required_fields": ["status"]},
        # Search tools
        "search_tasks": {
            "required_fields": ["status", "data", "total_count", "returned_count", "truncated"],
            "data_is_list": True,
        },
        "search_tasks_by_tag": {"required_fields": ["tag", "tasks", "count"]},
        # Tools that return status on success or error
        "get_all_tasks": {"required_fields": ["status", "data"], "data_is_list": True},
        # Activity tools
        "get_activity_log": {
            "required_fields": [
                "project_id",
                "events",
                "event_types",
                "total_count",
                "returned_count",
                "truncated",
                "truncation_reason",
            ],
            "field_is_list": ["events"],
            "field_is_dict": ["event_types"],
            "field_values": {
                "truncation_reason": ["none", "max_results", "size_cap", "both"],
            },
        },
        "get_user_activity": {
            "required_fields": [
                "user_id",
                "events",
                "projects_touched",
                "total_count",
                "returned_count",
                "truncated",
                "truncation_reason",
            ],
            "field_is_list": ["events"],
            "field_is_dict": ["projects_touched"],
            "field_values": {
                "truncation_reason": ["none", "max_results", "size_cap", "both"],
            },
        },
    }

    # Enhanced validation rules when rich task is specified
    # These add min_items requirements to ensure meaningful data is returned
    RICH_TASK_VALIDATION_RULES: ClassVar[dict[str, dict[str, Any]]] = {
        "get_comments": {"min_items": 1},  # Rich task should have comments
        "get_all_task_attachments": {"min_total_files": 1},  # Rich task should have files
        "list_image_attachments": {"min_image_count": 0},  # May or may not have images
    }

    def __init__(
        self,
        project_name: str | None = None,
        rich_task: str | None = None,
        verbose: bool = False,
    ):
        self.project_name = project_name
        self.rich_task = rich_task
        self.verbose = verbose
        self.results: list[dict[str, Any]] = []
        self.test_ids: dict[str, str | None] = {
            "user_id": None,
            "project_id": None,
            "task_id": None,
            "file_id": None,
            "comment_id": None,
            "files_project_id": None,
        }
        self.mcp: FastMCP[Any] | None = None
        self.client: WorksectionClient | None = None
        self.oauth: OAuth2Manager | None = None
        self.file_cache: FileCache | None = None
        self.tool_functions: dict[str, str] = {}

    @staticmethod
    def _out(message: object = "") -> None:
        """Write a single line of human-readable output."""
        sys.stdout.write(f"{message}\n")

    async def _get_registered_tools(self) -> dict[str, Any]:
        """Return registered tools keyed by tool name."""
        if self.mcp is None:
            raise RuntimeError("MCP server is not initialized. Call setup() first.")

        tools = await self.mcp.list_tools()
        return {tool.name: tool for tool in tools}

    async def setup(self) -> int:
        """Initialize MCP server and components."""
        self._out("=" * 80)
        self._out("WORKSECTION MCP - COMPREHENSIVE TOOL TEST")
        self._out("=" * 80)
        self._out(f"Started at: {datetime.now(UTC)}\n")

        settings = get_settings()

        # Initialize components
        oauth = OAuth2Manager(settings)
        client = WorksectionClient(oauth, settings)
        file_cache = FileCache(
            cache_path=settings.file_cache_path,
            max_file_size_bytes=settings.max_file_size_bytes,
            retention_hours=settings.file_cache_retention_hours,
        )
        self.oauth = oauth
        self.client = client
        self.file_cache = file_cache

        # Authenticate
        self._out("Authenticating...")
        await oauth.ensure_authenticated()
        self._out("✓ Authentication successful\n")

        # Create MCP server with tools
        self._out("Registering MCP tools...")
        mcp = FastMCP("test-server")
        register_all_tools(mcp, client, oauth, file_cache)
        self.mcp = mcp

        # Get all registered tools (returns dict of tool_name -> Tool object)
        tools_dict = await self._get_registered_tools()
        self._out(f"✓ Registered {len(tools_dict)} MCP tools\n")

        # Guard against drift between registered tools and validation rules
        registered_tools = set(tools_dict.keys())
        validation_tools = set(self.VALIDATION_RULES.keys())
        missing_rules = sorted(registered_tools - validation_tools)
        extra_rules = sorted(validation_tools - registered_tools)
        if missing_rules or extra_rules:
            self._out("✗ Tool/validation rule mismatch detected:")
            if missing_rules:
                self._out(f"  Missing validation rules: {', '.join(missing_rules)}")
            if extra_rules:
                self._out(f"  Extra validation rules: {', '.join(extra_rules)}")
            raise RuntimeError(
                "Validation rules are out of sync with registered MCP tools. "
                "Update VALIDATION_RULES in tests/test_all_mcp_tools.py"
            )
        self._out("✓ Tool registry matches validation rules\n")

        # Store tool names
        self.tool_functions = {name: name for name in tools_dict}

        return len(tools_dict)

    async def extract_test_ids(self) -> None:
        """Extract IDs from production data for testing."""
        if self.client is None:
            raise RuntimeError("Client is not initialized. Call setup() first.")
        client = self.client

        self._out("=" * 80)
        self._out("EXTRACTING TEST DATA")
        self._out("=" * 80)

        # Get current user
        try:
            me_data = await client.me()
            if me_data.get("data"):
                self.test_ids["user_id"] = me_data["data"]["id"]
                self._out(f"✓ user_id: {self.test_ids['user_id']}")
        except Exception as e:
            self._out(f"⚠️  Failed to get user_id: {e}")

        # Find project by name or use first available
        try:
            projects = await client.get_projects()
            if projects.get("data"):
                if self.project_name:
                    # Search for project by name
                    for project in projects["data"]:
                        if self.project_name.lower() in project.get("name", "").lower():
                            self.test_ids["project_id"] = project["id"]
                            self._out(
                                f"✓ project_id: {self.test_ids['project_id']} ({project['name']})"
                            )
                            break

                    if not self.test_ids["project_id"]:
                        self._out(
                            f"⚠️  Project '{self.project_name}' not found, using first available"
                        )

                # Fallback to first project if not found or no name specified
                if not self.test_ids["project_id"]:
                    self.test_ids["project_id"] = projects["data"][0]["id"]
                    project_name = projects["data"][0].get("name", "Unknown")
                    self._out(f"✓ project_id: {self.test_ids['project_id']} ({project_name})")
        except Exception as e:
            self._out(f"⚠️  Failed to get project_id: {e}")

        # If rich_task is specified, use it as primary task_id and extract file_id from it
        if self.rich_task:
            try:
                assert self.rich_task is not None
                task_detail = await client.get_task(self.rich_task, extra="files")
                task_data = task_detail.get("data", task_detail)
                self.test_ids["task_id"] = self.rich_task
                self._out(f"✓ task_id: {self.test_ids['task_id']} (rich task)")

                # Extract file_id from rich task
                task_files = task_data.get("files", [])
                if task_files:
                    self.test_ids["file_id"] = task_files[0]["id"]
                    self._out(
                        f"✓ file_id: {self.test_ids['file_id']} (from rich task, {len(task_files)} files total)"
                    )
                else:
                    self._out(f"⚠️  Rich task {self.rich_task} has no file attachments")
            except Exception as e:
                self._out(f"⚠️  Failed to get rich task {self.rich_task}: {e}")
                # Fall back to getting a task from the project
                self.rich_task = None

        # Get a task from the project if no rich_task or it failed
        if self.test_ids["project_id"] and not self.test_ids["task_id"]:
            try:
                tasks = await client.get_tasks(self.test_ids["project_id"])
                if tasks.get("data") and len(tasks["data"]) > 0:
                    self.test_ids["task_id"] = tasks["data"][0]["id"]
                    self._out(f"✓ task_id: {self.test_ids['task_id']}")

                    # Try to get file_id from task
                    task_id = self.test_ids["task_id"]
                    assert task_id is not None
                    task_detail = await client.get_task(
                        task_id,
                        extra="files",
                    )
                    task_data = task_detail.get("data", task_detail)
                    task_files = task_data.get("files", [])
                    if task_files:
                        self.test_ids["file_id"] = task_files[0]["id"]
                        self._out(f"✓ file_id: {self.test_ids['file_id']}")
            except Exception as e:
                self._out(f"⚠️  Failed to get task_id: {e}")

        # Auto-discover a project that has files for get_project_files testing
        try:
            primary_pid = self.test_ids["project_id"]
            if primary_pid:
                files_resp = await client.get_files(project_id=primary_pid)
                if files_resp.get("data") and len(files_resp["data"]) > 0:
                    self.test_ids["files_project_id"] = primary_pid
                    self._out(
                        f"✓ files_project_id: {primary_pid} ({len(files_resp['data'])} files)"
                    )

            if not self.test_ids["files_project_id"]:
                projects = await client.get_projects()
                for project in projects.get("data", []):
                    pid = project["id"]
                    if pid == primary_pid:
                        continue  # Already checked
                    files_resp = await client.get_files(project_id=pid)
                    if files_resp.get("data") and len(files_resp["data"]) > 0:
                        self.test_ids["files_project_id"] = pid
                        self._out(
                            f"✓ files_project_id: {pid} ({project.get('name', '?')}, "
                            f"{len(files_resp['data'])} files)"
                        )
                        break

            if not self.test_ids["files_project_id"]:
                self._out("⚠️  No project with files found for get_project_files test")
        except Exception as e:
            self._out(f"⚠️  Failed to discover files_project_id: {e}")

        self._out()

    def validate_response(self, tool_name: str, response: Any) -> tuple[bool, list[str], list[str]]:
        """Validate tool response against expected structure.

        Returns:
            Tuple of (is_valid, passed_checks, failed_checks)
        """
        passed: list[str] = []
        failed: list[str] = []

        # Get validation rules for this tool
        rules = self.VALIDATION_RULES.get(tool_name, {}).copy()

        # Add rich task validation rules if rich_task is specified
        if self.rich_task and tool_name in self.RICH_TASK_VALIDATION_RULES:
            rules.update(self.RICH_TASK_VALIDATION_RULES[tool_name])

        # If allow_error is set and response has status="error", treat as graceful error
        is_error_response = (
            rules.get("allow_error")
            and isinstance(response, dict)
            and response.get("status") == "error"
        )
        if is_error_response:
            passed.append("graceful error response")
            if "error" in response:
                passed.append(f"has error message: {str(response['error'])[:80]}")
            if "hint" in response:
                passed.append("has hint")
            return True, passed, failed

        # If no specific rules, use generic validation
        if not rules:
            # Generic: response should be dict and not empty
            if isinstance(response, dict):
                passed.append("response is dict")
                if response:
                    passed.append("response not empty")
                else:
                    failed.append("response is empty dict")
            elif isinstance(response, bytes):
                passed.append("response is bytes")
                if len(response) > 0:
                    passed.append(f"has content ({len(response)} bytes)")
                else:
                    failed.append("response is empty bytes")
            else:
                failed.append(f"unexpected response type: {type(response).__name__}")

            return len(failed) == 0, passed, failed

        # Check required fields
        if "required_fields" in rules:
            for field in rules["required_fields"]:
                if isinstance(response, dict) and field in response:
                    passed.append(f"has '{field}'")
                else:
                    failed.append(f"missing '{field}'")

        # Check any_of_fields
        if "any_of_fields" in rules:
            if isinstance(response, dict):
                present = [field for field in rules["any_of_fields"] if field in response]
                if present:
                    passed.append(f"has one of {rules['any_of_fields']}: {', '.join(present)}")
                else:
                    failed.append(f"missing all of {rules['any_of_fields']}")
            else:
                failed.append("response is not dict for any_of_fields check")

        # Check status values
        if "status_values" in rules and isinstance(response, dict):
            status = response.get("status")
            if status in rules["status_values"]:
                passed.append(f"status='{status}'")
            else:
                failed.append(f"status='{status}' not in {rules['status_values']}")

        # Check data is list
        if rules.get("data_is_list") and isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, list):
                passed.append(f"data is list ({len(data)} items)")

                # Check min_items if specified (for rich task validation)
                if "min_items" in rules:
                    if len(data) >= rules["min_items"]:
                        passed.append(f"has {len(data)} items (min: {rules['min_items']})")
                    else:
                        failed.append(
                            f"only {len(data)} items, expected at least {rules['min_items']}"
                        )
            else:
                failed.append(f"data is not list: {type(data).__name__}")

        # Check data is dict
        if rules.get("data_is_dict") and isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, dict):
                passed.append("data is dict")
            else:
                failed.append(f"data is not dict: {type(data).__name__}")

        # Check root fields are lists
        if "field_is_list" in rules and isinstance(response, dict):
            for field in rules["field_is_list"]:
                value = response.get(field)
                if isinstance(value, list):
                    passed.append(f"'{field}' is list ({len(value)} items)")
                else:
                    failed.append(f"'{field}' is not list: {type(value).__name__}")

        # Check root fields are dicts
        if "field_is_dict" in rules and isinstance(response, dict):
            for field in rules["field_is_dict"]:
                value = response.get(field)
                if isinstance(value, dict):
                    passed.append(f"'{field}' is dict")
                else:
                    failed.append(f"'{field}' is not dict: {type(value).__name__}")

        # Check fields against allowed values
        if "field_values" in rules and isinstance(response, dict):
            for field, allowed_values in rules["field_values"].items():
                value = response.get(field)
                if value in allowed_values:
                    passed.append(f"{field}='{value}'")
                else:
                    failed.append(f"{field}='{value}' not in {allowed_values}")

        # Check minimum size (for file downloads)
        if "min_size" in rules and isinstance(response, dict):
            size = response.get("size_bytes", 0)
            if size >= rules["min_size"]:
                passed.append(f"size_bytes={size}")
            else:
                failed.append(f"size_bytes={size} < {rules['min_size']}")

        # Check min_total_files (for rich task validation of get_all_task_attachments)
        if "min_total_files" in rules and isinstance(response, dict):
            total_files = response.get("total_files", 0)
            if total_files >= rules["min_total_files"]:
                passed.append(f"total_files={total_files}")
            else:
                failed.append(f"total_files={total_files} < {rules['min_total_files']}")

        # Check min_image_count (for rich task validation of list_image_attachments)
        if "min_image_count" in rules and isinstance(response, dict):
            image_count = response.get("image_count", 0)
            if image_count >= rules["min_image_count"]:
                passed.append(f"image_count={image_count}")
            else:
                failed.append(f"image_count={image_count} < {rules['min_image_count']}")

        # Check tasks nested object has status="ok" (for search_tasks_by_tag)
        if rules.get("tasks_status_ok") and isinstance(response, dict):
            tasks = response.get("tasks", {})
            if isinstance(tasks, dict):
                tasks_status = tasks.get("status")
                if tasks_status == "ok":
                    passed.append("tasks.status='ok'")
                elif tasks_status == "error":
                    error_msg = tasks.get("message", "unknown error")
                    failed.append(f"tasks.status='error': {error_msg}")
                else:
                    passed.append(f"tasks.status='{tasks_status}'")

        # Check events nested object has status="ok" (for get_project_activity)
        if rules.get("events_status_ok") and isinstance(response, dict):
            events = response.get("events", {})
            if isinstance(events, dict):
                events_status = events.get("status")
                if events_status == "ok":
                    passed.append("events.status='ok'")
                elif events_status == "error":
                    error_msg = events.get("message", "unknown error")
                    failed.append(f"events.status='error': {error_msg}")
                else:
                    passed.append(f"events.status='{events_status}'")

        return len(failed) == 0, passed, failed

    def format_response_preview(self, response: Any, max_len: int = 200) -> str:
        """Format response for preview display."""
        if isinstance(response, bytes):
            return f"<bytes: {len(response)} bytes>"
        if isinstance(response, dict):
            # Truncate large responses
            preview = json.dumps(response, ensure_ascii=False, default=str)
            if len(preview) > max_len:
                return preview[:max_len] + "..."
            return preview
        return str(response)[:max_len]

    async def call_mcp_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """Call an MCP tool by name and validate response."""
        if self.mcp is None:
            raise RuntimeError("MCP server is not initialized. Call setup() first.")

        try:
            # Get tools dict
            tools = await self._get_registered_tools()
            tool = tools.get(tool_name)

            if not tool:
                return {
                    "tool": tool_name,
                    "status": "error",
                    "error": f"Tool {tool_name} not found",
                    "args": kwargs,
                    "validation": {"passed": [], "failed": ["tool not found"]},
                }

            # Call the underlying tool function (FunctionTool exposes `.fn`).
            tool_fn = getattr(tool, "fn", None)
            if not callable(tool_fn):
                return {
                    "tool": tool_name,
                    "status": "error",
                    "error": f"Tool {tool_name} has no callable function",
                    "args": kwargs,
                    "validation": {"passed": [], "failed": ["tool function not callable"]},
                }
            typed_tool_fn = cast(Any, tool_fn)
            result = await typed_tool_fn(**kwargs)

            # Validate response
            is_valid, passed, failed = self.validate_response(tool_name, result)

            return {
                "tool": tool_name,
                "status": "success" if is_valid else "validation_failed",
                "response": result,
                "args": kwargs,
                "validation": {"passed": passed, "failed": failed},
            }

        except TypeError as e:
            if "'FunctionTool' object is not callable" in str(e):
                return {
                    "tool": tool_name,
                    "status": "error",
                    "error": f"Tool implementation bug: {e!s} (tool calls another MCP tool internally)",
                    "args": kwargs,
                    "validation": {"passed": [], "failed": ["exception thrown"]},
                }
            return {
                "tool": tool_name,
                "status": "error",
                "error": str(e),
                "args": kwargs,
                "validation": {"passed": [], "failed": ["exception thrown"]},
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "status": "error",
                "error": str(e),
                "args": kwargs,
                "validation": {"passed": [], "failed": ["exception thrown"]},
            }

    def get_tool_params(self, tool_name: str) -> dict[str, Any] | None:
        """Get appropriate parameters for a tool based on its name."""
        params: dict[str, Any] = {}

        # Project tools
        if (
            "project" in tool_name
            and tool_name in ["get_project", "get_project_team"]
            and self.test_ids["project_id"]
        ):
            params["project_id"] = self.test_ids["project_id"]

        # Task tools
        if "task" in tool_name:
            if tool_name in [
                "get_task",
                "get_task_files",
                "get_task_subtasks",
                "get_task_relations",
                "get_task_subscribers",
                "get_task_discussion",
                "get_task_with_tags",
            ]:
                if self.test_ids["task_id"]:
                    params["task_id"] = self.test_ids["task_id"]
            elif tool_name == "search_tasks":
                params["query"] = "test"
                if self.test_ids["project_id"]:
                    params["project_id"] = self.test_ids["project_id"]
            elif tool_name == "search_tasks_by_tag":
                params["tag"] = "email"
                if self.test_ids["project_id"]:
                    params["project_id"] = self.test_ids["project_id"]
            elif tool_name == "get_tasks_by_status":
                if self.test_ids["project_id"]:
                    params["project_id"] = self.test_ids["project_id"]
                params["status"] = "active"  # Use "active" not "open"
            elif tool_name == "get_tasks_by_priority":
                if self.test_ids["project_id"]:
                    params["project_id"] = self.test_ids["project_id"]
                params["priority"] = 10  # High priority more likely to have tasks
            elif tool_name == "get_tasks" and self.test_ids["project_id"]:
                params["project_id"] = self.test_ids["project_id"]

        # Comment tools
        if "comment" in tool_name and self.test_ids["task_id"]:
            params["task_id"] = self.test_ids["task_id"]

        # File tools
        if tool_name in ["download_file", "get_file_as_base64", "get_file_content"]:
            if not self.test_ids["file_id"]:
                return None  # Skip if no file available
            params["file_id"] = self.test_ids["file_id"]
        elif tool_name in ["get_task_files", "get_all_task_attachments"]:
            if self.test_ids["task_id"]:
                params["task_id"] = self.test_ids["task_id"]
        elif tool_name == "list_image_attachments":
            if self.test_ids["task_id"]:
                params["task_id"] = self.test_ids["task_id"]
            elif self.test_ids.get("files_project_id"):
                params["project_id"] = self.test_ids["files_project_id"]
            elif self.test_ids["project_id"]:
                params["project_id"] = self.test_ids["project_id"]
        elif tool_name == "get_project_files":
            if self.test_ids.get("files_project_id"):
                params["project_id"] = self.test_ids["files_project_id"]
            elif self.test_ids["project_id"]:
                params["project_id"] = self.test_ids["project_id"]

        # Timer tools
        if (
            ("timer" in tool_name or "cost" in tool_name or "time_report" in tool_name)
            and tool_name in ["get_costs", "get_costs_total", "get_project_time_report"]
            and self.test_ids["project_id"]
        ):
            params["project_id"] = self.test_ids["project_id"]

        # User tools
        if "user" in tool_name:
            if tool_name in ["get_user", "get_user_assignments", "get_user_activity"]:
                if self.test_ids["user_id"]:
                    params["user_id"] = self.test_ids["user_id"]
            elif tool_name == "get_user_workload":
                if self.test_ids["user_id"]:
                    params["user_id"] = self.test_ids["user_id"]
                params["date_start"] = "2024-01-01"
                params["date_end"] = "2024-12-31"

        # Activity tools
        if "activity" in tool_name or "event" in tool_name:
            if tool_name == "get_activity_log":
                params["period"] = "1d"
                if self.test_ids["project_id"]:
                    params["project_id"] = self.test_ids["project_id"]
            elif tool_name == "get_user_activity":
                if self.test_ids["user_id"]:
                    params["user_id"] = self.test_ids["user_id"]
                params["period"] = "1d"

        # Analytics tools
        if (
            "analytics" in tool_name or "stats" in tool_name or "summary" in tool_name
        ) and self.test_ids["project_id"]:
            params["project_id"] = self.test_ids["project_id"]

        # get_all_tasks needs status_filter to avoid "Too many tasks" error
        if tool_name == "get_all_tasks":
            params["status_filter"] = "active"

        return params

    async def test_all_tools(self) -> None:
        """Test all registered MCP tools."""
        if self.mcp is None:
            raise RuntimeError("MCP server is not initialized. Call setup() first.")

        self._out("=" * 80)
        self._out("TESTING ALL MCP TOOLS")
        self._out("=" * 80)
        self._out()

        # Get tools dict
        tools_dict = await self._get_registered_tools()
        tool_names = sorted(tools_dict.keys())
        total_tools = len(tool_names)

        for idx, tool_name in enumerate(tool_names, 1):
            # Get appropriate parameters
            params = self.get_tool_params(tool_name)

            # Skip if params is None (means we can't test this tool)
            if params is None:
                self._out(f"[{idx}/{total_tools}] ⊘ {tool_name} (skipped - no test data)")
                self.results.append(
                    {
                        "tool": tool_name,
                        "status": "skipped",
                        "reason": "No test data available",
                        "validation": {"passed": [], "failed": []},
                    }
                )
                continue

            # Call the tool
            result = await self.call_mcp_tool(tool_name, **params)
            self.results.append(result)

            # Print result
            validation = result.get("validation", {})
            passed_checks = validation.get("passed", [])
            failed_checks = validation.get("failed", [])

            if result["status"] == "success":
                self._out(f"[{idx}/{total_tools}] ✅ {tool_name}")
                if self.verbose:
                    self._out(f"    Args: {params}")
                    self._out(f"    Checks: {', '.join(passed_checks)}")
                    preview = self.format_response_preview(result.get("response"))
                    self._out(f"    Response: {preview}")
            elif result["status"] == "validation_failed":
                self._out(f"[{idx}/{total_tools}] ⚠️  {tool_name} (validation failed)")
                self._out(f"    Args: {params}")
                self._out(f"    ✓ Passed: {', '.join(passed_checks) or 'none'}")
                self._out(f"    ✗ Failed: {', '.join(failed_checks)}")
                if self.verbose:
                    preview = self.format_response_preview(result.get("response"))
                    self._out(f"    Response: {preview}")
            else:
                self._out(f"[{idx}/{total_tools}] ❌ {tool_name}")
                self._out(f"    Args: {params}")
                error = result.get("error", "Unknown error")
                self._out(f"    Error: {error[:150]}")

            # Rate limiting
            await asyncio.sleep(1.1)

    def print_summary(self):
        """Print test summary."""
        self._out("\n" + "=" * 80)
        self._out("TEST SUMMARY")
        self._out("=" * 80)

        total = len(self.results)
        success = sum(1 for r in self.results if r["status"] == "success")
        validation_failed = sum(1 for r in self.results if r["status"] == "validation_failed")
        failed = sum(1 for r in self.results if r["status"] == "error")
        skipped = sum(1 for r in self.results if r["status"] == "skipped")

        # Count total validation checks
        total_checks = sum(
            len(r.get("validation", {}).get("passed", []))
            + len(r.get("validation", {}).get("failed", []))
            for r in self.results
        )
        passed_checks = sum(len(r.get("validation", {}).get("passed", [])) for r in self.results)

        self._out(f"Total tools: {total}")
        self._out(f"✅ Passed: {success}")
        self._out(f"⚠️  Validation failed: {validation_failed}")
        self._out(f"❌ Error: {failed}")
        self._out(f"⊘ Skipped: {skipped}")

        if success + validation_failed + failed > 0:
            success_rate = success / (success + validation_failed + failed) * 100
            self._out(f"Success rate: {success_rate:.1f}%")

        if total_checks > 0:
            self._out(f"\nValidation checks: {passed_checks}/{total_checks} passed")

        if failed > 0:
            self._out("\n❌ FAILED TOOLS (errors):")
            for result in self.results:
                if result["status"] == "error":
                    self._out(f"  • {result['tool']}")
                    self._out(f"    Args: {result.get('args', {})}")
                    error_msg = result.get("error", "Unknown")
                    self._out(f"    Error: {error_msg[:200]}")
                    self._out()

        if validation_failed > 0:
            self._out("\n⚠️  VALIDATION FAILED TOOLS:")
            for result in self.results:
                if result["status"] == "validation_failed":
                    validation = result.get("validation", {})
                    self._out(f"  • {result['tool']}")
                    self._out(f"    Args: {result.get('args', {})}")
                    self._out(f"    ✓ Passed: {', '.join(validation.get('passed', []))}")
                    self._out(f"    ✗ Failed: {', '.join(validation.get('failed', []))}")
                    self._out()

        if skipped > 0:
            self._out("\n⊘ SKIPPED TOOLS:")
            for result in self.results:
                if result["status"] == "skipped":
                    self._out(f"  • {result['tool']} - {result.get('reason', 'Unknown')}")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()
        if self.file_cache:
            await self.file_cache.close()

    async def run(self) -> None:
        """Run the complete test suite."""
        try:
            await self.setup()
            await self.extract_test_ids()
            await self.test_all_tools()
            self.print_summary()
        finally:
            await self.cleanup()
            self._out(f"\nCompleted at: {datetime.now(UTC)}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test all Worksection MCP tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use first available project
  uv run python tests/test_all_mcp_tools.py

  # Specify project name
  uv run python tests/test_all_mcp_tools.py --project "My Project"

  # Specify a "rich" task (has comments, files, images) for comprehensive testing
  uv run python tests/test_all_mcp_tools.py --rich-task "12345678"

  # Verbose mode - show args, response preview, validation details
  uv run python tests/test_all_mcp_tools.py -v

  # Use environment variables
  TEST_PROJECT_NAME="My Project" uv run python tests/test_all_mcp_tools.py
  TEST_RICH_TASK="12345678" uv run python tests/test_all_mcp_tools.py

  # Full example with all options
  uv run python tests/test_all_mcp_tools.py --project "My Project" --rich-task "12345678" -v
        """,
    )
    parser.add_argument(
        "-p",
        "--project",
        help="Project name to use for testing (default: first available project)",
        default=os.getenv("TEST_PROJECT_NAME"),
    )
    parser.add_argument(
        "-r",
        "--rich-task",
        help="Task ID with comments, files, and images for comprehensive testing",
        default=os.getenv("TEST_RICH_TASK"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output: show args, response previews, and validation details",
    )
    return parser.parse_args()


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    tester = MCPToolTester(
        project_name=args.project,
        rich_task=args.rich_task,
        verbose=args.verbose,
    )
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
