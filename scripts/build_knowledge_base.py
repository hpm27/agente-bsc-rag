"""
Script para construir a base de conhecimento a partir dos documentos BSC.

Pipeline completo:
1. Carrega PDFs
2. Chunk com TableAwareChunker
3. Contextual Retrieval (Anthropic) - adiciona contexto aos chunks
4. Embeddings (OpenAI text-embedding-3-large)
5. Armazena em Vector Store (Qdrant/Weaviate/Redis)
"""
import warnings
# Suprimir warnings de deprecation do Pydantic v1 ANTES dos imports
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*ForwardRef._evaluate.*")

import os
import sys
from pathlib import Path
from tqdm import tqdm
from loguru import logger
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pypdf import PdfReader
from src.rag.vector_store_factory import create_vector_store
from src.rag.embeddings import EmbeddingManager
from src.rag.chunker import TableAwareChunker
from src.rag.contextual_chunker import ContextualChunker
from config.settings import settings
import json


def load_metadata_index(directory: str) -> Dict[str, Dict[str, Any]]:
    """
    Carrega index.json com metadados opcionais dos documentos.
    
    Args:
        directory: Diretório contendo index.json
        
    Returns:
        Dict mapeando filename -> metadados
        
    Example:
        {
            "doc1.pdf": {"title": "...", "authors": [...], "year": 2023},
            "doc2.pdf": {"title": "...", "authors": [...], "year": 2024}
        }
    """
    index_path = Path(directory) / "index.json"
    
    # Se não existir, retornar dict vazio (graceful degradation)
    if not index_path.exists():
        logger.info("   [INFO] index.json não encontrado, usando metadados padrão")
        return {}
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validar estrutura mínima
        if 'documents' not in data or not isinstance(data['documents'], list):
            logger.warning("   [WARN] index.json inválido: falta campo 'documents'")
            return {}
        
        # Criar dict de lookup filename -> metadata
        metadata_map = {}
        for doc in data['documents']:
            if 'filename' not in doc:
                continue
            
            filename = doc['filename']
            metadata_map[filename] = {
                'title': doc.get('title', ''),
                'authors': doc.get('authors', []),
                'year': doc.get('year'),
                'type': doc.get('type', 'document'),
                'perspectives': doc.get('perspectives', []),
                'language': doc.get('language', 'en'),
                'description': doc.get('description', '')
            }
        
        logger.info(f"   [OK] index.json encontrado: {len(metadata_map)} documentos mapeados")
        return metadata_map
        
    except json.JSONDecodeError as e:
        logger.warning(f"   [WARN] index.json inválido (JSON malformado): {e}")
        return {}
    except Exception as e:
        logger.warning(f"   [WARN] Erro ao carregar index.json: {e}")
        return {}


