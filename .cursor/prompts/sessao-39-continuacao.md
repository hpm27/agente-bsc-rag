# Prompt de Continuação - Sessão 39

**Data**: 2025-11-20
**Objetivo**: Continuar Sprint 2 (Strategy Map MVP) em novo chat

---

## VERSÃO COMPLETA (Recomendada)

```
# SESSÃO 39 - Sprint 2 Continuação: Node design_solution()

## [EMOJI] CONTEXTO
- **Projeto**: BSC RAG Agent (sistema consultivo multi-agente Balanced Scorecard)
- **Sessão Anterior**: 38/38 (Sprint 2 Parcial - 50% completo)
- **Sprint 2 Status**: 3/6 tarefas completas
  - [OK] 2.1 Schemas StrategyMap (17 testes passando)
  - [OK] 2.2 Strategy_Map_Designer_Tool (474 linhas, tool funcional, 2/10 testes)
  - [OK] 2.3 Alignment_Validator_Tool (574 linhas, 10/10 testes, 88% coverage)

## [EMOJI] TAREFA IMEDIATA
**2.4 Node design_solution() (4-6h)** - Integração LangGraph workflow
- Orquestrar StrategyMapDesignerTool + AlignmentValidatorTool
- Adicionar handler design_solution() em src/graph/workflow.py
- Expandir BSCState com campos: strategy_map, alignment_report
- Routing condicional: APPROVAL_PENDING -> SOLUTION_DESIGN -> IMPLEMENTATION (baseado em alignment score)

## [EMOJI] ARQUIVOS-CHAVE
Leia ANTES de implementar:
- @.cursor/progress/consulting-progress.md (Sessão 38 documentada, linhas 11-126)
- @docs/sprints/SPRINT_2_DESIGN.md (especificação técnica, seção 2.4 linhas 590-650)
- @src/tools/strategy_map_designer.py (API reference, método design_strategy_map)
- @src/tools/alignment_validator.py (API reference, método validate_strategy_map)
- @src/graph/workflow.py (handlers existentes como referência: discovery_handler linhas 856-920)

## [EMOJI] METODOLOGIA OBRIGATÓRIA
Seguir SUAS rules e memórias:
- **Sequential Thinking** ANTES de implementar (planejar 8-10 thoughts)
- **Brightdata research** se necessário (LangGraph patterns 2024-2025)
- **Checklist [[memory:9969868]]** 15 pontos (grep schemas ANTES de fixtures)
- **Pattern Sprint 1**: discovery_handler como template (coordenação + validação + routing)

## [OK] PRÓXIMOS PASSOS
1. Ler @SPRINT_2_DESIGN.md seção 2.4 (requisitos design_solution_handler completos)
2. Implementar design_solution_handler() em workflow.py (~150-200 linhas)
3. Expandir src/graph/states.py com strategy_map + alignment_report (BSCState)
4. Adicionar routing route_by_alignment_score() (score >= 80 -> IMPLEMENTATION, else -> DISCOVERY)
5. Criar testes E2E: tests/test_design_solution_workflow.py (10+ testes)
6. Validar integração: APPROVAL_PENDING -> SOLUTION_DESIGN -> routing correto

## [EMOJI] DOCUMENTAÇÃO COMPLETA
- @.cursor/rules/rag-bsc-core.mdc - Router central (workflow obrigatório, lições MVP)
- @.cursor/rules/derived-cursor-rules.mdc - Metodologias (test debugging, LLM testing)
- Consultar seção "Localização da Documentação" em rag-bsc-core.mdc (47 docs indexados)

## [EMOJI] DEFINITION OF DONE
- [ ] Handler design_solution() implementado (~150-200 linhas)
- [ ] BSCState expandido com 2 campos novos
- [ ] Routing condicional funcionando (score-based)
- [ ] 10+ testes E2E passando (100%)
- [ ] Zero regressões (Sprint 1 continua funcionando)
- [ ] Logs estruturados (timestamps, scores, decisões routing)
```

---

## VERSÃO MÍNIMA (Alternativa Rápida)

```
# SESSÃO 39 - Continuar Sprint 2: Task 2.4

**Contexto**: BSC RAG Agent, Sprint 2 (Strategy Map MVP) - 50% completo (3/6 tarefas).

**Tarefa**: 2.4 Node design_solution() (4-6h) - Integrar StrategyMapDesignerTool + AlignmentValidatorTool no LangGraph workflow.

**Arquivos**:
- @.cursor/progress/consulting-progress.md (Sessão 38, linhas 11-126)
- @docs/sprints/SPRINT_2_DESIGN.md (seção 2.4, linhas 590-650)
- @src/tools/strategy_map_designer.py (API design_strategy_map)
- @src/tools/alignment_validator.py (API validate_strategy_map)

**Metodologia**: Sequential Thinking + Brightdata research + Checklist 15 pontos.

**Próximos Passos**:
1. Ler SPRINT_2_DESIGN.md seção 2.4
2. Implementar design_solution_handler() em workflow.py
3. Expandir BSCState (strategy_map, alignment_report)
4. Criar testes E2E (10+ testes)
5. Validar routing APPROVAL -> SOLUTION_DESIGN -> IMPLEMENTATION
```

---

## INSTRUÇÕES DE USO

### Quando usar cada versão:

**VERSÃO COMPLETA** [OK] RECOMENDADA
- Primeira vez continuando após pausa longa (2+ dias)
- Contexto completo necessário
- Tarefa complexa (como esta - integração workflow)
- ~250 palavras

**VERSÃO MÍNIMA**
- Continuação no mesmo dia
- Contexto fresco na memória
- Tarefa simples/continuação direta
- ~100 palavras

### Como usar:

1. **Copiar** o prompt escolhido (incluindo markdown)
2. **Colar** no novo chat do Cursor
3. **Adicionar** qualquer contexto específico adicional se necessário
4. **Enviar** e deixar o agente ler os arquivos @mencionados

---

## NOTAS TÉCNICAS

### Por que este formato funciona:

1. **@mentions automáticos** - Agente abre arquivos sem precisar pedir
2. **Hierarquia clara** - Scan rápido das seções
3. **Comandos acionáveis** - Verbos imperativos (Ler, Implementar, Validar)
4. **Métricas concretas** - Estado quantificado (3/6 tarefas, 50%)
5. **DoD explícito** - Checklist de conclusão clara

### Template reutilizável:

Este formato pode ser adaptado para qualquer sessão futura:
- Atualizar número sessão
- Atualizar tarefa atual
- Atualizar arquivos @mencionados
- Manter estrutura 6 seções

---

**Criado**: 2025-11-20 (Sessão 38)
**Próxima Sessão**: 39 (Sprint 2 Continuação)

