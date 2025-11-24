"""Prompts para Action Plan Tool.

Este módulo contém prompts otimizados para facilitar criação de planos de ação
estruturados baseados em diagnóstico BSC e contexto empresarial.

Pattern: Conversational Facilitation + Structured Output (2025)
References:
- 7 Best Practices for Action Planning (SME Strategy 2025)
- Balanced Scorecard Implementation Guide (Mooncamp 2025)
- Strategic Planning Tools Comprehensive List (Spider Strategies 2024)

Created: 2025-10-27 (FASE 3.11)
"""

# ============================================================================
# ACTION PLAN FACILITATION PROMPT
# ============================================================================

FACILITATE_ACTION_PLAN_PROMPT = """Você é um consultor especialista em Balanced Scorecard facilitando a criação de um plano de ação estruturado.

SEU PAPEL:
- Analisar o contexto da empresa e diagnóstico BSC fornecido
- Criar ações específicas, mensuráveis e acionáveis para implementação BSC
- Usar conhecimento da literatura BSC para contexto adicional (fornecido abaixo)
- Gerar plano de ação completo seguindo 7 Best Practices para Action Planning

DATA ATUAL (REFERÊNCIA TEMPORAL):
{current_date}

IMPORTANTE: Use esta data como referência para TODAS as datas do plano de ação.
- Todas as datas devem ser FUTURAS em relação à data atual
- Cronograma deve começar a partir da data atual
- Prazos devem ser realistas considerando a data atual como ponto de partida

CONTEXTO DA EMPRESA:
{company_context}

DIAGNÓSTICO BSC REALIZADO:
{diagnostic_context}

CONHECIMENTO BSC RELEVANTE (da literatura):
{bsc_knowledge}

INSTRUÇÕES - 7 BEST PRACTICES PARA ACTION PLANNING:

1. ALINHE AÇÕES COM OBJETIVOS: Cada ação deve contribuir diretamente para objetivos estratégicos BSC identificados no diagnóstico

2. PRIORIZE BASEADO EM IMPORTÂNCIA E URGÊNCIA:
   - HIGH: Crítico para sucesso BSC, urgente (implementar primeiro)
   - MEDIUM: Importante mas não urgente (implementar segundo)
   - LOW: Desejável mas não crítico (implementar por último)

3. SEJA ESPECÍFICO AO INVÉS DE GENÉRICO:
   - [ERRO] ERRADO: "Melhorar processos"
   - [OK] CORRETO: "Implementar sistema de coleta de feedback de clientes com plataforma CRM até 15/12/2025"

4. DEFINA PRAZOS E RESPONSÁVEIS:
   - Cada ação deve ter data de início e data limite específicas
   - Cada ação deve ter pessoa/equipe claramente responsável
   - Use formato YYYY-MM-DD para datas
   - CRÍTICO: Todas as datas devem ser FUTURAS em relação à data atual fornecida acima
   - Não gere datas no passado - sempre use a data atual como ponto de partida mínimo

5. IDENTIFIQUE RECURSOS NECESSÁRIOS:
   - Orçamento, tecnologia, treinamento, pessoal
   - Seja específico sobre custos quando possível

6. DEFINA CRITÉRIOS DE SUCESSO:
   - Como medir se a ação foi bem-sucedida
   - Métricas específicas e mensuráveis

7. MAPEIE DEPENDÊNCIAS:
   - Quais outras ações devem ser concluídas antes desta
   - Sequência lógica de implementação

ESTRUTURA POR PERSPECTIVA BSC:

PERSPECTIVA FINANCEIRA:
- Ações para melhorar resultados financeiros
- Redução de custos, aumento de receita, ROI
- Exemplos: Implementar controle de custos, otimizar pricing, melhorar margem

PERSPECTIVA CLIENTES:
- Ações para melhorar satisfação e retenção de clientes
- Experiência do cliente, qualidade do produto/serviço
- Exemplos: Sistema de feedback, programa de fidelidade, melhorias no atendimento

PERSPECTIVA PROCESSOS INTERNOS:
- Ações para otimizar processos operacionais
- Eficiência, qualidade, inovação
- Exemplos: Automação de processos, padronização, melhoria contínua

PERSPECTIVA APRENDIZADO E CRESCIMENTO:
- Ações para desenvolver capacidades organizacionais
- Treinamento, tecnologia, cultura, inovação
- Exemplos: Programas de capacitação, investimento em tecnologia, cultura de dados

REQUISITOS DE QUALIDADE:

[OK] AÇÕES ESPECÍFICAS: Título claro e acionável (10-200 caracteres)
[OK] DESCRIÇÃO DETALHADA: Explicação completa da ação (20-1000 caracteres)
[OK] PERSPECTIVA CORRETA: Uma das 4 perspectivas BSC
[OK] PRIORIDADE JUSTIFICADA: HIGH/MEDIUM/LOW baseado em importância/urgência
[OK] ESFORÇO REALISTA: HIGH/MEDIUM/LOW baseado em complexidade/recursos
[OK] RESPONSÁVEL CLARO: Pessoa ou equipe específica (3-100 caracteres)
[OK] DATAS REALISTAS: Início e fim em formato YYYY-MM-DD
[OK] RECURSOS IDENTIFICADOS: Lista específica de recursos necessários
[OK] CRITÉRIOS MENSURÁVEIS: Como medir sucesso da ação (10-500 caracteres)
[OK] DEPENDÊNCIAS MAPEADAS: Ações que devem preceder esta

BALANCEAMENTO:
- Mínimo 1 ação por perspectiva BSC
- Ideal: 2-4 ações por perspectiva
- Distribuição equilibrada de prioridades (20-60% HIGH priority)
- Cronograma realista (3-6 meses para implementação completa)

OUTPUT ESPERADO:
Gere um plano de ação estruturado com 8-15 ações específicas distribuídas pelas 4 perspectivas BSC, seguindo rigorosamente os 7 Best Practices para Action Planning.

IMPORTANTE: Seja específico, prático e acionável. Evite ações genéricas ou vagas. Cada ação deve ser algo que uma pessoa/equipe possa executar concretamente."""

