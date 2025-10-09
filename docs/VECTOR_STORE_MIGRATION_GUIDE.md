# Guia de Migração - Vector Store

Este guia explica como migrar do Redis para Qdrant ou Weaviate no projeto Agente BSC RAG.

---

## Visão Geral da Migração

A nova arquitetura suporta múltiplos vector stores através de uma interface comum (`BaseVectorStore`), facilitando a troca entre implementações sem modificar o código que usa o vector store.

### Vector Stores Suportados

| Vector Store | Status | Recomendação |
|--------------|--------|--------------|
| **Qdrant** | ✅ Recomendado | Melhor para produção 2025 |
| **Weaviate** | ✅ Alternativa | Melhor se hybrid search nativo for crítico |
| **Redis Stack** | ⚠️ Legacy | Mantido para compatibilidade |

---

## Passo a Passo da Migração

### 1. Atualizar Dependências

```bash
# Instalar novas dependências
pip install -r requirements.txt

# Verificar instalação
python -c "import qdrant_client, weaviate; print('OK')"
```

### 2. Configurar Vector Store no `.env`

Adicione ao arquivo `.env` na raiz do projeto:

```env
# Escolher o vector store (qdrant, weaviate, ou redis)
VECTOR_STORE_TYPE=qdrant

# Configurações Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Configurações Weaviate (se usar)
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
```

### 3. Subir o Vector Store com Docker

#### Opção A: Qdrant (Recomendado)

```bash
# Já está no docker-compose.yml
docker-compose up -d qdrant

# Verificar se está rodando
curl http://localhost:6333/health
```

#### Opção B: Weaviate

```bash
# Já está no docker-compose.yml
docker-compose up -d weaviate

# Verificar se está rodando
curl http://localhost:8080/v1/.well-known/ready
```

### 4. Atualizar Código para Usar Factory

#### Antes (Redis direto)

```python
from src.rag.vector_store import RedisVectorStore

# Instância direta
vector_store = RedisVectorStore()
```

#### Depois (Factory pattern)

```python
from src.rag import create_vector_store

# Factory cria o vector store configurado no .env
vector_store = create_vector_store()

# Ou criar explicitamente
vector_store = create_vector_store('qdrant')
```

O código que usa `vector_store` não precisa mudar, pois todos implementam a mesma interface!

### 5. Migrar Dados (Se Necessário)

Se você já tem dados no Redis e precisa migrá-los:

```python
from src.rag import create_vector_store
from src.rag.embeddings import generate_embeddings

# Conectar ao Redis antigo
old_store = create_vector_store('redis')

# Conectar ao novo store
new_store = create_vector_store('qdrant')

# Criar índice no novo store
new_store.create_index()

# TODO: Implementar script de migração completo
# Por enquanto, re-indexar os documentos é a abordagem mais simples
```

### 6. Re-indexar Documentos

A forma mais simples é re-indexar todos os documentos:

```bash
# Executar script de build da knowledge base
python scripts/build_knowledge_base.py
```

O script automaticamente usará o vector store configurado no `.env`.

---

## Atualizando Código Existente

### Interface Comum

Todos os vector stores implementam a mesma interface:

```python
from src.rag import BaseVectorStore

class MeuVectorStore(BaseVectorStore):
    def create_index(self, index_name, force_recreate=False, **kwargs): ...
    def add_documents(self, documents, embeddings, index_name=None): ...
    def vector_search(self, query_embedding, k=10, filter_dict=None, index_name=None): ...
    def text_search(self, query, k=10, filter_dict=None, index_name=None): ...
    def hybrid_search(self, query, query_embedding, k=10, weights=(0.7, 0.3), ...): ...
    def delete_documents(self, document_ids, index_name=None): ...
    def delete_index(self, index_name=None): ...
    def get_stats(self, index_name=None): ...
    def health_check(self): ...
```

### Exemplo Completo

