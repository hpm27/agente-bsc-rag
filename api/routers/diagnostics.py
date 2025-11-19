"""Router de diagnósticos - /api/v1/diagnostics/*.

6 endpoints para gerenciamento de diagnósticos BSC.

Fase: 4.3 - Integration APIs
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request, Response

from api.dependencies import verify_api_key
from api.utils.rate_limit import limiter, LIMIT_READ, LIMIT_HEAVY
from api.schemas.requests import CreateDiagnosticRequest
from api.schemas.responses import (
    DiagnosticResponse,
    DiagnosticCompleteResponse,
    PerspectiveResponse
)

from src.agents.diagnostic_agent import DiagnosticAgent
from src.memory.mem0_client import Mem0ClientWrapper

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=DiagnosticResponse,
    status_code=202,
    summary="Criar diagnóstico BSC",
    description="Inicia diagnóstico BSC para um cliente. Pode ser síncrono ou assíncrono (webhook)."
)
@limiter.limit(LIMIT_HEAVY)
async def create_diagnostic(
    request: Request,
    response: Response,
    body: CreateDiagnosticRequest,
    background_tasks: BackgroundTasks,
    auth: dict = Depends(verify_api_key)
):
    """Cria novo diagnóstico BSC.
    
    Se async_mode=True, retorna imediatamente e envia resultado via webhook.
    Se async_mode=False, aguarda processamento completo (pode demorar 2-5 min).
    """
    logger.info(
        f"[API] create_diagnostic | client_id={body.client_id} | "
        f"async={body.async_mode}"
    )
    
    try:
        mem0_client = Mem0ClientWrapper()
        profile = mem0_client.get_client_profile(body.client_id)
        
        if not profile:
            raise HTTPException(404, f"Cliente {body.client_id} não encontrado")
        
        # Verificar se já existe diagnóstico
        if not body.force_regenerate and "diagnostics" in profile.metadata:
            raise HTTPException(
                400,
                "Cliente já possui diagnóstico. Use force_regenerate=true para re-gerar."
            )
        
        if body.async_mode:
            # Processar em background
            if not body.webhook_url:
                raise HTTPException(400, "webhook_url obrigatório para async_mode=true")
            
            # TODO: Implementar processamento async
            # background_tasks.add_task(process_diagnostic_async, body)
            
            return DiagnosticResponse(
                diagnostic_id=f"diag_{profile.client_id}",
                client_id=body.client_id,
                status="processing",
                created_at="2025-11-18T20:00:00Z",  # TODO: timestamp real
                webhook_configured=True
            )
        
        else:
            # Processar síncronamente
            diagnostic_agent = DiagnosticAgent()
            complete_diagnostic = await diagnostic_agent.run_diagnostic(profile)
            
            # Salvar diagnóstico no profile
            profile.metadata["diagnostics"] = complete_diagnostic.model_dump()
            mem0_client.save_profile(profile)
            
            logger.info(f"[API] Diagnóstico criado: {body.client_id}")
            
            return DiagnosticResponse(
                diagnostic_id=f"diag_{profile.client_id}",
                client_id=body.client_id,
                status="completed",
                created_at="2025-11-18T20:00:00Z",  # TODO: timestamp real
                webhook_configured=False
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao criar diagnóstico: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao criar diagnóstico: {str(e)}")


@router.get(
    "",
    response_model=List[DiagnosticCompleteResponse],
    summary="Listar diagnósticos",
    description="Lista todos os diagnósticos realizados."
)
@limiter.limit(LIMIT_READ)
async def list_diagnostics(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    auth: dict = Depends(verify_api_key)
):
    """Lista diagnósticos com paginação."""
    logger.info(f"[API] list_diagnostics | page={page} | page_size={page_size}")
    
    try:
        mem0_client = Mem0ClientWrapper()
        all_profiles = mem0_client.list_all_profiles(limit=1000)
        
        # Filtrar apenas profiles com diagnóstico
        profiles_with_diag = [
            p for p in all_profiles 
            if "diagnostics" in p.metadata
        ]
        
        # Paginação
        start = (page - 1) * page_size
        end = start + page_size
        page_profiles = profiles_with_diag[start:end]
        
        # Converter para response
        diagnostics = []
        for profile in page_profiles:
            diag_data = profile.metadata.get("diagnostics", {})
            diagnostics.append(
                DiagnosticCompleteResponse(
                    diagnostic_id=f"diag_{profile.client_id}",
                    client_id=profile.client_id,
                    executive_summary=diag_data.get("executive_summary", ""),
                    perspectives_analyzed=4,
                    recommendations_count=len(diag_data.get("recommendations", [])),
                    synergies_count=len(diag_data.get("synergies", [])),
                    created_at=profile.updated_at.isoformat()
                )
            )
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"[API] Erro ao listar diagnósticos: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao listar diagnósticos: {str(e)}")


@router.get(
    "/{diagnostic_id}",
    response_model=DiagnosticCompleteResponse,
    summary="Obter diagnóstico completo",
    description="Retorna diagnóstico BSC completo com todas perspectivas."
)
@limiter.limit(LIMIT_READ)
async def get_diagnostic(
    request: Request,
    response: Response,
    diagnostic_id: str,
    include_full: bool = Query(False, description="Incluir detalhes completos"),
    auth: dict = Depends(verify_api_key)
):
    """Obtém diagnóstico por ID."""
    logger.info(f"[API] get_diagnostic | id={diagnostic_id}")
    
    try:
        # Extrair client_id do diagnostic_id (formato: diag_{client_id})
        client_id = diagnostic_id.replace("diag_", "")
        
        mem0_client = Mem0ClientWrapper()
        profile = mem0_client.get_client_profile(client_id)
        
        if not profile or "diagnostics" not in profile.metadata:
            raise HTTPException(404, f"Diagnóstico {diagnostic_id} não encontrado")
        
        diag_data = profile.metadata["diagnostics"]
        
        response = DiagnosticCompleteResponse(
            diagnostic_id=diagnostic_id,
            client_id=client_id,
            executive_summary=diag_data.get("executive_summary", ""),
            perspectives_analyzed=4,
            recommendations_count=len(diag_data.get("recommendations", [])),
            synergies_count=len(diag_data.get("synergies", [])),
            created_at=profile.updated_at.isoformat()
        )
        
        if include_full:
            response.full_diagnostic = diag_data
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao obter diagnóstico: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao obter diagnóstico: {str(e)}")


# TODO: Implementar endpoints restantes:
# - GET /{diagnostic_id}/perspective/{name} - Perspectiva específica
# - GET /{diagnostic_id}/recommendations - Recomendações prioritárias
# - POST /{diagnostic_id}/regenerate - Re-gerar diagnóstico

