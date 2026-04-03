from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,  # SQLAlchemy 2.x style
    poolclass=QueuePool,
    pool_size=5,  # number of connections to keep in pool
    max_overflow=10,  # max overflow connections beyond pool_size
    pool_pre_ping=True,  # check connection health before using
    pool_recycle=3600,  # recycle connections after 1 hour
)

Session = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_session():
    """Create a new database session."""
    return Session()