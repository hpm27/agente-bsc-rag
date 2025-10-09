# Comparação de Vector Databases para BSC RAG

## Objetivo

Avaliar Qdrant vs Weaviate vs Redis Stack para escolher o melhor vector database para o projeto Agente BSC RAG, considerando:

1. **Performance**: Velocidade de indexação e queries
2. **Qualidade**: Recall e precisão do retrieval
3. **Integração**: Facilidade de uso com LangChain/LangGraph
4. **Features**: Suporte a hybrid search, filtros, etc.
5. **Operacional**: Facilidade de deploy e manutenção

---

## Metodologia de Avaliação

### Dataset de Teste

- **100 documentos** simulados de conteúdo BSC
- **10 queries** representativas de perguntas reais
- **Ground truth** manualmente anotado para calcular recall

### Métricas Avaliadas

1. **Indexação**
   - Tempo total de indexação
   - Documentos por segundo

2. **Query Performance**
   - Latência P50, P95, P99 (ms)
   - Throughput (queries/segundo)

3. **Qualidade de Retrieval**
   - Recall@10 (semântico)
   - Recall@10 (híbrido)
   - Precision@5

4. **Recursos**
   - Uso de memória
   - Uso de CPU

5. **Integração**
   - Score subjetivo (1-10) baseado em:
     - Documentação LangChain
     - Facilidade de setup
     - Features disponíveis

---

## Resultados do Benchmark

> **Status**: ⏳ Aguardando execução do benchmark
>
> Execute: `python tests/benchmark_vector_stores.py`

### Resumo Comparativo

| Métrica | Qdrant | Weaviate | Redis Stack |
|---------|--------|----------|-------------|
| Indexação (docs/seg) | - | - | - |
| Latência P95 (ms) | - | - | - |
| Recall@10 | - | - | - |
| Memória (MB) | - | - | - |
| Score Integração | - | - | - |

---

## Análise Detalhada

### Qdrant

#### Prós

- ✅ Open-source e ativo desenvolvimento
- ✅ Excelente performance em queries
- ✅ Integração nativa com LangChain
- ✅ Suporte a filtros complexos
- ✅ API REST e gRPC
- ✅ Documentação excelente

#### Contras

- ❌ Hybrid search requer implementação customizada
- ❌ Menos features enterprise que Weaviate

#### Features Relevantes para BSC

- **Payload Filtering**: Filtrar por perspectiva BSC, categoria, etc.
- **Scroll API**: Eficiente para processar todos documentos
- **Quantization**: Reduzir uso de memória
- **Sharding**: Escalabilidade horizontal

---

### Weaviate

#### Prós

- ✅ Hybrid search nativo (BM25 + vetorial)
- ✅ Suporte a GraphQL
- ✅ Multi-tenancy nativo
- ✅ Módulos de IA integrados
- ✅ Excelente para RAG

#### Contras

- ❌ Mais complexo de configurar
- ❌ Maior uso de recursos
- ❌ Integração LangChain menos madura que Qdrant

#### Features Relevantes para BSC

- **Hybrid Search**: Combina BM25 e vetorial nativamente
- **Multi-modal**: Suporta texto, imagem (futuro)
- **Generative Search**: Gera respostas diretamente
- **Cross-references**: Relações entre objetos

---

### Redis Stack

#### Prós

- ✅ Muito rápido para operações simples
- ✅ Já está no stack atual
- ✅ Familiaridade da equipe
- ✅ Versátil (cache + vector store)

#### Contras

- ❌ Menos features específicas para RAG
- ❌ Documentação LangChain menos completa
- ❌ Não é especializado em vector search
- ❌ Hybrid search menos robusto

#### Features Relevantes para BSC

- **HNSW Index**: Algoritmo eficiente
- **RediSearch**: Full-text search
- **Redis Streams**: Processamento em tempo real
- **Versatilidade**: Cache + queue + vector store

---

## Decisão

> **Status**: ⏳ Aguardando resultados do benchmark

### Critérios de Decisão

Pesos para escolha final:

- **40%** - Qualidade de retrieval (Recall@10)
- **25%** - Performance de queries (P95 latency)
- **20%** - Integração com LangChain
- **10%** - Facilidade operacional
- **5%** - Features adicionais

### Recomendação Preliminar

Baseado na pesquisa inicial (antes do benchmark):

**1ª Opção: Qdrant**

- Melhor equilíbrio performance/features/integração
- Comunidade ativa e documentação excelente
- Ideal para RAG em produção

**2ª Opção: Weaviate**

- Melhor se hybrid search nativo for crítico
- Mais features enterprise
- Melhor para casos complexos

**3ª Opção: Redis Stack**

- Melhor se simplicidade for prioridade
- Bom para MVP/prototipagem
- Já está no stack atual

---

## Próximos Passos

### Após Benchmark

1. ✅ Executar `python tests/benchmark_vector_stores.py`
2. ⏳ Analisar resultados quantitativos
3. ⏳ Tomar decisão final
4. ⏳ Atualizar este documento com escolha
5. ⏳ Iniciar migração (Fase 1.2)

### Implementação POC

Após escolha do vector database:

1. Implementar adaptador em `src/rag/vector_store.py`
2. Testar com dataset BSC real
3. Validar performance em cenário real
4. Comparar com Redis atual
5. Aprovar migração definitiva

---

## Referências

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Redis Stack Documentation](https://redis.io/docs/stack/)
- [LangChain VectorStores](https://python.langchain.com/docs/modules/data_connection/vectorstores/)
- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)

---

## Histórico de Atualizações

| Data | Autor | Mudança |
|------|-------|---------|
| 2025-10-09 | AI Agent | Documento inicial criado |
| - | - | Aguardando execução do benchmark |
