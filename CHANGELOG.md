# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1] - 2026-04-23

### Changed

- Offload helper tools, offload resource previews, and automatic tool-response
  offloading now run local store/file operations in a worker thread to avoid
  blocking the async MCP server loop
- Binary offload resource previews now use the MCP resource `blob` key for the
  capped base64 preview, matching existing file resource conventions
- `read_offloaded_response_text` may return fewer raw bytes than requested when
  JSON escaping would otherwise make the serialized helper-tool response too large

### Fixed

- Offloaded response reads, metadata lookups, and resource previews now return
  compact error payloads if cleanup or another process removes the file between
  ID lookup and file access
- New offloads now enforce `LARGE_RESPONSE_OFFLOAD_MAX_FILES` immediately after
  writing, even when full cleanup is throttled
- Text offload resource previews now trim to a complete UTF-8 boundary before
  decoding

### Security

- lxml 6.0.4 → 6.1.0 (HIGH: XXE via default `iterparse()` / `ETCompatXMLParser()`)
- authlib 1.6.10 → 1.6.11 (MEDIUM: CSRF when using cache)

## [0.6.0] - 2026-04-22

### Added

- Automatic large response offloading: tool responses exceeding
  `LARGE_RESPONSE_OFFLOAD_THRESHOLD_BYTES` (default 50 KB) are written to disk
  and replaced with a compact JSON envelope containing an ID, size, SHA-256,
  MIME type, and `worksection://offload/` resource URI
- `get_offloaded_response_info` tool — inspect metadata for an offloaded
  response by ID
- `read_offloaded_response_text` tool — read offloaded text/JSON responses in
  configurable byte-sized chunks with `offset`/`has_more` pagination;
  UTF-8 boundary-safe
- `worksection://offload/{response_id}` MCP resource — returns a 1 KB preview
  with full metadata for vision-capable clients
- Seven new configuration settings: `LARGE_RESPONSE_OFFLOAD_ENABLED`,
  `LARGE_RESPONSE_OFFLOAD_PATH`, `LARGE_RESPONSE_OFFLOAD_THRESHOLD_BYTES`,
  `LARGE_RESPONSE_OFFLOAD_RETENTION_HOURS`, `LARGE_RESPONSE_OFFLOAD_MAX_FILES`,
  `LARGE_RESPONSE_OFFLOAD_INCLUDE_FILE_PATH`, `LARGE_RESPONSE_MAX_READ_BYTES`
- Live end-to-end roundtrip test (`tests/live_large_response_offload_roundtrip.py`)
  that authenticates against the real Worksection API, triggers offloading, and
  verifies SHA-256 integrity across chunked reads
- `/app/data/offload` Docker directory and `offload_data` named volume for
  production deployments

### Changed

- `ToolRegistrar` protocol and `FakeMCP` test helper updated to support all
  three `@mcp.tool()` registration forms: `tool(fn)`, `tool(name=...)`,
  and `@tool()` decorator
- `pyproject.toml` `addopts`: coverage flags (`--cov`, `--cov-report`) moved to
  `make test` target so `make test-fast` and IDE test runners skip coverage
- `LARGE_RESPONSE_OFFLOAD_INCLUDE_FILE_PATH` now defaults to `false`; absolute
  server paths are no longer exposed in offload envelopes by default
- `ensure_directories()` only creates `large_response_offload_path` when
  `LARGE_RESPONSE_OFFLOAD_ENABLED=true`
- Startup offload cleanup is skipped when `LARGE_RESPONSE_OFFLOAD_ENABLED=false`

### Fixed

- `test_log_use_colors_is_tty_safe` now clears the `NO_COLOR` environment
  variable before the assertion to prevent false failures in environments where
  `NO_COLOR` is set globally
- `_trim_to_utf8_boundary`: extend trim range from 3 to 4 bytes so 4-byte
  UTF-8 sequences (e.g. emoji) are handled correctly at read boundaries
- `read_offloaded_response_text`: default `max_bytes` now derives from the
  configured `LARGE_RESPONSE_MAX_READ_BYTES` instead of a hardcoded value
