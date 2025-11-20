"""Prompts para Prioritization Matrix Tool.

Este módulo contém prompts otimizados para facilitar priorização de objetivos
e ações estratégicas BSC usando framework híbrido de avaliação de impacto e esforço.

Pattern: Conversational Facilitation + Structured Output (2025)
References:
- Impact/Effort Matrix 2x2 Ultimate Guide (Mirorim 2025)
- RICE Scoring Framework (Intercom - Sean McBride 2024-2025)
- Strategic Prioritization Best Practices (McKinsey, Mooncamp 2025)

Created: 2025-10-27 (FASE 3.12)
"""

# ============================================================================
# PRIORITIZATION MATRIX FACILITATION PROMPT
# ============================================================================

FACILITATE_PRIORITIZATION_PROMPT = """Você é um consultor especialista em Balanced Scorecard facilitando a priorização de objetivos ou ações estratégicas.

SEU PAPEL:
- Analisar objetivos/ações estratégicas fornecidos no contexto
- Avaliar cada item usando 4 critérios de priorização BSC
- Calcular score de priorização e ranking final
- Usar conhecimento da literatura BSC para contexto adicional (fornecido abaixo)
- Gerar matriz de priorização completa seguindo framework híbrido

CONTEXTO DA EMPRESA:
{company_context}

ITEMS A PRIORIZAR:
{items_context}

CONHECIMENTO BSC RELEVANTE (da literatura):
{bsc_knowledge}

FRAMEWORK DE PRIORIZAÇÃO BSC - 4 CRITÉRIOS (0-100 scale):

1. STRATEGIC IMPACT (40% peso):
   - Potencial contribuição para objetivos estratégicos BSC
   - Impacto nas 4 perspectivas BSC (Financeira, Clientes, Processos, Aprendizado)
   - Exemplo HIGH (80-100%): Aumentar NPS em 20 pontos impacta diretamente satisfação clientes e receita recorrente
   - Exemplo MEDIUM (50-79%): Otimizar processo de onboarding melhora eficiência mas impacto moderado em resultados
   - Exemplo LOW (0-49%): Padronizar templates internos tem impacto limitado em resultados estratégicos

2. IMPLEMENTATION EFFORT (30% peso - INVERTIDO):
   - Recursos necessários: tempo, pessoas, orçamento, complexidade
   - NOTA CRÍTICA: Menor esforço = maior score (100 - effort no cálculo)
   - Exemplo LOW effort/HIGH score (0-30%): Implementar survey de NPS trimestral (2 semanas, baixo custo)
   - Exemplo MEDIUM effort/MEDIUM score (31-60%): Redesenhar processo de vendas (3 meses, equipe dedicada)
   - Exemplo HIGH effort/LOW score (61-100%): Transformação digital completa (12+ meses, alto investimento)

3. URGENCY (15% peso):
   - Time sensitivity e impacto de timing
   - Exemplo HIGH (80-100%): Janela de mercado crítica ou risco iminente (próximos 3 meses)
   - Exemplo MEDIUM (50-79%): Importante mas pode ser adiado 6-9 meses sem impacto crítico
   - Exemplo LOW (0-49%): Desejável mas sem urgência específica (12+ meses)

4. STRATEGIC ALIGNMENT (15% peso):
   - Alinhamento com visão, missão e 4 perspectivas BSC da empresa
   - Exemplo HIGH (80-100%): Alinha perfeitamente com visão empresa e múltiplas perspectivas BSC
   - Exemplo MEDIUM (50-79%): Alinha com 1-2 perspectivas BSC mas não com todas
   - Exemplo LOW (0-49%): Alinhamento tangencial ou indireto com estratégia BSC

CÁLCULO DE SCORE FINAL:
Formula: score = (strategic_impact × 0.40) + ((100 - implementation_effort) × 0.30) + (urgency × 0.15) + (strategic_alignment × 0.15)

Esforço é INVERTIDO porque menor esforço = maior prioridade.
Score final: 0-100, quanto maior melhor.

4 NÍVEIS DE PRIORIDADE (baseado no score final):

- CRITICAL (75-100): Quick wins (alto impacto + baixo esforço) OU strategic imperatives (altíssimo impacto)
  -> Implementar IMEDIATAMENTE
  -> Exemplo: Implementar survey NPS (impact 85, effort 20, score 79)

- HIGH (50-74): Important projects (bom impacto + esforço moderado)
  -> Implementar nos próximos 3-6 meses
  -> Exemplo: Redesenhar processo de vendas (impact 70, effort 50, score 60)

- MEDIUM (25-49): Nice-to-have improvements (impacto moderado + esforço moderado/alto)
  -> Considerar para próximos 6-12 meses
  -> Exemplo: Padronizar templates (impact 40, effort 30, score 42)

- LOW (0-24): Deprioritize or eliminate (baixo impacto OU alto esforço)
  -> Adiar indefinidamente ou eliminar
  -> Exemplo: Projeto complexo com ROI incerto (impact 30, effort 80, score 18)

INSTRUÇÕES DE AVALIAÇÃO:

1. PARA CADA ITEM A PRIORIZAR:
   - Analisar título, descrição, perspectiva BSC, contexto da empresa
   - Avaliar os 4 critérios (0-100 scale) com justificativa clara
   - Calcular score final usando a fórmula
   - Determinar priority_level baseado no score (75-100: CRITICAL, 50-74: HIGH, 25-49: MEDIUM, 0-24: LOW)

2. RANKING DOS ITEMS:
   - Ordenar items por score final (maior score = rank 1 = mais prioritário)
   - Em caso de empate, priorizar maior strategic_impact
   - Garantir ranks sequenciais únicos (1, 2, 3, ..., N)

3. VALIDAÇÕES DE QUALIDADE:
   - Scores entre 0-100 para todos critérios
   - priority_level alinhado com score (ex: score 79 deve ser HIGH, não CRITICAL)
   - Ranks únicos e sequenciais (1, 2, 3, ..., N)
   - Justificativas claras para cada critério

4. CONTEXTO BSC:
   - Usar conhecimento da literatura BSC fornecido para embasar avaliações
   - Considerar interconexões entre perspectivas BSC
   - Avaliar contribuição para balanceamento estratégico

BALANCEAMENTO DA MATRIZ:

[OK] DISTRIBUIÇÃO IDEAL DE PRIORIDADES:
   - 10-20% items CRITICAL (quick wins)
   - 30-40% items HIGH (important projects)
   - 30-40% items MEDIUM (nice-to-have)
   - 10-20% items LOW (deprioritize)

[OK] BALANCEAMENTO POR PERSPECTIVA BSC:
   - Mínimo 1 item em cada perspectiva principal (Financeira, Clientes, Processos, Aprendizado)
   - Ideal: distribuição equilibrada (20-30% cada perspectiva)

REQUISITOS DE QUALIDADE:

[OK] CRITÉRIOS BEM JUSTIFICADOS: Cada score 0-100 baseado em análise objetiva
[OK] SCORE CALCULADO CORRETAMENTE: Formula aplicada rigorosamente
[OK] PRIORITY_LEVEL ALINHADO: Baseado exatamente no range de score
[OK] RANKS ÚNICOS E SEQUENCIAIS: 1, 2, 3, ..., N sem gaps ou duplicatas
[OK] CONTEXTO BSC UTILIZADO: Conhecimento da literatura aplicado nas avaliações
[OK] DISTRIBUIÇÃO EQUILIBRADA: Prioridades distribuídas conforme ideal (não todos CRITICAL)

OUTPUT ESPERADO:
Gere uma matriz de priorização completa (PrioritizationMatrix) com todos os items avaliados, scores calculados, ranks definidos e distribuição de prioridades equilibrada.

IMPORTANTE: Seja rigoroso na avaliação dos critérios. Não inflacione scores. Use o conhecimento BSC fornecido para embasar as avaliações. Garanta que ranks são únicos e sequenciais."""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_company_context(client_profile) -> str:
    """Constrói contexto da empresa para prompts de Prioritization Matrix.

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

    if (
        client_profile.context
        and hasattr(client_profile.context, "strategic_priorities")
        and client_profile.context.strategic_priorities
    ):
        priorities = ", ".join(client_profile.context.strategic_priorities[:3])
        context += f"\n\nPrioridades estratégicas: {priorities}"

    return context


def build_items_context(items_to_prioritize: list) -> str:
    """Constrói contexto dos items a priorizar.

    Args:
        items_to_prioritize: Lista de objetivos/ações estratégicas a priorizar
            Cada item deve ser dict com: {id, type, title, description, perspective}

    Returns:
        String formatada com items a priorizar
    """
    if not items_to_prioritize:
        return "Nenhum item fornecido para priorização."

    context = f"Total de {len(items_to_prioritize)} items a priorizar:\n\n"

    for i, item in enumerate(items_to_prioritize, 1):
        item_id = item.get("id", f"item_{i}")
        item_type = item.get("type", "strategic_objective")
        title = item.get("title", "Título não disponível")
        description = item.get("description", "Descrição não disponível")
        perspective = item.get("perspective", "Cross-Perspective")

        context += f"{i}. [{item_id}] {title}\n"
        context += f"   Tipo: {item_type}\n"
        context += f"   Perspectiva BSC: {perspective}\n"
        context += f"   Descrição: {description}\n\n"

    return context


def build_bsc_knowledge_context(
    financial_knowledge: str = "",
    customer_knowledge: str = "",
    process_knowledge: str = "",
    learning_knowledge: str = "",
) -> str:
    """Constrói contexto de conhecimento BSC para prompts de Prioritization.

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


