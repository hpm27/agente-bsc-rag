"""
Cause-Effect Mapper Tool - Sprint 3.2

Analisa completude, correcao e balanceamento das conexoes causa-efeito
entre objetivos estrategicos das 4 perspectivas BSC.

Framework Kaplan & Norton: Learning -> Process -> Customer -> Financial
- Lower perspectives (enablers) EXPLICAM como atingir higher perspectives (outcomes)
- Minimo 4 conexoes (1 entre cada par de perspectivas adjacentes)
- Ideal 8-12 conexoes para Strategy Map completo

5 Validacoes Executadas:
1. Flow Direction: Conexoes seguem L->P->C->F (nao reverso)
2. No Cycles: Nao ha loops (Financial->Learning e violacao)
3. No Isolated: Todos objectives conectados
4. Minimum Connections: >= 4 (1 entre cada par adjacente)
5. Balance: Conexoes distribuidas entre perspectivas

Scoring: Score = (checks passando / total checks) * 100
- Score >= 80: Conexoes completas
- Score >= 60: Conexoes parciais
- Score < 60: Conexoes insuficientes

Best Practices (Kaplan & Norton 2025, Brightdata Research):
- Conexoes tipicas: Learning enables Process, Process drives Customer, Customer drives Financial
- Todo objective deve ter pelo menos 1 conexao (source ou target)
- Rationale especifico (nao generico como "contribui para")
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage, HumanMessage

if TYPE_CHECKING:
    from src.memory.schemas import ClientProfile

from src.memory.schemas import (
    StrategyMap,
    CauseEffectConnection,
    CauseEffectAnalysis,
    CauseEffectGap,
)
from config.settings import get_llm_for_agent

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES - FLUXO CORRETO BSC
# ============================================================================

# Ordem das perspectivas (bottom-up)
PERSPECTIVE_ORDER = {
    "Aprendizado e Crescimento": 0,  # Learning (base)
    "Processos Internos": 1,  # Process
    "Clientes": 2,  # Customer
    "Financeira": 3,  # Financial (topo)
}

# Abreviacoes para perspectivas
PERSPECTIVE_ABBREV = {
    "Aprendizado e Crescimento": "L",
    "Processos Internos": "P",
    "Clientes": "C",
    "Financeira": "F",
}

# Pares de perspectivas adjacentes (fluxo correto)
ADJACENT_PAIRS = [
    ("Aprendizado e Crescimento", "Processos Internos"),  # L -> P
    ("Processos Internos", "Clientes"),  # P -> C
    ("Clientes", "Financeira"),  # C -> F
]


# ============================================================================
# PROMPTS PARA SUGESTAO DE CONEXOES (LLM)
# ============================================================================

SUGGEST_CONNECTIONS_PROMPT = """Voce e um consultor BSC sênior especialista em conexoes causa-efeito (Kaplan & Norton framework).

STRATEGY MAP ATUAL:
{objectives_summary}

CONEXOES EXISTENTES:
{existing_connections}

GAPS IDENTIFICADOS:
{gaps}

TAREFA:
Sugira conexoes causa-efeito que faltam para completar o Strategy Map.

FRAMEWORK KAPLAN & NORTON:
- Fluxo: Learning -> Process -> Customer -> Financial (bottom-up)
- Learning HABILITA Process (enables): Capacitacao permite melhorar processos
- Process IMPULSIONA Customer (drives): Processos melhores geram satisfacao cliente
- Customer IMPULSIONA Financial (drives): Satisfacao cliente gera receita/lucro

RELATIONSHIP TYPES:
- "enables": Permite alcançar (ex: treinamento -> melhor execucao)
- "drives": Impulsiona diretamente (ex: qualidade -> NPS alto)
- "supports": Suporta indiretamente (ex: cultura -> colaboracao)

STRENGTH LEVELS:
- "strong": Conexao direta e alto impacto
- "medium": Conexao provavel, dependente de contexto
- "weak": Conexao indireta ou condicional

RETORNE ate 4 sugestoes de conexao no formato JSON:
[
    {{
        "source_objective_id": "Nome do objetivo origem",
        "target_objective_id": "Nome do objetivo destino",
        "relationship_type": "enables|drives|supports",
        "strength": "strong|medium|weak",
        "rationale": "Explicacao detalhada da conexao (minimo 30 chars)"
    }}
]

