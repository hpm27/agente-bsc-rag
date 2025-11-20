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

- [OK] Open-source e ativo desenvolvimento
- [OK] Excelente performance em queries
- [OK] Integração nativa com LangChain
- [OK] Suporte a filtros complexos
- [OK] API REST e gRPC
- [OK] Documentação excelente

#### Contras

- [ERRO] Hybrid search requer implementação customizada
- [ERRO] Menos features enterprise que Weaviate

#### Features Relevantes para BSC

- **Payload Filtering**: Filtrar por perspectiva BSC, categoria, etc.
- **Scroll API**: Eficiente para processar todos documentos
- **Quantization**: Reduzir uso de memória
- **Sharding**: Escalabilidade horizontal

---

### Weaviate

#### Prós

- [OK] Hybrid search nativo (BM25 + vetorial)
- [OK] Suporte a GraphQL
- [OK] Multi-tenancy nativo
- [OK] Módulos de IA integrados
- [OK] Excelente para RAG

#### Contras

- [ERRO] Mais complexo de configurar
- [ERRO] Maior uso de recursos
- [ERRO] Integração LangChain menos madura que Qdrant

#### Features Relevantes para BSC

- **Hybrid Search**: Combina BM25 e vetorial nativamente
- **Multi-modal**: Suporta texto, imagem (futuro)
- **Generative Search**: Gera respostas diretamente
- **Cross-references**: Relações entre objetos

---

### Redis Stack

#### Prós

- [OK] Muito rápido para operações simples
- [OK] Já está no stack atual
- [OK] Familiaridade da equipe
- [OK] Versátil (cache + vector store)

#### Contras

- [ERRO] Menos features específicas para RAG
- [ERRO] Documentação LangChain menos completa
- [ERRO] Não é especializado em vector search
- [ERRO] Hybrid search menos robusto

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

1. [OK] Executar `python tests/benchmark_vector_stores.py`
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
