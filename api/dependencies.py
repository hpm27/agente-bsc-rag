"""Dependências FastAPI reutilizáveis (Auth, DB, Rate Limit).

Este módulo fornece dependencies para autenticação, rate limiting e acesso a recursos.
Usados via Depends() nos endpoints.

Fase: 4.3 - Integration APIs
"""

import logging

from fastapi import Header, HTTPException, Depends
import redis.asyncio as aioredis

from config.settings import settings

logger = logging.getLogger(__name__)


# Redis client global (lazy loading)
_redis_client = None


async def get_redis() -> aioredis.Redis:
    """Retorna Redis client (singleton lazy-loaded).
    
    Usado para rate limiting e caching de API keys.
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}",
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("[AUTH] Redis client conectado para rate limiting")
    
    return _redis_client


async def verify_api_key(
    x_api_key: str = Header(None, alias="X-API-Key")
) -> dict:
    """Valida API key e retorna metadata do cliente.
    
    Dependency para proteger endpoints autenticados.
    
    Args:
        x_api_key: API key no header X-API-Key
    
    Returns:
        dict: Metadata do cliente {client_id, permissions, tier}
    
    Raises:
        HTTPException 401: API key inválida ou ausente
    
    Usage:
        @app.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            pass
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Validar formato (bsc_live_* ou bsc_test_*)
    if not (x_api_key.startswith("bsc_live_") or x_api_key.startswith("bsc_test_")):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format. Must start with 'bsc_live_' or 'bsc_test_'",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Buscar metadata no Redis
    redis_client = await get_redis()
    key_metadata = await redis_client.get(f"api_key:{x_api_key}")
    
    if not key_metadata:
        logger.warning(f"[AUTH] API key inválida tentada: {x_api_key[:20]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Parse metadata (JSON string)
    import json
    metadata = json.loads(key_metadata)
    
    logger.info(
        f"[AUTH] API key validada: client_id={metadata.get('client_id')} | "
        f"tier={metadata.get('tier', 'free')}"
    )
    
    return metadata

