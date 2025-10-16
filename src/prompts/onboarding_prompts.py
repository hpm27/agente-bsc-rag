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
        f"✓ Perfeito! Empresa **{company_name}** no setor de **{industry}** registrada.\n"
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
        f"✓ Excelente! Identifiquei **{num_challenges} desafios estratégicos** principais:\n\n"
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
        f"✓ Ótimo! **{num_objectives} objetivos estratégicos** definidos nas perspectivas BSC:\n\n"
        f"{objectives_summary}"
    )


# ============================================================================
# MENSAGEM DE CONCLUSÃO (ONBOARDING COMPLETO)
# ============================================================================

ONBOARDING_COMPLETE_MESSAGE = """✅ **Onboarding Completo!**

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

    Args:
        step: OnboardingStep (1=COMPANY_INFO, 2=CHALLENGES, 3=OBJECTIVES)

    Returns:
        str: Pergunta formatada

    Example:
        >>> get_initial_question(1)
        "**Sobre sua empresa:**..."
    """
    questions = {
        1: COMPANY_INFO_QUESTION,
        2: CHALLENGES_QUESTION,
        3: OBJECTIVES_QUESTION,
    }

    return questions.get(step, "")


def get_followup_question(
    step: int, missing_info: list[str], context: dict[str, Any] | None = None
) -> str:
    """
    Retorna pergunta de follow-up baseado em informações faltantes.

    Args:
        step: OnboardingStep atual
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

    return FOLLOWUP_GENERIC


def get_confirmation_message(step: int, extraction: dict[str, Any]) -> str:
    """
    Retorna mensagem de confirmação ao completar um step.

    Args:
        step: OnboardingStep recém completo
        extraction: Dados extraídos (dict com name, industry, challenges, objectives, etc)

    Returns:
        str: Mensagem de confirmação personalizada

    Example:
        >>> extraction = {"name": "Empresa X", "industry": "Tecnologia", "size": "50-200"}
        >>> get_confirmation_message(1, extraction)
        "✓ Perfeito! Empresa Empresa X no setor de Tecnologia registrada..."
    """
    if step == 1:  # COMPANY_INFO
        return generate_company_info_confirmation(
            extraction.get("name", "sua empresa"),
            extraction.get("industry", "seu setor"),
            extraction.get("size", "não especificado"),
        )

    elif step == 2:  # CHALLENGES
        challenges = extraction.get("challenges", [])
        return generate_challenges_confirmation(len(challenges), challenges)

    elif step == 3:  # OBJECTIVES
        objectives = extraction.get("objectives", [])
        return generate_objectives_confirmation(len(objectives), objectives)

    return "✓ Informações registradas!"

