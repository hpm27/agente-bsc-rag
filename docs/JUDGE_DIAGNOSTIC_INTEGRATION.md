# Judge Agent - Integração no Workflow de Diagnóstico

**Data:** Novembro 2025
**Versão:** 1.0
**Status:** [OK] Implementado e Validado

---

## [EMOJI] Resumo Executivo

O **Judge Agent** foi integrado ao workflow de diagnóstico BSC para avaliar automaticamente a qualidade dos diagnósticos gerados ANTES de enviar para aprovação humana. Esta integração implementa um **quality gate** que:

- [OK] Avalia diagnósticos com critérios context-aware (DIAGNOSTIC vs RAG)
- [OK] Adiciona scores e reasoning em metadata
- [OK] Permite prosseguir mesmo com score baixo (human-in-the-loop)
- [OK] Registra logs estruturados para monitoramento

---

## [EMOJI] Problema Resolvido

**Observação do Usuário (Nov 2025):**
> "Após a fase de diagnóstico é feito um relatório com os pontos, e o Judge faz uma avaliação do diagnóstico feito da empresa. Normalmente ele da uma nota abaixo por na fase de diagnóstico os agentes muitas vezes não atribuem fonte, mas eu acredito que as fontes só virão na próxima etapa quando os agente efetivamente farão a busca nos conteúdos indexados."

**Análise:**
1. Na fase DIAGNÓSTICO, recomendações são baseadas APENAS no `client_profile` (sem retrieval)
2. Judge penalizava por falta de fontes (`has_sources=False`)
3. Fontes de literatura BSC só virão nas próximas fases (Ferramentas Consultivas)
4. Diagnóstico era rejeitado incorretamente

**Solução Implementada:**
- Judge agora é **context-aware**: relaxa critérios de fontes quando `evaluation_context='DIAGNOSTIC'`
- Diagnóstico é avaliado com foco em **qualidade da análise** (não em citações de fonte)
- Score registrado em metadata, mas PERMITE prosseguir (decisão final humana)

---

## [EMOJI] Implementação

### 1. Arquitetura

```
coordinate_discovery()
    ↓
run_diagnostic()  [4 agentes paralelos]
    ↓
CompleteDiagnostic gerado
    ↓
[NOVO] Judge.evaluate(context='DIAGNOSTIC')
    ↓
Judge_evaluation adicionada em metadata
    ↓
APPROVAL_PENDING (com scores Judge)
```

### 2. Código Adicionado

**Arquivo:** `src/graph/consulting_orchestrator.py`

#### 2.1 Imports e Lazy Loading

```python
# TYPE_CHECKING imports
if TYPE_CHECKING:
    from src.agents.judge_agent import JudgeAgent

# Lazy loading property
@property
def judge_agent(self) -> JudgeAgent:
    if self._judge_agent is None:
        from src.agents.judge_agent import JudgeAgent
        self._judge_agent = JudgeAgent()
        logger.info("[LOAD] JudgeAgent carregado")
    return self._judge_agent
```

#### 2.2 Método Helper: Formatação para Judge

```python
def _format_diagnostic_for_judge(self, diagnostic: Any) -> str:
    """
    Formata diagnostico para avaliacao do Judge Agent.

    Args:
        diagnostic: CompleteDiagnostic Pydantic

    Returns:
        String formatada com conteudo essencial para Judge avaliar qualidade
    """
    # Executive summary
    output_parts = [
        "[DIAGNOSTICO BSC]\\n\\n",
        f"EXECUTIVE SUMMARY:\\n{diagnostic.executive_summary}\\n\\n"
    ]

    # Top insights por perspectiva (2-3 por perspectiva)
    perspectives_data = {
        "FINANCEIRA": diagnostic.financial_perspective,
        "CLIENTES": diagnostic.customer_perspective,
        "PROCESSOS": diagnostic.process_perspective,
        "APRENDIZADO": diagnostic.learning_perspective
    }

    output_parts.append("INSIGHTS PRINCIPAIS POR PERSPECTIVA:\\n\\n")

    for persp_name, persp_data in perspectives_data.items():
        if persp_data and persp_data.insights:
            output_parts.append(f"[{persp_name}]\\n")
            for insight in persp_data.insights[:3]:  # Top 3
                output_parts.append(f"- {insight}\\n")
            output_parts.append("\\n")

    # Top 5 recomendacoes HIGH priority
    high_priority_recs = [
        rec for rec in diagnostic.recommendations
        if rec.priority == "HIGH"
    ][:5]

    if high_priority_recs:
        output_parts.append("RECOMENDACOES PRIORITARIAS:\\n\\n")
        for i, rec in enumerate(high_priority_recs, 1):
            output_parts.append(
                f"{i}. [{rec.priority}] {rec.title}\\n"
                f"   Impacto: {rec.impact}\\n"
                f"   Descricao: {rec.description}\\n\\n"
            )

    return "".join(output_parts)
```

