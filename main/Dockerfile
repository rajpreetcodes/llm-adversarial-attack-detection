FROM python:3.11-slim

WORKDIR /app

# uv for fast, locked dependency installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml README.md ./
COPY src ./src

# CPU-only torch first to avoid the multi-GB CUDA wheel
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system -e .

EXPOSE 8000

CMD ["uvicorn", "dgad.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
