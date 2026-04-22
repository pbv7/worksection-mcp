# Worksection MCP Server - Multi-stage Dockerfile
# Optimized for minimal image size and security

# =============================================================================
# Stage 1: Builder - Install dependencies with uv
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install dependencies (production only)
RUN uv sync --frozen --no-dev --no-editable

# Copy source code
COPY src/ ./src/

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.14-slim AS runtime

# Labels
LABEL org.opencontainers.image.title="Worksection MCP Server"
LABEL org.opencontainers.image.description="Multi-tenant MCP server for Worksection with 40+ read-only tools"
LABEL org.opencontainers.image.vendor="Your Organization"
LABEL org.opencontainers.image.source="https://github.com/your-org/worksection-mcp"

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

WORKDIR /app

# Install runtime dependencies (for Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpng16-16 \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/src /app/src

# Create data directories with restricted permissions
RUN mkdir -p /app/data/tokens /app/data/files /app/data/certs /app/data/offload && \
    chown -R mcp:mcp /app/data && \
    chmod -R 700 /app/data

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

# Default environment variables (can be overridden)
ENV MCP_TRANSPORT=streamable-http
ENV MCP_SERVER_PORT=8000
ENV LOG_LEVEL=INFO
ENV TOKEN_STORAGE_PATH=/app/data/tokens
ENV FILE_CACHE_PATH=/app/data/files
ENV LARGE_RESPONSE_OFFLOAD_PATH=/app/data/offload
ENV LARGE_RESPONSE_OFFLOAD_ENABLED=true
ENV LARGE_RESPONSE_OFFLOAD_THRESHOLD_BYTES=50000
ENV LARGE_RESPONSE_MAX_READ_BYTES=50000

# Expose port for HTTP transport
EXPOSE 8000

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health', timeout=5); exit(0 if r.status_code == 200 else 1)" || exit 1

# Run the server
CMD ["python", "-m", "worksection_mcp"]