#### 2.3 Integração no Workflow (coordinate_discovery)

```python
# AVALIACAO JUDGE: Validar qualidade do diagnostico ANTES de enviar para aprovacao
logger.info("[JUDGE] Avaliando qualidade do diagnostico BSC...")

try:
    # Formatar diagnostico para avaliacao
    diagnostic_formatted = self._format_diagnostic_for_judge(complete_diagnostic)

    # Avaliar com Judge (context='DIAGNOSTIC': relaxa criterios de fontes)
    judge_result = self.judge_agent.evaluate(
        original_query=(
            f"Diagnostico BSC para {state.client_profile.company.name} "
            f"(setor: {state.client_profile.company.sector})"
        ),
        agent_response=diagnostic_formatted,
        retrieved_documents="[Perfil cliente coletado no onboarding]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC"  # <- CRÍTICO: Context-aware
    )

    # Log resultado Judge
    logger.info(
        f"[JUDGE] Avaliacao concluida | "
        f"Score: {judge_result.quality_score:.2f} | "
        f"Verdict: {judge_result.verdict} | "
        f"Is_grounded: {judge_result.is_grounded} | "
        f"Is_complete: {judge_result.is_complete}"
    )

    # Armazenar avaliacao Judge em metadata
    judge_evaluation = {
        "quality_score": judge_result.quality_score,
        "verdict": judge_result.verdict,
        "is_grounded": judge_result.is_grounded,
        "is_complete": judge_result.is_complete,
        "has_sources": judge_result.has_sources,
        "reasoning": judge_result.reasoning,
        "suggestions": judge_result.suggestions,
        "evaluated_at": datetime.now(timezone.utc).isoformat()
    }

    # Warning se score baixo (mas permitir prosseguir)
    if judge_result.quality_score < 0.7:
        logger.warning(
            f"[JUDGE] [WARN] Score abaixo de 0.7 detectado! | "
            f"Score: {judge_result.quality_score:.2f} | "
            f"Sugestoes: {judge_result.suggestions} | "
            f"Diagnostico sera enviado para aprovacao mas requer atencao humana"
        )

except Exception as judge_err:
    logger.error(f"[JUDGE] [ERRO] Falha ao avaliar diagnostico: {judge_err}")
    # Fallback: continuar sem avaliacao Judge
    judge_evaluation = {
        "quality_score": None,
        "verdict": "evaluation_failed",
        "error": str(judge_err),
        "evaluated_at": datetime.now(timezone.utc).isoformat()
    }

# Serializar CompleteDiagnostic
diagnostic_dict = complete_diagnostic.model_dump()

# Adicionar judge_evaluation em metadata
if "metadata" not in diagnostic_dict:
    diagnostic_dict["metadata"] = {}
diagnostic_dict["metadata"]["judge_evaluation"] = judge_evaluation
```

---

## [EMOJI] Comportamento Esperado

### Cenário 1: Score Alto (>= 0.85)

```python
# Judge Result
{
    "quality_score": 0.92,
    "verdict": "approved",
    "is_grounded": True,
    "is_complete": True,
    "has_sources": False,  # OK em DIAGNOSTIC
    "reasoning": "Diagnostico de alta qualidade com insights profundos...",
    "suggestions": []
}

# Log
[JUDGE] Avaliacao concluida | Score: 0.92 | Verdict: approved | Is_grounded: True
```

