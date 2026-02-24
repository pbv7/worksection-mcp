# Worksection API Limitations

Known limitations of the Worksection API and how this MCP server handles them.

## No Pagination

The Worksection API does not support pagination. All endpoints return complete
datasets in a single response. For large datasets, this MCP server applies
client-side truncation with metadata (`total_count`, `returned_count`,
`truncated`).

## 10,000 Record Hard Limit

The API returns a maximum of ~10,000 records per request. This is a
server-side limit that cannot be overridden.

## `status_filter='done'` with `project_id`

The API may return incomplete results when combining `status_filter='done'`
with `project_id`. The `get_tasks` tool works around this by fetching all
tasks and filtering client-side when this combination is used.

## `filter_query` Supported-Field Limitation

The `search_tasks` API `filter` parameter supports complex logical expressions,
but only for documented fields. Not every task field is queryable in this
grammar.

For example, expressions using `name`, `project`, and date fields may work,
while expressions using unsupported fields such as `priority` can fail with an
API validation error.

Use dedicated tools for those fields (for example `get_tasks_by_priority`) or
apply client-side filtering after retrieval.

## User Filtering in Costs/Events

The API's `id_user` parameter for cost endpoints may not filter correctly.
This MCP server applies client-side filtering when `user_id` is provided
to ensure accurate results.

The `get_events` API does not support filtering by event type. The
`event_filter` parameter is applied client-side by this MCP server on the
`object.type` field.

## MCP Response Size Cap

MCP protocol has a ~1MB response limit. To prevent errors, this server
truncates large responses using a `MAX_RESPONSE_BYTES = 850_000` constant
(defined in `response_utils.py`). The `truncate_to_size` function uses
binary search to find the maximum number of items whose JSON serialization
fits under the cap.

Activity and event tools include a `truncation_reason` metadata field:

- `none` — no truncation applied
- `max_results` — truncated by explicit `max_results` parameter only
- `size_cap` — truncated by size cap only
- `both` — both `max_results` and size cap were applied

When truncated, `event_types` counts reflect the full pre-truncation dataset.

## Event Type Field

Event types are located in `event.object.type` (not `event.type`).
Common values: `project`, `task`, `comment`.
