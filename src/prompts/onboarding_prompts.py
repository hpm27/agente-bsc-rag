"""
Prompts conversacionais para OnboardingAgent.

Centraliza todos os templates de mensagens, perguntas e confirmações
usados no processo de onboarding multi-turn.

Autor: BSC Consulting Agent v2.0
Data: 2025-10-15
Atualizado: 2025-12-01 (Dez/2025)
- Adicionadas perguntas de estrategia/visao (Kaplan & Norton best practice)
- Adicionada identificacao de estagio do negocio (Growth/Sustain/Harvest)
- Melhoradas perguntas de segmentacao de clientes
"""

from typing import Any

# ============================================================================
# MENSAGENS DE BOAS-VINDAS
# ============================================================================

WELCOME_MESSAGE = """Bem-vindo ao diagnostico estrategico BSC. Para iniciarmos de forma estruturada, preciso identificar a empresa que sera analisada. Qual e o nome da empresa, o setor de atuacao e o numero aproximado de colaboradores?"""


# ============================================================================
# PERGUNTAS INICIAIS POR STEP
# ============================================================================

COMPANY_INFO_QUESTION = """**Sobre sua empresa:**

Por favor, me conte:
- Qual o **nome da empresa**?
- Em qual **setor/industria** voces atuam?
- Qual o **tamanho aproximado** (numero de funcionarios)?"""


# ============================================================================
# FASE 3 - PERGUNTAS DE ESTRATEGIA/VISAO (Dez/2025)
# Best Practice Kaplan & Norton: Entender estrategia ANTES das perspectivas BSC
# ============================================================================

STRATEGY_VISION_QUESTION = """**Estrategia e Visao Empresarial:**

Para um diagnostico BSC efetivo, preciso entender o direcionamento estrategico da empresa.

1. **VISAO**: Onde a empresa quer estar em 3-5 anos?
2. **PROPOSTA DE VALOR**: Por que os clientes compram de voces (e nao dos concorrentes)?
3. **DIFERENCIAIS**: O que diferencia a empresa no mercado?

Pode responder de forma livre - essas informacoes guiarao todo o diagnostico BSC."""


BUSINESS_STAGE_QUESTION = """**Estagio do Negocio:**

Para recomendar os KPIs mais adequados, preciso identificar o estagio atual da empresa:

1. **CRESCIMENTO (Growth)**: Empresa em expansao rapida, investindo para ganhar mercado
   - Foco: Crescimento de receita, novos clientes, novos produtos
   - Aceita margens menores para crescer

2. **MANUTENCAO (Sustain)**: Empresa madura buscando maximizar retorno
   - Foco: Lucratividade, ROI, eficiencia operacional
   - Equilibrio entre crescimento e margem

3. **COLHEITA (Harvest)**: Empresa maximizando fluxo de caixa
   - Foco: Cash flow, reducao de custos, eficiencia maxima
   - Investimentos minimos, retorno maximo

Em qual desses estagios a empresa se encontra hoje?"""


CUSTOMER_SEGMENTATION_QUESTION = """**Segmentacao de Clientes:**

Para a perspectiva de Clientes do BSC, preciso entender sua base:

1. **SEGMENTOS-ALVO**: Quais sao os principais perfis de clientes que voces atendem?
2. **SEGMENTO MAIS LUCRATIVO**: Qual tipo de cliente gera mais receita/margem?
3. **SEGMENTOS NAO ATENDIDOS**: Existem clientes que voces conscientemente escolhem NAO atender?
4. **PROPOSTA POR SEGMENTO**: O que cada tipo de cliente mais valoriza na relacao com voces?

Pode descrever seus clientes de forma livre."""


CHALLENGES_QUESTION = """**Desafios Estrategicos:**

Quais são os **3 principais desafios estratégicos** que sua empresa enfrenta atualmente?

Podem ser relacionados a:
- Crescimento e expansão
- Competitividade no mercado
- Eficiência operacional
- Qualidade de produtos/serviços
- Gestão de pessoas
- Inovação e tecnologia"""


# ============================================================================
# FASE 2 - PERGUNTAS ESPECIFICAS COM METRICAS (Dez/2025)
# Best Practice McKinsey: Perguntas quantificadas > genéricas
# ============================================================================

