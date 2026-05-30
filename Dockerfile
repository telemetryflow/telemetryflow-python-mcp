# =============================================================================
# TelemetryFlow Python MCP Server - Dockerfile
# =============================================================================
#
# TelemetryFlow Python MCP Server - Community Enterprise Observability Platform (CEOP)
# Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
#
# Multi-stage build for minimal image size with aggressive CVE patching.
# Uses Debian Trixie (13) base for patched system libraries (zlib 1.3.1,
# sqlite3 3.46+, ncurses 6.5, PAM 1.7) and strips attack-surface packages.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Build wheel and install into isolated prefix
# -----------------------------------------------------------------------------
FROM python:3.13-slim-trixie AS builder

ARG VERSION=1.2.0
ARG GIT_COMMIT=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_TIME=unknown

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN pip install --upgrade pip build && \
    python -m build --wheel

# Install into install prefix (no pip in final image)
RUN pip install --prefix=/install --no-cache-dir /build/dist/*.whl

# -----------------------------------------------------------------------------
# Stage 2: Runtime (distroless-like minimal image)
# -----------------------------------------------------------------------------
FROM python:3.13-slim-trixie

LABEL org.opencontainers.image.title="TelemetryFlow Python MCP Server" \
      org.opencontainers.image.description="MCP Server for TelemetryFlow with Claude AI integration and official MCP SDK" \
      org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.vendor="TelemetryFlow" \
      org.opencontainers.image.authors="Telemetri Data Indonesia <support@telemetryflow.id>" \
      org.opencontainers.image.url="https://telemetryflow.id" \
      org.opencontainers.image.documentation="https://docs.telemetryflow.id" \
      org.opencontainers.image.source="https://github.com/telemetryflow/telemetryflow-python-mcp" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.base.name="python:3.13-slim-trixie" \
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
    apt-get dist-upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN dpkg --remove --force-remove-essential --force-depends \
       perl-base \
       libperl5.40 \
       perl-modules-5.40 \
       ncurses-bin \
       libncurses6 \
       libncursesw6 \
       ncurses-base \
       libtinfo6 \
       gnupg \
       gnupg-utils \
       gpg \
       gpgv \
       gpg-wks-client \
       gpg-wks-server \
       dirmngr \
       libldap-common \
       libldap-2.5-0 \
       libcurl4 \
       curl \
       binutils \
       binutils-common \
       libbinutils \
       libctf0 \
       libctf-nobfd0 \
    || true

RUN apt-get autoremove -y --purge 2>/dev/null || true \
    && apt-get clean 2>/dev/null || true \
    && rm -rf \
       /var/lib/apt/lists/* \
       /tmp/* \
       /var/tmp/* \
       /usr/share/doc/* \
       /usr/share/man/* \
       /usr/share/info/* \
       /var/log/* \
       /var/cache/* \
       /usr/lib/*/libgcrypt* \
       /usr/lib/*/libsasl2*

RUN groupadd -g 10001 telemetryflow && \
    useradd -u 10001 -g telemetryflow -d /home/telemetryflow -m telemetryflow

RUN mkdir -p /app && chown -R telemetryflow:telemetryflow /app

# Copy pre-installed packages from builder (no pip needed in runtime)
COPY --from=builder /install /usr/local

COPY configs/ /app/configs/

RUN chown -R telemetryflow:telemetryflow /app

USER telemetryflow

WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["tfo-mcp"]
CMD ["serve"]
