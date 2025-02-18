FROM python:3.12-slim

WORKDIR /app

COPY requirements.setup.txt pyproject.toml uv.lock /app/
RUN python -m pip install --no-cache-dir -r requirements.setup.txt \
    && uv venv \
    && uv sync


COPY . /app

ENTRYPOINT ["uv", "run", "mcp-vertexai-search"]
