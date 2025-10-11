"""
Orchestrator Agent - Coordenador dos Agentes Especialistas.

Responsável por:
- Analisar a pergunta do usuário
- Determinar quais agentes especialistas devem ser acionados
- Coordenar a execução dos agentes
- Combinar e sintetizar respostas
- Usar Judge Agent para validação
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from loguru import logger

from config.settings import settings, get_llm
from src.agents.financial_agent import FinancialAgent
from src.agents.customer_agent import CustomerAgent
from src.agents.process_agent import ProcessAgent
from src.agents.learning_agent import LearningAgent
from src.agents.judge_agent import JudgeAgent


class RoutingDecision(BaseModel):
    """Decisão de roteamento para agentes."""
    
    agents_to_use: List[str] = Field(
        description="Lista de perspectivas a acionar: 'financeira', 'cliente', 'processos', 'aprendizado'"
    )
    reasoning: str = Field(
        description="Justificativa da escolha dos agentes"
    )
    is_general_question: bool = Field(
        description="Se é uma pergunta geral sobre BSC (acionar todos)"
    )


class SynthesisResult(BaseModel):
    """Resultado da síntese de múltiplas respostas."""
    
    synthesized_answer: str = Field(
        description="Resposta sintetizada combinando insights de múltiplos agentes"
    )
    perspectives_covered: List[str] = Field(
        description="Perspectivas BSC cobertas na resposta"
    )
    confidence: float = Field(
        description="Confiança na resposta (0-1)",
        ge=0.0,
        le=1.0
    )


class Orchestrator:
    """Orquestrador dos agentes especialistas BSC."""
    
    def __init__(self):
        """Inicializa o orquestrador."""
        self.name = "Orchestrator"
        
        # LLM para routing e synthesis (usa factory)
        self.llm = get_llm(temperature=0.3)
        
        # Agentes especialistas
        self.agents = {
            "financeira": FinancialAgent(),
            "cliente": CustomerAgent(),
            "processos": ProcessAgent(),
            "aprendizado": LearningAgent()
        }
        
        # Judge agent
        self.judge = JudgeAgent()
        
        # Prompts
        self.routing_prompt = self._create_routing_prompt()
        self.synthesis_prompt = self._create_synthesis_prompt()
        
        # Chains
        self.routing_chain = self.routing_prompt | self.llm.with_structured_output(RoutingDecision)
        self.synthesis_chain = self.synthesis_prompt | self.llm.with_structured_output(SynthesisResult)
        
        logger.info(f"[OK] {self.name} inicializado com {len(self.agents)} agentes especialistas")
    
    def _create_routing_prompt(self) -> ChatPromptTemplate:
        """Cria prompt para routing de agentes."""
        template = """Você é um roteador inteligente para sistema multi-agente de Balanced Scorecard.

Sua tarefa é analisar a pergunta do usuário e determinar qual(is) agente(s) especialista(s) deve(m) ser acionado(s):

**Agentes Disponíveis:**
- **financeira**: Indicadores financeiros, ROI, lucro, custos, receita
- **cliente**: Satisfação, NPS, retenção, proposta de valor, experiência do cliente
- **processos**: Eficiência operacional, qualidade, ciclo de tempo, produtividade
- **aprendizado**: Capacitação, cultura, inovação, sistemas de informação, crescimento

**Pergunta do Usuário:**
{query}

**Instruções:**
1. Se a pergunta for GERAL sobre BSC (ex: "O que é BSC?", "Como funciona o BSC?"):
   - Marque is_general_question=True
   - Inclua TODAS as 4 perspectivas

2. Se a pergunta menciona EXPLICITAMENTE uma ou mais perspectivas:
   - Selecione apenas as perspectivas mencionadas

