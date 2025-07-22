# ===== Builder stage =====
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl

# Install Poetry
COPY pyproject.toml poetry.lock ./
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${PATH}:/root/.local/bin"

# Install Python dependencies
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

# ===== Runtime stage =====
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies + Blender
RUN apt-get update && apt-get install -y \
    libpq-dev wget ca-certificates gnupg \
    && echo "deb http://archive.ubuntu.com/ubuntu jammy universe" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
        blender \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment & app code
COPY --from=builder /usr/local /usr/local
COPY ./app /app/app
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

# Expose FastAPI port
EXPOSE 8000

CMD ["/app/docker-entrypoint.sh"]
