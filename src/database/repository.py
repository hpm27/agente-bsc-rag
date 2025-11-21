"""
Repository pattern para CRUD operations em dados BSC.

Padrão baseado em:
- Repository Pattern (Domain-Driven Design)
- SQLAlchemy ORM best practices 2025
"""

import json
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from src.database.models import ActionPlan, ClientProfile, StrategyMap
from src.memory.schemas import (
    ActionItem,
    CauseEffectConnection,
    StrategicObjective,
)


class ClientProfileRepository:
    """Repository para ClientProfile."""

    @staticmethod
    def create(
        db: Session, user_id: str, company_name: str, sector: Optional[str] = None
    ) -> ClientProfile:
        """Criar novo client profile."""
        client = ClientProfile(user_id=user_id, company_name=company_name, sector=sector)
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def get_by_user_id(db: Session, user_id: str) -> Optional[ClientProfile]:
        """Buscar client por user_id."""
        return db.query(ClientProfile).filter(ClientProfile.user_id == user_id).first()

    @staticmethod
    def get_all(db: Session, limit: int = 100) -> List[ClientProfile]:
        """Listar todos os clients."""
        return db.query(ClientProfile).order_by(ClientProfile.created_at.desc()).limit(limit).all()

    @staticmethod
    def update(db: Session, user_id: str, **kwargs) -> Optional[ClientProfile]:
        """Atualizar client profile."""
        client = db.query(ClientProfile).filter(ClientProfile.user_id == user_id).first()
        if client:
            for key, value in kwargs.items():
                setattr(client, key, value)
            client.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(client)
        return client

    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        """Deletar client profile."""
        client = db.query(ClientProfile).filter(ClientProfile.user_id == user_id).first()
        if client:
            db.delete(client)
            db.commit()
            return True
        return False


class StrategyMapRepository:
    """Repository para StrategyMap."""

    @staticmethod
    def create(
        db: Session,
        user_id: str,
        objectives: List[StrategicObjective],
        connections: List[CauseEffectConnection],
        alignment_score: Optional[float] = None,
    ) -> StrategyMap:
        """Criar novo strategy map."""
        # Converter Pydantic models para JSON
        objectives_json = [obj.model_dump() for obj in objectives]
        connections_json = [conn.model_dump() for conn in connections]

        strategy_map = StrategyMap(
            user_id=user_id,
            objectives=objectives_json,
            connections=connections_json,
            alignment_score=alignment_score,
        )
        db.add(strategy_map)
        db.commit()
        db.refresh(strategy_map)
        return strategy_map

    @staticmethod
    def get_by_user_id(db: Session, user_id: str) -> Optional[StrategyMap]:
        """Buscar strategy map mais recente de um user."""
        return (
            db.query(StrategyMap)
            .filter(StrategyMap.user_id == user_id)
            .order_by(StrategyMap.created_at.desc())
            .first()
        )

    @staticmethod
    def get_all_by_user_id(db: Session, user_id: str) -> List[StrategyMap]:
        """Buscar todos strategy maps de um user (histórico)."""
        return (
            db.query(StrategyMap)
            .filter(StrategyMap.user_id == user_id)
            .order_by(StrategyMap.created_at.desc())
            .all()
        )

    @staticmethod
    def update(db: Session, strategy_map_id: int, **kwargs) -> Optional[StrategyMap]:
        """Atualizar strategy map."""
        strategy_map = db.query(StrategyMap).filter(StrategyMap.id == strategy_map_id).first()
        if strategy_map:
            for key, value in kwargs.items():
                setattr(strategy_map, key, value)
            strategy_map.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(strategy_map)
        return strategy_map

    @staticmethod
    def delete(db: Session, strategy_map_id: int) -> bool:
        """Deletar strategy map."""
        strategy_map = db.query(StrategyMap).filter(StrategyMap.id == strategy_map_id).first()
        if strategy_map:
            db.delete(strategy_map)
            db.commit()
            return True
        return False


class ActionPlanRepository:
    """Repository para ActionPlan."""

    @staticmethod
    def create(
        db: Session,
        user_id: str,
        actions: List[ActionItem],
        total_actions: int,
        high_priority_count: int,
        timeline_summary: str,
        by_perspective: Optional[dict] = None,
    ) -> ActionPlan:
        """Criar novo action plan."""
        # Converter Pydantic models para JSON
        actions_json = [action.model_dump() for action in actions]

        action_plan = ActionPlan(
            user_id=user_id,
            actions=actions_json,
            total_actions=total_actions,
            high_priority_count=high_priority_count,
            timeline_summary=timeline_summary,
            by_perspective=by_perspective or {},
        )
        db.add(action_plan)
        db.commit()
        db.refresh(action_plan)
        return action_plan

    @staticmethod
    def get_by_user_id(db: Session, user_id: str) -> Optional[ActionPlan]:
        """Buscar action plan mais recente de um user."""
        return (
            db.query(ActionPlan)
            .filter(ActionPlan.user_id == user_id)
            .order_by(ActionPlan.created_at.desc())
            .first()
        )

    @staticmethod
    def get_all_by_user_id(db: Session, user_id: str) -> List[ActionPlan]:
        """Buscar todos action plans de um user (histórico)."""
        return (
            db.query(ActionPlan)
            .filter(ActionPlan.user_id == user_id)
            .order_by(ActionPlan.created_at.desc())
            .all()
        )

    @staticmethod
    def update(db: Session, action_plan_id: int, **kwargs) -> Optional[ActionPlan]:
        """Atualizar action plan."""
        action_plan = db.query(ActionPlan).filter(ActionPlan.id == action_plan_id).first()
        if action_plan:
            for key, value in kwargs.items():
                setattr(action_plan, key, value)
            action_plan.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(action_plan)
        return action_plan

    @staticmethod
    def delete(db: Session, action_plan_id: int) -> bool:
        """Deletar action plan."""
        action_plan = db.query(ActionPlan).filter(ActionPlan.id == action_plan_id).first()
        if action_plan:
            db.delete(action_plan)
            db.commit()
            return True
        return False


# Facade para simplificar uso
class BSCRepository:
    """Facade pattern para acesso aos repositories."""

    def __init__(self, db: Session):
        self.db = db
        self.clients = ClientProfileRepository()
        self.strategy_maps = StrategyMapRepository()
        self.action_plans = ActionPlanRepository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()
