"""
Prompts conversacionais para OnboardingAgent.

Centraliza todos os templates de mensagens, perguntas e confirmações
usados no processo de onboarding multi-turn.

Autor: BSC Consulting Agent v2.0
Data: 2025-10-15
"""

from typing import Any

# ============================================================================
# MENSAGENS DE BOAS-VINDAS
# ============================================================================

WELCOME_MESSAGE = """Olá! Sou o Agente Consultor BSC e vou ajudá-lo a estruturar sua estratégia empresarial.

Primeiro, preciso conhecer melhor sua empresa para personalizar o diagnóstico estratégico.
Vamos começar?"""


# ============================================================================
# PERGUNTAS INICIAIS POR STEP
# ============================================================================

COMPANY_INFO_QUESTION = """**Sobre sua empresa:**

Por favor, me conte:
- Qual o **nome da empresa**?
- Em qual **setor/indústria** vocês atuam?
- Qual o **tamanho aproximado** (número de funcionários)?"""


CHALLENGES_QUESTION = """**Desafios Estratégicos:**

Quais são os **3 principais desafios estratégicos** que sua empresa enfrenta atualmente?

Podem ser relacionados a:
- Crescimento e expansão
- Competitividade no mercado
- Eficiência operacional
- Qualidade de produtos/serviços
- Gestão de pessoas
- Inovação e tecnologia"""


OBJECTIVES_QUESTION = """**Objetivos Estratégicos (4 Perspectivas BSC):**

Vamos definir seus objetivos usando o framework Balanced Scorecard:

- **Perspectiva Financeira**: Quais metas financeiras? (receita, lucro, EBITDA, margens)
- **Perspectiva de Clientes**: O que querem alcançar com clientes? (satisfação, retenção, NPS, market share)
- **Perspectiva de Processos Internos**: Melhorias operacionais desejadas? (lead time, qualidade, produtividade)
- **Perspectiva de Aprendizado e Crescimento**: Desenvolvimento de pessoas e cultura? (treinamento, engajamento, inovação)

Pode listar 3-5 objetivos principais distribuídos nessas 4 áreas."""


# ============================================================================
# PERGUNTAS OPCIONAIS (STEPS 4-7) - Kaplan & Norton Best Practices
# SESSAO 45: Adicionado para diagnóstico BSC completo
# ============================================================================

MVV_QUESTION = """**Missão, Visão e Valores (Fundamentos Estratégicos):**

Para um diagnóstico mais completo, preciso entender os fundamentos da empresa:

- **Missão**: Por que a empresa existe? Qual o propósito central?
- **Visão**: Onde a empresa quer chegar nos próximos 5-10 anos?
- **Valores**: Quais princípios guiam as decisões e comportamentos?

Se vocês já têm isso definido, pode compartilhar? Se não, também é uma informação valiosa."""


COMPETITIVE_CONTEXT_QUESTION = """**Contexto Competitivo:**

Para entender seu posicionamento no mercado:

- **Concorrentes**: Quem são seus principais concorrentes (diretos e indiretos)?
- **Diferenciação**: O que torna sua empresa única? Qual sua proposta de valor?
- **Clientes-alvo**: Quais segmentos de clientes são prioritários para vocês?"""


ORGANIZATION_STRUCTURE_QUESTION = """**Estrutura Organizacional:**

Para mapear os recursos disponíveis:

- **Estrutura**: Quais os principais departamentos/áreas?
- **Pessoas**: Aproximadamente quantos funcionários? Competências-chave?
- **Sistemas**: Que sistemas utilizam (ERP, CRM, BI, etc)?
- **Métricas**: Quais KPIs já são rastreados hoje?"""


PROJECT_CONSTRAINTS_QUESTION = """**Escopo do Projeto BSC:**

Para definir expectativas:

- **Prazo**: Qual o prazo ideal para implementar o BSC?
- **Sponsor**: Quem será o patrocinador/responsável pelo projeto?
- **Sucesso**: Como vocês vão medir o sucesso deste projeto?
- **Histórico**: Já tentaram implementar BSC ou algo similar antes?"""


# ============================================================================
# TEMPLATES DE FOLLOW-UP (INFORMAÇÕES FALTANTES)
# ============================================================================

FOLLOWUP_MISSING_COMPANY_NAME = (
    "Entendi! Mas não identifiquei o **nome da empresa**. Pode me informar?"
)

FOLLOWUP_MISSING_INDUSTRY = (
    "Certo! Mas qual o **setor ou indústria** que a empresa atua? "
    "(Ex: tecnologia, saúde, varejo, manufatura, serviços, etc.)"
)

FOLLOWUP_MISSING_SIZE = (
    "OK! E qual o **tamanho aproximado** da empresa em número de funcionários? "
    "(Ex: 1-50, 50-200, 200-500, 500+)"
)

