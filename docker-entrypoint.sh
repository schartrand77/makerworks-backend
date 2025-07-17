#!/bin/bash
set -e

cd /app

exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app