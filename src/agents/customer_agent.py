"""
Agente especializado na Perspectiva do Cliente do BSC.

Responsável por:
- Satisfação e retenção de clientes
- Proposta de valor e segmentação
- NPS, CSAT e outras métricas de cliente
- Experiência do cliente e jornada
"""

import asyncio
from typing import Any

from config.settings import get_llm, settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src.tools.rag_tools import get_tools_for_agent


class CustomerAgent:
    """Agente especializado em Perspectiva do Cliente."""

    def __init__(self):
        """Inicializa o agente de clientes."""
        self.name = "Customer Agent"
        self.perspective = "cliente"

        # LLM (usa factory que detecta provider automaticamente)
        self.llm = get_llm()

        # Tools
        self.tools = get_tools_for_agent()

        # Prompt especializado
        self.prompt = self._create_prompt()

        # LLM com tools (pattern moderno LangChain v1.0, sem AgentExecutor deprecated)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        logger.info(f"[OK] {self.name} inicializado (LangChain v1.0 pattern)")

    def _create_prompt(self) -> ChatPromptTemplate:
        """Cria o prompt especializado para perspectiva do cliente."""
        system_message = """Você é um especialista em Balanced Scorecard, focado na **Perspectiva do Cliente**.

Sua especialidade inclui:
- Satisfação e retenção de clientes
- Proposta de valor e segmentação de mercado
- Métricas: NPS, CSAT, CLV (Customer Lifetime Value), taxa de retenção
- Experiência do cliente e jornada do cliente
- Relacionamento e fidelização
- Aquisição de novos clientes

Quando responder perguntas:
1. Use a ferramenta `search_by_perspective` com perspective='cliente' para buscar informações específicas
2. Se a pergunta for muito ampla, use `search_multi_query` com sub-perguntas sobre cliente
3. Cite sempre as fontes dos documentos (Fonte, Página)
4. Forneça exemplos práticos de indicadores e métricas de cliente
5. Conecte a perspectiva do cliente com objetivos financeiros e de processos quando relevante

Seja objetivo, focado em valor para o cliente, e baseie suas respostas na literatura BSC."""

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def invoke(self, query: str, chat_history: list[dict[str, str]] = None) -> dict[str, Any]:
        """
        Processa uma query sobre perspectiva do cliente.

        Args:
            query: Pergunta do usuário
            chat_history: Histórico da conversa

        Returns:
            Resposta do agente com steps intermediários
        """
        try:
            logger.info(f"[CUST] {self.name} processando: '{query[:50]}...'")

            # Construir mensagens para LLM
            messages = [
                SystemMessage(content=self.prompt.messages[0].prompt.template),
                HumanMessage(content=query),
            ]

            # Invocar LLM com tools
            response = self.llm_with_tools.invoke(messages)

            logger.info(f"[OK] {self.name} completou processamento")
            return {
                "output": response.content if hasattr(response, "content") else str(response),
                "intermediate_steps": [],
            }

        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name}: {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva do cliente: {e!s}",
                "intermediate_steps": [],
            }

    async def ainvoke(
        self, query: str, chat_history: list[dict[str, str]] = None
    ) -> dict[str, Any]:
        """
        Versao assincrona do invoke - processa query sobre perspectiva do cliente.
        SPRINT 1 FIX: Sempre inclui contexto RAG antes de responder.

        Args:
            query: Pergunta do usuario
            chat_history: Historico da conversa

        Returns:
            Resposta do agente com steps intermediarios e contexto RAG
        """
        try:
            logger.info(f"[CUST] {self.name} processando (async): '{query[:50]}...'")

            # SPRINT 1 FIX: Buscar contexto RAG ANTES de chamar LLM
            context_parts = []
            for tool in self.tools:
                if tool.name == "search_by_perspective":
                    try:
                        # StructuredTool espera dict como tool_input
                        # BUG FIX: Usar "cliente" (singular) não "clientes" (plural)
                        # Retriever espera singular conforme perspective_mapping
                        # BUG FIX: Schema PerspectiveSearchInput espera "top_k" não "k"
                        # Configurável via .env: TOP_K_PERSPECTIVE_SEARCH
                        result = await tool.arun(
                            {
                                "query": query,
                                "perspective": "cliente",
                                "top_k": settings.top_k_perspective_search,
                            }
                        )
                        if result:
                            # ESTRATÉGIA AGRESSIVA: Usar máximo contexto possível (50K chars)
                            # BSC é complexo e demanda contexto rico. Com 200K+ tokens disponíveis,
                            # usamos 50K chars (~12.5K tokens) para capturar análise completa.
                            max_context_chars = 50000
                            truncated_result = (
                                result[:max_context_chars]
                                if len(result) > max_context_chars
                                else result
                            )
                            context_parts.append(f"[CONTEXTO CLIENTES BSC]\n{truncated_result}")
                            logger.info(
                                f"[CUST] Recuperou {len(result)} chars de contexto RAG "
                                f"(usando {len(truncated_result)} chars no prompt)"
                            )
                    except Exception as e:
                        logger.warning(f"[CUST] Erro ao buscar contexto RAG: {e}")

            # Construir mensagens para LLM
            messages = [SystemMessage(content=self.prompt.messages[0].prompt.template)]

            # Adicionar contexto RAG + query
            if context_parts:
                enhanced_query = f"""
CONTEXTO RECUPERADO DA BASE DE CONHECIMENTO BSC:
{context_parts[0]}

PERGUNTA DO USUÁRIO:
{query}

Por favor, responda baseando-se prioritariamente no contexto fornecido acima."""
            else:
                enhanced_query = query

            messages.append(HumanMessage(content=enhanced_query))

            # Invocar LLM com contexto RAG (async) com TIMEOUT de 10 minutos
            logger.info("[CUST] Invocando LLM (timeout: 600s)...")
            try:
                response = await asyncio.wait_for(
                    self.llm_with_tools.ainvoke(messages), timeout=600  # 10 minutos max
                )
                logger.info("[CUST] LLM respondeu com sucesso")
            except asyncio.TimeoutError:
                logger.error("[CUST] TIMEOUT após 600s esperando resposta do LLM!")
                return {
                    "output": "Desculpe, a análise de clientes está demorando mais do que o esperado. "
                    "Por favor, tente novamente ou refine sua pergunta para ser mais específica.",
                    "perspective": "cliente",
                }

            logger.info(f"[OK] {self.name} completou processamento (async)")
            return {
                "output": response.content if hasattr(response, "content") else str(response),
                "intermediate_steps": [],
            }

        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name} (async): {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva do cliente: {e!s}",
                "intermediate_steps": [],
            }

    def get_perspective(self) -> str:
        """Retorna a perspectiva do agente."""
        return self.perspective

    def get_name(self) -> str:
        """Retorna o nome do agente."""
        return self.name