def generate_metadata_from_content(
    content: str, 
    filename: str
) -> Dict[str, Any]:
    """
    Gera metadados automaticamente usando LLM a partir do conteúdo do documento.
    
    Args:
        content: Conteúdo do documento (primeiras N palavras)
        filename: Nome do arquivo (para context)
        
    Returns:
        Dict com metadados gerados: title, authors, year, type, perspectives, language
        
    Example:
        >>> metadata = generate_metadata_from_content(text[:3000], "doc.pdf")
        >>> metadata["title"]
        "The Balanced Scorecard"
    """
    # Verificar se auto-geração está habilitada
    if not settings.enable_auto_metadata_generation:
        return {}
    
    try:
        from openai import OpenAI
        
        # Limitar conteúdo para análise (economizar tokens)
        words = content.split()
        limited_content = " ".join(words[:settings.auto_metadata_content_limit])
        
        # Criar cliente OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Prompt estruturado para extração de metadados
        system_prompt = """Você é um assistente especializado em extrair metadados de documentos acadêmicos e empresariais sobre Balanced Scorecard (BSC).

Analise o conteúdo fornecido e extraia os seguintes metadados em formato JSON:

{
  "title": "Título completo do documento",
  "authors": ["Lista", "de", "autores"],
  "year": 2024,
  "type": "book|paper|case_study|article",
  "perspectives": ["financial", "customer", "process", "learning", "all"],
  "language": "en|pt-BR"
}

REGRAS:
- title: Título COMPLETO (procure no cabeçalho, capa, ou primeiras linhas)
- authors: Lista de nomes completos dos autores (se não houver, retorne [])
- year: Ano de publicação (se não encontrar, retorne null)
- type: Classifique como:
  * "book" se mencionar "Chapter", "Copyright", "ISBN"
  * "paper" se mencionar "Abstract", "References", "Journal"
  * "case_study" se mencionar "Case", "Company", "Implementation"
  * "article" para outros casos
- perspectives: Perspectivas BSC mencionadas:
  * ["all"] se mencionar "Balanced Scorecard" ou "BSC" de forma geral
  * ["financial"] se focar em métricas financeiras
  * ["customer"] se focar em clientes
  * ["process"] se focar em processos internos
  * ["learning"] se focar em aprendizado e crescimento
  * Pode combinar múltiplas: ["financial", "customer"]
- language: 
  * "en" se texto em inglês
  * "pt-BR" se texto em português brasileiro

IMPORTANTE: Retorne APENAS o JSON válido, sem explicações adicionais."""

        user_prompt = f"""Filename: {filename}

Conteúdo:
{limited_content}

Extraia os metadados em formato JSON:"""

        # Chamar LLM com JSON mode forçado
        response = client.chat.completions.create(
            model=settings.auto_metadata_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            timeout=30
        )
        
        # Parsear resposta JSON
        metadata_str = response.choices[0].message.content
        metadata = json.loads(metadata_str)
        
        # Validar campos obrigatórios e defaults
        result = {
            'title': metadata.get('title', ''),
            'authors': metadata.get('authors', []),
            'year': metadata.get('year'),
            'type': metadata.get('type', 'document'),
            'perspectives': metadata.get('perspectives', ['all']),
            'language': metadata.get('language', 'en'),
            'description': f"Auto-generated metadata for {filename}"
        }
        
        logger.info(f"      [AUTO-METADATA] Gerado com sucesso: {result.get('title', filename)}")
        return result
        
    except Exception as e:
        logger.warning(f"      [AUTO-METADATA] Falha ao gerar metadados: {e}")
        # Fallback: metadados vazios (graceful degradation)
        return {}


def save_metadata_to_index(
    directory: str,
    filename: str,
    metadata: Dict[str, Any]
) -> bool:
    """
    Salva metadados gerados automaticamente de volta no index.json.
    
    Isso cria um cache para evitar re-gerar metadados em indexações futuras.
    Preserva metadados manuais existentes (não sobrescreve).
    
    Args:
        directory: Diretório contendo index.json
        filename: Nome do arquivo do documento
        metadata: Metadados a salvar
        
    Returns:
        True se salvou com sucesso, False caso contrário
        
    Example:
        >>> save_metadata_to_index("data/bsc_literature", "doc.pdf", {"title": "..."})
        True
    """
    # Verificar se salvamento está habilitado
    if not settings.save_auto_metadata:
        return False
    
    # Não salvar se metadados estão vazios
    if not metadata or not metadata.get('title'):
        return False
    
    try:
        index_path = Path(directory) / "index.json"
        
        # Carregar index existente ou criar novo
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "metadata": {
                    "version": "1.0",
                    "created": "2025-10-14",
                    "description": "Metadados dos documentos BSC para indexação avançada"
                },
                "documents": []
            }
        
        # Verificar se documento JÁ existe (não sobrescrever manual)
        existing_docs = data.get('documents', [])
        for doc in existing_docs:
            if doc.get('filename') == filename:
                logger.info(f"      [AUTO-METADATA] Documento {filename} já existe no index.json (preservando manual)")
                return False
        
        # Adicionar novo documento
        new_doc = {
            "filename": filename,
            "title": metadata.get('title', ''),
            "authors": metadata.get('authors', []),
            "year": metadata.get('year'),
            "type": metadata.get('type', 'document'),
            "perspectives": metadata.get('perspectives', ['all']),
            "language": metadata.get('language', 'en'),
            "description": metadata.get('description', f"Auto-generated metadata for {filename}")
        }
        
        existing_docs.append(new_doc)
        data['documents'] = existing_docs
        
        # Salvar de volta
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"      [AUTO-METADATA] Salvo no index.json: {filename}")
        return True
        
    except Exception as e:
        logger.warning(f"      [AUTO-METADATA] Falha ao salvar no index.json: {e}")
        return False