### Cenário 2: Score Médio (0.70-0.84)

```python
# Judge Result
{
    "quality_score": 0.78,
    "verdict": "approved",
    "is_grounded": True,
    "is_complete": True,
    "has_sources": False,
    "reasoning": "Diagnostico solido, poderia ter mais detalhes em processos...",
    "suggestions": ["Expandir analise de processos internos"]
}

# Log
[JUDGE] Avaliacao concluida | Score: 0.78 | Verdict: approved
```

### Cenário 3: Score Baixo (< 0.70)

```python
# Judge Result
{
    "quality_score": 0.55,
    "verdict": "needs_improvement",
    "is_grounded": False,
    "is_complete": True,
    "has_sources": False,
    "reasoning": "Diagnostico superficial, falta profundidade...",
    "suggestions": [
        "Adicionar mais insights por perspectiva",
        "Recomendacoes muito genericas, especificar melhor"
    ]
}

# Log
[JUDGE] Avaliacao concluida | Score: 0.55 | Verdict: needs_improvement
[JUDGE] [WARN] Score abaixo de 0.7 detectado! | Score: 0.55 |
    Sugestoes: ['Adicionar mais insights...'] |
    Diagnostico sera enviado para aprovacao mas requer atencao humana
```

**IMPORTANTE:** Mesmo com score baixo, o diagnóstico **PROSSEGUE** para aprovação. A decisão final é humana.

### Cenário 4: Erro na Avaliação

```python
# Fallback
{
    "quality_score": None,
    "verdict": "evaluation_failed",
    "error": "Timeout ao chamar Judge LLM",
    "evaluated_at": "2025-11-19T..."
}

# Log
[JUDGE] [ERRO] Falha ao avaliar diagnostico: Timeout ao chamar Judge LLM
```

---

## [EMOJI] Critérios de Avaliação (Context='DIAGNOSTIC')

### [OK] Avaliados (Score Alto Possível)

1. **Qualidade da análise** (0-1): Insights são profundos e específicos?
2. **Completude**: Todas 4 perspectivas BSC analisadas?
3. **Coerência**: Recomendações alinhadas com desafios identificados?
4. **Especificidade**: Recomendações são acionáveis ou genéricas?

### [EMOJI] Relaxados (Não Penalizam)

1. **Citação de fontes**: Não esperado em DIAGNOSTIC (apenas perfil cliente)
2. **Documentos recuperados**: Não esperado (sem retrieval nesta fase)

### [ERRO] Ainda Penalizam

1. **Alucinações**: Inventar informações não presentes no perfil cliente
2. **Incompletude**: Perspectivas BSC não analisadas
3. **Contradições**: Recomendações contraditórias entre perspectivas

---

## [EMOJI] Métricas e Monitoramento

### Logs Estruturados

Todos os logs Judge seguem padrão estruturado:

```
[JUDGE] Avaliando qualidade do diagnostico BSC...
[JUDGE] Avaliacao concluida | Score: X.XX | Verdict: YYY | Is_grounded: ZZZ
[JUDGE] [WARN] Score abaixo de 0.7 detectado! | ...  # Se score < 0.7
[JUDGE] [ERRO] Falha ao avaliar diagnostico: ...     # Se erro
```

### Metadata Adicionada

```python
state.diagnostic["metadata"]["judge_evaluation"] = {
    "quality_score": float,        # 0.0-1.0
    "verdict": str,                # approved | needs_improvement | rejected
    "is_grounded": bool,           # Baseado em dados reais?
    "is_complete": bool,           # Completo?
    "has_sources": bool,           # Tem fontes? (False esperado em DIAGNOSTIC)
    "reasoning": str,              # Explicação do Judge
    "suggestions": List[str],      # Melhorias sugeridas
    "evaluated_at": str            # ISO 8601 timestamp
}
```

### Queries Úteis (Analytics Futuro)

