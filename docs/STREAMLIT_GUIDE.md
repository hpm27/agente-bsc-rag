## Interface Streamlit - Guia do Usuario

### Visao Geral

Interface web moderna e interativa para consultar o sistema multi-agente de Balanced Scorecard. Construida com **Streamlit**, oferece uma experiencia chat-like intuitiva para interagir com os 4 especialistas BSC.

---

## Caracteristicas

### Interface Chat-Like

- **Input natural**: Digite perguntas em linguagem natural
- **Historico de conversacao**: Mantem contexto de queries anteriores
- **Respostas estruturadas**: Resposta principal + detalhes expandiveis
- **Feedback em tempo real**: Spinners e indicadores de progresso

### Perspectivas BSC

- **4 Especialistas**: Financeira, Cliente, Processos Internos, Aprendizado e Crescimento
- **Selecao customizada**: Escolha quais perspectivas consultar
- **Visualizacao por tabs**: Respostas organizadas por perspectiva
- **Codificacao por cores**: Cada perspectiva tem sua cor identificadora

### Configuracoes

- **Retrieval**: Top K documentos, threshold de confianca
- **Workflow**: Iteracoes de refinamento, enable/disable Judge
- **Avancadas**: Temperatura LLM, modelo (GPT-5 vs Claude)

### Display de Resultados

- **Resposta Final**: Sintese integrada de todas as perspectivas
- **Perspectivas Individuais**: Analise detalhada por especialista
- **Documentos Relevantes**: Tabela com scores e fontes
- **Avaliacao do Judge**: Metricas de qualidade, feedback, sugestoes

---

## Instalacao e Execucao

### Pre-requisitos

1. **Ambiente configurado**:

   ```bash
   # Criar e ativar venv
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows
   source venv/bin/activate     # Linux/Mac

   # Instalar dependencias
   pip install -r requirements.txt
   ```

2. **Variaveis de ambiente** (arquivo `.env`):

   ```env
   OPENAI_API_KEY=sk-...
   COHERE_API_KEY=...
   ANTHROPIC_API_KEY=...  # Opcional
   ```

3. **Docker containers rodando**:

   ```bash
   docker-compose up -d
   ```

4. **Base de conhecimento indexada**:

   ```bash
   python scripts/build_knowledge_base.py
   ```

### Executar Streamlit

**Metodo 1: Script de conveniencia**

```bash
python run_streamlit.py
```

**Metodo 2: Streamlit CLI**

```bash
streamlit run app/main.py
```

**Metodo 3: Modulo Python**

```bash
python -m streamlit run app/main.py
```

A aplicacao sera aberta automaticamente no navegador em `http://localhost:8501`.

---

## Guia de Uso

### 1. Interface Inicial

Ao abrir a aplicacao:

- **Sidebar esquerda**: Configuracoes e controles
- **Area principal**: Mensagem de boas-vindas e exemplos
- **Input box**: Campo de texto para digitar perguntas

### 2. Configurar Perspectivas

Na sidebar, marque/desmarque as perspectivas desejadas:

- **Financeira**: Indicadores financeiros, ROI, receita, lucro, EVA
- **Clientes**: Satisfacao, retencao, proposta de valor, segmentacao
- **Processos**: Eficiencia operacional, qualidade, inovacao
- **Aprendizado**: Capital humano, tecnologia, cultura organizacional

**Dica**: Deixe todas ativas para resposta mais completa, ou selecione especificas para foco direcionado.

### 3. Ajustar Configuracoes

**Configuracoes de Busca**:

- **Top K Documentos** (5-20): Numero de docs a recuperar
  - Mais docs = mais contexto, mas tempo maior
  - Recomendado: 10

- **Threshold de Confianca** (0.0-1.0): Score minimo para aceitar resposta
  - Maior = mais exigente
  - Recomendado: 0.7

**Configuracoes do Workflow**:

