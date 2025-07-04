# MakerWorks Backend

MakerWorks is a FastAPI-based backend that powers the MakerWorks 3D printing platform. It provides user authentication, model uploads and background processing via Celery workers.

## Features
- **JWT Authentication** for signup and login
- **Redis + Celery** queue for background tasks
- **STL analysis** and **thumbnail rendering** using Blender
- **PostgreSQL** database managed with SQLAlchemy and Alembic
- **Outbound HTTP requests** handled via the `requests` library
- **GPU monitoring** powered by NVIDIA's `pynvml`

## Getting Started

### Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# installs requests, pynvml and all other dependencies
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Docker Compose
```bash
docker-compose up --build
```

Environment variables are documented in `.env.example` and loaded automatically via `app/config.py`.

### Unraid Installation

The repository includes a Docker template at `unraid/makerworks-backend.xml`.
Copy this file to `/boot/config/plugins/dockerMan/templates-user/` so it shows
up in the Unraid interface.

The container publishes port `8000` and stores uploads under
`/data/uploads`. Map this path to persistent storage (for example
`/mnt/user/appdata/makerworks/uploads`) and provide the environment variables
shown in `.env.example` such as `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB`, `REDIS_URL`, `CELERY_REDIS_URL` and `JWT_SECRET_KEY`.
`CELERY_REDIS_URL` defaults to `redis://redis:6379/0` if unset and controls the
Celery broker and result backend.

To pull and run the container through the **Community Apps** plugin:

1. Open the **Apps** tab and search for **MakerWorks Backend**.
2. Click **Install** to download the image using the template.
3. Review the environment variables and volume mappings, then apply the
   changes to start the container.

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
