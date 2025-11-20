# FASE 4.6 - Refinement Logic: Design Técnico

**Data:** 2025-11-19
**Versão:** 1.0
**Status:** [EMOJI] Em Design
**Fase:** 4.6 - Refinement Logic

---

## [EMOJI] EXECUTIVE SUMMARY

### Objetivo

Implementar lógica de refinamento de diagnóstico baseada em feedback do usuário. Quando um diagnóstico é rejeitado ou modificado (approval_status REJECTED ou MODIFIED), o sistema deve usar o `approval_feedback` para refinar o diagnóstico existente ao invés de recriar do zero.

### Contexto

- **FASE 4.5**: Sistema de feedback collection implementado [OK]
- **Workflow atual**: REJECTED/MODIFIED -> DISCOVERY (refaz diagnóstico completo)
- **Problema**: Refazer diagnóstico completo é ineficiente quando apenas ajustes são necessários
- **Solução**: Refinement logic que melhora diagnóstico existente baseado em feedback específico

### Benefícios Esperados

- **Eficiência**: 50-70% mais rápido que refazer diagnóstico completo
- **Qualidade**: Mantém insights válidos do diagnóstico original
- **Satisfação**: Usuário vê melhorias incrementais baseadas em seu feedback específico
- **Custo**: Reduz chamadas LLM desnecessárias (refina apenas o necessário)

---

## [EMOJI] ARQUITETURA

### Fluxo de Refinement

```
┌─────────────────────────────────────────────────────────────┐
│  APPROVAL_PENDING (approval_status = REJECTED/MODIFIED)     │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  approval_feedback: "SWOT precisa mais Opportunities        │
│  relacionadas ao mercado enterprise"                        │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  DISCOVERY Handler detecta: diagnostic exists +             │
│  approval_status REJECTED/MODIFIED                          │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  DiagnosticAgent.refine_diagnostic(                         │
│    diagnostic=existing_diagnostic,                          │
│    feedback=approval_feedback                                │
│  )                                                          │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM analisa feedback e identifica:                        │
│  - O que precisa ser melhorado                             │
│  - Quais perspectivas afetadas                              │
│  - Como refinar mantendo insights válidos                  │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Refinement Strategy:                                       │
│  1. Targeted refinement (apenas perspectivas afetadas)      │
│  2. Full refinement (se feedback muito amplo)                │
│  3. Recommendations-only (se feedback sobre recomendações) │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  CompleteDiagnostic refinado retornado                      │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  APPROVAL_PENDING (novo diagnóstico refinado)               │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principais

1. **DiagnosticAgent.refine_diagnostic()**
   - Método principal de refinement
   - Recebe: `CompleteDiagnostic` existente + `approval_feedback`
   - Retorna: `CompleteDiagnostic` refinado

2. **Refinement Prompt**
   - Prompt estruturado para LLM analisar feedback
   - Identifica áreas de melhoria específicas
   - Gera estratégia de refinement

3. **Refinement Strategies**
   - **Targeted**: Refina apenas perspectivas/recomendações específicas
   - **Full**: Refaz diagnóstico completo (fallback se feedback muito amplo)
   - **Recommendations-only**: Refina apenas recomendações

4. **Workflow Integration**
   - `discovery_handler` detecta refinement necessário
   - Chama `refine_diagnostic()` ao invés de `run_diagnostic()`

---

## [EMOJI] IMPLEMENTAÇÃO

### Etapa 1: Prompt de Refinement

**Arquivo:** `src/prompts/diagnostic_prompts.py`

```python
REFINE_DIAGNOSTIC_PROMPT = """Você é um consultor BSC especializado em refinar diagnósticos baseado em feedback específico.

Você receberá:
1. Um diagnóstico BSC completo existente (CompleteDiagnostic)
2. Feedback do usuário sobre o que precisa ser melhorado

Sua tarefa:
1. Analisar o feedback e identificar áreas específicas de melhoria
2. Decidir estratégia de refinement:
   - TARGETED: Refinar apenas perspectivas/recomendações específicas mencionadas no feedback
   - FULL: Refazer diagnóstico completo (se feedback muito amplo ou genérico)
   - RECOMMENDATIONS_ONLY: Refinar apenas recomendações (se feedback foca em ações)
3. Gerar diagnóstico refinado mantendo insights válidos do original

Feedback do usuário:
{feedback}

Diagnóstico existente:
{diagnostic_json}

Estratégia escolhida: [TARGETED|FULL|RECOMMENDATIONS_ONLY]

Diagnóstico refinado (JSON completo seguindo schema CompleteDiagnostic):
"""
```

### Etapa 2: Método refine_diagnostic()

**Arquivo:** `src/agents/diagnostic_agent.py`

```python
async def refine_diagnostic(
    self,
    existing_diagnostic: CompleteDiagnostic,
    feedback: str,
    state: BSCState,
) -> CompleteDiagnostic:
    """Refina diagnóstico existente baseado em feedback do usuário.

    Args:
        existing_diagnostic: Diagnóstico original a ser refinado
        feedback: Feedback textual do usuário sobre o que melhorar
        state: Estado atual com client_profile e contexto

    Returns:
        CompleteDiagnostic refinado

    Raises:
        ValueError: Se feedback vazio ou diagnóstico inválido

    Example:
        >>> diagnostic = await agent.run_diagnostic(state)
        >>> refined = await agent.refine_diagnostic(
        ...     diagnostic,
        ...     "SWOT precisa mais Opportunities relacionadas ao mercado enterprise",
        ...     state
        ... )
        >>> len(refined.recommendations) >= len(diagnostic.recommendations)
        True
    """
