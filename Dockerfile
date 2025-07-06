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

# Configure Poetry and install only runtime deps
RUN poetry config virtualenvs.create false \
  && poetry install --only=main

# ─── Runtime Stage ───────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install runtime libraries only
RUN apt-get update && apt-get install -y \
  libpq-dev \
  libjpeg-dev \
  zlib1g-dev \
  libmagic1 \
  && rm -rf /var/lib/apt/lists/*

# Copy Python + Poetry deps from build stage
COPY --from=builder /usr/local /usr/local

# Copy application source code
COPY . .

# Ensure required runtime directories exist
RUN mkdir -p /app/uploads /app/keys \
  && chmod -R 700 /app/keys

# Copy RSA private key into image (adjust path if needed)
# Optional: uncomment this if you keep a key in the repo
# COPY app/keys/private.pem /app/keys/private.pem

# Expose API port
EXPOSE 8000

# Run Gunicorn with Uvicorn worker
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]