# ============================================================================
# ACTION PLAN SYNTHESIS PROMPT
# ============================================================================

SYNTHESIZE_ACTION_PLAN_PROMPT = """Você é um consultor especialista em Balanced Scorecard consolidando um plano de ação estruturado.

SEU PAPEL:
- Consolidar ações individuais em plano coeso e executável
- Criar resumo executivo e cronograma de implementação
- Validar balanceamento entre perspectivas BSC
- Garantir qualidade e praticidade do plano

AÇÕES INDIVIDUAIS GERADAS:
{individual_actions}

CONTEXTO DA EMPRESA:
{company_context}

INSTRUÇÕES DE CONSOLIDAÇÃO:

1. VALIDAR QUALIDADE DAS AÇÕES:
   - Verificar se todas as ações são específicas e acionáveis
   - Confirmar que datas são realistas e sequenciais
   - Validar que responsáveis são apropriados
   - Checar se critérios de sucesso são mensuráveis

2. ORGANIZAR POR PERSPECTIVA:
   - Agrupar ações por perspectiva BSC
   - Contar ações por perspectiva
   - Identificar gaps ou desbalanceamentos

3. PRIORIZAR E SEQUENCIAR:
   - Confirmar distribuição de prioridades (20-60% HIGH)
   - Verificar sequência lógica de dependências
   - Identificar ações críticas para início

4. CRIAR RESUMO EXECUTIVO:
   - Visão geral do plano (50-2000 caracteres)
   - Principais objetivos e benefícios esperados
   - Recursos totais necessários
   - Riscos e dependências críticas

5. CRIAR CRONOGRAMA:
   - Resumo da timeline de implementação (30-1000 caracteres)
   - Fases principais de execução
   - Marcos importantes e entregas
   - Duração total estimada

REQUISITOS FINAIS:

[OK] TOTAL DE AÇÕES: 8-15 ações específicas
[OK] BALANCEAMENTO: Mínimo 1 ação por perspectiva BSC
[OK] PRIORIDADES: 20-60% ações HIGH priority
[OK] CRONOGRAMA: 3-6 meses para implementação completa
[OK] RESUMO: Visão executiva clara e inspiradora
[OK] TIMELINE: Sequência lógica e realista

OUTPUT ESPERADO:
Consolide as ações em um ActionPlan estruturado com summary executivo, timeline_summary e contadores (total_actions, high_priority_count, by_perspective).

IMPORTANTE: Mantenha todas as ações originais, apenas organize e consolide em formato final."""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_company_context(client_profile) -> str:
    """Constrói contexto da empresa para prompts de Action Plan.

    Args:
        client_profile: ClientProfile com informações da empresa

    Returns:
        String formatada com contexto empresarial
    """
    if not client_profile or not client_profile.company:
        return "Contexto da empresa não disponível."

    company = client_profile.company
    context = company.name

    if company.sector:
        context += f" - Setor: {company.sector}"

    if company.size:
        context += f" - Porte: {company.size}"

    if company.industry:
        context += f" - Indústria: {company.industry}"

    if hasattr(company, "description") and company.description:
        context += f"\n\nDescrição: {company.description}"

    if client_profile.context and client_profile.context.current_challenges:
        challenges = ", ".join(client_profile.context.current_challenges[:3])
        context += f"\n\nPrincipais desafios atuais: {challenges}"

    return context


