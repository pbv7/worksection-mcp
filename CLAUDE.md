# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --frozen --extra dev

# Run all checks (format, lint, lint-docs, typecheck, test) — mirrors CI
make check

# Individual checks
make format          # ruff format (writes)
make lint            # ruff check (read-only)
make lint-docs       # markdownlint-cli2 on all *.md
make typecheck       # mypy + pyright

# Tests
make test            # pytest with coverage (HTML + term)
make test-fast       # pytest without coverage
uv run pytest tests/test_tools/test_analytics.py         # single file
uv run pytest tests/test_server.py::test_create_server   # single test
uv run pytest -k "oauth"                                 # pattern match

# Live E2E test for large response offload (requires real credentials + data)
uv run python tests/live_large_response_offload_roundtrip.py -v

# Package management — always use uv, never pip
uv add <pkg>                   # add runtime dep
uv add --optional dev <pkg>    # add dev dep
uv lock                        # regenerate uv.lock after pyproject.toml changes
```

## Architecture

### Source Layout

```text
src/worksection_mcp/
├── server.py          # composition root — create_server()
├── mcp_protocols.py   # ToolRegistrar / ResourceRegistrar protocols
├── large_response.py  # LargeResponseStore + LargePayloadToolRegistrar
├── logging_config.py  # unified logging pipeline
├── auth/              # OAuth2Manager, token storage, SSL, callback server
├── cache/             # FileCache (disk) + SessionCache (in-memory)
├── client/            # WorksectionClient (api.py) + RateLimiter
├── config/            # Settings (pydantic-settings, .env)
├── resources/         # files.py + offload.py (MCP resources)
├── tools/             # one module per domain; offload.py = helper tools
└── utils/             # date_utils.py + response_utils.py
```

### Server Startup

`server.py:create_server()` is the composition root. It wires all singletons:

- `OAuth2Manager` → `WorksectionClient` → `FileCache`
- `LargeResponseStore` (from `large_response.py`) — handles offload storage; see Large Response Offload section
- Registers tools via `register_all_tools(mcp, client, oauth, file_cache)`
- Registers offload helper tools directly on raw `mcp` (not wrapped, to avoid recursive offloading)
- Registers resources via `register_file_resources(mcp, client, file_cache)`
- Registers offload resource via `register_large_response_resources(mcp, store)`
- Uses a FastMCP **lifespan context manager** for startup/shutdown (auth on startup, cleanup on shutdown)

Transport is selected at runtime from `MCP_TRANSPORT` env var: `streamable-http` (default) or `stdio`.

### Adding a Tool

All tools live in `src/worksection_mcp/tools/`. Each module exports a `register_*_tools(mcp, client)`
function. Tools are registered with `@mcp.tool()` decorator inside that function.

1. Add the tool function to the appropriate module in `tools/`
2. Add the corresponding API method to `client/api.py` if needed
3. `tools/__init__.py:register_all_tools()` calls all registrar functions —
   no changes needed there unless adding a new module

The `ToolRegistrar` protocol in `mcp_protocols.py` enables testing tools without a real FastMCP instance.

All registered tools are automatically wrapped by `LargePayloadToolRegistrar`: responses exceeding
`LARGE_RESPONSE_OFFLOAD_THRESHOLD_BYTES` are offloaded to `./data/offload/` and replaced with a
compact metadata envelope. Clients use `read_offloaded_response_text` to read content in
UTF-8-safe chunks.

### API Client

`client/api.py:WorksectionClient` wraps all Worksection API calls. Every request:

1. Acquires the adaptive rate limiter (`client/rate_limiter.py`) — base 1 req/sec
2. Gets a valid token via `oauth.get_valid_token()` (refreshes automatically)
3. Checks session cache if `use_cache=True`
4. Makes the HTTP call; backs off on 429

### Authentication

`auth/oauth2.py:OAuth2Manager` handles the full OAuth2 flow. `ensure_authenticated()` is called at
lifespan startup. Tokens are Fernet-encrypted at rest in `./data/tokens/tokens.enc`. SSL certs for
the callback server are auto-generated in `./data/certs/`.

### Resources

`resources/files.py` registers `worksection://file/{file_id}` and `worksection://task/{task_id}/context`.
Files are cached to disk with SQLite metadata in `./data/files/`. Text files return `text`, binary
files return base64 `blob`.

