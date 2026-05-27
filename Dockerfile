# =============================================================================
# TelemetryFlow Python MCP Server - Dockerfile
# =============================================================================
#
# TelemetryFlow Python MCP Server - Community Enterprise Observability Platform (CEOP)
# Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
#
# Multi-stage build for minimal image size with CVE patching
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ARG VERSION=1.2.0
ARG GIT_COMMIT=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_TIME=unknown

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN pip install --upgrade pip build && \
    python -m build --wheel

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim

LABEL org.opencontainers.image.title="TelemetryFlow Python MCP Server" \
      org.opencontainers.image.description="MCP Server for TelemetryFlow with Claude AI integration and official MCP SDK" \
      org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.vendor="TelemetryFlow" \
      org.opencontainers.image.authors="Telemetri Data Indonesia <support@telemetryflow.id>" \
      org.opencontainers.image.url="https://telemetryflow.id" \
      org.opencontainers.image.documentation="https://docs.telemetryflow.id" \
      org.opencontainers.image.source="https://github.com/telemetryflow/telemetryflow-python-mcp" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.base.name="python:3.12-slim" \
      io.telemetryflow.product="TelemetryFlow Python MCP Server" \
      io.telemetryflow.component="telemetryflow-python-mcp" \
      io.telemetryflow.platform="CEOP"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TELEMETRYFLOW_ENDPOINT=api.telemetryflow.id:4317 \
    TELEMETRYFLOW_ENVIRONMENT=production

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && apt-get remove -y --purge perl \
    && apt-get autoremove -y --purge \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd -g 10001 telemetryflow && \
    useradd -u 10001 -g telemetryflow -d /home/telemetryflow -m telemetryflow

RUN mkdir -p /app && chown -R telemetryflow:telemetryflow /app

COPY --from=builder /build/dist/*.whl /tmp/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

COPY configs/ /app/configs/

RUN chown -R telemetryflow:telemetryflow /app

USER telemetryflow

WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["tfo-mcp"]
CMD ["serve"]
