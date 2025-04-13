FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

COPY . /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

RUN uv sync

ENV PORT=8000

EXPOSE $PORT

CMD uv run fastapi run --port $PORT fastapi_backend/src/main.py