- **Max Iteracoes de Refinamento** (0-2): Ciclos com Judge Agent
  - 0 = sem refinamento
  - 2 = maximo refinamento (mais tempo)
  - Recomendado: 2

- **Habilitar Judge Agent**: Validacao de qualidade
  - Recomendado: Sempre habilitado

**Configuracoes Avancadas** (expander):

- **Temperatura LLM** (0.0-1.0): Criatividade vs determinismo
  - 0.0 = mais deterministico
  - 1.0 = mais criativo
  - Recomendado: 0.7

- **Modelo LLM**: GPT-5 ou Claude Sonnet 4.5
  - GPT-5: Melhor raciocinio geral
  - Claude: Melhor para agentes e codigo

- **Vector Store**: Qdrant, Weaviate ou Redis (informativo)

### 4. Fazer Perguntas

Digite sua pergunta no campo de input e pressione Enter.

**Exemplos de perguntas**:

**Iniciante**:

- "O que e Balanced Scorecard?"
- "Quais sao as 4 perspectivas do BSC?"
- "Como comecar a implementar um BSC?"

**Intermediario**:

- "Quais KPIs usar na perspectiva financeira?"
- "Como criar um mapa estrategico eficaz?"
- "Qual a relacao entre as 4 perspectivas?"

**Avancado**:

- "Como integrar BSC com OKRs e KPIs tradicionais?"
- "Quais indicadores leading vs lagging usar em cada perspectiva?"
- "Como medir ROI da implementacao de um BSC?"

### 5. Interpretar Resultados

**Resposta Principal**:

- Sintese integrada consultando todas as perspectivas ativas
- Formatada em Markdown para facil leitura
- Cita fontes quando apropriado

**Perspectivas Consultadas** (expander):

- **Tabs por perspectiva**: Clique para ver analise de cada especialista
- **Cor identificadora**: Cada perspectiva tem sua cor
- **Confianca**: Score 0-100% da qualidade da resposta
- **Fontes**: Lista de documentos consultados

**Documentos Relevantes** (expander):

- **Tabela interativa**: Score, fonte, conteudo truncado
- **Checkbox "Mostrar completos"**: Ver documentos inteiros
- **Ordenado por score**: Mais relevantes primeiro

**Avaliacao do Judge** (expander):

- **Veredito**: Aprovado / Necessita Refinamento / Reprovado
  - Verde: Aprovado (score >= 0.8)
  - Laranja: Necessita refinamento (0.6-0.79)
  - Vermelho: Reprovado (< 0.6)
- **Metricas**: Score geral, completude, fundamentacao
- **Feedback**: Analise qualitativa
- **Problemas**: Issues identificados
- **Sugestoes**: Melhorias recomendadas

### 6. Gerenciar Historico

**Limpar Chat**:

- Botao "Limpar Chat" na sidebar
- Remove todo historico de conversacao
- Util para comecar nova consulta sem contexto anterior

**Resetar Config**:

- Botao "Resetar Config" na sidebar
- Volta configuracoes para valores padrao
- Util se ajustes experimentais nao funcionaram

---

## Personalizacao

### CSS Customizado

O arquivo `app/main.py` contem CSS customizado para styling:

- Cores das perspectivas
- Layout de mensagens
- Badges e metricas
- Loading spinners

Para personalizar, edite a secao `st.markdown("""<style>...</style>""")`.

### Adicionar Novas Perspectivas

1. Editar `app/components/sidebar.py`:
   - Adicionar checkbox para nova perspectiva

2. Editar `app/utils.py`:
   - Adicionar mapeamento em `format_perspective_name()`
   - Adicionar cor em `get_perspective_color()`

3. Implementar agente correspondente em `src/agents/`

### Customizar Layout

Streamlit usa layout baseado em colunas e containers:

