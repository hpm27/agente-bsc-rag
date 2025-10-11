# LangGraph Workflow - Sistema BSC Multi-Agente

## 📋 Visão Geral

O **LangGraph Workflow** é o componente de orquestração do sistema BSC RAG que coordena a execução de múltiplos agentes especialistas usando um grafo de estados gerenciado pelo [LangGraph](https://github.com/langchain-ai/langgraph).

### Características Principais

- ✅ **Orquestração Visual**: Grafo de estados explícito e auditável
- ✅ **Refinamento Iterativo**: Loop de melhoria baseado em avaliação do Judge
- ✅ **Execução Paralela**: Agentes especialistas executam simultaneamente
- ✅ **State Management**: Estado tipado e validado com Pydantic
- ✅ **Decisão Condicional**: Branching baseado em avaliação de qualidade
- ✅ **Recuperação de Erros**: Fallbacks em cada nó

---

## 🏗️ Arquitetura do Grafo

```
START
  ↓
analyze_query
  │ Analisa query e determina perspectivas relevantes
  ↓
execute_agents
  │ Executa agentes especialistas em paralelo
  ↓
synthesize_response
  │ Sintetiza respostas em resposta unificada
  ↓
judge_evaluation
  │ Avalia qualidade com Judge Agent
  ↓
decide_next_step (conditional)
  ├─ [approved] → finalize
  ├─ [needs_refinement] → execute_agents (loop)
  └─ [default] → finalize
       ↓
     END
```

### Nós do Grafo

#### 1. `analyze_query`

**Responsabilidade**: Analisar a pergunta do usuário e determinar roteamento

**Input**:

- `query`: Pergunta do usuário
- `session_id`: ID da sessão (opcional)

**Output**:

- `relevant_perspectives`: Lista de perspectivas BSC a consultar
- `query_type`: Tipo da query ("general", "specific")
- `complexity`: Complexidade ("simple", "complex")
- `metadata.routing_reasoning`: Justificativa do roteamento

**Lógica**:

1. Usa `Orchestrator.route_query()` para determinar agentes
2. Mapeia nomes de agentes para `PerspectiveType` enum
3. Classifica tipo e complexidade da query

---

#### 2. `execute_agents`

**Responsabilidade**: Executar agentes especialistas em paralelo

**Input**:

- `query`: Pergunta do usuário
- `relevant_perspectives`: Perspectivas a consultar
- `metadata.chat_history`: Histórico de conversa (opcional)

**Output**:

- `agent_responses`: Lista de `AgentResponse` com respostas dos agentes

**Lógica**:

1. Mapeia `PerspectiveType` de volta para nomes de agentes
2. Usa `Orchestrator.invoke_agents()` para executar em paralelo
3. Converte respostas para modelo Pydantic `AgentResponse`
4. Extrai fontes e confidence dos `intermediate_steps`

**Nota**: Este nó pode ser executado múltiplas vezes em caso de refinamento.

---

#### 3. `synthesize_response`

**Responsabilidade**: Sintetizar múltiplas respostas em uma resposta unificada

**Input**:

- `query`: Pergunta original
- `agent_responses`: Lista de respostas dos agentes

**Output**:

- `aggregated_response`: Resposta sintetizada
- `metadata.synthesis_confidence`: Confiança da síntese (0-1)
- `metadata.perspectives_covered`: Perspectivas incluídas na síntese

**Lógica**:

1. Formata respostas dos agentes para o Orchestrator
2. Usa `Orchestrator.synthesize_responses()` com LLM
3. Combina insights de múltiplas perspectivas
4. Mantém citações de fontes
5. Calcula confidence score

---

#### 4. `judge_evaluation`

**Responsabilidade**: Avaliar qualidade da resposta sintetizada

**Input**:

- `query`: Pergunta original
- `aggregated_response`: Resposta sintetizada

**Output**:

- `judge_evaluation`: Objeto `JudgeEvaluation` com:
  - `approved`: Boolean (true se aprovado)
  - `score`: Score de qualidade (0-1)
  - `feedback`: Feedback textual
  - `issues`: Lista de problemas encontrados
  - `suggestions`: Lista de sugestões de melhoria
- `needs_refinement`: Boolean (true se precisa refinar)

**Critérios de Avaliação**:

- ✅ **Aprovado** (`approved=True`): score >= 0.8 e bem fundamentado
- 🟡 **Precisa Melhoria** (`needs_improvement`): 0.5 <= score < 0.8
- ❌ **Rejeitado** (`rejected`): score < 0.5 ou não fundamentado

---

#### 5. `finalize`

**Responsabilidade**: Preparar resposta final para o usuário

**Input**:

- `aggregated_response`: Resposta sintetizada
- `judge_evaluation`: Avaliação do Judge
- `refinement_iteration`: Número de refinamentos realizados

**Output**:

- `final_response`: Resposta final formatada
- `is_complete`: True (marca workflow como completo)
- `metadata.total_refinements`: Total de refinamentos
- `metadata.final_score`: Score final do Judge

**Lógica**:

1. Usa `aggregated_response` como base
2. Se reprovado, adiciona aviso de qualidade
3. Marca workflow como completo
4. Registra métricas finais

---

### Edge Condicional: `decide_next_step`

**Responsabilidade**: Decidir próximo passo após avaliação do Judge

**Condições**:

| Condição | Ação | Próximo Nó |
|----------|------|------------|
| `judge_evaluation.approved == True` | Finalizar | `finalize` |
| `needs_refinement == True` e `iteration < max` | Refinar | `execute_agents` |
| `iteration >= max_refinement_iterations` | Finalizar (força) | `finalize` |
| Padrão | Finalizar | `finalize` |

**Máximo de Refinamentos**: 2 iterações (configurável via `BSCState.max_refinement_iterations`)

---

## 💾 Estado do Workflow (`BSCState`)

O estado do workflow é gerenciado por um modelo Pydantic `BSCState`:

```python
class BSCState(BaseModel):
    # Input
    query: str
    session_id: Optional[str] = None
    
    # Análise da query
    relevant_perspectives: List[PerspectiveType] = []
    query_type: Optional[str] = None
    complexity: Optional[str] = None
    
    # Respostas dos agentes
    agent_responses: List[AgentResponse] = []
    
    # Agregação
    aggregated_response: Optional[str] = None
    
    # Validação
    judge_evaluation: Optional[JudgeEvaluation] = None
    
    # Refinamento
    refinement_iteration: int = 0
    max_refinement_iterations: int = 2
    
    # Output final
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    # Controle de fluxo
    needs_refinement: bool = False
    is_complete: bool = False
```

---

## 🚀 Uso Básico

### Exemplo 1: Query Simples

```python
from src.graph.workflow import get_workflow

# Obter instância do workflow (singleton)
workflow = get_workflow()

# Executar query
result = workflow.run(
    query="O que é Balanced Scorecard?",
    session_id="user-123"
)

# Acessar resultado
print(result["final_response"])
print(f"Perspectivas consultadas: {result['perspectives']}")
print(f"Score do Judge: {result['judge_evaluation']['score']}")
```

### Exemplo 2: Query com Histórico

```python
chat_history = [
    {"role": "user", "content": "O que é BSC?"},
    {"role": "assistant", "content": "BSC é uma metodologia..."}
]

result = workflow.run(
    query="Quais são as 4 perspectivas?",
    chat_history=chat_history
)
```

### Exemplo 3: Inspecionar Detalhes

```python
result = workflow.run(query="Como melhorar ROI?")

# Respostas individuais dos agentes
for agent_resp in result["agent_responses"]:
    print(f"Perspectiva: {agent_resp['perspective']}")
    print(f"Confidence: {agent_resp['confidence']}")
    print(f"Resposta: {agent_resp['content'][:100]}...")

# Avaliação do Judge
judge = result["judge_evaluation"]
print(f"Aprovado: {judge['approved']}")
print(f"Feedback: {judge['feedback']}")
print(f"Issues: {judge['issues']}")
print(f"Sugestões: {judge['suggestions']}")

# Métricas
print(f"Refinamentos: {result['refinement_iterations']}")
```

---

## 📊 Formato da Resposta

```python
{
    "query": str,                    # Query original
    "final_response": str,           # Resposta final sintetizada
    "perspectives": List[str],       # Perspectivas consultadas
    "agent_responses": [             # Respostas individuais
        {
            "perspective": str,
            "content": str,
            "confidence": float
        }
    ],
    "judge_evaluation": {            # Avaliação do Judge
        "approved": bool,
        "score": float,
        "feedback": str,
        "issues": List[str],
        "suggestions": List[str]
    },
    "refinement_iterations": int,    # Número de refinamentos
    "metadata": dict                 # Metadados adicionais
}
```

---

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# APIs necessárias
OPENAI_API_KEY=sk-...          # Para agentes e synthesis
ANTHROPIC_API_KEY=sk-ant-...   # Para contextual retrieval
COHERE_API_KEY=...             # Para re-ranking

# Qdrant (vector store)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=bsc_collection
```

### Parâmetros Customizáveis

No código `src/graph/states.py`:

```python
class BSCState(BaseModel):
    max_refinement_iterations: int = 2  # Ajustar máximo de refinamentos
```

No código `src/agents/orchestrator.py`:

```python
self.llm = ChatOpenAI(
    model="gpt-4",           # Modelo LLM
    temperature=0.3,         # Criatividade
    max_tokens=2000          # Tamanho da resposta
)
```

---

## 🧪 Testes

### Executar Testes Unitários

```bash
# Testes unitários (não requerem APIs)
pytest tests/test_workflow.py -v

# Testes específicos
pytest tests/test_workflow.py::TestBSCWorkflow::test_workflow_initialization
```

### Executar Testes de Integração

```bash
# Testes de integração (requerem APIs configuradas + Qdrant rodando)
pytest tests/test_workflow.py::TestBSCWorkflowIntegration -v -s
```

### Executar Exemplo Interativo

```bash
python examples/run_workflow_example.py
```

Opções:

1. Executar queries de exemplo
2. Modo interativo (fazer suas próprias perguntas)
3. Visualizar estrutura do grafo

---

## 📈 Performance

### Latência Esperada

| Cenário | Latência (P95) | Descrição |
|---------|----------------|-----------|
| Query simples (1 agente) | ~3-5s | Execução + synthesis + judge |
| Query complexa (4 agentes) | ~5-8s | Execução paralela + synthesis + judge |
| Com refinamento (1 iteração) | +3-5s | Re-execução dos agentes |

**Fatores que impactam latência**:

- Número de agentes acionados (1-4)
- Tamanho do knowledge base (retrieval)
- Latência das APIs (OpenAI, Anthropic, Cohere)
- Refinamentos iterativos (0-2)

### Otimizações

✅ **Já Implementadas**:

- Execução paralela de agentes
- Cache de embeddings
- Batch upload para Qdrant
- Contextual caching (Anthropic)

🔮 **Possíveis Melhorias Futuras**:

- Cache de sínteses similares
- Streaming de respostas (LLM streaming)
- Pré-computação de queries frequentes

---

## 🐛 Troubleshooting

### Erro: "No linter errors found"

**Problema**: Imports falhando

**Solução**:

```bash
# Adicionar src ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/caminho/para/projeto/src"

# Ou no Windows
set PYTHONPATH=%PYTHONPATH%;C:\caminho\para\projeto\src
```

### Erro: "Qdrant connection refused"

**Problema**: Qdrant não está rodando

**Solução**:

```bash
# Iniciar Qdrant com Docker
docker-compose up -d qdrant

# Verificar status
docker ps | grep qdrant
```

### Erro: "Rate limit exceeded"

**Problema**: Muitas chamadas para API

**Solução**:

- Aguardar alguns minutos
- Verificar tier da API (Anthropic, OpenAI, Cohere)
- Reduzir `max_refinement_iterations` para 1

### Aviso: "Judge reprovou mas finalizou"

**Problema**: Resposta não atingiu qualidade ideal

**Análise**:

- Verificar `judge_evaluation.feedback` para entender o motivo
- Verificar `judge_evaluation.issues` para problemas específicos
- Considerar melhorar prompts dos agentes
- Considerar expandir knowledge base

---

## 📚 Referências

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [Pydantic Models](https://docs.pydantic.dev/)
- [Balanced Scorecard (Kaplan & Norton)](https://www.balancedscorecard.org/)

---

## 🔄 Próximos Passos

### MVP (Concluído)

- [x] Implementar grafo LangGraph
- [x] Integrar com agentes existentes
- [x] Adicionar loop de refinamento
- [x] Criar testes unitários e de integração
- [x] Documentar workflow

### Melhorias Futuras

- [ ] Visualização do grafo com Mermaid/Graphviz
- [ ] Streaming de respostas em tempo real
- [ ] Cache de sínteses para queries similares
- [ ] Métricas detalhadas de performance
- [ ] Dashboard de observabilidade (traces)
- [ ] Suporte a sessões multi-turn completas

---

**Última Atualização**: 2025-10-10  
**Status**: MVP Completo ✅  
**Versão**: 1.0