```

**Fluxo interno:**

1. **Validar inputs**
   - Feedback não vazio
   - Diagnóstico válido
   - State com client_profile

2. **Analisar feedback com LLM**
   - Usar prompt REFINE_DIAGNOSTIC_PROMPT
   - Identificar estratégia (TARGETED/FULL/RECOMMENDATIONS_ONLY)
   - Extrair áreas específicas de melhoria

3. **Executar refinement baseado em estratégia**
   - **TARGETED**: Refinar apenas perspectivas/recomendações específicas
   - **FULL**: Chamar `run_diagnostic()` novamente (fallback)
   - **RECOMMENDATIONS_ONLY**: Refinar apenas recomendações

4. **Validar diagnóstico refinado**
   - Schema válido (Pydantic validation)
   - Melhorias aplicadas conforme feedback
   - Insights válidos mantidos

5. **Retornar diagnóstico refinado**

### Etapa 3: Integração Workflow

**Arquivo:** `src/graph/workflow.py` (discovery_handler)

```python
def discovery_handler(self, state: BSCState) -> dict[str, Any]:
    """Handler de discovery com suporte a refinement."""

    # Detectar se refinement necessário
    needs_refinement = (
        state.diagnostic is not None and
        state.approval_status in (ApprovalStatus.REJECTED, ApprovalStatus.MODIFIED) and
        state.approval_feedback
    )

    if needs_refinement:
        # Refinement: melhorar diagnóstico existente
        logger.info("[DISCOVERY] Refinement necessário baseado em feedback")
        result = await self.consulting_orchestrator.coordinate_refinement(state)
    else:
        # Discovery normal: criar diagnóstico novo
        result = await self.consulting_orchestrator.coordinate_discovery(state)

    return result
```

**Arquivo:** `src/graph/consulting_orchestrator.py`

```python
async def coordinate_refinement(self, state: BSCState) -> dict[str, Any]:
    """Coordena refinement de diagnóstico baseado em feedback."""

    diagnostic_agent = self.diagnostic_agent
    existing_diagnostic = state.diagnostic
    feedback = state.approval_feedback or ""

    # Refinar diagnóstico
    refined_diagnostic = await diagnostic_agent.refine_diagnostic(
        existing_diagnostic=existing_diagnostic,
        feedback=feedback,
        state=state
    )

    return {
        "diagnostic": refined_diagnostic,
        "current_phase": ConsultingPhase.APPROVAL_PENDING,
        "metadata": {
            **state.metadata,
            "refinement_applied": True,
            "refinement_feedback": feedback
        }
    }
