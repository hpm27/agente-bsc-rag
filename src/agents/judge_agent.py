"""
Judge Agent - Validador de Respostas.

Responsável por:
- Avaliar qualidade e completude das respostas dos agentes especialistas
- Verificar citação de fontes
- Detectar alucinações e informações incorretas
- Determinar se resposta atende à pergunta original
- Sugerir melhorias ou perguntas complementares
"""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from loguru import logger

from config.settings import settings


class JudgmentResult(BaseModel):
    """Resultado da avaliação do Judge."""
    
    quality_score: float = Field(
        description="Score de qualidade de 0 a 1",
        ge=0.0,
        le=1.0
    )
    is_complete: bool = Field(
        description="Se a resposta está completa"
    )
    has_sources: bool = Field(
        description="Se a resposta cita fontes apropriadamente"
    )
    is_grounded: bool = Field(
        description="Se a resposta está fundamentada nos documentos"
    )
    issues: List[str] = Field(
        description="Lista de problemas encontrados",
        default_factory=list
    )
    suggestions: List[str] = Field(
        description="Sugestões de melhoria",
        default_factory=list
    )
    verdict: str = Field(
        description="Veredito final: 'approved', 'needs_improvement', ou 'rejected'"
    )
    reasoning: str = Field(
        description="Justificativa da avaliação"
    )


class JudgeAgent:
    """Agente Judge para validação de respostas."""
    
    def __init__(self):
        """Inicializa o Judge Agent."""
        self.name = "Judge Agent"
        
        # LLM com temperatura 0 para consistência
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.0,  # Máxima consistência
            max_tokens=1500,
            api_key=settings.openai_api_key
        )
        
        # Prompt de avaliação
        self.prompt = self._create_prompt()
        
        # Chain estruturado
        self.chain = self.prompt | self.llm.with_structured_output(JudgmentResult)
        
        logger.info(f"✅ {self.name} inicializado")
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Cria o prompt de avaliação."""
        template = """Você é um Judge Agent especializado em avaliar respostas sobre Balanced Scorecard (BSC).

Sua tarefa é avaliar criticamente a resposta fornecida por um agente especialista, verificando:

1. **Qualidade** (0-1): Quão bem a resposta atende à pergunta?
2. **Completude**: A resposta aborda todos os aspectos da pergunta?
3. **Citação de Fontes**: A resposta cita fontes (Fonte, Página) adequadamente?
4. **Fundamentação**: A resposta está baseada nos documentos recuperados (grounded)?
5. **Alucinações**: A resposta inventa informações não presentes nos documentos?

**Pergunta Original:**
{original_query}

**Resposta do Agente:**
{agent_response}

**Documentos Recuperados:**
{retrieved_documents}

**Instruções de Avaliação:**
- quality_score: 0.0 (péssima) a 1.0 (excelente)
- is_complete: True se responde completamente a pergunta
- has_sources: True se cita fontes apropriadamente
- is_grounded: True se baseada nos documentos (sem alucinações)
- issues: Liste problemas encontrados (ex: "Não cita fontes", "Informação X não está nos documentos")
- suggestions: Sugestões de melhoria (ex: "Adicionar citação na afirmação Y")
- verdict: 
  * 'approved' se quality_score >= 0.8 e is_grounded=True
  * 'needs_improvement' se 0.5 <= quality_score < 0.8
  * 'rejected' se quality_score < 0.5 ou is_grounded=False
- reasoning: Justificativa em 2-3 sentenças

Seja rigoroso mas justo. Priorize respostas fundamentadas em fontes."""

        return ChatPromptTemplate.from_template(template)
    
    def evaluate(
        self,
        original_query: str,
        agent_response: str,
        retrieved_documents: str,
        agent_name: str = "Unknown Agent"
    ) -> JudgmentResult:
        """
        Avalia a resposta de um agente especialista.
        
        Args:
            original_query: Pergunta original do usuário
            agent_response: Resposta fornecida pelo agente
            retrieved_documents: Documentos recuperados e usados
            agent_name: Nome do agente que forneceu a resposta
            
        Returns:
            Resultado da avaliação
        """
        try:
            logger.info(f"⚖️ {self.name} avaliando resposta de {agent_name}")
            
            result = self.chain.invoke({
                "original_query": original_query,
                "agent_response": agent_response,
                "retrieved_documents": retrieved_documents
            })
            
            logger.info(
                f"✅ Avaliação completa: "
                f"score={result.quality_score:.2f}, "
                f"verdict={result.verdict}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no {self.name}: {e}")
            # Retorna avaliação neutra em caso de erro
            return JudgmentResult(
                quality_score=0.5,
                is_complete=False,
                has_sources=False,
                is_grounded=False,
                issues=[f"Erro na avaliação: {str(e)}"],
                suggestions=["Reavalie manualmente a resposta"],
                verdict="needs_improvement",
                reasoning=f"Falha no processo de avaliação: {str(e)}"
            )
    
    def evaluate_multiple(
        self,
        original_query: str,
        agent_responses: List[Dict[str, Any]],
        retrieved_documents: str
    ) -> List[Dict[str, Any]]:
        """
        Avalia múltiplas respostas (de diferentes agentes).
        
        Args:
            original_query: Pergunta original
            agent_responses: Lista de respostas com formato:
                [{"agent_name": "...", "response": "..."}, ...]
            retrieved_documents: Documentos recuperados
            
        Returns:
            Lista de avaliações com formato:
                [{"agent_name": "...", "response": "...", "judgment": JudgmentResult}, ...]
        """
        results = []
        
        for agent_resp in agent_responses:
            judgment = self.evaluate(
                original_query=original_query,
                agent_response=agent_resp["response"],
                retrieved_documents=retrieved_documents,
                agent_name=agent_resp.get("agent_name", "Unknown")
            )
            
            results.append({
                **agent_resp,
                "judgment": judgment
            })
        
        # Ordena por quality_score (melhor primeiro)
        results.sort(key=lambda x: x["judgment"].quality_score, reverse=True)
        
        logger.info(f"✅ Avaliadas {len(results)} respostas")
        return results
    
    def get_name(self) -> str:
        """Retorna o nome do agente."""
        return self.name

