"""
Agente especializado na Perspectiva Financeira do BSC.

Responsável por:
- Indicadores financeiros (receita, lucro, ROI, EVA)
- Análise de custos e eficiência operacional
- Objetivos e metas financeiras
- Relação entre estratégia e resultados financeiros
"""
from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from loguru import logger

from config.settings import settings
from src.tools.rag_tools import get_tools_for_agent


class FinancialAgent:
    """Agente especializado em Perspectiva Financeira."""
    
    def __init__(self):
        """Inicializa o agente financeiro."""
        self.name = "Financial Agent"
        self.perspective = "financeira"
        
        # LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key
        )
        
        # Tools
        self.tools = get_tools_for_agent()
        
        # Prompt especializado
        self.prompt = self._create_prompt()
        
        # Agent executor
        self.agent = create_openai_functions_agent(
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
        
        logger.info(f"✅ {self.name} inicializado")
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Cria o prompt especializado para perspectiva financeira."""
        system_message = """Você é um especialista em Balanced Scorecard, focado na **Perspectiva Financeira**.

Sua especialidade inclui:
- 📊 Indicadores financeiros: receita, lucro, ROI, EVA, margem de contribuição
- 💰 Análise de custos e eficiência operacional
- 🎯 Objetivos e metas financeiras estratégicas
- 📈 Relação entre estratégia empresarial e resultados financeiros
- 💡 Criação de valor para acionistas e stakeholders

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
            logger.info(f"💰 {self.name} processando: '{query[:50]}...'")
            
            result = self.executor.invoke({
                "input": query,
                "chat_history": chat_history or []
            })
            
            logger.info(f"✅ {self.name} completou processamento")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no {self.name}: {e}")
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

