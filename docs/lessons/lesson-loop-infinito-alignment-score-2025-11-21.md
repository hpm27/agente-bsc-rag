# Lição Aprendida: Loop Infinito no Workflow BSC (Alignment Score)

**Data:** 2025-11-21
**Sessão:** Debugging de Loop Infinito
**Componente:** src/graph/workflow.py
**Severidade:** CRÍTICA
**Tempo de Resolução:** 45 minutos

## Problema Identificado

### Sintoma
Sistema entrava em loop infinito ao criar Strategy Map com score de alinhamento < 80:
1. Strategy Map criado com score=75.0
2. Sistema roteia para `approval`
3. `approval_handler` detecta status já como `approved`
4. Roteia de volta para `design_solution`
5. Strategy Map criado novamente (score continua 75.0)
6. **LOOP INFINITO** ♾️

### Logs Observados
```
13:16:20 - Strategy Map criado: score=75.0, warnings=38
13:16:20 - [ROUTING] alignment_score=75.0 < 80 → approval
13:16:20 - [APPROVAL] Status: approved → design_solution
13:16:20 - [SOLUTION_DESIGN] Handler iniciado NOVAMENTE
# Loop continua indefinidamente...
```

## Root Cause Analysis

### Código Original (PROBLEMA)
```python
def route_by_alignment_score(self, state: BSCState):
    score = state.alignment_report.score
    threshold = 80

    if score < threshold:
        return "approval"  # Sempre volta para approval
    else:
        return "implementation"
```

### Problema Conceitual
- Não havia controle de quantas vezes o Strategy Map foi tentado
- Sistema permitia loops infinitos de approval → design_solution
- Score provavelmente não muda significativamente entre iterações

## Solução Implementada

### 1. Adicionar Contador de Retry

**Em `design_solution_handler`:**
```python
# Incrementar contador no início
retry_count = state.metadata.get("design_solution_retry_count", 0) + 1
if retry_count > 1:
    logger.warning(f"[WARN] Retry #{retry_count} de design_solution")

# Adicionar ao metadata no return
return {
    "metadata": {
        **state.metadata,
        "design_solution_retry_count": retry_count,
    }
}
```

### 2. Verificar Contador no Roteamento

**Em `route_by_alignment_score`:**
```python
def route_by_alignment_score(self, state: BSCState):
    score = state.alignment_report.score
    threshold = 80
    retry_count = state.metadata.get("design_solution_retry_count", 0)

    if score >= threshold:
        return "implementation"
    else:
        if retry_count >= 1:
            # Já tentou uma vez, forçar implementation
            next_node = "implementation"
            logger.warning(
                f"[WARN] score={score} < {threshold}, mas "
                f"retry_count={retry_count} >= 1. Forçando -> {next_node}"
            )
        else:
            # Primeira tentativa, permitir approval manual
            next_node = "approval"
            logger.info(f"[INFO] Primeira tentativa -> {next_node}")

        return next_node
```

### 3. Reset do Contador

**Em `discovery_handler`:**
```python
# Reset quando voltamos para discovery (novo ciclo)
if state.metadata.get("design_solution_retry_count", 0) > 0:
    result["metadata"]["design_solution_retry_count"] = 0
```

## Testes de Validação

### Script de Teste: `scripts/test_loop_fix.py`

Testa 5 cenários:
1. Score < 80, primeira tentativa → approval ✅
2. Score < 80, segunda tentativa → implementation ✅
3. Score < 80, terceira+ tentativa → implementation ✅
4. Score >= 80 → implementation ✅
5. Sem alignment_report → discovery ✅

### Resultado
```
[SUCCESS] TODOS OS TESTES PASSARAM!
Loop infinito RESOLVIDO com sucesso.
```

## Métricas de Impacto

| Métrica | Antes | Depois |
|---------|-------|---------|
| Loop infinito | SIM | NÃO |
| Max tentativas | ∞ | 1 retry |
| Tempo médio workflow | ∞ (travado) | Normal |
| CPU usage | 100% (loop) | Normal |

## Lições Aprendidas

### 1. **Sempre Implementar Limites em Loops**
- Qualquer roteamento condicional precisa de limite de tentativas
- Usar contadores no metadata do state para rastrear iterações

### 2. **Testar Edge Cases de Roteamento**
- Testar scores limítrofes (75, 79, 80, 81)
- Testar múltiplas iterações do mesmo flow
- Verificar que não há loops infinitos

### 3. **Logging Detalhado em Roteamento**
- Adicionar logs com retry_count
- Logar decisões de roteamento com contexto
- Facilita debugging de loops

### 4. **Pattern de Prevenção de Loop**
```python
# Pattern genérico reutilizável
retry_count = state.metadata.get(f"{node_name}_retry_count", 0)
if retry_count >= MAX_RETRIES:
    # Forçar saída do loop
    return fallback_node
else:
    # Permitir retry
    return retry_node
```

## Recomendações Futuras

1. **Adicionar Métricas de Monitoramento**
   - Alertar se algum handler executar >2 vezes
   - Dashboard com retry_counts

2. **Configurar MAX_RETRIES Global**
   - Criar setting MAX_DESIGN_SOLUTION_RETRIES=1
   - Permitir ajuste sem alterar código

3. **Implementar Circuit Breaker**
   - Se muitos loops detectados, pausar workflow
   - Notificar administrador

## Código de Referência

- **Arquivo:** `src/graph/workflow.py`
- **Linhas modificadas:**
  - 903-912 (incrementar retry_count)
  - 750-773 (verificar retry_count)
  - 1544-1549 (reset retry_count)
- **Teste:** `scripts/test_loop_fix.py`

## Status

✅ **RESOLVIDO E TESTADO**

Loop infinito eliminado com sucesso. Sistema agora permite máximo 1 retry via approval manual antes de forçar continuation para implementation.

## Keywords

`loop-infinito`, `workflow`, `alignment-score`, `retry-count`, `langgraph`, `routing`, `approval`, `strategy-map`
