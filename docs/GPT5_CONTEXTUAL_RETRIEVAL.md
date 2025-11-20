# Configuração GPT-5 para Contextual Retrieval

## Visão Geral

O sistema agora suporta **dois providers** para contextualização de chunks durante a indexação:

1. **GPT-5 (OpenAI)** - Mais rápido e econômico, ideal para contextualização
2. **Claude Sonnet 4.5 (Anthropic)** - Mais preciso, mas mais caro

## Por Que Usar GPT-5 para Contextualização?

### Vantagens do GPT-5

- **Custo Menor**: ~40-60% mais barato que Claude 4.5 para tarefas de contextualização
- **Velocidade**: Reasoning "minimal" reduz drasticamente o tempo de processamento
- **Qualidade**: Mantém qualidade excelente para tarefas estruturadas como contextualização
- **Otimizado**: Parâmetro `reasoning_effort` permite ajustar custo vs. complexidade

### Quando Usar Claude vs. GPT-5

| Tarefa | Provider Recomendado | Razão |
|--------|---------------------|-------|
| **Contextualização de Chunks** | GPT-5 | Tarefa simples, estruturada, grande volume |
| **Agentes BSC (análise complexa)** | Claude 4.5 | Raciocínio profundo, análise estratégica |
| **Resumos de Documentos** | GPT-5 | Tarefa de formatação/sumarização |
| **Julgamento de Qualidade** | Claude 4.5 | Avaliação crítica e nuanced |

## Configuração no `.env`

```bash
# Contextual Retrieval Provider (openai ou anthropic)
# Usar 'openai' para GPT-5 (mais barato) ou 'anthropic' para Claude (mais preciso)
CONTEXTUAL_PROVIDER=openai

# GPT-5 Configuration (para Contextual Retrieval)
# NOTA: GPT-5 eh modelo de reasoning com parametros DIFERENTES:
# - max_completion_tokens (NAO max_tokens)
# - NAO suporta temperature, top_p, logprobs
# - reasoning_effort: "minimal" para tarefas simples (contextualizacao, formatacao)
GPT5_MODEL=gpt-5-2025-08-07
GPT5_MAX_COMPLETION_TOKENS=2048
GPT5_REASONING_EFFORT=minimal
```

## Parâmetros do GPT-5

### `GPT5_MODEL`

Modelo GPT-5 a usar. Atualmente disponível:

- `gpt-5-2025-08-07` (recomendado)

### `GPT5_MAX_COMPLETION_TOKENS`

Número máximo de tokens na resposta gerada.

**ATENÇÃO**: GPT-5 usa `max_completion_tokens` (não `max_tokens` como outros modelos)

- **Padrão**: 2048
- **Recomendado para contextualização**: 2048-4096
- **Para resumos**: 200-500

### `GPT5_REASONING_EFFORT`

Controla o esforço de raciocínio do modelo. Valores possíveis:

| Valor | Descrição | Uso Recomendado | Custo Relativo |
|-------|-----------|-----------------|----------------|
| `minimal` | Reasoning mínimo | [OK] Contextualização, formatação, tarefas simples | Mais barato |
| `low` | Reasoning baixo | Tarefas leves com lógica básica | Barato |
| `medium` | Reasoning médio (padrão) | Tarefas balanceadas | Médio |
| `high` | Reasoning alto | Problemas complexos, matemática, análise | Mais caro |

**Recomendação**: Use `minimal` para contextualização de chunks (tarefa estruturada e simples).

## Diferenças Críticas GPT-5 vs. Outros Modelos

O GPT-5 (série `o1`) é um **modelo de reasoning** com limitações específicas:

### [OK] GPT-5 SUPORTA

- `max_completion_tokens` (substitui `max_tokens`)
- `reasoning_effort` (`minimal`, `low`, `medium`, `high`)
- `messages` (formato padrão de chat)

### [ERRO] GPT-5 NÃO SUPORTA

- `temperature` (sempre usa valor padrão `1`)
- `top_p`
- `logprobs`
- `presence_penalty` / `frequency_penalty`
- `system` (use primeira mensagem do usuário)

## Como Funciona no Código

### ContextualChunker com GPT-5

