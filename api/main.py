"""FastAPI application principal - BSC RAG Consultant API.

Este módulo configura o FastAPI app com:
- CORS
- OpenAPI metadata
- Routers (clientes, diagnostics, tools, reports, webhooks)
- Middleware logging e error handling
- Health check endpoint

Fase: 4.3 - Integration APIs
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Lifespan context manager (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifecycle events para FastAPI app."""
    # Startup
    logger.info("[API] Iniciando BSC RAG Consultant API...")
    logger.info(f"[API] Versão: {app.version}")
    logger.info(f"[API] Ambiente: {'PROD' if not settings.DEBUG else 'DEV'}")
    
    # TODO: Conectar Redis para rate limiting
    # TODO: Verificar Mem0 connection
    
    yield
    
    # Shutdown
    logger.info("[API] Encerrando API...")


# Criar FastAPI app
app = FastAPI(
    title="BSC RAG Consultant API",
    description=(
        "API REST enterprise-ready para sistema consultor BSC multi-agente. "
        "Fornece acesso programático a diagnósticos BSC, ferramentas consultivas, "
        "e gerenciamento de clientes."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check e status da API"
        },
        {
            "name": "clients",
            "description": "Operações com clientes BSC (CRUD completo)"
        },
        {
            "name": "diagnostics",
            "description": "Diagnósticos BSC multi-perspectiva"
        },
        {
            "name": "tools",
            "description": "Ferramentas consultivas (SWOT, Five Whys, KPI, etc)"
        },
        {
            "name": "reports",
            "description": "Exports PDF e CSV"
        },
        {
            "name": "webhooks",
            "description": "Notificações assíncronas e gerenciamento de webhooks"
        },
        {
            "name": "admin",
            "description": "Endpoints administrativos (API keys, metrics)"
        }
    ]
)


# Configurar CORS
origins = [
    "http://localhost:8501",  # Streamlit local
    "http://localhost:3000",  # Frontend local típico
]

if not settings.DEBUG:
    # Produção: adicionar domínios confiáveis
    origins.append("https://app.engelar.eng.br")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint (sem autenticação)
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint para monitoramento.
    
    Retorna status da API e dependências (Redis, Mem0).
    """
    return {
        "status": "ok",
        "version": app.version,
        "environment": "production" if not settings.DEBUG else "development"
    }


# Root endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint com informações da API."""
    return {
        "message": "BSC RAG Consultant API",
        "version": app.version,
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers globais
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handler para 404 Not Found."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} não encontrado",
            "docs": "/docs"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handler para 500 Internal Server Error."""
    logger.error(f"[API] Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Erro interno no servidor. Contate o suporte."
        }
    )


# TODO: Registrar routers
# from api.routers import clients, diagnostics, tools, reports, webhooks
# app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
# app.include_router(diagnostics.router, prefix="/api/v1/diagnostics", tags=["diagnostics"])
# app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
# app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
# app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