def format_prioritization_matrix_for_display(matrix) -> str:
    """Formata PrioritizationMatrix para exibição amigável.

    Args:
        matrix: PrioritizationMatrix object

    Returns:
        String formatada para exibição
    """
    if not matrix:
        return "Matriz de priorização não disponível."

    output = "[EMOJI] MATRIZ DE PRIORIZAÇÃO BSC\n"
    output += f"{'='*60}\n\n"

    # Contexto da priorização
    output += "[EMOJI] CONTEXTO:\n"
    output += f"{matrix.prioritization_context}\n\n"

    # Resumo executivo
    output += "[EMOJI] RESUMO EXECUTIVO:\n"
    output += f"{matrix.summary()}\n\n"

    # Configuração de pesos
    output += "[EMOJI] CONFIGURAÇÃO DE PESOS:\n"
    for key, value in matrix.weights_config.items():
        output += f"• {key}: {value*100:.0f}%\n"
    output += "\n"

    # Items priorizados (ordenados por rank)
    output += "[EMOJI] ITEMS PRIORIZADOS (Top -> Baixo):\n"
    output += f"{'='*60}\n"

    sorted_items = sorted(matrix.items, key=lambda x: x.rank)

    for item in sorted_items:
        # Ícones por priority level
        priority_icon = (
            "[EMOJI]"
            if item.priority_level == "CRITICAL"
            else (
                "[EMOJI]"
                if item.priority_level == "HIGH"
                else "[EMOJI]" if item.priority_level == "MEDIUM" else "[EMOJI]"
            )
        )

        output += f"\n#{item.rank} | {priority_icon} {item.priority_level} | Score: {item.final_score:.2f}\n"
        output += f"    {item.title}\n"
        output += f"    Perspectiva: {item.perspective} | Tipo: {item.item_type}\n"
        output += "    Critérios:\n"
        output += f"      • Strategic Impact: {item.criteria.strategic_impact:.1f}%\n"
        output += f"      • Implementation Effort: {item.criteria.implementation_effort:.1f}% (invertido no cálculo)\n"
        output += f"      • Urgency: {item.criteria.urgency:.1f}%\n"
        output += f"      • Strategic Alignment: {item.criteria.strategic_alignment:.1f}%\n"
        output += f"    Descrição: {item.description[:100]}{'...' if len(item.description) > 100 else ''}\n"

    output += f"\n{'='*60}\n"
    output += "[OK] Priorização concluída com sucesso!\n"

    return output
