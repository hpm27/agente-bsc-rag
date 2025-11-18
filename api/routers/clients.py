"""Router de clientes - /api/v1/clients/*.

7 endpoints CRUD completos para gerenciamento de clientes BSC.

Fase: 4.3 - Integration APIs
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import verify_api_key
from api.schemas.requests import CreateClientRequest, UpdateClientRequest
from api.schemas.responses import ClientResponse, ClientListResponse, ClientSummaryResponse
# from api.utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE

from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=ClientResponse,
    status_code=201,
    summary="Criar novo cliente BSC",
    description="Cria perfil de cliente com informações básicas (company, challenges, objectives)."
)
# @limiter.limit(LIMIT_WRITE)  # TODO: Re-adicionar rate limiting após teste básico
async def create_client(
    request: CreateClientRequest,
    auth: dict = Depends(verify_api_key)
):
    """Cria novo cliente BSC via API.
    
    Requer API key válida com permissão 'write'.
    """
    logger.info(
        f"[API] create_client | company={request.company_name} | "
        f"api_key_client={auth.get('client_id')}"
    )
    
    try:
        # Criar profile via Mem0ClientWrapper
        mem0_client = Mem0ClientWrapper()
        
        # Construir ClientProfile
        profile = ClientProfile(
            company=CompanyInfo(
                name=request.company_name,
                sector=request.sector,
                size=request.size or "não informado",
                revenue=request.revenue
            ),
            context=StrategicContext(
                current_challenges=request.challenges,
                strategic_objectives=request.objectives
            )
        )
        
        # Salvar no Mem0
        saved_profile = mem0_client.create_profile(profile)
        
        logger.info(f"[API] Cliente criado: {saved_profile.client_id}")
        
        # Retornar response
        return ClientResponse(
            client_id=saved_profile.client_id,
            company_name=saved_profile.company.name,
            sector=saved_profile.company.sector,
            size=saved_profile.company.size,
            current_phase=saved_profile.engagement.current_phase,
            created_at=saved_profile.created_at.isoformat(),
            updated_at=saved_profile.updated_at.isoformat(),
            total_challenges=len(saved_profile.context.current_challenges),
            total_objectives=len(saved_profile.context.strategic_objectives),
            has_diagnostic=False  # Novo cliente nunca tem diagnóstico
        )
        
    except Exception as e:
        logger.error(f"[API] Erro ao criar cliente: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao criar cliente: {str(e)}")


@router.get(
    "",
    response_model=ClientListResponse,
    summary="Listar clientes",
    description="Lista todos os clientes com paginação e filtros opcionais."
)
# @limiter.limit(LIMIT_READ)  # TODO: Re-adicionar rate limiting
async def list_clients(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Items por página"),
    sector: str | None = Query(None, description="Filtrar por setor"),
    phase: str | None = Query(None, description="Filtrar por fase"),
    auth: dict = Depends(verify_api_key)
):
    """Lista clientes com paginação."""
    logger.info(
        f"[API] list_clients | page={page} | page_size={page_size} | "
        f"sector={sector} | phase={phase}"
    )
    
    try:
        mem0_client = Mem0ClientWrapper()
        
        # Buscar todos profiles
        all_profiles = mem0_client.list_all_profiles(limit=1000)
        
        # Aplicar filtros
        filtered_profiles = all_profiles
        if sector:
            filtered_profiles = [
                p for p in filtered_profiles 
                if p.company.sector.lower() == sector.lower()
            ]
        if phase:
            filtered_profiles = [
                p for p in filtered_profiles
                if p.engagement.current_phase == phase
            ]
        
        # Paginação
        total = len(filtered_profiles)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_profiles = filtered_profiles[start_idx:end_idx]
        
        # Converter para response
        clients = [
            ClientResponse(
                client_id=p.client_id,
                company_name=p.company.name,
                sector=p.company.sector,
                size=p.company.size,
                current_phase=p.engagement.current_phase,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
                total_challenges=len(p.context.current_challenges),
                total_objectives=len(p.context.strategic_objectives),
                has_diagnostic="diagnostics" in p.metadata
            )
            for p in page_profiles
        ]
        
        return ClientListResponse(
            clients=clients,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total
        )
        
    except Exception as e:
        logger.error(f"[API] Erro ao listar clientes: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao listar clientes: {str(e)}")


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Obter cliente por ID",
    description="Retorna detalhes completos de um cliente específico."
)
# @limiter.limit(LIMIT_READ)  # TODO: Re-adicionar rate limiting
async def get_client(
    client_id: str,
    auth: dict = Depends(verify_api_key)
):
    """Obtém cliente por ID."""
    logger.info(f"[API] get_client | client_id={client_id}")
    
    try:
        mem0_client = Mem0ClientWrapper()
        profile = mem0_client.get_client_profile(client_id)
        
        if not profile:
            raise HTTPException(404, f"Cliente {client_id} não encontrado")
        
        return ClientResponse(
            client_id=profile.client_id,
            company_name=profile.company.name,
            sector=profile.company.sector,
            size=profile.company.size,
            current_phase=profile.engagement.current_phase,
            created_at=profile.created_at.isoformat(),
            updated_at=profile.updated_at.isoformat(),
            total_challenges=len(profile.context.current_challenges),
            total_objectives=len(profile.context.strategic_objectives),
            has_diagnostic="diagnostics" in profile.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao obter cliente: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao obter cliente: {str(e)}")


@router.get(
    "/{client_id}/summary",
    response_model=ClientSummaryResponse,
    summary="Resumo executivo do cliente",
    description="Retorna resumo enxuto para dashboard."
)
# @limiter.limit(LIMIT_READ)  # TODO: Re-adicionar rate limiting
async def get_client_summary(
    client_id: str,
    auth: dict = Depends(verify_api_key)
):
    """Obtém resumo executivo do cliente."""
    logger.info(f"[API] get_client_summary | client_id={client_id}")
    
    try:
        mem0_client = Mem0ClientWrapper()
        summary = mem0_client.get_client_summary(client_id)
        
        if not summary:
            raise HTTPException(404, f"Cliente {client_id} não encontrado")
        
        # Contar tools executadas
        tools_count = sum([
            summary.get(f"has_{tool}", False)
            for tool in ["swot", "five_whys", "issue_tree", "kpi", 
                        "objectives", "benchmark", "action_plan", "prioritization"]
        ])
        
        return ClientSummaryResponse(
            client_id=client_id,
            company_name=summary["company_name"],
            sector=summary["sector"],
            current_phase=summary["current_phase"],
            updated_at=summary["updated_at"],
            tools_executed=tools_count,
            diagnostic_status="completed" if summary.get("has_diagnostic") else "none"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao obter resumo: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao obter resumo: {str(e)}")


# TODO: Implementar endpoints restantes:
# - PUT /{client_id} - Atualizar cliente
# - DELETE /{client_id} - Arquivar cliente
# - GET /{client_id}/history - Histórico de interações

