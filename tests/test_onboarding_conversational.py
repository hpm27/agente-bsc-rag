"""
Testes para Onboarding Conversacional - FASE 1 Opportunistic Extraction.

Testa novo fluxo adaptativo com _extract_all_entities() e collect_client_info().
Criado: 2025-10-20 (Refatoração FASE 1)

Cobertura:
- F1-TEST-1 a F1-TEST-5: _extract_all_entities()
- F1-TEST-6 a F1-TEST-10: collect_client_info()
- F1-TEST-11 a F1-TEST-15: Integração prompts
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config.settings import settings
from src.agents.onboarding_agent import OnboardingAgent
from src.graph.consulting_states import ConsultingPhase
from src.graph.states import BSCState
from src.memory.schemas import ClientProfile, CompanyInfo


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM para testes sem custo de API."""
    llm = AsyncMock()
    llm.model_name = "gpt-4o-mini"
    return llm


@pytest.fixture
def mock_profile_agent():
    """Mock ClientProfileAgent."""
    agent = MagicMock()
    agent.extract_company_info = MagicMock()
    agent.identify_challenges = MagicMock()
    agent.define_objectives = MagicMock()
    return agent


@pytest.fixture
def mock_memory_client():
    """Mock Mem0ClientWrapper."""
    memory = MagicMock()
    memory.add = MagicMock()
    memory.search = MagicMock(return_value=[])
    memory.get_all = MagicMock(return_value=[])
    return memory


@pytest.fixture
def valid_company_info():
    """Fixture CompanyInfo válida com margem +20% segurança.
    
    Aplicando CHECKLIST [[memory:9969868]] PONTO 15.6:
    - name: min_length=2 → usar 3+ chars (margem +50%)
    - sector: obrigatório
    - size: obrigatório, default="média"
    - founded_year: 1800-2025 (validado)
    """
    return CompanyInfo(
        name="TechCorp Brasil",  # 16 chars (>>2 min)
        sector="Tecnologia",
        size="média",
        industry="Software empresarial",
        founded_year=2020  # Dentro de 1800-2025
    )


@pytest.fixture
def valid_client_profile(valid_company_info):
    """Fixture ClientProfile válida.
    
    ClientProfile tem:
    - company: CompanyInfo (obrigatório com default factory)
    - context: StrategicContext (default factory)
    - engagement: EngagementState (default factory)
    - diagnostics: Optional[DiagnosticData] = None
    """
    profile = ClientProfile()
    profile.company = valid_company_info
    return profile


@pytest.fixture
def valid_bsc_state(valid_client_profile):
    """Fixture BSCState válida para testes onboarding.
    
    BSCState principal usa:
    - query: str (obrigatório)
    - client_profile: ClientProfile | None (default None)
    - onboarding_progress: dict (default {})
    - partial_profile: dict (adicionado FASE 1, não está no schema original)
    """
    state = BSCState(
        query="Quero implementar BSC na minha empresa",
        session_id="test_session_123",
        user_id="user_test_456",
        client_profile=valid_client_profile,
        current_phase=ConsultingPhase.ONBOARDING,
        onboarding_progress={
            "current_step": 1,
            "followup_counts": {1: 0, 2: 0, 3: 0},
            "company_info": False,
            "challenges": False,
            "objectives": False,
        }
    )
    # Adicionar partial_profile em metadata (campo dinâmico FASE 1)
    state.metadata["partial_profile"] = {
        "company_name": None,
        "industry": None,
        "size": None,
        "revenue": None,
        "challenges": [],
        "goals": [],
        "timeline": None,
        "budget": None,
        "location": None,
    }
    return state


@pytest.fixture
def onboarding_agent(mock_llm, mock_profile_agent, mock_memory_client):
    """Fixture OnboardingAgent configurado."""
    return OnboardingAgent(
        llm=mock_llm,
        client_profile_agent=mock_profile_agent,
        memory_client=mock_memory_client,
        max_followups_per_step=2
    )


