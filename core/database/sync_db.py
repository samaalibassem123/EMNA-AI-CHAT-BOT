from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,  # SQLAlchemy 2.x style
    pool_pre_ping=True,  # important for SQL Server
)

session = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)