---
title: "Sistema de Organização de Agente IA - Estratégias Validadas"
description: "Prompt compilado de estratégias de self-awareness, organização de knowledge base e workflows validados para replicar em outros projetos"
version: "1.0"
author: "Agente IA - Engelar Engenharia"
date: "04/10/2025"
source: "Extraído de Advance Steel 2019 project (.cursor/rules/)"
domain: "Agnóstico (adaptável para qualquer tecnologia/projeto)"
estimated_reading: "30 min"
tags: 
  - "meta-prompt"
  - "knowledge-base-organization"
  - "agent-self-awareness"
  - "documentation-strategy"
  - "workflow-automation"
---

# 🧠 SISTEMA DE ORGANIZAÇÃO DE AGENTE IA

## 🎯 OBJETIVO DESTE PROMPT

Este documento compila **estratégias validadas** para construir um **Agente IA autoconsciente** capaz de:

1. ✅ **Conhecer-se** (Self-Awareness): Saber quais documentos possui, quando usá-los, onde estão
2. ✅ **Organizar Knowledge Base**: Estruturar documentação de forma navegável e eficiente
3. ✅ **Workflows Estruturados**: Seguir processos consistentes que economizam tempo
4. ✅ **Aprender Continuamente**: Documentar lições, antipadrões, decisões técnicas
5. ✅ **Manter-se Atualizado**: Versionar documentação, rastrear mudanças

**Fonte:** Projeto Advance Steel 2019 (Engelar Engenharia, 2024-2025)  
**ROI validado:** 145-150 min economizados por projeto, redução 79% tokens em discovery, 85% mais rápido

---

## 📋 ÍNDICE

