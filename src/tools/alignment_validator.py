"""
Alignment Validator Tool - Sprint 2

Valida balanceamento e completude do Strategy Map BSC seguindo best practices
Kaplan & Norton (2025). Executa 8 validações críticas e gera report estruturado.

8 Validações Obrigatórias (BSCDesigner 2025):
1. balanced_perspectives: 2-10 objectives por perspectiva
2. all_objectives_have_kpis: Cada objective tem ≥1 KPI
3. cause_effect_exists: ≥4 conexões causa-efeito
4. no_isolated_objectives: Todos objectives conectados
5. kpis_are_smart: KPIs mensuráveis (SMART)
6. goals_are_strategic: Goals estratégicos (não operacionais)
7. has_rationale: Objectives têm rationale explicado
8. no_jargon: Não usa business jargon genérico

Scoring: Score = (validações passando / 8) * 100
- Score ≥90: Excelente
- Score ≥80: Bom
- Score <80: Precisa refinamento
"""

import logging
import re
from typing import List, Dict, Set
from datetime import datetime, timezone

from src.memory.schemas import (
    StrategyMap,
    StrategyMapPerspective,
    StrategicObjective,
    CauseEffectConnection,
    AlignmentReport
)

logger = logging.getLogger(__name__)


# ============================================================================
# JARGON GENÉRICO A EVITAR (baseado em BSCDesigner 2025 + Kaplan & Norton)
# ============================================================================

GENERIC_JARGON = [
    "leverage synergies",
    "drive innovation",
    "maximize value",
    "optimize performance",
    "strategic alignment",
    "best in class",
    "world class",
    "paradigm shift",
    "game changer",
    "low-hanging fruit",
    "move the needle",
    "think outside the box"
]


# ============================================================================
# OPERATIONAL KEYWORDS (indicam goals operacionais ao invés de estratégicos)
# ============================================================================

OPERATIONAL_KEYWORDS = [
    "implementar erp",
    "instalar software",
    "comprar equipamento",
    "contratar pessoa",
    "fazer reunião",
    "enviar email",
    "criar planilha",
    "atualizar documento"
]


# ============================================================================
# ALIGNMENT VALIDATOR TOOL
# ============================================================================

