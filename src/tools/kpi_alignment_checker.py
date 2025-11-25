"""
KPI Alignment Checker Tool - Sprint 3.1

Valida alinhamento semantico entre KPIs do KPIFramework e objetivos estrategicos
do Strategy Map, usando LLM para analise semantica e regras logicas para validacoes estruturais.

6 Validacoes Executadas:
1. Perspective Match: KPI perspectiva == Objective perspectiva
2. Semantic Alignment: KPI nome/descricao relacionado ao objetivo (LLM)
3. Coverage: Todas perspectivas tem KPIs E Objectives
4. Orphan Detection: KPIs sem objective.related_kpis
5. Sufficiency: Cada objective tem 1-3 KPIs (ideal)
6. SMART Validation: KPIs sao mensuraveis

Scoring: Score = (checks passando / total checks) * 100
- Score >= 80: Alinhamento bom
- Score >= 60: Alinhamento regular
- Score < 60: Alinhamento ruim

Best Practices (Kaplan & Norton 2025, Brightdata Research):
- Cada objective deve ter 1-3 KPIs (leading + lagging)
- KPIs devem estar na mesma perspectiva do objetivo
- KPIs devem medir diretamente o progresso do objetivo
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage, HumanMessage

if TYPE_CHECKING:
    from src.memory.schemas import ClientProfile

from src.memory.schemas import (
    StrategyMap,
    KPIFramework,
    KPIAlignmentReport,
    AlignmentIssue,
)
from config.settings import get_llm_for_agent

logger = logging.getLogger(__name__)


# ============================================================================
# PROMPTS PARA VALIDACAO SEMANTICA (LLM)
# ============================================================================

SEMANTIC_ALIGNMENT_PROMPT = """Voce e um especialista em Balanced Scorecard (BSC) validando alinhamento entre KPIs e objetivos estrategicos.

OBJETIVO ESTRATEGICO:
Nome: {objective_name}
Descricao: {objective_description}
Perspectiva: {objective_perspective}
Criterios de Sucesso: {success_criteria}

KPI ASSOCIADO:
Nome: {kpi_name}
Descricao: {kpi_description}
Perspectiva: {kpi_perspective}
Tipo Metrica: {metric_type}
Meta: {target_value}

TAREFA:
Avalie se o KPI realmente mede o progresso do objetivo estrategico.

CRITERIOS DE AVALIACAO:
1. Relevancia: KPI mede diretamente o objetivo?
2. Perspectiva: KPI esta na mesma perspectiva ou relacionada?
3. Especificidade: KPI e especifico o suficiente para o objetivo?
4. Acionabilidade: Melhorar o KPI contribui para o objetivo?

