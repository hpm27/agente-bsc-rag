"""
Agente especializado na Perspectiva Financeira do BSC.

Responsável por:
- Indicadores financeiros (receita, lucro, ROI, EVA)
- Análise de custos e eficiência operacional
- Objetivos e metas financeiras
- Relação entre estratégia e resultados financeiros
"""
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from config.settings import get_llm, settings
from src.tools.rag_tools import get_tools_for_agent


class FinancialAgent:
    """Agente especializado em Perspectiva Financeira."""
    
    def __init__(self):
        """Inicializa o agente financeiro."""
        self.name = "Financial Agent"
        self.perspective = "financeira"
        
        # LLM (usa factory que detecta provider automaticamente)
        self.llm = get_llm()
        
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

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def invoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
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
            messages = [
                SystemMessage(content=self.prompt.messages[0].prompt.template)
            ]
            
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
                "output": response.content if hasattr(response, 'content') else str(response),
                "intermediate_steps": []
            }
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name}: {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva financeira: {str(e)}",
                "intermediate_steps": []
            }
    
    async def ainvoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Versao assincrona do invoke - processa query sobre perspectiva financeira.
        
        Args:
            query: Pergunta do usuario
            chat_history: Historico da conversa
            
        Returns:
            Resposta do agente com steps intermediarios
        """
        try:
            logger.info(f"[FIN] {self.name} processando (async): '{query[:50]}...'")
            
            # Construir mensagens (pattern LangChain v1.0)
            messages = [
                SystemMessage(content=self.prompt.messages[0].prompt.template)
            ]
            
            # Adicionar histórico se existir
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Adicionar query atual
            messages.append(HumanMessage(content=query))
            
            # Invocar LLM com tools (async)
            response = await self.llm_with_tools.ainvoke(messages)
            
            logger.info(f"[OK] {self.name} completou processamento (async)")
            
            # Retornar formato compatível (mantém interface)
            return {
                "output": response.content if hasattr(response, 'content') else str(response),
                "intermediate_steps": []
            }
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name} (async): {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva financeira: {str(e)}",
                "intermediate_steps": []
            }
    
    def get_perspective(self) -> str:
        """Retorna a perspectiva do agente."""
        return self.perspective
    
    def get_name(self) -> str:
        """Retorna o nome do agente."""
        return self.name

