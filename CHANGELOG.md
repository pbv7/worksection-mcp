# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[0.4.0]: https://github.com/pbv7/worksection-mcp/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/pbv7/worksection-mcp/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/pbv7/worksection-mcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pbv7/worksection-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pbv7/worksection-mcp/releases/tag/v0.1.0
