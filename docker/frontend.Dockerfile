FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

COPY . /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

RUN uv sync

ENV PORT=8501

EXPOSE $PORT

CMD streamlit run --server.port $PORT streamlit_app/src/Home.py
