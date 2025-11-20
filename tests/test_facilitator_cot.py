"""Testes para FacilitatorAgent Chain of Thought (FASE 3.8).

Testa funcionalidade de consultoria BSC usando Chain of Thought reasoning
no ConsultingOrchestrator.facilitate_cot_consulting().

Cobertura:
- Execução bem-sucedida do Chain of Thought
- Fallback quando há erro técnico
- Construção correta de contexto empresarial
- Integração com prompts CoT
- Validação de estrutura de resposta (5 steps)

Created: 2025-10-27 (FASE 3.8)
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.consulting_orchestrator import ConsultingOrchestrator
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext


class TestFacilitatorChainOfThought:
    """Testes para FacilitatorAgent Chain of Thought."""

    @pytest.fixture
    def orchestrator(self):
        """Fixture para ConsultingOrchestrator."""
        return ConsultingOrchestrator()

    @pytest.fixture
    def mock_client_profile(self):
        """Fixture para ClientProfile válido."""
        return ClientProfile(
            company=CompanyInfo(
                name="TechCorp Ltda",
                sector="Tecnologia",
                size="Média",
                industry="Software as a Service",
                founded_year=2015,
            ),
            context=StrategicContext(
                current_challenges=["Baixa satisfação do cliente", "Custos operacionais altos"],
                strategic_objectives=["Aumentar market share", "Melhorar eficiência operacional"],
            ),
        )

    @pytest.fixture
    def mock_llm_response(self):
        """Fixture para resposta LLM simulada."""
        return Mock(
            content="""
**STEP 1: ANÁLISE INICIAL**
- Tipo de problema: Implementação de BSC em empresa de tecnologia
- Perspectivas BSC relevantes: Todas as 4 (Financeira, Cliente, Processos, Aprendizado)
- Complexidade: Alta (primeira implementação)
- Informações críticas: Estratégia atual disponível

**STEP 2: DECOMPOSIÇÃO**
- Sub-problemas identificados:
  1. Definição de objetivos estratégicos claros
  2. Seleção de KPIs apropriados
  3. Estabelecimento de metas
- Dependências: Objetivos -> KPIs -> Metas
- Priorização: 1. Objetivos, 2. KPIs, 3. Metas

**STEP 3: ANÁLISE ESTRATÉGICA**
- Perspectiva Financeira: Foco em crescimento de receita
- Perspectiva Cliente: Melhorar satisfação e retenção
- Perspectiva Processos: Otimizar operações
- Perspectiva Aprendizado: Desenvolver capacidades
- Gaps identificados: Falta de KPIs estruturados

**STEP 4: ALTERNATIVAS**
- Alternativa A: Implementação completa BSC (6 meses)
- Alternativa B: Implementação gradual por perspectiva (12 meses)
- Alternativa C: Piloto em uma perspectiva (3 meses)

