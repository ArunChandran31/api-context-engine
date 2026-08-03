from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine,
)


def get_db():
    """
    Database session dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
