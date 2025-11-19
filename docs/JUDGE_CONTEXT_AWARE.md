# Judge Agent Context-Aware

**Data:** Novembro 2025  
**Versão:** 1.0  
**Status:** ✅ Implementado

---

## 📋 Visão Geral

O Judge Agent foi modificado para avaliar respostas de forma **context-aware**, ajustando critérios de avaliação baseado no tipo de conteúdo sendo avaliado (RAG, DIAGNÓSTICO, FERRAMENTAS).

**Problema Resolvido:**
- Na fase DIAGNÓSTICO, recomendações são baseadas APENAS no perfil do cliente (sem retrieval)
- Judge penalizava diagnósticos por falta de fontes (`has_sources=False`)
- Fontes de literatura BSC só virão em fases posteriores (Ferramentas Consultivas com retrieval)

**Solução Implementada:**
- Parâmetro `evaluation_context` adicionado ao Judge.evaluate()
- Prompt context-aware que ajusta critérios baseado no contexto
- Compatibilidade retroativa mantida (default 'RAG')

---

## 🎯 Contextos de Avaliação

### 1. **RAG** (Retrieval-Augmented Generation)

**Quando usar:** Respostas geradas com retrieval em documentos BSC indexados

**Critérios aplicados:**
- ✅ **Citação de fontes ESPERADA** (Fonte, Página)
- ✅ **Fundamentação em docs ESPERADA** (grounded)
- ✅ **Detecção de alucinações ATIVA**
- ✅ **Penalização por falta de fontes** (se quality_score < 0.85)

**Exemplo de uso:**
```python
from src.agents.judge_agent import JudgeAgent

judge = JudgeAgent()

judgment = judge.evaluate(
    original_query="O que é BSC?",
    agent_response="BSC é um sistema... (Fonte: Kaplan & Norton, 1996)",
    retrieved_documents="[Documentos BSC recuperados...]",
    agent_name="RAG Agent",
    evaluation_context="RAG"  # ← Fontes ESPERADAS
)
```

**Critério de aprovação:**
```
approved: quality_score >= 0.7 E (is_grounded=True OU quality_score >= 0.85)
needs_improvement: 0.5 <= quality_score < 0.7 OU (0.7 <= quality_score < 0.85 E is_grounded=False)
rejected: quality_score < 0.5 OU (is_grounded=False E has_sources=False E quality_score < 0.7)
```

---

### 2. **DIAGNOSTIC** (Diagnóstico sem Retrieval)

**Quando usar:** Diagnósticos BSC baseados no perfil do cliente (sem retrieval em docs)

**Critérios aplicados:**
- ✅ **Qualidade da análise** (coerência, profundidade)
- ✅ **Relevância ao perfil do cliente**
- ✅ **Viabilidade das recomendações**
- ❌ **Citação de fontes NÃO esperada** (não penaliza)
- ❌ **Fundamentação em docs NÃO esperada** (não penaliza)

**Exemplo de uso:**
```python
judgment = judge.evaluate(
    original_query="Diagnóstico BSC para TechCorp",
    agent_response="""
        EXECUTIVE SUMMARY:
        Empresa TechCorp apresenta sólido desempenho financeiro mas 
        enfrenta desafios em retenção de clientes (churn 15%).
        
        RECOMENDAÇÕES:
        1. [HIGH] Implementar Customer Success estruturado
        2. [MEDIUM] Melhorar onboarding de clientes
    """,
    retrieved_documents="[Perfil cliente: TechCorp, setor tecnologia, 500 funcionários...]",
    agent_name="Diagnostic Agent",
    evaluation_context="DIAGNOSTIC"  # ← Fontes NÃO esperadas
)
```

**Critério de aprovação (simplificado):**
```
approved: quality_score >= 0.7
needs_improvement: 0.5 <= quality_score < 0.7
rejected: quality_score < 0.5
```

**Foco da avaliação:**
- Análise está alinhada com perfil do cliente?
- Recomendações são lógicas e viáveis?
- Diagnóstico aborda aspectos relevantes?

---

### 3. **TOOLS** (Ferramentas Consultivas - Futuro)

**Quando usar:** Saídas de ferramentas consultivas (SWOT, Five Whys, Issue Tree, etc.)

