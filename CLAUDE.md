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

# Always use uv, never pip
uv sync --frozen --extra dev   # install
uv add <pkg>                   # add runtime dep
uv add --optional dev <pkg>    # add dev dep
```

## Architecture

### Server Startup

`server.py:create_server()` is the composition root. It wires all singletons:

- `OAuth2Manager` → `WorksectionClient` → `FileCache`
- Registers tools via `register_all_tools(mcp, client, oauth, file_cache)`
- Registers resources via `register_file_resources(mcp, client, file_cache)`
- Uses a FastMCP **lifespan context manager** for startup/shutdown (auth on startup, cleanup on shutdown)

Transport is selected at runtime from `MCP_TRANSPORT` env var: `streamable-http` (default), `sse`, or `stdio`.

### Adding a Tool

All tools live in `src/worksection_mcp/tools/`. Each module exports a `register_*_tools(mcp, client)`
function. Tools are registered with `@mcp.tool()` decorator inside that function.

1. Add the tool function to the appropriate module in `tools/`
2. Add the corresponding API method to `client/api.py` if needed
3. `tools/__init__.py:register_all_tools()` calls all registrar functions —
   no changes needed there unless adding a new module

The `ToolRegistrar` protocol in `mcp_protocols.py` enables testing tools without a real FastMCP instance.

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

### Configuration

`config/settings.py` uses Pydantic Settings. All config comes from `.env`. Validation runs at startup —
missing or malformed values raise immediately with clear messages.

### Testing

Tests use `pytest-asyncio` (`asyncio_mode = "auto"`). Shared fixtures are in `tests/conftest.py`
(mock settings, mock OAuth, mock client, sample data). HTTP calls are mocked with `respx`.
The `pyproject.toml` `addopts` automatically adds `--cov` and `-v` to every run.

## Release Flow

To cut a release:

1. **`pyproject.toml`** — bump `version = "x.y.z"`
2. **`CHANGELOG.md`** — rename `[Unreleased]` to `[x.y.z] - YYYY-MM-DD`
3. Commit: `chore(release): bump to vx.y.z`
4. Tag: `git tag vx.y.z && git push origin vx.y.z`

Pushing the tag triggers `release.yml` which builds the package and creates a GitHub Release with auto-generated notes and `dist/*` assets attached.

## CI Workflows

| Workflow | Trigger | Checks |
| --- | --- | --- |
| `ci.yml` | push/PR to main | format, lint, typecheck (mypy+pyright), pytest + Codecov |
| `docs.yml` | push/PR to main (`.md` only) | markdownlint-cli2 |
| `codeql.yml` | push/PR to main + weekly | CodeQL security analysis |
| `release.yml` | push to main | Release automation |

Both `CI` and `Docs` are required status checks on `main`. Branch protection enforces PR + 1 approval + linear history.
