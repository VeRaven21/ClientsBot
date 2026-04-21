FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY ./src /app

EXPOSE 8000

CMD ["uv", "run", "main.py"]