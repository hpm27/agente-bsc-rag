# Testes e Benchmarks - Agente BSC RAG

Este diretório contém testes e benchmarks para o projeto Agente BSC RAG.

---

## Benchmark de Vector Databases

### Objetivo

Comparar Qdrant, Weaviate e Redis Stack para escolher o melhor vector database para o projeto.

### Pré-requisitos

1. **Docker e Docker Compose** instalados
2. **Python 3.10+** com dependências instaladas
3. **Chave OpenAI API** configurada no `.env`

### Como Executar

#### 1. Subir os serviços

```bash
# Na raiz do projeto
docker-compose up -d qdrant weaviate redis
```

Aguarde alguns segundos para os serviços iniciarem completamente.

#### 2. Verificar se os serviços estão rodando

```bash
# Qdrant
curl http://localhost:6333/health

# Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Redis
redis-cli ping
```

Todos devem retornar sucesso.

#### 3. Configurar variáveis de ambiente

Certifique-se de que o arquivo `.env` na raiz do projeto contém:

```env
OPENAI_API_KEY=sk-...
```

#### 4. Executar o benchmark

```bash
# Instalar dependências (se ainda não instalou)
pip install -r requirements.txt

# Executar benchmark
python tests/benchmark_vector_stores.py
```

O benchmark irá:

1. Criar índices em cada vector database
2. Indexar 100 documentos BSC simulados
3. Executar 10 queries de teste
4. Calcular métricas de performance e qualidade
5. Gerar relatório comparativo
6. Salvar resultados em `tests/benchmark_results.json`

#### 5. Analisar resultados

Os resultados serão exibidos no terminal e salvos em JSON:

```bash
# Ver resultados salvos
cat tests/benchmark_results.json | python -m json.tool
```

### Métricas Avaliadas

- **Indexação**: Tempo e throughput (docs/segundo)
- **Query Latency**: P50, P95, P99 em milissegundos
- **Recall@10**: Qualidade do retrieval
- **Memória**: Uso de memória durante operações
- **Integração**: Score subjetivo de facilidade de integração com LangChain

### Interpretação dos Resultados

**Latência de Query**:

- Excelente: < 50ms (P95)
- Bom: 50-100ms
- Aceitável: 100-200ms
- Ruim: > 200ms

**Recall@10**:

- Excelente: > 80%
- Bom: 60-80%
- Aceitável: 40-60%
- Ruim: < 40%

**Throughput de Indexação**:

- Excelente: > 100 docs/seg
- Bom: 50-100 docs/seg
- Aceitável: 20-50 docs/seg
- Ruim: < 20 docs/seg

### Limpeza

Após o benchmark, você pode parar os serviços:

```bash
# Parar sem remover dados
docker-compose stop qdrant weaviate redis

# Parar e remover dados
docker-compose down -v
```

---

## Testes Unitários

### Executar todos os testes

```bash
pytest tests/ -v
```

### Executar testes específicos

```bash
# Testar vector store
pytest tests/test_vector_store.py -v

# Testar retriever
pytest tests/test_retriever.py -v

# Testar com coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Testes de Integração

### Executar testes end-to-end

```bash
pytest tests/integration/ -v
```

---

## Avaliação de RAG

### Métricas de Qualidade

O projeto usa duas bibliotecas para avaliar qualidade do RAG:

1. **RAGAS**: Framework completo para avaliação RAG
2. **DeepEval**: Avaliação com LLMs

### Executar avaliação

```bash
# Avaliação completa
python tests/evaluation/rag_evaluation.py

# Apenas Recall e Precision
python tests/evaluation/rag_evaluation.py --metrics recall precision

# Com dataset customizado
python tests/evaluation/rag_evaluation.py --dataset tests/evaluation/custom_queries.json
```

---

## Estrutura de Diretórios

```
tests/
├── README.md                     # Este arquivo
├── benchmark_vector_stores.py    # Benchmark Qdrant vs Weaviate vs Redis
├── benchmark_results.json        # Resultados do benchmark (gerado)
├── test_vector_store.py          # Testes unitários vector store
├── test_retriever.py             # Testes unitários retriever
├── test_embeddings.py            # Testes unitários embeddings
├── test_chunker.py               # Testes unitários chunker
├── test_reranker.py              # Testes unitários reranker
├── evaluation/
│   ├── rag_evaluation.py         # Framework de avaliação RAG
│   ├── test_queries_bsc.json     # Dataset de queries BSC
│   └── custom_queries.json       # Queries customizadas (opcional)
└── integration/
    ├── test_e2e.py               # Testes end-to-end
    └── test_pipeline.py          # Testes de pipeline completo
```

---

## Troubleshooting

### Erro: "Connection refused" ao conectar vector databases

**Solução**: Verifique se os serviços estão rodando:

```bash
docker ps | grep -E "qdrant|weaviate|redis"
```

Se não estiverem, suba novamente:

```bash
docker-compose up -d qdrant weaviate redis
```

### Erro: "OpenAI API key not found"

**Solução**: Configure a chave no `.env`:

```bash
echo "OPENAI_API_KEY=sk-sua-chave-aqui" >> .env
```

### Erro: "Module not found"

**Solução**: Instale as dependências:

```bash
pip install -r requirements.txt
```

### Benchmark muito lento

**Solução**: O benchmark gera embeddings usando OpenAI API, o que pode ser lento. Para acelerar:

1. Reduza o número de documentos no dataset (edite `benchmark_vector_stores.py`)
2. Use embeddings menores (ex: `text-embedding-3-small` com 1536 dims)
3. Execute apenas um vector database por vez

---

## Contribuindo

Ao adicionar novos testes:

1. Siga o padrão de nomenclatura: `test_*.py`
2. Use fixtures do pytest para setup/teardown
3. Documente o propósito de cada teste
4. Adicione assertions claras
5. Mock APIs externas quando possível

---

## Referências

- [pytest Documentation](https://docs.pytest.org/)
- [RAGAS Documentation](https://docs.ragas.io/)
- [DeepEval Documentation](https://docs.deepeval.com/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [Weaviate Python Client](https://github.com/weaviate/weaviate-python-client)