CHALLENGES_QUESTION_V2 = """**Desafios Estrategicos com Metricas:**

Para um diagnostico BSC preciso, preciso entender os GAPS quantitativos entre situacao atual e desejada.

Responda o que souber (nao precisa preencher tudo agora):

**PERSPECTIVA FINANCEIRA:**
- Faturamento anual ATUAL: R$ _______
- Meta de faturamento (12 meses): R$ _______
- Margem EBITDA atual: _____% | Meta: _____%

**PERSPECTIVA PROCESSOS:**
- Lead time atual (pedido ate entrega): _____ dias
- Lead time ideal: _____ dias
- Principal gargalo operacional: _________________

**PERSPECTIVA CLIENTES:**
- Numero de clientes ativos: _______
- Taxa de churn mensal: _____%
- NPS atual (se souber): _______

**PERSPECTIVA APRENDIZADO:**
- Numero de funcionarios: _______
- Taxa de rotatividade anual: _____%
- Sistemas utilizados (ERP/CRM/BI): _________________

Pode responder os campos que conhecer - iremos aprofundar os mais criticos."""


# ============================================================================
# FASE 3 - PERGUNTAS-GUIA OFICIAIS BSC (Dez/2025)
# Best Practice Kaplan & Norton (1996, Fig 1-1): 4 perguntas fundamentais
# ============================================================================

BSC_FINANCIAL_PERSPECTIVE_QUESTION = """**Perspectiva Financeira (Kaplan & Norton):**

Pergunta-guia BSC: "Para ter sucesso financeiro, como devemos aparecer para nossos acionistas/proprietarios?"

Para responder essa pergunta, me conte:
1. **RECEITA**: Faturamento atual e meta para 12 meses?
2. **LUCRATIVIDADE**: Margem EBITDA atual e meta?
3. **RETORNO**: Qual ROI/ROCE a empresa busca?
4. **RISCO**: Quais sao os principais riscos financeiros?"""


BSC_CUSTOMER_PERSPECTIVE_QUESTION = """**Perspectiva de Clientes (Kaplan & Norton):**

Pergunta-guia BSC: "Para alcancar nossa visao, como devemos aparecer para nossos clientes?"

Para responder essa pergunta, me conte:
1. **SEGMENTOS**: Quais sao os segmentos de clientes que voces atendem?
2. **PROPOSTA DE VALOR**: Por que os clientes escolhem voces (preco, qualidade, relacionamento, inovacao)?
3. **SATISFACAO**: Como esta a satisfacao dos clientes (NPS, pesquisas, feedbacks)?
4. **RETENCAO**: Qual a taxa de retencao/churn dos clientes?"""


BSC_PROCESS_PERSPECTIVE_QUESTION = """**Perspectiva de Processos Internos (Kaplan & Norton):**

Pergunta-guia BSC: "Para satisfazer acionistas e clientes, em quais processos devemos excel?"

Para responder essa pergunta, me conte:
1. **INOVACAO**: Quanto tempo leva para desenvolver novos produtos/servicos?
2. **OPERACOES**: Qual o lead time atual? Qual o principal gargalo operacional?
3. **POS-VENDA**: Como funciona o atendimento ao cliente apos a venda?
4. **QUALIDADE**: Qual a taxa de defeitos/retrabalho?"""


BSC_LEARNING_PERSPECTIVE_QUESTION = """**Perspectiva de Aprendizado e Crescimento (Kaplan & Norton):**

Pergunta-guia BSC: "Para alcancar nossa visao, como sustentaremos nossa capacidade de mudar e melhorar?"

Para responder essa pergunta, me conte:
1. **PESSOAS**: Quantos funcionarios? Taxa de rotatividade? Competencias que faltam?
2. **SISTEMAS**: Quais sistemas utilizam (ERP, CRM, BI)? Estao integrados?
3. **CULTURA**: Como e a cultura (inovadora, conservadora)? Existe alinhamento com estrategia?
4. **INCENTIVOS**: Os incentivos estao alinhados aos objetivos estrategicos?"""


CHALLENGES_FOLLOWUP_ROOT_CAUSE = """**Aprofundamento do Desafio:**

Voce mencionou {challenge_summary}. Para entender melhor:

1. **Quantifique o GAP:** Qual o valor ATUAL vs o IDEAL?
2. **Causa-raiz:** Esse problema e causado por limitacao de equipamento, pessoas ou processo?
3. **Tentativas anteriores:** Ja tentaram alguma iniciativa para resolver? O que funcionou/nao funcionou?
4. **Impacto financeiro:** Quanto vocês estimam perder por ano com esse problema?

Pode responder o que souber - essas informacoes serao valiosas para o diagnostico."""


