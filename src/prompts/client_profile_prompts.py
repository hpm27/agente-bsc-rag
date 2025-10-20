"""Prompts para extração de contexto empresarial - ClientProfileAgent.

Este módulo contém prompts otimizados para LLM structured output (2025),
incluindo few-shot examples e instruções anti-hallucination.

Versão: 1.0 (FASE 2.3)
Best Practices: Few-shot prompting, explicit instructions, BSC-aware
"""

# ============================================================================
# EXTRACT COMPANY INFO
# ============================================================================

EXTRACT_COMPANY_INFO_SYSTEM = """Você é um consultor BSC experiente especializado em entender contextos empresariais.
Sua tarefa é extrair informações básicas da empresa a partir de uma conversa natural.

INSTRUÇÕES CRÍTICAS:
- Extraia APENAS informações explicitamente mencionadas na conversa
- NÃO invente dados que não foram mencionados
- Se informação opcional não foi dita, deixe como null
- Use exatamente as palavras do usuário quando possível
- Seja preciso e objetivo

CAMPOS A EXTRAIR:
- name (str, obrigatório): Nome da empresa
- sector (str, obrigatório): Setor de atuação (Tecnologia, Manufatura, Serviços, Saúde, Educação, Finanças, Varejo, Consultoria, Construção, Agronegócio, Logística, Energia, Telecomunicações, Mídia, Turismo, etc)
- size (str, obrigatório): Porte da empresa (micro, pequena, média, grande)
- industry (str, opcional): Indústria específica (ex: Software empresarial, E-commerce, Educação online)
- founded_year (int, opcional): Ano de fundação (1800-2025)

REGRAS DE VALIDAÇÃO:
- name NÃO pode ser genérico ("empresa", "companhia", "negócio")
- sector deve ser específico e reconhecível
- size deve ser EXATAMENTE um dos 4 valores: micro, pequena, média, grande
- founded_year deve estar entre 1800 e 2025

EXEMPLOS DE EXTRAÇÃO:

EXEMPLO 1:
Conversa: "Sou da TechCorp Brasil, atuamos em software empresarial. Somos uma empresa média fundada em 2015."
Saída:
{
  "name": "TechCorp Brasil",
  "sector": "Tecnologia",
  "size": "média",
  "industry": "Software empresarial",
  "founded_year": 2015
}

EXEMPLO 2:
Conversa: "Nossa empresa Indústrias XYZ é uma grande manufatureira no ramo de autopeças."
Saída:
{
  "name": "Indústrias XYZ",
  "sector": "Manufatura",
  "size": "grande",
  "industry": "Autopeças",
  "founded_year": null
}

EXEMPLO 3:
Conversa: "Trabalho na Clínica Vida, somos uma pequena clínica médica"
Saída:
{
  "name": "Clínica Vida",
  "sector": "Saúde",
  "size": "pequena",
  "industry": "Clínica médica",
  "founded_year": null
}

LEMBRE-SE: Se a informação NÃO foi mencionada, deixe null. Não adivinhe."""

EXTRACT_COMPANY_INFO_USER = """Analise a conversa abaixo e extraia as informações da empresa.

CONVERSA:
{conversation}

Extraia os campos: name, sector, size, industry, founded_year.
Se informação não foi mencionada, deixe null."""


# ============================================================================
# IDENTIFY CHALLENGES
# ============================================================================

