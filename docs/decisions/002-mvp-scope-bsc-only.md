# ADR 002: Escopo MVP - BSC Exclusivo (Multi-Domain Fase 6)

**Data**: 2025-10-15  
**Status**: Aceito  
**Decisores**: Usuário + Claude (Cursor IDE)

---

## Contexto

RAG Core é 100% reutilizável para qualquer domínio de conhecimento (OKRs, Design Thinking, Lean Startup, etc). Decisão necessária: Implementar multi-domain no MVP ou focar BSC exclusivamente?

---

## Opções Consideradas

### Opção A: BSC-Only MVP (ESCOLHIDA)
**Escopo**: Literatura BSC exclusiva (7.965 chunks atuais)  
**Timeline**: 4-5 semanas (48 micro-tarefas)

### Opção B: Multi-Domain MVP
**Escopo**: BSC + OKRs + Design Thinking (3 domínios)  
**Timeline**: 5-6 semanas (+8 tarefas, 13-18h adicionais)

### Opção C: Multi-Domain Massivo
**Escopo**: BSC + OKRs + Design Thinking + Lean + Agile + Change Mgmt (6+ domínios)  
**Timeline**: 6-8 semanas (+20 tarefas, 30-40h adicionais)

---

## Decisão

**Escolhemos Opção A: BSC-Only MVP**

Multi-domain será **FASE 6** (pós-validação, 1-1.5 semanas adicionais)

---

## Justificativa

### 1. Validação de Valor Primeiro
- MVP já tem 48 micro-tarefas (59-75h esforço)
- Adicionar multi-domain = scope creep (+27% tempo)
- Validar valor do agente consultor ANTES de expandir domínios
- Princípio Anthropic: "Start simple, add complexity when needed"

### 2. Especialização Profunda
- BSC é domínio complexo (4 perspectivas, mapas estratégicos, KPIs, governance)
- Melhor ser **especialista profundo em BSC** que **generalista superficial**
- C-level valoriza especialização (não "jack of all trades")

### 3. Feedback-Driven Expansion
- Após MVP validado, feedback de clientes direcionará quais domínios adicionar
- "Gostaria de ajuda com OKRs também" (3+ pedidos) → TRIGGER Fase 6
- Evita gastar tempo em domínios que clientes não querem

### 4. Infraestrutura RAG Já é Multi-Domain
- Chunker, embeddings, vector store, hybrid search = genéricos
- Adicionar novo domínio = apenas curar conteúdo + indexar (13-18h)
- Não estamos "fechando porta" para multi-domain, apenas adiando

### 5. Proposta de Valor Clara
- MVP: "Agente Consultor Especialista em Balanced Scorecard" (nicho claro)
- Multi-domain: "Agente Consultor Estratégia Empresarial" (genérico demais para MVP)

---

## Trade-offs

| Aspecto | BSC-Only | Multi-Domain |
|---------|----------|--------------|
| **Timeline** | 4-5 semanas | 5-6 semanas |
| **Especialização** | Profunda BSC | Superficial 3 domínios |
| **Target Market** | Empresas implementando BSC | Todas empresas (menos focado) |
| **Validação** | Rápida (foco) | Lenta (muitas variáveis) |
| **Feedback Quality** | Alta (nicho claro) | Dispersa (vários domínios) |

---

## FASE 6: Multi-Domain (Futura)

### Quando Implementar
**Trigger**: Após MVP validado + 3+ clientes pedirem outro domínio

### Domínios Prioritários (Baseado em Complementaridade)
1. **OKRs** (Objectives & Key Results): Complementar a BSC para execution management
2. **Design Thinking**: Inovação e customer-centricity (alinha com perspectiva Clientes)
3. **Lean Startup**: Startups preferem Lean vs BSC full (segmento novo)

### Esforço Fase 6
- 8 micro-tarefas
- 13-18 horas (4-5 sessões)
- 1-1.5 semanas

### Arquitetura Multi-Domain
```
Qdrant Collections:
├── bsc_literature (7.965 chunks)
├── okr_guides (~200-300 chunks)
├── design_thinking_methods (~200-300 chunks)
└── lean_startup_principles (~200-300 chunks)

Query Router Expandido:
- Detecta domínio(s) relevante(s) na query
- Busca em collection(s) específica(s)
- Aplica RRF se múltiplas collections
- Cross-domain insights ("BSC vs OKRs")
```

---

## Riscos e Mitigações

**RISCO**: Clientes querem multi-domain já no MVP
- **Probabilidade**: Baixa (C-level geralmente foca em 1 metodologia)
- **Mitigação**: Explicar roadmap, Fase 6 vem rápido (1-1.5 semanas)
- **Contingência**: Se 50%+ clientes pedirem, priorizar Fase 6 imediatamente pós-MVP

**RISCO**: Competidores multi-domain ganham mercado
- **Probabilidade**: Baixa (especialização profunda é defensável)
- **Mitigação**: BSC é nicho grande ($2B+ consulting market)
- **Contingência**: Fast-follow com Fase 6 se necessário

---

## Consequências

**Positivas**:
- ✅ MVP 27% mais rápido (4-5 semanas vs 5-6)
- ✅ Especialização profunda (autoridade em BSC)
- ✅ Validação focada (menos variáveis)
- ✅ Feedback claro ("O que falta no agente BSC?")

**Negativas**:
- ❌ Target market limitado (apenas empresas BSC)
- ❌ Competidores generalistas podem parecer "mais completos"

**Neutras**:
- Multi-domain continua viável (Fase 6 já planejada)
- Arquitetura RAG já suporta (zero modificações necessárias)

---

## Validação

**Checkpoint 5 (Após FASE 5)**:
- Clientes pediram outro domínio? Quantos? Qual?
- Se >= 3 pedidos do mesmo domínio → TRIGGER Fase 6

**Beta Testing (2-3 semanas pós-MVP)**:
- Survey: "Você gostaria que o agente cobrisse OKRs/Design Thinking/Lean?"
- Se > 60% dizem "SIM" → Priorizar Fase 6

---

**Referências**:
- Anthropic: "Building Effective Agents" - Start simple
- OpenAI: "Practical Guide" - Validate before scaling
- Kaplan & Norton: "The Balanced Scorecard" - Especialização estratégica