FOLLOWUP_INCOMPLETE_CHALLENGES = """Entendi o contexto! Mas preciso de **pelo menos 2-3 desafios estratégicos específicos** para fazer uma boa análise.

Pode detalhar:
- Qual o desafio principal que impede o crescimento?
- Quais problemas operacionais ou de mercado enfrentam?
- O que gostariam de resolver nos próximos 12-24 meses?"""

FOLLOWUP_INCOMPLETE_OBJECTIVES = """Ótimo início! Mas preciso de **pelo menos 3 objetivos estratégicos** distribuídos nas 4 perspectivas BSC.

Faltam objetivos nas áreas de:
{missing_perspectives}

Pode complementar com 1-2 objetivos em cada perspectiva faltante?"""


# ============================================================================
# MENSAGENS DE CONFIRMAÇÃO (STEP COMPLETO)
# ============================================================================


def generate_company_info_confirmation(company_name: str, industry: str, size: str) -> str:
    """
    Gera confirmação após completar Company Info.

    Args:
        company_name: Nome da empresa extraído
        industry: Setor/indústria extraído
        size: Tamanho da empresa extraído

    Returns:
        str: Mensagem de confirmação personalizada
    """
    return (
        f"[OK] Perfeito! Empresa **{company_name}** no setor de **{industry}** registrada.\n"
        f"   Porte: {size}"
    )


def generate_challenges_confirmation(num_challenges: int, challenges: list[str]) -> str:
    """
    Gera confirmação após completar Challenges.

    Args:
        num_challenges: Número de desafios identificados
        challenges: Lista de desafios

    Returns:
        str: Mensagem de confirmação com resumo
    """
    challenges_summary = "\n".join([f"   {i+1}. {ch}" for i, ch in enumerate(challenges[:3])])

    return (
        f"[OK] Excelente! Identifiquei **{num_challenges} desafios estratégicos** principais:\n\n"
        f"{challenges_summary}"
    )


def generate_objectives_confirmation(num_objectives: int, objectives: list[str]) -> str:
    """
    Gera confirmação após completar Objectives.

    Args:
        num_objectives: Número de objetivos definidos
        objectives: Lista de objetivos

    Returns:
        str: Mensagem de confirmação com resumo
    """
    objectives_summary = "\n".join([f"   {i+1}. {obj}" for i, obj in enumerate(objectives[:5])])

    return (
        f"[OK] Ótimo! **{num_objectives} objetivos estratégicos** definidos nas perspectivas BSC:\n\n"
        f"{objectives_summary}"
    )


# ============================================================================
# MENSAGEM DE CONCLUSÃO (ONBOARDING COMPLETO)
# ============================================================================

ONBOARDING_COMPLETE_MESSAGE = """[OK] **Onboarding Completo!**

Perfeito! Tenho todas as informações necessárias para começarmos o diagnóstico estratégico.

**Próximos Passos:**
1. Análise aprofundada dos seus desafios usando ferramentas consultivas (SWOT, 5 Whys, Issue Tree)
2. Validação e priorização dos objetivos estratégicos
3. Construção do Mapa Estratégico BSC personalizado
4. Definição de KPIs e metas

Vamos agora aprofundar a análise? Preparado para a fase de **Discovery**?"""


# ============================================================================
# TEMPLATES DE FOLLOW-UP GENÉRICO (FALLBACK)
# ============================================================================

FOLLOWUP_GENERIC = """Pode fornecer mais detalhes sobre essa informação?

Quanto mais específico, melhor será a análise estratégica que poderei fazer."""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_initial_question(step: int) -> str:
    """
    Retorna pergunta inicial para um step específico.

    SESSAO 45: Expandido para 7 steps baseado em Kaplan & Norton best practices.

    Args:
        step: OnboardingStep (1-7)
            1=COMPANY_INFO, 2=CHALLENGES, 3=OBJECTIVES (obrigatórios)
            4=MVV, 5=COMPETITIVE_CONTEXT, 6=ORGANIZATION_STRUCTURE,
            7=PROJECT_CONSTRAINTS (opcionais)

    Returns:
        str: Pergunta formatada

    Example:
        >>> get_initial_question(1)
        "**Sobre sua empresa:**..."
        >>> get_initial_question(4)
        "**Missão, Visão e Valores (Fundamentos Estratégicos):**..."
    """
    questions = {
        # OBRIGATÓRIOS (Steps 1-3)
        1: COMPANY_INFO_QUESTION,
        2: CHALLENGES_QUESTION,
        3: OBJECTIVES_QUESTION,
        # OPCIONAIS (Steps 4-7) - Kaplan & Norton best practices
        4: MVV_QUESTION,
        5: COMPETITIVE_CONTEXT_QUESTION,
        6: ORGANIZATION_STRUCTURE_QUESTION,
        7: PROJECT_CONSTRAINTS_QUESTION,
    }

    return questions.get(step, "")