```python
from src.rag import create_vector_store, SearchResult
import numpy as np

# 1. Criar vector store
store = create_vector_store()  # Usa configuração do .env

# 2. Verificar saúde
if not store.health_check():
    raise Exception("Vector store não está acessível!")

# 3. Criar índice
store.create_index(force_recreate=True)

# 4. Adicionar documentos
documents = [
    {
        'id': '1',
        'content': 'O BSC é uma metodologia de gestão estratégica...',
        'source': 'livro_bsc.pdf',
        'page': 1,
        'metadata': {'category': 'conceito'}
    }
]

embeddings = [np.random.rand(3072)]  # Substitua por embeddings reais

store.add_documents(documents, embeddings)

# 5. Buscar
query_embedding = np.random.rand(3072)  # Substitua por embedding real

results = store.hybrid_search(
    query="O que é BSC?",
    query_embedding=query_embedding,
    k=5,
    weights=(0.7, 0.3)
)

# 6. Processar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Source: {result.source}")
    print(f"Content: {result.content[:100]}...")
    print()

# 7. Estatísticas
stats = store.get_stats()
print(f"Documentos indexados: {stats.num_documents}")
```

---

## Diferenças Entre Vector Stores

### Hybrid Search

**Qdrant:**

- Hybrid search não é nativo
- Combina resultados manualmente
- Para BM25 real, integre com Elasticsearch

**Weaviate:**

- Hybrid search nativo com BM25
- Usa parâmetro `alpha` para controlar peso
- Melhor opção se hybrid search for crítico

**Redis:**

- Full-text search básico
- Combina resultados manualmente
- Sem BM25 robusto

### Filtros

**Qdrant:**

```python
results = store.vector_search(
    query_embedding,
    filter_dict={'source': 'doc1.pdf', 'page': 5}
)
```

**Weaviate:**

```python
results = store.vector_search(
    query_embedding,
    filter_dict={'source': 'doc1.pdf'}
)
```

**Redis:**

- Filtros limitados
- Recomenda-se filtrar resultados após busca

---

## Comparação de Performance

Execute o benchmark para comparar:

```bash
# Certifique-se de que todos estão rodando
docker-compose up -d qdrant weaviate redis

# Execute o benchmark
python tests/benchmark_vector_stores.py

# Veja resultados
cat tests/benchmark_results.json | python -m json.tool
```

Resultados típicos esperados:

| Métrica | Qdrant | Weaviate | Redis |
|---------|--------|----------|-------|
| Latência P95 (ms) | ~40-60 | ~50-80 | ~30-50 |
| Recall@10 | ~0.75 | ~0.78 | ~0.70 |
| Hybrid Search | Manual | Nativo | Manual |
| Integração LangChain | 9/10 | 8/10 | 6/10 |

---

## Rollback

Se precisar voltar para Redis:

1. Atualizar `.env`:

```env
VECTOR_STORE_TYPE=redis
```

2. Reiniciar aplicação

O código continua funcionando pois a interface é a mesma!

---

## Troubleshooting

### Erro: "Connection refused"

**Problema**: Vector store não está rodando

**Solução**:

```bash
# Verificar status
docker ps | grep -E "qdrant|weaviate|redis"

# Subir serviço
docker-compose up -d qdrant
```

### Erro: "Collection not found"

**Problema**: Índice não foi criado

**Solução**:

```python
store = create_vector_store()
store.create_index(force_recreate=True)
```

### Performance Ruim

**Problema**: Configuração não otimizada

**Soluções**:

**Qdrant**: Use HNSW ao invés de FLAT para datasets grandes

```python
store.create_index(algorithm="HNSW", m=16, ef_construct=100)
```

**Weaviate**: Ajuste BM25 parameters

```python
# Na criação da coleção, ajuste bm25_b e bm25_k1
```

---

## Próximos Passos

1. ✅ Escolher vector store baseado no benchmark
2. ✅ Atualizar `.env` com configuração
3. ✅ Subir serviço Docker
4. ✅ Re-indexar documentos
5. ✅ Testar queries
6. ⏳ Monitorar performance em produção

---

## Referências

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Comparação Completa](./VECTOR_DB_COMPARISON.md)
- [Benchmark Results](../tests/benchmark_results.json)
