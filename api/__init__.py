"""Módulo API REST para sistema BSC RAG Consultant.

Este módulo fornece API REST enterprise-ready para acesso programático ao sistema
BSC RAG multi-agente.

Funcionalidades:
- REST endpoints (Clientes, Diagnósticos, Ferramentas, Reports)
- Autenticação API keys
- Rate limiting (Redis-backed)
- Webhooks para notificações assíncronas
- Documentação OpenAPI/Swagger auto-gerada

Uso:
    >>> uvicorn api.main:app --reload --port 8000

Fase: 4.3 - Integration APIs
Versão: 1.0
"""

__version__ = "1.0.0"
__all__ = []

