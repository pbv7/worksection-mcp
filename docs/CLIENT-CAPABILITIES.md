# Client Capability Profile

This document explains what the Worksection MCP server provides in production
for read-only usage, and which limits come from Worksection API/platform
behavior (not from MCP implementation quality).

## Scope

- Read-only MCP server (no write operations)
- 48 registered tools across projects, tasks, comments, files, users, tags,
  analytics, activity, costs, and timers
- Designed for reporting, analysis, and assistant-driven data retrieval

## What Is Covered

The server provides broad read-only access to Worksection entities:

- Projects and project structure
- Tasks and task search
- Comments and discussion threads
- File metadata, downloads, and content extraction
- Users, groups, contacts, and assignments
- Task/project tags and tag-based lookup
- Time/cost reports and timer reads
- Activity/event logs

## What "Comprehensive" Means

"Comprehensive read-only" means:

- all major read endpoints used in operational reporting are implemented;
- tool response contracts are tested and stable;
- known API limitations are handled or surfaced predictably.

It does not mean bypassing Worksection API constraints.

## Platform Limits You Should Expect

### 1) 10,000 Record Hard Limit

Some broad task queries can return:

```json
{"status":"error","message":"Too many tasks (10000 max)"}
```

This is a Worksection API hard limit, not an MCP defect.

### 2) No Pagination in Key Endpoints

Worksection commonly returns full datasets in one response. For large datasets,
you must narrow scope by project/date/status and aggregate outside a single call.

### 3) `filter_query` Is Field-Limited

`search_tasks(filter_query=...)` supports complex logical expressions on
documented fields. Not every task field is queryable in this grammar.

Example:

- supported pattern: `(name has 'Bug' or name has 'Report') and (project = 302485)`
- unsupported pattern: `name has 'Bug' and priority >= 7` (fails by API)

Use dedicated tools (for example `get_tasks_by_priority`) or client-side
post-filtering for unsupported fields.

### 4) Permission-Scoped Data

Returned data depends on OAuth token scopes and account permissions.
Some endpoints (for example webhooks) require elevated scopes.

### 5) MCP Payload Safety Cap

MCP protocol has a 1MB response limit. This server applies an internal
`MAX_RESPONSE_BYTES = 850_000` safety cap for large list responses and returns
truncation metadata when applicable.

## Response Metadata You Can Rely On

For truncation-aware tools, expect:

- `total_count`
- `returned_count`
- `truncated`
- `truncation_reason` (`none`, `max_results`, `size_cap`, `both`) where supported

Use these fields in client reports to show completeness and limits explicitly.

## Recommended Reporting Patterns

- Prefer project-scoped and date-scoped queries over workspace-wide pulls.
- Split large reports into windows (for example 7/14/30-day segments).
- Avoid assuming `filter_query` can filter every field.
- Use truncation metadata in downstream dashboards/reports.

## Related Docs

- [API limitations](API-LIMITATIONS.md)
- [API reference](api-reference.md)
- [Schema](api-schema.json)