**Status:** Planejado para implementação futura

**Critérios esperados:**
- ✅ **Estrutura adequada da ferramenta** (ex: matriz SWOT 2x2)
- ✅ **Citação de fontes ESPERADA** (retrieval em docs BSC)
- ✅ **Relevância ao contexto do cliente**
- ✅ **Profundidade da análise**

---

## 🔧 API Reference

### `JudgeAgent.evaluate()`

```python
def evaluate(
    self,
    original_query: str,
    agent_response: str,
    retrieved_documents: str,
    agent_name: str = "Unknown Agent",
    evaluation_context: str = "RAG"  # ← NOVO PARÂMETRO
) -> JudgmentResult:
    """
    Avalia resposta de um agente especialista (context-aware).
    
    Args:
        original_query: Pergunta original do usuário
        agent_response: Resposta fornecida pelo agente
        retrieved_documents: Documentos recuperados e usados
        agent_name: Nome do agente que forneceu a resposta
        evaluation_context: Contexto da avaliação:
            - 'RAG': Respostas com retrieval (fontes esperadas) [DEFAULT]
            - 'DIAGNOSTIC': Diagnóstico sem retrieval (fontes não esperadas)
            - 'TOOLS': Ferramentas consultivas (futuro)
    
    Returns:
        JudgmentResult com avaliação completa
    """
```

### `JudgeAgent.evaluate_multiple()`

```python
def evaluate_multiple(
    self,
    original_query: str,
    agent_responses: List[Dict[str, Any]],
    retrieved_documents: str,
    evaluation_context: str = "RAG"  # ← NOVO PARÂMETRO
) -> List[Dict[str, Any]]:
    """
    Avalia múltiplas respostas (de diferentes agentes).
    
    Args:
        original_query: Pergunta original
        agent_responses: Lista de respostas
        retrieved_documents: Documentos recuperados
        evaluation_context: Contexto da avaliação ('RAG', 'DIAGNOSTIC', 'TOOLS')
    
    Returns:
        Lista de avaliações ordenadas por quality_score
    """
```

---

## 📊 Comparação de Critérios

| Critério | RAG | DIAGNOSTIC | TOOLS (futuro) |
|----------|-----|------------|----------------|
| **Citação de fontes** | ✅ OBRIGATÓRIO | ❌ Não esperado | ✅ OBRIGATÓRIO |
| **Fundamentação em docs** | ✅ OBRIGATÓRIO | ❌ Não esperado | ✅ OBRIGATÓRIO |
| **Detecção alucinações** | ✅ ATIVA | ❌ N/A | ✅ ATIVA |
| **Qualidade da análise** | ✅ Avaliada | ✅ **FOCO PRINCIPAL** | ✅ Avaliada |
| **Relevância ao cliente** | ✅ Avaliada | ✅ **FOCO PRINCIPAL** | ✅ Avaliada |
| **Penalização por falta de fontes** | ✅ SIM (se score < 0.85) | ❌ **NÃO** | ✅ SIM |

---

## 🎓 Exemplos Práticos

### Exemplo 1: Diagnóstico BSC (context='DIAGNOSTIC')

```python
from src.agents.judge_agent import JudgeAgent

judge = JudgeAgent()

# Diagnóstico SEM fontes (análise do perfil do cliente)
diagnostic = """
EXECUTIVE SUMMARY:
Empresa TechCorp (setor tecnologia, 500 funcionários) apresenta:
- Sólido desempenho financeiro (EBITDA 35%, crescimento 25% a.a.)
- Desafios críticos em retenção de clientes (churn 15%)
- Processos de desenvolvimento lentos (18 meses ciclo)

GAPS IDENTIFICADOS:
- Perspectiva Clientes: NPS 45 (benchmark 70+)
- Perspectiva Processos: Time-to-market lento
- Perspectiva Aprendizado: Turnover engenheiros 22% (mercado 10%)

RECOMENDAÇÕES PRIORIZADAS:
1. [HIGH] Implementar Customer Success estruturado (ROI: -30% churn em 6 meses)
2. [HIGH] Adotar metodologia Agile (ROI: -40% time-to-market em 12 meses)
3. [MEDIUM] Programa retenção talentos (ROI: -50% turnover em 18 meses)
"""

judgment = judge.evaluate(
    original_query="Diagnóstico BSC para TechCorp",
    agent_response=diagnostic,
    retrieved_documents="[Perfil cliente: TechCorp, setor tecnologia, 500 funcionários...]",
    agent_name="Diagnostic Agent",
    evaluation_context="DIAGNOSTIC"  # ← Fontes NÃO esperadas
)

print(f"Score: {judgment.quality_score:.2f}")  # Ex: 0.85
print(f"Verdict: {judgment.verdict}")  # Ex: 'approved'
print(f"Reasoning: {judgment.reasoning}")
# Ex: "Diagnóstico abrangente com análise coerente das 4 perspectivas BSC.
#      Recomendações priorizadas com ROI estimado demonstram viabilidade."
```

