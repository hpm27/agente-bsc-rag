# FASE 4.5 - Feedback Collection System: Design Técnico

**Data Início:** 2025-11-19
**Versão:** 1.0
**Status:** [EMOJI] DESIGN APROVADO - Pronto para implementação

---

## [EMOJI] Objetivos

Implementar sistema de coleta de feedback dos usuários sobre diagnósticos BSC gerados:

1. **Coleta Estruturada** - Rating (1-5) + feedback textual opcional
2. **Armazenamento Persistente** - Mem0 para histórico completo
3. **API REST** - Endpoints para coleta programática
4. **Integração Workflow** - Coleta automática após diagnósticos
5. **Análise e Insights** - Agregação de feedback para melhorias

**Estimativa:** 1.5h (conforme plano original)
**Dependências:** FASE 4.4 completa (Analytics Dashboard) [OK]

---

## [EMOJI] Stack Tecnológico (Decisões Fundamentadas - Brightdata Nov 2025)

### **1. Schema Pydantic para Feedback**

**Escolha:** Schema estruturado com rating numérico + texto opcional
**Alternativas consideradas:** Apenas texto livre, apenas rating binário (thumbs up/down)

**Razões:**
- [OK] **Rating numérico (1-5)**: Quantificável, permite análise estatística
- [OK] **Texto opcional**: Captura contexto qualitativo quando necessário
- [OK] **Metadata rica**: Timestamp, user_id, diagnostic_id, phase
- [OK] **Alinhado com best practices**: Helicone AI, Winder.AI (2025)

**Estrutura proposta:**
```python
class Feedback(BaseModel):
    rating: int = Field(ge=1, le=5, description="Rating de 1-5")
    comment: Optional[str] = Field(None, max_length=1000, description="Feedback textual opcional")
    diagnostic_id: str = Field(description="ID do diagnóstico avaliado")
    user_id: str = Field(description="ID do usuário")
    phase: ConsultingPhase = Field(description="Fase do workflow")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**Fontes:**
- Helicone AI (May 2025): "How to Track LLM User Feedback"
- Winder.AI (Mar 2025): "User Feedback in LLM-Powered Applications"

---

### **2. Armazenamento Mem0**

**Escolha:** Mem0 para persistência de feedback histórico
**Alternativas consideradas:** Redis (volátil), PostgreSQL (overhead)

**Razões:**
- [OK] **Já integrado**: Mem0 já usado para ClientProfile
- [OK] **Persistência garantida**: Não perdemos feedback histórico
- [OK] **Busca e análise**: Mem0 permite queries estruturadas
- [OK] **Consistência**: Mesmo storage layer do resto do sistema

**Estrutura Mem0:**
```
Memory Type: "feedback"
Metadata:
  - diagnostic_id: str
  - rating: int (1-5)
  - phase: str (discovery, approval_pending, etc)
  - user_id: str
  - created_at: ISO timestamp
