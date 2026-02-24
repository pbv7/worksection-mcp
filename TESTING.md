# Testing Worksection MCP Tools

## Quick Start

Test all MCP tools with one command:

```bash
# Use first available project
uv run python tests/test_all_mcp_tools.py

# Specify project name
uv run python tests/test_all_mcp_tools.py --project "My Project"

# Specify a "rich" task for comprehensive testing (see Rich Task section below)
uv run python tests/test_all_mcp_tools.py --rich-task "12345678"

# Use environment variables
TEST_PROJECT_NAME="My Project" uv run python tests/test_all_mcp_tools.py
TEST_RICH_TASK="12345678" uv run python tests/test_all_mcp_tools.py

# Full example with all options
uv run python tests/test_all_mcp_tools.py --project "My Project" --rich-task "12345678" -v
```

## What It Does

The test script:

1. **Authenticates** - Uses your OAuth2 credentials from `.env`
2. **Extracts test data** - Finds IDs from specified project (or first available)
3. **Tests all tools** - Runs every MCP tool with appropriate parameters
4. **Shows results** - Clear pass/fail output with summary

## Configuration

### Project Selection

The script supports multiple ways to specify which project to use for testing:

1. **Command-line argument** (highest priority):

   ```bash
   uv run python tests/test_all_mcp_tools.py --project "My Project"
   ```

2. **Environment variable**:

   ```bash
   export TEST_PROJECT_NAME="My Project"
   uv run python tests/test_all_mcp_tools.py
   ```

3. **Default** (lowest priority):
   - Uses the first available project from your account

The project name matching is case-insensitive and uses partial matching.

### Rich Task

A "rich task" is a task that contains meaningful test data for comprehensive testing:

- ✅ **Comments** - for testing comment tools (`get_comments`, `get_task_discussion`)
- ✅ **File attachments** - for testing file tools (`download_file`, `get_file_as_base64`, `get_all_task_attachments`)
- ✅ **Image attachments** - for testing image tools (`list_image_attachments`)
- ✅ **DOCX/PDF files** - for testing content extraction (`get_file_content`)

When you specify a rich task, the script:

1. Uses it as the primary `task_id` for all task-related tools
2. Extracts `file_id` from its attachments for file tools
3. Applies stricter validation (expects non-empty results from comment and file tools)

**Command-line argument**:

```bash
uv run python tests/test_all_mcp_tools.py --rich-task "12345678"
```

**Environment variable**:

```bash
export TEST_RICH_TASK="12345678"
uv run python tests/test_all_mcp_tools.py
```