`resources/offload.py` registers `worksection://offload/{response_id}` — returns metadata and a
small preview for an offloaded tool response. Full content is read via `read_offloaded_response_text`.

### Large Response Offload

`large_response.py` is the central safety layer for oversized MCP responses.

- `LargeResponseStore` — writes/reads/cleans offloaded files under `./data/offload/`
- `LargePayloadToolRegistrar` — wraps `ToolRegistrar`; intercepts responses above threshold
- Default threshold and read limit: **50,000 bytes**; read limit must be at least 4 bytes
- Local `file_path` metadata is hidden by default; prefer `resource_uri` and helper tools
- Cleanup runs on startup and before due future offloads for long-running servers
- Helper tools (`get_offloaded_response_info`, `read_offloaded_response_text`) are registered on
  raw `mcp` — never offload-wrapped — to prevent recursive offloading

### Configuration

`config/settings.py` uses Pydantic Settings. All config comes from `.env`. Validation runs at startup —
missing or malformed values raise immediately with clear messages.

### Utilities

`utils/response_utils.py` — `truncate_response()` (pagination) and `truncate_to_size()` (byte-cap
list truncation) are used in high-volume tools (`get_activity_log`, `search_tasks`, etc.).

### Testing

Tests use `pytest-asyncio` (`asyncio_mode = "auto"`). Shared fixtures are in `tests/conftest.py`
(mock settings, mock OAuth, mock client, sample data). HTTP calls are mocked with `respx`.
The `pyproject.toml` `addopts` adds `-v` only. Use `make test` or `make check` for coverage.
`tests/helpers.py:FakeMCP` is the lightweight tool registrar used in unit tests — supports
`tool()`, `tool(fn)`, `tool(name=...)`, and `resource()` registration forms.

## Code Style

- Line length: **100** (ruff enforced)
- All source files use `from __future__ import annotations` at the top
- Python 3.14 target — use modern syntax (`X | Y` unions, `match`, etc.)
- `S101` (assert) suppressed in tests only — use `assert` freely in tests

## Gotchas

- **Claude Code MCP config** goes in `~/.claude.json` (under `mcpServers`), NOT `~/.claude/settings.json`.
  The MCP dialog (`/mcp`) shows which file it reads — confirm there if tools are missing from a session.

- **Never manually edit `uv.lock`**, including the `[options]` block at the top. The
  `exclude-newer` and `exclude-newer-span = "P7D"` fields are machine-generated supply-chain
  security controls: they prevent uv from resolving packages released less than 7 days before the
  lock was generated (quarantine window against malicious new releases). uv recalculates them
  automatically on every `uv lock` run. Use `uv lock` to regenerate and `uv sync --frozen` to
  install — never touch the file by hand.

## Release Flow

To cut a release:

1. **`pyproject.toml`** — bump `version = "x.y.z"`
2. **`uv.lock`** — run `uv lock` (do not edit manually) and commit lockfile changes so the local package version matches `pyproject.toml`
3. **`CHANGELOG.md`** — rename `[Unreleased]` to `[x.y.z] - YYYY-MM-DD`; add comparison link at bottom
4. **`SECURITY.md`** — update Supported Versions table on minor/major bumps (e.g. `0.3.x` → `0.4.x`)
5. Commit: `chore(release): bump to vx.y.z`
6. Tag: `git tag vx.y.z && git push origin vx.y.z`

Pushing the tag triggers `release.yml` which builds the package and creates a GitHub Release with auto-generated notes and `dist/*` assets attached.

## CI Workflows

| Workflow | Trigger | Checks |
| --- | --- | --- |
| `ci.yml` | push/PR to main | format, lint, typecheck (mypy+pyright), pytest + Codecov |
| `docs.yml` | push/PR to main (`.md` only) | markdownlint-cli2 |
| `codeql.yml` | push/PR to main + weekly | CodeQL security analysis |
| `release.yml` | push to main | Release automation |

Both `CI` and `Docs` are required status checks on `main`. Branch protection enforces PR + 1 approval + linear history.