# ============================================================================
# F1-TEST-1 a F1-TEST-5: _extract_all_entities()
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_entities_complete_extraction(onboarding_agent, mock_llm):
    """F1-TEST-1: Extração completa com todas entidades presentes."""
    # Mock LLM response com JSON completo
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "entities": {
            "company_name": "TechCorp Brasil",
            "industry": "Tecnologia",
            "size": "startup",
            "revenue": "R$ 3 milhões ao ano",
            "challenges": ["Crescimento lento", "Falta de capital"],
            "goals": ["Crescer 50% em receita"],
            "timeline": "12 meses",
            "budget": None,
            "location": "São Paulo"
        },
        "confidence_scores": {
            "company_name": 1.0,
            "industry": 0.9,
            "size": 1.0,
            "revenue": 1.0,
            "challenges": 1.0,
            "goals": 1.0,
            "timeline": 1.0,
            "budget": 0.0,
            "location": 1.0
        }
    })
    mock_llm.ainvoke.return_value = mock_response
    
    # Executar extração
    user_text = (
        "Sou da TechCorp Brasil, startup de software com 30 funcionários em São Paulo. "
        "Faturamos cerca de R$ 3 milhões ao ano. "
        "Nossos principais desafios são crescimento lento e falta de capital. "
        "Queremos crescer 50% em receita nos próximos 12 meses."
    )
    
    result = await onboarding_agent._extract_all_entities(user_text)
    
    # Validações
    assert "entities" in result
    assert "confidence_scores" in result
    
    entities = result["entities"]
    assert entities["company_name"] == "TechCorp Brasil"
    assert entities["industry"] == "Tecnologia"
    assert entities["size"] == "startup"
    assert len(entities["challenges"]) == 2
    assert "Crescimento lento" in entities["challenges"]
    
    scores = result["confidence_scores"]
    assert scores["company_name"] == 1.0
    assert scores["industry"] == 0.9
    
    # Verificar que LLM foi chamado
    assert mock_llm.ainvoke.called


@pytest.mark.asyncio
async def test_extract_all_entities_partial_extraction(onboarding_agent, mock_llm):
    """F1-TEST-2: Extração parcial com apenas alguns campos."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": "Manufatura",
            "size": "média",
            "revenue": None,
            "challenges": ["Problemas de eficiência"],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 1.0,
            "size": 1.0,
            "revenue": 0.0,
            "challenges": 0.9,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    mock_llm.ainvoke.return_value = mock_response
    
    user_text = "Trabalho em uma empresa média de manufatura. Temos problemas de eficiência."
    result = await onboarding_agent._extract_all_entities(user_text)
    
    entities = result["entities"]
    assert entities["company_name"] is None
    assert entities["industry"] == "Manufatura"
    assert entities["size"] == "média"
    assert len(entities["challenges"]) == 1
    
    scores = result["confidence_scores"]
    assert scores["company_name"] == 0.0
    assert scores["industry"] == 1.0


@pytest.mark.asyncio
async def test_extract_all_entities_empty_text(onboarding_agent, mock_llm):
    """F1-TEST-3: Extração de texto vazio ou muito curto."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": [],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.0,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    mock_llm.ainvoke.return_value = mock_response
    
    user_text = "Oi"
    result = await onboarding_agent._extract_all_entities(user_text)
    
    entities = result["entities"]
    assert all(v is None or v == [] for v in entities.values())
    
    scores = result["confidence_scores"]
    assert all(score == 0.0 for score in scores.values())


@pytest.mark.asyncio
async def test_extract_all_entities_json_parse_error_fallback(onboarding_agent, mock_llm):
    """F1-TEST-4: Fallback quando LLM retorna JSON inválido."""
    mock_response = MagicMock()
    mock_response.content = "Texto inválido sem JSON"
    mock_llm.ainvoke.return_value = mock_response
    
    user_text = "Empresa ABC"
    result = await onboarding_agent._extract_all_entities(user_text)
    
    # Deve retornar estrutura vazia (fallback)
    assert "entities" in result
    assert "confidence_scores" in result
    
    entities = result["entities"]
    assert all(v is None or v == [] for v in entities.values())


