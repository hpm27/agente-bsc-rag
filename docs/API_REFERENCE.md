# Referência da API - Agente BSC RAG

## 📦 Módulos Principais

### `src.graph.workflow`

#### `BSCWorkflow`

Classe principal que orquestra o fluxo de execução com LangGraph.

**Métodos:**

##### `__init__()`

Inicializa o workflow com todos os agentes e constrói o grafo.

```python
from src.graph.workflow import BSCWorkflow

workflow = BSCWorkflow()
```

##### `run(query: str, session_id: str = None) -> Dict[str, Any]`

Executa o workflow completo para uma query.

**Parâmetros:**

- `query` (str): Pergunta do usuário
- `session_id` (str, opcional): ID da sessão para rastreamento

**Retorna:**

```python
{
    "response": str,              # Resposta final agregada
    "metadata": {
        "perspectives_used": List[str],
        "judge_score": float,
        "refinement_iterations": int,
        "total_sources": int,
        "latency": float
    },
    "judge_evaluation": {
        "approved": bool,
        "score": float,
        "feedback": str,
        "issues": List[str],
        "suggestions": List[str]
    },
    "perspectives": List[Dict]    # Respostas individuais por perspectiva
}
```

**Exemplo:**

```python
import asyncio
from src.graph.workflow import create_bsc_workflow

async def main():
    workflow = create_bsc_workflow()
    result = await workflow.run(
        query="Quais são os principais KPIs financeiros?",
        session_id="session-123"
    )
    print(result["response"])

asyncio.run(main())
```

---

### `src.agents`

#### `Orchestrator`

Orquestrador central que analisa queries e coordena agentes.

**Métodos:**

##### `analyze_query(query: str) -> Dict[str, Any]`

Analisa a query para determinar tipo e complexidade.

```python
from src.agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
analysis = await orchestrator.analyze_query("Como implementar BSC?")
# {'type': 'conceptual', 'complexity': 'moderate', ...}
```

##### `route_to_perspectives(query: str, query_type: str) -> List[PerspectiveType]`

Determina quais perspectivas BSC são relevantes.

```python
perspectives = await orchestrator.route_to_perspectives(
    query="Quais KPIs financeiros usar?",
    query_type="factual"
)
# [PerspectiveType.FINANCIAL]
```

##### `aggregate_responses(query: str, responses: List[Dict]) -> str`

Agrega respostas de múltiplos agentes.

---

#### Agentes Especialistas

Todos os agentes especialistas (`FinancialAgent`, `CustomerAgent`, `ProcessAgent`, `LearningAgent`) compartilham a mesma interface:

##### `process(query: str, context: Dict = None) -> Dict[str, Any]`

Processa uma query na perspectiva do agente.

**Retorna:**

```python
{
    "content": str,           # Resposta do agente
    "confidence": float,      # Confiança (0-1)
    "sources": List[Dict],    # Fontes consultadas
    "reasoning": str          # Raciocínio (opcional)
}
```

**Exemplo:**

```python
from src.agents.financial_agent import FinancialAgent

agent = FinancialAgent()
result = await agent.process("Quais métricas de ROI usar?")
print(f"Confiança: {result['confidence']}")
```

---

#### `JudgeAgent`

Avalia qualidade e relevância das respostas.

##### `evaluate(query: str, response: str, sources: List[Dict]) -> Dict[str, Any]`

Avalia uma resposta gerada.

**Retorna:**

```python
{
    "approved": bool,         # Se a resposta foi aprovada
    "score": float,           # Score de qualidade (0-1)
    "feedback": str,          # Feedback textual
    "issues": List[str],      # Problemas identificados
    "suggestions": List[str]  # Sugestões de melhoria
}
```

---

### `src.rag`

#### `BSCRetriever`

Sistema de retrieval híbrido (semântico + BM25).

**Métodos:**

##### `retrieve(query: str, top_k: int = 10, filters: Dict = None) -> List[SearchResult]`

Busca documentos relevantes.

```python
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()
results = retriever.retrieve(
    query="KPIs financeiros",
    top_k=10,
    filters={"perspective": "financial"}
)
```

##### `retrieve_with_rerank(query: str, top_k: int = 10, top_n: int = 5) -> List[SearchResult]`

Busca com re-ranking Cohere.

```python
results = retriever.retrieve_with_rerank(
    query="Como medir satisfação do cliente?",
    top_k=20,  # Buscar 20
    top_n=5    # Re-rankar para 5 melhores
)
```

---

#### `EmbeddingManager`

Gerencia geração de embeddings com OpenAI.

**Métodos:**

##### `embed_text(text: str) -> List[float]`

Gera embedding para texto.

```python
from src.rag.embeddings import EmbeddingManager

embedder = EmbeddingManager()
embedding = embedder.embed_text("Balanced Scorecard")
# [0.123, -0.456, ...]  (3072 dimensões)
```

##### `embed_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]`

Gera embeddings em batch.

---

#### Vector Stores

Todos os vector stores (`QdrantVectorStore`, `WeaviateVectorStore`, `RedisVectorStore`) implementam `BaseVectorStore`:

##### `add_documents(documents: List[Dict]) -> List[str]`

Adiciona documentos ao índice.

```python
from src.rag.vector_store_factory import create_vector_store

store = create_vector_store()
doc_ids = store.add_documents([
    {
        "id": "doc1",
        "content": "...",
        "metadata": {"perspective": "financial"}
    }
])
```

##### `hybrid_search(query_text: str, query_embedding: List[float], top_k: int = 10) -> List[SearchResult]`

Busca híbrida (semântica + keyword).

