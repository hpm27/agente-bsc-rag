"""
Prompts para Contextual Retrieval (Anthropic).

Estes prompts são usados para gerar contexto explicativo
para chunks de documentos, melhorando retrieval.
"""

DOCUMENT_SUMMARY_PROMPT = """Analise o documento abaixo e crie um resumo conciso (2-3 sentenças) descrevendo:
1. Do que se trata o documento
2. Principais temas abordados
3. Contexto ou domínio (ex: gestão, finanças, BSC, estratégia, etc.)

{metadata_info}

Conteúdo:
{content}

Resumo (2-3 sentenças):"""


CHUNK_CONTEXT_PROMPT = """Você receberá um resumo de documento e um trecho (chunk) desse documento.
Sua tarefa é criar uma frase de contexto curta (1-2 sentenças) que explica sobre o que este trecho trata, situando-o no contexto do documento maior.

Esta contextualização será usada para melhorar a busca semântica em um sistema RAG.

Diretrizes:
- Seja conciso (máximo 2 sentenças)
- Mencione o tópico principal do chunk
- Se relevante, mencione a perspectiva BSC (Financeira, Clientes, Processos Internos, Aprendizado e Crescimento)
- Se for uma tabela ou dados quantitativos, mencione isso
- NÃO repita o conteúdo do chunk, apenas contextualize-o
- Use linguagem clara e objetiva
- Não use aspas ou formatação especial

Resumo do documento:
{document_summary}

Trecho do documento:
{chunk_content}

Contexto (1-2 sentenças):"""


CHUNK_CONTEXT_BSC_SPECIFIC_PROMPT = """Você receberá um resumo de documento BSC (Balanced Scorecard) e um trecho desse documento.
Sua tarefa é criar uma frase de contexto curta (1-2 sentenças) que explica sobre o que este trecho trata, situando-o no contexto BSC.

Esta contextualização será usada para melhorar a busca semântica em um sistema RAG especializado em BSC.

Diretrizes CRÍTICAS:
- Seja conciso (máximo 2 sentenças)
- Identifique e mencione a perspectiva BSC:
  * Financeira (ROI, receita, custos, lucratividade)
  * Clientes (satisfação, retenção, aquisição, NPS)
  * Processos Internos (eficiência, qualidade, ciclos, inovação)
  * Aprendizado e Crescimento (competências, tecnologia, cultura)
- Se for sobre KPIs/indicadores, mencione qual perspectiva
- Se for sobre mapa estratégico, mencione relações de causa-efeito
- Se for sobre implementação, mencione a fase (planejamento, execução, monitoramento)
- NÃO repita o conteúdo do chunk, apenas contextualize-o
- Use terminologia BSC quando apropriado

Resumo do documento:
{document_summary}

Trecho do documento:
{chunk_content}

Contexto BSC (1-2 sentenças):"""


TABLE_CONTEXT_PROMPT = """Você receberá um resumo de documento e uma tabela desse documento.
Sua tarefa é criar uma frase de contexto curta (1-2 sentenças) que explica sobre o que esta tabela trata.

Diretrizes:
- Seja conciso (máximo 2 sentenças)
- Mencione o que a tabela mostra/compara/lista
- Se possível, mencione as dimensões principais (linhas x colunas)
- Se for BSC, mencione a perspectiva e tipo de indicadores
- NÃO liste todos os dados, apenas descreva o propósito da tabela

Resumo do documento:
{document_summary}

Tabela:
{table_content}

Contexto da tabela (1-2 sentenças):"""


SYSTEM_PROMPT_CONTEXTUALIZATION = """Você é um especialista em contextualização de documentos para sistemas de busca semântica (RAG).

Seu papel é gerar contextos curtos e precisos que ajudam sistemas de IA a entender melhor chunks isolados de documentos.

Especialidade: Balanced Scorecard (BSC), gestão estratégica, KPIs, e performance management.

Princípios:
1. Contexto deve ser informativo mas conciso
2. Foque no "sobre o que" e não no "conteúdo literal"
3. Ajude a situar o chunk no documento maior
4. Use terminologia do domínio quando apropriado
5. Nunca repita o conteúdo do chunk, apenas contextualize-o"""


def get_document_summary_prompt(
    content: str,
    source: str = "documento desconhecido",
    title: str = "",
    **kwargs
) -> str:
    """
    Gera prompt para resumo de documento.
    
    Args:
        content: Conteúdo do documento (truncado se necessário)
        source: Nome do arquivo fonte
        title: Título do documento (opcional)
        **kwargs: Outros metadados
        
    Returns:
        Prompt formatado
    """
    metadata_info = f"Fonte: {source}"
    if title:
        metadata_info += f"\nTítulo: {title}"
    
    # Adiciona outros metadados relevantes
    for key, value in kwargs.items():
        if key not in ['content', 'source', 'title']:
            metadata_info += f"\n{key.capitalize()}: {value}"
    
    return DOCUMENT_SUMMARY_PROMPT.format(
        metadata_info=metadata_info,
        content=content[:10000]  # Trunca para 10k caracteres
    )


def get_chunk_context_prompt(
    chunk_content: str,
    document_summary: str,
    chunk_type: str = "text",
    use_bsc_specific: bool = True
) -> str:
    """
    Gera prompt para contexto de chunk.
    
    Args:
        chunk_content: Conteúdo do chunk
        document_summary: Resumo do documento
        chunk_type: 'text', 'table', etc.
        use_bsc_specific: Se True, usa prompt específico BSC
        
    Returns:
        Prompt formatado
    """
    # Trunca chunk se muito longo
    truncated_content = chunk_content[:1000] if len(chunk_content) > 1000 else chunk_content
    
    # Escolhe template baseado no tipo e domínio
    if chunk_type == "table":
        template = TABLE_CONTEXT_PROMPT
    elif use_bsc_specific:
        template = CHUNK_CONTEXT_BSC_SPECIFIC_PROMPT
    else:
        template = CHUNK_CONTEXT_PROMPT
    
    return template.format(
        document_summary=document_summary,
        chunk_content=truncated_content,
        table_content=truncated_content if chunk_type == "table" else ""
    )


def get_system_prompt() -> str:
    """
    Retorna system prompt para contextualização.
    
    Returns:
        System prompt
    """
    return SYSTEM_PROMPT_CONTEXTUALIZATION