OBJECTIVES_QUESTION_SMART = """**Objetivos SMART (Especificos, Mensuraveis, Alcancaveis, Relevantes, Temporais):**

Para cada objetivo, tente incluir:
- **METRICA**: Qual numero vai mudar? (%, R$, unidades)
- **PRAZO**: Ate quando? (ex: "em 12 meses", "ate dezembro 2025")

Exemplos de objetivos SMART:
- "Aumentar faturamento de R$24M para R$30M em 12 meses" [OK - tem metrica e prazo]
- "Melhorar satisfacao do cliente" [INCOMPLETO - falta metrica e prazo]
- "Reduzir lead time de 40 dias para 25 dias ate junho 2025" [OK - SMART completo]

Quais sao os 3-5 objetivos estrategicos SMART da empresa?"""


# ============================================================================
# FASE 4 - PRIORIZACAO DE PROBLEMAS (Dez/2025)
# Best Practice BCG: Prioritization Matrix (Impacto x Urgencia)
# ============================================================================

PRIORITIZATION_QUESTION = """**Priorizacao dos Desafios Estrategicos:**

Voce mencionou {num_challenges} desafios. Para focarmos no que realmente importa para a estrategia BSC:

**1. MAIOR IMPACTO:**
Dos desafios abaixo, qual tem **MAIOR IMPACTO** no resultado financeiro da empresa?
{challenges_list}

**2. MAIOR URGENCIA:**
E qual tem **MAIOR URGENCIA** de resolucao? (pode piorar significativamente se nao resolvido em 6 meses)

**3. FACILIDADE (opcional):**
Qual seria mais FACIL de implementar com os recursos atuais?

Pode responder de forma livre ou dar notas de 1-10 para cada dimensao:
- Impacto (1=baixo, 10=muito alto)
- Urgencia (1=pode esperar, 10=critico agora)
- Facilidade (1=muito dificil, 10=rapido de implementar)"""


PRIORITIZATION_FOLLOWUP = """**Aprofundamento da Priorizacao:**

Voce indicou que "{top_challenge}" e o desafio mais critico.

Para quantificar melhor:
1. **Gap quantificado**: Qual o valor ATUAL vs o IDEAL? (ex: "50 ton/mes vs 250 ton/mes")
2. **Impacto financeiro**: Quanto a empresa perde/deixa de ganhar por ano por causa desse problema?
3. **Tentativas anteriores**: Ja tentaram resolver? O que funcionou/nao funcionou?

Essas informacoes serao valiosas para priorizar as acoes no plano estrategico BSC."""


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
    Retorna pergunta inicial para um step especifico.

    SESSAO 49 (Dez/2025): Expandido para 11 steps baseado em Kaplan & Norton best practices.
    - Adicionadas perguntas de estrategia/visao ANTES dos desafios
    - Adicionada identificacao de estagio do negocio (Growth/Sustain/Harvest)
    - Adicionadas perguntas por perspectiva BSC oficial

    Args:
        step: OnboardingStep (1-11)
            1=COMPANY_INFO (basico)
            2=STRATEGY_VISION (novo - estrategia antes de desafios)
            3=BUSINESS_STAGE (novo - Growth/Sustain/Harvest)
            4=CUSTOMER_SEGMENTATION (novo - antes das perspectivas)
            5=CHALLENGES (desafios com metricas V2)
            6=OBJECTIVES (SMART goals)
            7-11=OPCIONAIS (MVV, Competitive, Organization, Project, Perspectivas BSC)

    Returns:
        str: Pergunta formatada

    Example:
        >>> get_initial_question(1)
        "**Sobre sua empresa:**..."
        >>> get_initial_question(2)
        "**Estrategia e Visao Empresarial:**..."
    """
    # FASE 3 (Dez/2025): Ordem atualizada seguindo Kaplan & Norton
    # 1. Entender empresa (basico)
    # 2. Entender estrategia/visao (ANTES de perguntar desafios!)
    # 3. Identificar estagio (Growth/Sustain/Harvest)
    # 4. Segmentacao de clientes
    # 5. Desafios com metricas
    # 6. Objetivos SMART
    # 7+. Opcionais
    questions = {
        # OBRIGATORIOS (Steps 1-6) - Ordem Kaplan & Norton
        1: COMPANY_INFO_QUESTION,
        2: STRATEGY_VISION_QUESTION,  # NOVO: Estrategia ANTES de desafios
        3: BUSINESS_STAGE_QUESTION,  # NOVO: Growth/Sustain/Harvest
        4: CUSTOMER_SEGMENTATION_QUESTION,  # NOVO: Segmentos-alvo
        5: CHALLENGES_QUESTION_V2,  # V2: Com metricas especificas
        6: OBJECTIVES_QUESTION_SMART,  # V2: SMART goals
        # OPCIONAIS (Steps 7-11) - Aprofundamento
        7: MVV_QUESTION,
        8: COMPETITIVE_CONTEXT_QUESTION,
        9: ORGANIZATION_STRUCTURE_QUESTION,
        10: PROJECT_CONSTRAINTS_QUESTION,
        # PERSPECTIVAS BSC DETALHADAS (sob demanda)
        11: BSC_FINANCIAL_PERSPECTIVE_QUESTION,
        12: BSC_CUSTOMER_PERSPECTIVE_QUESTION,
        13: BSC_PROCESS_PERSPECTIVE_QUESTION,
        14: BSC_LEARNING_PERSPECTIVE_QUESTION,
    }

    return questions.get(step, "")


def get_followup_question(
    step: int, missing_info: list[str], context: dict[str, Any] | None = None
) -> str:
    """
    Retorna pergunta de follow-up baseado em informacoes faltantes.

    SESSAO 49 (Dez/2025): Expandido para 14 steps com Kaplan & Norton best practices.

    Args:
        step: OnboardingStep atual (1-14)
        missing_info: Lista de campos faltando
        context: Contexto adicional (opcional)

    Returns:
        str: Pergunta de follow-up personalizada

    Example:
        >>> get_followup_question(1, ["nome da empresa"])
        "Entendi! Mas nao identifiquei o nome da empresa..."
    """
    if step == 1:  # COMPANY_INFO
        if "nome da empresa" in str(missing_info):
            return FOLLOWUP_MISSING_COMPANY_NAME
        if "setor" in str(missing_info) or "industry" in str(missing_info):
            return FOLLOWUP_MISSING_INDUSTRY
        if "tamanho" in str(missing_info) or "size" in str(missing_info):
            return FOLLOWUP_MISSING_SIZE

    elif step == 2:  # STRATEGY_VISION (novo)
        return """Entendi! Mas para um diagnostico BSC completo, preciso entender melhor a estrategia.