class AlignmentValidatorTool:
    """
    Valida balanceamento e completude do Strategy Map BSC.
    
    Executa 8 validações críticas baseadas em best practices Kaplan & Norton
    e retorna AlignmentReport estruturado com score 0-100, gaps e recommendations.
    
    ARQUITETURA:
    - validate_strategy_map() - Orquestração principal
    - 8 métodos _check_*() - Uma validação cada
    - _calculate_score() - Calcula % de validações passando
    - _generate_report() - Consolida gaps/warnings/recommendations
    
    IMPORTANTE:
    - Não precisa LLM (validações são regras lógicas)
    - Não precisa RAG (análise estrutural do Strategy Map)
    - Retorna AlignmentReport Pydantic validado
    """
    
    def __init__(self):
        """Inicializa validator (stateless, não precisa de configuração)."""
        logger.info("[AlignmentValidator] Inicializado")
    
    def validate_strategy_map(self, strategy_map: StrategyMap) -> AlignmentReport:
        """
        Valida Strategy Map e retorna report completo.
        
        STEPS:
        1. Executar 8 validações (cada retorna bool + mensagens)
        2. Calcular score (% validações passando)
        3. Consolidar gaps/warnings/recommendations
        4. Retornar AlignmentReport
        
        Args:
            strategy_map: Strategy Map a ser validado
        
        Returns:
            AlignmentReport com score, gaps, warnings, recommendations
        """
        logger.info("[AlignmentValidator] Iniciando validação do Strategy Map")
        
        # Container para resultados
        validation_checks = {}
        all_gaps = []
        all_warnings = []
        all_recommendations = []
        
        # VALIDAÇÃO 1: Perspectivas balanceadas (2-10 objectives cada)
        check1, gaps1, warnings1, recs1 = self._check_balanced_perspectives(strategy_map)
        validation_checks["balanced_perspectives"] = check1
        all_gaps.extend(gaps1)
        all_warnings.extend(warnings1)
        all_recommendations.extend(recs1)
        
        # VALIDAÇÃO 2: Objetivos têm KPIs
        check2, gaps2, warnings2, recs2 = self._check_objectives_have_kpis(strategy_map)
        validation_checks["all_objectives_have_kpis"] = check2
        all_gaps.extend(gaps2)
        all_warnings.extend(warnings2)
        all_recommendations.extend(recs2)
        
        # VALIDAÇÃO 3: Conexões causa-efeito existem (mínimo 4)
        check3, gaps3, warnings3, recs3 = self._check_cause_effect_exists(strategy_map)
        validation_checks["cause_effect_exists"] = check3
        all_gaps.extend(gaps3)
        all_warnings.extend(warnings3)
        all_recommendations.extend(recs3)
        
        # VALIDAÇÃO 4: Não há objectives isolated
        check4, gaps4, warnings4, recs4 = self._check_no_isolated_objectives(strategy_map)
        validation_checks["no_isolated_objectives"] = check4
        all_gaps.extend(gaps4)
        all_warnings.extend(warnings4)
        all_recommendations.extend(recs4)
        
        # VALIDAÇÃO 5: KPIs são SMART (mensuráveis)
        check5, gaps5, warnings5, recs5 = self._check_kpis_are_smart(strategy_map)
        validation_checks["kpis_are_smart"] = check5
        all_gaps.extend(gaps5)
        all_warnings.extend(warnings5)
        all_recommendations.extend(recs5)
        
        # VALIDAÇÃO 6: Goals são estratégicos (não operacionais)
        check6, gaps6, warnings6, recs6 = self._check_goals_are_strategic(strategy_map)
        validation_checks["goals_are_strategic"] = check6
        all_gaps.extend(gaps6)
        all_warnings.extend(warnings6)
        all_recommendations.extend(recs6)
        
        # VALIDAÇÃO 7: Objectives têm rationale explicado
        check7, gaps7, warnings7, recs7 = self._check_has_rationale(strategy_map)
        validation_checks["has_rationale"] = check7
        all_gaps.extend(gaps7)
        all_warnings.extend(warnings7)
        all_recommendations.extend(recs7)
        
        # VALIDAÇÃO 8: Não usa jargon genérico
        check8, gaps8, warnings8, recs8 = self._check_no_jargon(strategy_map)
        validation_checks["no_jargon"] = check8
        all_gaps.extend(gaps8)
        all_warnings.extend(warnings8)
        all_recommendations.extend(recs8)
        
        # Calcular score (% validações passando)
        total_checks = len(validation_checks)
        passed_checks = sum(1 for passed in validation_checks.values() if passed)
        score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # is_balanced = validação 1 passou
        is_balanced = validation_checks.get("balanced_perspectives", False)
        
        # Criar AlignmentReport
        report = AlignmentReport(
            score=score,
            is_balanced=is_balanced,
            gaps=all_gaps,
            warnings=all_warnings,
            recommendations=all_recommendations,
            validation_checks=validation_checks,
            validated_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"[AlignmentValidator] Validação completa: score={score:.1f}%, "
                   f"gaps={len(all_gaps)}, warnings={len(all_warnings)}")
        
        return report
    
    def _check_balanced_perspectives(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se 4 perspectivas estão balanceadas (2-10 objectives cada).
        
        REGRA (BSCDesigner 2025):
        - Mínimo 2 objectives por perspectiva (evitar perspectiva negligenciada)
        - Máximo 10 objectives por perspectiva (RED FLAG: falta de cascading)
        - Ideal: 8-10 objectives por perspectiva
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        perspectives = {
            "Financeira": strategy_map.financial,
            "Clientes": strategy_map.customer,
            "Processos Internos": strategy_map.process,
            "Aprendizado e Crescimento": strategy_map.learning
        }
        
        passou = True
        
        for name, perspective in perspectives.items():
            obj_count = len(perspective.objectives)
            
            if obj_count < 2:
                passou = False
                gaps.append(f"Perspectiva '{name}' tem apenas {obj_count} objetivo(s) (mínimo 2)")
                recommendations.append(f"Adicionar pelo menos {2 - obj_count} objetivo(s) em '{name}'")
            
            elif obj_count > 10:
                passou = False
                gaps.append(f"Perspectiva '{name}' tem {obj_count} objectives (máximo 10 - RED FLAG: falta cascading)")
                recommendations.append(f"Revisar objectives em '{name}' e fazer cascading para nível tático")
            
            elif obj_count < 8:
                warnings.append(f"Perspectiva '{name}' tem {obj_count} objectives (ideal: 8-10)")
        
        return passou, gaps, warnings, recommendations
    
    def _check_objectives_have_kpis(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se todos objectives têm pelo menos 1 KPI.
        
        REGRA (Kaplan & Norton):
        - Cada strategic objective DEVE ter ≥1 KPI para medir progresso
        - Ideal: 1-2 KPIs por objective (leading + lagging)
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        passou = True
        
        all_perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning
        ]
        
        for perspective in all_perspectives:
            for obj in perspective.objectives:
                kpi_count = len(obj.related_kpis)
                
                if kpi_count == 0:
                    passou = False
                    gaps.append(f"Objective '{obj.name}' não tem KPIs vinculados")
                    recommendations.append(f"Definir pelo menos 1 KPI para medir '{obj.name}'")
        
        return passou, gaps, warnings, recommendations
    
    def _check_cause_effect_exists(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se existem conexões causa-efeito (mínimo 4).
        
        REGRA (Kaplan & Norton 2025):
        - Mínimo 4 conexões (1 entre cada par de perspectivas adjacentes)
        - Lógica: Learning -> Process -> Customer -> Financial
        - Ideal: 8-12 conexões para Strategy Map completo
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        conn_count = len(strategy_map.cause_effect_connections)
        
        passou = conn_count >= 4
        
        if conn_count < 4:
            gaps.append(f"Strategy Map tem apenas {conn_count} conexões causa-efeito (mínimo 4)")
            recommendations.append(f"Adicionar pelo menos {4 - conn_count} conexões entre perspectivas")
        
        elif conn_count < 8:
            warnings.append(f"Strategy Map tem {conn_count} conexões (ideal: 8-12 para completude)")
        
        return passou, gaps, warnings, recommendations
    
    def _check_no_isolated_objectives(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se não há objectives isolated (sem conexões causa-efeito).
        
        REGRA (Kaplan & Norton):
        - Todo objective DEVE estar conectado (source ou target)
        - Objectives isolated indicam falta de alignment estratégico
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        # Coletar todos objective names
        all_obj_names = set()
        for perspective in [strategy_map.financial, strategy_map.customer, 
                           strategy_map.process, strategy_map.learning]:
            for obj in perspective.objectives:
                all_obj_names.add(obj.name)
        
        # Coletar objectives conectados
        connected_obj_names = set()
        for conn in strategy_map.cause_effect_connections:
            connected_obj_names.add(conn.source_objective_id)
            connected_obj_names.add(conn.target_objective_id)
        
        # Identificar isolated
        isolated_obj_names = all_obj_names - connected_obj_names
        
        passou = len(isolated_obj_names) == 0
        
        for isolated_name in isolated_obj_names:
            warnings.append(f"Objective '{isolated_name}' está isolated (sem conexões causa-efeito)")
            recommendations.append(f"Conectar '{isolated_name}' com outros objectives")
        
        return passou, gaps, warnings, recommendations
    
    def _check_kpis_are_smart(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se KPIs são SMART (mensuráveis).
        
        REGRA (SMART criteria):
        - KPI deve ter unidade de medida (%, R$, dias, unidades, etc)
        - KPI deve ser específico e mensurável
        
        HEURÍSTICA:
        - Verificar se KPI name contém número/unidade/métrica
        - Exemplo BOM: "Margem EBITDA >= 18%", "NPS >= 50"
        - Exemplo RUIM: "Melhorar lucratividade", "Aumentar satisfação"
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        passou = True
        
        # Padrões que indicam KPI mensurável
        measurable_patterns = [
            r'\d+',  # Contém número
            r'%',    # Contém percentual
            r'R\$',  # Contém moeda
            r'\b(dias|meses|anos|horas|minutos)\b',  # Unidade tempo
            r'\b(kg|toneladas|unidades|itens)\b',  # Unidade quantidade
            r'\b(>=|<=|>|<|=)\b'  # Comparadores
        ]
        
        all_perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning
        ]
        
        for perspective in all_perspectives:
            for obj in perspective.objectives:
                for kpi_name in obj.related_kpis:
                    # Verificar se KPI é mensurável
                    is_measurable = any(
                        re.search(pattern, kpi_name, re.IGNORECASE)
                        for pattern in measurable_patterns
                    )
                    
                    if not is_measurable:
                        passou = False
                        warnings.append(f"KPI '{kpi_name}' parece não ser mensurável (falta número/unidade)")
                        recommendations.append(f"Tornar KPI '{kpi_name}' SMART (ex: adicionar meta numérica)")
        
        return passou, gaps, warnings, recommendations
    
    def _check_goals_are_strategic(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se goals são estratégicos (não operacionais).
        
        REGRA (Kaplan & Norton):
        - Goals estratégicos: Onde queremos chegar (ex: "Aumentar rentabilidade")
        - Goals operacionais: Como faremos (ex: "Implementar ERP")
        - Strategy Map deve ter APENAS goals estratégicos
        
        HEURÍSTICA:
        - Verificar se objective name/description contém palavras operacionais
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        passou = True
        
        all_perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning
        ]
        
        for perspective in all_perspectives:
            for obj in perspective.objectives:
                text = f"{obj.name} {obj.description}".lower()
                
                # Verificar keywords operacionais
                for keyword in OPERATIONAL_KEYWORDS:
                    if keyword in text:
                        passou = False
                        warnings.append(f"Objective '{obj.name}' parece operacional (contém '{keyword}')")
                        recommendations.append(f"Reformular '{obj.name}' como goal estratégico (onde chegar, não como fazer)")
                        break  # Evitar múltiplos warnings para mesmo objective
        
        return passou, gaps, warnings, recommendations
    
    def _check_has_rationale(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se objectives têm rationale explicado (campo description).
        
        REGRA (BSCDesigner 2025):
        - Cada objective DEVE ter description >= 50 caracteres
        - Description explica WHY escolhemos esse objective (rationale)
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        passou = True
        
        all_perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning
        ]
        
        for perspective in all_perspectives:
            for obj in perspective.objectives:
                desc_length = len(obj.description)
                
                if desc_length < 50:
                    passou = False
                    warnings.append(f"Objective '{obj.name}' tem description muito curta ({desc_length} chars, mínimo 50)")
                    recommendations.append(f"Expandir rationale de '{obj.name}' explicando WHY escolhemos esse objective")
        
        return passou, gaps, warnings, recommendations
    
    def _check_no_jargon(
        self,
        strategy_map: StrategyMap
    ) -> tuple[bool, List[str], List[str], List[str]]:
        """
        Valida se não usa business jargon genérico.
        
        REGRA (BSCDesigner 2025):
        - Evitar frases vazias: "leverage synergies", "drive innovation"
        - Usar linguagem específica e acionável
        
        Returns:
            (passou: bool, gaps: List[str], warnings: List[str], recommendations: List[str])
        """
        gaps = []
        warnings = []
        recommendations = []
        
        passou = True
        
        all_perspectives = [
            strategy_map.financial,
            strategy_map.customer,
            strategy_map.process,
            strategy_map.learning
        ]
        
        for perspective in all_perspectives:
            for obj in perspective.objectives:
                text = f"{obj.name} {obj.description}".lower()
                
                # Verificar jargon genérico
                for jargon in GENERIC_JARGON:
                    if jargon in text:
                        passou = False
                        warnings.append(f"Objective '{obj.name}' usa jargon genérico ('{jargon}')")
                        recommendations.append(f"Substituir jargon em '{obj.name}' por linguagem específica e mensurável")
                        break  # Evitar múltiplos warnings para mesmo objective
        
        return passou, gaps, warnings, recommendations


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_alignment_validator_tool() -> AlignmentValidatorTool:
    """Factory function para criar Alignment Validator Tool."""
    return AlignmentValidatorTool()


