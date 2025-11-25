# [EMOJI] Guia de Teste - Agente BSC RAG

Sistema **100% validado e pronto** para interação real!

---

## [OK] Status Final do Sistema

- **Docker**: 3 containers rodando (Qdrant, Redis, Weaviate)
- **Vector Store**: 7.965 chunks indexados (5 livros Kaplan & Norton)
- **API Keys**: OpenAI + Cohere configurados
- **Streamlit**: Bugs corrigidos (sources + retrieved_documents)
- **Workflow**: LangGraph com 8 agentes + Judge + Orchestrator

---

## [EMOJI] Opção 1: Interface Streamlit (RECOMENDADA)

### Interface web completa com chat interativo, visualização de resultados e métricas.

**Iniciar:**

```powershell
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
streamlit run app/main.py
```

**Aguarde a mensagem:**
```
Local URL: http://localhost:8501
```

**Abra seu navegador:** [http://localhost:8501](http://localhost:8501)

### [EMOJI] Recursos da Interface:

- [OK] Chat interativo com histórico de conversas
- [OK] Visualização por perspectiva BSC (Financeira, Clientes, Processos, Aprendizado)
- [OK] Documentos relevantes com scores de relevância
- [OK] Avaliação do Judge Agent (score, feedback, problemas)
- [OK] Métricas de confiança e fontes consultadas

### [EMOJI] Perguntas Sugeridas:

**Conceituais:**
- "O que é Balanced Scorecard?"
- "Explique o conceito de mapa estratégico"
- "Qual a diferença entre indicadores de resultado e indicadores de tendência?"

**Específicas de Perspectiva:**
- "Quais são os principais KPIs da perspectiva financeira?"
- "Como medir satisfação de clientes no BSC?"
- "Quais indicadores usar para processos internos?"

**Multi-Perspectiva (complexas):**
- "Como a satisfação do cliente impacta a lucratividade?"
- "Qual a relação entre capacitação de funcionários e qualidade dos processos?"
- "Como implementar BSC em uma empresa de tecnologia?"

**Implementação:**
- "Quais são as etapas para implementar um BSC?"
- "Como criar um mapa estratégico eficaz?"
- "Quais os erros comuns na implementação do BSC?"

---

## [EMOJI] Opção 2: Script Python Interativo

### Modo console para testes rápidos e debugging.

**Iniciar:**

```powershell
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
python examples/run_workflow_example.py
```

**Menu Interativo:**
```
1. Executar queries de exemplo (4 queries pré-definidas)
2. Modo interativo (fazer suas próprias perguntas)
3. Visualizar estrutura do grafo
4. Sair
```

### [EMOJI] Queries de Exemplo (Opção 1):

1. "O que é Balanced Scorecard?" (query geral - todas perspectivas)
2. "Quais são os principais KPIs da perspectiva financeira?" (específica)
3. "Como a satisfação do cliente impacta a lucratividade?" (multi-perspectiva)
4. "Qual a relação entre capacitação de funcionários e qualidade dos processos?" (complexa)

### ⌨ Modo Interativo (Opção 2):

- Digite suas perguntas livremente
- Digite "sair" para encerrar
- Veja resultados formatados no console

---

## [EMOJI] O Que Observar Durante os Testes

### 1. **Routing Inteligente**
- Queries simples ("O que é BSC?") -> Todas perspectivas
- Queries específicas ("KPIs financeiros?") -> Apenas perspectiva financeira
- Queries complexas -> Múltiplas perspectivas + Query Decomposition

### 2. **Qualidade das Respostas**
- Respostas devem citar fontes (livros Kaplan & Norton)
- Confiança (confidence) entre 0.7-1.0 = boa qualidade
- Judge Agent deve aprovar (score > 0.8)

### 3. **Performance**
- Query simples: ~10-20s
- Query complexa: ~30-60s
- Multi-perspectiva com decomposição: ~60-90s

### 4. **Documentos Recuperados**
- Hybrid Search (semântico + BM25)
- Re-ranking Cohere (top-10 mais relevantes)
- Scores de relevância > 0.7 = muito relevante

---

## [EMOJI] Troubleshooting Durante os Testes

### Erro: "Connection refused" ao Qdrant
**Solução:**
```powershell
docker ps
# Se Qdrant não estiver healthy:
docker restart bsc-qdrant
# Aguardar 10 segundos
```

### Erro: "OpenAI API Error"
**Solução:**
- Verificar saldo da conta OpenAI
- Verificar se API key está válida no .env
- Trocar para Claude: editar .env -> `DEFAULT_LLM_MODEL=claude-sonnet-4-5-20250929`

### Resposta vazia ou "Nenhuma resposta gerada"
**Solução:**
- Verificar logs: `logs/app.log`
- Testar query mais simples: "O que é BSC?"
- Verificar se vector store tem documentos: já validamos 7.965 chunks [OK]

### Streamlit não abre automaticamente
**Solução:**
```powershell
# Abrir manualmente
Start-Process "http://localhost:8501"
```

---

## [EMOJI] Métricas de Sucesso

**Sistema está funcionando bem quando:**

- [OK] Respostas em português brasileiro fluente
- [OK] Citações de livros de Kaplan & Norton
- [OK] Confidence > 0.7 na maioria das queries
- [OK] Judge aprova (score > 0.8)
- [OK] Documentos relevantes listados com scores
- [OK] Latência < 90s para queries complexas

---

## [EMOJI] Próximos Passos Após Teste

1. **Teste as 10 queries sugeridas** (5 conceituais + 5 implementação)
2. **Avalie a qualidade** das respostas (factual? útil? completa?)
3. **Identifique melhorias** (o que faltou? o que pode melhorar?)
4. **Compartilhe feedback** sobre:
   - Qualidade das respostas
   - Relevância dos documentos recuperados
   - Performance (tempo de resposta)
   - UX (experiência de uso Streamlit)

---

## [EMOJI] Suporte

**Se encontrar problemas:**

1. [OK] Verificar logs: `logs/app.log`
2. [OK] Verificar Docker: `docker ps`
3. [OK] Revalidar setup: `python scripts/validate_setup.py`
4. [OK] Restart containers: `docker-compose restart`

---

**Última Atualização:** 2025-10-19 (22:15)
**Status:** [OK] 100% PRONTO PARA TESTE REAL
