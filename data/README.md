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

## Metadados (Opcional)

Você pode criar um arquivo `index.json` em `bsc_literature/` com metadados:

```json
{
  "documents": [
    {
      "filename": "kaplan_norton_1996.pdf",
      "title": "The Balanced Scorecard",
      "authors": ["Robert S. Kaplan", "David P. Norton"],
      "year": 1996,
      "type": "paper",
      "perspectives": ["all"],
      "language": "en"
    },
    {
      "filename": "bsc_implementacao_brasil.pdf",
      "title": "Implementação de BSC no Brasil",
      "authors": ["Autor Exemplo"],
      "year": 2023,
      "type": "case_study",
      "perspectives": ["financial", "customer"],
      "language": "pt-BR"
    }
  ]
}
```

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