```python
# 2 colunas
col1, col2 = st.columns(2)
with col1:
    st.metric("Metrica 1", "100")
with col2:
    st.metric("Metrica 2", "200")

# Expander
with st.expander("Detalhes"):
    st.write("Conteudo expandivel")

# Tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Conteudo tab 1")
```

---

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'streamlit'"

```bash
# Instalar streamlit
pip install streamlit==1.29.0
```

### Erro: "Variaveis de ambiente obrigatorias faltando"

Verificar arquivo `.env`:

```env
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...
```

Se variaveis estao corretas, recarregar aplicacao (Ctrl+C e reexecutar).

### Erro: "Falha ao inicializar workflow"

Verificar:

1. **Docker containers rodando**:

   ```bash
   docker-compose ps
   ```

2. **Base de conhecimento indexada**:

   ```bash
   python scripts/build_knowledge_base.py
   ```

3. **Dependencias instaladas**:

   ```bash
   pip install -r requirements.txt
   ```

### Erro: "UnicodeEncodeError" em logs

Este erro **NAO DEVE** ocorrer se o codigo esta conforme (zero emojis).

Se ocorrer:

1. Verificar pre-commit hooks:

   ```bash
   pre-commit run check-no-emoji --all-files
   ```

2. Corrigir emojis manualmente:

   ```bash
   python scripts/check_no_emoji.py app/**/*.py
   ```

### Interface lenta / Timeout

Ajustar configuracoes:

- **Reduzir Top K**: 20 → 10 → 5
- **Desabilitar perspectivas**: Marcar apenas 1-2
- **Desabilitar refinamento**: Max iteracoes = 0
- **Simplificar query**: Perguntas mais diretas

### Streamlit trava ou nao responde

1. **Parar aplicacao**: Ctrl+C no terminal

2. **Limpar cache**:

   ```bash
   streamlit cache clear
   ```

3. **Reexecutar**:

   ```bash
   streamlit run app/main.py
   ```

---

## Performance

### Metricas Esperadas

| Configuracao | Tempo de Resposta | Qualidade |
|--------------|-------------------|-----------|
| 1 perspectiva, top_k=5 | 5-10s | Media |
| 2 perspectivas, top_k=10 | 10-15s | Boa |
| 4 perspectivas, top_k=10 | 15-25s | Otima |
| 4 perspectivas, top_k=20, refinamento | 30-45s | Maxima |

**Fatores de performance**:

- Numero de perspectivas consultadas
- Top K documentos
- Iteracoes de refinamento do Judge
- Velocidade da API (OpenAI, Cohere, Anthropic)
- Tamanho da base de conhecimento

### Otimizacoes

**Para respostas mais rapidas**:

1. Reduzir top_k para 5
2. Consultar apenas 1-2 perspectivas
3. Desabilitar refinamento (max_iterations=0)
4. Usar cache do Streamlit (ja implementado)

**Para melhor qualidade**:

1. Aumentar top_k para 15-20
2. Consultar todas as 4 perspectivas
3. Habilitar refinamento (max_iterations=2)
4. Usar Judge Agent sempre

---

## Deployment (Futuro)

### Streamlit Cloud

```bash
# 1. Criar requirements.txt para produção
pip freeze > requirements.txt

# 2. Criar streamlit config
mkdir -p .streamlit
cat > .streamlit/config.toml << EOF
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF

# 3. Deploy para Streamlit Cloud
# Seguir docs: https://docs.streamlit.io/streamlit-community-cloud
```

### Docker

```dockerfile
# Dockerfile (exemplo futuro)
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app/main.py"]
```

---

## Referencias

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit API Reference](https://docs.streamlit.io/library/api-reference)
- [Streamlit Gallery](https://streamlit.io/gallery)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- Documentacao interna: `docs/LANGGRAPH_WORKFLOW.md`

---

**Ultima atualizacao**: 2025-10-10  
**Versao**: 1.0 (MVP)  
**Status**: COMPLETO E FUNCIONAL
