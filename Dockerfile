FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install uv \
    && uv pip install . --system

COPY . .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    SERVER_WORKERS=4 \
    SERVER_LOG_LEVEL=info \
    SERVER_RELOAD=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY orion ./orion

LABEL org.opencontainers.image.title="Orion" \
      org.opencontainers.image.description="Serviço de ingestão e processamento de dados de pesquisa" \
      org.opencontainers.image.vendor="Plumavir" \
      org.opencontainers.image.source="https://github.com/plumavir/orion"

ARG GIT_COMMIT
ENV GIT_COMMIT_SHA=$GIT_COMMIT

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/meta || exit 1

RUN groupadd -r -g 1001 orion \
    && useradd -r -u 1001 -g orion -s /bin/false -d /app orion \
    && chown -R orion:orion /app
USER orion

ENTRYPOINT ["python", "-m", "orion"]
