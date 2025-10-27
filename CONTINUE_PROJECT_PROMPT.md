# 🚀 PROMPT PARA CONTINUAR O PROJETO

**Copy-paste this prompt to start a new chat session:**

---

```
Continue com o projeto Agente BSC RAG (transformação em Agente Consultor Empresarial).

ESTADO ATUAL:
- FASE 3 (Diagnostic Tools) - 86% completa (12/14 tarefas)
- Tarefas completas: 3.1-3.10 (SWOT, Five Whys, Issue Tree, KPI, Strategic Objectives, Benchmarking, Tool Selection, CoT Reasoning, Tool Output Persistence, E2E Tests)
- Faltam apenas: 3.11 Action Plan Tool + 3.12 Priorization Matrix (últimas 2 tarefas da FASE 3)

PRÓXIMA TAREFA:
FASE 3.11 - Action Plan Tool (3-4h estimado)
- Objetivo: Criar ferramenta para gerar planos de ação baseados em diagnósticos BSC
- Padrão estabelecido: Schema → Prompts → Tool → Integração → Testes → Docs
- Consulte @.cursor/progress/consulting-progress.md para histórico completo

METODOLOGIA OBRIGATÓRIA:
1. Sequential Thinking para planejamento antes de implementar
2. Brightdata para pesquisar melhores práticas da comunidade
3. Consulte @.cursor/rules/derived-cursor-rules.mdc para metodologias validadas
4. Seguir workflow de 7 steps em @.cursor/rules/rag-bsc-core.mdc

REGRAS CRÍTICAS:
- Implementar testes (pytest) antes de considerar completo
- Documentar lições aprendidas em docs/lessons/
- Rodar suite E2E completo ao finalizar (pytest -v)
- Não fazer regressões: validar que funcionalidade existente continua funcionando
- Pattern reutilizar: Schema/Prompts/Tool/Integration/Testes/Docs (ROI: 30-40 min economizados)

Comece com Sequential Thinking para planejar FASE 3.11 Action Plan Tool.
```

---

## 📝 ANOTAÇÕES DE USO

**Quando usar este prompt:**
- Iniciando nova sessão de chat com o agente de IA
- Retomando trabalho após pausa
- Alternando entre diferentes agentes AI

**O que o prompt faz:**
1. ✅ Estabelece contexto do projeto (FASE 3, 86% completo)
2. ✅ Define estado atual (12/14 tarefas, faltam 3.11 + 3.12)
3. ✅ Especifica próxima tarefa (3.11 Action Plan Tool)
4. ✅ Referencia arquivos-chave (@consulting-progress.md, @derived-cursor-rules.mdc)
5. ✅ Define metodologia obrigatória (Sequential + Brightdata)
6. ✅ Lista regras críticas (testes, docs, E2E)
7. ✅ Inicia com ação concreta (Sequential Thinking para planejar)

**Por que funciona bem:**
- ✅ Conciso mas completo (8 linhas essenciais)
- ✅ Referencia arquivos (@mentions) - agente pode ler automaticamente
- ✅ Específico sobre o que fazer (FASE 3.11)
- ✅ Metodológico sobre como fazer (Sequential + Brightdata)
- ✅ Acionável (comece com...)
- ✅ Copy-paste friendly (bloco único de texto)

---

## 🔧 PERSONALIZAÇÃO

Para usar em outras fases do projeto, ajuste apenas:

```diff
- Tarefas completas: 3.1-3.10 (...)
+ Tarefas completas: [lista atual]

- Faltam apenas: 3.11 Action Plan Tool + 3.12 Priorization Matrix
+ Faltam apenas: [próximas tarefas específicas]

- PRÓXIMA TAREFA: FASE 3.11 - Action Plan Tool
+ PRÓXIMA TAREFA: [tarefa específica atual]
```

**Template genérico:**
```
Continue com o projeto. Consulte @consulting-progress.md. ESTADO: [FASE X] [% complete] ([N/M] tarefas). Próxima: [TAREFA]. Use Sequential Thinking + Brightdata. Siga @derived-cursor-rules.mdc + @rag-bsc-core.mdc workflow 7 steps. Rodar suite E2E ao finalizar. Comece planejando [TAREFA].
```

