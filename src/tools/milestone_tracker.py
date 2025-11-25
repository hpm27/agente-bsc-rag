"""
Milestone Tracker Tool - Sprint 4.2

Ferramenta para rastrear progresso de milestones do Action Plan BSC.
Gera relatorio consolidado com status, riscos e recomendacoes.

Best Practices (BSC + OKR 2025):
- Milestones sao checkpoints mensuraveis
- Critical path = sequencia que determina duracao total
- Risk identification proativa

Fontes:
- balancedscorecard.org (OKR Basics 2025)
- mooncamp.com (BSC Complete Guide 2025)
- profit.co (BSC Relevance 2025)
"""

from datetime import datetime, timezone
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger

from config.settings import get_llm_for_agent
from src.memory.schemas import (
    ActionItem,
    ActionPlan,
    Milestone,
    MilestoneTrackerReport,
)


class MilestoneTrackerTool:
    """Ferramenta para rastrear progresso de milestones do Action Plan.

    Gera milestones a partir de ActionItems e calcula progresso,
    caminho critico, riscos e recomendacoes.

    Attributes:
        llm: Modelo de linguagem para geracao de insights
    """

    def __init__(self, llm: BaseChatModel | None = None):
        """Inicializa MilestoneTrackerTool.

        Args:
            llm: LLM para geracao de insights. Se None, usa default.
        """
        self.llm = llm or get_llm_for_agent(agent_type="tools")
        logger.debug("[MILESTONE_TRACKER] Tool inicializada")

    async def generate_milestones_from_action_plan(
        self,
        action_plan: ActionPlan,
        current_date: str | None = None,
    ) -> MilestoneTrackerReport:
        """Gera relatorio de milestones a partir de Action Plan.

        Args:
            action_plan: Action Plan com action items
            current_date: Data atual para calculo de status (YYYY-MM-DD)

        Returns:
            MilestoneTrackerReport com milestones e metricas
        """
        logger.info(
            f"[MILESTONE_TRACKER] Gerando milestones para {len(action_plan.action_items)} action items"
        )

        if current_date is None:
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Gerar milestones a partir dos action items
        milestones = self._create_milestones_from_actions(action_plan.action_items, current_date)

        # 2. Calcular metricas
        total = len(milestones)
        completed = sum(1 for m in milestones if m.status == "COMPLETED")
        in_progress = sum(1 for m in milestones if m.status == "IN_PROGRESS")
        at_risk = sum(1 for m in milestones if m.status in ["BLOCKED", "AT_RISK"])

        # 3. Calcular progresso geral (media ponderada)
        if total > 0:
            overall_progress = sum(m.progress_percent for m in milestones) / total
        else:
            overall_progress = 0.0

        # 4. Identificar caminho critico (milestones de alta prioridade)
        critical_path = self._identify_critical_path(milestones)

        # 5. Identificar proximos milestones
        next_due = self._get_next_due_milestones(milestones, current_date)

        # 6. Gerar recomendacoes
        recommendations = self._generate_recommendations(milestones)

        # 7. Gerar summary
        summary = self._generate_summary(total, completed, in_progress, at_risk, overall_progress)

        report = MilestoneTrackerReport(
            milestones=milestones,
            total_milestones=total,
            completed_count=completed,
            in_progress_count=in_progress,
            at_risk_count=at_risk,
            overall_progress=round(overall_progress, 1),
            critical_path=critical_path,
            next_due_milestones=next_due,
            summary=summary,
            recommendations=recommendations,
        )

        logger.info(
            f"[MILESTONE_TRACKER] Relatorio gerado: {total} milestones, "
            f"{completed} completos, {at_risk} em risco"
        )

        return report

    def _create_milestones_from_actions(
        self,
        action_items: list[ActionItem],
        current_date: str,
    ) -> list[Milestone]:
        """Cria milestones a partir de action items.

        Args:
            action_items: Lista de action items
            current_date: Data atual para calculo de status

        Returns:
            Lista de Milestones
        """
        milestones = []

        for action in action_items:
            # Determinar status baseado em datas e prioridade
            status = self._determine_status(action, current_date)

            # Calcular progresso simulado baseado em status
            progress = self._estimate_progress(status, action, current_date)

            # Extrair dependencias
            dependencies = action.dependencies if action.dependencies else []

            milestone = Milestone(
                name=self._create_milestone_name(action),
                description=self._create_milestone_description(action),
                action_item_ref=action.action_title,
                status=status,
                progress_percent=progress,
                target_date=action.due_date,
                responsible=action.responsible,
                dependencies=dependencies,
                blockers=[],  # Inicialmente vazio, pode ser atualizado
            )

            milestones.append(milestone)

        return milestones

    def _create_milestone_name(self, action: ActionItem) -> str:
        """Cria nome do milestone a partir do action item."""
        # Extrair palavras-chave do titulo
        title = action.action_title
        if len(title) <= 100:
            return title
        return title[:97] + "..."

    def _create_milestone_description(self, action: ActionItem) -> str:
        """Cria descricao do milestone."""
        desc = f"Milestone para: {action.description[:200]}"
        if action.success_criteria:
            desc += f" | Criterio: {action.success_criteria}"
        if len(desc) < 20:
            desc = (
                f"Entrega relacionada a: {action.action_title} na perspectiva {action.perspective}"
            )
        return desc[:500]

    def _determine_status(self, action: ActionItem, current_date: str) -> str:
        """Determina status do milestone baseado em datas e contexto.

        Args:
            action: Action item
            current_date: Data atual (YYYY-MM-DD)

        Returns:
            Status: NOT_STARTED, IN_PROGRESS, AT_RISK, etc.
        """
        try:
            current = datetime.strptime(current_date, "%Y-%m-%d")
            due = datetime.strptime(action.due_date, "%Y-%m-%d")
            start = datetime.strptime(action.start_date, "%Y-%m-%d")

            # Se ainda nao comecou
            if current < start:
                return "NOT_STARTED"

            # Se passou da data limite
            if current > due:
                return "AT_RISK"

            # Se esta dentro do prazo
            days_total = (due - start).days
            days_elapsed = (current - start).days

            if days_total > 0:
                elapsed_ratio = days_elapsed / days_total
                if elapsed_ratio > 0.8:
                    # Mais de 80% do tempo passou - verificar prioridade
                    if action.priority == "HIGH":
                        return "AT_RISK"
                    return "IN_PROGRESS"
                return "IN_PROGRESS"

            return "IN_PROGRESS"

        except (ValueError, TypeError):
            # Se datas invalidas, assumir em andamento
            return "IN_PROGRESS"

    def _estimate_progress(
        self,
        status: str,
        action: ActionItem,
        current_date: str,
    ) -> float:
        """Estima progresso do milestone baseado em status e tempo decorrido.

        Args:
            status: Status do milestone
            action: Action item
            current_date: Data atual

        Returns:
            Progresso estimado (0-100)
        """
        if status == "COMPLETED":
            return 100.0
        if status == "NOT_STARTED":
            return 0.0

        try:
            current = datetime.strptime(current_date, "%Y-%m-%d")
            due = datetime.strptime(action.due_date, "%Y-%m-%d")
            start = datetime.strptime(action.start_date, "%Y-%m-%d")

            days_total = (due - start).days
            days_elapsed = (current - start).days

            if days_total > 0:
                # Progresso linear baseado em tempo
                raw_progress = (days_elapsed / days_total) * 100

                # Ajustar por esforco (HIGH = mais lento)
                if action.effort == "HIGH":
                    raw_progress *= 0.7
                elif action.effort == "MEDIUM":
                    raw_progress *= 0.85

                return min(95.0, max(5.0, round(raw_progress, 1)))

            return 50.0  # Default se datas iguais

        except (ValueError, TypeError):
            return 50.0  # Default se erro

    def _identify_critical_path(self, milestones: list[Milestone]) -> list[str]:
        """Identifica milestones no caminho critico.

        Caminho critico = milestones de alta dependencia ou em risco.

        Args:
            milestones: Lista de milestones

        Returns:
            Lista de nomes de milestones no caminho critico
        """
        critical = []

        # Milestones em risco sao sempre criticos
        for m in milestones:
            if m.status in ["AT_RISK", "BLOCKED"]:
                critical.append(m.name)

        # Milestones com muitas dependencias
        dependency_counts: dict[str, int] = {}
        for m in milestones:
            for dep in m.dependencies:
                dependency_counts[dep] = dependency_counts.get(dep, 0) + 1

        # Milestones que sao dependencia de outros (bloqueadores)
        for m in milestones:
            if m.name in dependency_counts and dependency_counts[m.name] >= 2:
                if m.name not in critical:
                    critical.append(m.name)

        return critical[:5]  # Limitar a 5 para nao sobrecarregar

    def _get_next_due_milestones(
        self,
        milestones: list[Milestone],
        current_date: str,
    ) -> list[str]:
        """Identifica proximos milestones com prazo.

        Args:
            milestones: Lista de milestones
            current_date: Data atual

        Returns:
            Lista de nomes dos proximos milestones
        """
        # Filtrar milestones nao completados e ordenar por data
        pending = [m for m in milestones if m.status != "COMPLETED"]

        try:
            current = datetime.strptime(current_date, "%Y-%m-%d")

            # Ordenar por target_date
            sorted_pending = sorted(
                pending,
                key=lambda m: datetime.strptime(m.target_date, "%Y-%m-%d"),
            )

            # Pegar os 3 proximos
            next_due = []
            for m in sorted_pending[:3]:
                target = datetime.strptime(m.target_date, "%Y-%m-%d")
                if target >= current:
                    next_due.append(m.name)

            return next_due

        except (ValueError, TypeError):
            return [m.name for m in pending[:3]]

    def _generate_recommendations(self, milestones: list[Milestone]) -> list[str]:
        """Gera recomendacoes baseadas no status dos milestones.

        Args:
            milestones: Lista de milestones

        Returns:
            Lista de recomendacoes
        """
        recommendations = []

        # Verificar milestones em risco
        at_risk = [m for m in milestones if m.status in ["AT_RISK", "BLOCKED"]]
        if at_risk:
            recommendations.append(
                f"CRITICO: {len(at_risk)} milestone(s) em risco. " f"Priorizar: {at_risk[0].name}"
            )

        # Verificar milestones com blockers
        blocked = [m for m in milestones if m.blockers]
        if blocked:
            recommendations.append(
                f"Resolver impedimentos em {len(blocked)} milestone(s) bloqueados"
            )

        # Verificar dependencias nao iniciadas
        not_started = [m for m in milestones if m.status == "NOT_STARTED"]
        if len(not_started) > len(milestones) * 0.5:
            recommendations.append(
                "Mais de 50% dos milestones nao iniciados. "
                "Considerar kickoff geral para acelerar execucao"
            )

        # Recomendacao de priorizacao
        if not at_risk and not blocked:
            recommendations.append(
                "Plano em execucao saudavel. " "Manter cadencia de acompanhamento semanal"
            )

        return recommendations[:5]  # Limitar a 5

    def _generate_summary(
        self,
        total: int,
        completed: int,
        in_progress: int,
        at_risk: int,
        overall_progress: float,
    ) -> str:
        """Gera resumo executivo do status.

        Args:
            total: Total de milestones
            completed: Milestones completados
            in_progress: Milestones em andamento
            at_risk: Milestones em risco
            overall_progress: Progresso geral

        Returns:
            Resumo executivo
        """
        status_text = "saudavel" if at_risk == 0 else "atencao necessaria"

        summary = (
            f"Plano de acao {overall_progress:.1f}% completo ({status_text}). "
            f"{completed}/{total} milestones finalizados, "
            f"{in_progress} em andamento"
        )

        if at_risk > 0:
            summary += f", {at_risk} em risco requerendo acao imediata"
        else:
            summary += ". Nenhum bloqueio identificado"

        return summary


def create_milestone_tracker_tool(
    llm: BaseChatModel | None = None,
) -> MilestoneTrackerTool:
    """Factory function para criar MilestoneTrackerTool.

    Args:
        llm: LLM opcional para geracao de insights

    Returns:
        Instancia de MilestoneTrackerTool
    """
    return MilestoneTrackerTool(llm=llm)
