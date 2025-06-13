import logging
import os

logger = logging.getLogger("makerworks")
__version__ = os.getenv("API_VERSION", "0.1.0")

__all__ = ["logger", "__version__"]