Content: comment (texto opcional)
```

---

### **3. API REST Endpoints**

**Escolha:** FastAPI endpoints seguindo padrão FASE 4.3
**Estrutura:**
- `POST /api/v1/feedback` - Criar novo feedback
- `GET /api/v1/feedback/{feedback_id}` - Buscar feedback específico
- `GET /api/v1/feedback` - Listar feedbacks (filtros: user_id, diagnostic_id, rating)

**Features:**
- Autenticação obrigatória (API key)
- Rate limiting (LIMIT_WRITE para POST)
- Validação Pydantic completa
- Schemas de request/response padronizados

---

### **4. Integração Workflow LangGraph**

**Escolha:** Coleta automática após fase DISCOVERY completa
**Trigger:** Quando diagnóstico é gerado e apresentado ao usuário

**Fluxo:**
1. DiagnosticAgent gera diagnóstico completo
2. Workflow transiciona para APPROVAL_PENDING
3. FeedbackCollector oferece coleta de feedback (opcional, não bloqueia)
4. Feedback armazenado no Mem0
5. Análise agregada disponível via API

**Não bloqueia workflow:** Feedback é opcional, usuário pode pular

---

## [EMOJI] Arquitetura de Implementação

### **Componentes Principais**

1. **Schema Pydantic** (`src/memory/schemas.py`)
   - Classe `Feedback` com validação completa
   - Métodos utilitários: `is_positive()`, `is_negative()`, `to_dict()`

2. **FeedbackCollector Service** (`api/services/feedback_service.py`)
   - Método `collect_feedback()` - Armazena no Mem0
   - Método `get_feedback()` - Busca feedback específico
   - Método `list_feedback()` - Lista com filtros
   - Método `get_feedback_stats()` - Agregação (avg rating, count, etc)

3. **API Router** (`api/routers/feedback.py`)
   - 3 endpoints REST seguindo padrão FASE 4.3
   - Schemas de request/response em `api/schemas/responses.py`

4. **Integração Workflow** (`src/graph/workflow.py`)
   - Método `collect_feedback_after_diagnostic()` chamado após DISCOVERY
   - Não bloqueia workflow (opcional)

---

## [EMOJI] Plano de Implementação (5 Etapas)

### **Etapa 0: Design Técnico** [OK] (COMPLETO)

**Arquivos:**
- `docs/architecture/FASE_4_5_FEEDBACK_COLLECTION_DESIGN.md` (este documento)

**Validação:**
- Design aprovado
- Stack tecnológico definido
- Arquitetura detalhada

---

### **Etapa 1: Schema Pydantic** (15min)

**Objetivo:** Criar schema Feedback completo com validação

**Arquivos:**
- `src/memory/schemas.py` (adicionar classe Feedback)

**Implementação:**
1. Classe `Feedback` com campos obrigatórios (rating, diagnostic_id, user_id, phase)
2. Campos opcionais (comment, metadata)
3. Validadores: rating entre 1-5, comment max 1000 chars
4. Métodos utilitários: `is_positive()` (rating >= 4), `is_negative()` (rating <= 2)

**Validação:**
- Schema valida corretamente
- Métodos utilitários funcionam
- Testes unitários básicos passam

---

### **Etapa 2: FeedbackService** (30min)

**Objetivo:** Implementar service para coleta e análise de feedback

**Arquivos:**
- `api/services/feedback_service.py` (novo arquivo, ~200 linhas)

**Implementação:**
1. Classe `FeedbackService` com Mem0 client
2. Método `collect_feedback(feedback: Feedback) -> str` - Retorna feedback_id
3. Método `get_feedback(feedback_id: str) -> Feedback | None`
4. Método `list_feedback(filters: Dict) -> List[Feedback]`
5. Método `get_feedback_stats(diagnostic_id: str) -> Dict` - Agregação

**Validação:**
- Feedback armazenado corretamente no Mem0
- Busca funciona
- Agregação calcula média, count, etc

---

### **Etapa 3: API Endpoints** (30min)

**Objetivo:** Criar endpoints REST para feedback

**Arquivos:**
- `api/routers/feedback.py` (novo arquivo, ~150 linhas)
- `api/schemas/responses.py` (adicionar schemas FeedbackRequest, FeedbackResponse)

**Endpoints:**
1. `POST /api/v1/feedback` - Criar feedback
2. `GET /api/v1/feedback/{feedback_id}` - Buscar feedback
3. `GET /api/v1/feedback` - Listar feedbacks (query params: user_id, diagnostic_id, rating_min, rating_max)

**Features:**
- Autenticação obrigatória
- Rate limiting (LIMIT_WRITE para POST)
- Validação Pydantic
- Tratamento de erros robusto

**Validação:**
- Endpoints retornam JSON válido
- Autenticação funciona
- Filtros funcionam

---

### **Etapa 4: Integração Workflow** (15min)

**Objetivo:** Integrar coleta de feedback no workflow LangGraph

**Arquivos:**
- `src/graph/workflow.py` (adicionar método collect_feedback)

**Implementação:**
1. Método `collect_feedback_after_diagnostic(state: ConsultingState) -> None`
2. Chamado após DISCOVERY completa (antes de APPROVAL_PENDING)
3. Feedback opcional (não bloqueia workflow se usuário não fornecer)
4. Armazena feedback no Mem0 via FeedbackService

**Validação:**
- Feedback coletado após diagnóstico
- Workflow não bloqueia se feedback não fornecido
- Feedback armazenado corretamente

---

### **Etapa 5: Testes** (30min)

**Objetivo:** Validar implementação completa com testes

**Arquivos:**
- `tests/test_api/test_feedback_service.py` (testes unitários, ~150 linhas)
- `tests/test_api/test_feedback_endpoints.py` (testes E2E, ~100 linhas)

**Testes:**
- Unitários: FeedbackService (8 testes)
  - collect_feedback armazena corretamente
  - get_feedback busca corretamente
  - list_feedback filtra corretamente
  - get_feedback_stats agrega corretamente
  - Handles invalid rating
  - Handles missing diagnostic_id
  - Handles empty comment
  - Handles metadata
- E2E: Endpoints (7 testes)
  - POST cria feedback
  - GET retorna feedback
  - GET lista feedbacks
  - Filtros funcionam
  - Autenticação obrigatória
  - Validação de rating
  - Validação de campos obrigatórios

**Total:** 15 testes (8 unitários + 7 E2E)

**Validação:**
- 15 testes passando (100%)
- Coverage >80%

---

## [EMOJI] Métricas Esperadas

| Métrica | Target | Status |
|---------|--------|--------|
| **Schema Pydantic** | 50 linhas | ⏳ |
| **FeedbackService** | 200 linhas | ⏳ |
| **API Endpoints** | 150 linhas | ⏳ |
| **Integração Workflow** | 50 linhas | ⏳ |
| **Testes** | 250 linhas | ⏳ |
| **Total Código** | ~700 linhas | ⏳ |
| **Tempo Estimado** | 1.5h | ⏳ |
| **Testes Implementados** | 15 testes | ⏳ |

---

## [EMOJI] Best Practices Aplicadas (Brightdata Nov 2025)

### **1. Rating Numérico vs Binário**

**Decisão:** Rating 1-5 (não apenas thumbs up/down)

**Razão:** Permite análise estatística mais rica (média, distribuição, tendências)

**Fonte:** Helicone AI (May 2025) - "Custom Properties allow numeric ratings"

---

### **2. Feedback Opcional Não Bloqueia**

**Decisão:** Coleta de feedback é opcional, workflow continua mesmo sem feedback

**Razão:** Alta taxa de abandono quando feedback é obrigatório

**Fonte:** Winder.AI (Mar 2025) - "Keep feedback process simple, high completion rates come from frictionless mechanisms"

---

### **3. Metadata Rica para Análise**

**Decisão:** Armazenar diagnostic_id, phase, user_id, timestamp

**Razão:** Permite análise segmentada (por diagnóstico, por fase, por usuário)

**Fonte:** Helicone AI (May 2025) - "Custom Properties help segment feedback by user types, features, or use cases"

---

### **4. Armazenamento Persistente**

**Decisão:** Mem0 ao invés de Redis (volátil)

**Razão:** Feedback histórico é valioso para análise de longo prazo

**Fonte:** Winder.AI (Mar 2025) - "Feedback must be triaged, aggregated feedback signals fuel production monitoring dashboards"

---

## [EMOJI] Referências (Brightdata Nov 2025)

### **Feedback Collection:**
1. **Helicone AI (May 2025):** "How to Track LLM User Feedback to Improve Your AI Applications"
   - Feedback API, Custom Properties, User Metrics
2. **Winder.AI (Mar 2025):** "User Feedback in LLM-Powered Applications"
   - Inline Feedback, Freeform Feedback, Implicit Feedback, Retrospective Feedback

### **FastAPI Best Practices:**
3. **FastAPI Docs (2025):** "Request Body Validation"
   - Pydantic schemas, Field validation
4. **GitHub fastapi-best-practices (2025):** "API Design Patterns"
   - Router organization, dependency injection

---

## [OK] Checklist de Implementação

- [ ] Etapa 0: Design Técnico completo
- [ ] Etapa 1: Schema Pydantic Feedback
- [ ] Etapa 2: FeedbackService com Mem0
- [ ] Etapa 3: API Endpoints REST
- [ ] Etapa 4: Integração Workflow LangGraph
- [ ] Etapa 5: Testes (15 testes, 100% passando)
- [ ] Documentação atualizada
- [ ] Progress tracking atualizado

---

**Última Atualização:** 2025-11-19
**Status:** [EMOJI] DESIGN APROVADO - Pronto para implementação
**Próximo:** Etapa 1 - Schema Pydantic
