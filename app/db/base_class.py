import os
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

database_url = os.getenv("DATABASE_URL", "")
if database_url.startswith("sqlite"):
    Base = declarative_base()
else:
    Base = declarative_base(metadata=MetaData(schema="public"))