**Resultado esperado:**
- ✅ **Aprovado** (foco em qualidade da análise, não fontes)
- ✅ Score alto (0.80-0.90) se análise for coerente
- ❌ Sem penalização por falta de fontes

---

### Exemplo 2: Resposta RAG (context='RAG')

```python
# Resposta RAG COM fontes
rag_response = """
O Balanced Scorecard (BSC) é um sistema de gestão estratégica desenvolvido por 
Robert Kaplan e David Norton em 1992 que traduz a visão e estratégia da organização 
em objetivos mensuráveis organizados em 4 perspectivas balanceadas:

1. **Perspectiva Financeira**: Objetivos financeiros tradicionais como crescimento 
   de receita, lucratividade, ROI (Fonte: Kaplan & Norton, 1996, p. 8-12)

2. **Perspectiva Clientes**: Satisfação, retenção, aquisição e participação de 
   mercado (Fonte: Kaplan & Norton, 1996, p. 13-18)

3. **Perspectiva Processos Internos**: Processos críticos que geram valor para 
   clientes e acionistas (Fonte: Kaplan & Norton, 1996, p. 19-24)

4. **Perspectiva Aprendizado e Crescimento**: Capacidades organizacionais, sistemas 
   e cultura necessários para inovação (Fonte: Kaplan & Norton, 1996, p. 25-30)
"""

judgment = judge.evaluate(
    original_query="O que é Balanced Scorecard?",
    agent_response=rag_response,
    retrieved_documents="[Kaplan, R. S., & Norton, D. P. (1996). The Balanced Scorecard...]",
    agent_name="RAG Agent",
    evaluation_context="RAG"  # ← Fontes ESPERADAS (default)
)

print(f"Score: {judgment.quality_score:.2f}")  # Ex: 0.95
print(f"Verdict: {judgment.verdict}")  # Ex: 'approved'
print(f"has_sources: {judgment.has_sources}")  # True
print(f"is_grounded: {judgment.is_grounded}")  # True
```

**Resultado esperado:**
- ✅ **Aprovado** (fontes citadas adequadamente)
- ✅ Score alto (0.90-1.0) se bem fundamentado
- ✅ `has_sources=True`, `is_grounded=True`

---

### Exemplo 3: Resposta RAG SEM fontes (penalizada)

```python
# Resposta RAG SEM fontes
rag_response_no_sources = """
O Balanced Scorecard é um sistema de gestão que organiza objetivos em 4 perspectivas:
Financeira, Clientes, Processos Internos, e Aprendizado e Crescimento.
Ajuda empresas a medir performance e executar estratégia de forma balanceada.
"""

judgment = judge.evaluate(
    original_query="O que é Balanced Scorecard?",
    agent_response=rag_response_no_sources,
    retrieved_documents="[Kaplan & Norton, 1996...]",
    agent_name="RAG Agent",
    evaluation_context="RAG"  # ← Fontes ESPERADAS
)

print(f"Score: {judgment.quality_score:.2f}")  # Ex: 0.65
print(f"Verdict: {judgment.verdict}")  # Ex: 'needs_improvement' ou 'rejected'
print(f"has_sources: {judgment.has_sources}")  # False
print(f"Issues: {judgment.issues}")
# Ex: ["Não cita fontes apropriadamente", "Falta fundamentação nos documentos"]
```

