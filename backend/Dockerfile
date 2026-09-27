# Multi-Stage Hardened Dockerfile for VECTIS Sentinel API
# Stage 1: Build & wheels generation with compilers
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal non-root runner without compilers
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/vectis/.local/bin:$PATH" \
    PORT=8000

# Install runtime utilities only (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root security principal (UID 10001)
RUN groupadd -g 10001 vectis && \
    useradd -u 10001 -g vectis -m -d /home/vectis -s /bin/bash vectis

# Copy python packages from builder to non-root user directory
COPY --from=builder --chown=vectis:vectis /root/.local /home/vectis/.local

# Copy application code
COPY --chown=vectis:vectis . /app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
