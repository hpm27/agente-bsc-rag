"""
Agente especializado na Perspectiva do Cliente do BSC.

Responsável por:
- Satisfação e retenção de clientes
- Proposta de valor e segmentação
- NPS, CSAT e outras métricas de cliente
- Experiência do cliente e jornada
"""
from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from config.settings import get_llm, settings
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
        
        # Agent executor (tool calling - compatible com Claude/OpenAI/Gemini)
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=settings.max_iterations,
            return_intermediate_steps=True
        )
        
        logger.info(f"[OK] {self.name} inicializado")
    
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

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def invoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
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
            
            result = self.executor.invoke({
                "input": query,
                "chat_history": chat_history or []
            })
            
            logger.info(f"[OK] {self.name} completou processamento")
            return result
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name}: {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva do cliente: {str(e)}",
                "intermediate_steps": []
            }
    
    async def ainvoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Versao assincrona do invoke - processa query sobre perspectiva do cliente.
        
        Args:
            query: Pergunta do usuario
            chat_history: Historico da conversa
            
        Returns:
            Resposta do agente com steps intermediarios
        """
        try:
            logger.info(f"[CUST] {self.name} processando (async): '{query[:50]}...'")
            
            result = await self.executor.ainvoke({
                "input": query,
                "chat_history": chat_history or []
            })
            
            logger.info(f"[OK] {self.name} completou processamento (async)")
            return result
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name} (async): {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva do cliente: {str(e)}",
                "intermediate_steps": []
            }
    
    def get_perspective(self) -> str:
        """Retorna a perspectiva do agente."""
        return self.perspective
    
    def get_name(self) -> str:
        """Retorna o nome do agente."""
        return self.name