@pytest.mark.asyncio
async def test_extract_all_entities_markdown_json_extraction(onboarding_agent, mock_llm):
    """F1-TEST-5: Extração de JSON dentro de markdown code blocks."""
    # LLM às vezes retorna JSON dentro de ```json ... ```
    mock_response = MagicMock()
    mock_response.content = """```json
{
  "entities": {
    "company_name": "Indústrias XYZ",
    "industry": "Manufatura",
    "size": "grande",
    "revenue": null,
    "challenges": ["Alta rotatividade", "Eficiência baixa"],
    "goals": ["Reduzir turnover 30%"],
    "timeline": "18 meses",
    "budget": "R$ 200k",
    "location": "Rio de Janeiro"
  },
  "confidence_scores": {
    "company_name": 1.0,
    "industry": 1.0,
    "size": 0.8,
    "revenue": 0.0,
    "challenges": 0.9,
    "goals": 0.85,
    "timeline": 0.9,
    "budget": 1.0,
    "location": 1.0
  }
}
```"""
    mock_llm.ainvoke.return_value = mock_response
    
    user_text = "Indústrias XYZ, grande manufatureira no RJ"
    result = await onboarding_agent._extract_all_entities(user_text)
    
    # Deve extrair JSON de dentro do markdown
    entities = result["entities"]
    assert entities["company_name"] == "Indústrias XYZ"
    assert entities["industry"] == "Manufatura"
    assert entities["location"] == "Rio de Janeiro"
    assert len(entities["challenges"]) == 2


# ============================================================================
# F1-TEST-6 a F1-TEST-10: collect_client_info()
# ============================================================================

