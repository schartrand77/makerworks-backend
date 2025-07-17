# ─── Build Stage ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  libpq-dev \
  curl \
  libjpeg-dev \
  zlib1g-dev \
  libmagic1 \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY pyproject.toml poetry.lock ./

# Configure Poetry and install only runtime dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --only=main

# ─── Runtime Stage ───────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime libraries
RUN apt-get update && apt-get install -y \
  libpq-dev \
  libjpeg-dev \
  zlib1g-dev \
  libmagic1 \
  && rm -rf /var/lib/apt/lists/*

# Set PYTHONPATH to /app so `from app.xxx` works
ENV PYTHONPATH=/app

# Copy Python + Poetry deps from build stage
COPY --from=builder /usr/local /usr/local

# Copy application source code into /app directly
COPY ./app /app

# Ensure required runtime directories exist
RUN mkdir -p /app/uploads /app/keys \
  && chmod -R 700 /app/keys

# Optional: uncomment if you want to include a private key
# COPY app/keys/private.pem /app/keys/private.pem

# Expose API port
EXPOSE 8000

# Optional: add container healthcheck
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/status || exit 1

# Run Gunicorn with Uvicorn worker
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]