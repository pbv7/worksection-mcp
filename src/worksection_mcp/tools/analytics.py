"""Analytics and reporting MCP tools."""

from datetime import datetime, timedelta
from typing import Literal

from fastmcp import FastMCP

from worksection_mcp.client import WorksectionClient


def register_analytics_tools(mcp: FastMCP, client: WorksectionClient) -> None:
    """Register analytics and reporting tools with the MCP server."""

    @mcp.tool()
    async def get_project_stats(project_id: str) -> dict:
        """Get statistics for a project.

        Args:
            project_id: The project ID

        Returns:
            Project statistics:
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - active_tasks: Number of active tasks
            - completion_rate: Percentage of tasks completed
            - overdue_tasks: Number of overdue tasks
            - by_priority: Task count by priority level
            - by_status: Task count by status
        """
        # Get all tasks for the project
        tasks_data = await client.get_tasks(project_id=project_id, filter="all")

        total = 0
        completed = 0
        active = 0
        overdue = 0
        by_priority = {}
        by_status = {}

        now = datetime.now()

        if isinstance(tasks_data, dict) and "data" in tasks_data:
            tasks = tasks_data["data"]
            total = len(tasks)

            for task in tasks:
                status = task.get("status", "unknown")

                # Count by status
                by_status[status] = by_status.get(status, 0) + 1

                if status in ("done", "closed", "completed"):
                    completed += 1
                else:
                    active += 1

                    # Check if overdue
                    date_end = task.get("date_end")
                    if date_end:
                        try:
                            deadline = datetime.strptime(date_end, "%Y-%m-%d")
                            if deadline < now:
                                overdue += 1
                        except ValueError:
                            pass

                # Count by priority
                priority = task.get("priority", 0)
                priority_key = f"priority_{priority}"
                by_priority[priority_key] = by_priority.get(priority_key, 0) + 1

        completion_rate = round((completed / total * 100), 2) if total > 0 else 0

        return {
            "project_id": project_id,
            "total_tasks": total,
            "completed_tasks": completed,
            "active_tasks": active,
            "overdue_tasks": overdue,
            "completion_rate": completion_rate,
            "by_priority": by_priority,
            "by_status": by_status,
        }

    @mcp.tool()
    async def get_overdue_tasks(project_id: str | None = None) -> dict:
        """Get all overdue tasks.

        Args:
            project_id: Filter by project (optional)

        Returns:
            List of overdue tasks:
            - tasks: Overdue task list
            - count: Number of overdue tasks
            - by_project: Count per project (if no project filter)
        """
        if project_id:
            tasks_data = await client.get_tasks(project_id=project_id, filter="active")
        else:
            tasks_data = await client.get_all_tasks(filter="active")

        overdue_tasks = []
        by_project = {}
        now = datetime.now()

        if isinstance(tasks_data, dict) and "data" in tasks_data:
            for task in tasks_data["data"]:
                date_end = task.get("date_end")
                if date_end:
                    try:
                        deadline = datetime.strptime(date_end, "%Y-%m-%d")
                        if deadline < now:
                            overdue_tasks.append({
                                **task,
                                "days_overdue": (now - deadline).days,
                            })

                            # Count by project
                            proj = task.get("project", {})
                            proj_id = proj.get("id", "unknown")
                            proj_name = proj.get("name", "Unknown")
                            if proj_id not in by_project:
                                by_project[proj_id] = {"name": proj_name, "count": 0}
                            by_project[proj_id]["count"] += 1
                    except ValueError:
                        pass

        # Sort by days overdue (most overdue first)
        overdue_tasks.sort(key=lambda x: x.get("days_overdue", 0), reverse=True)

        return {
            "tasks": overdue_tasks,
            "count": len(overdue_tasks),
            "by_project": by_project,
        }

    @mcp.tool()
    async def get_tasks_by_status(
        project_id: str,
        status: str,
    ) -> dict:
        """Get tasks filtered by specific status.

        Args:
            project_id: The project ID
            status: Status to filter by (open, in_progress, review, done, etc.)

        Returns:
            Tasks with the specified status
        """
        tasks_data = await client.get_tasks(project_id=project_id, filter="all")

        filtered_tasks = []
        if isinstance(tasks_data, dict) and "data" in tasks_data:
            for task in tasks_data["data"]:
                if task.get("status", "").lower() == status.lower():
                    filtered_tasks.append(task)

        return {
            "project_id": project_id,
            "status": status,
            "tasks": filtered_tasks,
            "count": len(filtered_tasks),
        }

    @mcp.tool()
    async def get_tasks_by_priority(
        project_id: str,
        priority: int,
    ) -> dict:
        """Get tasks filtered by priority level.

        Args:
            project_id: The project ID
            priority: Priority level (typically 1-10, higher = more important)

        Returns:
            Tasks with the specified priority
        """
        tasks_data = await client.get_tasks(project_id=project_id, filter="active")

        filtered_tasks = []
        if isinstance(tasks_data, dict) and "data" in tasks_data:
            for task in tasks_data["data"]:
                # API returns priority as string, convert for comparison
                task_priority = task.get("priority")
                if task_priority is not None and str(task_priority) == str(priority):
                    filtered_tasks.append(task)

        return {
            "project_id": project_id,
            "priority": priority,
            "tasks": filtered_tasks,
            "count": len(filtered_tasks),
        }

    @mcp.tool()
    async def get_team_workload_summary(
        project_id: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> dict:
        """Get workload summary for all team members.

        Args:
            project_id: Filter by project (optional)
            date_start: Start date for time data (YYYY-MM-DD or DD.MM.YYYY, optional)
            date_end: End date for time data (YYYY-MM-DD or DD.MM.YYYY, optional)

        Returns:
            Team workload summary:
            - members: List of team members with their workload
            - Each member has: tasks_assigned, tasks_completed, time_logged
        """
        # Get users
        users_data = await client.get_users(filter="active")

        # Get tasks
        if project_id:
            tasks_data = await client.get_tasks(project_id=project_id, filter="all")
        else:
            tasks_data = await client.get_all_tasks(filter="all")

        # Get time data
        costs_data = await client.get_costs(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
        )

        # Build workload by user
        workload = {}

        # Initialize with all users
        if isinstance(users_data, dict) and "data" in users_data:
            for user in users_data["data"]:
                user_id = user.get("id")
                workload[user_id] = {
                    "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "email": user.get("email"),
                    "tasks_assigned": 0,
                    "tasks_completed": 0,
                    "time_logged_minutes": 0,
                }

        # Count tasks
        if isinstance(tasks_data, dict) and "data" in tasks_data:
            for task in tasks_data["data"]:
                user_to = task.get("user_to", {})
                user_id = user_to.get("id")
                if user_id in workload:
                    workload[user_id]["tasks_assigned"] += 1
                    if task.get("status") in ("done", "closed", "completed"):
                        workload[user_id]["tasks_completed"] += 1

        # Add time data
        if isinstance(costs_data, dict) and "data" in costs_data:
            for entry in costs_data["data"]:
                user = entry.get("user", {})
                user_id = user.get("id")
                if user_id in workload:
                    time_val = entry.get("time", 0)
                    if isinstance(time_val, str):
                        try:
                            if ":" in time_val:
                                hours, mins = time_val.split(":")
                                time_val = int(hours) * 60 + int(mins)
                            else:
                                time_val = int(time_val)
                        except ValueError:
                            time_val = 0
                    workload[user_id]["time_logged_minutes"] += time_val

        # Convert to list and add hours
        members = []
        for user_id, data in workload.items():
            data["user_id"] = user_id
            data["time_logged_hours"] = round(data["time_logged_minutes"] / 60, 2)
            members.append(data)

        # Sort by tasks assigned (descending)
        members.sort(key=lambda x: x["tasks_assigned"], reverse=True)

        return {
            "project_id": project_id,
            "date_start": date_start,
            "date_end": date_end,
            "members": members,
            "total_members": len(members),
        }