3. Se a pergunta é ESPECÍFICA mas não menciona perspectiva:
   - Identifique a(s) perspectiva(s) mais relevante(s) baseado no conteúdo
   - Exemplos:
     * "Como melhorar lucratividade?" → financeira
     * "Como aumentar satisfação do cliente?" → cliente
     * "Como reduzir tempo de produção?" → processos
     * "Como capacitar equipe?" → aprendizado

4. Se a pergunta aborda MÚLTIPLAS perspectivas:
   - Selecione TODAS as perspectivas relevantes

Seja preciso e justifique sua decisão."""

        return ChatPromptTemplate.from_template(template)
    
    def _create_synthesis_prompt(self) -> ChatPromptTemplate:
        """Cria prompt para síntese de respostas."""
        template = """Você é um sintetizador especializado em Balanced Scorecard.

Sua tarefa é combinar múltiplas respostas de agentes especialistas em uma resposta coesa e completa.

**Pergunta Original:**
{original_query}

**Respostas dos Agentes Especialistas:**
{agent_responses}

**Instruções:**
1. Combine as respostas em uma resposta **unificada e coerente**
2. Mantenha TODAS as citações de fontes (Fonte, Página)
3. Organize por tópicos/perspectivas quando apropriado
4. Destaque conexões entre as perspectivas quando relevante
5. Seja conciso mas completo
6. Use markdown para formatação (títulos, listas, negrito)

**Formato da Resposta Sintetizada:**
- Comece com uma visão geral
- Organize por perspectiva se múltiplas foram consultadas
- Termine com uma síntese ou conclusão
- Sempre cite fontes