**STEP 5: RECOMENDAÇÃO**
- Recomendação principal: Implementação gradual (Alternativa B)
- Próximos passos: Começar com perspectiva Financeira
- Responsáveis: Equipe estratégica + consultor BSC
- Cronograma: 12 meses
- Métricas de sucesso: KPIs definidos e monitorados
"""
        )

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_success(
        self, orchestrator, mock_client_profile, mock_llm_response
    ):
        """Testa execução bem-sucedida do Chain of Thought."""
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            # Configurar mock LLM
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.return_value = mock_llm_response
            mock_chat.return_value = mock_llm_instance

            # Executar CoT
            result = await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile,
                client_query="Como implementar BSC em nossa empresa?",
            )

            # Validações
            assert result is not None
            assert len(result) > 100  # Resposta substancial
            assert "STEP 1: ANÁLISE INICIAL" in result
            assert "STEP 2: DECOMPOSIÇÃO" in result
            assert "STEP 3: ANÁLISE ESTRATÉGICA" in result
            assert "STEP 4: ALTERNATIVAS" in result
            assert "STEP 5: RECOMENDAÇÃO" in result

            # Verificar se LLM foi chamado corretamente
            mock_llm_instance.ainvoke.assert_called_once()
            call_args = mock_llm_instance.ainvoke.call_args[0][0]
            assert len(call_args) == 2
            assert isinstance(call_args[0], SystemMessage)
            assert isinstance(call_args[1], HumanMessage)

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_with_fallback(self, orchestrator, mock_client_profile):
        """Testa fallback quando LLM falha."""
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            # Configurar mock LLM para falhar
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.side_effect = Exception("LLM API Error")
            mock_chat.return_value = mock_llm_instance

            # Executar CoT
            result = await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile, client_query="Como implementar BSC?"
            )

            # Validações do fallback
            assert result is not None
            assert "CHAIN OF THOUGHT FACILITATION - FALLBACK" in result
            assert "ERRO TÉCNICO" in result
            assert "LLM API Error" in result
            assert "STEP 1: ANÁLISE INICIAL" in result
            assert "STEP 5: RECOMENDAÇÃO" in result

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_without_query(
        self, orchestrator, mock_client_profile, mock_llm_response
    ):
        """Testa CoT sem query específica do cliente."""
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.return_value = mock_llm_response
            mock_chat.return_value = mock_llm_instance

            # Executar CoT sem query
            result = await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile, client_query=None
            )

            # Validações
            assert result is not None
            assert "STEP 1: ANÁLISE INICIAL" in result

            # Verificar se prompt foi construído corretamente
            call_args = mock_llm_instance.ainvoke.call_args[0][0]
            human_message = call_args[1]
            assert "Consulta específica não fornecida" in human_message.content

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_with_custom_bsc_knowledge(
        self, orchestrator, mock_client_profile, mock_llm_response
    ):
        """Testa CoT com conhecimento BSC customizado."""
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.return_value = mock_llm_response
            mock_chat.return_value = mock_llm_instance

            custom_bsc = "Conhecimento BSC customizado para teste"

            # Executar CoT com conhecimento customizado
            result = await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile,
                client_query="Implementação BSC",
                bsc_knowledge=custom_bsc,
            )

            # Validações
            assert result is not None

            # Verificar se conhecimento customizado foi usado
            call_args = mock_llm_instance.ainvoke.call_args[0][0]
            human_message = call_args[1]
            assert custom_bsc in human_message.content

    def test_build_company_context_for_cot(self, mock_client_profile):
        """Testa construção de contexto empresarial para CoT."""
        from src.prompts.facilitator_cot_prompt import build_company_context_for_cot

        context = build_company_context_for_cot(mock_client_profile)

        # Validações
        assert context is not None
        assert "TechCorp Ltda" in context
        assert "Tecnologia" in context
        assert "média" in context  # Valor real do schema
        assert "Software as a Service" in context
        assert "2015" in context
        assert "Baixa satisfação do cliente" in context
        assert "Aumentar market share" in context

    def test_build_company_context_for_cot_none_profile(self):
        """Testa construção de contexto com profile None."""
        from src.prompts.facilitator_cot_prompt import build_company_context_for_cot

        context = build_company_context_for_cot(None)

        assert context == "Contexto da empresa não disponível"

    def test_build_bsc_knowledge_context(self):
        """Testa construção de contexto de conhecimento BSC."""
        from src.prompts.facilitator_cot_prompt import build_bsc_knowledge_context

        context = build_bsc_knowledge_context()

        # Validações
        assert context is not None
        assert "PRINCÍPIOS BSC FUNDAMENTAIS" in context
        assert "Perspectiva Financeira" in context
        assert "Perspectiva Cliente" in context
        assert "Perspectiva Processos Internos" in context
        assert "Perspectiva Aprendizado e Crescimento" in context
        assert "INTERCONEXÕES BSC" in context
        assert "IMPLEMENTAÇÃO BSC" in context

    def test_build_client_query_context(self):
        """Testa construção de contexto de query do cliente."""
        from src.prompts.facilitator_cot_prompt import build_client_query_context

        # Teste com query válida
        context = build_client_query_context("Como implementar BSC?")
        assert "Como implementar BSC?" in context

        # Teste com query None
        context = build_client_query_context(None)
        assert "Consulta específica não fornecida" in context

        # Teste com query vazia
        context = build_client_query_context("")
        assert "Consulta específica não fornecida" in context

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_structure_validation(
        self, orchestrator, mock_client_profile, mock_llm_response
    ):
        """Testa validação da estrutura de resposta CoT."""
        with patch("langchain_openai.ChatOpenAI") as mock_chat:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.return_value = mock_llm_response
            mock_chat.return_value = mock_llm_instance

            result = await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile, client_query="Implementação BSC"
            )

            # Validar estrutura dos 5 steps
            steps = [
                "STEP 1: ANÁLISE INICIAL",
                "STEP 2: DECOMPOSIÇÃO",
                "STEP 3: ANÁLISE ESTRATÉGICA",
                "STEP 4: ALTERNATIVAS",
                "STEP 5: RECOMENDAÇÃO",
            ]

            for step in steps:
                assert step in result, f"Step {step} não encontrado na resposta"

            # Validar conteúdo mínimo de cada step
            assert "Tipo de problema:" in result
            assert "Sub-problemas identificados:" in result
            assert "Perspectiva Financeira:" in result
            assert "Alternativa A:" in result
            assert "Recomendação principal:" in result

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_logging(
        self, orchestrator, mock_client_profile, mock_llm_response
    ):
        """Testa logging durante execução CoT."""
        with (
            patch("langchain_openai.ChatOpenAI") as mock_chat,
            patch("src.graph.consulting_orchestrator.logger") as mock_logger,
        ):

            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.return_value = mock_llm_response
            mock_chat.return_value = mock_llm_instance

            await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile, client_query="Teste logging"
            )

            # Verificar se logs foram chamados
            assert mock_logger.info.call_count >= 2  # Início + sucesso
            assert any("FACILITATOR_COT" in str(call) for call in mock_logger.info.call_args_list)

    @pytest.mark.asyncio
    async def test_facilitate_cot_consulting_error_logging(self, orchestrator, mock_client_profile):
        """Testa logging de erro durante CoT."""
        with (
            patch("langchain_openai.ChatOpenAI") as mock_chat,
            patch("src.graph.consulting_orchestrator.logger") as mock_logger,
        ):

            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke.side_effect = Exception("Test Error")
            mock_chat.return_value = mock_llm_instance

            await orchestrator.facilitate_cot_consulting(
                client_profile=mock_client_profile, client_query="Teste erro"
            )

            # Verificar se erro foi logado
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "FACILITATOR_COT" in error_call
            assert "Test Error" in error_call
