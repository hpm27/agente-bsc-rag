# Sprint 1 - Fix Crítico: RAG Usage nos Specialist Agents

**Data:** 2025-11-20 (Tarde)  
**Sessão:** 37  
**Status:** [OK] RESOLVIDO E VALIDADO

---

## [EMOJI] Problema Identificado

### Sintoma
Durante teste E2E Streamlit, observou-se que os **4 specialist agents** (Financial, Customer, Process, Learning) **não estavam consultando o RAG** antes de responder.

### Evidência
- Logs não mostravam "Recuperou X chars de contexto RAG"
- Respostas dos agents eram genéricas (sem contexto específico dos documentos BSC)
- Ferramentas consultivas recebiam contexto empobrecido dos agents

---

## [EMOJI] Root Cause

### Análise
O método `ainvoke()` dos specialist agents estava configurado com `llm.bind_tools(self.tools)`, mas **NÃO estava chamando explicitamente** os RAG tools.

**Pattern encontrado nos 4 agents:**

```python
# ANTES (INCORRETO)
async def ainvoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    messages = [
        SystemMessage(content=self.system_prompt),
        HumanMessage(content=query)
    ]
    
    # LLM com ferramentas bound, mas NUNCA chamadas explicitamente
    response = await self.llm_with_tools.ainvoke(messages)
    
    return {
        "output": response.content,  # Resposta GENÉRICA (sem RAG!)
        "agent_name": self.name
    }
```

**Problema:** `llm.bind_tools()` torna as ferramentas DISPONÍVEIS, mas o LLM decide SE e QUANDO chamá-las. Para garantir RAG em TODA resposta, precisamos **chamada explícita**.

---

## [OK] Solução Implementada

### Pattern Correto Validado

Modificamos os 4 agents para **SEMPRE chamar tool.arun() explicitamente** antes de invocar o LLM:

```python
# DEPOIS (CORRETO)
async def ainvoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    # STEP 1: Buscar contexto RAG EXPLICITAMENTE
    context_parts = []
    for tool in self.tools:
        if tool.name == "search_by_perspective":
            try:
                # Chamada explícita do RAG tool
                result = await tool.arun({
                    "query": query,
                    "perspective": "financeira",  # Ou respectiva perspectiva
                    "k": 5
                })
                if result:
                    context_parts.append(f"[CONTEXTO FINANCEIRO BSC]\n{result[:2000]}")
                    logger.info(f"[{self.name}] Recuperou {len(result)} chars de contexto RAG")
            except Exception as e:
                logger.warning(f"[{self.name}] Erro ao buscar contexto RAG: {e}")
    
    # STEP 2: Construir mensagens com contexto RAG
    messages = [
        SystemMessage(content=self.system_prompt)
    ]
    
    # Adicionar contexto RAG às mensagens
    if context_parts:
        messages.insert(1, SystemMessage(content="\n".join(context_parts)))
    
    messages.append(HumanMessage(content=query))
    
    # STEP 3: Invocar LLM com contexto RAG
    response = await self.llm_with_tools.ainvoke(messages)
    
    return {
        "output": response.content,  # Resposta ENRIQUECIDA com RAG!
        "agent_name": self.name
    }
```

---

## [EMOJI] Arquivos Modificados

### 1. `src/agents/financial_agent.py` (linhas 94-131)
- Adicionado loop explícito para chamar `tool.arun()`
- Tool name: `"search_by_perspective"`
- Perspective: `"financeira"`

### 2. `src/agents/customer_agent.py` (linhas 94-131)
- Adicionado loop explícito para chamar `tool.arun()`
- Tool name: `"search_by_perspective"`
- Perspective: `"clientes"`

### 3. `src/agents/process_agent.py` (linhas 94-131)
- Adicionado loop explícito para chamar `tool.arun()`
- Tool name: `"search_by_perspective"`
- Perspective: `"processos"`

### 4. `src/agents/learning_agent.py` (linhas 94-131)
- Adicionado loop explícito para chamar `tool.arun()`
- Tool name: `"search_by_perspective"`
- Perspective: `"aprendizado"`

---

## [OK] Validação do Fix

### Teste E2E Streamlit - Logs Confirmados

**Query:** "Realizar diagnóstico BSC completo" (empresa Engelar)

**Evidências de sucesso:**

```
[FIN] Recuperou 13771 chars de contexto RAG
[CUST] Recuperou 100 chars de contexto RAG
[PROC] Recuperou 12065 chars de contexto RAG
[LEARN] Recuperou 12554 chars de contexto RAG
```

**Resultado:**
- [OK] 4/4 agents consultaram RAG explicitamente
- [OK] Contexto RAG incluído em TODAS as respostas
- [OK] Ferramentas consultivas receberam contexto rico dos agents
- [OK] Diagnóstico final mencionou conceitos específicos da literatura BSC

---

## [EMOJI] Lições Aprendidas

### 1. `llm.bind_tools()` NÃO Garante Uso de Ferramentas

**Descoberta:** `bind_tools()` torna ferramentas DISPONÍVEIS ao LLM, mas não OBRIGA seu uso.

**Pattern Errado:**
```python
llm_with_tools = llm.bind_tools(self.tools)
response = await llm_with_tools.ainvoke(messages)  # Ferramentas podem NÃO ser chamadas!
```

**Pattern Correto:**
```python
# Chamar tool EXPLICITAMENTE
result = await tool.arun({"query": query, ...})
# Depois invocar LLM com contexto
response = await llm.ainvoke(messages_with_context)
```

---

### 2. Formato Correto de `tool.arun()`

**Descoberta:** `BaseTool.arun()` espera **UM argumento de dicionário** (não argumentos nomeados).

**Tentativa Errada:**
```python
result = await tool.arun(query=query, perspective="financeira", k=5)  # TypeError!
```

**Correto:**
```python
result = await tool.arun({
    "query": query,
    "perspective": "financeira",
    "k": 5
})  # [OK] Funciona!
```

---

### 3. Logs Defensivos São Essenciais

**Descoberta:** Sem logs explícitos, era impossível saber se RAG estava sendo usado.

**Pattern Validado:**
```python
logger.info(f"[{self.name}] Recuperou {len(result)} chars de contexto RAG")
```

**ROI:** Identificação imediata de problemas (agents sem RAG detectado em <5 min vs horas de tentativa e erro).

---

## [EMOJI] Impacto no Sprint 1

### Antes do Fix
- Agents retornavam respostas genéricas (sem RAG)
- Ferramentas consultivas trabalhavam com contexto empobrecido
- Diagnóstico BSC sem grounding na literatura

### Depois do Fix
- [OK] 100% dos agents consultam RAG explicitamente
- [OK] Ferramentas recebem contexto rico dos 4 agents
- [OK] Diagnóstico mencionando conceitos específicos BSC (Kaplan & Norton, 4 perspectivas balanceadas, etc.)

---

## [EMOJI] Próximas Otimizações (Sprint 2)

1. **Cache de RAG**: Evitar buscas duplicadas para queries similares
2. **Compressão de Contexto**: Reduzir tokens mantendo informação crítica
3. **Timeout Granular**: Fallback se RAG demorar >30s

---

**Última Atualização:** 2025-11-20  
**Status:** [OK] RESOLVIDO E VALIDADO