Especificamente:
- Qual a **visao de longo prazo** da empresa (3-5 anos)?
- Por que os clientes escolhem voces ao inves dos concorrentes?"""

    elif step == 3:  # BUSINESS_STAGE (novo)
        return """Para recomendar os KPIs mais adequados, preciso saber:

A empresa esta mais focada em:
- **CRESCER** rapidamente (aceitar margens menores para ganhar mercado)?
- **MANTER** lucratividade (equilibrio entre crescimento e margem)?
- **MAXIMIZAR** caixa (foco em eficiencia, investimentos minimos)?"""

    elif step == 4:  # CUSTOMER_SEGMENTATION (novo)
        return """Para a perspectiva de Clientes do BSC, preciso entender melhor:

- Quais sao os **tipos de clientes** que voces atendem (segmentos)?
- Qual segmento e mais **lucrativo**?
- O que os clientes mais **valorizam** na relacao com voces?"""

    elif step == 5:  # CHALLENGES
        return FOLLOWUP_INCOMPLETE_CHALLENGES

    elif step == 6:  # OBJECTIVES
        # Identificar perspectivas faltantes (se contexto fornecido)
        missing_perspectives = "Financeira, Clientes, Processos, Aprendizado"
        if context and "missing_perspectives" in context:
            missing_perspectives = ", ".join(context["missing_perspectives"])

        return FOLLOWUP_INCOMPLETE_OBJECTIVES.format(missing_perspectives=missing_perspectives)

    # OPCIONAIS (Steps 7-10) - perguntas de enriquecimento
    elif step == 7:  # MVV
        return MVV_QUESTION

    elif step == 8:  # COMPETITIVE_CONTEXT
        return COMPETITIVE_CONTEXT_QUESTION

    elif step == 9:  # ORGANIZATION_STRUCTURE
        return ORGANIZATION_STRUCTURE_QUESTION

    elif step == 10:  # PROJECT_CONSTRAINTS
        return PROJECT_CONSTRAINTS_QUESTION

    # PERSPECTIVAS BSC DETALHADAS (Steps 11-14)
    elif step == 11:  # BSC_FINANCIAL
        return BSC_FINANCIAL_PERSPECTIVE_QUESTION

    elif step == 12:  # BSC_CUSTOMER
        return BSC_CUSTOMER_PERSPECTIVE_QUESTION

    elif step == 13:  # BSC_PROCESS
        return BSC_PROCESS_PERSPECTIVE_QUESTION

    elif step == 14:  # BSC_LEARNING
        return BSC_LEARNING_PERSPECTIVE_QUESTION

    return FOLLOWUP_GENERIC


def get_confirmation_message(step: int, extraction: dict[str, Any]) -> str:
    """
    Retorna mensagem de confirmacao ao completar um step.

    SESSAO 49 (Dez/2025): Expandido para 14 steps com Kaplan & Norton best practices.

    Args:
        step: OnboardingStep recem completo (1-14)
        extraction: Dados extraidos (dict com name, industry, challenges, objectives, etc)

    Returns:
        str: Mensagem de confirmacao personalizada

    Example:
        >>> extraction = {"name": "Empresa X", "industry": "Tecnologia", "size": "50-200"}
        >>> get_confirmation_message(1, extraction)
        "[OK] Perfeito! Empresa Empresa X no setor de Tecnologia registrada..."
    """
    if step == 1:  # COMPANY_INFO
        return generate_company_info_confirmation(
            extraction.get("name", "sua empresa"),
            extraction.get("industry", "seu setor"),
            extraction.get("size", "nao especificado"),
        )

    if step == 2:  # STRATEGY_VISION (novo)
        vision = extraction.get("vision", "")
        value_prop = extraction.get("value_proposition", "")
        parts = []
        if vision:
            parts.append(f"Visao: {vision[:80]}...")
        if value_prop:
            parts.append(f"Proposta de valor: {value_prop[:80]}...")
        if parts:
            return "[OK] Estrategia registrada!\n   " + "\n   ".join(parts)
        return "[OK] Entendi o direcionamento estrategico."

    if step == 3:  # BUSINESS_STAGE (novo)
        stage = extraction.get("business_stage", "")
        stage_map = {
            "growth": "CRESCIMENTO (foco em expansao)",
            "sustain": "MANUTENCAO (foco em ROI)",
            "harvest": "COLHEITA (foco em caixa)"
        }
        stage_desc = stage_map.get(stage.lower(), stage) if stage else "identificado"
        return f"[OK] Estagio do negocio: {stage_desc}. KPIs serao ajustados para esse perfil."

    if step == 4:  # CUSTOMER_SEGMENTATION (novo)
        segments = extraction.get("customer_segments", [])
        if segments:
            return f"[OK] {len(segments)} segmento(s) de cliente identificado(s): {', '.join(segments[:3])}"
        return "[OK] Segmentacao de clientes registrada."

    if step == 5:  # CHALLENGES
        challenges = extraction.get("challenges", [])
        return generate_challenges_confirmation(len(challenges), challenges)

    if step == 6:  # OBJECTIVES
        objectives = extraction.get("objectives", [])
        return generate_objectives_confirmation(len(objectives), objectives)

    # OPCIONAIS (Steps 7-10) - confirmacoes simplificadas
    if step == 7:  # MVV
        mission = extraction.get("mission", "")
        vision = extraction.get("vision", "")
        values = extraction.get("core_values", [])
        parts = []
        if mission:
            parts.append(f"Missao: {mission[:50]}...")
        if vision:
            parts.append(f"Visao: {vision[:50]}...")
        if values:
            parts.append(f"Valores: {', '.join(values[:3])}")
        return "[OK] Fundamentos estrategicos registrados!\n   " + "\n   ".join(parts)

    if step == 8:  # COMPETITIVE_CONTEXT
        competitors = extraction.get("competitors", [])
        advantages = extraction.get("competitive_advantages", [])
        return (
            f"[OK] Contexto competitivo mapeado!\n"
            f"   Concorrentes: {len(competitors)} identificados\n"
            f"   Diferenciais: {len(advantages)} registrados"
        )

    if step == 9:  # ORGANIZATION_STRUCTURE
        departments = extraction.get("departments", [])
        systems = extraction.get("key_systems", [])
        return (
            f"[OK] Estrutura organizacional registrada!\n"
            f"   Departamentos: {len(departments)} areas\n"
            f"   Sistemas: {len(systems)} identificados"
        )

    if step == 10:  # PROJECT_CONSTRAINTS
        timeline = extraction.get("timeline", "nao definido")
        sponsor = extraction.get("sponsor_name", "nao definido")
        return (
            f"[OK] Escopo do projeto definido!\n" f"   Prazo: {timeline}\n" f"   Sponsor: {sponsor}"
        )

    return "[OK] Informações registradas!"
