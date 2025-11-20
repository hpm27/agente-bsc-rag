# [EMOJI] Referência da API - Agente BSC RAG

> Documentação técnica completa da API do sistema BSC RAG para uso programático

---

## [EMOJI] Índice

- [Visão Geral](#visão-geral)
- [LangGraph Workflow](#langgraph-workflow)
- [Orchestrator](#orchestrator)
- [Agentes Especialistas BSC](#agentes-especialistas-bsc)
- [Judge Agent](#judge-agent)
- [Pipeline RAG](#pipeline-rag)
- [Ferramentas RAG](#ferramentas-rag)
- [Configurações](#configurações)
- [Tipos e Modelos](#tipos-e-modelos)

---

## [EMOJI] Visão Geral

A API do Agente BSC RAG segue uma arquitetura modular baseada em:

- **LangGraph Workflow**: Orquestração com grafo de estados
- **Orchestrator**: Coordenação de agentes especialistas
- **Agentes BSC**: 4 especialistas (Financial, Customer, Process, Learning) + Judge
- **Pipeline RAG**: Retrieval, reranking, query expansion multilíngue
- **Ferramentas**: Search tools para acesso ao conhecimento BSC

---

## [EMOJI] LangGraph Workflow

### `get_workflow()`

Retorna a instância singleton do workflow BSC.

```python
from src.graph.workflow import get_workflow

workflow = get_workflow()
```

**Retorno**: `BSCWorkflow` - Instância do workflow LangGraph

**Características**:
- [OK] Singleton (sempre retorna a mesma instância)
- [OK] Thread-safe
- [OK] Carregamento lazy (inicializa apenas no primeiro uso)

---

### `BSCWorkflow.run()`

Executa o workflow completo para processar uma query BSC.

```python
result = workflow.run(
    query="Como definir objetivos para a perspectiva financeira?",
    session_id="my-session-123",
    max_iterations=2,
    judge_threshold=0.7
)
```

**Parâmetros**:

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | (obrigatório) | Query do usuário |
| `session_id` | `str` | `None` | ID da sessão para contexto |
| `max_iterations` | `int` | `2` | Máximo de refinamentos |
| `judge_threshold` | `float` | `0.7` | Score mínimo do Judge (0-1) |

**Retorno**: `dict` com estrutura:

```python
{
    "query": str,                      # Query original
    "final_response": str,             # Resposta final sintetizada
    "perspectives": List[str],         # Perspectivas consultadas
    "perspectives_covered": List[str], # Perspectivas na resposta
    "agent_responses": List[dict],     # Respostas individuais dos agentes
    "judge_evaluation": {              # Avaliação do Judge
        "score": float,                # Score 0-1
        "approved": bool,              # Se foi aprovado
        "feedback": str,               # Feedback detalhado
        "completeness": float,         # Score de completude
        "grounding": float,            # Score de fundamentação
        "source_citation": float,      # Score de citação de fontes
        "issues": List[str],           # Problemas identificados
        "suggestions": List[str]       # Sugestões de melhoria
    },
    "refinement_iterations": int,      # Número de refinamentos
    "metadata": dict                   # Metadados adicionais
}
```

**Exemplo Completo**:

```python
from src.graph.workflow import get_workflow

workflow = get_workflow()

result = workflow.run(
    query="Quais são os principais KPIs da perspectiva financeira?",
    session_id="session-001"
)

# Acessar resposta
print(result["final_response"])

# Verificar aprovação do Judge
if result["judge_evaluation"]["approved"]:
    print(f"Resposta aprovada com score {result['judge_evaluation']['score']:.2f}")
else:
    print("Resposta reprovada:")
    print(result["judge_evaluation"]["feedback"])

# Listar perspectivas consultadas
for perspective in result["perspectives"]:
    print(f"- {perspective}")
```

---

### `BSCWorkflow.get_graph_visualization()`

Retorna visualização ASCII do grafo LangGraph.

```python
viz = workflow.get_graph_visualization()
print(viz)
```

**Retorno**: `str` - Diagrama ASCII do grafo

**Exemplo de Saída**:

```
START -> analyze_query -> execute_agents -> synthesize_response
-> judge_evaluation -> decide_next_step -> [finalize OR refine] -> END
```

---

## [EMOJI] Orchestrator

Classe responsável por coordenar agentes especialistas.

### Inicialização

```python
from src.agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
```

**Propriedades**:

```python
orchestrator.name            # "Orchestrator"
orchestrator.llm             # LLM configurado (Claude/GPT)
orchestrator.agents          # Dict com 4 agentes BSC
orchestrator.judge           # JudgeAgent instance
```

---

### `analyze_query()`

Analisa a query e determina quais agentes acionar.

```python
from src.agents.orchestrator import Orchestrator

orchestrator = Orchestrator()

routing = orchestrator.analyze_query(
    query="Como a satisfação do cliente impacta a lucratividade?"
)
```

**Parâmetros**:

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `query` | `str` | Query do usuário |

**Retorno**: `RoutingDecision` (Pydantic Model)

```python
{
    "agents_to_use": ["cliente", "financeira"],
    "reasoning": "Query envolve satisfação (cliente) e lucratividade (financeira)",
    "is_general_question": False
}
```

---

### `invoke_agents()` (Síncrono)

Executa agentes selecionados de forma **síncrona** (sequencial).

```python
responses = orchestrator.invoke_agents(
    query="Quais são os KPIs financeiros?",
    agents_to_use=["financeira"]
)
```

**Parâmetros**:

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `query` | `str` | Query do usuário |
| `agents_to_use` | `List[str]` | Nomes dos agentes: `["financeira", "cliente", "processos", "aprendizado"]` |

**Retorno**: `List[AgentResponse]`

```python
[
    {
        "perspective": "Financial",
        "response": "Os principais KPIs financeiros incluem...",
        "confidence": 0.92,
        "sources": [
            {"source": "The Balanced Scorecard", "page": 42, "score": 0.95}
        ]
    }
]
```

---

### `ainvoke_agents()` (Assíncrono) [FAST]

Executa agentes selecionados de forma **assíncrona** (paralela).

```python
import asyncio

responses = asyncio.run(
    orchestrator.ainvoke_agents(
        query="Como implementar BSC?",
        agents_to_use=["financeira", "cliente", "processos", "aprendizado"]
    )
)
```

**Vantagens**:
- [FAST] **3.34x mais rápido** que execução síncrona
- [OK] Execução paralela com `asyncio.gather()`
- [OK] Mesma interface que `invoke_agents()`

**Performance**:
- 4 agentes sequencial: ~120s
- 4 agentes paralelo (AsyncIO): ~36s

---

### `synthesize_response()`

Combina respostas de múltiplos agentes em uma resposta coesa.

```python
synthesis = orchestrator.synthesize_response(
    query="Como satisfação do cliente impacta lucratividade?",
    agent_responses=[
        {"perspective": "Customer", "response": "...", "confidence": 0.9},
        {"perspective": "Financial", "response": "...", "confidence": 0.88}
    ]
)
```

**Retorno**: `SynthesisResult` (Pydantic Model)

```python
{
    "synthesized_answer": "A satisfação do cliente impacta a lucratividade através de...",
    "perspectives_covered": ["Customer", "Financial"],
    "confidence": 0.89
}
```

---

## [EMOJI] Agentes Especialistas BSC

### Estrutura Comum

Todos os 4 agentes especialistas seguem a mesma interface:

```python
# Financial, Customer, Process, Learning Agents
from src.agents.financial_agent import FinancialAgent

agent = FinancialAgent()

# Invocação síncrona
response = agent.invoke(query="Quais são os KPIs de receita?")

# Invocação assíncrona
response = await agent.ainvoke(query="Quais são os KPIs de receita?")
```

**Retorno**: `AgentResponse` (dict)

```python
{
    "perspective": "Financial",
    "response": "Os principais KPIs de receita incluem...",
    "confidence": 0.91,
    "sources": [
        {
            "source": "The Balanced Scorecard",
            "page": 65,
            "score": 0.94,
            "content": "Revenue growth is a key financial metric..."
        }
    ]
}
```

---

### `FinancialAgent` [EMOJI]

**Especialização**: Perspectiva Financeira do BSC

**Áreas de Expertise**:
- ROI, crescimento de receita, lucratividade
- Produtividade, redução de custos
- Mix de produtos, valor para acionistas

**Exemplo**:

```python
from src.agents.financial_agent import FinancialAgent

agent = FinancialAgent()
response = agent.invoke("Como medir ROI em BSC?")

print(response["response"])
```

---

### `CustomerAgent` [EMOJI]

**Especialização**: Perspectiva de Clientes

**Áreas de Expertise**:
- Satisfação, retenção, NPS
- Proposta de valor, experiência do cliente
- Quota de mercado, fidelização

**Exemplo**:

```python
from src.agents.customer_agent import CustomerAgent

agent = CustomerAgent()
response = agent.invoke("Como medir satisfação do cliente no BSC?")
```

---

### `ProcessAgent` [EMOJI]

**Especialização**: Perspectiva de Processos Internos

**Áreas de Expertise**:
- Eficiência operacional, qualidade
- Ciclo de tempo, produtividade
- Inovação, melhoria contínua

**Exemplo**:

```python
from src.agents.process_agent import ProcessAgent

agent = ProcessAgent()
response = agent.invoke("Quais processos críticos monitorar no BSC?")
```

---

### `LearningAgent` [EMOJI]

**Especialização**: Perspectiva de Aprendizado e Crescimento

**Áreas de Expertise**:
- Capacitação de funcionários
- Cultura organizacional, clima
- Sistemas de informação, infraestrutura

**Exemplo**:

```python
from src.agents.learning_agent import LearningAgent

agent = LearningAgent()
response = agent.invoke("Como desenvolver capacidades organizacionais?")
```

---

## [EMOJI] Judge Agent

Agente de validação de qualidade (LLM as Judge).

### Inicialização

```python
from src.agents.judge_agent import JudgeAgent

judge = JudgeAgent()
```

---

### `evaluate()`

Avalia a qualidade de uma resposta gerada.

```python
evaluation = judge.evaluate(
    query="Quais são os KPIs financeiros?",
    response="Os principais KPIs financeiros são ROI, crescimento de receita...",
    sources=[
        {"source": "The Balanced Scorecard", "page": 42, "score": 0.95}
    ],
    perspectives=["Financial"]
)
```

**Parâmetros**:

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `query` | `str` | Query original do usuário |
| `response` | `str` | Resposta gerada pelo sistema |
| `sources` | `List[dict]` | Fontes utilizadas |
| `perspectives` | `List[str]` | Perspectivas BSC consultadas |

**Retorno**: `JudgeEvaluation` (Pydantic Model)

```python
{
    "score": 0.92,                    # Score geral (0-1)
    "approved": True,                 # Se passou no threshold (0.7)
    "completeness": 0.95,             # Completude da resposta
    "grounding": 0.91,                # Fundamentação em fontes
    "source_citation": 0.89,          # Citação adequada de fontes
    "feedback": "Resposta bem fundamentada cobrindo aspectos financeiros...",
    "issues": [],                     # Problemas identificados
    "suggestions": [
        "Adicionar exemplo prático de cálculo de ROI"
    ]
}
```

**Critérios de Avaliação**:

| Critério | Peso | Descrição |
|----------|------|-----------|
| **Completeness** | 35% | Responde totalmente à query? |
| **Grounding** | 35% | Fundamentada em fontes? Sem alucinações? |
| **Source Citation** | 30% | Cita fontes adequadamente? |

**Thresholds Padrão**:
- [OK] Aprovado: score ≥ 0.7
- [WARN] Revisar: 0.5 ≤ score < 0.7
- [ERRO] Reprovado: score < 0.5

---

## [EMOJI] Pipeline RAG

### `BSCRetriever`

Classe principal de retrieval com hybrid search e multilingual expansion.

#### Inicialização

```python
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()
```

---

#### `retrieve()`

Recupera documentos relevantes para uma query.

```python
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()

results = retriever.retrieve(
    query="Quais são os KPIs financeiros?",
    top_k=10,
    threshold=0.7,
    multilingual=True
)
```

**Parâmetros**:

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `query` | `str` | (obrigatório) | Query do usuário |
| `top_k` | `int` | `10` | Número de documentos a retornar |
| `threshold` | `float` | `0.7` | Score mínimo de relevância (0-1) |
| `multilingual` | `bool` | `True` | Ativar query expansion PT-BR <-> EN |

**Retorno**: `List[SearchResult]`

```python
[
    {
        "content": "ROI (Return on Investment) is a key financial metric...",
        "source": "The Balanced Scorecard",
        "page": 42,
        "score": 0.95,
        "metadata": {
            "context_pt": "Contexto em português...",
            "context_en": "Context in English...",
            "chunk_index": 1234
        }
    },
    # ... mais resultados
]
```

**Pipeline Interno**:

1. **Query Translation** (se `multilingual=True`):
   - Detecta idioma (PT-BR vs EN)
   - Traduz query PT-BR -> EN
   - Gera segunda query em inglês

2. **Hybrid Search** (Qdrant nativo):
   - 70% busca semântica (embeddings)
   - 30% busca lexical (BM25)

3. **Reciprocal Rank Fusion** (RRF):
   - Combina resultados PT-BR + EN
   - Formula: `score = Σ 1/(k + rank)`
   - k=60 (padrão da literatura)

4. **Adaptive Reranking** (Cohere):
   - Detecção automática de idioma
   - top_n ajustado (+20% se PT-BR)
   - Modelo: rerank-multilingual-v3.0

**Performance**:
- +106% precisão top-1 (vs busca monolíngue)
- +70% recall (query expansion)
- +200-300ms latência (tradução GPT-5 mini)

---

### `EmbeddingManager`

Gerenciador de embeddings com cache persistente.

#### `embed_text()`

Gera embedding para um texto.

```python
from src.rag.embeddings import EmbeddingManager

embedding_manager = EmbeddingManager()

embedding = embedding_manager.embed_text("Balanced Scorecard KPIs")
```

**Retorno**: `List[float]` - Vector de 3072 dimensões

**Cache**:
- [OK] Cache automático em disco (diskcache)
- [OK] 949x speedup para textos repetidos
- [OK] 87.5% hit rate em cenários realistas
- [OK] Thread-safe e multiprocess-safe
- [OK] TTL: 30 dias (configurável)
- [OK] Tamanho máximo: 5GB com LRU eviction

**Estatísticas**:

```python
stats = embedding_manager.get_cache_stats()

print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit Rate: {stats['hit_rate']:.1%}")
print(f"Size: {stats['size_mb']:.2f} MB")
```

---

### `QueryTranslator`

Tradutor de queries para busca multilíngue.

#### `translate()`

Traduz query PT-BR <-> EN.

```python
from src.rag.query_translator import QueryTranslator

translator = QueryTranslator()

translation = translator.translate(
    query="Quais são os KPIs financeiros?",
    target_lang="en"
)
```

**Retorno**: `str` - "What are the financial KPIs?"

**Cache**:
- [OK] Cache in-memory automático
- [OK] LLM: GPT-5 mini (rápido e barato: ~$0.001/query)

---

## [EMOJI] Ferramentas RAG

### `SearchTool`

Ferramenta de busca básica para agentes.

```python
from src.tools.rag_tools import SearchTool

search_tool = SearchTool()

results = search_tool.invoke({
    "query": "ROI calculation methods",
    "top_k": 5
})
```

**Parâmetros do invoke**:

```python
{
    "query": str,     # Query de busca
    "top_k": int      # Número de resultados (padrão: 10)
}
```

**Retorno**: `str` - Resultados formatados para o agente

```
Source 1 (Score: 0.95):
Content: ROI is calculated as...
Reference: The Balanced Scorecard, p. 42

Source 2 (Score: 0.89):
...
```

---

## [EMOJI] Configurações

### Arquivo `.env`

Todas as configurações são gerenciadas via `.env`:

```env
# ==============================================================================
# APIs de IA
# ==============================================================================

OPENAI_API_KEY=sk-proj-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

COHERE_API_KEY=...

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

DEFAULT_LLM_MODEL=claude-sonnet-4-5-20250929

# ==============================================================================
# Vector Store
# ==============================================================================

VECTOR_STORE_TYPE=qdrant
VECTOR_STORE_INDEX=bsc_documents

QDRANT_HOST=localhost
QDRANT_PORT=6333

# ==============================================================================
# RAG Configuration
# ==============================================================================

TOP_K_RETRIEVAL=10
RERANK_TOP_N=5
SIMILARITY_THRESHOLD=0.7

ENABLE_MULTILINGUAL_SEARCH=true
ENABLE_QUERY_EXPANSION=true
ENABLE_ADAPTIVE_RERANKING=true

# ==============================================================================
# Performance
# ==============================================================================

ENABLE_EMBEDDING_CACHE=true
EMBEDDING_CACHE_DIR=.cache/embeddings
EMBEDDING_CACHE_TTL_DAYS=30
EMBEDDING_CACHE_SIZE_GB=5

AGENT_MAX_WORKERS=4

# ==============================================================================
# Judge Configuration
# ==============================================================================

JUDGE_THRESHOLD=0.7
JUDGE_MAX_TOKENS=16384
```

---

### `settings.py`

Classe `Settings` centralizada (Pydantic BaseSettings):

```python
from config.settings import settings

# Acessar configurações
print(settings.openai_api_key)
print(settings.vector_store_type)
print(settings.top_k_retrieval)
print(settings.enable_embedding_cache)

# LLM factory
llm = settings.get_llm(temperature=0.7)
```

**Propriedades Principais**:

```python
settings.openai_api_key: str
settings.cohere_api_key: str
settings.anthropic_api_key: str

settings.default_llm_model: str
settings.openai_embedding_model: str

settings.vector_store_type: str  # "qdrant" | "weaviate" | "redis"
settings.vector_store_index: str

settings.qdrant_host: str
settings.qdrant_port: int

settings.top_k_retrieval: int
settings.rerank_top_n: int
settings.similarity_threshold: float

settings.enable_multilingual_search: bool
settings.enable_embedding_cache: bool
settings.embedding_cache_dir: str

settings.judge_threshold: float
settings.agent_max_workers: int
```

---

## [EMOJI] Tipos e Modelos

### Pydantic Models

Todos os modelos principais usam Pydantic para validação:

#### `BSCState` (LangGraph State)

```python
from src.graph.states import BSCState

state = BSCState(
    query="Como implementar BSC?",
    perspectives=["financeira", "cliente"],
    final_response="",
    refinement_iterations=0
)
```

**Campos**:

```python
{
    "query": str,
    "perspectives": List[str],
    "agent_responses": List[AgentResponse],
    "synthesized_response": Optional[str],
    "judge_evaluation": Optional[JudgeEvaluation],
    "final_response": str,
    "refinement_iterations": int,
    "max_iterations": int,
    "metadata": dict
}
```

---

#### `AgentResponse`

```python
from src.graph.states import AgentResponse

response = AgentResponse(
    perspective="Financial",
    response="Os KPIs financeiros incluem...",
    confidence=0.92,
    sources=[...]
)
```

---

#### `JudgeEvaluation`

```python
from src.graph.states import JudgeEvaluation

evaluation = JudgeEvaluation(
    score=0.89,
    approved=True,
    completeness=0.91,
    grounding=0.88,
    source_citation=0.87,
    feedback="Resposta bem fundamentada...",
    issues=[],
    suggestions=["Adicionar exemplo prático"]
)
```

---

#### `PerspectiveType` (Enum)

```python
from src.graph.states import PerspectiveType

# Valores possíveis
PerspectiveType.FINANCIAL    # "Financial"
PerspectiveType.CUSTOMER     # "Customer"
PerspectiveType.PROCESS      # "Process"
PerspectiveType.LEARNING     # "Learning"
```

---

## [EMOJI] Exemplos Completos

### Exemplo 1: Uso Básico do Workflow

```python
from src.graph.workflow import get_workflow

# Inicializar workflow
workflow = get_workflow()

# Executar query
result = workflow.run(
    query="Como definir objetivos para a perspectiva financeira?",
    session_id="session-001"
)

# Processar resultado
if result["judge_evaluation"]["approved"]:
    print("[OK] Resposta aprovada!")
    print(f"\nResposta:\n{result['final_response']}\n")

    print(f"Perspectivas consultadas:")
    for p in result["perspectives"]:
        print(f"  - {p}")

    print(f"\nScore do Judge: {result['judge_evaluation']['score']:.2f}")
else:
    print("[ERRO] Resposta reprovada")
    print(f"Feedback: {result['judge_evaluation']['feedback']}")
```

---

### Exemplo 2: Uso Direto de Agentes

```python
from src.agents.financial_agent import FinancialAgent
from src.agents.customer_agent import CustomerAgent

# Inicializar agentes
financial_agent = FinancialAgent()
customer_agent = CustomerAgent()

# Executar queries específicas
financial_response = financial_agent.invoke("Quais são os KPIs de ROI?")
customer_response = customer_agent.invoke("Como medir NPS?")

# Processar respostas
print(f"Financial Agent (confidence {financial_response['confidence']:.2f}):")
print(financial_response['response'])

print(f"\nCustomer Agent (confidence {customer_response['confidence']:.2f}):")
print(customer_response['response'])
```

---

### Exemplo 3: Busca RAG Direta

```python
from src.rag.retriever import BSCRetriever

# Inicializar retriever
retriever = BSCRetriever()

# Busca multilíngue
results = retriever.retrieve(
    query="Quais são os objetivos da perspectiva de processos?",
    top_k=5,
    multilingual=True
)

# Processar resultados
for i, result in enumerate(results, 1):
    print(f"\n[{i}] Score: {result['score']:.3f}")
    print(f"Fonte: {result['source']}, Seção {result['page']}")
    print(f"Conteúdo: {result['content'][:200]}...")
```

---

### Exemplo 4: Validação com Judge

```python
from src.agents.judge_agent import JudgeAgent

# Inicializar Judge
judge = JudgeAgent()

# Avaliar resposta
evaluation = judge.evaluate(
    query="O que é Balanced Scorecard?",
    response="Balanced Scorecard é uma metodologia de gestão estratégica...",
    sources=[
        {"source": "The Balanced Scorecard", "page": 1, "score": 0.98}
    ],
    perspectives=["Financial", "Customer", "Process", "Learning"]
)

# Verificar aprovação
if evaluation["approved"]:
    print(f"[OK] Aprovado com score {evaluation['score']:.2f}")
else:
    print(f"[ERRO] Reprovado")
    print(f"Issues: {', '.join(evaluation['issues'])}")
    print(f"Sugestões: {', '.join(evaluation['suggestions'])}")
```

---

## [EMOJI] Suporte

Para dúvidas técnicas sobre a API:

- [EMOJI] Consulte [ARCHITECTURE.md](ARCHITECTURE.md) para detalhes de arquitetura
- [EMOJI] Veja [TUTORIAL.md](TUTORIAL.md) para casos de uso práticos
- [EMOJI] Reporte bugs em [Issues](https://github.com/seu-usuario/agente-bsc-rag/issues)

---

<p align="center">
  <strong>[EMOJI] API Reference v1.0</strong><br>
  <em>Agente BSC RAG - MVP Out/2025</em>
</p>
