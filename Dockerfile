# syntax=docker/dockerfile:1.4

FROM python:3.11-slim

WORKDIR /app

# Install build tools and PostgreSQL headers for psycopg2 and similar packages
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        build-essential \
        gcc \
        libpq-dev \
    && pip install --upgrade pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose internal app port
EXPOSE 8000

# Run the FastAPI app via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]