```

---

## [EMOJI] ESTRATÉGIAS DE REFINEMENT

### 1. Targeted Refinement (Preferencial)

**Quando usar:** Feedback específico sobre perspectivas ou recomendações individuais.

**Exemplo feedback:**
- "SWOT precisa mais Opportunities relacionadas ao mercado enterprise"
- "Recomendação sobre KPIs financeiros está muito genérica"
- "Perspectiva Clientes não menciona segmentação por persona"

**Implementação:**
- Identificar perspectiva/recomendação específica afetada
- Refinar apenas essa parte usando LLM
- Manter resto do diagnóstico intacto
- Re-consolidar executive_summary se necessário

**ROI:** 60-70% mais rápido que full refinement

---

### 2. Full Refinement (Fallback)

**Quando usar:** Feedback muito amplo ou genérico.

**Exemplo feedback:**
- "Diagnóstico não reflete realidade da empresa"
- "Preciso de análise mais profunda"
- "Não está alinhado com nossos objetivos"

**Implementação:**
- Chamar `run_diagnostic()` novamente
- Passar feedback como contexto adicional
- Usar feedback para guiar análise mais profunda

**ROI:** Mesmo tempo que discovery normal, mas com contexto melhor

---

### 3. Recommendations-Only Refinement

**Quando usar:** Feedback foca apenas em recomendações/ações.

**Exemplo feedback:**
- "Recomendações não são práticas o suficiente"
- "Faltam recomendações sobre implementação"
- "Priorização não está correta"

**Implementação:**
- Refinar apenas `recommendations` usando LLM
- Manter perspectivas intactas
- Re-priorizar baseado em feedback

**ROI:** 80-90% mais rápido que full refinement

---

## [EMOJI] MÉTRICAS DE SUCESSO

| Métrica | Target | Como Medir |
|---------|--------|------------|
| **Refinement Success Rate** | >= 85% | % refinements que geram diagnóstico melhorado |
| **Time Improvement** | 50-70% | Tempo refinement vs discovery completo |
| **User Satisfaction** | >= 4/5 | Rating após refinement |
| **Feedback Incorporation** | >= 80% | % feedbacks que resultam em melhorias visíveis |
| **LLM Calls Reduction** | 40-60% | Redução de chamadas LLM vs discovery completo |

---

## [EMOJI] TESTES

### Testes Unitários (8 testes)

1. `test_refine_diagnostic_targeted_refinement` - Refinement targeted funciona
2. `test_refine_diagnostic_full_refinement` - Refinement full funciona
3. `test_refine_diagnostic_recommendations_only` - Refinement recommendations-only funciona
4. `test_refine_diagnostic_validates_feedback` - Valida feedback vazio
5. `test_refine_diagnostic_validates_diagnostic` - Valida diagnóstico inválido
6. `test_refine_diagnostic_preserves_valid_insights` - Mantém insights válidos
7. `test_refine_diagnostic_improves_based_on_feedback` - Melhora baseado em feedback
8. `test_refine_diagnostic_handles_ambiguous_feedback` - Trata feedback ambíguo

### Testes E2E (4 testes)

1. `test_workflow_refinement_rejected` - Workflow refinement quando REJECTED
2. `test_workflow_refinement_modified` - Workflow refinement quando MODIFIED
3. `test_refinement_improves_diagnostic_quality` - Refinement melhora qualidade
4. `test_refinement_faster_than_discovery` - Refinement mais rápido que discovery

**Total:** 12 testes (8 unitários + 4 E2E)

---

## [EMOJI] REFERÊNCIAS

### Best Practices (2025)

1. **FRAME: Feedback-Refined Agent Methodology** (ACL 2025)
   - Padrão de refinement baseado em feedback estruturado
   - Iterative improvement loops

2. **LLMLOOP: Iterative Refinement Loops** (ICSME 2025)
   - Framework para refinement iterativo de outputs LLM
   - 5 tipos de loops de refinement

3. **Evaluation-Driven Development** (ArXiv 2025)
   - Incorporação de feedback loops em tempo real
   - Retrospective analysis e structured feedback

### Padrões Aplicados

- **Targeted Refinement**: Refinar apenas o necessário (eficiente)
- **Feedback Loop**: Incorporar feedback do usuário (qualidade)
- **Incremental Improvement**: Melhorar incrementalmente (satisfação)

---

## [EMOJI] PLANO DE IMPLEMENTAÇÃO

### Etapa 0: Design Técnico [OK] (Esta etapa)

- [x] Documento de design completo
- [x] Arquitetura definida
- [x] Estratégias de refinement mapeadas
- [x] Plano de implementação em 4 etapas

### Etapa 1: Prompt de Refinement

- [ ] Criar `REFINE_DIAGNOSTIC_PROMPT` em `diagnostic_prompts.py`
- [ ] Validar prompt com exemplos de feedback
- [ ] Documentar estratégias de refinement no prompt

**Estimativa:** 30-45 min

### Etapa 2: Método refine_diagnostic()

- [ ] Implementar `refine_diagnostic()` em `DiagnosticAgent`
- [ ] Implementar análise de feedback (LLM)
- [ ] Implementar estratégias de refinement (TARGETED/FULL/RECOMMENDATIONS_ONLY)
- [ ] Validação de diagnóstico refinado

**Estimativa:** 1-1.5h

### Etapa 3: Integração Workflow

- [ ] Modificar `discovery_handler` para detectar refinement necessário
- [ ] Criar `coordinate_refinement()` em `ConsultingOrchestrator`
- [ ] Integrar com workflow LangGraph
- [ ] Testar fluxo completo

**Estimativa:** 30-45 min

### Etapa 4: Testes

- [ ] Testes unitários (8 testes)
- [ ] Testes E2E (4 testes)
- [ ] Validação de métricas de sucesso

**Estimativa:** 1-1.5h

**Total Estimado:** 3-4h (1 sessão)

---

## [WARN] RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Refinement não melhora diagnóstico | Média | Alto | Fallback para full refinement se targeted falhar |
| Feedback ambíguo não processado | Média | Médio | Prompt estruturado com exemplos, fallback para full |
| Refinement mais lento que discovery | Baixa | Médio | Timeout e fallback para discovery normal |
| Insights válidos perdidos | Baixa | Alto | Validação explícita de preservação de insights |

---

**Última Atualização:** 2025-11-19
**Status:** [EMOJI] Design Completo - Pronto para Implementação
**Próximo:** Etapa 1 - Criar Prompt de Refinement
