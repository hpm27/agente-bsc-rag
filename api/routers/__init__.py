"""Routers FastAPI para API BSC RAG.

Exporta todos os routers para registro no main.py.

Fase: 4.3 - Integration APIs
"""

from api.routers import clients  # noqa: F401

# TODO: Importar outros routers quando implementados
# from api.routers import diagnostics, tools, reports, webhooks

__all__ = ["clients"]