REGRAS:
1. Priorize conexoes entre perspectivas ADJACENTES (L->P, P->C, C->F)
2. NAO sugira conexoes reversas (F->L, C->P)
3. Conecte objetivos ISOLADOS primeiro
4. Rationale ESPECIFICO (nao "contribui para sinergia")
"""


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================


class CauseEffectMapperTool:
    """
    Analisa e sugere melhorias nas conexoes causa-efeito do Strategy Map.

    ARQUITETURA:
    - analyze_cause_effect() - Orquestracao principal
    - _check_flow_direction() - Validar direcao L->P->C->F
    - _detect_cycles() - Detectar loops invalidos
    - _find_isolated_objectives() - Encontrar objectives sem conexao
    - _check_minimum_connections() - Validar minimo 4 conexoes
    - _check_balance() - Validar distribuicao entre perspectivas
    - _suggest_connections() - Sugerir conexoes via LLM+RAG
    - _calculate_completeness_score() - Calcular score final

    DEPENDENCIES:
    - 4 specialist agents (Financial, Customer, Process, Learning) - para RAG (opcional)
    - LLM (GPT-5.1/Claude) para sugestoes de conexoes
    - Schemas: StrategyMap, CauseEffectConnection, CauseEffectAnalysis, CauseEffectGap
    """

    def __init__(
        self,
        financial_agent=None,
        customer_agent=None,
        process_agent=None,
        learning_agent=None,
        llm=None,
    ):
        """
        Inicializa Cause-Effect Mapper.

        Args:
            financial_agent: Agent para RAG perspectiva Financeira (opcional)
            customer_agent: Agent para RAG perspectiva Clientes (opcional)
            process_agent: Agent para RAG perspectiva Processos (opcional)
            learning_agent: Agent para RAG perspectiva Learning (opcional)
            llm: LLM para sugestao de conexoes (default: get_llm_for_agent("analysis"))
        """
        self.financial_agent = financial_agent
        self.customer_agent = customer_agent
        self.process_agent = process_agent
        self.learning_agent = learning_agent
        # SESSAO 45: LLM analysis (Claude Opus 4.5 - analise profunda)
        self.llm = llm or get_llm_for_agent("analysis")

        logger.info("[CauseEffectMapper] Inicializado com LLM para sugestao de conexoes")

    async def analyze_cause_effect(
        self,
        strategy_map: StrategyMap,
        client_profile: "ClientProfile | None" = None,
        suggest_improvements: bool = True,
    ) -> CauseEffectAnalysis:
        """
        Analisa completude das conexoes causa-efeito do Strategy Map.

        STEPS:
        1. Coletar conexoes existentes
        2. Executar 5 validacoes
        3. Identificar gaps
        4. Sugerir conexoes (se habilitado)
        5. Calcular score de completude

        Args:
            strategy_map: Strategy Map com conexoes causa-efeito
            client_profile: Profile da empresa (opcional, para contexto RAG)
            suggest_improvements: Se True, sugere conexoes faltantes via LLM

        Returns:
            CauseEffectAnalysis com score, gaps, sugestoes e recommendations
        """
        logger.info("[CauseEffectMapper] Iniciando analise de conexoes causa-efeito")

        connections = strategy_map.cause_effect_connections
        total_connections = len(connections)

        # Container para resultados
        all_gaps: list[CauseEffectGap] = []
        flow_violations: list[str] = []
        all_recommendations: list[str] = []
        suggested_connections: list[CauseEffectConnection] = []

        # Coletar todos objectives
        all_objectives = self._collect_all_objectives_names(strategy_map)
        logger.info(
            f"[CauseEffectMapper] {total_connections} conexoes, {len(all_objectives)} objectives"
        )

        # VALIDACAO 1: Flow Direction (L->P->C->F)
        violations = self._check_flow_direction(connections, strategy_map)
        flow_violations.extend(violations)
        for violation in violations:
            all_recommendations.append(f"Corrigir direcao: {violation}")

        # VALIDACAO 2: No Cycles (sem loops)
        has_cycles, cycle_descriptions = self._detect_cycles(connections, strategy_map)
        if has_cycles:
            for cycle_desc in cycle_descriptions:
                flow_violations.append(f"Ciclo detectado: {cycle_desc}")
                all_recommendations.append(f"Remover ciclo: {cycle_desc}")

        # VALIDACAO 3: No Isolated Objectives
        isolated = self._find_isolated_objectives(connections, all_objectives)
        for obj_name in isolated:
            all_gaps.append(
                CauseEffectGap(
                    gap_type="isolated_objective",
                    source_perspective=self._get_objective_perspective(strategy_map, obj_name),
                    target_perspective=self._get_objective_perspective(strategy_map, obj_name),
                    source_objective=obj_name,
                    description=f"Objetivo '{obj_name}' nao tem conexoes como source ou target",
                    impact="medium",
                )
            )
            all_recommendations.append(f"Conectar objetivo isolated '{obj_name}'")

        # VALIDACAO 4: Minimum Connections (>= 4)
        has_minimum, missing_pairs = self._check_minimum_connections(connections, strategy_map)
        if not has_minimum:
            for source_persp, target_persp in missing_pairs:
                all_gaps.append(
                    CauseEffectGap(
                        gap_type="missing_connection",
                        source_perspective=source_persp,
                        target_perspective=target_persp,
                        description=f"Nao existe conexao entre '{source_persp}' e '{target_persp}'",
                        impact="high",
                    )
                )
                all_recommendations.append(f"Criar conexao {source_persp} -> {target_persp}")

        # VALIDACAO 5: Balance (distribuicao entre perspectivas)
        balance_gaps, balance_recs = self._check_balance(connections, strategy_map)
        all_gaps.extend(balance_gaps)
        all_recommendations.extend(balance_recs)

        # Contar conexoes por tipo e perspectiva
        connections_by_type = self._count_by_type(connections)
        connections_by_pair = self._count_by_perspective_pair(connections, strategy_map)

        # SUGESTOES via LLM (se habilitado e houver gaps)
        if suggest_improvements and (len(all_gaps) > 0 or len(isolated) > 0):
            logger.info("[CauseEffectMapper] Gerando sugestoes de conexoes via LLM")
            suggested = await self._suggest_connections(strategy_map, all_gaps, isolated)
            suggested_connections.extend(suggested)

        # Calcular score de completude
        completeness_score = self._calculate_completeness_score(
            total_connections,
            len(all_objectives),
            len(isolated),
            len(flow_violations),
            len(all_gaps),
            connections_by_pair,
        )

        # Criar report
        analysis = CauseEffectAnalysis(
            completeness_score=completeness_score,
            is_complete=completeness_score >= 80.0,
            total_connections=total_connections,
            connections_by_type=connections_by_type,
            connections_by_perspective_pair=connections_by_pair,
            gaps=all_gaps,
            flow_violations=flow_violations,
            isolated_objectives=isolated,
            suggested_connections=suggested_connections,
            recommendations=list(set(all_recommendations))[:10],  # Top 10 unicas
            analyzed_at=datetime.now(timezone.utc),
        )

        logger.info(
            f"[CauseEffectMapper] Analise completa: score={completeness_score:.1f}%, "
            f"gaps={len(all_gaps)}, isolated={len(isolated)}, sugestoes={len(suggested_connections)}"
        )

        return analysis

    def _collect_all_objectives_names(self, strategy_map: StrategyMap) -> list[str]:
        """Coleta nomes de todos objectives do Strategy Map."""
        names = []

        perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning,
        ]

        for perspective in perspectives:
            for obj in perspective.objectives:
                names.append(obj.name)

        return names

    def _get_objective_perspective(self, strategy_map: StrategyMap, obj_name: str) -> str:
        """Retorna a perspectiva de um objective pelo nome.

        SESSAO 49 FIX: Adiciona FUZZY MATCHING para resolver desalinhamento
        entre nomes gerados pelo LLM e nomes reais dos objetivos.

        Algoritmo:
        1. Tentar match EXATO primeiro (mais rápido)
        2. Se não encontrar, fazer fuzzy match com difflib.SequenceMatcher
        3. Retornar perspectiva se match ratio >= 0.80 (80% similaridade)
        """
        from difflib import SequenceMatcher

        perspectives_map = {
            "Financeira": strategy_map.financial,
            "Clientes": strategy_map.customer,
            "Processos Internos": strategy_map.process,
            "Aprendizado e Crescimento": strategy_map.learning,
        }

        # DEBUG: Log estado das perspectivas (apenas uma vez)
        if not hasattr(self, "_perspective_debug_logged"):
            self._perspective_debug_logged = True
            for persp_name, perspective in perspectives_map.items():
                if perspective is None:
                    logger.warning(f"[DEBUG] Perspectiva '{persp_name}' e None!")
                elif not perspective.objectives:
                    logger.warning(f"[DEBUG] Perspectiva '{persp_name}' tem 0 objetivos!")
                else:
                    obj_names = [obj.name[:40] for obj in perspective.objectives[:2]]
                    logger.info(
                        f"[DEBUG] Perspectiva '{persp_name}': {len(perspective.objectives)} objetivos. "
                        f"Primeiros: {obj_names}"
                    )

        # PASSO 1: Tentar match EXATO (comportamento original)
        for persp_name, perspective in perspectives_map.items():
            # Null-check: perspective pode ser None se strategy_map incompleto
            if perspective is None or not perspective.objectives:
                continue
            for obj in perspective.objectives:
                if obj.name == obj_name:
                    return persp_name

        # PASSO 2: FUZZY MATCHING - encontrar objetivo mais similar
        best_match_ratio = 0.0
        best_match_persp = "Desconhecida"
        best_match_name = ""

        for persp_name, perspective in perspectives_map.items():
            # Null-check: perspective pode ser None se strategy_map incompleto
            if perspective is None or not perspective.objectives:
                continue
            for obj in perspective.objectives:
                # Normalizar para comparação (lowercase, sem espaços extras)
                name_normalized = obj.name.lower().strip()
                query_normalized = obj_name.lower().strip()

                ratio = SequenceMatcher(None, name_normalized, query_normalized).ratio()

                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_persp = persp_name
                    best_match_name = obj.name

        # PASSO 3: Retornar se ratio >= 0.80 (80% similaridade)
        if best_match_ratio >= 0.80:
            logger.debug(
                f"[FUZZY MATCH] '{obj_name[:40]}...' -> '{best_match_name[:40]}...' "
                f"({best_match_ratio:.0%}) = {best_match_persp}"
            )
            return best_match_persp

        # Nenhum match encontrado - log com mais contexto
        logger.warning(
            f"[WARN] Objetivo nao encontrado (nem fuzzy): '{obj_name[:50]}...' | "
            f"Melhor match: '{best_match_name[:30]}...' ({best_match_ratio:.0%})"
        )
        return "Desconhecida"

    def _check_flow_direction(
        self, connections: list[CauseEffectConnection], strategy_map: StrategyMap
    ) -> list[str]:
        """
        Valida se conexoes seguem fluxo correto L->P->C->F.

        REGRA: Source perspective deve ter order <= target perspective order
        (Learning=0, Process=1, Customer=2, Financial=3)
        """
        violations = []

        for conn in connections:
            source_persp = self._get_objective_perspective(strategy_map, conn.source_objective_id)
            target_persp = self._get_objective_perspective(strategy_map, conn.target_objective_id)

            source_order = PERSPECTIVE_ORDER.get(source_persp, -1)
            target_order = PERSPECTIVE_ORDER.get(target_persp, -1)

            # Violacao: source esta ACIMA do target (ex: Financial -> Learning)
            if source_order > target_order and source_order >= 0 and target_order >= 0:
                source_abbrev = PERSPECTIVE_ABBREV.get(source_persp, "?")
                target_abbrev = PERSPECTIVE_ABBREV.get(target_persp, "?")
                violations.append(
                    f"Conexao {source_abbrev}->{target_abbrev} viola fluxo (correto: L->P->C->F)"
                )

        return violations

    def _detect_cycles(
        self, connections: list[CauseEffectConnection], strategy_map: StrategyMap
    ) -> tuple[bool, list[str]]:
        """
        Detecta ciclos nas conexoes usando DFS.

        REGRA: Nao deve existir caminho A->B->C->A
        """
        # Construir grafo de adjacencia
        graph: dict[str, list[str]] = {}
        for conn in connections:
            source = conn.source_objective_id
            target = conn.target_objective_id
            if source not in graph:
                graph[source] = []
            graph[source].append(target)

        # DFS para detectar ciclos
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Ciclo encontrado
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(" -> ".join(cycle))
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph.keys():
            if node not in visited:
                dfs(node, [])

        return len(cycles) > 0, cycles

    def _find_isolated_objectives(
        self, connections: list[CauseEffectConnection], all_objectives: list[str]
    ) -> list[str]:
        """
        Encontra objectives que nao tem nenhuma conexao.

        REGRA: Todo objective deve aparecer como source OU target

        SESSAO 49 FIX: Adiciona fuzzy matching para evitar falsos positivos
        quando nomes nas conexoes sao ligeiramente diferentes dos objetivos reais.
        """
        from difflib import SequenceMatcher

        # Coletar nomes nas conexoes
        connected_names = set()
        for conn in connections:
            connected_names.add(conn.source_objective_id)
            connected_names.add(conn.target_objective_id)

        def is_connected(obj_name: str) -> bool:
            """Verifica se objetivo esta conectado (exact ou fuzzy match)."""
            # PASSO 1: Exact match
            if obj_name in connected_names:
                return True

            # PASSO 2: Fuzzy match (threshold 80%)
            obj_normalized = obj_name.lower().strip()
            for conn_name in connected_names:
                conn_normalized = conn_name.lower().strip()
                ratio = SequenceMatcher(None, obj_normalized, conn_normalized).ratio()
                if ratio >= 0.80:
                    logger.debug(
                        f"[FUZZY CONNECTED] '{obj_name[:30]}...' matches "
                        f"'{conn_name[:30]}...' ({ratio:.0%})"
                    )
                    return True

            return False

        isolated = [obj for obj in all_objectives if not is_connected(obj)]

        # DEBUG: Log resultado
        if isolated:
            logger.info(
                f"[DEBUG] _find_isolated_objectives: {len(isolated)}/{len(all_objectives)} "
                f"objetivos isolados"
            )

        return isolated

    def _check_minimum_connections(
        self, connections: list[CauseEffectConnection], strategy_map: StrategyMap
    ) -> tuple[bool, list[tuple[str, str]]]:
        """
        Valida se existe pelo menos 1 conexao entre cada par de perspectivas adjacentes.

        REGRA: L->P, P->C, C->F devem ter pelo menos 1 conexao cada
        """
        connections_by_pair = self._count_by_perspective_pair(connections, strategy_map)

        missing_pairs = []

        if connections_by_pair.get("L->P", 0) == 0:
            missing_pairs.append(("Aprendizado e Crescimento", "Processos Internos"))

        if connections_by_pair.get("P->C", 0) == 0:
            missing_pairs.append(("Processos Internos", "Clientes"))

        if connections_by_pair.get("C->F", 0) == 0:
            missing_pairs.append(("Clientes", "Financeira"))

        has_minimum = len(missing_pairs) == 0 and len(connections) >= 4
        return has_minimum, missing_pairs

    def _check_balance(
        self, connections: list[CauseEffectConnection], strategy_map: StrategyMap
    ) -> tuple[list[CauseEffectGap], list[str]]:
        """
        Valida distribuicao balanceada de conexoes entre perspectivas.

        REGRA: Nao deve ter concentracao excessiva em um par de perspectivas
        """
        gaps = []
        recommendations = []

        connections_by_pair = self._count_by_perspective_pair(connections, strategy_map)
        total = sum(connections_by_pair.values())

        if total == 0:
            return gaps, recommendations

        # Verificar se algum par tem mais de 50% das conexoes (desbalanceado)
        for pair, count in connections_by_pair.items():
            if count > total * 0.6 and total >= 4:
                gaps.append(
                    CauseEffectGap(
                        gap_type="weak_connection",
                        source_perspective=pair.split("->")[0],
                        target_perspective=pair.split("->")[1],
                        description=f"Conexoes concentradas em {pair} ({count}/{total} = {count/total*100:.0f}%)",
                        impact="low",
                    )
                )
                recommendations.append(f"Distribuir conexoes - {pair} esta super-representado")

        return gaps, recommendations

    def _count_by_type(self, connections: list[CauseEffectConnection]) -> dict[str, int]:
        """Conta conexoes por tipo de relacionamento."""
        counts = {"enables": 0, "drives": 0, "supports": 0}

        for conn in connections:
            if conn.relationship_type in counts:
                counts[conn.relationship_type] += 1

        return counts

    def _count_by_perspective_pair(
        self, connections: list[CauseEffectConnection], strategy_map: StrategyMap
    ) -> dict[str, int]:
        """Conta conexoes por par de perspectivas."""
        counts = {
            "L->P": 0,
            "P->C": 0,
            "C->F": 0,
            "L->C": 0,
            "L->F": 0,
            "P->F": 0,
        }

        # DEBUG: Log objetivos disponíveis no strategy_map
        all_obj_names = self._collect_all_objectives_names(strategy_map)
        logger.info(
            f"[DEBUG] _count_by_perspective_pair: {len(connections)} conexoes, "
            f"{len(all_obj_names)} objetivos no strategy_map"
        )
        if all_obj_names:
            logger.info(f"[DEBUG] Primeiros 3 objetivos do map: {all_obj_names[:3]}")

        unknown_count = 0
        for idx, conn in enumerate(connections):
            # SESSAO 49 FIX: Usar campos source_perspective/target_perspective se disponiveis
            # Isso evita busca por nome (mais robusto)
            if conn.source_perspective:
                source_persp = conn.source_perspective
            else:
                source_persp = self._get_objective_perspective(strategy_map, conn.source_objective_id)
            
            if conn.target_perspective:
                target_persp = conn.target_perspective
            else:
                target_persp = self._get_objective_perspective(strategy_map, conn.target_objective_id)

            source_abbrev = PERSPECTIVE_ABBREV.get(source_persp, "?")
            target_abbrev = PERSPECTIVE_ABBREV.get(target_persp, "?")

            # DEBUG: Log primeiras 3 conexões para diagnóstico
            if idx < 3:
                logger.info(
                    f"[DEBUG] Conexao {idx}: source='{conn.source_objective_id[:50]}...' -> "
                    f"persp={source_persp} ({source_abbrev}), "
                    f"target='{conn.target_objective_id[:50]}...' -> persp={target_persp} ({target_abbrev})"
                )

            pair_key = f"{source_abbrev}->{target_abbrev}"
            if pair_key in counts:
                counts[pair_key] += 1
            else:
                unknown_count += 1

        # DEBUG: Log se muitas conexões desconhecidas
        if unknown_count > 0:
            logger.warning(
                f"[DEBUG] {unknown_count}/{len(connections)} conexoes com perspectiva DESCONHECIDA (nao contadas)"
            )

        logger.info(f"[DEBUG] Contagem final por par: {counts}")
        return counts

    async def _suggest_connections(
        self,
        strategy_map: StrategyMap,
        gaps: list[CauseEffectGap],
        isolated_objectives: list[str],
    ) -> list[CauseEffectConnection]:
        """
        Sugere conexoes faltantes usando LLM.

        STEPS:
        1. Preparar contexto (objectives, conexoes existentes, gaps)
        2. Chamar LLM com prompt especializado
        3. Parsear resposta para CauseEffectConnection
        """
        # Preparar resumo de objectives
        objectives_summary = self._prepare_objectives_summary(strategy_map)

        # Preparar conexoes existentes
        existing_summary = self._prepare_connections_summary(strategy_map.cause_effect_connections)

        # Preparar gaps
        gaps_summary = "\n".join([f"- {gap.gap_type}: {gap.description}" for gap in gaps])
        if isolated_objectives:
            gaps_summary += "\nObjetivos isolados:\n"
            gaps_summary += "\n".join([f"- {obj}" for obj in isolated_objectives])

        prompt_content = SUGGEST_CONNECTIONS_PROMPT.format(
            objectives_summary=objectives_summary,
            existing_connections=existing_summary,
            gaps=gaps_summary if gaps_summary else "Nenhum gap identificado",
        )

        messages = [
            SystemMessage(content="Voce e um consultor BSC especialista em conexoes causa-efeito."),
            HumanMessage(content=prompt_content),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            suggested = self._parse_suggested_connections(response.content)
            return suggested

        except Exception as e:
            logger.warning(f"[CauseEffectMapper] Erro ao sugerir conexoes: {e}")
            return []

    def _prepare_objectives_summary(self, strategy_map: StrategyMap) -> str:
        """Prepara resumo de objectives para o prompt."""
        summary = ""

        perspectives_map = {
            "Financeira": strategy_map.financial,
            "Clientes": strategy_map.customer,
            "Processos Internos": strategy_map.process,
            "Aprendizado e Crescimento": strategy_map.learning,
        }

        for persp_name, perspective in perspectives_map.items():
            abbrev = PERSPECTIVE_ABBREV.get(persp_name, "?")
            summary += f"\n{abbrev} - {persp_name}:\n"
            for idx, obj in enumerate(perspective.objectives, 1):
                summary += f"  {idx}. {obj.name}\n"

        return summary

    def _prepare_connections_summary(self, connections: list[CauseEffectConnection]) -> str:
        """Prepara resumo de conexoes existentes para o prompt."""
        if not connections:
            return "Nenhuma conexao existente"

        summary = ""
        for conn in connections:
            summary += f"- {conn.source_objective_id} --[{conn.relationship_type}]--> {conn.target_objective_id}\n"

        return summary

    def _parse_suggested_connections(self, response_text: str) -> list[CauseEffectConnection]:
        """
        Parseia resposta do LLM para lista de CauseEffectConnection.

        Tenta extrair JSON da resposta e converter para schemas.
        """
        import json
        import re

        suggested = []

        try:
            # Tentar encontrar JSON na resposta
            json_match = re.search(r"\[[\s\S]*\]", response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                for item in data:
                    if isinstance(item, dict):
                        try:
                            conn = CauseEffectConnection(
                                source_objective_id=item.get("source_objective_id", ""),
                                target_objective_id=item.get("target_objective_id", ""),
                                relationship_type=item.get("relationship_type", "supports"),
                                strength=item.get("strength", "medium"),
                                rationale=item.get("rationale", "Conexao sugerida pelo sistema")[
                                    :200
                                ],
                            )
                            suggested.append(conn)
                        except Exception as e:
                            logger.warning(f"[CauseEffectMapper] Erro ao parsear sugestao: {e}")
                            continue

        except json.JSONDecodeError as e:
            logger.warning(f"[CauseEffectMapper] Erro ao parsear JSON: {e}")
        except Exception as e:
            logger.warning(f"[CauseEffectMapper] Erro inesperado ao parsear: {e}")

        return suggested

    def _calculate_completeness_score(
        self,
        total_connections: int,
        total_objectives: int,
        isolated_count: int,
        violations_count: int,
        gaps_count: int,
        connections_by_pair: dict[str, int],
    ) -> float:
        """
        Calcula score de completude das conexoes.

        Fatores:
        - Conexoes por objective (ideal: 1.0-1.5)
        - Objectives isolados (penalidade)
        - Violacoes de fluxo (penalidade)
        - Pares adjacentes conectados (bonus)
        """
        # Base score
        base_score = 100.0

        # Fator 1: Ratio conexoes/objectives (ideal 1.0-1.5)
        if total_objectives > 0:
            ratio = total_connections / total_objectives
            if ratio < 0.5:
                base_score -= 30  # Muito poucas conexoes
            elif ratio < 1.0:
                base_score -= 15  # Abaixo do ideal
            # Ratio >= 1.0 nao penaliza

        # Fator 2: Penalidade por isolated
        base_score -= isolated_count * 10

        # Fator 3: Penalidade por violacoes
        base_score -= violations_count * 15

        # Fator 4: Penalidade por gaps
        base_score -= gaps_count * 5

        # Fator 5: Bonus por pares adjacentes completos
        adjacent_pairs_connected = 0
        if connections_by_pair.get("L->P", 0) > 0:
            adjacent_pairs_connected += 1
        if connections_by_pair.get("P->C", 0) > 0:
            adjacent_pairs_connected += 1
        if connections_by_pair.get("C->F", 0) > 0:
            adjacent_pairs_connected += 1

        if adjacent_pairs_connected == 3:
            base_score += 10  # Bonus: todos pares adjacentes conectados

        # Clamp entre 0 e 100
        return max(0, min(100, base_score))


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_cause_effect_mapper_tool(
    financial_agent=None,
    customer_agent=None,
    process_agent=None,
    learning_agent=None,
    llm=None,
) -> CauseEffectMapperTool:
    """Factory function para criar Cause-Effect Mapper Tool."""
    return CauseEffectMapperTool(
        financial_agent=financial_agent,
        customer_agent=customer_agent,
        process_agent=process_agent,
        learning_agent=learning_agent,
        llm=llm,
    )