def build_diagnostic_context(diagnostic_results) -> str:
    """Constrói contexto do diagnóstico BSC para prompts de Action Plan.

    Args:
        diagnostic_results: CompleteDiagnostic ou dict com resultados

    Returns:
        String formatada com contexto do diagnóstico
    """
    if not diagnostic_results:
        return "Diagnóstico BSC não disponível."

    # Se for CompleteDiagnostic, extrair informações relevantes
    if hasattr(diagnostic_results, "consolidated_analysis"):
        analysis = diagnostic_results.consolidated_analysis
        context = f"Análise consolidada: {analysis.summary[:500]}..."

        if hasattr(analysis, "key_gaps") and analysis.key_gaps:
            gaps = ", ".join(analysis.key_gaps[:3])
            context += f"\n\nPrincipais gaps identificados: {gaps}"

        if hasattr(analysis, "synergies") and analysis.synergies:
            synergies = ", ".join(analysis.synergies[:3])
            context += f"\n\nPrincipais sinergias: {synergies}"

    # Se for dict, usar informações disponíveis
    elif isinstance(diagnostic_results, dict):
        context = "Resultados do diagnóstico BSC:\n"

        if "summary" in diagnostic_results:
            context += f"Resumo: {diagnostic_results['summary'][:300]}...\n"

        if "gaps" in diagnostic_results:
            gaps = ", ".join(diagnostic_results["gaps"][:3])
            context += f"Gaps: {gaps}\n"

        if "recommendations" in diagnostic_results:
            recs = ", ".join(diagnostic_results["recommendations"][:3])
            context += f"Recomendações: {recs}"

    else:
        context = "Diagnóstico BSC realizado - detalhes não estruturados disponíveis."

    return context


def build_bsc_knowledge_context(
    financial_knowledge: str = "",
    customer_knowledge: str = "",
    process_knowledge: str = "",
    learning_knowledge: str = "",
) -> str:
    """Constrói contexto de conhecimento BSC para prompts de Action Plan.

    Args:
        financial_knowledge: Conhecimento da perspectiva financeira
        customer_knowledge: Conhecimento da perspectiva clientes
        process_knowledge: Conhecimento da perspectiva processos
        learning_knowledge: Conhecimento da perspectiva aprendizado

    Returns:
        String formatada com conhecimento BSC relevante
    """
    knowledge_parts = []

    if financial_knowledge:
        knowledge_parts.append(f"PERSPECTIVA FINANCEIRA:\n{financial_knowledge[:500]}...")

    if customer_knowledge:
        knowledge_parts.append(f"PERSPECTIVA CLIENTES:\n{customer_knowledge[:500]}...")

    if process_knowledge:
        knowledge_parts.append(f"PERSPECTIVA PROCESSOS:\n{process_knowledge[:500]}...")

    if learning_knowledge:
        knowledge_parts.append(f"PERSPECTIVA APRENDIZADO:\n{learning_knowledge[:500]}...")

    if not knowledge_parts:
        return "Conhecimento BSC da literatura não disponível."

    return "\n\n".join(knowledge_parts)


def format_action_plan_for_display(action_plan) -> str:
    """Formata ActionPlan para exibição amigável.

    Args:
        action_plan: ActionPlan object

    Returns:
        String formatada para exibição
    """
    if not action_plan:
        return "Plano de ação não disponível."

    output = "[EMOJI] PLANO DE AÇÃO BSC\n"
    output += f"{'='*50}\n\n"

    # Resumo executivo
    output += "[EMOJI] RESUMO EXECUTIVO:\n"
    output += f"{action_plan.summary}\n\n"

    # Estatísticas
    output += "[EMOJI] ESTATÍSTICAS:\n"
    output += f"• Total de ações: {action_plan.total_actions}\n"
    output += f"• Ações de alta prioridade: {action_plan.high_priority_count}\n"
    output += f"• Balanceamento: {'[OK] Balanceado' if action_plan.is_balanced() else '[WARN] Desbalanceado'}\n"
    output += f"• Score de qualidade: {action_plan.quality_score():.1%}\n\n"

    # Por perspectiva
    output += "[EMOJI] AÇÕES POR PERSPECTIVA:\n"
    for perspective, count in action_plan.by_perspective.items():
        output += f"• {perspective}: {count} ações\n"
    output += "\n"

    # Cronograma
    output += "[EMOJI] CRONOGRAMA:\n"
    output += f"{action_plan.timeline_summary}\n\n"

    # Ações detalhadas
    output += "[EMOJI] AÇÕES DETALHADAS:\n"
    output += f"{'='*50}\n"

    for i, action in enumerate(action_plan.action_items, 1):
        priority_icon = (
            "[EMOJI]"
            if action.priority == "HIGH"
            else "[EMOJI]" if action.priority == "MEDIUM" else "[EMOJI]"
        )
        effort_icon = (
            "[HIGH]"
            if action.effort == "HIGH"
            else "[MEDIUM]" if action.effort == "MEDIUM" else "[LOW]"
        )

        output += f"\n{i}. {priority_icon} {effort_icon} {action.action_title}\n"
        output += f"   Perspectiva: {action.perspective}\n"
        output += f"   Responsável: {action.responsible}\n"
        output += f"   Período: {action.start_date} -> {action.due_date}\n"
        output += f"   Descrição: {action.description}\n"

        if action.resources_needed:
            output += f"   Recursos: {', '.join(action.resources_needed)}\n"

        if action.success_criteria:
            output += f"   Sucesso: {action.success_criteria}\n"

        if action.dependencies:
            output += f"   Dependências: {', '.join(action.dependencies)}\n"

    return output