@pytest.mark.asyncio
async def test_collect_client_info_first_turn_initialization(
    onboarding_agent, valid_bsc_state, mock_llm
):
    """F1-TEST-6: Primeiro turno inicializa partial_profile corretamente."""
    # Mock extração
    mock_extraction_response = MagicMock()
    mock_extraction_response.content = json.dumps({
        "entities": {
            "company_name": "TechCorp",
            "industry": "Tecnologia",
            "size": None,
            "revenue": None,
            "challenges": [],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 1.0,
            "industry": 0.9,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.0,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    # Mock pergunta contextual
    mock_question_response = MagicMock()
    mock_question_response.content = "TechCorp, qual o porte da empresa?"
    
    mock_llm.ainvoke.side_effect = [mock_extraction_response, mock_question_response]
    
    # Executar
    result = await onboarding_agent.collect_client_info(
        "user_123",
        "Sou da TechCorp, setor de tecnologia",
        valid_bsc_state
    )
    
    # Validações
    assert "question" in result
    assert "is_complete" in result
    assert result["is_complete"] is False
    
    # Partial profile deve estar inicializado em metadata
    assert "partial_profile" in valid_bsc_state.metadata
    assert valid_bsc_state.metadata["partial_profile"]["company_name"] == "TechCorp"
    assert valid_bsc_state.metadata["partial_profile"]["industry"] == "Tecnologia"


@pytest.mark.asyncio
async def test_collect_client_info_accumulation_multiple_turns(
    onboarding_agent, valid_bsc_state, mock_llm
):
    """F1-TEST-7: Acumulação de conhecimento entre múltiplos turnos."""
    # Turno 1: company_name + industry
    mock_extraction1 = MagicMock()
    mock_extraction1.content = json.dumps({
        "entities": {
            "company_name": "TechCorp",
            "industry": "Tecnologia",
            "size": None,
            "revenue": None,
            "challenges": [],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 1.0,
            "industry": 1.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.0,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    mock_question1 = MagicMock()
    mock_question1.content = "Qual o porte da empresa?"
    
    mock_llm.ainvoke.side_effect = [mock_extraction1, mock_question1]
    
    result1 = await onboarding_agent.collect_client_info(
        "user_123",
        "Sou da TechCorp, tecnologia",
        valid_bsc_state
    )
    
    assert valid_bsc_state.metadata["partial_profile"]["company_name"] == "TechCorp"
    assert valid_bsc_state.metadata["partial_profile"]["industry"] == "Tecnologia"
    assert valid_bsc_state.metadata["partial_profile"]["size"] is None
    
    # Turno 2: adicionar size + challenges
    mock_extraction2 = MagicMock()
    mock_extraction2.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": "startup",
            "revenue": None,
            "challenges": ["Crescimento lento", "Falta de capital"],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 1.0,
            "revenue": 0.0,
            "challenges": 1.0,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    mock_completion = MagicMock()
    mock_completion.content = "Perfeito, TechCorp! Tenho as informações essenciais..."
    
    mock_llm.ainvoke.side_effect = [mock_extraction2, mock_completion]
    
    result2 = await onboarding_agent.collect_client_info(
        "user_123",
        "Somos uma startup. Principais desafios: crescimento lento e falta de capital.",
        valid_bsc_state
    )
    
    # Acumulação: dados anteriores preservados + novos dados adicionados
    assert valid_bsc_state.metadata["partial_profile"]["company_name"] == "TechCorp"  # Preservado
    assert valid_bsc_state.metadata["partial_profile"]["industry"] == "Tecnologia"  # Preservado
    assert valid_bsc_state.metadata["partial_profile"]["size"] == "startup"  # Novo
    assert len(valid_bsc_state.metadata["partial_profile"]["challenges"]) == 2  # Novos


@pytest.mark.asyncio
async def test_collect_client_info_minimum_info_completion(
    onboarding_agent, valid_bsc_state, mock_llm
):
    """F1-TEST-8: Onboarding completa quando informações mínimas atingidas."""
    # Pré-preencher partial_profile com informações mínimas em metadata
    valid_bsc_state.metadata["partial_profile"] = {
        "company_name": "TechCorp",
        "industry": "Tecnologia",
        "size": "startup",
        "revenue": None,
        "challenges": ["Crescimento lento", "Falta de capital"],
        "goals": [],
        "timeline": None,
        "budget": None,
        "location": None,
    }
    
    # Mock extração que não adiciona nada novo (já completo)
    mock_extraction = MagicMock()
    mock_extraction.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": [],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.0,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    mock_llm.ainvoke.return_value = mock_extraction
    
    result = await onboarding_agent.collect_client_info(
        "user_123",
        "OK, pode prosseguir",
        valid_bsc_state
    )
    
    # Deve marcar como completo
    assert result["is_complete"] is True
    assert "Perfeito, TechCorp!" in result["question"]
    
    # ClientProfile deve estar atualizado
    assert valid_bsc_state.client_profile.company.name == "TechCorp"
    assert valid_bsc_state.client_profile.company.sector == "Tecnologia"
    assert len(valid_bsc_state.client_profile.context.current_challenges) == 2
    
    # Phase deve ter transicionado para DISCOVERY
    assert valid_bsc_state.current_phase == ConsultingPhase.DISCOVERY


@pytest.mark.asyncio
async def test_collect_client_info_challenges_accumulation(
    onboarding_agent, valid_bsc_state, mock_llm
):
    """F1-TEST-9: Desafios são acumulados sem duplicatas entre turnos."""
    # Turno 1: adicionar 2 desafios
    valid_bsc_state.metadata["partial_profile"]["challenges"] = ["Crescimento lento"]
    
    mock_extraction = MagicMock()
    mock_extraction.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": ["Falta de capital", "Crescimento lento"],  # Um novo + um duplicado
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.9,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    mock_question = MagicMock()
    mock_question.content = "Qual o porte da empresa?"
    
    mock_llm.ainvoke.side_effect = [mock_extraction, mock_question]
    
    await onboarding_agent.collect_client_info(
        "user_123",
        "Temos falta de capital e crescimento lento",
        valid_bsc_state
    )
    
    # Deve ter 2 desafios únicos (duplicata removida)
    challenges = valid_bsc_state.metadata["partial_profile"]["challenges"]
    assert len(challenges) == 2
    assert "Crescimento lento" in challenges
    assert "Falta de capital" in challenges


@pytest.mark.asyncio
async def test_collect_client_info_llm_error_fallback_question(
    onboarding_agent, valid_bsc_state, mock_llm
):
    """F1-TEST-10: Fallback para pergunta genérica quando LLM falha."""
    # Mock extração OK
    mock_extraction = MagicMock()
    mock_extraction.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": [],
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.0,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    # Mock LLM de pergunta contextual falha
    mock_llm.ainvoke.side_effect = [mock_extraction, Exception("LLM timeout")]
    
    result = await onboarding_agent.collect_client_info(
        "user_123",
        "Olá",
        valid_bsc_state
    )
    
    # Deve retornar pergunta de fallback
    assert result["is_complete"] is False
    assert "question" in result
    assert "nome da sua empresa" in result["question"].lower() or "qual o nome" in result["question"].lower()


# ============================================================================
# F1-TEST-11 a F1-TEST-15: Integração Prompts
# ============================================================================

def test_entity_extraction_prompt_has_required_fields():
    """F1-TEST-11: Prompt ENTITY_EXTRACTION tem todos campos necessários."""
    from src.prompts.client_profile_prompts import (
        ENTITY_EXTRACTION_SYSTEM,
        ENTITY_EXTRACTION_USER,
    )
    
    # System prompt deve mencionar os 9 campos
    assert "company_name" in ENTITY_EXTRACTION_SYSTEM
    assert "industry" in ENTITY_EXTRACTION_SYSTEM
    assert "size" in ENTITY_EXTRACTION_SYSTEM
    assert "revenue" in ENTITY_EXTRACTION_SYSTEM
    assert "challenges" in ENTITY_EXTRACTION_SYSTEM
    assert "goals" in ENTITY_EXTRACTION_SYSTEM
    assert "timeline" in ENTITY_EXTRACTION_SYSTEM
    assert "budget" in ENTITY_EXTRACTION_SYSTEM
    assert "location" in ENTITY_EXTRACTION_SYSTEM
    
    # User prompt deve ter placeholder
    assert "{user_text}" in ENTITY_EXTRACTION_USER


def test_opportunistic_followup_prompt_has_context():
    """F1-TEST-12: Prompt OPPORTUNISTIC_FOLLOWUP usa contexto conhecido."""
    from src.prompts.client_profile_prompts import (
        OPPORTUNISTIC_FOLLOWUP_SYSTEM,
        OPPORTUNISTIC_FOLLOWUP_USER,
    )
    
    # System prompt deve ter estratégias de follow-up
    assert "APROFUNDAMENTO" in OPPORTUNISTIC_FOLLOWUP_SYSTEM
    assert "QUANTIFICAÇÃO" in OPPORTUNISTIC_FOLLOWUP_SYSTEM
    assert "PRIORIZAÇÃO" in OPPORTUNISTIC_FOLLOWUP_SYSTEM
    
    # User prompt deve ter placeholders de contexto
    assert "{known_entities}" in OPPORTUNISTIC_FOLLOWUP_USER
    assert "{user_last_message}" in OPPORTUNISTIC_FOLLOWUP_USER


def test_context_aware_question_prompt_has_prioritization():
    """F1-TEST-13: Prompt CONTEXT_AWARE_QUESTION prioriza campos obrigatórios."""
    from src.prompts.client_profile_prompts import (
        CONTEXT_AWARE_QUESTION_SYSTEM,
        CONTEXT_AWARE_QUESTION_USER,
    )
    
    # System prompt deve ter priorização
    assert "PRIORIDADE ALTA" in CONTEXT_AWARE_QUESTION_SYSTEM
    assert "company_name" in CONTEXT_AWARE_QUESTION_SYSTEM
    assert "industry" in CONTEXT_AWARE_QUESTION_SYSTEM
    
    # User prompt deve ter placeholders
    assert "{known_fields}" in CONTEXT_AWARE_QUESTION_USER
    assert "{missing_fields}" in CONTEXT_AWARE_QUESTION_USER


def test_all_prompts_have_examples():
    """F1-TEST-14: Todos os 3 novos prompts têm examples (few-shot)."""
    from src.prompts.client_profile_prompts import (
        ENTITY_EXTRACTION_SYSTEM,
        OPPORTUNISTIC_FOLLOWUP_SYSTEM,
        CONTEXT_AWARE_QUESTION_SYSTEM,
    )
    
    # Todos devem ter seção EXEMPLO ou EXAMPLES
    assert "EXEMPLO" in ENTITY_EXTRACTION_SYSTEM
    assert "EXEMPLO" in OPPORTUNISTIC_FOLLOWUP_SYSTEM
    assert "EXEMPLO" in CONTEXT_AWARE_QUESTION_SYSTEM


def test_prompts_are_anti_hallucination():
    """F1-TEST-15: Prompts têm instruções anti-alucinação."""
    from src.prompts.client_profile_prompts import (
        ENTITY_EXTRACTION_SYSTEM,
        OPPORTUNISTIC_FOLLOWUP_SYSTEM,
        CONTEXT_AWARE_QUESTION_SYSTEM,
    )
    
    # Devem ter instruções para NÃO inventar/adivinhar
    extraction_has_anti_hallucination = (
        "NÃO invente" in ENTITY_EXTRACTION_SYSTEM
        or "NÃO adivinhe" in ENTITY_EXTRACTION_SYSTEM
    )
    
    followup_has_anti_hallucination = (
        "NÃO repita" in OPPORTUNISTIC_FOLLOWUP_SYSTEM
        or "NÃO peça informações que já foram fornecidas" in OPPORTUNISTIC_FOLLOWUP_SYSTEM
    )
    
    context_aware_has_anti_hallucination = (
        "NÃO repita" in CONTEXT_AWARE_QUESTION_SYSTEM
    )
    
    assert extraction_has_anti_hallucination
    assert followup_has_anti_hallucination
    assert context_aware_has_anti_hallucination


# ============================================================================
# TESTES FASE 2: INTELLIGENT VALIDATION
# ============================================================================

@pytest.mark.asyncio
async def test_validate_challenge_correct(onboarding_agent):
    """Challenge válido deve ser classificado corretamente."""
    # Mock LLM response (challenge correto)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "challenge",
        "confidence": 0.95,
        "reasoning": "Problema atual claramente identificado"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Baixa satisfação de clientes",
        "challenge"
    )
    
    assert result["is_valid"] is True
    assert result["classified_as"] == "challenge"
    assert result["confidence"] > 0.7
    assert result["correction_suggestion"] is None


@pytest.mark.asyncio
async def test_validate_objective_correct(onboarding_agent):
    """Objective válido deve ser classificado corretamente."""
    # Mock LLM response (objective correto)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "objective",
        "confidence": 1.0,
        "reasoning": "Meta futura quantificada"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Aumentar satisfação para 90%",
        "objective"
    )
    
    assert result["is_valid"] is True
    assert result["classified_as"] == "objective"
    assert result["confidence"] >= 0.9
    assert result["correction_suggestion"] is None


@pytest.mark.asyncio
async def test_validate_challenge_misclassified_as_objective(onboarding_agent):
    """Challenge confundido com objective deve ser detectado."""
    # Mock LLM response (misclassified)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "objective",
        "confidence": 0.9,
        "reasoning": "Meta futura identificada"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Reduzir custos em 15%",
        "challenge"
    )
    
    assert result["is_valid"] is False
    assert result["classified_as"] == "objective"
    assert result["confidence"] > 0.7
    assert result["correction_suggestion"] is not None
    assert "objective" in result["correction_suggestion"]


@pytest.mark.asyncio
async def test_validate_objective_misclassified_as_challenge(onboarding_agent):
    """Objective confundido com challenge deve ser detectado."""
    # Mock LLM response (misclassified)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "challenge",
        "confidence": 0.85,
        "reasoning": "Problema atual identificado"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Processos ineficientes",
        "objective"
    )
    
    assert result["is_valid"] is False
    assert result["classified_as"] == "challenge"
    assert result["confidence"] > 0.7
    assert result["correction_suggestion"] is not None
    assert "challenge" in result["correction_suggestion"]


@pytest.mark.asyncio
async def test_validate_ambiguous_text(onboarding_agent):
    """Texto ambíguo deve ser classificado como ambiguous."""
    # Mock LLM response (ambíguo)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "ambiguous",
        "confidence": 0.4,
        "reasoning": "Falta quantificação e especificidade"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Queremos crescer",
        "objective"
    )
    
    assert result["classified_as"] == "ambiguous"
    assert result["confidence"] < 0.6


@pytest.mark.asyncio
async def test_validate_high_confidence(onboarding_agent):
    """Validação com alta confidence (> 0.9)."""
    # Mock LLM response (alta confidence)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "objective",
        "confidence": 0.98,
        "reasoning": "Meta quantificada claramente"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Reduzir custos operacionais em 15%",
        "objective"
    )
    
    assert result["confidence"] >= 0.9
    assert result["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_low_confidence(onboarding_agent):
    """Validação com baixa confidence (< 0.5)."""
    # Mock LLM response (baixa confidence)
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classified_as": "ambiguous",
        "confidence": 0.3,
        "reasoning": "Extremamente vago"
    })
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Melhorar desempenho",
        "objective"
    )
    
    assert result["confidence"] <= 0.5