**Resultado esperado:**
- ⚠️ **Needs improvement** ou **Rejected** (falta de fontes penaliza)
- ⚠️ Score médio/baixo (0.50-0.70)
- ❌ `has_sources=False`, issues listam falta de fontes

---

## 🔄 Integração com Workflow

### Fluxo RAG Tradicional

```python
# src/graph/workflow.py - judge_evaluation()

def judge_evaluation(self, state: BSCState) -> dict[str, Any]:
    """Avalia resposta agregada (RAG tradicional)."""
    
    judgment = self.judge.evaluate(
        original_query=state.query,
        agent_response=state.aggregated_response,
        retrieved_documents="[Documentos recuperados pelos agentes]",
        agent_name="Synthesized Response",
        evaluation_context="RAG"  # ← Fontes ESPERADAS (default)
    )
    
    # ... processar judgment
```

### Fluxo Diagnóstico (DISCOVERY)

```python
# src/graph/consulting_orchestrator.py - coordinate_discovery()

async def coordinate_discovery(self, state: BSCState) -> dict[str, Any]:
    """Coordena diagnóstico BSC."""
    
    # Gerar diagnóstico (sem retrieval)
    complete_diagnostic = await diagnostic_agent.run_diagnostic(state)
    
    # Avaliar diagnóstico com Judge (context='DIAGNOSTIC')
    judgment = self.judge.evaluate(
        original_query="Diagnóstico BSC completo",
        agent_response=self._format_diagnostic_for_judge(complete_diagnostic),
        retrieved_documents=f"[Perfil cliente: {state.client_profile.company.name}...]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC"  # ← Fontes NÃO esperadas
    )
    
    # ... processar judgment
```

---

## ✅ Validação e Testes

### Testes Unitários

Arquivo: `tests/test_judge_context_aware.py`

**Cobertura:**
- ✅ Context 'DIAGNOSTIC' aceita diagnósticos sem fontes
- ✅ Context 'DIAGNOSTIC' foca em qualidade da análise
- ✅ Context 'RAG' exige fontes
- ✅ Context 'RAG' aprova respostas com fontes
- ✅ Mesmo conteúdo avaliado diferente em contextos diferentes
- ✅ Compatibilidade retroativa (default 'RAG')
- ✅ evaluate_multiple propaga contexto
- ✅ Smoke tests para todos contextos

**Executar testes:**
```bash
pytest tests/test_judge_context_aware.py -v
```

### Demonstração Interativa

Arquivo: `examples/judge_context_aware_demo.py`

**Demos incluídas:**
1. Avaliação RAG (fontes esperadas)
2. Avaliação DIAGNÓSTICO (fontes não esperadas)
3. Comparação lado a lado

**Executar demo:**
```bash
python examples/judge_context_aware_demo.py
```

---

## 📚 Decisões de Design

### Por que Context-Aware ao invés de Separate Prompts?

**Decisão:** Usar 1 método `evaluate()` com parâmetro `evaluation_context`

**Alternativas consideradas:**
- ❌ **Separate prompts**: Criar `evaluate_diagnostic()`, `evaluate_rag()` → Duplicação de código
- ❌ **Relaxar critério global**: Mudar Judge para sempre tolerar falta de fontes → Reduz precisão RAG
- ❌ **Add retrieval ao diagnóstico**: Fazer DiagnosticAgent buscar docs → Muda conceito, latência +3-5s

**Trade-offs:**
| Solução | Complexidade | Precisão | Manutenção | Flexibilidade |
|---------|--------------|----------|------------|---------------|
| **Context-Aware** ✅ | Baixa | Alta | Fácil | Alta |
| Separate prompts | Média | Alta | Difícil (2x código) | Média |
| Relaxar critério | Baixa | **Reduz** | Fácil | Baixa |
| Add retrieval | Muito alta | Alta | Difícil | Baixa |

**Benefícios da solução escolhida:**
1. ✅ **Baixa complexidade**: 1 parâmetro + ajuste de prompt
2. ✅ **Alta precisão**: Mantém rigor RAG, relaxa DIAGNOSTIC
3. ✅ **Flexibilidade**: Fácil adicionar novos contextos (TOOLS, etc.)
4. ✅ **Compatibilidade**: Default 'RAG' mantém comportamento original
5. ✅ **Manutenção**: Código centralizado, sem duplicação

