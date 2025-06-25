# ────── Stage 1: Build ──────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install Python deps early for caching
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# ────── Stage 2: Runtime ──────
FROM python:3.11-slim

WORKDIR /app

# Copy code and installed site-packages from builder
COPY --from=builder /app /app

# Create runtime folders
RUN mkdir -p /app/uploads /app/keys

# Copy static frontend build
COPY ./frontend/dist /usr/share/nginx/html

# Copy NGINX config
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Copy private key (during dev; mount in prod)
COPY ./keys/private.pem ./keys/public.pem /app/keys/

# Install NGINX and runtime dependencies
RUN apt-get update && apt-get install -y nginx curl && rm -rf /var/lib/apt/lists/*

# Uvicorn will serve FastAPI backend
EXPOSE 8000
EXPOSE 80

# Copy entrypoint
COPY ./start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]