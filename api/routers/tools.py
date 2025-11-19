"""Router de ferramentas consultivas - /api/v1/tools/*.

9 endpoints para execução de ferramentas consultivas BSC:
- SWOT, Five Whys, Issue Tree, KPI Definer, Strategic Objectives, Benchmarking,
  Action Plan, Prioritization Matrix, List Tools

Fase: 4.3 - Integration APIs
"""

import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from api.dependencies import verify_api_key
from api.schemas.requests import (
    SwotRequest,
    FiveWhysRequest,
    ToolExecutionRequest,
    KpiDefinitionRequest,
)
from api.schemas.responses import (
    SwotResponse,
    FiveWhysResponse,
    KpiDefinitionResponse,
    ToolExecutionResponse,
    ToolsListResponse,
)
from api.utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE, LIMIT_HEAVY

from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import CompanyInfo, StrategicContext
from config.settings import get_llm

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_tool_agents():
    """Retorna instâncias dos 4 specialist agents para RAG."""
    from src.agents.financial_agent import FinancialAgent
    from src.agents.customer_agent import CustomerAgent
    from src.agents.process_agent import ProcessAgent
    from src.agents.learning_agent import LearningAgent
    
    return {
        "financial": FinancialAgent(),
        "customer": CustomerAgent(),
        "process": ProcessAgent(),
        "learning": LearningAgent(),
    }


def _get_client_profile(client_id: str) -> tuple[CompanyInfo, StrategicContext]:
    """Busca ClientProfile e retorna CompanyInfo e StrategicContext."""
    mem0_client = Mem0ClientWrapper()
    profile = mem0_client.get_client_profile(client_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID '{client_id}' não encontrado."
        )
    
    return profile.company, profile.context


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=ToolsListResponse,
    summary="Listar ferramentas disponíveis",
    description="Retorna lista de todas as ferramentas consultivas BSC disponíveis."
)
@limiter.limit(LIMIT_READ)
async def list_tools(
    request: Request,
    response: Response,
    auth: dict = Depends(verify_api_key)
):
    """Lista todas as ferramentas consultivas disponíveis."""
    logger.info("[API] list_tools")
    
    tools = [
        {
            "name": "swot",
            "display_name": "SWOT Analysis",
            "description": "Análise SWOT (Strengths, Weaknesses, Opportunities, Threats)",
            "endpoint": "/api/v1/tools/swot",
            "requires_problem_statement": False,
        },
        {
            "name": "five-whys",
            "display_name": "5 Whys (Root Cause Analysis)",
            "description": "Análise de causa raiz usando método 5 Porquês",
            "endpoint": "/api/v1/tools/five-whys",
            "requires_problem_statement": True,
        },
        {
            "name": "issue-tree",
            "display_name": "Issue Tree",
            "description": "Decomposição MECE de problemas complexos",
            "endpoint": "/api/v1/tools/issue-tree",
            "requires_problem_statement": True,
        },
        {
            "name": "kpi",
            "display_name": "KPI Definer",
            "description": "Definição de KPIs SMART para perspectivas BSC",
            "endpoint": "/api/v1/tools/kpi",
            "requires_problem_statement": False,
        },
        {
            "name": "objectives",
            "display_name": "Strategic Objectives",
            "description": "Definição de objetivos estratégicos balanceados",
            "endpoint": "/api/v1/tools/objectives",
            "requires_problem_statement": False,
        },
        {
            "name": "benchmarking",
            "display_name": "Benchmarking",
            "description": "Comparação com setor e concorrentes",
            "endpoint": "/api/v1/tools/benchmarking",
            "requires_problem_statement": False,
        },
        {
            "name": "action-plan",
            "display_name": "Action Plan",
            "description": "Criação de plano de ação estruturado",
            "endpoint": "/api/v1/tools/action-plan",
            "requires_problem_statement": False,
        },
        {
            "name": "prioritization",
            "display_name": "Prioritization Matrix",
            "description": "Matriz de priorização de ações estratégicas",
            "endpoint": "/api/v1/tools/prioritization",
            "requires_problem_statement": False,
        },
    ]
    
    return ToolsListResponse(tools=tools, total=len(tools))


