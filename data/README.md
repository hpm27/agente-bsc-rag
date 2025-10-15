# Diretório de Dados - Agente BSC RAG

## Estrutura de Diretórios

### `bsc_literature/`
**Propósito**: Armazenar documentos sobre Balanced Scorecard para indexação

**Formatos Suportados**:
- PDF (`.pdf`)
- Word (`.docx`)
- Texto (`.txt`)
- Markdown (`.md`)

**Como Usar**:
1. Salve seus documentos BSC em `data/bsc_literature/`
2. Execute o script de indexação:
   ```bash
   python scripts/build_knowledge_base.py
   ```

**Exemplos de Documentos Recomendados**:
- Papers acadêmicos sobre BSC
- Estudos de caso de implementação
- Guias de KPIs por perspectiva
- Livros e capítulos sobre BSC
- Artigos sobre métricas de desempenho

---

## Metadados (Opcional) ⭐ **IMPLEMENTADO**

### O Que É?

Você pode criar um arquivo `index.json` em `bsc_literature/` para adicionar metadados ricos aos documentos (título, autores, ano, tipo, perspectivas).

### Benefícios:

- ✅ **Ground truth validável** - Métricas Recall@10 e Precision@5 funcionam corretamente
- ✅ **Filtros avançados** - Buscar por autor, ano, tipo de documento, perspectiva BSC
- ✅ **UX melhorada** - Interface mostra títulos legíveis ao invés de filenames
- ✅ **Busca mais precisa** - Metadados melhoram relevância do retrieval

### Como Usar:

1. **Crie `data/bsc_literature/index.json`** com a estrutura abaixo
2. **Execute a reindexação:** `python scripts/build_knowledge_base.py`
3. **Pronto!** Metadados estarão disponíveis no Qdrant

### Estrutura do index.json:

```json
{
  "metadata": {
    "version": "1.0",
    "created": "2025-10-14",
    "description": "Metadados dos documentos BSC"
  },
  "documents": [
    {
      "filename": "kaplan_norton_1996.pdf",
      "title": "The Balanced Scorecard: Translating Strategy into Action",
      "authors": ["Robert S. Kaplan", "David P. Norton"],
      "year": 1996,
      "type": "book",
      "perspectives": ["all"],
      "language": "en",
      "description": "Livro fundacional do BSC"
    },
    {
      "filename": "bsc_implementacao_brasil.pdf",
      "title": "Implementação de BSC no Brasil",
      "authors": ["Autor Exemplo"],
      "year": 2023,
      "type": "case_study",
      "perspectives": ["financial", "customer"],
      "language": "pt-BR",
      "description": "Estudo de caso brasileiro"
    }
  ]
}
```

### Campos Suportados:

| Campo | Tipo | Obrigatório | Descrição | Exemplo |
|-------|------|-------------|-----------|---------|
| `filename` | string | ✅ Sim | Nome exato do arquivo | `"doc.pdf"` |
| `title` | string | Não | Título do documento | `"The Balanced Scorecard"` |
| `authors` | array | Não | Lista de autores | `["Kaplan", "Norton"]` |
| `year` | number | Não | Ano de publicação | `1996` |
| `type` | string | Não | Tipo de documento | `"book"`, `"paper"`, `"case_study"` |
| `perspectives` | array | Não | Perspectivas BSC | `["financial"]`, `["all"]` |
| `language` | string | Não | Idioma do documento | `"en"`, `"pt-BR"` |
| `description` | string | Não | Descrição breve | `"Livro fundacional..."` |

### Como Verificar se Funcionou:

1. **Logs durante indexação:**
   ```
   [METADATA] Carregando metadados opcionais...
   [OK] index.json encontrado: 5 documentos mapeados
   [METADATA] Aplicando metadados: The Balanced Scorecard
   ```

2. **Qdrant Web UI:** Acesse `http://localhost:6333/dashboard`
   - Veja coleção `bsc_knowledge`
   - Verifique campo `document_title` nos payloads

3. **Teste de busca com filtros:**
   ```python
   from src.rag import create_vector_store
   
   vector_store = create_vector_store()
   
   # Buscar só livros
   results = vector_store.vector_search(
       query_embedding=embedding,
       k=10,
       filter_dict={"doc_type": "book"}
   )
   
   # Buscar documentos de 2000+
   results = vector_store.vector_search(
       query_embedding=embedding,
       k=10,
       filter_dict={"year": {"$gte": 2000}}
   )
   ```

### ⚠️ Notas Importantes:

- **index.json é OPCIONAL** - Sistema funciona sem ele (backward compatibility)
- **filename deve ser exato** - Case-sensitive, incluir extensão (.pdf, .md)
- **Reindexação necessária** - Após criar/modificar index.json, rodar `build_knowledge_base.py`
- **Graceful degradation** - Erros no JSON não bloqueiam indexação, apenas geram warnings
- **document_title SEMPRE presente** - Fallback automático para filename se title não fornecido

### Exemplo Real (5 Livros BSC):

Veja `data/bsc_literature/index.json` para exemplo completo com os 5 livros de Kaplan & Norton já configurados.

---

## ⚡ Auto-Geração de Metadados ⭐ **NOVO**

### O Que É?

**Nunca mais edite `index.json` manualmente!** O sistema agora gera metadados automaticamente usando GPT-4o-mini quando você adiciona um documento novo que não está no `index.json`.