```python
from src.rag.contextual_chunker import ContextualChunker

# Cria chunker com GPT-5 (lê CONTEXTUAL_PROVIDER do .env)
chunker = ContextualChunker()

# Ou explicitamente:
chunker = ContextualChunker(provider="openai")

# Processa documento
contextual_chunks = chunker.chunk_text(
    text=document_text,
    metadata={"source": "bsc_paper.pdf"}
)
```

### Troca de Provider

Para alternar entre GPT-5 e Claude, basta mudar no `.env`:

```bash
# Usar GPT-5 (mais rápido e barato)
CONTEXTUAL_PROVIDER=openai

# Ou usar Claude 4.5 (mais preciso)
CONTEXTUAL_PROVIDER=anthropic
```

O código detecta automaticamente o provider e usa os parâmetros corretos.

## Exemplo de Chamada API

### GPT-5 (via OpenAI Python SDK)

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-5-2025-08-07",
    max_completion_tokens=2048,
    reasoning_effort="minimal",
    messages=[{
        "role": "user",
        "content": "Contextualize este chunk: [...]"
    }]
)

context = response.choices[0].message.content
```

### Claude 4.5 (via Anthropic Python SDK)

```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=150,
    temperature=0.0,
    system=[{
        "type": "text",
        "text": "Você é especialista em contextualização...",
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[{
        "role": "user",
        "content": "Contextualize este chunk: [...]"
    }]
)

context = response.content[0].text
```

## Testando a Configuração

### 1. Verificar Variáveis de Ambiente

```bash
# Verificar se está configurado corretamente
python -c "from config.settings import settings; print(f'Provider: {settings.contextual_provider}'); print(f'Model: {settings.gpt5_model if settings.contextual_provider == \"openai\" else settings.contextual_model}')"
```

### 2. Executar Build da Base de Conhecimento

```bash
# Com GPT-5
python scripts/build_knowledge_base.py
```

Você verá no log:

```
[INIT] Inicializando componentes...
   [OK] Contextual Retrieval: Habilitado (GPT-5)
ContextualChunker inicializado com GPT-5 (gpt-5-2025-08-07, reasoning_effort=minimal)
```

### 3. Verificar Custos

Durante o processamento, compare logs:

**Com GPT-5 (minimal)**:

```
[DONE] 150 chunks contextualizados em 45.2s (média: 0.30s/chunk)
```

**Com Claude 4.5**:

```
[DONE] 150 chunks contextualizados em 78.5s (média: 0.52s/chunk)
```

## Troubleshooting

### Erro: "max_tokens is not supported"

**Causa**: Tentou usar `max_tokens` com GPT-5 (deve ser `max_completion_tokens`)

**Solução**: O código já trata isso automaticamente. Se persistir, verifique se está usando `ContextualChunker` atualizado.

### Erro: "temperature is not supported"

**Causa**: Tentou definir `temperature` com GPT-5 (não suportado)

**Solução**: Remova `temperature` das chamadas GPT-5. O código já trata isso.

### Qualidade Inferior com GPT-5

**Causa**: Reasoning effort muito baixo ou prompt inadequado

**Solução**: Ajuste `GPT5_REASONING_EFFORT`:

- `minimal` -> `low` (tarefas simples)
- `low` -> `medium` (mais complexidade)

### Custos Altos com GPT-5

**Causa**: Reasoning effort muito alto

**Solução**: Reduza `GPT5_REASONING_EFFORT`:

- `high` -> `medium` (análise moderada)
- `medium` -> `minimal` (tarefas simples)

## Referências

- [OpenAI GPT-5 Documentation](https://platform.openai.com/docs/models/gpt-5)
- [Anthropic Claude 4.5 Documentation](https://docs.anthropic.com/claude/docs/models)
- [Anthropic Contextual Retrieval Paper](https://www.anthropic.com/news/contextual-retrieval)

## Estrutura de Custos (Estimativa 2025)

| Modelo | Input (1M tokens) | Output (1M tokens) | Contextualização (150 chunks) |
|--------|-------------------|-------------------|-------------------------------|
| GPT-5 (minimal) | $2.50 | $10.00 | ~$0.15 |
| GPT-5 (medium) | $2.50 | $10.00 | ~$0.30 |
| Claude 4.5 | $3.00 | $15.00 | ~$0.25 |

**Economia com GPT-5 (minimal)**: ~40-60% vs. Claude 4.5

---

**Última Atualização**: 11/10/2025
**Autor**: Agente BSC RAG Team