def load_pdf(file_path: str) -> dict:
    """Carrega um arquivo PDF."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return {
            "content": text,
            "source": os.path.basename(file_path),
            "num_pages": len(reader.pages)
        }
    except Exception as e:
        logger.error(f"Erro ao carregar {file_path}: {e}")
        return None


def main():
    """Função principal do pipeline de ingestão."""
    logger.info("=" * 70)
    logger.info("[START] Pipeline de Ingestao - Base de Conhecimento BSC")
    logger.info("=" * 70)
    
    # Inicializa componentes
    logger.info("\n[INIT] Inicializando componentes...")
    vector_store = create_vector_store()
    logger.info(f"   [OK] Vector Store: {type(vector_store).__name__}")
    
    embedding_manager = EmbeddingManager()
    logger.info(f"   [OK] Embeddings: {embedding_manager.provider} ({embedding_manager.model_name if embedding_manager.provider == 'openai' else 'fine-tuned'})")
    
    chunker = TableAwareChunker()
    logger.info(f"   [OK] Chunker: TableAwareChunker")
    
    # Contextual Retrieval (opcional)
    contextual_chunker = None
    if settings.enable_contextual_retrieval and settings.anthropic_api_key:
        contextual_chunker = ContextualChunker()
        logger.info(f"   [OK] Contextual Retrieval: Habilitado (Anthropic)")
    else:
        logger.info(f"   [WARN]  Contextual Retrieval: Desabilitado")
    
    # Cria/recria índice
    logger.info(f"\n[SETUP] Criando índice '{settings.vector_store_index}'...")
    try:
        vector_store.create_index(
            index_name=settings.vector_store_index,
            force_recreate=True
        )
        logger.info("   [OK] Índice criado com sucesso")
    except Exception as e:
        logger.error(f"   [ERRO] Erro ao criar índice: {e}")
        return
    
    # Carrega documentos
    literature_dir = Path(settings.literature_dir)
    pdf_files = list(literature_dir.glob("*.pdf"))
    md_files = list(literature_dir.glob("*.md"))
    all_files = pdf_files + md_files
    
    if not all_files:
        logger.warning(f"\n[WARN] Nenhum arquivo PDF ou MD encontrado em {literature_dir}")
        logger.info("[INFO] Por favor, adicione arquivos da literatura BSC neste diretório.")
        logger.info("   Exemplo: papers sobre Balanced Scorecard, livros, artigos, etc.")
        return
    
    logger.info(f"\n[INFO] Encontrados {len(pdf_files)} PDFs e {len(md_files)} Markdown")
    
    # Carrega metadados opcionais do index.json
    logger.info(f"\n[METADATA] Carregando metadados opcionais...")
    metadata_index = load_metadata_index(str(literature_dir))
    
    all_chunks: List[Dict[str, Any]] = []
    
    # Processa cada documento
    logger.info("\n[PROCESS] Processando documentos...")
    for doc_file in tqdm(all_files, desc="Documentos"):
        logger.info(f"   [DOC] {doc_file.name}")
        
        # Carrega documento (PDF ou MD)
        if doc_file.suffix == '.pdf':
            doc = load_pdf(str(doc_file))
        else:  # .md
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
                doc = {
                    "content": content,
                    "source": doc_file.name,
                    "num_pages": 1
                }
        
        if not doc:
            logger.error(f"      [ERRO] Erro ao carregar")
            continue
        
        # Divide em chunks (com ou sem Contextual Retrieval)
        if contextual_chunker:
            logger.info(f"      [CONTEXT] Aplicando Contextual Retrieval...")
            contextual_chunks = contextual_chunker.chunk_text(
                text=doc["content"],
                metadata={
                    "source": doc["source"],
                    "num_pages": doc["num_pages"]
                }
            )
            # Converte ContextualChunk para dict format e adiciona 'page' + contextos bilíngues
            chunks = [
                {
                    "content": c.contextual_content,  # Usa conteúdo com contexto PT-BR
                    "source": c.metadata.get('source', doc["source"]),  # Garante source
                    "page": c.metadata.get('chunk_index', i) + 1,  # 1-based page number (seção)
                    "context_pt": c.context_pt,  # Contexto em português
                    "context_en": c.context_en,  # Contexto em inglês (tradução automática)
                    **{k: v for k, v in c.metadata.items() if k not in ['content', 'source', 'page']}
                }
                for i, c in enumerate(contextual_chunks)
            ]
        else:
            base_chunks = chunker.chunk_text(
                doc["content"],
                metadata={
                    "source": doc["source"],
                    "num_pages": doc["num_pages"]
                }
            )
            # Adiciona 'page' baseado em chunk_index e garante 'source'
            chunks = [
                {
                    "content": chunk["content"],
                    "source": chunk.get("source", doc["source"]),  # Garante source
                    "page": chunk.get('chunk_index', i) + 1,  # 1-based page number (seção)
                    **{k: v for k, v in chunk.items() if k not in ['content', 'source', 'page']}
                }
                for i, chunk in enumerate(base_chunks)
            ]
        
        # Adiciona metadados do index.json (se disponível)
        doc_filename = doc_file.name
        doc_metadata = metadata_index.get(doc_filename, {})
        
        # Auto-geração de metadados se não existir no index.json
        if not doc_metadata and settings.enable_auto_metadata_generation:
            logger.info(f"      [AUTO-METADATA] Documento {doc_filename} não está no index.json")
            logger.info(f"      [AUTO-METADATA] Gerando metadados automaticamente...")
            
            # Gerar metadados a partir do conteúdo
            generated_metadata = generate_metadata_from_content(
                content=doc["content"],
                filename=doc_filename
            )
            
            # Se gerou com sucesso, usar e salvar
            if generated_metadata:
                doc_metadata = generated_metadata
                
                # Salvar no index.json para cache futuro
                save_metadata_to_index(
                    directory=str(literature_dir),
                    filename=doc_filename,
                    metadata=generated_metadata
                )
        
        if doc_metadata:
            logger.info(f"      [METADATA] Aplicando metadados: {doc_metadata.get('title', 'N/A')}")
        
        # Merge metadados em todos os chunks
        for chunk in chunks:
            # document_title SEMPRE presente (fallback para filename)
            document_title = doc_metadata.get('title', '') or doc_filename
            
            chunk['document_title'] = document_title
            chunk['title'] = doc_metadata.get('title', '')
            chunk['authors'] = doc_metadata.get('authors', [])
            chunk['year'] = doc_metadata.get('year')
            chunk['doc_type'] = doc_metadata.get('type', 'document')
            chunk['perspectives'] = doc_metadata.get('perspectives', [])
            chunk['language'] = doc_metadata.get('language', 'en')
            chunk['description'] = doc_metadata.get('description', '')
        
        all_chunks.extend(chunks)
        logger.info(f"      [OK] {len(chunks)} chunks criados")
    
    logger.info(f"\n[STATS] Total de chunks: {len(all_chunks)}")
    
    if not all_chunks:
        logger.error("[ERRO] Nenhum chunk foi criado. Verifique os documentos.")
        return
    
    # Gera embeddings
    logger.info("\n[EMBED] Gerando embeddings...")
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = embedding_manager.embed_batch(texts, batch_size=32)
    logger.info(f"   [OK] {len(embeddings)} embeddings gerados")
    
    # Adiciona ao vector store
    logger.info(f"\n[STORE] Adicionando ao {type(vector_store).__name__}...")
    
    # Prepara documentos com IDs únicos
    documents_to_add = []
    embeddings_list = []
    
    for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
        # Monta doc_dict com source/page no nível raiz e resto em metadata
        source = chunk.get("source", "unknown")
        page = chunk.get("page", 0)
        metadata = {k: v for k, v in chunk.items() 
                   if k not in ["content", "source", "page"]}
        
        doc_dict = {
            "id": f"doc_{i}",
            "content": chunk["content"],
            "source": source,
            "page": page,
            "metadata": metadata
        }
        documents_to_add.append(doc_dict)
        
        # Converte embedding para lista se for numpy array
        if hasattr(embedding, 'tolist'):
            embeddings_list.append(embedding.tolist())
        elif isinstance(embedding, list):
            embeddings_list.append(embedding)
        else:
            # Se já for outro formato, converte para lista
            embeddings_list.append(list(embedding))
    
    try:
        # Adiciona em batches para evitar payload muito grande
        batch_size = 100  # Qdrant tem limite de 33MB por request
        total_docs = len(documents_to_add)
        
        logger.info(f"[DEBUG] Adicionando {total_docs} docs em batches de {batch_size}...")
        
        for i in range(0, total_docs, batch_size):
            batch_docs = documents_to_add[i:i+batch_size]
            batch_embeddings = embeddings_list[i:i+batch_size]
            
            vector_store.add_documents(
                documents=batch_docs,
                embeddings=batch_embeddings
            )
            logger.info(f"   [BATCH] {i+len(batch_docs)}/{total_docs} documentos adicionados ({int((i+len(batch_docs))/total_docs*100)}%)")
        
        logger.info("   [OK] Todos os documentos adicionados com sucesso")
    except Exception as e:
        import traceback
        logger.error(f"   [ERRO] Erro ao adicionar documentos: {e}")
        logger.error(f"[DEBUG] Traceback completo:\n{traceback.format_exc()}")
        return
    
    # Estatísticas finais
    logger.info("\n" + "=" * 70)
    logger.info("[OK] Base de Conhecimento Construída com Sucesso!")
    logger.info("=" * 70)
    
    try:
        stats = vector_store.get_stats()
        logger.info(f"[STATS] Estatisticas:")
        logger.info(f"   Documentos indexados: {stats.num_documents}")
        logger.info(f"   Dimensao dos vetores: {stats.vector_dimensions}")
        logger.info(f"   Metrica de distancia: {stats.distance_metric}")
    except Exception as e:
        logger.warning(f"[WARN] Nao foi possivel obter estatisticas: {e}")
    
    # Teste rápido de retrieval
    logger.info("\n[TEST] Executando teste rápido...")
    test_query = "O que é Balanced Scorecard?"
    
    try:
        test_embedding = embedding_manager.embed_text(test_query)
        results = vector_store.vector_search(
            query_embedding=test_embedding,
            k=3
        )
        
        logger.info(f"   Query: '{test_query}'")
        logger.info(f"   Resultados: {len(results)}")
        
        if results:
            source = results[0].source
            page_label = "Seção" if source.endswith('.md') else "Página"
            logger.info(f"\n   [DOC] Melhor resultado:")
            logger.info(f"      Fonte: {source}")
            logger.info(f"      {page_label}: {results[0].page}")
            logger.info(f"      Score: {results[0].score:.4f}")
            logger.info(f"      Preview: {results[0].content[:150]}...")
        else:
            logger.warning("   [WARN]  Nenhum resultado encontrado")
    except Exception as e:
        logger.error(f"   [ERRO] Erro no teste: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info("[SUCCESS] Pipeline de Ingestão Completo!")
    logger.info("=" * 70)
    logger.info("[INFO] Próximos passos:")
    logger.info("   1. Testar retrieval com queries reais")
    logger.info("   2. Ajustar parâmetros de chunking se necessário")
    logger.info("   3. Avaliar qualidade dos resultados")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