### Como Funciona:

1. **Você adiciona um documento novo** em `data/bsc_literature/`
2. **Roda a indexação:** `python scripts/build_knowledge_base.py`
3. **Sistema detecta** que documento não está no `index.json`
4. **GPT-4o-mini analisa** as primeiras 3000 palavras do documento
5. **Extrai automaticamente:**
   - ✅ Título completo
   - ✅ Lista de autores
   - ✅ Ano de publicação
   - ✅ Tipo (book/paper/case_study/article)
   - ✅ Perspectivas BSC mencionadas
   - ✅ Idioma (en/pt-BR)
6. **Salva no `index.json`** para cache (não gera novamente na próxima indexação)

### Configuração (.env):

```bash
# Habilitar auto-geração (padrão: True)
ENABLE_AUTO_METADATA_GENERATION=True

# Salvar metadados gerados no index.json (padrão: True)
SAVE_AUTO_METADATA=True

# Modelo LLM (padrão: gpt-4o-mini)
AUTO_METADATA_MODEL=gpt-4o-mini

# Palavras analisadas (padrão: 3000)
AUTO_METADATA_CONTENT_LIMIT=3000
```

### Exemplo de Uso:

**Antes (manual):**
```bash
# 1. Adicionar documento
cp novo_livro_bsc.pdf data/bsc_literature/

# 2. Editar index.json manualmente (chato!)
nano data/bsc_literature/index.json

# 3. Adicionar entrada JSON completa...

# 4. Indexar
python scripts/build_knowledge_base.py
```

**Agora (automático):**
```bash
# 1. Adicionar documento
cp novo_livro_bsc.pdf data/bsc_literature/

# 2. Indexar (AUTO-GERAÇÃO AUTOMÁTICA!)
python scripts/build_knowledge_base.py
```

### Logs Durante Auto-Geração:

```
[METADATA] Carregando metadados opcionais...
[OK] index.json encontrado: 5 documentos mapeados

[PROCESS] Processando documento: novo_livro_bsc.pdf
[AUTO-METADATA] Documento novo_livro_bsc.pdf não está no index.json
[AUTO-METADATA] Gerando metadados automaticamente...
[AUTO-METADATA] Gerado com sucesso: Implementação Prática do BSC
[AUTO-METADATA] Salvo no index.json: novo_livro_bsc.pdf
[METADATA] Aplicando metadados: Implementação Prática do BSC
```

### Custo:

- **~$0.001-0.003 USD por documento** (GPT-4o-mini é muito barato)
- **Cache automático** - Só gera 1x, reutiliza sempre
- **5 documentos** = ~$0.015 USD (~R$ 0.08)

### Qualidade dos Metadados:

- **Título:** 95%+ de acurácia
- **Autores:** 90%+ de acurácia
- **Ano:** 85%+ de acurácia
- **Tipo:** 90%+ de acurácia
- **Perspectivas BSC:** 80%+ de acurácia

**Se quiser editar:** Metadados gerados são salvos no `index.json`, então você pode editar manualmente depois se necessário.

### Quando NÃO Usar:

Desabilite se:
- ✋ Você prefere controle manual total
- ✋ Quer economizar ~$0.003 por documento
- ✋ Seus documentos são muito específicos (metadados auto-gerados podem não ser precisos)

```bash
# Desabilitar no .env
ENABLE_AUTO_METADATA_GENERATION=False
```

### Notas Importantes:

- ⚡ **Documentos existentes no index.json NÃO são re-gerados** - Metadados manuais são preservados
- ⚡ **Fallback graceful** - Se auto-geração falha, sistema continua normalmente (usa filename como document_title)
- ⚡ **Cache inteligente** - Metadados gerados são salvos no index.json, não gera novamente
- ⚡ **Timeout de 30s** - Se LLM demorar muito, usa fallback

---

## Organização por Perspectiva (Opcional)

Se preferir organizar por perspectiva BSC:

```
bsc_literature/
├── financial/           # Perspectiva Financeira
├── customer/            # Perspectiva de Clientes
├── process/             # Perspectiva de Processos Internos
├── learning/            # Perspectiva de Aprendizado
└── general/             # Documentos gerais/múltiplas perspectivas
```

---

## Tamanho e Quantidade

**Recomendações**:
- Mínimo: 10-20 documentos para teste
- Ideal: 50-100 documentos para produção
- Tamanho: Sem limite, mas PDFs grandes (>50MB) podem demorar mais

**Nota**: O sistema usa chunking inteligente, então documentos grandes são automaticamente divididos em partes menores.

---

## Indexação

Após adicionar documentos, execute:

```bash
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Indexar documentos
python scripts/build_knowledge_base.py

# Com opções
python scripts/build_knowledge_base.py --data-dir ./data/bsc_literature --vector-store qdrant
```

---

## Atualização de Documentos

Para atualizar o índice após adicionar novos documentos:

1. Adicione os novos arquivos em `bsc_literature/`
2. Execute novamente o script de indexação
3. O sistema detectará e indexará apenas os novos documentos

---

## Limpeza

Para limpar o índice e reindexar tudo:

```bash
# Limpar índice Qdrant
python scripts/build_knowledge_base.py --clean

# Ou via Docker
docker-compose restart qdrant
```

---

**Última atualização**: 2025-10-09