@router.post(
    "/swot",
    response_model=SwotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Executar análise SWOT",
    description="Executa análise SWOT completa para um cliente BSC."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_swot(
    request: Request,
    response: Response,
    body: SwotRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa análise SWOT para um cliente."""
    logger.info(f"[API] execute_swot | client_id={body.client_id}")
    
    start_time = time.time()
    
    try:
        # Buscar ClientProfile
        company_info, strategic_context = _get_client_profile(body.client_id)
        
        # Instanciar ferramenta
        llm = get_llm()
        agents = _get_tool_agents()
        
        from src.tools.swot_analysis import SWOTAnalysisTool
        tool = SWOTAnalysisTool(
            llm=llm,
            financial_agent=agents["financial"],
            customer_agent=agents["customer"],
            process_agent=agents["process"],
            learning_agent=agents["learning"],
        )
        
        # Executar SWOT
        swot_result = tool.facilitate_swot(
            company_info=company_info,
            strategic_context=strategic_context,
            use_rag=True,
        )
        
        execution_time = time.time() - start_time
        
        # Construir response
        return SwotResponse(
            tool_output_id=f"swot_{int(time.time())}",
            tool_name="SWOT Analysis",
            client_id=body.client_id,
            status="completed",
            created_at=datetime.now().isoformat(),
            execution_time_seconds=round(execution_time, 2),
            strengths=swot_result.strengths,
            weaknesses=swot_result.weaknesses,
            opportunities=swot_result.opportunities,
            threats=swot_result.threats,
            strategic_recommendations=swot_result.strategic_recommendations or [],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao executar SWOT: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar análise SWOT: {str(e)}"
        )


@router.post(
    "/five-whys",
    response_model=FiveWhysResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Executar 5 Whys",
    description="Executa análise de causa raiz usando método 5 Porquês."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_five_whys(
    request: Request,
    response: Response,
    body: FiveWhysRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa análise 5 Whys para um problema específico."""
    logger.info(
        f"[API] execute_five_whys | client_id={body.client_id} | "
        f"problem={body.problem_statement[:50]}..."
    )
    
    start_time = time.time()
    
    try:
        # Buscar ClientProfile
        company_info, strategic_context = _get_client_profile(body.client_id)
        
        # Instanciar ferramenta
        llm = get_llm()
        agents = _get_tool_agents()
        
        from src.tools.five_whys import FiveWhysTool
        tool = FiveWhysTool(
            llm=llm,
            financial_agent=agents["financial"],
            customer_agent=agents["customer"],
            process_agent=agents["process"],
            learning_agent=agents["learning"],
        )
        
        # Executar 5 Whys
        five_whys_result = tool.facilitate_five_whys(
            company_info=company_info,
            strategic_context=strategic_context,
            problem_statement=body.problem_statement,
        )
        
        execution_time = time.time() - start_time
        
        # Construir whys_chain a partir das iterações
        whys_chain = []
        for i, iteration in enumerate(five_whys_result.iterations, 1):
            whys_chain.append({
                "why_number": i,
                "question": iteration.question,
                "answer": iteration.answer,
                "is_root_cause": iteration.is_root_cause,
            })
        
        # Construir response
        return FiveWhysResponse(
            tool_output_id=f"5whys_{int(time.time())}",
            tool_name="5 Whys (Root Cause Analysis)",
            client_id=body.client_id,
            status="completed",
            created_at=datetime.now().isoformat(),
            execution_time_seconds=round(execution_time, 2),
            problem_statement=body.problem_statement,
            root_causes=[five_whys_result.root_cause_summary] if five_whys_result.root_cause_summary else [],
            whys_chain=whys_chain,
            recommended_actions=five_whys_result.recommended_actions or [],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao executar 5 Whys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar análise 5 Whys: {str(e)}"
        )


@router.post(
    "/issue-tree",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Executar Issue Tree",
    description="Decompõe problema complexo em sub-problemas usando MECE."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_issue_tree(
    request: Request,
    response: Response,
    body: ToolExecutionRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa Issue Tree para decomposição de problema."""
    logger.info(f"[API] execute_issue_tree | client_id={body.client_id}")
    
    # TODO: Implementar IssueTreeTool quando disponível
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Issue Tree ainda não implementado. Em breve!"
    )


@router.post(
    "/kpi",
    response_model=KpiDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Definir KPIs",
    description="Define KPIs SMART para perspectivas BSC."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_kpi_definer(
    request: Request,
    response: Response,
    body: KpiDefinitionRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa definição de KPIs para um cliente."""
    logger.info(
        f"[API] execute_kpi_definer | client_id={body.client_id} | "
        f"perspective={body.perspective}"
    )
    
    start_time = time.time()
    
    try:
        # Buscar ClientProfile
        company_info, strategic_context = _get_client_profile(body.client_id)
        
        # Instanciar ferramenta
        llm = get_llm()
        agents = _get_tool_agents()
        
        from src.tools.kpi_definer import KPIDefinerTool
        tool = KPIDefinerTool(
            llm=llm,
            financial_agent=agents["financial"],
            customer_agent=agents["customer"],
            process_agent=agents["process"],
            learning_agent=agents["learning"],
        )
        
        # Executar KPI Definer
        kpi_result = tool.facilitate_kpi_definition(
            company_info=company_info,
            strategic_context=strategic_context,
            perspective=body.perspective,
        )
        
        execution_time = time.time() - start_time
        
        # Construir lista de KPIs
        kpis_list = []
        for kpi in kpi_result.kpis:
            kpis_list.append({
                "name": kpi.name,
                "description": kpi.description,
                "formula": kpi.formula or "",
                "target": kpi.target or "",
                "perspective": kpi.perspective,
            })
        
        # Construir response
        return KpiDefinitionResponse(
            tool_output_id=f"kpi_{int(time.time())}",
            tool_name="KPI Definer",
            client_id=body.client_id,
            status="completed",
            created_at=datetime.now().isoformat(),
            execution_time_seconds=round(execution_time, 2),
            perspective=body.perspective,
            kpis=kpis_list,
            total_kpis=len(kpis_list),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao executar KPI Definer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao definir KPIs: {str(e)}"
        )


@router.post(
    "/objectives",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Definir objetivos estratégicos",
    description="Define objetivos estratégicos balanceados para as 4 perspectivas BSC."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_strategic_objectives(
    request: Request,
    response: Response,
    body: ToolExecutionRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa definição de objetivos estratégicos."""
    logger.info(f"[API] execute_strategic_objectives | client_id={body.client_id}")
    
    start_time = time.time()
    
    try:
        # Buscar ClientProfile
        company_info, strategic_context = _get_client_profile(body.client_id)
        
        # Instanciar ferramenta
        llm = get_llm()
        agents = _get_tool_agents()
        
        from src.tools.strategic_objectives import StrategicObjectivesTool
        tool = StrategicObjectivesTool(
            llm=llm,
            financial_agent=agents["financial"],
            customer_agent=agents["customer"],
            process_agent=agents["process"],
            learning_agent=agents["learning"],
        )
        
        # Executar Strategic Objectives
        objectives_result = tool.facilitate_strategic_objectives(
            company_info=company_info,
            strategic_context=strategic_context,
        )
        
        execution_time = time.time() - start_time
        
        # Construir response (simplificado por enquanto)
        return ToolExecutionResponse(
            tool_output_id=f"objectives_{int(time.time())}",
            tool_name="Strategic Objectives",
            client_id=body.client_id,
            status="completed",
            created_at=datetime.now().isoformat(),
            execution_time_seconds=round(execution_time, 2),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao executar Strategic Objectives: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao definir objetivos estratégicos: {str(e)}"
        )


@router.post(
    "/benchmarking",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Executar benchmarking",
    description="Compara desempenho com setor e concorrentes."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_benchmarking(
    request: Request,
    response: Response,
    body: ToolExecutionRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa benchmarking para um cliente."""
    logger.info(f"[API] execute_benchmarking | client_id={body.client_id}")
    
    start_time = time.time()
    
    try:
        # Buscar ClientProfile
        company_info, strategic_context = _get_client_profile(body.client_id)
        
        # Instanciar ferramenta
        llm = get_llm()
        agents = _get_tool_agents()
        
        from src.tools.benchmarking_tool import BenchmarkingTool
        tool = BenchmarkingTool(
            llm=llm,
            financial_agent=agents["financial"],
            customer_agent=agents["customer"],
            process_agent=agents["process"],
            learning_agent=agents["learning"],
        )
        
        # Executar Benchmarking
        benchmarking_result = tool.facilitate_benchmarking(
            company_info=company_info,
            strategic_context=strategic_context,
        )
        
        execution_time = time.time() - start_time
        
        # Construir response (simplificado por enquanto)
        return ToolExecutionResponse(
            tool_output_id=f"benchmarking_{int(time.time())}",
            tool_name="Benchmarking",
            client_id=body.client_id,
            status="completed",
            created_at=datetime.now().isoformat(),
            execution_time_seconds=round(execution_time, 2),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao executar Benchmarking: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar benchmarking: {str(e)}"
        )


@router.post(
    "/action-plan",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar plano de ação",
    description="Cria plano de ação estruturado baseado em diagnóstico BSC."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_action_plan(
    request: Request,
    response: Response,
    body: ToolExecutionRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa criação de plano de ação."""
    logger.info(f"[API] execute_action_plan | client_id={body.client_id}")
    
    # TODO: Implementar ActionPlanTool quando disponível
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Action Plan ainda não implementado. Em breve!"
    )


@router.post(
    "/prioritization",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Matriz de priorização",
    description="Cria matriz de priorização de ações estratégicas."
)
@limiter.limit(LIMIT_HEAVY)
async def execute_prioritization(
    request: Request,
    response: Response,
    body: ToolExecutionRequest,
    auth: dict = Depends(verify_api_key)
):
    """Executa matriz de priorização."""
    logger.info(f"[API] execute_prioritization | client_id={body.client_id}")
    
    # TODO: Implementar PrioritizationMatrixTool quando disponível
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Prioritization Matrix ainda não implementado. Em breve!"
    )

