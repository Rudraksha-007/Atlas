FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY alembic ./alembic
COPY alembic.ini ./
COPY app ./app
COPY main.py ./
COPY entrypoint.sh ./

RUN chmod +x /app/entrypoint.sh \
    && useradd --create-home --shell /usr/sbin/nologin atlas \
    && chown -R atlas:atlas /app
USER atlas

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
