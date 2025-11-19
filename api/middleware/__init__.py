"""Middleware FastAPI para coleta de métricas e analytics.

Este módulo contém middleware customizado para interceptar requests
e coletar métricas de performance, uso e erros.

Fase: 4.4 - Advanced Analytics Dashboard
"""

from api.middleware.analytics import AnalyticsMiddleware

__all__ = ["AnalyticsMiddleware"]