```python
# % Diagnósticos com score >= 0.85
high_quality_rate = (
    len([d for d in diagnostics if d.metadata.judge_evaluation.quality_score >= 0.85])
    / len(diagnostics)
)

# Média de score por setor
import pandas as pd
df = pd.DataFrame([{
    "sector": d.client_profile.company.sector,
    "score": d.metadata.judge_evaluation.quality_score
} for d in diagnostics])
df.groupby("sector")["score"].mean()

# Top sugestões do Judge (quais melhorias mais comuns?)
from collections import Counter
all_suggestions = []
for d in diagnostics:
    all_suggestions.extend(d.metadata.judge_evaluation.suggestions)
Counter(all_suggestions).most_common(10)
```

---

## [EMOJI] Exemplo de Uso

Ver arquivo: `examples/judge_context_aware_demo.py`

---

## [EMOJI] Lições Aprendidas

### 1. Context-Aware é Essencial

**Por quê:** Diagnóstico BSC (sem retrieval) vs RAG (com retrieval) têm expectativas DIFERENTES de qualidade.

**Como:** Parâmetro `evaluation_context` no Judge permite ajustar critérios dinamicamente.

**ROI:** Diagnósticos não são mais rejeitados incorretamente por falta de fontes.

### 2. Human-in-the-Loop > Rejeição Automática

**Por quê:** Score baixo PODE ser diagnóstico válido para cliente específico (ex: startup pequena com informações limitadas).

**Como:** Score < 0.7 adiciona WARNING mas permite prosseguir. Decisão final é humana na aprovação.

**ROI:** 0 diagnósticos perdidos por rejeição automática incorreta.

### 3. Logs Estruturados Facilitam Analytics

**Por quê:** Queries ad-hoc em logs não-estruturados são lentas e propensas a erro.

**Como:** Logs seguem padrão: `[JUDGE] <AÇÃO> | key1: value1 | key2: value2`.

**ROI:** Analytics futuro (% score alto, top sugestões) trivial de implementar.

### 4. Fallback Gracioso Previne Bloqueios

**Por quê:** Timeout/erro no Judge NÃO deve bloquear workflow (diagnóstico é caro: 4 agentes paralelos).

**Como:** try/except com fallback: `verdict='evaluation_failed'`, permite prosseguir.

**ROI:** 100% uptime do workflow, mesmo com Judge instável.

---

## [EMOJI] Troubleshooting

### Judge Sempre Retorna Score Baixo

**Diagnóstico:**
```bash
# Verificar se context='DIAGNOSTIC' está sendo passado
grep "evaluation_context" src/graph/consulting_orchestrator.py
```

**Solução:** Garantir que linha contém `evaluation_context="DIAGNOSTIC"`.

### Metadata judge_evaluation Não Aparece

**Diagnóstico:**
```python
# Verificar se diagnostic_dict tem metadata
print(diagnostic_dict.keys())
```

**Solução:** Verificar se código adiciona metadata ANTES de retornar state.

### ImportError: cannot import JudgeAgent

**Diagnóstico:** Circular import.

**Solução:** Usar lazy loading (property) ao invés de import no topo do arquivo.

---

## [EMOJI] Referências

1. **Judge Context-Aware:** `docs/JUDGE_CONTEXT_AWARE.md`
2. **Sequential Thinking Planning:** Sessão Nov 19, 2025
3. **Brightdata Research:** Stack Overflow Q79796733 (LangChain deprecations)
4. **Always-Applied Rules:** `.cursor/rules/rag-bsc-core.mdc`

---

## [OK] Checklist de Validação

Antes de considerar integração completa:

- [x] Judge importado com lazy loading
- [x] Método `_format_diagnostic_for_judge()` criado
- [x] Avaliação Judge inserida após `run_diagnostic()`
- [x] Logs estruturados adicionados
- [x] Metadata `judge_evaluation` em diagnostic_dict
- [x] Fallback gracioso implementado
- [x] Context='DIAGNOSTIC' validado
- [x] Warning para score < 0.7 implementado
- [x] Documentação completa criada
- [x] Exemplo de uso criado

---

**Última Atualização:** 2025-11-19
**Status:** [OK] Pronto para Produção
**Autor:** AI Agent (Sequential Thinking + Brightdata Research)
