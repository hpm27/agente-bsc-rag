"""Configuração de rate limiting para FastAPI (SlowAPI + Redis).

Este módulo configura rate limiting baseado em Redis para proteção contra abuso.
Usa SlowAPI library (wrapper do limits library).

Fase: 4.3 - Integration APIs
"""

import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config.settings import settings

logger = logging.getLogger(__name__)


# Configurar Limiter (Redis-backed)
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit por IP
    storage_uri=f"redis://{settings.redis_host}:{settings.redis_port}",
    default_limits=["100/minute"],  # Default global (GET endpoints)
    enabled=True,
    headers_enabled=True,  # Retornar X-RateLimit-* headers
)


def rate_limit_exceeded_handler(request, exc: RateLimitExceeded):
    """Handler customizado para rate limit excedido.
    
    Retorna 429 + headers padrão RFC + mensagem em português.
    """
    logger.warning(
        f"[RATE_LIMIT] Limite excedido: {request.url.path} | "
        f"IP: {get_remote_address(request)}"
    )
    
    return _rate_limit_exceeded_handler(request, exc)


# Decorators reutilizáveis para tiers diferentes
# Usage: @limiter.limit(TIER_FREE)
TIER_FREE = "1000/day;100/hour;10/minute"  # Free tier
TIER_PROFESSIONAL = "100000/day;3000/hour;100/minute"  # Professional tier
TIER_ENTERPRISE = "unlimited"  # Enterprise tier (sem limite)

# Limites por tipo de operação
LIMIT_READ = "100/minute"  # GET endpoints (lista, busca)
LIMIT_WRITE = "30/minute"  # POST/PUT endpoints (criação, atualização)
LIMIT_HEAVY = "10/minute"  # Operações custosas (diagnóstico, reports)
LIMIT_ADMIN = "1000/minute"  # Endpoints admin (sem limite prático)


logger.info(
    f"[RATE_LIMIT] SlowAPI configurado | "
    f"Storage: redis://{settings.redis_host}:{settings.redis_port} | "
    f"Default: 100/minute"
)

