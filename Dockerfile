FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl

# Install Python dependencies using Poetry
COPY pyproject.toml poetry.lock ./
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${PATH}:/root/.local/bin"
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y libpq-dev

# Copy Python environment and app code
COPY --from=builder /usr/local /usr/local
COPY ./app /app/app
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh

# ✅ Copy the keys folder (fix for private.pem not found)
COPY ./app/keys /app/keys

RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]