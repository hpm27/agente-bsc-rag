"""Serviço de notificações para comunicação assíncrona com usuários.

Este serviço gerencia notificações sobre eventos críticos do workflow BSC,
armazenando-as no Mem0 para consulta posterior via API.

Features:
- Criação de notificações estruturadas (4 tipos de eventos)
- Armazenamento persistente no Mem0
- Marcação de leitura (unread → read)
- Busca e listagem com filtros (user_id, type, status, priority)
- Agregação de estatísticas (total não lidas, por prioridade)

Fase: 4.7 - Notification System
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

from mem0 import MemoryClient
import os

from src.memory.schemas import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Serviço para gerenciar notificações sobre eventos do workflow BSC.
    
    Armazena notificações no Mem0 com estrutura:
    - Memory Type: "notification"
    - Metadata: type, user_id, diagnostic_id, status, priority, created_at
    - Content: "{title}: {message}"
    
    Usage:
        service = NotificationService()
        notification_id = service.create_notification(notification)
        service.mark_as_read(notification_id)
        notifications = service.list_notifications(user_id="user_123")
    """
    
    def __init__(self, mem0_client: Optional[MemoryClient] = None):
        """Inicializa NotificationService.
        
        Args:
            mem0_client: MemoryClient do Mem0 (opcional, cria se None)
        """
        if mem0_client is None:
            api_key = os.getenv("MEM0_API_KEY")
            if not api_key:
                raise ValueError(
                    "MEM0_API_KEY não encontrada. Configure no .env ou passe mem0_client."
                )
            os.environ["MEM0_API_KEY"] = api_key
            self.client = MemoryClient()
        else:
            self.client = mem0_client
        
        logger.info("[NOTIFICATION] NotificationService inicializado")
    
    def create_notification(self, notification: Notification) -> str:
        """Cria e armazena notificação no Mem0.
        
        Args:
            notification: Instância de Notification a ser armazenada
            
        Returns:
            notification_id: ID único da notificação (notification.id)
            
        Raises:
            ValueError: Se notification for inválida
            Exception: Erros de comunicação com Mem0
            
        Example:
            >>> notification = Notification(
            ...     type="diagnostic_completed",
            ...     user_id="user_123",
            ...     title="Diagnóstico Pronto",
            ...     message="Seu diagnóstico BSC está disponível.",
            ...     priority="high"
            ... )
            >>> notification_id = service.create_notification(notification)
            >>> print(notification_id)
            notif_20251119143000_a1b2c3d4
        """
        try:
            logger.info(
                f"[NOTIFICATION] [CREATE] Criando notificação | "
                f"type={notification.type} | user_id={notification.user_id} | "
                f"priority={notification.priority}"
            )
            
            # Validar notification
            if not notification.user_id or len(notification.user_id) < 3:
                raise ValueError("user_id inválido (mín 3 caracteres)")
            
            if not notification.title or len(notification.title) < 5:
                raise ValueError("title inválido (mín 5 caracteres)")
            
            if not notification.message or len(notification.message) < 10:
                raise ValueError("message inválido (mín 10 caracteres)")
            
            # Preparar metadata para Mem0
            mem0_metadata = {
                "type": notification.type,
                "user_id": notification.user_id,
                "diagnostic_id": notification.diagnostic_id or "",
                "status": notification.status,
                "priority": notification.priority,
                "created_at": notification.created_at.isoformat(),
                "read_at": notification.read_at.isoformat() if notification.read_at else "",
                "notification_id": notification.id,
                **notification.metadata  # Merge metadata adicional
            }
            
            # Content: "TITLE: MESSAGE"
            mem0_content = f"{notification.title}: {notification.message}"
            
            # Adicionar ao Mem0
            response = self.client.add(
                messages=mem0_content,
                user_id=notification.user_id,
                metadata=mem0_metadata
            )
            
            # Aguardar eventual consistency do Mem0
            time.sleep(2)
            
            logger.info(
                f"[NOTIFICATION] [CREATE] [OK] Notificação criada | "
                f"id={notification.id} | mem0_id={response.get('id', 'N/A')}"
            )
            
            return notification.id
            
        except ValueError as e:
            logger.error(f"[NOTIFICATION] [CREATE] [ERRO] Validação falhou: {e}")
            raise
        except Exception as e:
            logger.error(
                f"[NOTIFICATION] [CREATE] [ERRO] Falha ao criar notificação: {e}",
                exc_info=True
            )
            raise
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Marca notificação como lida.
        
        Args:
            notification_id: ID da notificação a marcar como lida
            
        Returns:
            True se marcada com sucesso, False se não encontrada
            
        Raises:
            Exception: Erros de comunicação com Mem0
            
        Example:
            >>> service.mark_as_read("notif_20251119143000_a1b2c3d4")
            True
        """
        try:
            logger.info(f"[NOTIFICATION] [READ] Marcando como lida | id={notification_id}")
            
            # Buscar notificação pelo notification_id (custom metadata)
            filters = {
                "AND": [
                    {"notification_id": notification_id}
                ]
            }
            
            results = self.client.search(
                query="",
                filters=filters,
                limit=1
            )
            
            if not results or len(results) == 0:
                logger.warning(f"[NOTIFICATION] [READ] Notificação não encontrada | id={notification_id}")
                return False
            
            mem0_id = results[0].get("id")
            
            # Atualizar metadata
            updated_metadata = results[0].get("metadata", {})
            updated_metadata["status"] = "read"
            updated_metadata["read_at"] = datetime.now(timezone.utc).isoformat()
            
            self.client.update(
                memory_id=mem0_id,
                data=updated_metadata
            )
            
            logger.info(f"[NOTIFICATION] [READ] [OK] Marcada como lida | id={notification_id}")
            return True
            
        except Exception as e:
            logger.error(
                f"[NOTIFICATION] [READ] [ERRO] Falha ao marcar como lida: {e}",
                exc_info=True
            )
            raise
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Busca notificação por ID.
        
        Args:
            notification_id: ID da notificação
            
        Returns:
            Notification se encontrada, None caso contrário
            
        Example:
            >>> notification = service.get_notification("notif_20251119143000_a1b2c3d4")
            >>> print(notification.title if notification else "Não encontrada")
            Diagnóstico Pronto
        """
        try:
            logger.info(f"[NOTIFICATION] [GET] Buscando notificação | id={notification_id}")
            
            filters = {
                "AND": [
                    {"notification_id": notification_id}
                ]
            }
            
            results = self.client.search(
                query="",
                filters=filters,
                limit=1
            )
            
            if not results or len(results) == 0:
                logger.warning(f"[NOTIFICATION] [GET] Notificação não encontrada | id={notification_id}")
                return None
            
            # Reconstruir Notification do Mem0
            mem0_data = results[0]
            metadata = mem0_data.get("metadata", {})
            content = mem0_data.get("memory", "")
            
            # Parse content "TITLE: MESSAGE"
            if ": " in content:
                title, message = content.split(": ", 1)
            else:
                title = "Notificação"
                message = content
            
            notification = Notification(
                id=metadata.get("notification_id", notification_id),
                type=metadata.get("type", "error_occurred"),
                user_id=metadata.get("user_id", ""),
                diagnostic_id=metadata.get("diagnostic_id") or None,
                title=title,
                message=message,
                status=metadata.get("status", "unread"),
                priority=metadata.get("priority", "medium"),
                metadata={k: v for k, v in metadata.items() if k not in [
                    "type", "user_id", "diagnostic_id", "status", "priority",
                    "created_at", "read_at", "notification_id"
                ]},
                created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now(timezone.utc).isoformat())),
                read_at=datetime.fromisoformat(metadata.get("read_at")) if metadata.get("read_at") else None
            )
            
            logger.info(f"[NOTIFICATION] [GET] [OK] Notificação encontrada | id={notification_id}")
            return notification
            
        except Exception as e:
            logger.error(
                f"[NOTIFICATION] [GET] [ERRO] Falha ao buscar notificação: {e}",
                exc_info=True
            )
            return None
    
    def list_notifications(
        self,
        user_id: Optional[str] = None,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Notification]:
        """Lista notificações com filtros opcionais.
        
        Args:
            user_id: Filtrar por usuário
            type_filter: Filtrar por tipo de evento
            status_filter: Filtrar por status (unread/read)
            priority_filter: Filtrar por prioridade (high/medium/low)
            limit: Limite de resultados (1-1000)
            
        Returns:
            Lista de notificações ordenadas por created_at desc
            
        Example:
            >>> notifications = service.list_notifications(
            ...     user_id="user_123",
            ...     status_filter="unread",
            ...     priority_filter="high"
            ... )
            >>> len(notifications)
            3
        """
        try:
            logger.info(
                f"[NOTIFICATION] [LIST] Listando notificações | "
                f"user_id={user_id} | type={type_filter} | status={status_filter} | "
                f"priority={priority_filter} | limit={limit}"
            )
            
            # Construir filters Mem0
            filter_conditions = []
            
            if user_id:
                filter_conditions.append({"user_id": user_id})
            else:
                # Wildcard para listar todas
                filter_conditions.append({"user_id": "*"})
            
            if type_filter:
                filter_conditions.append({"type": type_filter})
            
            if status_filter:
                filter_conditions.append({"status": status_filter})
            
            if priority_filter:
                filter_conditions.append({"priority": priority_filter})
            
            filters = {"AND": filter_conditions} if filter_conditions else {"AND": [{"user_id": "*"}]}
            
            # Buscar no Mem0
            results = self.client.search(
                query="",
                filters=filters,
                limit=limit
            )
            
            if not results:
                logger.info("[NOTIFICATION] [LIST] Nenhuma notificação encontrada")
                return []
            
            # Reconstruir Notifications
            notifications = []
            for mem0_data in results:
                metadata = mem0_data.get("metadata", {})
                content = mem0_data.get("memory", "")
                
                # Parse content "TITLE: MESSAGE"
                if ": " in content:
                    title, message = content.split(": ", 1)
                else:
                    title = "Notificação"
                    message = content
                
                try:
                    notification = Notification(
                        id=metadata.get("notification_id", f"notif_{uuid4().hex[:8]}"),
                        type=metadata.get("type", "error_occurred"),
                        user_id=metadata.get("user_id", ""),
                        diagnostic_id=metadata.get("diagnostic_id") or None,
                        title=title,
                        message=message,
                        status=metadata.get("status", "unread"),
                        priority=metadata.get("priority", "medium"),
                        metadata={k: v for k, v in metadata.items() if k not in [
                            "type", "user_id", "diagnostic_id", "status", "priority",
                            "created_at", "read_at", "notification_id"
                        ]},
                        created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now(timezone.utc).isoformat())),
                        read_at=datetime.fromisoformat(metadata.get("read_at")) if metadata.get("read_at") else None
                    )
                    notifications.append(notification)
                except Exception as e:
                    logger.warning(f"[NOTIFICATION] [LIST] Ignorando notificação inválida: {e}")
                    continue
            
            # Ordenar por created_at desc (mais recentes primeiro)
            notifications.sort(key=lambda n: n.created_at, reverse=True)
            
            logger.info(f"[NOTIFICATION] [LIST] [OK] {len(notifications)} notificações retornadas")
            return notifications
            
        except Exception as e:
            logger.error(
                f"[NOTIFICATION] [LIST] [ERRO] Falha ao listar notificações: {e}",
                exc_info=True
            )
            return []
    
    def get_unread_count(self, user_id: str) -> int:
        """Conta notificações não lidas de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Número de notificações não lidas
            
        Example:
            >>> count = service.get_unread_count("user_123")
            >>> print(count)
            5
        """
        notifications = self.list_notifications(
            user_id=user_id,
            status_filter="unread"
        )
        return len(notifications)
    
    def get_stats_by_priority(self, user_id: str) -> Dict[str, int]:
        """Estatísticas de notificações por prioridade.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com contagem por prioridade {"high": 3, "medium": 5, "low": 2}
            
        Example:
            >>> stats = service.get_stats_by_priority("user_123")
            >>> print(stats)
            {'high': 3, 'medium': 5, 'low': 2}
        """
        notifications = self.list_notifications(user_id=user_id)
        
        stats = {"high": 0, "medium": 0, "low": 0}
        for notif in notifications:
            stats[notif.priority] += 1
        
        return stats


# Singleton para FastAPI dependency injection
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Retorna instância singleton de NotificationService.
    
    Usado como dependency em FastAPI endpoints:
        @router.post("/notifications")
        def create(service: NotificationService = Depends(get_notification_service)):
            ...
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

