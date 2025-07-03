# MakerWorks Backend

MakerWorks is a FastAPI-based backend that powers the MakerWorks 3D printing platform. It provides user authentication, model uploads and background processing via Celery workers.

## Features
- **JWT Authentication** for signup and login
- **Redis + Celery** queue for background tasks
- **STL analysis** and **thumbnail rendering** using Blender
- **PostgreSQL** database managed with SQLAlchemy and Alembic

## Getting Started

### Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Docker Compose
```bash
docker-compose up --build
```

Environment variables are documented in `.env.example` and loaded automatically via `app/config.py`.

## Project Layout
```
app/
  ├─ config/        # Settings and environment configuration
  ├─ routes/        # API route declarations
  ├─ models/        # SQLAlchemy models
  ├─ services/      # Business logic modules
  ├─ utils/         # Helper utilities
  └─ ...
```

## Contributing
Pull requests are welcome! For major changes please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.
