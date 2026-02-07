"""Project-related MCP tools."""

from typing import Literal

from worksection_mcp.client import WorksectionClient
from worksection_mcp.mcp_protocols import ToolRegistrar


def register_project_tools(mcp: ToolRegistrar, client: WorksectionClient) -> None:
    """Register project-related tools with the MCP server."""

    @mcp.tool()
    async def get_projects(
        status_filter: Literal["active", "archive", "all"] | None = None,
        extra: str | None = None,
    ) -> dict:
        """Get all projects from Worksection.

        Args:
            status_filter: Filter projects by status:
                - active: Only active projects (default)
                - archive: Only archived projects
                - all: All projects
            extra: Additional data to include. Valid values:
                text, options, users. Example: 'text' or 'text,users'.

        Returns:
            Dictionary containing list of projects with their details:
            - id: Project ID
            - name: Project name
            - status: Project status
            - page: Project URL path
            - date_start, date_end: Project dates
        """
        return await client.get_projects(status_filter=status_filter, extra=extra)

    @mcp.tool()
    async def get_project(
        project_id: str,
        extra: str | None = None,
    ) -> dict:
        """Get detailed information about a specific project.

        Args:
            project_id: The unique identifier of the project
            extra: Additional data to include. Valid values:
                text, options, users. Example: 'text' or 'text,users'.

        Returns:
            Complete project details including:
            - Basic info (id, name, status, dates)
            - Team members (if extra=users)
            - Description (if extra=text)
            - Settings (if extra=options)
        """
        return await client.get_project(project_id=project_id, extra=extra)

    @mcp.tool()
    async def get_project_groups() -> dict:
        """Get all project folders/groups.

        Returns:
            List of project groups/folders that organize projects.
            Each group contains:
            - id: Group ID
            - name: Group name
            - projects: List of project IDs in this group
        """
        return await client.get_project_groups()

    @mcp.tool()
    async def get_project_team(project_id: str) -> dict:
        """Get team members assigned to a project.

        Args:
            project_id: The project ID

        Returns:
            Project details with team members included:
            - users: List of users with their roles
            - Each user has: id, name, email, role
        """
        return await client.get_project(project_id=project_id, extra="users")