def get_followup_question(
    step: int, missing_info: list[str], context: dict[str, Any] | None = None
) -> str:
    """
    Retorna pergunta de follow-up baseado em informações faltantes.

    SESSAO 45: Expandido para 7 steps.

    Args:
        step: OnboardingStep atual (1-7)
        missing_info: Lista de campos faltando
        context: Contexto adicional (opcional)

    Returns:
        str: Pergunta de follow-up personalizada

    Example:
        >>> get_followup_question(1, ["nome da empresa"])
        "Entendi! Mas não identifiquei o nome da empresa..."
    """
    if step == 1:  # COMPANY_INFO
        if "nome da empresa" in str(missing_info):
            return FOLLOWUP_MISSING_COMPANY_NAME
        if "setor/indústria" in str(missing_info) or "industry" in str(missing_info):
            return FOLLOWUP_MISSING_INDUSTRY
        if "tamanho" in str(missing_info) or "size" in str(missing_info):
            return FOLLOWUP_MISSING_SIZE

    elif step == 2:  # CHALLENGES
        return FOLLOWUP_INCOMPLETE_CHALLENGES

    elif step == 3:  # OBJECTIVES
        # Identificar perspectivas faltantes (se contexto fornecido)
        missing_perspectives = "Financeira, Clientes, Processos, Aprendizado"
        if context and "missing_perspectives" in context:
            missing_perspectives = ", ".join(context["missing_perspectives"])

        return FOLLOWUP_INCOMPLETE_OBJECTIVES.format(missing_perspectives=missing_perspectives)

    # OPCIONAIS (Steps 4-7) - perguntas de enriquecimento
    elif step == 4:  # MVV
        return MVV_QUESTION

    elif step == 5:  # COMPETITIVE_CONTEXT
        return COMPETITIVE_CONTEXT_QUESTION

    elif step == 6:  # ORGANIZATION_STRUCTURE
        return ORGANIZATION_STRUCTURE_QUESTION

    elif step == 7:  # PROJECT_CONSTRAINTS
        return PROJECT_CONSTRAINTS_QUESTION

    return FOLLOWUP_GENERIC


def get_confirmation_message(step: int, extraction: dict[str, Any]) -> str:
    """
    Retorna mensagem de confirmação ao completar um step.

    SESSAO 45: Expandido para 7 steps.

    Args:
        step: OnboardingStep recém completo (1-7)
        extraction: Dados extraídos (dict com name, industry, challenges, objectives, etc)

    Returns:
        str: Mensagem de confirmação personalizada

    Example:
        >>> extraction = {"name": "Empresa X", "industry": "Tecnologia", "size": "50-200"}
        >>> get_confirmation_message(1, extraction)
        "[OK] Perfeito! Empresa Empresa X no setor de Tecnologia registrada..."
    """
    if step == 1:  # COMPANY_INFO
        return generate_company_info_confirmation(
            extraction.get("name", "sua empresa"),
            extraction.get("industry", "seu setor"),
            extraction.get("size", "não especificado"),
        )

    if step == 2:  # CHALLENGES
        challenges = extraction.get("challenges", [])
        return generate_challenges_confirmation(len(challenges), challenges)

    if step == 3:  # OBJECTIVES
        objectives = extraction.get("objectives", [])
        return generate_objectives_confirmation(len(objectives), objectives)

    # OPCIONAIS (Steps 4-7) - confirmações simplificadas
    if step == 4:  # MVV
        mission = extraction.get("mission", "")
        vision = extraction.get("vision", "")
        values = extraction.get("core_values", [])
        parts = []
        if mission:
            parts.append(f"Missão: {mission[:50]}...")
        if vision:
            parts.append(f"Visão: {vision[:50]}...")
        if values:
            parts.append(f"Valores: {', '.join(values[:3])}")
        return "[OK] Fundamentos estratégicos registrados!\n   " + "\n   ".join(parts)

    if step == 5:  # COMPETITIVE_CONTEXT
        competitors = extraction.get("competitors", [])
        advantages = extraction.get("competitive_advantages", [])
        return (
            f"[OK] Contexto competitivo mapeado!\n"
            f"   Concorrentes: {len(competitors)} identificados\n"
            f"   Diferenciais: {len(advantages)} registrados"
        )

    if step == 6:  # ORGANIZATION_STRUCTURE
        departments = extraction.get("departments", [])
        systems = extraction.get("key_systems", [])
        return (
            f"[OK] Estrutura organizacional registrada!\n"
            f"   Departamentos: {len(departments)} áreas\n"
            f"   Sistemas: {len(systems)} identificados"
        )

    if step == 7:  # PROJECT_CONSTRAINTS
        timeline = extraction.get("timeline", "não definido")
        sponsor = extraction.get("sponsor_name", "não definido")
        return (
            f"[OK] Escopo do projeto definido!\n" f"   Prazo: {timeline}\n" f"   Sponsor: {sponsor}"
        )

    return "[OK] Informações registradas!"
