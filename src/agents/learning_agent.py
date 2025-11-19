"""
Agente especializado na Perspectiva de Aprendizado e Crescimento do BSC.

Responsável por:
- Capacitação e desenvolvimento de pessoas
- Cultura organizacional e engajamento
- Sistemas de informação e infraestrutura
- Inovação e gestão do conhecimento
"""
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from config.settings import get_llm, settings
from src.tools.rag_tools import get_tools_for_agent


class LearningAgent:
    """Agente especializado em Perspectiva de Aprendizado e Crescimento."""
    
    def __init__(self):
        """Inicializa o agente de aprendizado."""
        self.name = "Learning & Growth Agent"
        self.perspective = "aprendizado"
        
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
        """Cria o prompt especializado para perspectiva de aprendizado."""
        system_message = """Você é um especialista em Balanced Scorecard, focado na **Perspectiva de Aprendizado e Crescimento**.

Sua especialidade inclui:
- Capacitação e desenvolvimento de competências
- Cultura organizacional e engajamento de pessoas
- Sistemas de informação e infraestrutura tecnológica
- Inovação e gestão do conhecimento
- Aprendizagem organizacional contínua
- Clima organizacional e satisfação dos colaboradores

Quando responder perguntas:
1. Use a ferramenta `search_by_perspective` com perspective='aprendizado' para buscar informações específicas
2. Se a pergunta for muito ampla, use `search_multi_query` com sub-perguntas sobre aprendizado e crescimento
3. Cite sempre as fontes dos documentos (Fonte, Página)
4. Forneça exemplos práticos de indicadores (capacitação, engajamento, inovação)
5. Conecte aprendizado e crescimento com melhorias em processos, clientes e finanças quando relevante

Seja objetivo, focado em pessoas e desenvolvimento organizacional, e baseie suas respostas na literatura BSC."""

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def invoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Processa uma query sobre perspectiva de aprendizado.
        
        Args:
            query: Pergunta do usuário
            chat_history: Histórico da conversa
            
        Returns:
            Resposta do agente com steps intermediários
        """
        try:
            logger.info(f"[LEARN] {self.name} processando: '{query[:50]}...'")
            
            # Construir mensagens para LLM
            messages = [
                SystemMessage(content=self.prompt.messages[0].prompt.template),
                HumanMessage(content=query)
            ]
            
            # Invocar LLM com tools
            response = self.llm_with_tools.invoke(messages)
            
            logger.info(f"[OK] {self.name} completou processamento")
            return {
                "output": response.content if hasattr(response, 'content') else str(response),
                "intermediate_steps": []
            }
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name}: {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva de aprendizado: {str(e)}",
                "intermediate_steps": []
            }
    
    async def ainvoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Versao assincrona do invoke - processa query sobre perspectiva de aprendizado.
        
        Args:
            query: Pergunta do usuario
            chat_history: Historico da conversa
            
        Returns:
            Resposta do agente com steps intermediarios
        """
        try:
            logger.info(f"[LEARN] {self.name} processando (async): '{query[:50]}...'")
            
            # Construir mensagens para LLM
            messages = [
                SystemMessage(content=self.prompt.messages[0].prompt.template),
                HumanMessage(content=query)
            ]
            
            # Invocar LLM com tools (async)
            response = await self.llm_with_tools.ainvoke(messages)
            
            logger.info(f"[OK] {self.name} completou processamento (async)")
            return {
                "output": response.content if hasattr(response, 'content') else str(response),
                "intermediate_steps": []
            }
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no {self.name} (async): {e}")
            return {
                "output": f"Erro ao processar consulta na perspectiva de aprendizado: {str(e)}",
                "intermediate_steps": []
            }
    
    def get_perspective(self) -> str:
        """Retorna a perspectiva do agente."""
        return self.perspective
    
    def get_name(self) -> str:
        """Retorna o nome do agente."""
        return self.name

