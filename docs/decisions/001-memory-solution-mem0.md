# ADR 001: Solução de Memória Persistente - Mem0 Platform

**Data**: 2025-10-15  
**Status**: Aceito  
**Decisores**: Usuário + Claude (Cursor IDE)

---

## Contexto

Agente Consultor BSC precisa de memória persistente para:
- Armazenar ClientProfile (empresa, indústria, desafios, objetivos)
- Manter histórico de engagements (sessões, decisões, tool outputs)
- Permitir consultas semânticas ("O que decidimos sobre KPIs financeiros?")
- Preservar contexto entre sessões (dias/semanas de intervalo)

---

## Opções Consideradas

### Opção A: Mem0 Platform (mem0.ai)
**PROS**:
- Self-improving memory (+26% accuracy research validado)
- Otimizado para LLM context retrieval (não DB genérico)
- API simples (store/recall vs SQL queries)
- Semantic search built-in
- Free tier generoso (100k operations/mês)
- Setup rápido (30 min vs 2-3h SQL)

**CONS**:
- Vendor lock-in (serviço externo)
- Custo recorrente ($29/mês após free tier)
- Menos poder para analytics complexos (não SQL)

### Opção B: Supabase (PostgreSQL + pgvector)
**PROS**:
- Controle total (SQL + auth + storage + functions)
- Free tier generoso (500MB DB, 2GB storage)
- Row-Level Security (multi-tenancy fácil)
- Analytics SQL poderosos
- Self-hosted option disponível

**CONS**:
- Setup mais complexo (schema design, migrations)
- Menos "inteligente" que Mem0 (sem self-improving)
- Requer queries SQL (mais código boilerplate)

### Opção C: Redis (in-memory)
**PROS**:
- Muito rápido (sub-ms latency)
- Simples key-value store
- Free tier Redis Cloud

**CONS**:
- Não otimizado para LLM memory
- Sem semantic search nativo
- Persistência menos durável que DB

---

## Decisão

**Escolhemos Opção A: Mem0 Platform**

---

## Justificativa

1. **MVP Speed**: Setup 30 min (Mem0) vs 2-3h (Supabase SQL) → Acelera FASE 1
2. **LLM-Optimized**: Mem0 foi desenhado especificamente para memória de agentes LLM
3. **Self-Improving**: Research validado (arXiv 2025) mostra +26% accuracy, 91% lower latency
4. **Semantic Search**: Built-in, não precisa implementar vetores manualmente
5. **Free Tier Suficiente**: 100k ops/mês = ~2.000 clientes/mês (50 ops/cliente)
6. **Cloud-Native**: Mem0 é backing service externo desde o início (12-Factor #4)

---

## Arquitetura Híbrida Futura

**MVP (Fase 1-5)**: Mem0 exclusivo
- ClientProfile, session history, tool outputs, diagnostic reports (markdown)

**Fase 7 (Se escalar >50 clientes)**: Mem0 + Supabase
- Mem0: Memória conversacional (contexto, decisões, semantic search)
- Supabase: Multi-tenancy (auth, RLS), file storage (PDFs), analytics (SQL tables)

---

## Riscos e Mitigações

**RISCO**: Mem0 ficando caro ($29/mês → $99/mês se crescer)
- **Mitigação**: Factory pattern permite migrar para Supabase sem reescrever código
- **Contingência**: Mem0 open-source self-hosted disponível

**RISCO**: Vendor lock-in
- **Mitigação**: Export semanal de memories (Mem0 API permite)
- **Contingência**: Plano de migração para PostgreSQL documentado

---

## Consequências

**Positivas**:
- ✅ FASE 1 mais rápida (5-7h vs 7-9h Supabase)
- ✅ Memória self-improving (melhora com uso)
- ✅ Menos código boilerplate (API simples vs SQL queries)

**Negativas**:
- ❌ Custo recorrente ($0 → $29/mês eventualmente)
- ❌ Analytics complexos precisarão de Supabase depois (Fase 7)

**Neutras**:
- Supabase continua disponível para Fase 7 (auth, files, analytics)

---

## Validação

**Checkpoint 1 (Após FASE 1)**:
- Memória persiste entre sessões? ✅/❌
- Profile recupera corretamente? ✅/❌
- Semantic search funciona? ✅/❌

Se FALHAR: Rollback para Supabase (contingência documentada)

---

**Referências**:
- Mem0 Research Paper: arXiv 2025 "Building Production-Ready AI Agents"
- Mem0 Platform: https://mem0.ai
- 12-Factor Agents: Factor #4 (Backing Services)