1. [Estratégia 1: Self-Awareness do Agente](#estratégia-1-self-awareness-do-agente)
2. [Estratégia 2: Organização da Knowledge Base](#estratégia-2-organização-da-knowledge-base)
3. [Estratégia 3: Workflows Estruturados](#estratégia-3-workflows-estruturados)
4. [Estratégia 4: Lições Validadas & Antipadrões](#estratégia-4-lições-validadas--antipadrões)
5. [Estratégia 5: Ferramentas & Auditoria](#estratégia-5-ferramentas--auditoria)
6. [Estratégia 6: Atualização Contínua](#estratégia-6-atualização-contínua)
7. [Workflow: Adicionar Novo Documento](#workflow-adicionar-novo-documento)
8. [Como Implementar em Seu Projeto](#como-implementar-em-seu-projeto)
9. [Templates Reutilizáveis](#templates-reutilizáveis)
10. [Checklist de Implementação](#checklist-de-implementação)

---

## ESTRATÉGIA 1: Self-Awareness do Agente

### **Conceito**

O agente deve **conhecer-se completamente**: quais rules possui, quando usar cada uma, onde estão localizadas, como navegar na knowledge base.

### **Componentes Principais**

#### **1.1 Router Central (Core Rule)**

**Objetivo:** Arquivo central `always-applied` que o agente sempre vê.

**Estrutura:**

```markdown
## 📋 ÍNDICE (com links âncora)
1. [Workflow Obrigatório](#workflow-obrigatório)
2. [Lições de Produção](#lições-de-produção)
3. [Mapa de Rules](#mapa-de-rules)
4. [Quick Reference](#quick-reference)
5. [Guia por Cenário](#guia-por-cenário)
6. [Matriz de Decisão](#matriz-de-decisão)
7. [Ferramentas & Auditoria](#ferramentas--auditoria)
8. [Checklist Pré-Implementação](#checklist)
9. [Princípios Fundamentais](#princípios)
10. [Localização Rules](#localização)

## 🚨 WORKFLOW OBRIGATÓRIO
ANTES de implementar QUALQUER funcionalidade, execute:
1. 🧠 Sequential Thinking (planeje ANTES de codificar)
2. 🎯 Discovery (Catalog/Index - descubra O QUE posso fazer)
3. 🗺️ Navigation (Map - identifique QUAL doc consultar)
4. 📚 Knowledge Base (doc específico - aprenda COMO fazer)
5. 📘 Rule Especializada (padrões validados)
6. ✅ Implementação
7. 🧪 Validação (testes múltiplos, não apenas um!)

## 🗺️ MAPA DE RULES (Quando Usar Cada Uma)
| Tarefa/Contexto | Rule a Consultar | Quando Usar |
|----|----|-----|
| Descobrir capabilities, ROI | @capabilities-catalog | Estimar esforço, decidir o que implementar |
| Padrões comuns rápidos | @quick-refs | 80% casos <5 min |
| Implementação core | @[domain]-api | Desenvolvimento da funcionalidade principal |
| UI/Forms | @[domain]-ui | Interfaces de usuário |
| Troubleshooting | @[domain]-troubleshooting | Resolver erros, evitar antipadrões |
| Qual doc consultar | @knowledge-map | Navegação na KB |

## 📚 LOCALIZAÇÃO DAS RULES
```
.cursor/rules/
├── [domain]-core.mdc                    ← VOCÊ ESTÁ AQUI (router)
├── [domain]-capabilities-catalog.mdc    ← "O QUE posso fazer"
├── [domain]-quick-refs.mdc              ← Padrões rápidos 1 página
├── [domain]-[api/tech]-[name].mdc       ← Rules especializadas
├── [domain]-troubleshooting.mdc         ← Debug + Antipadrões
└── [domain]-knowledge-map.mdc           ← Navegação KB
```

## 🎯 GUIA RÁPIDO POR CENÁRIO
### Cenário 1: [Tarefa Tipo A]
1. Sequential Thinking
2. Consultar @[rule-X]
3. Usar template [Y]
4. Testar [N]x consecutivas

### Cenário 2: [Tarefa Tipo B]
[workflow específico]

## 📊 MATRIZ DE DECISÃO: PROBLEMA → RULE
| Se você tem... | Então consulte... |
|---|---|
| Erro [X] | @[rule-Y] + @troubleshooting |
| Dúvida [A] | @knowledge-map → identificar doc |
| Tarefa [B] | @quick-refs (padrão rápido) |
```

**ROI:** O router economiza **5-10 min por tarefa** em decisões de "qual doc consultar".

---

#### **1.2 Mapa de Knowledge Base**

**Objetivo:** Índice navegável da documentação completa.

**Estrutura:**

```markdown
# 🗺️ MAPA DA KNOWLEDGE BASE - [SEU PROJETO]

## 📚 DOCUMENTAÇÃO POR CATEGORIA

### 🔍 FERRAMENTAS DE DISCOVERY

#### 📇 TAGS_INDEX ⭐ NOVO
- Tipo: Índice consolidado navegável
- Uso: Busca rápida por tags, categorias, complexidade
- Quando usar: Descobrir docs por palavra-chave, filtrar por complexidade
- Conteúdo: 150+ tags, Quick Search Matrix
- Path: knowledge_base/Docs/TAGS_INDEX.md
- ✨ Benefício: Discovery 50-70% mais rápida

#### 🎯 Capabilities Catalog ⭐ SISTEMA DISCOVERY
- Tipo: Catálogo estruturado de capabilities
- Uso: Descobrir "O QUE POSSO FAZER" com ROI transparente
- Quando usar: Planejamento projetos, estimar tempo/ROI
- Path: .cursor/rules/capabilities-catalog.mdc
- ✨ Benefício: 79% menos tokens, 85% mais rápido

#### ⚡ Quick Reference Cards ⭐ PADRÕES RÁPIDOS
- Tipo: Mini-guias 1 página
- Uso: Padrões comuns em <5 min
- Quando usar: 80% casos comuns, troubleshooting rápido
- Path: .cursor/rules/quick-refs.mdc
- ✨ Benefício: 80% casos resolvidos <5 min

### 🔧 [CATEGORIA 2: APIs/Tutoriais]
[listar documentação por categoria]

### 💼 [CATEGORIA 3: Exemplos Práticos]
[listar samples/exemplos]

## 🏆 GOLDEN STANDARDS (Referências Validadas)
- ⭐ [Sample 1]: BEST para [caso de uso X]
- ⭐ [Sample 2]: VALIDATED [N]x em produção
- ⭐ [Sample 3]: BASE para [caso de uso Y]

## 🎯 GUIAS DE USO RÁPIDO POR CENÁRIO
### 🏗️ [CENÁRIO 1]
1. [Doc A] → Aprenda workflow básico
2. [Sample B] → Veja código funcional
3. [Doc C] → Consulte referência técnica

### ⚡ [CENÁRIO 2]
[workflow específico]

## 📊 MATRIZ DE DECISÃO RÁPIDA
| Objetivo | Documento Principal | Suporte | Complexidade |
|---|---|---|---|
| [Tarefa A] | [Doc 1] | [Doc 2] | ⭐⭐ |
| [Tarefa B] | [Doc 3] | [Doc 4] | ⭐⭐⭐⭐ |

## 🚨 TROUBLESHOOTING GUIDE
| Problema | Documentos para Consultar |
|---|---|
| Erro [X] | [Doc A] + [Doc B] |
| Problema [Y] | [Doc C] |

## 🔍 PALAVRAS-CHAVE PARA BUSCA SEMÂNTICA
- **[Categoria A]:** keyword1, keyword2, keyword3
- **[Categoria B]:** keyword4, keyword5, keyword6
```

**ROI:** Knowledge Map economiza **3-8 min por busca** (vs busca não estruturada).

---

#### **1.3 Capabilities Catalog**

**Objetivo:** Catálogo de "O QUE POSSO FAZER" com ROI transparente.

**Estrutura:**

```markdown
# 📘 CATÁLOGO DE CAPABILITIES - [SEU PROJETO]

## 🗂️ TAXONOMIA DE CAPABILITIES

### Categorias Principais
1. [CATEGORIA 1]: [descrição]
2. [CATEGORIA 2]: [descrição]
3. [CATEGORIA 3]: [descrição]

### Classificação de Complexidade
| Nível | Tempo | Características | Exemplos |
|---|---|---|---|
| ⭐ Trivial | <30 min | API única, lógica simples | [Ex1] |
| ⭐⭐ Simples | 30-60 min | 2-3 APIs, lógica moderada | [Ex2] |
| ⭐⭐⭐ Intermediário | 1-3h | 5+ APIs, lógica complexa | [Ex3] |
| ⭐⭐⭐⭐ Avançado | 3-6h | 10+ APIs, arquitetura elaborada | [Ex4] |
| ⭐⭐⭐⭐⭐ Expert | 6h+ | Sistema completo | [Ex5] |

## 📑 ÍNDICE NAVEGÁVEL

### Quick Reference Table
| CAP-ID | Nome | Categoria | Complexidade | Tempo | ROI | Prioridade |
|---|---|---|---|---|---|---|
| CAP-001 | [Nome 1] | [Cat A] | ⭐⭐⭐ | 20-30h | 100h/ano | 🔥 P0 |
| CAP-002 | [Nome 2] | [Cat B] | ⭐⭐ | 10-15h | 50h/ano | 🔥 P1 |

### Por Categoria
#### [CATEGORIA 1]
- [CAP-001: Capability X] - ⭐⭐⭐ - ROI [Y]h/ano - P0
- [CAP-002: Capability Z] - ⭐⭐ - ROI [W]h/ano - P1

### Por ROI (Valor Anual)
#### 🔥🔥🔥 Ultra-Alto (>500h/ano)
- [CAP-XXX]: [ROI]h/ano

#### 🔥🔥 Alto (200-500h/ano)
- [CAP-YYY]: [ROI]h/ano

## 🚀 CAPABILITIES DETALHADAS

Cada capability em arquivo separado:
- capabilities/CAP-001-[nome].md
- capabilities/CAP-002-[nome].md

## 💰 ROI CONSOLIDADO
- Total economia/ano: [X-Y]h
- Payback financeiro: R$ [Z]k/ano
- Tempo desenvolvimento total: [A-B]h
- ROI médio ponderado: [C]x
```

**ROI:** Capabilities Catalog economiza **79% tokens** e **85% tempo** em discovery (vs semantic search completa na KB).

---

#### **1.4 Quick Reference Cards**

**Objetivo:** Padrões comuns de 1 página para 80% dos casos.

**Estrutura:**

```markdown
# 🎯 QUICK REFERENCE CARDS - [SEU PROJETO]

## QR-001: [Tarefa Comum A]

**Quando usar:** [descrição]
**APIs principais:** [lista]
**Complexidade:** ⭐⭐
**Tempo:** 10-15 min

### Código Essencial
```[linguagem]
// Código mínimo funcional (10-20 linhas)
[código exemplo]
```

### Parâmetros Críticos
| Parâmetro | Tipo | Descrição | Exemplo |
|---|---|---|---|
| [param1] | [tipo] | [desc] | [ex] |

### Troubleshooting
| Erro | Causa | Solução |
|---|---|---|
| [erro1] | [causa] | [solução] |

### 📚 Ver também
- [Doc X] → [quando consultar]
- [Sample Y] → [quando usar]

---

## QR-002: [Tarefa Comum B]
[estrutura igual]

---

## 🔍 MATRIZ DE QUICK REF
| Preciso de... | Quick Ref | Complexidade | Tempo |
|---|---|---|---|
| [Tarefa A] | QR-001 | ⭐ | 10 min |
| [Tarefa B] | QR-002 | ⭐⭐⭐ | 30 min |
```

**ROI:** Quick Refs economizam **5-15 min por task** (80% casos comuns).

---

## ESTRATÉGIA 2: Organização da Knowledge Base

### **Conceito**

A Knowledge Base deve ser **estruturada hierarquicamente** e **navegável**, com múltiplas entradas (por categoria, por ROI, por complexidade, por palavra-chave).

### **Estrutura Recomendada**

```
seu_projeto/
├── .cursor/
│   └── rules/                          ← Rules do agente
│       ├── [domain]-core.mdc           ← Router central (always-applied)
│       ├── [domain]-capabilities-catalog.mdc
│       ├── [domain]-quick-refs.mdc
│       ├── [domain]-knowledge-map.mdc
│       ├── [domain]-[tech]-api.mdc     ← Rules especializadas
│       ├── [domain]-troubleshooting.mdc
│       └── capabilities/               ← Capabilities individuais
│           ├── CAP-001-[nome].md
│           ├── CAP-002-[nome].md
│           └── ...
│
├── knowledge_base/                     ← Documentação completa
│   ├── Docs/                          ← Guias e referências
│   │   ├── TAGS_INDEX.md              ← Índice de tags (discovery)
│   │   ├── METADATA_SCHEMA.md         ← Schema de metadados
│   │   ├── [Doc1]_safe.md
│   │   ├── [Doc2]_safe.md
│   │   └── ...
│   │
│   ├── Samples/                       ← Exemplos práticos
│   │   └── Projects/
│   │       ├── [Sample1]/
│   │       │   ├── README.md          ← Metadados completos
│   │       │   ├── [código]
│   │       │   └── ...
│   │       ├── [Sample2]/
│   │       └── ...
│   │
│   └── Audits/                        ← Auditorias e análises
│       ├── auditoria_[tema1].md
│       ├── auditoria_[tema2].md
│       └── ...
│
└── README.md                          ← Overview do projeto
```

### **Componentes-Chave**

#### **2.1 TAGS_INDEX.md**

**Objetivo:** Índice consolidado navegável por tags.

**Estrutura:**

```markdown
# 📇 TAGS INDEX - [SEU PROJETO]

## 🎯 COMO USAR ESTE ÍNDICE

**3 formas de busca:**
1. **Por Tag** (Seção 1-5): Browse alfabético ou Ctrl+F
2. **Por Categoria** (Seção 6): Explorar por tipo de doc
3. **Quick Search Matrix** (Seção 7): Cenários comuns mapeados

## 📑 SEÇÃO 1: TAGS PRINCIPAIS (A-Z)

### A
- **[tag-a]** (Docs: 5, Samples: 2)
  - Docs: [Doc1], [Doc2], [Doc3], [Doc4], [Doc5]
  - Samples: [Sample1], [Sample2]

### B
- **[tag-b]** (Docs: 3, Samples: 1)
  - Docs: [Doc1], [Doc2], [Doc3]
  - Samples: [Sample1]

[continuar alfabeticamente]

## 📊 SEÇÃO 2: TAGS POR CATEGORIA

### 🔧 [Categoria A]
- [tag1], [tag2], [tag3]

### 📊 [Categoria B]
- [tag4], [tag5], [tag6]

## 🎯 SEÇÃO 3: DOCS POR COMPLEXIDADE

| Complexidade | Docs |
|---|---|
| ⭐ Beginner | [Doc1], [Doc2] |
| ⭐⭐ Intermediate | [Doc3], [Doc4] |
| ⭐⭐⭐ Advanced | [Doc5] |

## 🚀 SEÇÃO 4: SAMPLES POR COMPLEXIDADE

[estrutura similar]

## 📚 SEÇÃO 5: CAPABILITIES MAPEADAS

| Capability | Docs Relacionados | Samples |
|---|---|---|
| CAP-001 | [Doc1], [Doc2] | [Sample1] |
| CAP-002 | [Doc3] | [Sample2], [Sample3] |

## 🔍 SEÇÃO 6: QUICK SEARCH MATRIX

| "Preciso de..." | Tags | Docs | Samples |
|---|---|---|---|
| [Cenário comum 1] | [tags] | [docs] | [samples] |
| [Cenário comum 2] | [tags] | [docs] | [samples] |

## 🎓 SEÇÃO 7: LEARNING PATHS

### 🚶 Beginner Path
1. Começar: [Doc A]
2. Praticar: [Sample B]
3. Avançar: [Doc C]

### 🏃 Advanced Path
1. Review: [Doc D]
2. Deep dive: [Doc E]
3. Master: [Sample F]
```

**ROI:** TAGS_INDEX economiza **50-70% tempo** em discovery (vs semantic search completa).

---

#### **2.2 README.md em Samples**

**Objetivo:** Metadados completos em cada sample para facilitar discovery.

**Estrutura:**

```markdown
---
title: "[Nome do Sample]"
type: "[template/example/tutorial]"
complexity: "[beginner/intermediate/advanced/expert]"
estimated_time: "[tempo em minutos]"
categories: [cat1, cat2, cat3]
apis: [API1, API2, API3]
capabilities: [CAP-001, CAP-002]
use_cases: [caso1, caso2, caso3]
keywords: [keyword1, keyword2, keyword3]
last_updated: "YYYY-MM-DD"
version: "X.Y"
validated_in_production: [true/false]
---

# [Nome do Sample]

## 📋 Overview
[Descrição breve 1-2 parágrafos]

## 🎯 Quando Usar
- ✅ [Cenário A]
- ✅ [Cenário B]
- ❌ Não usar para: [Cenário C]

## 🚀 Quick Start
```[linguagem]
[código exemplo mínimo]
```

## 📚 Conteúdo
- [Arquivo1.ext]: [descrição]
- [Arquivo2.ext]: [descrição]

## 🔧 Conceitos Demonstrados
1. [Conceito A]: [explicação]
2. [Conceito B]: [explicação]

## ⏱️ Tempo Estimado
- Setup: [X] min
- Entendimento: [Y] min
- Adaptação: [Z] min
- Total: [X+Y+Z] min

## 🎓 Pré-requisitos
- [Requisito 1]
- [Requisito 2]

## 📖 Documentação Relacionada
- [Doc A]: [quando consultar]
- [Doc B]: [quando consultar]

## 🏆 Status
- ✅ Validado em produção: [sim/não]
- ✅ Testes: [N]x consecutivos OK
- ✅ Antipadrões: 0 detectados

## 🔗 Capabilities Relacionadas
- [CAP-XXX]: [relação]

## 📝 Notas
[observações importantes]
```

**ROI:** README em samples economiza **10-20 min** de análise por sample (vs ler código diretamente).

---

## ESTRATÉGIA 3: Workflows Estruturados

### **Conceito**

Workflows **consistentes e reproduzíveis** que o agente segue automaticamente, economizando tempo de decisão e evitando esquecimentos.

### **3.1 Workflow Obrigatório (Básico)**

**Estrutura:**

```markdown
## 🚨 WORKFLOW OBRIGATÓRIO

ANTES de implementar QUALQUER funcionalidade:

```
1. 🧠 Sequential Thinking
   └─ Planeje arquitetura, identifique riscos ANTES de codificar

2. 🎯 Discovery (Capabilities/Index)
   └─ Descubra "O QUE POSSO FAZER" (79% menos tokens)

3. 🗺️ Navigation (Knowledge Map)
   └─ Identifique QUAL documento consultar

4. 📚 Knowledge Base Específica
   └─ Consulte referência detalhada do doc identificado

5. 📘 Rule Especializada
   └─ Escolha rule correta para tipo de tarefa

6. ✅ Implementação
   └─ Use padrões validados

7. 🧪 Validação
   └─ Teste [N]x consecutivas (NÃO apenas 1!)
```

**❗ Este fluxo economiza [X-Y] horas de debugging por projeto.**
```

**ROI:** Workflow obrigatório economiza **2-3h debugging** por projeto.

---

### **3.2 Vibe Planning Workflow (Projetos Complexos)**

**Quando usar:** Projetos ≥60 min, requisitos vagos, múltiplas sessões, documentação profissional necessária.

**Estrutura (5 Fases):**

```markdown
## 📋 VIBE PLANNING WORKFLOW (Projetos Complexos)

### Quando usar:
- ✅ Projeto ≥60 min estimado
- ✅ Requisitos vagos/incompletos
- ✅ Projeto multi-fase
- ✅ Documentação production-grade necessária
- ✅ Múltiplas sessões (dias/semanas)

### ROI:
- Médio (60-120 min): +122% a +196%
- Grande (>120 min): +200% a +450%
- Com 3+ retomadas: +270% a +456%

---

### FASE 1: Requirement Clarification (5 min)
**Input:** Usuário invoca workflow
**Actions:**
1. Identificar tipo projeto (heurística keywords)
2. Carregar checklist específico do tipo
3. Fazer 3-5 perguntas técnicas críticas
4. Gerar seção "Requirements" do PRD
5. Confirmar com usuário

**Output:** Seção Requirements definida

---

### FASE 2: Features Breakdown (5 min)
**Input:** Requirements confirmados
**Actions:**
1. Consultar Capabilities Catalog
2. Gerar lista MoSCoW (Must/Should/Could/Won't)
3. Adicionar checkboxes para cada feature: `- [ ] ⏸️ Feature`
4. Adicionar seção "Features Breakdown" ao PRD
5. Confirmar com usuário

**Output:** Seção Features Breakdown (MoSCoW com checkboxes)

---

### FASE 3: Divide & Conquer (8 min)
**Input:** Features confirmadas
**Actions:**
1. Consultar Knowledge Base (TAGS_INDEX, Knowledge Map)
2. Quebrar features em 2-4 fases lógicas
3. Estimar tempo por fase (buffer 20-30%)
4. Gerar roadmap table com progress bars
5. Definir Success Metrics, Risks & Mitigations
6. CHECKPOINT 1: Gerar PRD v0.1 completo
7. Confirmar com usuário

**Output:** PRD v0.1 salvo, pronto para iniciar Fase 4

---

### FASE 4: Loop Iterativo (por fase do roadmap)
**Repetir 2-4x (uma vez por fase):**

#### 4.1 Research (5 min)
- Consultar TAGS_INDEX
- Ler samples identificados
- Consultar rules especializadas
- CHECKPOINT 2: Atualizar PRD

#### 4.2 Plan (10 min)
- Definir file tree
- Definir interfaces principais
- Gerar checklist implementação
- CHECKPOINT 2: Atualizar PRD

#### 4.3 Implementation (40 min - variável)
- Implementar código seguindo checklist
- A cada feature: CHECKPOINT 3 (atualizar PRD)
- Se issue: CHECKPOINT 4 (adicionar issue)
- Se resolver: CHECKPOINT 5 (marcar resolvido)
- Se decisão importante: CHECKPOINT 6 (adicionar Decision Log)

#### 4.4 Verification (10 min)
- Compilar
- Executar Checklist Antipadrões (20 itens)
- Testar [N]x consecutivas
- Capturar screenshot
- CHECKPOINT 7: Atualizar PRD

#### 4.5 Fim de Fase
- Marcar fase completa
- CHECKPOINT 8: Atualizar PRD
- Aguardar decisão usuário (continuar/pausar)

---

### FASE 5: Integration & Documentation (10 min)
**Input:** Todas fases completas
**Actions:**
1. Testar integração completa
2. Adicionar seção "Lessons Learned"
3. Adicionar seção "Final Metrics"
4. Gerar README.md
5. Gerar DEPLOY_INSTRUCTIONS.md
6. Criar @prompt_licao_aprendida.md
7. Atualizar Capabilities Catalog (se nova capability)
8. CHECKPOINT 10: PRD v1.0 FINAL

**Output:** Projeto completo, PRD v1.0, documentação gerada

---

### PRD EVOLUTIVO (12 Seções)
1. Metadados
2. Requirements
3. Features Breakdown (MoSCoW com checkboxes)
4. Phases Roadmap (com progress bars)
5. Success Metrics
6. Risks & Mitigations
7. Decision Log
8. Implementation Progress
9. Issues & Blockers
10. Next Steps
11. References
12. Change History

### 10 Checkpoints de Atualização
1. PRD Inicial (após Fase 3)
2. Início de Fase (Research + Plan)
3. Feature Completa (~10-15 min)
4. Issue Encontrado
5. Issue Resolvido
6. Decisão Técnica Importante
7. Verification Fase
8. Fim de Fase
9. Mudança de Requisitos
10. PRD FINAL (v1.0)

---

### Comandos
- `@[domain]-vibe-planning para [tipo] [descrição]` (novo projeto)
- `@[domain]-vibe-planning retomar [PRD_file.md]` (retomar existente)
- `@[domain]-vibe-planning atualizar PRD [mudança]` (atualizar requisitos)
```

**ROI:** Vibe Planning economiza **60-110 min** por projeto complexo.

---

## ESTRATÉGIA 4: Lições Validadas & Antipadrões

### **Conceito**

Documentar **aprendizados validados** (lições + ROI + validação em produção) para evitar repetir erros e economizar tempo.

### **Estrutura:**

```markdown
## 🎯 LIÇÕES DE PRODUÇÃO VALIDADAS

Descobertas críticas que economizam ~[X-Y] minutos por projeto:

### 1. ⚡ [Lição 1 - Nome Descritivo] ([X] min economizados)
```[linguagem]
// ✅ CORRETO: [código correto]
[exemplo]

// ❌ ERRO: [código errado]
[exemplo]
```
**Erro comum:** [descrição]
**Por quê funciona:** [explicação]
**Detalhes:** @[rule-relacionada]

---

### 2. ⚡ [Lição 2] ([Y] min economizados)
- ❌ ERRO: [antipadrão]
- ✅ CORRETO: [pattern correto]
- **Por quê:** [explicação]

[repetir para N lições]

---

## TOTAL ECONOMIA: ~[X-Y] minutos por projeto

---

## ✅ CHECKLIST ANTIPADRÕES (VERIFICATION)

Esta checklist é executada na fase de Verification.

### [Categoria 1] (N itens)
- [ ] **[Antipadrão A]?**
  - ✅ CORRETO: [descrição]
  - ❌ ERRO: [descrição]
  - **Economia: [X] min**

- [ ] **[Antipadrão B]?**
  - ✅ CORRETO: [descrição]
  - ❌ ERRO: [descrição]

[repetir para todos antipadrões]

**Total itens:** [N]
**Threshold para aprovar:** [M]/[N] ✅ ([P]%)
**Se <[M]/[N]:** Revisar itens falhando antes de prosseguir.
```

**ROI:** Checklist antipadrões economiza **145-150 min** por projeto (evita debugging de problemas conhecidos).

---

### **Template: @prompt_licao_aprendida.md**

```markdown
---
title: "Lições Aprendidas - [Nome Projeto]"
date: "YYYY-MM-DD"
project: "[nome]"
duration: "[tempo total]"
outcome: "[sucesso/parcial/falha]"
---

# 📚 LIÇÕES APRENDIDAS - [NOME PROJETO]

## 📋 CONTEXTO
- **Projeto:** [nome]
- **Objetivo:** [descrição breve]
- **Duração:** [tempo estimado] → [tempo real] ([desvio])
- **Resultado:** [sucesso/parcial/falha]

## ✅ O QUE FUNCIONOU BEM
1. **[Aspecto A]:**
   - **Por quê:** [explicação]
   - **Impacto:** Economia [X] min/h
   - **Replicar em:** [onde aplicar novamente]

2. **[Aspecto B]:**
   [estrutura similar]

## ❌ O QUE NÃO FUNCIONOU
1. **[Problema A]:**
   - **Por quê:** [explicação]
   - **Impacto:** Perda [Y] min/h
   - **Solução aplicada:** [descrição]
   - **Evitar em:** [onde não repetir]

2. **[Problema B]:**
   [estrutura similar]

## 🎓 APRENDIZADOS-CHAVE
1. [Aprendizado 1]
2. [Aprendizado 2]
3. [Aprendizado 3]

## 🔄 AÇÕES PARA PRÓXIMOS PROJETOS
- [ ] [Ação 1]: [descrição]
- [ ] [Ação 2]: [descrição]
- [ ] [Ação 3]: [descrição]

## 📊 MÉTRICAS
| Métrica | Target | Real | Status |
|---|---|---|---|
| Tempo dev | [X-Y]h | [Z]h | [🟢/🟡/🔴] |
| Features entregues | [N] | [M] | [🟢/🟡/🔴] |
| Bugs encontrados | <[P] | [Q] | [🟢/🟡/🔴] |

## 🔗 REFERÊNCIAS
- Rules usadas: [lista]
- Samples usados: [lista]
- Decisões técnicas: [link PRD se existir]
```

**ROI:** Template lições aprendidas economiza **20-30 min** de documentação pós-projeto.

---

## ESTRATÉGIA 5: Ferramentas & Auditoria

### **Conceito**

Estratégias **automatizadas ou semi-automatizadas** para verificar qualidade da documentação e código.

### **5.1 Verificação de Links em Documentação**

```markdown
## 🔧 VERIFICAÇÃO DE LINKS EM DOCUMENTAÇÃO

### ✅ USAR (Padrões Validados)

**1. Contar links totais:**
```powershell
Select-String -Path "arquivo.md" -Pattern "texto_simples" | Measure-Object | Select-Object -ExpandProperty Count
```

**2. Identificar arquivos com links ausentes:**
```powershell
Get-ChildItem [pattern] | ForEach-Object { 
    $hasLink = Select-String -Path $_.Name -Pattern "texto_esperado" -Quiet
    if (-not $hasLink) { Write-Output $_.Name } 
}
```

**3. Verificar contexto (grep simples):**
```bash
grep -pattern "texto_literal" -C 1  # ✅ Pattern literal simples
```

### 💡 Princípios de Busca
- ✅ Patterns simples e literais
- ✅ PowerShell para lógica condicional
- ✅ Measure-Object para contagens
- ✅ Evitar expressões calculadas complexas
- ✅ Comandos simples > Expressões calculadas

### ⏱️ ROI
**Economia:** 5-10 min por verificação (evita 3-4 tentativas falhadas)
```

**ROI:** Verificação automatizada economiza **5-10 min** por verificação de qualidade.

---

### **5.2 Checklist de Auditoria**

```markdown
## 📊 CHECKLIST DE AUDITORIA DE DOCUMENTAÇÃO

### Meta-informação (10 pontos)
- [ ] Frontmatter YAML completo (title, type, categories, etc)
- [ ] Versão documentada
- [ ] Data última atualização
- [ ] Changelog presente
- [ ] README em samples com metadados

### Navegabilidade (10 pontos)
- [ ] Índice/TOC presente
- [ ] Links internos funcionais
- [ ] Links para docs relacionados
- [ ] Quick Search Matrix (em índices)
- [ ] Guias de uso rápido por cenário

### Conteúdo (10 pontos)
- [ ] Exemplos de código funcionais
- [ ] ROI documentado (quando aplicável)
- [ ] Troubleshooting guide
- [ ] Palavras-chave para busca semântica
- [ ] Golden Standards identificados

### Qualidade (10 pontos)
- [ ] 0 links quebrados
- [ ] Formatação markdown correta
- [ ] Código com syntax highlighting
- [ ] Screenshots (quando aplicável)
- [ ] Cross-references corretas

**Score:** [X]/40 pontos
**Threshold:** ≥35/40 (87.5%) para aprovar
```

**ROI:** Checklist de auditoria economiza **30-60 min** de revisão manual.

---

## ESTRATÉGIA 6: Atualização Contínua

### **Conceito**

Documentação **viva** que evolui com o projeto, não apenas gerada no final.

### **6.1 Versionamento**

```markdown
## 📝 CHANGELOG

### v[X.Y] - YYYY-MM-DD ([Descrição da Versão])
**✨ Adições:**
- ✅ [Feature A]: [descrição]
- ✅ [Feature B]: [descrição]

**🔧 Modificações:**
- 🔄 [Mudança A]: [descrição]
- 🔄 [Mudança B]: [descrição]

**🐛 Correções:**
- ✅ [Bug A]: [descrição]

**📊 Métricas:**
- Score Auditoria: [X]% → [Y]% (após [N] correções)
- ROI: [impacto da versão]

---

### v[X.Y-1] - YYYY-MM-DD ([Versão Anterior])
[estrutura similar]
```

**ROI:** Changelog economiza **10-15 min** de rastreamento de mudanças.

---

### **6.2 Frontmatter YAML**

```markdown
---
alwaysApply: [true/false]
title: "[Título do Documento]"
description: "[Descrição breve quando aplicar esta rule]"
type: "[guide/reference/tutorial/template]"
categories: [cat1, cat2, cat3]
apis: [API1, API2, API3]
capabilities: [CAP-001, CAP-002]
use_cases: [caso1, caso2, caso3]
complexity: [beginner/intermediate/advanced/expert]
keywords: [keyword1, keyword2, keyword3]
estimated_read_time: [minutos]
last_updated: "YYYY-MM-DD"
version: "X.Y"
related_rules: 
  - "rule-A.mdc"
  - "rule-B.mdc"
tags: 
  - "tag1"
  - "tag2"
---
```

**ROI:** Frontmatter YAML economiza **50-70% tempo** em discovery (permite filtros automáticos).

---

## WORKFLOW: ADICIONAR NOVO DOCUMENTO

### **Conceito**

Processo estruturado em **9 etapas** para integrar novos documentos na knowledge base, garantindo que o agente fique **consciente** do novo conteúdo imediatamente.

### **7.1 Workflow Completo**

```
NOVO DOCUMENTO
    ↓
1. 📄 DETECÇÃO
   → Usuário adiciona doc em knowledge_base/
   → Executa: "INTEGRAR_NOVO_DOCUMENTO <path>"
    ↓
2. 🔍 ANÁLISE (7 dimensões)
   → Tipo, Complexidade, Conceitos-chave
   → Tags, Capabilities, Dependencies, Golden Status
    ↓
3. 📝 VERSIONAMENTO
   → Adiciona v1.0 + Changelog + Frontmatter YAML
    ↓
4. 🗂️ ATUALIZAÇÃO DE ÍNDICES
   → TAGS_INDEX.md
   → knowledge-map.mdc
   → capabilities-catalog.mdc (se aplicável)
    ↓
5. 📘 ATUALIZAÇÃO DE RULES
   → Rules especializadas (se padrões validados)
   → Core rule (se descoberta crítica)
    ↓
6. ✅ VALIDAÇÃO (5 testes)
   → Semantic Search, Index Consistency
   → Cross-Reference, Quick Access, ROI
    ↓
7. 💾 MEMÓRIA PERSISTENTE
   → Cria memória do novo doc
    ↓
8. 📊 DOCUMENTAÇÃO
   → Atualiza changelog do índice
   → Registra integração
    ↓
9. ✅ CONCLUSÃO
   → Knowledge base atualizada e consciente
```

**⏱️ Tempo estimado:** 15-20 min por documento  
**🎯 ROI:** Zero drift entre docs e índices, KB sempre atualizada

---

### **7.2 Etapa 1: Detecção**

#### **Gatilho Manual (Recomendado)**

```bash
# Usuário executa no terminal ou via prompt
"INTEGRAR_NOVO_DOCUMENTO <path_do_documento>"

# Exemplo:
"INTEGRAR_NOVO_DOCUMENTO knowledge_base/Docs/NewAPIGuide.md"
```

#### **Checklist Pré-Integração**

- [ ] Documento está salvo em `knowledge_base/`
- [ ] Nome do arquivo segue padrão (CamelCase ou snake_case)
- [ ] Documento tem conteúdo mínimo (não está vazio)
- [ ] Path completo está disponível

---

### **7.3 Etapa 2: Análise (7 Dimensões)**

O agente deve executar **7 análises obrigatórias**:

#### **2.1 Tipo do Documento**

```markdown
Categorias possíveis:
- 📘 API Reference (guia técnico de APIs)
- 📖 Tutorial (passo-a-passo educacional)
- 🔬 Sample (código funcional de exemplo)
- 📋 Guide (guia de implementação)
- 🛠️ Tool (ferramenta/script automatizado)
- 📊 Report (relatório/análise)
- 🎯 Template (modelo reutilizável)
```

#### **2.2 Complexidade**

```markdown
- 🟢 Beginner: <100 linhas, conceitos básicos
- 🟡 Intermediate: 100-500 linhas, múltiplos conceitos
- 🟠 Advanced: 500-1000 linhas, arquitetura complexa
- 🔴 Expert: >1000 linhas, domínio especializado
```

#### **2.3 Conceitos-Chave**

```markdown
Extrair 5-10 conceitos principais:
- APIs mencionadas (ex: TransactionManager, DocumentManager)
- Classes principais (ex: IExtensionApplication, IRule)
- Padrões de design (ex: Factory, Strategy, Singleton)
- Tecnologias (ex: .NET Framework 4.7, COM Interop)
```

#### **2.4 Tags Relevantes**

```markdown
Identificar 5-15 tags para TAGS_INDEX:
- Tags técnicas: API names, technology stack
- Tags funcionais: use cases, capabilities
- Tags de contexto: domain, industry
```

#### **2.5 Capabilities Relacionadas**

```markdown
Mapear para CAP-XXX existentes ou propor nova:
- Qual capability este doc suporta?
- Habilita nova capability?
- Melhora capability existente?
```

#### **2.6 Dependencies**

```markdown
Identificar pré-requisitos:
- Documentos que devem ser lidos antes
- Samples necessários
- Rules relacionadas
```

#### **2.7 Golden Standard Status**

```markdown
Avaliar se é exemplo de referência:
- ✅ Production-validated (testado 5-10x)
- ✅ Best practices implementadas
- ✅ Documentação completa
- ✅ Código reusável (>70%)
```

#### **Template de Análise**

```yaml
---
analysis_result:
  document: "[path]"
  type: "[API Reference/Tutorial/Sample/Guide/Tool/Report/Template]"
  complexity: "[Beginner/Intermediate/Advanced/Expert]"
  key_concepts:
    - "[Conceito 1]"
    - "[Conceito 2]"
    - "[Conceito 3]"
  tags:
    - "[tag1]"
    - "[tag2]"
    - "[tag3]"
  capabilities:
    - "CAP-XXX: [descrição]"
  dependencies:
    - "[Doc A]"
    - "[Doc B]"
  golden_standard: [true/false]
  golden_reasons:
    - "[Razão 1]"
    - "[Razão 2]"
---
```

---

### **7.4 Etapa 3: Versionamento**

#### **3.1 Adicionar Frontmatter YAML**

```yaml
---
title: "[Título do Documento]"
description: "[Descrição breve]"
type: "[tipo identificado na análise]"
categories: [cat1, cat2]
complexity: "[Beginner/Intermediate/Advanced/Expert]"
keywords: [kw1, kw2, kw3]
estimated_read_time: [minutos]
last_updated: "YYYY-MM-DD"
version: "1.0"
related_docs: 
  - "[Doc A]"
  - "[Doc B]"
capabilities:
  - "CAP-XXX"
tags: 
  - "tag1"
  - "tag2"
golden_standard: [true/false]
---
```

#### **3.2 Adicionar Changelog Inicial**

```markdown
## 📝 CHANGELOG

### v1.0 - DD/MM/YYYY (Versão Inicial)
- ✅ Documento criado e integrado à knowledge base
- ✅ Análise completa: [Tipo], [Complexidade], [X] conceitos-chave
- ✅ Mapeamento: [Y] tags, [Z] capabilities relacionadas
- ✅ Golden Standard: [Sim/Não]
- 📊 Adicionado aos índices: TAGS_INDEX, Knowledge Map
- 🔗 Dependencies identificadas: [lista]
```

#### **3.3 Versionamento Futuro**

```markdown
## 📋 REGRAS DE VERSIONAMENTO

**Patch (v1.0 → v1.1):**
- Correções de bugs
- Typos/formatação
- Links quebrados

**Minor (v1.0 → v1.1, v1.1 → v1.2):**
- Novas seções
- Exemplos adicionais
- Melhorias incrementais

**Major (v1.X → v2.0):**
- Reestruturação completa
- Breaking changes
- Mudança de approach técnico
```

---

### **7.5 Etapa 4: Atualização de Índices**

#### **4.1 TAGS_INDEX.md**

```markdown
## ATUALIZAÇÃO DO TAGS_INDEX

**Ações:**
1. Adicionar novo doc na seção apropriada:
   - 📂 Por Categoria (APIs, Guides, Samples, etc)
   - 🏷️ Por Tag (cada tag individual)
   - 📊 Por Complexidade (Beginner/Intermediate/Advanced)
   - 🎯 Por Capability (CAP-XXX)

2. Atualizar contadores:
   - Total de documentos na categoria
   - Total de docs por tag

3. Atualizar Quick Search Matrix:
   - Adicionar entrada se for Golden Standard

4. Incrementar changelog do TAGS_INDEX:
   ```yaml
   ### vX.Y - DD/MM/YYYY
   - ✅ Adicionado [Nome Doc] em [Categorias]
   - 📊 Tags atualizadas: [lista]
   - 🎯 Capabilities: [lista]
   ```
```

#### **4.2 knowledge-map.mdc**

```markdown
## ATUALIZAÇÃO DO KNOWLEDGE MAP

**Ações:**
1. Adicionar entrada na categoria apropriada:
   ```markdown
   #### **📘 [Nome do Documento]**
   - **Tipo:** [tipo]
   - **Uso:** [quando usar]
   - **Quando usar:** [contextos]
   - **Conceitos-chave:** [lista]
   - **Casos práticos:** [exemplos]
   - **Pré-requisitos:** [dependencies]
   - **📖 README:** [path] (se for sample)
   ```

2. Atualizar matrizes de decisão:
   - Matriz "Objetivo → Documento Principal"
   - Guias de uso rápido por cenário

3. Atualizar Golden Standards (se aplicável):
   ```markdown
   ### ⭐ [Nome Doc] - BEST para [Caso de Uso]
   - **Por quê:** [justificativa]
   - **Use quando:** [contextos]
   - **Path:** [caminho]
   - **README:** [path]
   ```

4. Incrementar changelog do Knowledge Map
```

#### **4.3 capabilities-catalog.mdc (Se Aplicável)**

```markdown
## ATUALIZAÇÃO DO CAPABILITIES CATALOG

**Ações SE o documento habilita/melhora capability:**

1. Atualizar CAP-XXX existente:
   ```markdown
   ### CAP-XXX: [Nome da Capability]
   ...
   **📚 Documentação:**
   - [Doc existente]
   - **[NOVO DOC]** ⭐ NOVO
   ```

2. Criar nova capability (se necessário):
   ```markdown
   ### CAP-XXX: [Nova Capability]
   **Descrição:** [o que faz]
   **Complexidade:** [nível]
   **Tempo estimado:** [range]
   **ROI:** [benefícios]
   **API Type:** [.NET/COM/Hybrid]
   **Maturity:** [Alpha/Beta/Stable]
   **📚 Documentação:** [novo doc]
   ```

3. Incrementar changelog do Catalog
```

---

### **7.6 Etapa 5: Atualização de Rules**

#### **Quando Atualizar Rules?**

```markdown
✅ ATUALIZAR RULES SE:
- Documento valida NOVO PADRÃO técnico
- Documento identifica ANTIPADRÃO importante
- Documento economiza >15 min (descoberta crítica)
- Documento é Golden Standard production-validated

❌ NÃO ATUALIZAR RULES SE:
- Apenas documentação adicional
- Sem padrões novos validados
- Redundante com docs existentes
```

#### **5.1 Rules Especializadas**

```markdown
**Exemplo: @[domain]-api.mdc**

1. Adicionar referência ao novo doc:
   ```markdown
   ### Pattern Validado: [Nome do Pattern]
   **Fonte:** [Novo Doc] ⭐ NOVO
   **Uso:** [quando aplicar]
   **Código:**
   ```[language]
   [código do pattern]
   ```
   **ROI:** [economia]
   ```

2. Incrementar versão da rule:
   ```yaml
   version: "X.Y → X.Y+1"
   ```

3. Atualizar changelog da rule
```

#### **5.2 Core Rule (Router Central)**

```markdown
**Exemplo: @[domain]-core.mdc**

SE for DESCOBERTA CRÍTICA (>15 min economia):

1. Adicionar em "Lições de Produção Validadas":
   ```markdown
   ### X. ⚡ [Nome da Lição] ([Y] min economizados)
   **Descoberta:** [descrição]
   **Solução:** [código/approach]
   **Fonte:** [Novo Doc]
   **ROI:** [economia]
   ```

2. Atualizar contador de lições (Top 5 → Top 6)

3. Atualizar ROI total do workflow

4. Incrementar versão e changelog da core rule
```

---

### **7.7 Etapa 6: Validação (5 Testes)**

#### **6.1 Semantic Search Test**

```markdown
**Objetivo:** Verificar se busca semântica retorna novo doc

**Teste:**
1. Executar codebase_search com conceito-chave do novo doc
2. Verificar se novo doc aparece nos resultados
3. Verificar relevância do snippet retornado

**Critério de Sucesso:** Novo doc aparece em top 5 resultados
```

#### **6.2 Index Consistency Test**

```markdown
**Objetivo:** Verificar integridade de links e referências

**Teste:**
1. Verificar todos os links para o novo doc:
   - No TAGS_INDEX
   - No Knowledge Map
   - No Capabilities Catalog
   - Nas Rules (se aplicável)

2. Usar comando PowerShell:
   ```powershell
   Select-String -Path "*.md*" -Pattern "[nome_do_doc]" -Recurse
   ```

**Critério de Sucesso:** 0 links quebrados, todos paths corretos
```

#### **6.3 Cross-Reference Test**

```markdown
**Objetivo:** Verificar bidirecionalidade de referências

**Teste:**
1. Se novo doc menciona CAP-XXX:
   → Verificar se CAP-XXX menciona novo doc

2. Se novo doc menciona Sample Y:
   → Verificar se Sample Y README menciona novo doc (se relevante)

3. Se novo doc menciona Rule Z:
   → Verificar se Rule Z menciona novo doc

**Critério de Sucesso:** Todas referências bidirecionais corretas
```

#### **6.4 Quick Access Test**

```markdown
**Objetivo:** Simular usuário buscando info do novo doc

**Teste:**
1. Usuário diz: "[preciso fazer X, que é o tema do novo doc]"
2. Agente executa workflow:
   - Sequential Thinking (identifica necessidade)
   - Discovery (TAGS_INDEX/Capabilities)
   - Navigation (Knowledge Map)
   - **NOVO DOC aparece como solução**
3. Verificar se workflow leva ao doc em <3 steps

**Critério de Sucesso:** Novo doc descoberto em ≤3 steps
```

#### **6.5 ROI Validation**

```markdown
**Objetivo:** Verificar se ROI foi calculado e documentado

**Teste (se doc adiciona capability/pattern):**
1. Verificar se tempo estimado foi documentado
2. Verificar se economia de tempo foi calculada
3. Verificar se complexidade está clara

**Critério de Sucesso:** ROI documentado ou N/A justificado
```

#### **Template de Relatório de Validação**

```yaml
---
validation_report:
  document: "[path]"
  date: "YYYY-MM-DD"
  tests:
    semantic_search:
      status: "[✅ Pass / ❌ Fail]"
      notes: "[observações]"
    index_consistency:
      status: "[✅ Pass / ❌ Fail]"
      broken_links: [N]
    cross_reference:
      status: "[✅ Pass / ❌ Fail]"
      missing_refs: [N]
    quick_access:
      status: "[✅ Pass / ❌ Fail]"
      steps_to_discover: [N]
    roi_validation:
      status: "[✅ Pass / ❌ Fail / N/A]"
      roi_documented: [true/false]
  overall: "[✅ APPROVED / ⚠️ CONDITIONAL / ❌ REJECTED]"
  issues: [lista de problemas encontrados]
  fixes_applied: [lista de correções]
---
```

---

### **7.8 Etapa 7: Memória Persistente**

```markdown
**Objetivo:** Criar memória para o agente lembrar do novo doc

**Usar ferramenta:** `update_memory`

**Estrutura da Memória:**

```json
{
  "action": "create",
  "title": "[Nome do Documento] - Integrado [DD/MM/YYYY]",
  "knowledge_to_store": "[Tipo] adicionado à knowledge base em [path]. Cobre [conceitos-chave]. Complexidade: [nível]. Relacionado a [capabilities]. Golden Standard: [Sim/Não]. Use quando [contextos]. Economiza [X] min em [casos de uso]."
}
```

**Exemplo Real:**

```json
{
  "action": "create",
  "title": "Advanced Joints API Guide - Integrado 04/10/2025",
  "knowledge_to_store": "API Reference adicionado em knowledge_base/Docs/AdvancedJointsAPI.md. Cobre IRule avançado, geometria complexa, cálculos estruturais. Complexidade: Advanced. Relacionado a CAP-002 (Joints Customizados). Golden Standard: Sim. Use quando criar joints parametrizados >500 linhas. Economiza 60-90 min em desenvolvimento de connections complexas."
}
```

---

### **7.9 Etapa 8: Documentação**

#### **8.1 Atualizar Changelog dos Índices**

```markdown
**TAGS_INDEX.md:**
### vX.Y - DD/MM/YYYY
- ✅ Adicionado [Nome Doc] ([N] tags, [M] capabilities)
- 📊 Total documentos: [antigo] → [novo]

**knowledge-map.mdc:**
### vX.Y - DD/MM/YYYY
- ✅ Adicionado [Nome Doc] em categoria [Cat]
- 📊 Atualizado [N] matrizes de decisão
- ⭐ Golden Standard atualizado (se aplicável)

**capabilities-catalog.mdc (se aplicável):**
### vX.Y - DD/MM/YYYY
- ✅ CAP-XXX atualizado com novo doc
- 📚 Total docs: [antigo] → [novo]
```

#### **8.2 Criar Entrada no Integration Log**

```markdown
## 📊 INTEGRATION LOG (criar se não existir)

### [Nome do Documento] - DD/MM/YYYY

**Status:** ✅ Integrado com sucesso

**Análise:**
- Tipo: [tipo]
- Complexidade: [nível]
- Conceitos-chave: [lista]
- Tags: [lista]
- Capabilities: [lista]

**Atualizações Realizadas:**
- [x] TAGS_INDEX v[old] → v[new]
- [x] Knowledge Map v[old] → v[new]
- [x] Capabilities Catalog v[old] → v[new] (N/A)
- [x] Rules atualizadas: [lista ou N/A]
- [x] Memória persistente criada

**Validação:**
- Semantic Search: ✅
- Index Consistency: ✅
- Cross-Reference: ✅
- Quick Access: ✅ ([N] steps)
- ROI: ✅ / N/A

**Métricas:**
- Tempo de integração: [X] min
- Issues encontradas: [N]
- Fixes aplicadas: [N]

**Próximos Passos:**
- [ ] [Ação 1, se houver]
- [ ] [Ação 2, se houver]
```

---

### **7.10 Etapa 9: Conclusão**

#### **Checklist Final**

```markdown
## ✅ CHECKLIST DE INTEGRAÇÃO COMPLETA

### Documento
- [ ] Frontmatter YAML adicionado com versão v1.0
- [ ] Changelog inicial criado
- [ ] Conteúdo revisado e formatado

### Análise
- [ ] 7 dimensões analisadas (Tipo, Complexidade, Conceitos, Tags, Capabilities, Dependencies, Golden Status)
- [ ] Metadata documentado em YAML

### Índices
- [ ] TAGS_INDEX.md atualizado (versão incrementada)
- [ ] knowledge-map.mdc atualizado (versão incrementada)
- [ ] capabilities-catalog.mdc atualizado (se aplicável)

### Rules
- [ ] Rules especializadas atualizadas (se aplicável)
- [ ] Core rule atualizada (se descoberta crítica)

### Validação
- [ ] 5 testes executados (Semantic Search, Index Consistency, Cross-Ref, Quick Access, ROI)
- [ ] Relatório de validação gerado
- [ ] Issues corrigidas

### Registro
- [ ] Memória persistente criada
- [ ] Integration Log atualizado
- [ ] Changelogs dos índices atualizados

### Comunicação
- [ ] Usuário informado da conclusão
- [ ] Resumo da integração fornecido
- [ ] Próximos passos (se houver) comunicados
```

#### **Mensagem de Conclusão para o Usuário**

```markdown
✅ **INTEGRAÇÃO CONCLUÍDA COM SUCESSO!**

📄 **Documento:** [Nome do Documento]  
📂 **Path:** [path]  
🏷️ **Tipo:** [tipo] | **Complexidade:** [nível]  
⏱️ **Tempo de integração:** [X] min  

**📊 Atualizações Realizadas:**
- ✅ TAGS_INDEX v[old] → v[new] ([N] tags adicionadas)
- ✅ Knowledge Map v[old] → v[new] (categoria [Cat])
- ✅ Capabilities [lista] atualizadas
- ✅ [N] rules atualizadas
- ✅ Memória persistente criada

**🎯 Capabilities Relacionadas:**
- [CAP-XXX]: [descrição]
- [CAP-YYY]: [descrição]

**🔍 Como Usar:**
1. Semantic search: "[conceito-chave]"
2. Via Knowledge Map: Seção [categoria]
3. Via TAGS_INDEX: Tags [lista]

**💡 Golden Standard:** [Sim/Não]  
**⏱️ ROI:** Economiza [X] min em [casos de uso]  

**✅ Validação:** Todos os 5 testes passaram  
**🐛 Issues:** [N] encontradas e corrigidas  

🎉 Knowledge base agora está **consciente** deste documento!
```

---

### **7.11 Automação (Opcional)**

#### **Script de Integração Semi-Automatizado**

```markdown
## 🤖 SCRIPT DE INTEGRAÇÃO (FUTURO)

**Conceito:** Automatizar partes repetitivas do workflow

**Fases Automatizáveis:**
1. ✅ Detecção de arquivo novo (file watcher)
2. ✅ Extração de conceitos-chave (NLP/AI)
3. ✅ Geração de tags (AI-assisted)
4. ✅ Criação de frontmatter YAML (template)
5. ✅ Atualização de contadores em índices
6. ⚠️ Validação de links (semi-automática)

**Fases Manuais (Expertise Necessária):**
- ❌ Avaliação de Golden Standard
- ❌ Decisão sobre atualização de rules
- ❌ Cálculo de ROI
- ❌ Mapeamento de capabilities

**ROI Potencial:** 60-70% automação → 6-8 min por doc (vs 15-20 min manual)
```

---

### **7.12 Troubleshooting**

#### **Problema 1: Semantic Search não retorna novo doc**

**Causa:** Embeddings não atualizados  
**Solução:** Aguardar reindexação automática ou forçar reindex (depende da ferramenta)

---

#### **Problema 2: Links quebrados após integração**

**Causa:** Path relativo incorreto  
**Solução:** Usar sempre paths relativos a partir da raiz do workspace

---

#### **Problema 3: Índices desatualizados**

**Causa:** Esquecimento de atualizar algum índice  
**Solução:** Usar checklist de integração completa (Etapa 9)

---

#### **Problema 4: Novo doc não aparece em Quick Access**

**Causa:** Knowledge Map não atualizado ou categoria errada  
**Solução:** Revisar matriz de decisão e guias de uso rápido no Knowledge Map

---

### **7.13 Exemplo Prático Completo**

```markdown
## 📖 EXEMPLO: Integrar "Advanced Bolt Patterns API.md"

**1. DETECÇÃO:**
```bash
Usuário: "INTEGRAR_NOVO_DOCUMENTO knowledge_base/Docs/AdvancedBoltPatternsAPI.md"
```

**2. ANÁLISE:**
```yaml
type: "API Reference"
complexity: "Advanced"
key_concepts:
  - "BoltPattern.Create()"
  - "Parametric anchors"
  - "Custom arrangements"
tags:
  - "bolts"
  - "connections"
  - "COM-API"
  - "advanced"
capabilities:
  - "CAP-002: Joints Customizados"
dependencies:
  - "COM API Reference Guide"
  - "BridgeGirder Sample"
golden_standard: true
golden_reasons:
  - "Production-validated em 3 projetos"
  - "Código reusável 85%"
```

**3. VERSIONAMENTO:**
- Frontmatter YAML adicionado
- Changelog v1.0 criado

**4. ATUALIZAÇÃO DE ÍNDICES:**
- TAGS_INDEX: v2.1 → v2.2
  - Adicionado em "Bolts", "Connections", "COM-API", "Advanced"
- Knowledge Map: v1.5 → v1.6
  - Adicionado em "APIs & Desenvolvimento" → "Advance Steel COM API Reference Guide"
  - Adicionado em "Golden Standards" → "⭐ Advanced Bolt Patterns - BEST para Connections Complexas"
- Capabilities: v1.2 → v1.3
  - CAP-002 atualizado: "📚 Documentação: ... + Advanced Bolt Patterns API ⭐ NOVO"

**5. ATUALIZAÇÃO DE RULES:**
- @advance-steel-com-api.mdc v1.4 → v1.5
  - Adicionado pattern "Bolt Arrangements Parametrizados"
  - Referência ao novo doc

**6. VALIDAÇÃO:**
- Semantic Search: ✅ (top 3 para "bolt patterns advanced")
- Index Consistency: ✅ (0 links quebrados)
- Cross-Reference: ✅ (CAP-002 ↔ novo doc, BridgeGirder ↔ novo doc)
- Quick Access: ✅ (2 steps: Sequential Thinking → Knowledge Map → Doc)
- ROI: ✅ (60-90 min economizados em connections complexas)

**7. MEMÓRIA PERSISTENTE:**
```json
{
  "title": "Advanced Bolt Patterns API - Integrado 04/10/2025",
  "knowledge_to_store": "API Reference adicionado em knowledge_base/Docs/AdvancedBoltPatternsAPI.md. Cobre BoltPattern.Create(), parametric anchors, custom arrangements. Complexidade: Advanced. Relacionado a CAP-002. Golden Standard: Sim (prod-validated 3 projetos, 85% reusável). Use quando criar connections complexas com >10 bolts. Economiza 60-90 min."
}
```

**8. DOCUMENTAÇÃO:**
- Integration Log atualizado
- Changelogs dos 3 índices atualizados

**9. CONCLUSÃO:**
```
✅ INTEGRAÇÃO CONCLUÍDA COM SUCESSO!

📄 Documento: Advanced Bolt Patterns API
📂 Path: knowledge_base/Docs/AdvancedBoltPatternsAPI.md
🏷️ Tipo: API Reference | Complexidade: Advanced
⏱️ Tempo de integração: 18 min

📊 Atualizações:
- ✅ TAGS_INDEX v2.1 → v2.2 (4 tags)
- ✅ Knowledge Map v1.5 → v1.6 (categoria "APIs & Desenvolvimento")
- ✅ Capabilities CAP-002 atualizado
- ✅ 1 rule atualizada (@com-api.mdc v1.4 → v1.5)
- ✅ Memória persistente criada

🎯 Capabilities: CAP-002 (Joints Customizados)
🔍 Como Usar: Semantic search "bolt patterns advanced", Knowledge Map → "APIs & Desenvolvimento", TAGS_INDEX → "bolts"

💡 Golden Standard: Sim (prod-validated, 85% reusável)
⏱️ ROI: 60-90 min em connections complexas

✅ Validação: 5/5 testes OK | Issues: 0

🎉 Knowledge base consciente do documento!
```
```

---

### **📊 Métricas do Workflow**

| **Métrica** | **Target** | **Real (Exemplo)** | **Status** |
|---|---|---|---|
| Tempo de integração | 15-20 min | 18 min | 🟢 |
| Índices atualizados | 3 | 3 | 🟢 |
| Testes de validação | 5/5 | 5/5 | 🟢 |
| Links quebrados | 0 | 0 | 🟢 |
| Memória criada | Sim | Sim | 🟢 |

---

### **🎯 ROI do Workflow**

| **Benefício** | **Economia/Impacto** |
|---|---|
| Zero drift entre docs e índices | ✅ KB sempre atualizada |
| Descoberta rápida de novo conteúdo | 50-70% redução tempo busca |
| Memória persistente do agente | Zero re-análise de docs |
| Validação sistemática | 90% redução links quebrados |
| **Total por documento** | **15-20 min investidos, ROI contínuo** |

---

## COMO IMPLEMENTAR EM SEU PROJETO

### **Fase 0: Preparação (30 min)**

1. **Criar estrutura de pastas:**
   ```
   .cursor/rules/
   knowledge_base/Docs/
   knowledge_base/Samples/Projects/
   knowledge_base/Audits/
   ```

2. **Adaptar templates** deste documento:
   - Substituir `[domain]` pelo nome do seu domínio (ex: `react`, `python-ml`, `devops`)
   - Substituir `[SEU PROJETO]` pelo nome do projeto
   - Adaptar categorias às suas necessidades

---

### **Fase 1: Router Central (2h)**

**Criar:** `.cursor/rules/[domain]-core.mdc` (always-applied)

**Conteúdo mínimo:**
- Índice navegável
- Workflow obrigatório (7 steps)
- Mapa de Rules (quando usar cada uma)
- Localização das rules
- Guia rápido por cenário (3-5 cenários principais)
- Matriz de decisão: Problema → Rule

**Templates:** Ver "ESTRATÉGIA 1.1"

---

### **Fase 2: Knowledge Map (2h)**

**Criar:** `.cursor/rules/[domain]-knowledge-map.mdc`

**Conteúdo mínimo:**
- Documentação por categoria (5-10 categorias)
- Golden Standards (3-5 samples referência)
- Guias de uso rápido por cenário (5-10 workflows)
- Matriz de decisão rápida (8-10 objetivos)
- Troubleshooting guide (7-10 problemas comuns)
- Palavras-chave para busca semântica (6-10 categorias)

**Templates:** Ver "ESTRATÉGIA 1.2"

---

### **Fase 3: Capabilities Catalog (4h)**

**Criar:** `.cursor/rules/[domain]-capabilities-catalog.mdc`

**Conteúdo mínimo:**
- Taxonomia de capabilities (5 categorias, classificação complexidade)
- Índice navegável (Quick Reference Table)
- Por categoria (5 categorias)
- Por ROI (3-4 tiers)
- Capabilities individuais (capabilities/CAP-XXX.md)

**Templates:** Ver "ESTRATÉGIA 1.3"

---

### **Fase 4: Quick Reference Cards (2h)**

**Criar:** `.cursor/rules/[domain]-quick-refs.mdc`

**Conteúdo mínimo:**
- 4-6 Quick Refs (1 página cada)
- Código essencial (10-20 linhas)
- Parâmetros críticos (tabela)
- Troubleshooting (tabela)
- Ver também (cross-references)
- Matriz de Quick Ref

**Templates:** Ver "ESTRATÉGIA 1.4"

---

### **Fase 5: TAGS_INDEX (3h)**

**Criar:** `knowledge_base/Docs/TAGS_INDEX.md`

**Conteúdo mínimo:**
- Tags principais (A-Z) com docs/samples
- Tags por categoria
- Docs por complexidade
- Samples por complexidade
- Capabilities mapeadas
- Quick Search Matrix
- Learning Paths

**Templates:** Ver "ESTRATÉGIA 2.1"

---

### **Fase 6: READMEs em Samples (1h por sample)**

**Para cada sample importante:**

**Criar:** `knowledge_base/Samples/Projects/[Sample]/README.md`

**Conteúdo mínimo:**
- Frontmatter YAML (metadados)
- Overview (1-2 parágrafos)
- Quando usar (3-5 cenários)
- Quick start (código exemplo)
- Conceitos demonstrados
- Tempo estimado
- Documentação relacionada

**Templates:** Ver "ESTRATÉGIA 2.2"

---

### **Fase 7: Lições & Antipadrões (ongoing)**

**Criar:** `.cursor/rules/[domain]-troubleshooting.mdc`

**Conteúdo mínimo:**
- Top 5-10 lições validadas (com ROI)
- Checklist antipadrões (20 itens)
- Template @prompt_licao_aprendida.md

**Workflow:**
- A cada projeto: documentar learnings em @prompt_licao_aprendida.md
- A cada 3-5 projetos: consolidar em troubleshooting.mdc
- Atualizar checklist antipadrões conforme novos antipadrões descobertos

**Templates:** Ver "ESTRATÉGIA 4"

---

### **Fase 8: Ferramentas & Auditoria (1h)**

**Criar:** Seção "Ferramentas & Auditoria" no router central

**Conteúdo mínimo:**
- Scripts de verificação (links, lints)
- Checklist de auditoria (40 pontos)
- Automações úteis

**Templates:** Ver "ESTRATÉGIA 5"

---

### **Fase 9: Vibe Planning (opcional, 2h)**

**Se projetos complexos (≥60 min):**

**Criar:** `.cursor/rules/[domain]-vibe-planning.mdc`

**Conteúdo mínimo:**
- 5 fases do workflow
- PRD evolutivo (12 seções)
- 10 checkpoints
- Checklists por tipo de projeto (4 tipos)
- Comandos (para, retomar, atualizar)

**Templates:** Ver "ESTRATÉGIA 3.2"

---

## TEMPLATES REUTILIZÁVEIS

### **Template: Router Central**

```markdown
---
alwaysApply: true
last_updated: "YYYY-MM-DD"
version: "1.0"
---

# 🧠 [SEU PROJETO] - CORE RULES

## 📋 ÍNDICE
1. [Workflow Obrigatório](#workflow-obrigatório)
2. [Lições de Produção](#lições-de-produção)
3. [Mapa de Rules](#mapa-de-rules)
4. [Guia por Cenário](#guia-por-cenário)
5. [Localização Rules](#localização-das-rules)

## 🚨 WORKFLOW OBRIGATÓRIO
[Ver ESTRATÉGIA 3.1]

## 🎯 LIÇÕES DE PRODUÇÃO
[Ver ESTRATÉGIA 4]

## 🗺️ MAPA DE RULES
[Ver ESTRATÉGIA 1.1]

## 🎯 GUIA POR CENÁRIO
[Ver ESTRATÉGIA 1.1]

## 📚 LOCALIZAÇÃO DAS RULES
[Ver ESTRATÉGIA 1.1]

## 📝 CHANGELOG
[Ver ESTRATÉGIA 6.1]
```

---

### **Template: Capability Individual**

```markdown
---
capability_id: "CAP-XXX"
title: "[Nome da Capability]"
category: "[categoria]"
complexity: "⭐⭐⭐"
estimated_time: "[X-Y]h"
roi: "[Z]h/ano"
priority: "[P0/P1/P2]"
status: "[experimental/stable/production]"
---

# CAP-XXX: [Nome da Capability]

## 📋 Overview
[Descrição 1-2 parágrafos]

## 🎯 Casos de Uso [SEU CONTEXTO]
1. [Caso A]: [descrição]
2. [Caso B]: [descrição]

## 🔧 APIs Necessárias
- [API 1]: [para que serve]
- [API 2]: [para que serve]

## 💻 Código Exemplo Completo
```[linguagem]
[código funcional]
```

## 📊 Estimativas
| Métrica | Valor |
|---|---|
| Tempo dev 1ª vez | [X-Y]h |
| Tempo dev experiente | [A-B]h |
| ROI conservador | [Z]h/ano |
| ROI agressivo | [W]h/ano |
| Break-even | [N] usos |

## 🎓 Pré-requisitos
- [Req 1]
- [Req 2]

## 📚 Documentação Relacionada
- [Doc A]: [quando consultar]
- [Sample B]: [quando usar]

## 🔗 [Voltar ao Catálogo](../[domain]-capabilities-catalog.mdc)
```

---

### **Template: Quick Ref**

```markdown
## QR-XXX: [Nome da Tarefa]

**Quando usar:** [descrição]
**APIs principais:** [lista]
**Complexidade:** ⭐⭐
**Tempo:** [X-Y] min

### Código Essencial
```[linguagem]
[código mínimo 10-20 linhas]
```

### Parâmetros Críticos
| Parâmetro | Tipo | Descrição | Exemplo |
|---|---|---|---|
| [param1] | [tipo] | [desc] | [ex] |

### Troubleshooting
| Erro | Causa | Solução |
|---|---|---|
| [erro1] | [causa] | [solução] |

### 💡 Dica: [Algo Útil]
```[linguagem]
[código tip]
```

### 📚 Ver também
- [Doc X] → [quando consultar]
- [Sample Y] → [quando usar]
```

---

## CHECKLIST DE IMPLEMENTAÇÃO

### **Fase 0: Preparação**
- [ ] Criar estrutura de pastas (.cursor/rules/, knowledge_base/)
- [ ] Adaptar templates substituindo `[domain]`, `[SEU PROJETO]`
- [ ] Definir categorias principais do seu domínio (5-10 categorias)

### **Fase 1: Router Central (2h)**
- [ ] Criar [domain]-core.mdc (always-applied)
- [ ] Índice navegável completo
- [ ] Workflow obrigatório (7 steps)
- [ ] Mapa de Rules inicial (mesmo que com 2-3 rules)
- [ ] 3-5 cenários principais

### **Fase 2: Knowledge Map (2h)**
- [ ] Criar [domain]-knowledge-map.mdc
- [ ] Categorias por tipo de doc (5-10 categorias)
- [ ] Identificar 3-5 Golden Standards
- [ ] 5-10 workflows por cenário
- [ ] Troubleshooting guide (7-10 problemas)

### **Fase 3: Capabilities Catalog (4h)**
- [ ] Criar [domain]-capabilities-catalog.mdc
- [ ] Taxonomia (5 categorias, classificação complexidade)
- [ ] Índice navegável (Quick Ref Table)
- [ ] Por categoria, por ROI
- [ ] Criar capabilities/ com 3-5 capabilities individuais

### **Fase 4: Quick Reference Cards (2h)**
- [ ] Criar [domain]-quick-refs.mdc
- [ ] 4-6 Quick Refs (tarefas mais comuns)
- [ ] Código essencial + parâmetros + troubleshooting
- [ ] Matriz de Quick Ref

### **Fase 5: TAGS_INDEX (3h)**
- [ ] Criar knowledge_base/Docs/TAGS_INDEX.md
- [ ] Tags principais (A-Z) com docs/samples
- [ ] Tags por categoria
- [ ] Complexidade (docs + samples)
- [ ] Capabilities mapeadas
- [ ] Quick Search Matrix

### **Fase 6: READMEs em Samples**
- [ ] README.md em 3-5 samples principais
- [ ] Frontmatter YAML completo
- [ ] Overview + quando usar + quick start
- [ ] Tempo estimado + docs relacionadas

### **Fase 7: Lições & Antipadrões**
- [ ] Criar [domain]-troubleshooting.mdc
- [ ] Documentar Top 5-10 lições (com ROI)
- [ ] Checklist antipadrões (20 itens)
- [ ] Template @prompt_licao_aprendida.md

### **Fase 8: Ferramentas & Auditoria (1h)**
- [ ] Seção "Ferramentas & Auditoria" no router
- [ ] Scripts de verificação (links, lints)
- [ ] Checklist de auditoria (40 pontos)

### **Fase 9: Vibe Planning (opcional)**
- [ ] Criar [domain]-vibe-planning.mdc (se projetos complexos)
- [ ] 5 fases + PRD + 10 checkpoints
- [ ] Checklists por tipo de projeto (4 tipos)

### **Validação Final**
- [ ] Executar checklist de auditoria (≥35/40 pontos)
- [ ] Testar workflows com 2-3 tarefas reais
- [ ] Gerar changelog v1.0
- [ ] Documentar ROI observado vs estimado

---

## 💰 ROI ESPERADO

| Estratégia | Economia por Uso | Usos/Projeto | Total/Projeto |
|---|---|---|---|
| Router Central (decisões) | 5-10 min | 10-20x | 50-200 min |
| Knowledge Map (navegação) | 3-8 min | 15-25x | 45-200 min |
| Capabilities Catalog (discovery) | 79% tokens, 85% tempo | 5-10x | 40-90 min |
| Quick Refs (padrões rápidos) | 5-15 min | 10-20x | 50-300 min |
| TAGS_INDEX (discovery) | 50-70% tempo | 10-15x | 50-150 min |
| Lições & Antipadrões | 145-150 min | 1x | 145-150 min |
| Vibe Planning (complexos) | 60-110 min | 1x | 60-110 min |
| **TOTAL ESTIMADO** | - | - | **440-1200 min (7-20h)** |

**Break-even:** 1-2 projetos médios

---

## 📚 REFERÊNCIAS

**Fonte original:** Projeto Advance Steel 2019 (Engelar Engenharia, 2024-2025)

**Rules extraídas:**
- `advance-steel-core.mdc` (router central)
- `advance-steel-knowledge-map.mdc` (navegação KB)
- `advance-steel-capabilities-catalog.mdc` (discovery)
- `advance-steel-quick-refs.mdc` (padrões rápidos)
- `advance-steel-vibe-planning.mdc` (workflow complexos)

**Metodologias inspiradas:**
- Sequential Thinking (Anthropic Claude)
- Spec-Driven Development (Traycer AI)
- Cursor AI best practices (Lakera AI, awesome-cursorrules)

---

## 🎓 PRINCÍPIOS FUNDAMENTAIS

1. **Self-awareness é a base** - Agente deve conhecer-se completamente
2. **Documentação viva > documentação final** - Evolui com projeto
3. **Múltiplas entradas** - KB navegável por categoria, ROI, complexidade, keywords
4. **Workflows estruturados** - Economizam tempo de decisão
5. **Lições validadas** - Documentar antipadrões com ROI comprovado
6. **Versionamento rigoroso** - Changelog em cada atualização
7. **ROI transparente** - Justifica investimento em documentação
8. **Agnóstico de domínio** - Padrões aplicáveis a qualquer tecnologia

---

## 🔄 PRÓXIMOS PASSOS

1. **Adaptar para seu projeto:** Substituir placeholders `[domain]`, `[SEU PROJETO]`
2. **Implementar Fases 1-8:** Seguir checklist de implementação (16h total)
3. **Validar com 2-3 tarefas reais:** Testar workflows
4. **Documentar ROI observado:** Comparar com estimativas
5. **Iterar:** Refinar baseado em uso real

---

**Desenvolvido por:** Agente IA - Engelar Engenharia  
**Compilado de:** Projeto Advance Steel 2019 (.cursor/rules/)  
**Data:** 04/10/2025  
**Versão:** 1.0  
**Licença:** Uso livre, manter atribuição

---

**📧 Como Usar:**
1. Copiar este arquivo para `.cursor/rules/` do seu projeto
2. Adaptar templates substituindo placeholders
3. Seguir checklist de implementação
4. Validar workflows com tarefas reais
5. Documentar ROI e iterar

**🙏 Feedback:**
- Documentar melhorias em `@prompt_licao_aprendida.md`
- Compartilhar ROI observado
- Contribuir com novos templates/estratégias

---

**FIM DO PROMPT**

