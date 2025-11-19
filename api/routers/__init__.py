"""Routers FastAPI para API BSC RAG.

Exporta todos os routers para registro no main.py.

Fase: 4.3 - Integration APIs
"""

from api.routers import clients  # noqa: F401
from api.routers import diagnostics  # noqa: F401
from api.routers import tools  # noqa: F401
from api.routers import reports  # noqa: F401
from api.routers import webhooks  # noqa: F401
from api.routers import analytics  # noqa: F401
from api.routers import feedback  # noqa: F401

__all__ = ["clients", "diagnostics", "tools", "reports", "webhooks", "analytics", "feedback"]