Calcule confidence baseado em:
- 1.0: Múltiplos agentes concordam, bem fundamentado
- 0.7-0.9: Respostas consistentes mas com algumas lacunas
- 0.5-0.7: Respostas parciais ou com conflitos menores
- <0.5: Informações insuficientes ou conflitantes"""

        return ChatPromptTemplate.from_template(template)
    
    def route_query(self, query: str) -> RoutingDecision:
        """
        Determina quais agentes devem processar a query.
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            Decisão de roteamento
        """
        try:
            logger.info(f"[ROUTING] {self.name} roteando query: '{query[:50]}...'")
            
            decision = self.routing_chain.invoke({"query": query})
            
            logger.info(
                f"[OK] Roteamento: {len(decision.agents_to_use)} agente(s) - "
                f"{', '.join(decision.agents_to_use)}"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no roteamento: {e}")
            # Fallback: aciona todos os agentes
            return RoutingDecision(
                agents_to_use=["financeira", "cliente", "processos", "aprendizado"],
                reasoning=f"Erro no roteamento, acionando todos os agentes. Erro: {str(e)}",
                is_general_question=True
            )
    
    def _invoke_single_agent(
        self,
        agent_name: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Invoca um unico agente especialista.
        Metodo auxiliar para execucao paralela com ThreadPoolExecutor.
        
        Args:
            agent_name: Nome do agente a invocar
            query: Pergunta do usuario
            chat_history: Historico da conversa
            
        Returns:
            Dicionario com resposta do agente ou None se agente nao encontrado
        """
        if agent_name not in self.agents:
            logger.warning(f"[WARN] Agente '{agent_name}' nao encontrado")
            return None
        
        agent = self.agents[agent_name]
        agent_start = time.time()
        
        try:
            result = agent.invoke(query, chat_history)
            elapsed = time.time() - agent_start
            
            logger.info(f"[OK] {agent.get_name()} concluido em {elapsed:.2f}s")
            
            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_time": elapsed
            }
            
        except Exception as e:
            elapsed = time.time() - agent_start
            logger.error(f"[ERRO] Erro ao invocar {agent.get_name()}: {e}")
            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": f"Erro ao processar consulta: {str(e)}",
                "intermediate_steps": [],
                "execution_time": elapsed
            }
    
    def invoke_agents(
        self,
        query: str,
        agent_names: List[str],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Invoca multiplos agentes especialistas EM PARALELO usando ThreadPoolExecutor.
        
        Args:
            query: Pergunta do usuario
            agent_names: Lista de perspectivas a acionar
            chat_history: Historico da conversa
            
        Returns:
            Lista de respostas dos agentes (com execution_time para cada)
        """
        # Timer total de execucao
        start_time = time.time()
        
        # Determinar max_workers (minimo entre num de agentes e config)
        max_workers = min(len(agent_names), settings.agent_max_workers)
        
        logger.info(
            f"[PARALLEL] Executando {len(agent_names)} agente(s) "
            f"com {max_workers} worker(s)"
        )
        
        responses = []
        
        # ThreadPoolExecutor para paralelizacao
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks simultaneamente
            future_to_agent = {
                executor.submit(
                    self._invoke_single_agent,
                    agent_name,
                    query,
                    chat_history
                ): agent_name
                for agent_name in agent_names
            }
            
            # Collect results conforme completam
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    if result is not None:
                        responses.append(result)
                except Exception as e:
                    logger.error(
                        f"[ERRO] Excecao ao aguardar {agent_name}: {e}"
                    )
        
        # Log final com performance
        total_elapsed = time.time() - start_time
        avg_time = total_elapsed / len(responses) if responses else 0
        
        logger.info(
            f"[OK] {len(responses)} agente(s) executado(s) em {total_elapsed:.2f}s "
            f"(media {avg_time:.2f}s/agente, paralelo com {max_workers} workers)"
        )
        
        return responses
    
    async def _ainvoke_single_agent(
        self,
        agent_name: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Invoca um unico agente especialista de forma assincrona.
        Metodo auxiliar para execucao paralela com asyncio.gather().
        
        Args:
            agent_name: Nome do agente a invocar
            query: Pergunta do usuario
            chat_history: Historico da conversa
            
        Returns:
            Dicionario com resposta do agente ou None se agente nao encontrado
        """
        if agent_name not in self.agents:
            logger.warning(f"[WARN] Agente '{agent_name}' nao encontrado")
            return None
        
        agent = self.agents[agent_name]
        agent_start = time.time()
        
        try:
            # Chamar ainvoke() do agente (async)
            result = await agent.ainvoke(query, chat_history)
            elapsed = time.time() - agent_start
            
            logger.info(f"[OK] {agent.get_name()} concluido em {elapsed:.2f}s (async)")
            
            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_time": elapsed
            }
            
        except Exception as e:
            elapsed = time.time() - agent_start
            logger.error(f"[ERRO] Erro ao invocar {agent.get_name()} (async): {e}")
            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": f"Erro ao processar consulta: {str(e)}",
                "intermediate_steps": [],
                "execution_time": elapsed
            }
    
    async def ainvoke_agents(
        self,
        query: str,
        agent_names: List[str],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Invoca multiplos agentes especialistas EM PARALELO usando asyncio.gather().
        VERSAO ASYNC: 10-15% mais rapida que ThreadPoolExecutor para I/O-bound tasks.
        
        Args:
            query: Pergunta do usuario
            agent_names: Lista de perspectivas a acionar
            chat_history: Historico da conversa
            
        Returns:
            Lista de respostas dos agentes (com execution_time para cada)
        """
        # Timer total de execucao
        start_time = time.time()
        
        logger.info(
            f"[ASYNC] Executando {len(agent_names)} agente(s) com asyncio.gather()"
        )
        
        # Criar tasks para todos os agentes
        tasks = [
            self._ainvoke_single_agent(agent_name, query, chat_history)
            for agent_name in agent_names
        ]
        
        # Executar todos simultaneamente com asyncio.gather()
        # return_exceptions=True garante que erros nao quebrem todo o gather
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados validos (None ou Exception sao ignorados)
        responses = []
        for result in results:
            if result is not None and not isinstance(result, Exception):
                responses.append(result)
            elif isinstance(result, Exception):
                logger.error(f"[ERRO] Excecao durante gather: {result}")
        
        # Log final com performance
        total_elapsed = time.time() - start_time
        avg_time = total_elapsed / len(responses) if responses else 0
        
        logger.info(
            f"[OK] {len(responses)} agente(s) executado(s) em {total_elapsed:.2f}s "
            f"(media {avg_time:.2f}s/agente, async com asyncio.gather)"
        )
        
        return responses
    
    def synthesize_responses(
        self,
        original_query: str,
        agent_responses: List[Dict[str, Any]]
    ) -> SynthesisResult:
        """
        Sintetiza múltiplas respostas em uma resposta unificada.
        
        Args:
            original_query: Pergunta original
            agent_responses: Respostas dos agentes
            
        Returns:
            Resposta sintetizada
        """
        try:
            logger.info(f"[SYNTH] {self.name} sintetizando {len(agent_responses)} respostas")
            
            # Formata respostas para o prompt
            formatted_responses = "\n\n".join([
                f"**{resp['agent_name']} (Perspectiva {resp['perspective'].title()}):**\n{resp['response']}"
                for resp in agent_responses
            ])
            
            synthesis = self.synthesis_chain.invoke({
                "original_query": original_query,
                "agent_responses": formatted_responses
            })
            
            logger.info(f"[OK] Síntese completa (confidence: {synthesis.confidence:.2f})")
            return synthesis
            
        except Exception as e:
            logger.error(f"[ERRO] Erro na síntese: {e}")
            # Fallback: concatena respostas
            fallback_answer = "## Respostas dos Especialistas\n\n" + "\n\n".join([
                f"### {resp['agent_name']}\n{resp['response']}"
                for resp in agent_responses
            ])
            
            return SynthesisResult(
                synthesized_answer=fallback_answer,
                perspectives_covered=[r["perspective"] for r in agent_responses],
                confidence=0.5
            )
    
    def process_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        use_judge: bool = True
    ) -> Dict[str, Any]:
        """
        Processa uma query end-to-end.
        
        Args:
            query: Pergunta do usuário
            chat_history: Histórico da conversa
            use_judge: Se deve usar Judge Agent para validação
            
        Returns:
            Resultado completo com resposta sintetizada e metadados
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"[START] {self.name} processando query")
            logger.info(f"{'='*70}")
            
            # 1. Roteamento
            routing = self.route_query(query)
            
            # 2. Invocar agentes
            agent_responses = self.invoke_agents(
                query=query,
                agent_names=routing.agents_to_use,
                chat_history=chat_history
            )
            
            if not agent_responses:
                return {
                    "answer": "Nenhum agente pôde processar a consulta.",
                    "perspectives": [],
                    "confidence": 0.0,
                    "routing": routing.dict(),
                    "evaluations": []
                }
            
            # 3. Síntese
            synthesis = self.synthesize_responses(query, agent_responses)
            
            # 4. Avaliação (opcional)
            evaluations = []
            if use_judge:
                logger.info("[JUDGE] Executando avaliação com Judge Agent")
                evaluations = self.judge.evaluate_multiple(
                    original_query=query,
                    agent_responses=agent_responses,
                    retrieved_documents="[Documentos recuperados pelos agentes]"
                )
            
            result = {
                "answer": synthesis.synthesized_answer,
                "perspectives": synthesis.perspectives_covered,
                "confidence": synthesis.confidence,
                "routing": routing.dict(),
                "agent_responses": agent_responses,
                "evaluations": [e["judgment"].dict() for e in evaluations] if evaluations else []
            }
            
            logger.info(f"{'='*70}")
            logger.info(f"[OK] Query processada com sucesso")
            logger.info(f"{'='*70}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERRO] Erro no processamento: {e}")
            return {
                "answer": f"Erro ao processar consulta: {str(e)}",
                "perspectives": [],
                "confidence": 0.0,
                "routing": {},
                "agent_responses": [],
                "evaluations": []
            }
    
    def get_name(self) -> str:
        """Retorna o nome do orchestrator."""
        return self.name

