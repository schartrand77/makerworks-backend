# MakerWorks Backend

This is the FastAPI + Celery + PostgreSQL backend powering the MakerWorks 3D printing platform.

## Features
- 🔐 JWT Auth, Signup, Login
- 🔧 Upload & STL metadata extraction
- 📸 Thumbnail rendering (Blender)
- 🎯 Redis queue + Celery for background jobs
- 📁 PostgreSQL via SQLAlchemy

## Dev Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## License
MIT