```python
results = store.hybrid_search(
    query_text="ROI metrics",
    query_embedding=embedding,
    top_k=10
)
```

---

### `src.tools`

#### `RAGTools`

Ferramentas RAG para uso pelos agentes.

**Métodos:**

##### `search_knowledge_base(query: str, top_k: int = 10) -> List[Dict]`

Busca na base de conhecimento.

```python
from src.tools.rag_tools import RAGTools

tools = RAGTools()
results = tools.search_knowledge_base(
    query="BSC implementation",
    top_k=5
)
```

##### `search_by_perspective(query: str, perspective: str, top_k: int = 10) -> List[Dict]`

Busca filtrada por perspectiva BSC.

```python
results = tools.search_by_perspective(
    query="KPIs",
    perspective="financial",
    top_k=10
)
```

---

## 🔧 Configuração

### `config.settings`

Objeto singleton com todas as configurações:

```python
from config.settings import settings

# Acessar configurações
print(settings.openai_model)           # "gpt-5"
print(settings.vector_store_type)      # "qdrant"
print(settings.chunk_size)             # 1000
```

**Principais Settings:**

| Configuração | Tipo | Padrão | Descrição |
|--------------|------|--------|-----------|
| `openai_model` | str | gpt-5 | Modelo LLM principal |
| `openai_embedding_model` | str | text-embedding-3-large | Modelo de embeddings |
| `vector_store_type` | str | qdrant | Vector store (qdrant/weaviate/redis) |
| `chunk_size` | int | 1000 | Tamanho dos chunks |
| `chunk_overlap` | int | 200 | Sobreposição entre chunks |
| `top_k_retrieval` | int | 10 | Documentos retornados |
| `top_n_rerank` | int | 5 | Documentos após re-ranking |
| `enable_contextual_retrieval` | bool | True | Ativar Contextual Retrieval |
| `temperature` | float | 0.0 | Temperatura do LLM |
| `max_tokens` | int | 2000 | Tokens máximos por resposta |

---

## 📊 Modelos de Dados

### `BSCState`

Estado do grafo de execução:

```python
from src.graph.states import BSCState

state = BSCState(
    query="Como implementar BSC?",
    session_id="123",
    relevant_perspectives=[PerspectiveType.FINANCIAL],
    agent_responses=[...],
    aggregated_response="...",
    judge_evaluation=JudgeEvaluation(...),
    final_response="...",
    is_complete=True
)
```

### `AgentResponse`

Resposta de um agente especialista:

```python
from src.graph.states import AgentResponse, PerspectiveType

response = AgentResponse(
    perspective=PerspectiveType.FINANCIAL,
    content="KPIs financeiros incluem...",
    confidence=0.85,
    sources=[...],
    reasoning="Baseado em..."
)
```

### `SearchResult`

Resultado de busca do vector store:

```python
from src.rag.base_vector_store import SearchResult

result = SearchResult(
    id="doc_1",
    content="Texto do documento...",
    score=0.92,
    metadata={"perspective": "financial", "source": "kaplan_1996.pdf"}
)
```

---

## 🎯 Exemplos de Uso

### Exemplo 1: Workflow Simples

```python
import asyncio
from src.graph.workflow import create_bsc_workflow

async def main():
    workflow = create_bsc_workflow()
    
    result = await workflow.run(
        query="Quais são os KPIs principais do BSC?"
    )
    
    print("Resposta:", result["response"])
    print("Score Judge:", result["metadata"]["judge_score"])
    print("Perspectivas:", result["metadata"]["perspectives_used"])

asyncio.run(main())
```

### Exemplo 2: Busca Manual com Retriever

```python
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()

# Busca simples
results = retriever.retrieve("balanced scorecard implementation")

for result in results[:3]:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:100]}...")
    print("---")
```

### Exemplo 3: Usar Agente Específico

```python
from src.agents.financial_agent import FinancialAgent

async def financial_query():
    agent = FinancialAgent()
    
    response = await agent.process(
        query="Como calcular ROI no contexto BSC?",
        context={"company_size": "large"}
    )
    
    print(f"Resposta: {response['content']}")
    print(f"Confiança: {response['confidence']}")

asyncio.run(financial_query())
```

### Exemplo 4: Indexação Programática

```python
from src.rag.vector_store_factory import create_vector_store
from src.rag.embeddings import EmbeddingManager
from src.rag.chunker import SemanticChunker

# Setup
store = create_vector_store()
embedder = EmbeddingManager()
chunker = SemanticChunker()

# Texto para indexar
text = "O Balanced Scorecard é um framework..."

# Chunking
chunks = chunker.chunk(text)

# Embedding
embeddings = embedder.embed_batch([c.content for c in chunks])

# Indexar
documents = [
    {
        "id": f"doc_{i}",
        "content": chunk.content,
        "embedding": emb,
        "metadata": {"source": "manual"}
    }
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
]

doc_ids = store.add_documents(documents)
print(f"Indexados {len(doc_ids)} documentos")
```

---

## 🔍 Debugging

### Ativar Logs Verbosos

```python
from loguru import logger
import sys

# Remover handler padrão
logger.remove()

# Adicionar handler verbose
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time}</green> | <level>{level}</level> | {message}"
)
```

### Inspecionar Estado do Workflow

```python
workflow = BSCWorkflow()

# Grafo compilado
print(workflow.graph)

# Agentes disponíveis
print(workflow.agents.keys())
```

---

## 📚 Referências

- [Documentação LangGraph](https://langchain-ai.github.io/langgraph/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Cohere Rerank](https://docs.cohere.com/docs/reranking)


