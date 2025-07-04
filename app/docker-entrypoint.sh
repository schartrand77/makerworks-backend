#!/bin/bash
set -e

echo "📦 Running Alembic migrations..."
python scripts/upgrade.py || {
  echo "❌ Alembic migration failed"
  exit 1
}

echo "🚀 Starting MakerWorks API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
