# Worksection MCP Server

A multi-tenant MCP (Model Context Protocol) server for
[Worksection](https://worksection.com) project management platform,
built with FastMCP 2.0.

Provides **comprehensive read-only tools** for data access,
enabling AI assistants like Claude to generate reports, analyze project data,
and process image attachments.

## Features

- **Multi-tenant** - Configurable for any Worksection account
- **OAuth2 Authentication** - Secure authorization code flow with automatic
  token refresh
- **Comprehensive Read-only Tools** - Projects, tasks, comments, time tracking,
  users, and more
- **Image Analysis** - MCP resources for Claude vision to analyze screenshots
  and attachments
- **Rate Limiting** - Built-in 1 req/sec throttling per Worksection API limits
- **File Caching** - Local cache for downloaded attachments
- **Production Ready** - Docker containerization with multi-stage builds
- **Extensible** - Clean architecture for adding custom tools

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager
- Worksection account with OAuth2 app credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/pbv7/worksection-mcp.git
cd worksection-mcp

# Install dependencies with uv (always use --frozen to respect lockfile)
uv sync --frozen --extra dev

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Then validate your configuration
uv run python scripts/validate_config.py
```

### Configuration

Edit `.env` with your Worksection OAuth2 credentials:

```bash
# Required
WORKSECTION_CLIENT_ID=your_client_id
WORKSECTION_CLIENT_SECRET=your_client_secret
WORKSECTION_ACCOUNT_URL=https://yourcompany.worksection.com

# Optional (defaults shown)
WORKSECTION_REDIRECT_URI=https://localhost:8080/oauth/callback
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
```

### Running the Server

```bash
# Development
uv run python -m worksection_mcp

# Or using the entry point
uv run worksection-mcp
```

On first run, the server will:

1. Open your browser for OAuth2 authorization
2. After you authorize, it will save encrypted tokens
3. Start the MCP server on port 8000

### Docker Deployment

```bash
# Build the image
docker build -t worksection-mcp .

# Run with environment file
docker run -d \
  --name worksection-mcp \
  -p 8000:8000 \
  -e MCP_SERVER_HOST=0.0.0.0 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  worksection-mcp

# Or use docker-compose
docker compose up -d
```

## OAuth2 Setup

### Creating a Worksection OAuth2 App

1. Go to your Worksection account settings
2. Navigate to API / Integrations
3. Create a new OAuth2 application
4. Set the redirect URI to `https://localhost:8080/oauth/callback`
   (HTTPS required)
5. Note your `client_id` and `client_secret`
6. Enable required read scopes: Projects, Tasks, Costs, Tags,
   Comments, Files, People, Contacts

### HTTPS for OAuth Callback

Worksection requires HTTPS for OAuth2 redirect URIs. This server automatically
generates a self-signed SSL certificate on first run.

**What to expect:**

- Certificates are auto-generated and stored in `./data/certs/`
- Your browser will show "Your connection is not private" warning
- Click "Advanced" → "Proceed to localhost (unsafe)" to continue
- This is expected for self-signed certificates in local development

**Using custom certificates:**

```bash
# Set paths to your certificates in .env
OAUTH_SSL_CERT_PATH=/path/to/your/cert.crt
OAUTH_SSL_KEY_PATH=/path/to/your/key.key
```

**Disable SSL (not recommended):**

```bash
# Only if you have an alternative HTTPS solution (e.g., ngrok)
OAUTH_CALLBACK_USE_SSL=false
```

### Authentication Flow

```text
First Run (no tokens):
1. Server starts callback listener on port 8080
2. Opens browser → Worksection authorization page
3. User grants permissions
4. Callback receives authorization code
5. Server exchanges code for access + refresh tokens
6. Tokens encrypted and saved locally
7. MCP server starts

Subsequent Runs:
1. Load encrypted tokens from storage
2. If access token expired → auto-refresh
3. If refresh token expired → re-authenticate via browser
4. MCP server starts
```

## Available Tools

### Projects

| Tool | Description |
| ------ | ------------- |
| `get_projects` | List all projects with optional filtering |
| `get_project` | Get single project details |
| `get_project_groups` | Get project folders/groups |
| `get_project_team` | Get team members assigned to project |

### Tasks

| Tool | Description |
| ------ | ------------- |
| `get_all_tasks` | Get all tasks across projects |
| `get_tasks` | Get tasks for a specific project |
| `get_task` | Get single task details |
| `search_tasks` | Search tasks by query or filter expression |
| `get_task_subtasks` | Get subtasks of a task |
| `get_task_relations` | Get related/dependent tasks |
| `get_task_subscribers` | Get task watchers |

### Comments

| Tool | Description |
| ------ | ------------- |
| `get_comments` | Get comments for a task |
| `get_task_discussion` | Get full discussion thread with comments and files |

### Files

| Tool | Description |
| ------ | ------------- |
| `get_task_files` | Get files attached to task |
| `get_all_task_attachments` | Get all attachments from task and comments |
| `get_project_files` | List all files in a project or task |
| `download_file` | Download and cache a file |
| `get_file_as_base64` | Download file as base64 encoded string |
| `get_file_content` | Extract text content from files |
| `list_image_attachments` | List image files for a task or project |

### Costs & Timers

| Tool | Description |
| ------ | ------------- |
| `get_costs` | Get time/cost records |
| `get_costs_total` | Get aggregated costs |
| `get_user_workload` | Get user's time entries |
| `get_project_time_report` | Get project time report |
| `get_timers` | Get all currently running timers |
| `get_my_timer` | Get current user's running timer |

### Users & Teams

| Tool | Description |
| ------ | ------------- |
| `get_users` | Get all account users |
| `get_user` | Get single user details |
| `get_current_user` | Get current authenticated user |
| `get_user_groups` | Get teams/departments |
| `get_contacts` | Get contact database |
| `get_contact_groups` | List contact folders |
| `get_user_assignments` | Get tasks assigned to user |

### Tags

| Tool | Description |
| ------ | ------------- |
| `get_task_tags` | Get available task tags (labels/statuses) |
| `get_task_tag_groups` | Get task tag groups |
| `get_project_tags` | Get available project tags |
| `get_project_tag_groups` | Get project tag groups |
| `get_task_with_tags` | Get a task with its assigned tags |
| `search_tasks_by_tag` | Find tasks with a specific tag |

### Analytics

| Tool | Description |
| ------ | ------------- |
| `get_project_stats` | Get project statistics |
| `get_overdue_tasks` | Get overdue tasks |
| `get_tasks_by_status` | Filter tasks by status |
| `get_tasks_by_priority` | Filter tasks by priority |
| `get_team_workload_summary` | Get team workload overview |

### Activity

| Tool | Description |
| ------ | ------------- |
| `get_activity_log` | Get activity/event log with auto-size truncation and event type breakdown |
| `get_user_activity` | Get user's activity with auto-size truncation |

Activity tools default to returning as many events as fit under MCP's 1MB response
limit (with ~150KB safety margin, no fixed default cap). Set `max_results` explicitly to control truncation.
Truncation metadata (`total_count`, `returned_count`, `truncated`, `truncation_reason`)
is always included.

### System

| Tool | Description |
| ------ | ------------- |
| `health_check` | Check server health and API status |
| `get_webhooks` | List configured webhooks (requires `administrative` scope) |

## MCP Resources

Resources allow Claude to directly access and analyze files:

| Resource URI | Description |
| -------------- | ------------- |
| `worksection://file/{file_id}` | Access file for vision analysis |
| `worksection://task/{task_id}/context` | Get full task context with attachments |
| `worksection://cache/stats` | Get file cache statistics |

### Using Resources for Image Analysis

```python
# In your MCP client or skill:
# 1. Get task discussion with files
discussion = await get_task_discussion(task_id="12345")

# 2. For each image file, access via resource
for file in discussion.get("images", []):
    # Claude can read this resource and analyze the image
    image_content = await read_resource(file["resource_uri"])
```

## Configuration Reference

| Variable | Description | Default |
| ---------- | ------------- | --------- |
| `WORKSECTION_CLIENT_ID` | OAuth2 client ID | Required |
| `WORKSECTION_CLIENT_SECRET` | OAuth2 client secret | Required |
| `WORKSECTION_ACCOUNT_URL` | Your Worksection URL | Required |
| `WORKSECTION_REDIRECT_URI` | OAuth callback URL | `https://localhost:8080/oauth/callback` |
| `WORKSECTION_SCOPES` | OAuth2 scopes | `projects_read,tasks_read,...` |
| `OAUTH_CALLBACK_HOST` | Callback server host | `localhost` |
| `OAUTH_CALLBACK_PORT` | Callback server port | `8080` |
| `OAUTH_AUTO_OPEN_BROWSER` | Auto-open browser | `true` |
| `OAUTH_CALLBACK_USE_SSL` | Use HTTPS for callback | `true` |
| `OAUTH_SSL_CERT_PATH` | SSL certificate path | `./data/certs/callback.crt` |
| `OAUTH_SSL_KEY_PATH` | SSL private key path | `./data/certs/callback.key` |
| `OAUTH_SSL_CERT_DAYS` | Certificate validity (days) | `365` |
| `TOKEN_STORAGE_PATH` | Token storage directory | `./data/tokens` |
| `TOKEN_ENCRYPTION_KEY` | Encryption key (auto-generated) | |
| `FILE_CACHE_PATH` | File cache directory | `./data/files` |
| `FILE_CACHE_RETENTION_HOURS` | Cache retention | `24` |
| `MAX_FILE_SIZE_MB` | Max cached file size | `10` |
| `MCP_SERVER_NAME` | Server name | `worksection` |
| `MCP_SERVER_HOST` | SSE bind host (`127.0.0.1` local only, `0.0.0.0` LAN) | `127.0.0.1` |
| `MCP_SERVER_PORT` | Server port | `8000` |
| `MCP_TRANSPORT` | Transport type (`sse`/`stdio`) | `sse` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment name | `development` |

## Testing

### Automated Testing (Recommended)

Test all MCP tools automatically:

```bash
# Use first available project
uv run python tests/test_all_mcp_tools.py

# Specify project name
uv run python tests/test_all_mcp_tools.py --project "My Project"
```

This comprehensive test script:

- ✅ Tests all registered MCP tools
- ✅ Configurable project selection (via CLI argument or environment variable)
- ✅ Automatically extracts test IDs from your project data
- ✅ Provides detailed pass/fail results
- ✅ Handles rate limiting automatically

See **[TESTING.md](TESTING.md)** for complete documentation and configuration options.

### Manual Testing with MCP Inspector

For interactive testing:

```bash
# Start your MCP server
uv run worksection-mcp

# In another terminal, start the MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies (use --frozen, never uv pip install)
uv sync --frozen --extra dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=worksection_mcp --cov-report=html

# Lint code
uv run ruff check src/

# Lint all Markdown from repo root
npx markdownlint-cli2

# Auto-fix all Markdown from repo root
npx markdownlint-cli2 --fix

# Type check
uv run mypy src/
```

### Project Structure

```text
worksection-mcp/
├── src/
│   └── worksection_mcp/
│       ├── __init__.py          # Package init
│       ├── __main__.py          # Entry point
│       ├── server.py            # FastMCP server
│       ├── config/              # Configuration
│       ├── auth/                # OAuth2 authentication
│       ├── client/              # API client
│       ├── tools/               # MCP tools
│       ├── resources/           # MCP resources
│       ├── cache/               # File and session caching
│       └── utils/               # Date formatting, response truncation
├── tests/                       # Test suite
├── data/                        # Runtime data (gitignored)
├── Dockerfile                   # Container build
├── docker-compose.yml           # Local development
└── docker-compose.prod.yml      # Production deployment
```

## Deployment

### Docker Production

```bash
# Build production image
docker build -t worksection-mcp:latest .

# Run with production compose
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worksection-mcp
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: worksection-mcp
        image: worksection-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: WORKSECTION_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: worksection-secrets
              key: client_id
        - name: WORKSECTION_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: worksection-secrets
              key: client_secret
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: worksection-mcp-data
```

### Pre-authentication for Containers

Since OAuth2 requires browser interaction, authenticate locally first:

```bash
# 1. Run locally to authenticate
uv run python -m worksection_mcp

# 2. After authentication, tokens are saved to ./data/tokens/

# 3. Mount this directory in your container
docker run -v ./data:/app/data worksection-mcp
```

## Troubleshooting

### Configuration Validation

Before troubleshooting, validate your complete configuration:

```bash
uv run python scripts/validate_config.py
```

The validator performs comprehensive checks in 3 steps:

**Step 1: Pydantic Validation** (automatic when loading .env)

- OAuth2 credentials format and length
- URL format and structure
- Redirect URI HTTPS requirement
- Valid OAuth2 scope names
- Port number ranges (1-65535)
- Positive values for file sizes and retention
- SSL configuration consistency

#### Step 2: Configuration Summary

- Shows all loaded settings
- Displays derived values (API URLs)
- Helps verify environment variables are set correctly

#### Step 3: External Resource Checks

- DNS resolution for account URL
- Directory write permissions (tokens, cache, certs)
- Filesystem accessibility

If validation passes, your configuration is complete and the server will start successfully.

### OAuth2 Issues

#### "Invalid redirect URI"

- Ensure your registered redirect URI in Worksection matches exactly
- Default: `https://localhost:8080/oauth/callback`
- Worksection requires HTTPS - do not use `http://`

#### "Your connection is not private" browser warning

- This is expected with self-signed certificates
- Click "Advanced" → "Proceed to localhost (unsafe)" to continue
- The warning only appears during OAuth authorization

#### "Refresh token expired"

- Delete `./data/tokens/tokens.enc` and re-authenticate

#### SSL certificate issues

- Delete `./data/certs/` directory to regenerate certificates
- Ensure you have write permissions to the data directory

### Configuration & Connection Issues

#### "Cannot resolve hostname" or "nodename nor servname provided, or not known"

This DNS resolution error means the Worksection account URL cannot be resolved:

**Check your configuration:**

```bash
# Run validation to diagnose
uv run python scripts/validate_config.py
```

**Common causes:**

- Typo in `WORKSECTION_ACCOUNT_URL` in your `.env` file
- Missing or incorrect domain name (should be `https://yourcompany.worksection.com`)
- No internet connectivity
- Corporate firewall blocking DNS

**Fix:**

1. Verify the URL in your `.env` matches your actual Worksection account
2. Test DNS resolution: `nslookup yourcompany.worksection.com`
3. Check internet connectivity
4. Try alternative DNS servers (8.8.8.8, 1.1.1.1)

**Note:** With the new validation, this error is caught at startup with a clear message instead of during runtime.

#### "Validation errors" on startup

The server now validates all configuration at startup using Pydantic. If you see validation errors:

1. Check the error message - it tells you exactly what's wrong
2. Refer to `.env.example` for correct format
3. Common issues:
   - Client ID/Secret too short (minimum 8/16 characters)
   - Invalid redirect URI (must be HTTPS, except localhost)
   - Invalid scopes (see list in `.env.example`)
   - Port numbers out of range (1-65535)

### Rate Limiting

#### "429 Too Many Requests"

- The server automatically backs off and retries
- Worksection API limit: 1 request/second

### File Cache

#### "File too large"

- Increase `MAX_FILE_SIZE_MB` environment variable
- Default limit: 10MB

### API Constraints & Limitations

#### Worksection API Design

##### No Pagination Support

Most Worksection API endpoints return complete datasets without pagination:

- `get_users` - Returns ALL users in a single call
- `get_events` - Returns ALL events for the specified period
- `get_projects` - Returns ALL projects
- `get_all_tasks` - Returns ALL tasks across all projects
- `get_tasks` - Returns ALL tasks for a project
- `get_project_groups` - Returns ALL project folders

**Impact**: For large datasets, responses can exceed MCP's 1MB limit.

**Solution**: Tools with high data volume apply client-side truncation:

- `get_activity_log` - Auto-size truncation to fit under 1MB, default period `1d`
- `get_user_activity` - Auto-size truncation to fit under 1MB, default period `1d`
- `search_tasks` / `get_comments` - Default `max_results: 100` (configurable)

Truncated responses include metadata: `total_count`, `returned_count`, `truncated`,
`truncation_reason`.

For a comprehensive list of API limitations and workarounds, see
**[docs/API-LIMITATIONS.md](docs/API-LIMITATIONS.md)**.

For a client-facing summary of practical coverage, constraints, and expected
`PASS`/`PARTIAL` semantics, see
**[docs/CLIENT-CAPABILITIES.md](docs/CLIENT-CAPABILITIES.md)**.

##### Elevated Scope Requirements

Some endpoints require the `administrative` scope:

- `get_webhooks` - Webhook management
- Other administrative operations

Add `administrative` to `WORKSECTION_SCOPES` in `.env` to enable these tools.

#### MCP Protocol Constraints

##### Response Size Limit: 1MB

Error: `"Tool result is too large. Maximum size is 1MB."`

The Model Context Protocol enforces a 1MB maximum response size. This server handles
large responses automatically through client-side truncation with configurable limits.

#### Network & Security

##### Default Binding: 127.0.0.1

By default, the MCP server binds to `127.0.0.1` (localhost only) for security.

**Docker Deployment**: Set `MCP_SERVER_HOST=0.0.0.0` in docker-compose to make the
server accessible from the network.

See `.env.example` for configuration details

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## Support

- [GitHub Issues](https://github.com/pbv7/worksection-mcp/issues)
- [Worksection API Docs](https://worksection.com/en/faq/api-start.html)
- [MCP Documentation](https://modelcontextprotocol.io/)
