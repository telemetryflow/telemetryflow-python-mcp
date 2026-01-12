# TelemetryFlow Python MCP Server - Python Implementation
# Multi-stage build for minimal production image

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV for faster package management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Build wheel
RUN uv pip install --system build && \
    python -m build --wheel

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.12-slim as production

# Create non-root user
RUN groupadd -r telemetryflow && \
    useradd -r -g telemetryflow -d /app -s /sbin/nologin telemetryflow

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Copy configuration
COPY configs/ configs/

# Set ownership
RUN chown -R telemetryflow:telemetryflow /app

# Switch to non-root user
USER telemetryflow

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TFO_MCP_CONFIG=/app/configs/tfo-mcp.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Entry point
ENTRYPOINT ["tfo-mcp"]
CMD ["serve"]