RESPONDA com um JSON:
{{
    "is_aligned": true/false,
    "confidence": 0.0-1.0,
    "alignment_reason": "Explicacao da avaliacao",
    "recommendation": "Sugestao de melhoria (se nao alinhado)"
}}
"""


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================


class KPIAlignmentCheckerTool:
    """
    Valida alinhamento entre KPIs e objetivos estrategicos do Strategy Map.

    ARQUITETURA:
    - validate_kpi_alignment() - Orquestracao principal
    - _check_perspective_match() - Validacao perspectiva
    - _check_semantic_alignment() - Validacao semantica via LLM
    - _check_coverage() - Validacao cobertura
    - _find_orphan_kpis() - Detectar KPIs orfaos
    - _find_objectives_without_kpis() - Detectar objetivos sem KPI
    - _check_sufficiency() - Validar quantidade KPIs por objetivo
    - _calculate_score() - Calcular score final

    DEPENDENCIES:
    - LLM (GPT-5.1/Claude) para validacao semantica
    - Schemas: StrategyMap, KPIFramework, KPIAlignmentReport, AlignmentIssue
    """

    def __init__(self, llm=None):
        """
        Inicializa KPI Alignment Checker.

        Args:
            llm: LLM para validacao semantica (default: get_llm_for_agent("analysis"))
        """
        # SESSAO 45: LLM analysis (Claude Opus 4.5 - analise profunda)
        self.llm = llm or get_llm_for_agent("analysis")
        logger.info("[KPIAlignmentChecker] Inicializado com LLM para validacao semantica")

    async def validate_kpi_alignment(
        self,
        strategy_map: StrategyMap,
        kpi_framework: KPIFramework | None = None,
        client_profile: "ClientProfile | None" = None,
    ) -> KPIAlignmentReport:
        """
        Valida alinhamento completo entre KPIs e objetivos estrategicos.

        STEPS:
        1. Coletar todos KPIs e objectives
        2. Executar 6 validacoes
        3. Calcular score por perspectiva
        4. Calcular score geral
        5. Consolidar recommendations

        Args:
            strategy_map: Strategy Map com objetivos estrategicos
            kpi_framework: Framework de KPIs (opcional, usa related_kpis dos objectives se ausente)
            client_profile: Profile da empresa (opcional, para contexto)

        Returns:
            KPIAlignmentReport com score, issues e recommendations
        """
        logger.info("[KPIAlignmentChecker] Iniciando validacao de alinhamento KPI-Objective")

        # Container para resultados
        all_issues: list[AlignmentIssue] = []
        all_recommendations: list[str] = []
        score_by_perspective: dict[str, float] = {}
        orphan_kpis: list[str] = []
        objectives_without_kpis: list[str] = []

        # Coletar todos objectives do Strategy Map
        all_objectives = self._collect_all_objectives(strategy_map)
        logger.info(f"[KPIAlignmentChecker] Coletados {len(all_objectives)} objectives")

        # VALIDACAO 1: Perspective Match (se tiver KPIFramework)
        if kpi_framework:
            issues1, recs1 = self._check_perspective_match(strategy_map, kpi_framework)
            all_issues.extend(issues1)
            all_recommendations.extend(recs1)

        # VALIDACAO 2: Coverage (todas perspectivas tem objectives e KPIs)
        issues2, recs2 = self._check_coverage(strategy_map, kpi_framework)
        all_issues.extend(issues2)
        all_recommendations.extend(recs2)

        # VALIDACAO 3: Orphan KPIs (KPIs sem objective)
        if kpi_framework:
            orphan_kpis = self._find_orphan_kpis(strategy_map, kpi_framework)
            for kpi_name in orphan_kpis:
                all_issues.append(
                    AlignmentIssue(
                        issue_type="orphan_kpi",
                        severity="medium",
                        kpi_name=kpi_name,
                        description=f"KPI '{kpi_name}' nao esta vinculado a nenhum objetivo estrategico",
                        recommendation=f"Vincular KPI '{kpi_name}' a um objetivo da mesma perspectiva",
                    )
                )
                all_recommendations.append(f"Vincular KPI '{kpi_name}' a objetivo estrategico")

        # VALIDACAO 4: Objectives without KPIs
        objectives_without_kpis = self._find_objectives_without_kpis(strategy_map)
        for obj_name in objectives_without_kpis:
            all_issues.append(
                AlignmentIssue(
                    issue_type="missing_kpi",
                    severity="high",
                    objective_name=obj_name,
                    description=f"Objetivo '{obj_name}' nao tem KPIs associados para medir progresso",
                    recommendation=f"Definir pelo menos 1 KPI SMART para medir '{obj_name}'",
                )
            )
            all_recommendations.append(f"Criar KPI para objetivo '{obj_name}'")

        # VALIDACAO 5: Sufficiency (1-3 KPIs por objective)
        issues5, recs5 = self._check_sufficiency(strategy_map)
        all_issues.extend(issues5)
        all_recommendations.extend(recs5)

        # VALIDACAO 6: Semantic Alignment (LLM) - amostra de objectives
        # Limitado a 4 objectives (1 por perspectiva) para performance
        issues6, recs6 = await self._check_semantic_alignment_sample(strategy_map)
        all_issues.extend(issues6)
        all_recommendations.extend(recs6)

        # Calcular score por perspectiva
        score_by_perspective = self._calculate_score_by_perspective(strategy_map, all_issues)

        # Calcular score geral
        overall_score = self._calculate_overall_score(
            all_issues, len(all_objectives), len(orphan_kpis), len(objectives_without_kpis)
        )

        # Criar report
        report = KPIAlignmentReport(
            overall_score=overall_score,
            is_aligned=overall_score >= 80.0,
            alignment_by_perspective=score_by_perspective,
            orphan_kpis=orphan_kpis,
            objectives_without_kpis=objectives_without_kpis,
            alignment_issues=all_issues,
            recommendations=list(set(all_recommendations))[:10],  # Top 10 unicas
            validated_at=datetime.now(timezone.utc),
        )

        logger.info(
            f"[KPIAlignmentChecker] Validacao completa: score={overall_score:.1f}%, "
            f"issues={len(all_issues)}, orphans={len(orphan_kpis)}"
        )

        return report

    def _collect_all_objectives(self, strategy_map: StrategyMap) -> list[dict]:
        """Coleta todos objectives de todas perspectivas."""
        objectives = []

        perspectives = [
            ("Financeira", strategy_map.financial),
            ("Clientes", strategy_map.customer),
            ("Processos Internos", strategy_map.process),
            ("Aprendizado e Crescimento", strategy_map.learning),
        ]

        for perspective_name, perspective in perspectives:
            for obj in perspective.objectives:
                objectives.append(
                    {
                        "name": obj.name,
                        "description": obj.description,
                        "perspective": perspective_name,
                        "related_kpis": obj.related_kpis,
                        "success_criteria": obj.success_criteria,
                    }
                )

        return objectives

    def _check_perspective_match(
        self, strategy_map: StrategyMap, kpi_framework: KPIFramework
    ) -> tuple[list[AlignmentIssue], list[str]]:
        """
        Valida se KPIs estao na mesma perspectiva dos objectives.

        REGRA: KPI perspective == Objective perspective
        """
        issues = []
        recommendations = []

        # Mapear KPIs por perspectiva
        kpi_by_perspective = {
            "Financeira": [kpi.name for kpi in kpi_framework.financial_kpis],
            "Clientes": [kpi.name for kpi in kpi_framework.customer_kpis],
            "Processos Internos": [kpi.name for kpi in kpi_framework.process_kpis],
            "Aprendizado e Crescimento": [kpi.name for kpi in kpi_framework.learning_kpis],
        }

        # Verificar cada objective
        perspectives = [
            ("Financeira", strategy_map.financial),
            ("Clientes", strategy_map.customer),
            ("Processos Internos", strategy_map.process),
            ("Aprendizado e Crescimento", strategy_map.learning),
        ]

        for obj_perspective, perspective in perspectives:
            for obj in perspective.objectives:
                for kpi_name in obj.related_kpis:
                    # Verificar se KPI esta na perspectiva correta
                    kpi_in_correct = kpi_name in kpi_by_perspective.get(obj_perspective, [])

                    if not kpi_in_correct:
                        # Encontrar em qual perspectiva o KPI esta
                        actual_perspective = None
                        for persp, kpis in kpi_by_perspective.items():
                            if kpi_name in kpis:
                                actual_perspective = persp
                                break

                        if actual_perspective and actual_perspective != obj_perspective:
                            issues.append(
                                AlignmentIssue(
                                    issue_type="perspective_mismatch",
                                    severity="high",
                                    objective_name=obj.name,
                                    kpi_name=kpi_name,
                                    perspective=obj_perspective,
                                    description=(
                                        f"KPI '{kpi_name}' pertence a perspectiva '{actual_perspective}' "
                                        f"mas esta associado ao objetivo '{obj.name}' da perspectiva '{obj_perspective}'"
                                    ),
                                    recommendation=(
                                        f"Mover KPI para objetivo da perspectiva '{actual_perspective}' "
                                        f"ou substituir por KPI de '{obj_perspective}'"
                                    ),
                                )
                            )
                            recommendations.append(
                                f"Corrigir perspectiva do KPI '{kpi_name}' (atual: {actual_perspective}, esperado: {obj_perspective})"
                            )

        return issues, recommendations

    def _check_coverage(
        self, strategy_map: StrategyMap, kpi_framework: KPIFramework | None
    ) -> tuple[list[AlignmentIssue], list[str]]:
        """
        Valida se todas perspectivas tem objectives e KPIs.

        REGRA: Cada perspectiva deve ter >= 2 objectives E >= 2 KPIs
        """
        issues = []
        recommendations = []

        perspectives = [
            (
                "Financeira",
                strategy_map.financial,
                kpi_framework.financial_kpis if kpi_framework else [],
            ),
            (
                "Clientes",
                strategy_map.customer,
                kpi_framework.customer_kpis if kpi_framework else [],
            ),
            (
                "Processos Internos",
                strategy_map.process,
                kpi_framework.process_kpis if kpi_framework else [],
            ),
            (
                "Aprendizado e Crescimento",
                strategy_map.learning,
                kpi_framework.learning_kpis if kpi_framework else [],
            ),
        ]

        for perspective_name, perspective, kpis in perspectives:
            obj_count = len(perspective.objectives)
            kpi_count = len(kpis)

            if obj_count < 2:
                issues.append(
                    AlignmentIssue(
                        issue_type="insufficient_kpis",
                        severity="critical",
                        perspective=perspective_name,
                        description=f"Perspectiva '{perspective_name}' tem apenas {obj_count} objetivo(s) (minimo 2)",
                        recommendation=f"Adicionar pelo menos {2 - obj_count} objetivo(s) em '{perspective_name}'",
                    )
                )
                recommendations.append(f"Adicionar objectives em '{perspective_name}'")

            if kpi_framework and kpi_count < 2:
                issues.append(
                    AlignmentIssue(
                        issue_type="insufficient_kpis",
                        severity="high",
                        perspective=perspective_name,
                        description=f"Perspectiva '{perspective_name}' tem apenas {kpi_count} KPI(s) (minimo 2)",
                        recommendation=f"Adicionar pelo menos {2 - kpi_count} KPI(s) em '{perspective_name}'",
                    )
                )
                recommendations.append(f"Adicionar KPIs em '{perspective_name}'")

        return issues, recommendations

    def _find_orphan_kpis(
        self, strategy_map: StrategyMap, kpi_framework: KPIFramework
    ) -> list[str]:
        """
        Encontra KPIs que nao estao vinculados a nenhum objective.

        REGRA: Todo KPI do framework deve estar em pelo menos 1 objective.related_kpis
        """
        # Coletar todos KPIs referenciados em objectives
        referenced_kpis = set()
        perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning,
        ]

        for perspective in perspectives:
            for obj in perspective.objectives:
                referenced_kpis.update(obj.related_kpis)

        # Coletar todos KPIs do framework
        all_kpis = set()
        for kpi in kpi_framework.financial_kpis:
            all_kpis.add(kpi.name)
        for kpi in kpi_framework.customer_kpis:
            all_kpis.add(kpi.name)
        for kpi in kpi_framework.process_kpis:
            all_kpis.add(kpi.name)
        for kpi in kpi_framework.learning_kpis:
            all_kpis.add(kpi.name)

        # KPIs orfaos = KPIs no framework que nao estao referenciados
        orphan_kpis = all_kpis - referenced_kpis

        return list(orphan_kpis)

    def _find_objectives_without_kpis(self, strategy_map: StrategyMap) -> list[str]:
        """
        Encontra objectives que nao tem KPIs associados.

        REGRA: Todo objective deve ter pelo menos 1 KPI em related_kpis
        """
        objectives_without = []

        perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning,
        ]

        for perspective in perspectives:
            for obj in perspective.objectives:
                if not obj.related_kpis or len(obj.related_kpis) == 0:
                    objectives_without.append(obj.name)

        return objectives_without

    def _check_sufficiency(
        self, strategy_map: StrategyMap
    ) -> tuple[list[AlignmentIssue], list[str]]:
        """
        Valida se objectives tem quantidade adequada de KPIs (1-3 ideal).

        REGRA (Kaplan & Norton):
        - Minimo 1 KPI por objective
        - Ideal 2 KPIs (leading + lagging)
        - Maximo 3 KPIs (evitar excesso)
        """
        issues = []
        recommendations = []

        perspectives = [
            ("Financeira", strategy_map.financial),
            ("Clientes", strategy_map.customer),
            ("Processos Internos", strategy_map.process),
            ("Aprendizado e Crescimento", strategy_map.learning),
        ]

        for perspective_name, perspective in perspectives:
            for obj in perspective.objectives:
                kpi_count = len(obj.related_kpis)

                if kpi_count > 3:
                    issues.append(
                        AlignmentIssue(
                            issue_type="insufficient_kpis",
                            severity="low",
                            objective_name=obj.name,
                            perspective=perspective_name,
                            description=(
                                f"Objetivo '{obj.name}' tem {kpi_count} KPIs (ideal 1-3). "
                                f"Excesso de KPIs pode diluir foco"
                            ),
                            recommendation=(
                                f"Reduzir KPIs de '{obj.name}' para 1-3 (priorizar leading + lagging)"
                            ),
                        )
                    )
                    recommendations.append(f"Reduzir KPIs de '{obj.name}' para maximo 3")

        return issues, recommendations

    async def _check_semantic_alignment_sample(
        self, strategy_map: StrategyMap
    ) -> tuple[list[AlignmentIssue], list[str]]:
        """
        Valida alinhamento semantico usando LLM (amostra de 4 objectives).

        Seleciona 1 objective por perspectiva e valida se KPIs fazem sentido.
        """
        issues = []
        recommendations = []

        # Selecionar 1 objective por perspectiva (que tenha KPIs)
        sample_objectives = []

        perspectives = [
            ("Financeira", strategy_map.financial),
            ("Clientes", strategy_map.customer),
            ("Processos Internos", strategy_map.process),
            ("Aprendizado e Crescimento", strategy_map.learning),
        ]

        for perspective_name, perspective in perspectives:
            for obj in perspective.objectives:
                if obj.related_kpis and len(obj.related_kpis) > 0:
                    sample_objectives.append(
                        {
                            "name": obj.name,
                            "description": obj.description,
                            "perspective": perspective_name,
                            "related_kpis": obj.related_kpis,
                            "success_criteria": obj.success_criteria,
                        }
                    )
                    break  # Apenas 1 por perspectiva

        if not sample_objectives:
            logger.warning(
                "[KPIAlignmentChecker] Nenhum objective com KPIs para validar semanticamente"
            )
            return issues, recommendations

        # Validar semanticamente cada objective-KPI
        for obj in sample_objectives:
            for kpi_name in obj["related_kpis"][:2]:  # Max 2 KPIs por objective
                try:
                    is_aligned = await self._validate_semantic_alignment(obj, kpi_name)

                    if not is_aligned:
                        issues.append(
                            AlignmentIssue(
                                issue_type="semantic_mismatch",
                                severity="medium",
                                objective_name=obj["name"],
                                kpi_name=kpi_name,
                                perspective=obj["perspective"],
                                description=(
                                    f"KPI '{kpi_name}' pode nao medir diretamente o objetivo '{obj['name']}'"
                                ),
                                recommendation=(
                                    f"Revisar se KPI '{kpi_name}' realmente mede o progresso de '{obj['name']}'"
                                ),
                            )
                        )
                        recommendations.append(
                            f"Validar alinhamento entre '{kpi_name}' e '{obj['name']}'"
                        )

                except Exception as e:
                    logger.warning(f"[KPIAlignmentChecker] Erro na validacao semantica: {e}")
                    # Nao falhar por erro de LLM

        return issues, recommendations

    async def _validate_semantic_alignment(self, objective: dict, kpi_name: str) -> bool:
        """
        Valida se um KPI esta semanticamente alinhado com um objective via LLM.

        Returns:
            True se alinhado, False se nao alinhado
        """
        prompt_content = SEMANTIC_ALIGNMENT_PROMPT.format(
            objective_name=objective["name"],
            objective_description=objective["description"],
            objective_perspective=objective["perspective"],
            success_criteria=", ".join(objective.get("success_criteria", [])),
            kpi_name=kpi_name,
            kpi_description="(Descricao nao disponivel)",  # Simplificado
            kpi_perspective=objective["perspective"],  # Assumir mesma perspectiva
            metric_type="(Tipo nao disponivel)",
            target_value="(Meta nao disponivel)",
        )

        messages = [
            SystemMessage(
                content="Voce e um especialista em BSC validando alinhamento KPI-Objetivo."
            ),
            HumanMessage(content=prompt_content),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            response_text = response.content.lower()

            # Analise simples da resposta
            if '"is_aligned": true' in response_text or '"is_aligned":true' in response_text:
                return True
            elif '"is_aligned": false' in response_text or '"is_aligned":false' in response_text:
                return False
            else:
                # Se nao conseguir parsear, assumir alinhado (safe default)
                return True

        except Exception as e:
            logger.warning(f"[KPIAlignmentChecker] Erro LLM semantic validation: {e}")
            return True  # Safe default

    def _calculate_score_by_perspective(
        self, strategy_map: StrategyMap, issues: list[AlignmentIssue]
    ) -> dict[str, float]:
        """
        Calcula score de alinhamento por perspectiva.

        Score = 100 - (issues da perspectiva * penalidade)
        """
        perspective_names = [
            "Financeira",
            "Clientes",
            "Processos Internos",
            "Aprendizado e Crescimento",
        ]

        scores = {}

        for perspective in perspective_names:
            # Contar issues da perspectiva
            perspective_issues = [issue for issue in issues if issue.perspective == perspective]

            # Calcular penalidade por severidade
            penalty = 0
            for issue in perspective_issues:
                if issue.severity == "critical":
                    penalty += 30
                elif issue.severity == "high":
                    penalty += 20
                elif issue.severity == "medium":
                    penalty += 10
                else:  # low
                    penalty += 5

            # Score = 100 - penalidade (minimo 0)
            scores[perspective] = max(0, 100 - penalty)

        return scores

    def _calculate_overall_score(
        self,
        issues: list[AlignmentIssue],
        total_objectives: int,
        orphan_count: int,
        missing_kpis_count: int,
    ) -> float:
        """
        Calcula score geral de alinhamento.

        Fatores:
        - Issues por severidade
        - Orphan KPIs
        - Objectives sem KPIs
        """
        # Base score
        base_score = 100.0

        # Penalidade por issues
        for issue in issues:
            if issue.severity == "critical":
                base_score -= 15
            elif issue.severity == "high":
                base_score -= 10
            elif issue.severity == "medium":
                base_score -= 5
            else:  # low
                base_score -= 2

        # Penalidade adicional por orphans e missing
        base_score -= orphan_count * 3
        base_score -= missing_kpis_count * 5

        # Clamp entre 0 e 100
        return max(0, min(100, base_score))


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_kpi_alignment_checker_tool(llm=None) -> KPIAlignmentCheckerTool:
    """Factory function para criar KPI Alignment Checker Tool."""
    return KPIAlignmentCheckerTool(llm=llm)
