#!/bin/bash
set -euo pipefail

cd /app

# Start the FastAPI app with Gunicorn + Uvicorn workers
exec gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    app.main:app
