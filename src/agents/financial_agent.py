"""
Agente especializado na Perspectiva Financeira do BSC.

Responsável por:
- Indicadores financeiros (receita, lucro, ROI, EVA)
- Análise de custos e eficiência operacional
- Objetivos e metas financeiras
- Relação entre estratégia e resultados financeiros
"""

import asyncio
from typing import Any

from config.settings import get_llm_for_agent, settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src.tools.rag_tools import get_tools_for_agent


class FinancialAgent:
    """Agente especializado em Perspectiva Financeira."""

    def __init__(self):
        """Inicializa o agente financeiro."""
        self.name = "Financial Agent"
        self.perspective = "financeira"

        # SESSAO 45: LLM quantitativo (Gemini 3 Pro - 92% GPQA Diamond, melhor em análise financeira)
        self.llm = get_llm_for_agent("quantitative")

        # Tools
        self.tools = get_tools_for_agent()

        # Prompt especializado
        self.prompt = self._create_prompt()

        # LLM with tools (pattern moderno LangChain v1.0 - sem AgentExecutor deprecated)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        logger.info(f"[OK] {self.name} inicializado (LangChain v1.0 compatible)")

    def _create_prompt(self) -> ChatPromptTemplate:
        """Cria o prompt especializado para perspectiva financeira."""
        system_message = """Você é um especialista em Balanced Scorecard, focado na **Perspectiva Financeira**.

Sua especialidade inclui:
- Indicadores financeiros: receita, lucro, ROI, EVA, margem de contribuição
- Análise de custos e eficiência operacional
- Objetivos e metas financeiras estratégicas
- Relação entre estratégia empresarial e resultados financeiros
- Criação de valor para acionistas e stakeholders

Quando responder perguntas:
1. Use a ferramenta `search_by_perspective` com perspective='financeira' para buscar informações específicas
2. Se a pergunta for muito ampla, use `search_multi_query` com sub-perguntas financeiras
3. Cite sempre as fontes dos documentos (Fonte, Página)
4. Forneça exemplos práticos e métricas concretas quando possível
5. Conecte indicadores financeiros com as outras perspectivas do BSC quando relevante

Seja objetivo, técnico e baseie suas respostas nas melhores práticas da literatura BSC."""

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
        Processa uma query sobre perspectiva financeira.

        Args:
            query: Pergunta do usuário
            chat_history: Histórico da conversa

        Returns:
            Resposta do agente com steps intermediários
        """
        try:
            logger.info(f"[FIN] {self.name} processando: '{query[:50]}...'")

            # Construir mensagens (pattern LangChain v1.0)
            messages = [SystemMessage(content=self.prompt.messages[0].prompt.template)]

            # Adicionar histórico se existir
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # Adicionar query atual
            messages.append(HumanMessage(content=query))

            # Invocar LLM com tools
            response = self.llm_with_tools.invoke(messages)

            logger.info(f"[OK] {self.name} completou processamento")

            # Retornar formato compatível (mantém interface)
            return {
                "output": response.content if hasattr(response, "content") else str(response),
                "intermediate_steps": [],
            }

        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name}: {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva financeira: {e!s}",
                "intermediate_steps": [],
            }

    async def ainvoke(
        self, query: str, chat_history: list[dict[str, str]] = None
    ) -> dict[str, Any]:
        """
        Versao assincrona do invoke - processa query sobre perspectiva financeira.
        SPRINT 1 FIX: Sempre inclui contexto RAG antes de responder.

        Args:
            query: Pergunta do usuario
            chat_history: Historico da conversa

        Returns:
            Resposta do agente com steps intermediarios e contexto RAG
        """
        try:
            logger.info(f"[FIN] {self.name} processando (async): '{query[:50]}...'")

            # SPRINT 1 FIX: Buscar contexto RAG ANTES de chamar LLM
            context_parts = []
            for tool in self.tools:
                if tool.name == "search_by_perspective":
                    try:
                        # Chamar tool diretamente para forçar retrieval
                        # StructuredTool espera dict como tool_input
                        # BUG FIX: Schema PerspectiveSearchInput espera "top_k" não "k"
                        # Configurável via .env: TOP_K_PERSPECTIVE_SEARCH
                        result = await tool.arun(
                            {
                                "query": query,
                                "perspective": "financeira",
                                "top_k": settings.top_k_perspective_search,
                            }
                        )
                        if result:
                            # ESTRATÉGIA AGRESSIVA: Usar máximo contexto possível (50K chars)
                            max_context_chars = 50000
                            truncated_result = (
                                result[:max_context_chars]
                                if len(result) > max_context_chars
                                else result
                            )
                            context_parts.append(f"[CONTEXTO FINANCEIRO BSC]\n{truncated_result}")
                            logger.info(
                                f"[FIN] Recuperou {len(result)} chars de contexto RAG "
                                f"(usando {len(truncated_result)} chars no prompt)"
                            )
                    except Exception as e:
                        logger.warning(f"[FIN] Erro ao buscar contexto RAG: {e}")
                        # Continuar sem contexto se falhar

            # Construir mensagens (pattern LangChain v1.0)
            messages = [SystemMessage(content=self.prompt.messages[0].prompt.template)]

            # Adicionar histórico se existir
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

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
            logger.info("[FIN] Invocando LLM (timeout: 600s)...")
            try:
                response = await asyncio.wait_for(
                    self.llm_with_tools.ainvoke(messages), timeout=600  # 10 minutos max
                )
                logger.info("[FIN] LLM respondeu com sucesso")
            except asyncio.TimeoutError:
                logger.error("[FIN] TIMEOUT após 600s esperando resposta do LLM!")
                return {
                    "output": "Desculpe, a análise financeira está demorando mais do que o esperado. "
                    "Por favor, tente novamente ou refine sua pergunta para ser mais específica.",
                    "perspective": "financeira",
                }

            logger.info(f"[OK] {self.name} completou processamento (async)")

            # Retornar formato compatível (mantém interface)
            return {
                "output": response.content if hasattr(response, "content") else str(response),
                "intermediate_steps": [],
            }

        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name} (async): {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva financeira: {e!s}",
                "intermediate_steps": [],
            }

    def get_perspective(self) -> str:
        """Retorna a perspectiva do agente."""
        return self.perspective

    def get_name(self) -> str:
        """Retorna o nome do agente."""
        return self.name
