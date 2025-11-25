"""
SQLAlchemy ORM Models para persistência local de dados estruturados BSC.

Solução baseada em:
- LangGraph Persistence (Medium Set/2025)
- Streamlit + SQLite patterns (deeplink.kr Fev/2025)

ROI: Zero latency vs Mem0 eventual consistency (10 min)
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models (SQLAlchemy 2.0 style)."""

    pass


class ClientProfile(Base):
    """Profile básico do cliente (metadata, não dados completos Mem0)."""

    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    strategy_maps = relationship(
        "StrategyMap", back_populates="client", cascade="all, delete-orphan"
    )
    action_plans = relationship("ActionPlan", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClientProfile(user_id={self.user_id}, company={self.company_name})>"


class StrategyMap(Base):
    """Strategy Map com objectives e connections."""

    __tablename__ = "strategy_maps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("client_profiles.user_id"), nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    alignment_score = Column(Float)  # Score de alinhamento (0-100)

    # Dados estruturados (JSON para flexibilidade)
    objectives = Column(JSON, nullable=False)  # List[StrategicObjective]
    connections = Column(JSON, nullable=False)  # List[CauseEffectConnection]

    # Relationship
    client = relationship("ClientProfile", back_populates="strategy_maps")

    def __repr__(self):
        return f"<StrategyMap(user_id={self.user_id}, objectives={len(self.objectives)})>"


class ActionPlan(Base):
    """Action Plan com actions e timeline."""

    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("client_profiles.user_id"), nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Summary fields (para queries rápidas)
    total_actions = Column(Integer, default=0)
    high_priority_count = Column(Integer, default=0)
    timeline_summary = Column(String(500))

    # Dados estruturados (JSON para flexibilidade)
    actions = Column(JSON, nullable=False)  # List[ActionItem]
    by_perspective = Column(JSON)  # Dict[str, int] - contagem por perspectiva

    # Relationship
    client = relationship("ClientProfile", back_populates="action_plans")

    def __repr__(self):
        return f"<ActionPlan(user_id={self.user_id}, actions={self.total_actions})>"