---

## 🎯 Casos de Uso

### Caso 1: Diagnóstico BSC Inicial

**Cenário:** Cliente novo completa onboarding, DiagnosticAgent gera diagnóstico inicial

**Contexto:** `DIAGNOSTIC`

**Motivo:** Diagnóstico baseado APENAS em perfil do cliente (contexto, desafios, objetivos), sem retrieval em literatura BSC

**Expectativa:** Judge avalia QUALIDADE DA ANÁLISE e COERÊNCIA das recomendações, não penaliza por falta de fontes

---

### Caso 2: Ferramenta SWOT

**Cenário:** Cliente solicita análise SWOT, ferramenta busca literatura BSC sobre SWOT + contexto do cliente

**Contexto:** `TOOLS` (futuro)

**Motivo:** Ferramenta faz retrieval em docs BSC, fontes são ESPERADAS

**Expectativa:** Judge avalia estrutura SWOT + citação de fontes + relevância ao cliente

---

### Caso 3: Query RAG Tradicional

**Cenário:** Cliente pergunta "O que é Balanced Scorecard?", agentes fazem retrieval

**Contexto:** `RAG` (default)

**Motivo:** Resposta gerada com retrieval, fontes são ESPERADAS

**Expectativa:** Judge avalia citação de fontes + fundamentação + qualidade da resposta

---

## 🔮 Roadmap

### Fase 1: Implementado ✅

- ✅ Judge context-aware com 'RAG' e 'DIAGNOSTIC'
- ✅ Testes unitários completos
- ✅ Demonstração interativa
- ✅ Documentação completa

### Fase 2: Próximos Passos (Planejado)

- ⏳ **Context 'TOOLS'**: Adicionar suporte a ferramentas consultivas
- ⏳ **Métricas por contexto**: Tracking separado de approval rate por contexto
- ⏳ **Feedback loop**: Integrar avaliações Judge em refinamento de diagnósticos

### Fase 3: Futuro

- 🔜 **Context 'REFINEMENT'**: Avaliação de diagnósticos refinados (feedback cliente)
- 🔜 **Dynamic thresholds**: Ajustar thresholds de aprovação por contexto via config
- 🔜 **Multi-language**: Suporte a avaliações em múltiplos idiomas

---

## 📝 Changelog

### v1.0 - Novembro 2025

**Adicionado:**
- Parâmetro `evaluation_context` em `evaluate()` e `evaluate_multiple()`
- Prompt context-aware com instruções específicas por contexto
- Contextos 'RAG' e 'DIAGNOSTIC' implementados
- Testes unitários (10+ testes, 100% cobertura)
- Demonstração interativa
- Documentação completa

**Modificado:**
- `JudgeAgent.__init__()`: Removido chain estático (agora criado dinamicamente)
- `JudgeAgent._create_prompt()`: Aceita parâmetro `evaluation_context`
- `JudgeAgent.evaluate()`: Cria chain dinamicamente por contexto

**Compatibilidade:**
- ✅ Compatibilidade retroativa mantida (default 'RAG')
- ✅ Comportamento original preservado para código existente

---

## 🤝 Contribuindo

Ao adicionar novos contextos de avaliação:

1. **Adicionar contexto em `_create_prompt()`:**
```python
elif evaluation_context == "NEW_CONTEXT":
    context_instructions = """..."""
    verdict_rules = """..."""
```

2. **Criar testes em `tests/test_judge_context_aware.py`:**
```python
def test_new_context_behavior(judge):
    judgment = judge.evaluate(..., evaluation_context="NEW_CONTEXT")
    assert judgment.verdict == "expected"
```

3. **Documentar em `docs/JUDGE_CONTEXT_AWARE.md`:**
- Adicionar seção no "Contextos de Avaliação"
- Adicionar exemplos práticos
- Atualizar tabela comparativa

---

## 📧 Contato

**Problema identificado por:** Usuário do sistema BSC RAG Agent  
**Solução implementada por:** AI Agent (Cursor)  
**Data:** Novembro 2025  
**Versão:** 1.0