If no rich task is specified, the script will use the first task from the selected project. Without a rich task,
some tools may return empty results (which still pass basic validation but don't prove the tool works correctly).

## Prerequisites

- MCP server configured (`.env` file with OAuth2 credentials)
- Production Worksection account with data
- Python 3.14+ with dependencies installed (`uv sync`)

## Test Data

The script automatically extracts:

- **Project**: Specified project name or first available project
- **Task**: Rich task (if specified) or first task from the selected project
- **User**: Current authenticated user
- **File**: First file attachment from the rich task or task (if available)

## Output Example

```text
================================================================================
WORKSECTION MCP - COMPREHENSIVE TOOL TEST
================================================================================
Started at: 2026-01-28 02:30:00

Authenticating...
✓ Authentication successful

Registering MCP tools...
✓ Registered 48 MCP tools

================================================================================
EXTRACTING TEST DATA
================================================================================
✓ user_id: 555235
✓ project_id: 123456 (My Project)
✓ task_id: 789012
✓ file_id: 345678

================================================================================
TESTING ALL MCP TOOLS
================================================================================

[1/48] ✅ get_projects
[2/48] ✅ get_project
[3/48] ✅ get_project_groups
...
[48/48] ✅ health_check

================================================================================
TEST SUMMARY
================================================================================
Total tools: 48
✅ Passed: 46
❌ Failed: 0
⊘ Skipped: 2
Success rate: 100.0%

⊘ SKIPPED TOOLS:
  • download_file - No test data available
  • get_file_as_base64 - No test data available

Completed at: 2026-01-28 02:35:00
```

## Tool Categories

The test covers all tool categories:

- **Projects** (4 tools) - get_projects, get_project, get_project_groups, get_project_team
- **Tasks** (7 tools) - get_all_tasks, get_tasks, get_task, search_tasks, get_task_subtasks, get_task_relations, get_task_subscribers
- **Comments** (2 tools) - get_comments, get_task_discussion
- **Files** (7 tools) - get_task_files, get_all_task_attachments, get_project_files, download_file, get_file_as_base64, get_file_content, list_image_attachments
- **Costs & Timers** (6 tools) - get_costs, get_costs_total, get_user_workload, get_project_time_report, get_timers, get_my_timer
- **Users** (7 tools) - get_users, get_user, get_current_user, get_user_groups, get_contacts, get_contact_groups, get_user_assignments
- **Tags** (6 tools) - get_task_tags, get_task_tag_groups, get_project_tags, get_project_tag_groups, get_task_with_tags, search_tasks_by_tag
- **Analytics** (5 tools) - get_project_stats, get_overdue_tasks, get_tasks_by_status, get_tasks_by_priority, get_team_workload_summary
- **Activity** (2 tools) - get_activity_log, get_user_activity
- **System** (2 tools) - health_check, get_webhooks

## Troubleshooting

### Authentication Failed

```text
Error: Authentication failed
```

**Solution**: Check your `.env` file has correct OAuth2 credentials

### No Test Data

```text
⊘ Skipped: 2 tools - No test data available
```

**Solution**:

- Use `--rich-task` to specify a task with files, comments, and images
- Some tools require files in tasks (upload a file to a task)
- Ensure your test project has tasks with data

### API Rate Limit

```text
Error: Rate limit exceeded
```

**Solution**: Script automatically waits 1.1 seconds between calls. If you still hit limits, check for other API clients.

### Tool Failed

```text
❌ get_something
    Error: API request failed
```

**Solution**: Check the error details in output. Common causes:

- Missing permissions
- Invalid test data
- API changes

## Manual Testing

To test individual tools manually, use the MCP Inspector:

```bash
# Start server
uv run worksection-mcp

# In another terminal
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```

Or use the Python client directly:

```python
from worksection_mcp.client import WorksectionClient
from worksection_mcp.auth import OAuth2Manager
from worksection_mcp.config import get_settings

settings = get_settings()
oauth = OAuth2Manager(settings)
client = WorksectionClient(oauth, settings)

# Authenticate
await oauth.ensure_authenticated()

# Test a method
result = await client.get_projects()
print(result)
```

## Test Data Reference

Common test parameters used:

| Tool Type | Parameter | Example Value | Source |
| ----------- | ----------- | --------------- | -------- |
| Project tools | `project_id` | `"123456"` | Specified or first available project |
| Task tools | `task_id` | `"789012"` | Rich task or first task in project |
| User tools | `user_id` | `"555235"` | Current authenticated user |
| File tools | `file_id` | `"345678"` | First file in rich task or task |
| Search tools | `query` | `"test"` | Fixed test query |
| Filter tools | `status` | `"active"` | Fixed test value |
| Date tools | `date_start` | `"2024-01-01"` | Fixed test date |
| Activity tools | `period` | `"1d"` | Default 1-day period (configurable) |
| All tasks tool | `filter` | `"active"` | Filter to avoid "Too many tasks" error |

## Rate Limiting

- Worksection API: 1 request/second
- Test script automatically waits 1.1 seconds between calls
- Total test time: typically ~55-70 seconds for all tools (depends on API latency and retries)

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Install uv
  uses: astral-sh/setup-uv@v1

- name: Install dependencies
  run: uv sync

- name: Test MCP Tools
  run: uv run python tests/test_all_mcp_tools.py
  env:
    WORKSECTION_CLIENT_ID: ${{ secrets.WORKSECTION_CLIENT_ID }}
    WORKSECTION_CLIENT_SECRET: ${{ secrets.WORKSECTION_CLIENT_SECRET }}
    TEST_PROJECT_NAME: "Test Project"
    TEST_RICH_TASK: ${{ secrets.TEST_RICH_TASK }}  # Task with comments, files, and images
```

## Next Steps

After testing:

1. ✅ All tools passing → Ready for production
2. ⚠️  Some tools failing → Check error details, fix issues
3. 📝 Tools skipped → Add test data (files, etc.)

## Support

- **Issues**: <https://github.com/pbv7/worksection-mcp/issues>
- **Documentation**: See README.md
- **API Docs**: <https://worksection.com/en/faq/api-documentations.html>
