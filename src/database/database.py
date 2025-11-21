"""
Database connection management para SQLite local.

Padrão baseado em SQLAlchemy best practices 2025.
"""

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base

# Database path (local storage)
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "bsc_data.db"

# SQLite connection string
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine configuration
# - check_same_thread=False: permite uso em diferentes threads (Streamlit)
# - pool_pre_ping=True: verifica conexão antes de usar
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL logging
)


# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints in SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database (create all tables)."""
    print(f"[INFO] Inicializando database em: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("[OK] Database inicializado com sucesso")


@contextmanager
def get_db_session() -> Session:
    """
    Context manager para sessões de database.

    Usage:
        with get_db_session() as db:
            client = db.query(ClientProfile).filter_by(user_id="abc").first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Session:
    """
    Get database session (for dependency injection).

    Usage (FastAPI style):
        def some_function(db: Session = Depends(get_db)):
            client = db.query(ClientProfile).first()
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
