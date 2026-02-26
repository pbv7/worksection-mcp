# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Codecov coverage upload and badge
- CodeQL security analysis workflow
- Docs workflow for markdown linting (`.md` files only)
- CODEOWNERS with `@pbv7` as owner of all files
- CLAUDE.md with development guidance for Claude Code

### Changed

- markdownlint config: allow duplicate headings in changelog (`MD024` siblings_only)

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

[0.3.0]: https://github.com/pbv7/worksection-mcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pbv7/worksection-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pbv7/worksection-mcp/releases/tag/v0.1.0
