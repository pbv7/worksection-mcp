"""User and team MCP tools."""

from typing import Literal

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar


def register_user_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register user and team tools with the MCP server."""

    @mcp.tool()
    async def get_users(
        status_filter: Literal["active", "all"] | None = None,
    ) -> dict:
        """Get all users in the Worksection account.

        Note: Returns ALL users in a single call (pagination not supported by API).

        Args:
            status_filter: Filter by status:
                - active: Only active users (default)
                - all: All users including deactivated

        Returns:
            List of users with:
            - id: User ID
            - email: User email
            - first_name, last_name: User name
            - status: active/inactive
            - role: User role in the account
        """
        return await client.get_users(status_filter=status_filter)

    @mcp.tool()
    async def get_user(user_id: str) -> dict:
        """Get detailed information about a specific user.

        Args:
            user_id: The user ID

        Returns:
            User details:
            - id: User ID
            - email: User email
            - first_name, last_name: Full name
            - phone: Phone number (if set)
            - position: Job title
            - department: Department/team
        """
        return await client.get_user(user_id=user_id)

    @mcp.tool()
    async def get_current_user() -> dict:
        """Get information about the current authenticated user.

        Returns:
            Current user details:
            - id: User ID
            - email: User email
            - name: Full name
            - account_url: Worksection account URL
        """
        return await client.me()

    @mcp.tool()
    async def get_user_groups() -> dict:
        """Get all user teams/departments.

        Returns:
            List of user groups:
            - id: Group ID
            - name: Group/team name
            - members: User IDs in this group
        """
        return await client.get_user_groups()

    @mcp.tool()
    async def get_contacts() -> dict:
        """Get the contact database.

        Contacts are external people (clients, partners) stored in Worksection.

        Returns:
            List of contacts:
            - id: Contact ID
            - name: Contact name
            - email: Email address
            - phone: Phone number
            - company: Company name
        """
        return await client.get_contacts()

    @mcp.tool()
    async def get_contact_groups() -> dict:
        """List all contact folders in the Worksection account.

        Returns both preset system folders and custom folders.

        Returns:
            List of contact groups/folders:
            - id: Group ID
            - name: Folder name
        """
        return await client.get_contact_groups()

    @mcp.tool()
    async def get_user_assignments(user_id: str) -> dict:
        """Get active tasks assigned to a specific user.

        Uses server-side filtering via search_tasks API for efficiency.

        Args:
            user_id: The user ID

        Returns:
            Tasks assigned to this user:
            - user: User information
            - tasks: List of assigned tasks
            - task_count: Total number of assigned tasks
        """
        # Get user info (includes email needed for search)
        user_data = await client.get_user(user_id=user_id)

        # Extract email for server-side filtering
        email = None
        if isinstance(user_data, dict) and "data" in user_data:
            email = user_data["data"].get("email")

        if email:
            # Use server-side filtering via search_tasks
            tasks_data = await client.search_tasks(email_user_to=email, status="active")
            assigned_tasks = tasks_data.get("data", []) if isinstance(tasks_data, dict) else []
        else:
            # Fallback: fetch all active tasks and filter client-side
            all_tasks = await client.get_all_tasks(status_filter="active")
            assigned_tasks = []
            if isinstance(all_tasks, dict) and "data" in all_tasks:
                for task in all_tasks["data"]:
                    user_to = task.get("user_to", {})
                    if user_to.get("id") == user_id:
                        assigned_tasks.append(task)

        return {
            "user_id": user_id,
            "user": user_data,
            "tasks": assigned_tasks,
            "task_count": len(assigned_tasks),
        }