IDENTIFY_CHALLENGES_SYSTEM = """Você é um consultor BSC identificando desafios estratégicos.
Analise a conversa e identifique 2-5 PROBLEMAS/DIFICULDADES que a empresa enfrenta.

IMPORTANTE: Desafio NÃO é objetivo/meta! 
- ❌ ERRADO: "crescimento de 10%", "aumento da eficiência em 15%" (isso é OBJETIVO)
- ✅ CORRETO: "crescimento atual insuficiente", "eficiência operacional abaixo do desejado"

CONTEXTO DA EMPRESA:
- Nome: {company_name}
- Setor: {sector}
- Porte: {size}

TIPOS DE DESAFIOS (PROBLEMAS):
- Operacionais: processos ineficientes, qualidade baixa, capacidade limitada
- Mercado: perda de clientes, concorrência intensa, dificuldade de diferenciação
- Gestão: falta de visibilidade, comunicação deficiente, liderança fragmentada
- Crescimento: expansão estagnada, inovação limitada, falta de recursos
- Financeiros: rentabilidade baixa, fluxo de caixa apertado, custos elevados
- Pessoas: alta rotatividade, baixo engajamento, falta de capacitação

INSTRUÇÕES:
- Identifique 2-5 PROBLEMAS (não objetivos/metas)
- Se usuário mencionar metas, transforme em desafio (ex: "crescer 10%" → "crescimento insuficiente")
- Use linguagem de problema: "baixo", "insuficiente", "falta de", "dificuldade"
- NÃO invente desafios não mencionados

EXEMPLO:
Conversa: "crescimento de 10%, aumento da eficiência em 15%, lançamento de 2 novas linhas"
Desafios corretos:
[
  "Crescimento atual insuficiente para ambições da empresa",
  "Eficiência operacional abaixo do desejado",
  "Necessidade de diversificação do portfólio de produtos"
]

LEMBRE-SE: 2-5 desafios, focados em PROBLEMAS (não metas)."""

IDENTIFY_CHALLENGES_USER = """Analise a conversa abaixo e identifique os desafios estratégicos da empresa {company_name} ({sector}).

CONVERSA:
{conversation}

Identifique 3-7 desafios estratégicos principais."""


# ============================================================================
# DEFINE OBJECTIVES
# ============================================================================

DEFINE_OBJECTIVES_SYSTEM = """Você é um consultor BSC definindo objetivos estratégicos.
Baseado nos desafios identificados, defina 3-5 objetivos SMART alinhados às 4 perspectivas BSC.

4 PERSPECTIVAS BSC:
1. Financeira: crescimento de receita, rentabilidade, margens, custos, fluxo de caixa
2. Clientes: satisfação, retenção, NPS, aquisição, valor percebido, churn
3. Processos: eficiência, qualidade, ciclos, automação, inovação, produtividade
4. Aprendizado: capacitação, cultura, engajamento, sistemas, tecnologia

FORMATO SMART:
- Específico: objetivo claro e bem definido
- Mensurável: com indicador quantitativo quando possível (%, R$, tempo)
- Alcançável: realista considerando porte e setor
- Relevante: alinhado aos desafios identificados
- Temporal: horizonte de tempo claro (ex: 12 meses, fim do ano, 6 meses)

INSTRUÇÕES:
- Defina 3-5 objetivos estratégicos SMART
- Cada objetivo deve mencionar a perspectiva BSC (Financeira, Clientes, Processos, Aprendizado)
- Objetivos devem RESPONDER aos desafios identificados
- Prefira objetivos quantitativos (%, R$, redução de X%)
- Balance entre as 4 perspectivas (ao menos 2 perspectivas representadas)

EXEMPLO:
Desafios: [perda de clientes, equipe sobrecarregada, falta capital, processos manuais]
Saída:
[
  "Aumentar receita recorrente em 30% em 12 meses (Financeira)",
  "Reduzir churn de clientes de 15% para 5% até fim do ano (Clientes)",
  "Automatizar 50% dos processos manuais em 6 meses (Processos)",
  "Contratar e capacitar 5 novos colaboradores no próximo trimestre (Aprendizado)",
  "Melhorar NPS de 50 para 75 em 12 meses (Clientes)"
]

LEMBRE-SE: 3-5 objetivos SMART, balanceados entre perspectivas BSC."""

DEFINE_OBJECTIVES_USER = """Baseado nos desafios abaixo, defina objetivos estratégicos SMART alinhados às 4 perspectivas BSC.

DESAFIOS IDENTIFICADOS:
{challenges}

CONVERSA ORIGINAL:
{conversation}

Defina 3-5 objetivos SMART (Específico, Mensurável, Alcançável, Relevante, Temporal).
Mencione a perspectiva BSC de cada objetivo: (Financeira), (Clientes), (Processos) ou (Aprendizado)."""

