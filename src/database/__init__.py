"""
Database package para persistência local SQLite de dados BSC estruturados.

Modules:
    - models: SQLAlchemy ORM models
    - database: Connection management
    - repository: CRUD operations
"""

from src.database.database import get_db, get_db_session, init_db
from src.database.models import ActionPlan, Base, ClientProfile, StrategyMap

__all__ = [
    "Base",
    "ClientProfile",
    "StrategyMap",
    "ActionPlan",
    "get_db",
    "get_db_session",
    "init_db",
]
