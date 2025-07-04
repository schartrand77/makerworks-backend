import logging
import os
from app.db.database import engine

# Set logging configuration only once (avoid duplicate logs in Uvicorn workers)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("makerworks")
__version__ = os.getenv("API_VERSION", "0.1.0")

__all__ = ["logger", "__version__"]
