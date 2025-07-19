# MakerWorks Backend

This is the FastAPI + Celery + PostgreSQL backend powering the MakerWorks 3D printing platform.

## Features
- 🔐 JWT Auth, Signup, Login
- 🔧 Upload & STL metadata extraction
- 📸 Thumbnail rendering (Blender)
- 🎯 Redis queue + Celery for background jobs
- 📁 PostgreSQL via SQLAlchemy
- 🖼️ Avatar uploads via `/api/v1/users/avatar`

The repository ships with a `.env.example` file containing all the
environment variables required to run the application. Copy it to `.env`
and update the values for your environment.

## Dev Setup

```bash
python3 -m venv venv
source venv/bin/activate
poetry install  # installs dependencies defined in pyproject.toml
# alternatively, use `pip install -r requirements.txt`
cp .env.example .env
# edit .env and update the connection strings and secrets as needed
# `.env.example` lists all required environment variables
alembic upgrade head
uvicorn app.main:app --reload
```

## License
MIT