@pytest.mark.asyncio
async def test_validate_json_parse_error_fallback(onboarding_agent):
    """Erro de parsing JSON deve usar fallback."""
    # Mock LLM response (JSON inválido)
    mock_response = MagicMock()
    mock_response.content = "Texto inválido sem JSON"
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Baixa satisfação",
        "challenge"
    )
    
    # Fallback: assumir válido
    assert result["is_valid"] is True
    assert result["classified_as"] == "challenge"
    assert result["confidence"] == 0.5


@pytest.mark.asyncio
async def test_validate_markdown_json_extraction(onboarding_agent):
    """LLM retornando JSON em markdown code block deve ser parseado."""
    # Mock LLM response (markdown code block)
    mock_response = MagicMock()
    mock_response.content = """```json
{
  "classified_as": "challenge",
  "confidence": 0.9,
  "reasoning": "Problema atual"
}
```"""
    onboarding_agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    result = await onboarding_agent._validate_extraction(
        "Alta rotatividade de funcionários",
        "challenge"
    )
    
    assert result["classified_as"] == "challenge"
    assert result["confidence"] == 0.9
    assert result["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_batch_mixed(onboarding_agent):
    """Validar múltiplas entidades com classificações diferentes."""
    # Mock LLM responses para 3 validações
    responses = [
        # Challenge correto
        MagicMock(content=json.dumps({
            "classified_as": "challenge",
            "confidence": 0.95,
            "reasoning": "Problema atual"
        })),
        # Objective correto
        MagicMock(content=json.dumps({
            "classified_as": "objective",
            "confidence": 1.0,
            "reasoning": "Meta quantificada"
        })),
        # Ambíguo
        MagicMock(content=json.dumps({
            "classified_as": "ambiguous",
            "confidence": 0.4,
            "reasoning": "Vago"
        }))
    ]
    onboarding_agent.llm.ainvoke = AsyncMock(side_effect=responses)
    
    result1 = await onboarding_agent._validate_extraction("Baixa satisfação", "challenge")
    result2 = await onboarding_agent._validate_extraction("Aumentar 20%", "objective")
    result3 = await onboarding_agent._validate_extraction("Crescer", "objective")
    
    assert result1["classified_as"] == "challenge"
    assert result2["classified_as"] == "objective"
    assert result3["classified_as"] == "ambiguous"


# ============================================================================
# TESTES INTEGRAÇÃO FASE 2: Validação em _extract_all_entities()
# ============================================================================

@pytest.mark.asyncio
async def test_extract_with_validation_reclassify_challenge_to_objective(onboarding_agent):
    """Challenge misclassificado deve ser reclassificado para objective."""
    # Mock extração inicial: 1 challenge que é na verdade objective
    mock_extraction = MagicMock()
    mock_extraction.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": ["Aumentar vendas em 20%"],  # Misclassificado como challenge
            "goals": [],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.9,
            "goals": 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    # Mock validação: detectar que é objective
    mock_validation = MagicMock()
    mock_validation.content = json.dumps({
        "classified_as": "objective",
        "confidence": 0.95,
        "reasoning": "Meta quantificada"
    })
    
    onboarding_agent.llm.ainvoke = AsyncMock(side_effect=[mock_extraction, mock_validation])
    
    result = await onboarding_agent._extract_all_entities("Aumentar vendas em 20%")
    
    # Deve ter reclassificado
    assert len(result["entities"]["challenges"]) == 0
    assert len(result["entities"]["goals"]) == 1
    assert "Aumentar vendas em 20%" in result["entities"]["goals"]
    assert result["validated"] is True


@pytest.mark.asyncio
async def test_extract_with_validation_reclassify_objective_to_challenge(onboarding_agent):
    """Objective misclassificado deve ser reclassificado para challenge."""
    # Mock extração inicial: 1 goal que é na verdade challenge
    mock_extraction = MagicMock()
    mock_extraction.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": [],
            "goals": ["Baixa satisfação de clientes"],  # Misclassificado como goal
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.0,
            "goals": 0.9,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    # Mock validação: detectar que é challenge
    mock_validation = MagicMock()
    mock_validation.content = json.dumps({
        "classified_as": "challenge",
        "confidence": 0.9,
        "reasoning": "Problema atual"
    })
    
    onboarding_agent.llm.ainvoke = AsyncMock(side_effect=[mock_extraction, mock_validation])
    
    result = await onboarding_agent._extract_all_entities("Baixa satisfação")
    
    # Deve ter reclassificado
    assert len(result["entities"]["goals"]) == 0
    assert len(result["entities"]["challenges"]) == 1
    assert "Baixa satisfação de clientes" in result["entities"]["challenges"]
    assert result["validated"] is True


@pytest.mark.asyncio
async def test_extract_with_validation_preserves_correct(onboarding_agent):
    """Entidades corretamente classificadas devem ser preservadas."""
    # Mock extração inicial: challenge + goal corretos
    mock_extraction = MagicMock()
    mock_extraction.content = json.dumps({
        "entities": {
            "company_name": None,
            "industry": None,
            "size": None,
            "revenue": None,
            "challenges": ["Baixa satisfação"],
            "goals": ["Aumentar em 20%"],
            "timeline": None,
            "budget": None,
            "location": None
        },
        "confidence_scores": {
            "company_name": 0.0,
            "industry": 0.0,
            "size": 0.0,
            "revenue": 0.0,
            "challenges": 0.95,
            "goals": 1.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0
        }
    })
    
    # Mock validações: ambos corretos
    mock_validation1 = MagicMock()
    mock_validation1.content = json.dumps({
        "classified_as": "challenge",
        "confidence": 0.9,
        "reasoning": "Problema atual"
    })
    
    mock_validation2 = MagicMock()
    mock_validation2.content = json.dumps({
        "classified_as": "objective",
        "confidence": 1.0,
        "reasoning": "Meta quantificada"
    })
    
    onboarding_agent.llm.ainvoke = AsyncMock(
        side_effect=[mock_extraction, mock_validation1, mock_validation2]
    )
    
    result = await onboarding_agent._extract_all_entities("Baixa satisfação e aumentar 20%")
    
    # Ambos preservados
    assert len(result["entities"]["challenges"]) == 1
    assert len(result["entities"]["goals"]) == 1
    assert "Baixa satisfação" in result["entities"]["challenges"]
    assert "Aumentar em 20%" in result["entities"]["goals"]
    assert result["validated"] is True

