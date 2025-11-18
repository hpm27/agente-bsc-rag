"""API Key Manager: CRUD de API keys no Redis.

Este módulo gerencia ciclo de vida de API keys:
- Criação de keys (bsc_live_* ou bsc_test_*)
- Validação de keys
- Listagem de keys ativas
- Revogação de keys

Fase: 4.3 - Integration APIs
"""

import hashlib
import logging
import secrets
from datetime import datetime
from typing import Literal

import redis.asyncio as aioredis
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger(__name__)


class APIKeyMetadata(BaseModel):
    """Metadata de uma API key."""
    
    api_key: str
    client_id: str | None = None
    tier: Literal["free", "professional", "enterprise"] = "free"
    permissions: list[str] = ["read", "write"]  # ou ["admin"]
    created_at: str
    created_by: str | None = None  # user_id que criou
    expires_at: str | None = None  # None = sem expiração
    is_active: bool = True
    rate_limit_overrides: dict | None = None  # Overrides por endpoint


class APIKeyManager:
    """Gerencia API keys no Redis."""
    
    def __init__(self, redis_client: aioredis.Redis | None = None):
        """Inicializa manager com Redis client.
        
        Args:
            redis_client: Redis client async (opcional, cria se None)
        """
        self.redis_client = redis_client
    
    async def _get_redis(self) -> aioredis.Redis:
        """Retorna Redis client (lazy loading)."""
        if self.redis_client is None:
            self.redis_client = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client
    
    def _generate_api_key(self, environment: Literal["live", "test"] = "live") -> str:
        """Gera API key segura.
        
        Formato: bsc_{environment}_{32_hex_chars}
        Exemplo: bsc_live_a1b2c3d4e5f6...
        
        Args:
            environment: "live" (produção) ou "test" (desenvolvimento)
        
        Returns:
            str: API key única e segura
        """
        # Gerar 32 bytes aleatórios (256 bits segurança)
        random_bytes = secrets.token_bytes(32)
        
        # Hash SHA256 para 64 caracteres hex
        hash_hex = hashlib.sha256(random_bytes).hexdigest()
        
        # Formato final
        api_key = f"bsc_{environment}_{hash_hex}"
        
        return api_key
    
    async def create_api_key(
        self,
        client_id: str | None = None,
        tier: Literal["free", "professional", "enterprise"] = "free",
        permissions: list[str] | None = None,
        environment: Literal["live", "test"] = "live",
        created_by: str | None = None
    ) -> APIKeyMetadata:
        """Cria nova API key e armazena no Redis.
        
        Args:
            client_id: ID do cliente BSC (opcional)
            tier: Nível do plano (free, professional, enterprise)
            permissions: Lista de permissões (default: ["read", "write"])
            environment: "live" ou "test"
            created_by: User ID que criou (para audit)
        
        Returns:
            APIKeyMetadata: Metadata da key criada
        
        Raises:
            ValueError: Se tier inválido
        """
        redis_client = await self._get_redis()
        
        # Gerar key única
        api_key = self._generate_api_key(environment)
        
        # Criar metadata
        metadata = APIKeyMetadata(
            api_key=api_key,
            client_id=client_id,
            tier=tier,
            permissions=permissions or ["read", "write"],
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            is_active=True
        )
        
        # Salvar no Redis (chave: api_key:{key}, valor: JSON metadata)
        await redis_client.set(
            f"api_key:{api_key}",
            metadata.model_dump_json(),
            ex=None  # Sem expiração (gerenciado por is_active)
        )
        
        logger.info(
            f"[API_KEY] Criada: {api_key[:20]}... | "
            f"client_id={client_id} | tier={tier} | env={environment}"
        )
        
        return metadata
    
    async def validate_api_key(self, api_key: str) -> APIKeyMetadata | None:
        """Valida API key e retorna metadata.
        
        Args:
            api_key: API key para validar
        
        Returns:
            APIKeyMetadata se válida, None se inválida/inexistente
        """
        redis_client = await self._get_redis()
        
        # Buscar no Redis
        metadata_json = await redis_client.get(f"api_key:{api_key}")
        
        if not metadata_json:
            return None
        
        # Parse JSON
        metadata = APIKeyMetadata.model_validate_json(metadata_json)
        
        # Verificar se ativa
        if not metadata.is_active:
            logger.warning(f"[API_KEY] Key revogada tentada: {api_key[:20]}...")
            return None
        
        # TODO: Verificar expiração se expires_at definido
        
        return metadata
    
    async def list_api_keys(
        self,
        client_id: str | None = None,
        tier: str | None = None,
        active_only: bool = True
    ) -> list[APIKeyMetadata]:
        """Lista API keys (com filtros opcionais).
        
        Args:
            client_id: Filtrar por cliente (opcional)
            tier: Filtrar por tier (opcional)
            active_only: Apenas keys ativas (default: True)
        
        Returns:
            list[APIKeyMetadata]: Lista de keys
        """
        redis_client = await self._get_redis()
        
        # Buscar todas keys (pattern: api_key:*)
        keys = []
        async for key in redis_client.scan_iter(match="api_key:*", count=100):
            metadata_json = await redis_client.get(key)
            if metadata_json:
                metadata = APIKeyMetadata.model_validate_json(metadata_json)
                
                # Aplicar filtros
                if active_only and not metadata.is_active:
                    continue
                if client_id and metadata.client_id != client_id:
                    continue
                if tier and metadata.tier != tier:
                    continue
                
                keys.append(metadata)
        
        return keys
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoga API key (soft delete - marca como inactive).
        
        Args:
            api_key: API key para revogar
        
        Returns:
            bool: True se revogada com sucesso, False se não encontrada
        """
        redis_client = await self._get_redis()
        
        # Buscar metadata
        metadata_json = await redis_client.get(f"api_key:{api_key}")
        
        if not metadata_json:
            return False
        
        # Atualizar is_active = False
        metadata = APIKeyMetadata.model_validate_json(metadata_json)
        metadata.is_active = False
        
        # Salvar no Redis
        await redis_client.set(
            f"api_key:{api_key}",
            metadata.model_dump_json()
        )
        
        logger.info(f"[API_KEY] Revogada: {api_key[:20]}... | client_id={metadata.client_id}")
        
        return True
    
    async def delete_api_key(self, api_key: str) -> bool:
        """Deleta API key permanentemente (hard delete).
        
        Args:
            api_key: API key para deletar
        
        Returns:
            bool: True se deletada, False se não encontrada
        """
        redis_client = await self._get_redis()
        
        deleted = await redis_client.delete(f"api_key:{api_key}")
        
        if deleted:
            logger.info(f"[API_KEY] Deletada permanentemente: {api_key[:20]}...")
        
        return bool(deleted)

