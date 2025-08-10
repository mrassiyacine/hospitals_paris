## Builder Stage
FROM python:3.13-slim AS builder


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://astral.sh/uv/install.sh | bash

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY ./pyproject.toml .

RUN uv sync --no-dev


## Final Stage
FROM python:3.13-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser
USER appuser

WORKDIR /app

COPY /src src

COPY --from=builder /app/.venv .venv

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python","-m","uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]