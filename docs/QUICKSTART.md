# [EMOJI] Guia de Início Rápido - Agente BSC RAG

> **Objetivo**: Colocar o sistema BSC RAG funcionando em **menos de 10 minutos** [TIMER]

Este guia cobre:
1. [OK] Instalação e configuração inicial
2. [OK] Primeira execução e query
3. [OK] Verificação de funcionamento
4. [OK] Troubleshooting comum
5. [OK] Próximos passos

---

## [EMOJI] Pré-requisitos

Antes de começar, certifique-se de ter:

| Requisito | Versão | Como Verificar |
|-----------|--------|----------------|
| **Python** | 3.12+ | `python --version` |
| **Docker Desktop** | Qualquer | Abra o Docker Desktop |
| **Git** | Qualquer | `git --version` |
| **RAM** | 8GB+ | Gerenciador de Tarefas -> Performance |

**API Keys Necessárias**:
- [OK] **OpenAI API Key** - [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [OK] **Cohere API Key** - [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)
- [OK] **Anthropic API Key** - [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

[EMOJI] **Dica**: As 3 plataformas oferecem créditos gratuitos para novos usuários.

---

## [EMOJI] Instalação em 4 Passos

### Passo 1: Clone o Repositório

```powershell
# Clone o projeto
git clone https://github.com/seu-usuario/agente-bsc-rag.git

# Entre no diretório
cd agente-bsc-rag
```

### Passo 2: Execute o Setup Automatizado

**Windows PowerShell**:

```powershell
.\setup.ps1
```

**Linux/Mac**:

```bash
chmod +x setup.sh
./setup.sh
```

O script `setup.ps1` faz **TUDO automaticamente**:

```
[CHECK] Verificando Python 3.12+... OK
[CHECK] Verificando Docker Desktop... OK
[SETUP] Criando ambiente virtual Python... OK
[SETUP] Instalando dependências (requirements.txt)... OK (45 segundos)
[SETUP] Iniciando Docker Compose (Qdrant)... OK
[SETUP] Criando arquivo .env... OK
[DONE] Setup completo! Configure suas API keys no .env
```

[TIMER] **Tempo estimado**: 2-3 minutos

### Passo 3: Configure API Keys

1. Abra o arquivo `.env` na raiz do projeto
2. Adicione suas chaves de API:

```env
# APIs de IA (OBRIGATÓRIO)
OPENAI_API_KEY=sk-proj-XXXXX...
COHERE_API_KEY=XXXXXX...
ANTHROPIC_API_KEY=sk-ant-XXXXX...
```

3. Salve o arquivo (Ctrl+S)

[EMOJI] **Dica**: Se estiver usando VS Code, o arquivo `.env` será aberto automaticamente após o setup.

**Validar configuração**:

```powershell
python scripts/valida_env.py
```

Resultado esperado:

```
[CHECK] OPENAI_API_KEY: OK
[CHECK] COHERE_API_KEY: OK
[CHECK] ANTHROPIC_API_KEY: OK
[CHECK] Qdrant (localhost:6333): OK
[OK] Todas as configurações estão corretas!
```

### Passo 4: Indexe o Dataset BSC

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Indexar documentos BSC
python scripts/build_knowledge_base.py
```

**O que acontece**:

```
[INFO] Iniciando ingestão de documentos BSC...
[INFO] Encontrados 5 documentos em data/bsc_literature/
[INFO] Processando com Contextual Chunker (10 workers paralelos)...
[PROGRESS] Batch 1/80 (100 docs)... OK
[PROGRESS] Batch 2/80 (100 docs)... OK
...
[PROGRESS] Batch 80/80 (65 docs)... OK
[STATS] 7.965 chunks indexados em Qdrant
[STATS] 7.965 contextos bilíngues (PT-BR + EN)
[STATS] Tempo total: ~12 minutos
[OK] Knowledge base pronta para uso!
```

[TIMER] **Tempo estimado**: 10-15 minutos (depende da API Anthropic)

[EMOJI] **Dica**: Se já tiver processado antes, o cache será usado e levará apenas ~30 segundos.

---

## [EMOJI] Primeira Execução

### Iniciar a Interface Streamlit

**Método 1: Script de conveniência** (Recomendado)

```powershell
python run_streamlit.py
```

**Método 2: Streamlit CLI**

```powershell
streamlit run app/main.py
```

**Resultado**:

```
[INFO] Streamlit rodando em: http://localhost:8501
[INFO] Network URL: http://192.168.1.100:8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

[EMOJI] **A interface abrirá automaticamente no navegador.**

---

## [EMOJI] Primeira Query

### Exemplo 1: Query Simples (Perspectiva Única)

**Digite na interface**:

```
Quais são os principais KPIs da perspectiva financeira segundo Kaplan & Norton?
```

**Resultado Esperado**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPOSTA FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Segundo Kaplan & Norton, os principais KPIs da perspectiva financeira incluem:

1. ROI (Return on Investment)
   - Retorno sobre investimento
   - Medição de lucratividade

2. Crescimento de Receita
   - Receita total
   - Crescimento ano a ano

3. Produtividade
   - Receita por funcionário
   - Margem operacional

4. Mix de Produtos
   - % receita de novos produtos
   - Rentabilidade por linha de produto

[... mais detalhes ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSPECTIVAS CONSULTADAS: Financial (1)
DOCUMENTOS RECUPERADOS: 10
SCORE DO JUDGE: 0.92 (Aprovado)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Exemplo 2: Query Complexa (Multi-Perspectiva)

**Digite na interface**:

```
Como a satisfação do cliente impacta a lucratividade da empresa?
```

**Resultado Esperado**:

```
PERSPECTIVAS CONSULTADAS: Customer (Cliente), Financial (Financeira)

A satisfação do cliente impacta a lucratividade através de:

1. Retenção de Clientes (Perspectiva Cliente)
   - Clientes satisfeitos permanecem mais tempo
   - Redução de churn

2. Aumento de Receita (Perspectiva Financeira)
   - Cross-sell e up-sell
   - Lifetime Value maior

3. Redução de Custos (Perspectiva Financeira)
   - Menor custo de aquisição (CAC)
   - Marketing boca a boca

[... mais detalhes ...]
```

### Exemplo 3: Query Conceitual

```
O que é Balanced Scorecard?
```

**Resultado**: Resposta abrangente consultando todas as 4 perspectivas BSC.

---

## [OK] Verificação de Funcionamento

### Checklist de Validação

Execute estas verificações para garantir que tudo está funcionando:

#### 1. Qdrant está rodando?

```powershell
curl http://localhost:6333
```

**Esperado**: `{"title":"qdrant - vector search engine","version":"1.11.x"}`

**OU** abra [http://localhost:6333/dashboard](http://localhost:6333/dashboard) no navegador.

#### 2. Dataset indexado?

```powershell
python -c "from qdrant_client import QdrantClient; client = QdrantClient('localhost', port=6333); print(f'Chunks indexados: {client.count(\"bsc_documents\").count}')"
```

**Esperado**: `Chunks indexados: 7965`

#### 3. API Keys funcionando?

```powershell
python scripts/valida_env.py
```

**Esperado**: Todas as chaves com status `OK`.

#### 4. Interface Streamlit carregando?

- [OK] Abre em [http://localhost:8501](http://localhost:8501)
- [OK] Sidebar com configurações BSC visível
- [OK] Campo de input de query funcional
- [OK] Histórico de conversação vazio

#### 5. Query retorna resultado?

- [OK] Digite uma query e pressione Enter
- [OK] Veja "Processando..." aparecer
- [OK] Resposta é exibida em 30-120 segundos
- [OK] Perspectivas consultadas aparecem
- [OK] Fontes com scores são exibidas
- [OK] Avaliação do Judge aparece (score, feedback)

---

## [EMOJI] Troubleshooting Comum

### Problema 1: `ModuleNotFoundError: No module named 'X'`

**Causa**: Dependências não instaladas ou ambiente virtual não ativado.

**Solução**:

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Reinstalar dependências
pip install -r requirements.txt
```

### Problema 2: `ConnectionRefusedError: [Errno 111] Connection refused` (Qdrant)

**Causa**: Qdrant não está rodando.

**Solução**:

```powershell
# Iniciar Docker Compose
docker-compose up -d qdrant

# Verificar status
docker ps
```

**Esperado**: Container `qdrant` com status `Up`.

### Problema 3: `AuthenticationError: Invalid API key` (OpenAI/Anthropic/Cohere)

**Causa**: API key inválida ou não configurada.

**Solução**:

1. Verifique se o `.env` tem as chaves corretas
2. Certifique-se de que não há espaços extras
3. Teste a chave diretamente:

```powershell
# Testar OpenAI
python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list().data[0].id)"

# Testar Anthropic
python -c "from anthropic import Anthropic; client = Anthropic(); print('OK')"
```

### Problema 4: `UnicodeEncodeError` em logs

**Causa**: Emojis em código Python (problema de encoding Windows).

**Solução**: Já corrigido no MVP. Se encontrar, reporte como issue.

### Problema 5: Interface Streamlit não abre automaticamente

**Causa**: Navegador padrão não configurado ou bloqueio de firewall.

**Solução**: Abra manualmente [http://localhost:8501](http://localhost:8501) no navegador.

### Problema 6: Timeout na indexação de documentos

**Causa**: Rate limit da API Anthropic (Contextual Retrieval).

**Solução**:

```powershell
# Reduzir workers paralelos no .env
CONTEXTUAL_CHUNKER_MAX_WORKERS=5  # Padrão: 10
```

**OU** aguardar 1 minuto e tentar novamente (retry automático implementado).

### Problema 7: Resposta muito lenta (>3 minutos)

**Causas possíveis**:
- Cache de embeddings não ativo
- Muitos agentes sendo executados
- API externa lenta

**Soluções**:

```env
# Ativar cache de embeddings (.env)
ENABLE_EMBEDDING_CACHE=true

# Reduzir perspectivas na sidebar da interface
# (desmarcar perspectivas não relevantes para a query)
```

### Problema 8: `RuntimeError: This event loop is already running`

**Causa**: Conflito de event loops (Jupyter/asyncio).

**Solução**: Não execute em Jupyter Notebooks. Use terminal/PowerShell.

---

## [EMOJI] Próximos Passos

Agora que o sistema está funcionando, explore:

### 1. Interface Streamlit (Uso Básico)

- [EMOJI] **Guia Completo**: [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md)
- [EMOJI] Aprenda a:
  - Interpretar perspectivas BSC
  - Ajustar parâmetros de retrieval
  - Entender scores do Judge
  - Visualizar fontes

### 2. Uso Programático (API)

- [EMOJI] **Referência Completa**: [API_REFERENCE.md](API_REFERENCE.md)
- [EMOJI] Exemplo básico:

```python
from src.graph.workflow import get_workflow

workflow = get_workflow()
result = workflow.run(
    query="Como definir objetivos para a perspectiva financeira?",
    session_id="my-session"
)

print(result['final_response'])
```

### 3. Customização

- [EMOJI] **Tutorial Avançado**: [TUTORIAL.md](TUTORIAL.md)
- [EMOJI] Aprenda a:
  - Adicionar novos documentos BSC
  - Modificar prompts de agentes
  - Ajustar thresholds do Judge
  - Customizar perspectivas BSC

### 4. Testes e Validação

- [EMOJI] **Guia de Testes**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- [EMOJI] Execute testes E2E:

```powershell
pytest tests/integration/test_e2e.py -v
```

### 5. Deploy em Produção

- [EMOJI] **Guia de Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- [EMOJI] Opções:
  - Deploy local (systemd service)
  - Deploy Docker (container otimizado)
  - Deploy Cloud (AWS/Azure/GCP)

---

## [EMOJI] Recursos Adicionais

### Documentação Oficial

- [EMOJI] [README.md](../README.md) - Overview completo do projeto
- [EMOJI] [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitetura detalhada
- [EMOJI] [LANGGRAPH_WORKFLOW.md](LANGGRAPH_WORKFLOW.md) - Workflow LangGraph

### Otimizações e Performance

- [FAST] [MULTILINGUAL_OPTIMIZATION_SUMMARY.md](../MULTILINGUAL_OPTIMIZATION_SUMMARY.md) - Busca cross-lingual
- [EMOJI] [VECTOR_DB_COMPARISON.md](VECTOR_DB_COMPARISON.md) - Benchmark Qdrant vs Weaviate

### Exemplos Práticos

- [EMOJI] [examples/run_workflow_example.py](../examples/run_workflow_example.py) - Uso programático
- [EMOJI] [tests/integration/test_queries.json](../tests/integration/test_queries.json) - 20 queries BSC de exemplo

---

## [EMOJI] Dicas Pro

### Atalhos de Produtividade

1. **Alias para ativar ambiente virtual**:

```powershell
# Adicionar ao PowerShell Profile
Set-Alias -Name bsc -Value "cd D:\path\to\agente-bsc-rag; .\venv\Scripts\Activate.ps1"
```

2. **Script de inicialização rápida**:

```powershell
# start-bsc.ps1
.\venv\Scripts\Activate.ps1
docker-compose up -d qdrant
python run_streamlit.py
```

3. **Verificação rápida de status**:

```powershell
# status-bsc.ps1
docker ps --filter name=qdrant
python scripts/valida_env.py
```

### Queries de Exemplo para Testar

```
[Simples]
- Quais são as 4 perspectivas do BSC?
- O que é mapa estratégico?
- Exemplos de KPIs da perspectiva de clientes

[Médias]
- Como relacionar objetivos de aprendizado com objetivos financeiros?
- Diferença entre indicadores de resultado e indicadores de tendência
- Como implementar BSC em uma empresa de tecnologia?

[Complexas]
- Qual a cadeia de causa e efeito entre capacitação de funcionários e lucratividade?
- Como o BSC se integra com planejamento estratégico e orçamento?
- Explique o conceito de Strategy Map com um exemplo prático
```

---

## [EMOJI] Suporte

Se encontrar problemas não cobertos neste guia:

1. [EMOJI] Consulte [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (se existir)
2. [EMOJI] Busque em [Issues abertas](https://github.com/seu-usuario/agente-bsc-rag/issues)
3. 🆕 Abra uma [Nova Issue](https://github.com/seu-usuario/agente-bsc-rag/issues/new) com:
   - Descrição do problema
   - Mensagem de erro completa
   - Ambiente (Windows/Linux, Python version, Docker version)
   - Passos para reproduzir

---

## [OK] Checklist Final

Antes de considerar o setup completo, verifique:

- [ ] Python 3.12+ instalado e funcionando
- [ ] Docker Desktop rodando
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (requirements.txt)
- [ ] Arquivo .env configurado com API keys válidas
- [ ] Qdrant rodando em localhost:6333
- [ ] Dataset BSC indexado (7.965 chunks)
- [ ] Interface Streamlit abre em localhost:8501
- [ ] Primeira query retorna resposta em <120s
- [ ] Perspectivas BSC aparecem corretamente
- [ ] Fontes são exibidas com scores
- [ ] Avaliação do Judge funciona (score >0.7)

---

<p align="center">
  <strong>[EMOJI] Parabéns! Você está pronto para usar o Agente BSC RAG!</strong><br>
  <em>Próximo passo: Explore <a href="TUTORIAL.md">TUTORIAL.md</a> para uso avançado</em>
</p>
