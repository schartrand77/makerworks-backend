# MakerWorks Backend

This is the FastAPI + Celery + PostgreSQL backend powering the MakerWorks 3D printing platform.

## Features
- 🔐 JWT Auth, Signup, Login
- 🔧 Upload & STL metadata extraction
- 📸 Thumbnail rendering (Blender)
- 🎯 Redis queue + Celery for background jobs
- 📁 PostgreSQL via SQLAlchemy
- 🖼️ Avatar uploads via `/api/v1/users/avatar`

## Dev Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # installs dependencies such as aiosqlite and authlib
cp .env.example .env
# edit .env and update the connection strings and secrets as needed
alembic upgrade head
uvicorn app.main:app --reload
```

## License
MIT
