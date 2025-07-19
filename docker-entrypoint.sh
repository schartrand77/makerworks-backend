#!/bin/bash
set -e

cd /app

# Listen on 0.0.0.0 so it’s reachable from host
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