- `_build_metadata`: SHA-256 for existing files now streamed in 64 KB chunks
  instead of loading the full payload into memory
- `cleanup_if_due()` throttles offload-triggered cleanup to once per 5 minutes
  for long-running servers; `cleanup()` reuses `mtime` from initial scan to
  avoid a second `stat()` call per file during eviction
- `read_text_slice` and the `LARGE_RESPONSE_MAX_READ_BYTES` settings validator
  now reject values below 4 bytes — the minimum needed to safely advance
  across any UTF-8 boundary
- `cleanup_if_due()` now runs before `_write_atomic()` so stale files are
  evicted before a new write (improves behaviour under low-disk conditions)

## [0.5.0] - 2026-02-27

### Added

- Centralized logging configuration module for app, FastMCP, Uvicorn, and httpx
- New runtime logging settings: `LOG_USE_COLORS` and `REQUEST_LOG_MODE` (`INFO`/`DEBUG`/`OFF`)
- Test coverage for logging configuration, request-log-mode behavior, and config-validator output

### Changed

- Unified log line format across server components: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
- Uvicorn now runs with explicit `log_config` and `access_log` derived from `REQUEST_LOG_MODE`
- Configuration docs and `.env.example` updated for new logging controls
- `scripts/validate_config.py` now displays logging controls in the configuration summary
- `scripts/validate_config.py` now uses TTY-safe ANSI colors for headings/status output, with plain-text fallback (`NO_COLOR`/non-TTY)

### Security

- Startup authentication log now records only user `id` and `name` instead of full user payload

## [0.4.0] - 2026-02-26

### Removed

- Drop legacy SSE transport support; only `streamable-http` and `stdio` are accepted

### Fixed

- Set graceful shutdown timeout to 5s for HTTP transports to eliminate `CancelledError` tracebacks on Ctrl+C

## [0.3.1] - 2026-02-26

### Added

- Codecov coverage upload and badge
- CodeQL security analysis workflow
- Docs workflow for markdown linting (`.md` files only)
- CODEOWNERS with `@pbv7` as owner of all files
- CLAUDE.md with development guidance for Claude Code
- SECURITY.md with vulnerability reporting policy, scope, and deployment assumptions

### Changed

- markdownlint config: allow duplicate headings in changelog (`MD024` siblings_only)
- README: add `mkdir -p data && chmod 700 data` step to quick start

### Security

- Redact OAuth2 authorization codes from callback server debug logs
- Redact token values in refresh-failure warning logs (keys preserved, values replaced with `[REDACTED]`)
- Set `umask(0o077)` in `main()` so all runtime-created files get mode 600 and directories mode 700
- Docker: scope `chown` to `/app/data` only; apply `chmod -R 700` recursively; add `data/certs` directory

## [0.3.0] - 2025-06-15

### Changed

- Default to streamable-http transport
- Upgrade to FastMCP v3 tooling
- Bump Python target to 3.14

### Added

- Makefile for development task automation

## [0.2.0] - 2025-05-28

### Added

- Administrative scope support
- Comprehensive behavioral test suite across core modules
- Configuration validation and error handling

### Fixed

- Activity tool: prevent MCP 1MB response limit errors with truncation
- File classification for plain UTF-8 payloads
- Auth callback error-page formatting crash

### Changed

- Tighten typing across server, tools, and tests
- Align tool filter args and runtime config

## [0.1.0] - 2025-05-15

### Added

- Initial release
- Multi-tenant MCP server for Worksection
- Comprehensive read-only tools for data access and reporting
- OAuth 2.0 and API key authentication
- Docker support with multi-stage production build
- Full test coverage with pytest

[0.6.1]: https://github.com/pbv7/worksection-mcp/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/pbv7/worksection-mcp/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/pbv7/worksection-mcp/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/pbv7/worksection-mcp/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/pbv7/worksection-mcp/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/pbv7/worksection-mcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pbv7/worksection-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pbv7/worksection-mcp/releases/tag/v0.1.0
