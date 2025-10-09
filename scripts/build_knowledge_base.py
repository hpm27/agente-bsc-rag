"""
Script para construir a base de conhecimento a partir dos documentos BSC.

Pipeline completo:
1. Carrega PDFs
2. Chunk com TableAwareChunker
3. Contextual Retrieval (Anthropic) - adiciona contexto aos chunks
4. Embeddings (OpenAI text-embedding-3-large)
5. Armazena em Vector Store (Qdrant/Weaviate/Redis)
"""
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
    logger.info("🚀 Pipeline de Ingestão - Base de Conhecimento BSC")
    logger.info("=" * 70)
    
    # Inicializa componentes
    logger.info("\n📦 Inicializando componentes...")
    vector_store = create_vector_store()
    logger.info(f"   ✅ Vector Store: {type(vector_store).__name__}")
    
    embedding_manager = EmbeddingManager()
    logger.info(f"   ✅ Embeddings: {embedding_manager.provider} ({embedding_manager.model_name if embedding_manager.provider == 'openai' else 'fine-tuned'})")
    
    chunker = TableAwareChunker()
    logger.info(f"   ✅ Chunker: TableAwareChunker")
    
    # Contextual Retrieval (opcional)
    contextual_chunker = None
    if settings.enable_contextual_retrieval and settings.anthropic_api_key:
        contextual_chunker = ContextualChunker()
        logger.info(f"   ✅ Contextual Retrieval: Habilitado (Anthropic)")
    else:
        logger.info(f"   ⚠️  Contextual Retrieval: Desabilitado")
    
    # Cria/recria índice
    logger.info(f"\n[SETUP] Criando índice '{settings.vector_store_index}'...")
    try:
        vector_store.create_index(
            index_name=settings.vector_store_index,
            force_recreate=True
        )
        logger.info("   [OK] Índice criado com sucesso")
    except Exception as e:
        logger.error(f"   ❌ Erro ao criar índice: {e}")
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
            # Converte ContextualChunk para dict format
            chunks = [
                {
                    "content": c.contextual_content,  # Usa conteúdo com contexto
                    **c.metadata
                }
                for c in contextual_chunks
            ]
        else:
            chunks = chunker.chunk_text(
                doc["content"],
                metadata={
                    "source": doc["source"],
                    "num_pages": doc["num_pages"]
                }
            )
        
        all_chunks.extend(chunks)
        logger.info(f"      [OK] {len(chunks)} chunks criados")
    
    logger.info(f"\n📊 Total de chunks: {len(all_chunks)}")
    
    if not all_chunks:
        logger.error("❌ Nenhum chunk foi criado. Verifique os documentos.")
        return
    
    # Gera embeddings
    logger.info("\n🧬 Gerando embeddings...")
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = embedding_manager.embed_batch(texts, batch_size=32)
    logger.info(f"   ✅ {len(embeddings)} embeddings gerados")
    
    # Adiciona ao vector store
    logger.info(f"\n💾 Adicionando ao {type(vector_store).__name__}...")
    
    # Prepara documentos com IDs únicos
    documents_to_add = []
    embeddings_list = []
    
    for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
        # Monta doc_dict com metadata corretamente
        metadata = {k: v for k, v in chunk.items() if k != "content"}
        
        doc_dict = {
            "id": f"doc_{i}",
            "content": chunk["content"],
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
        
        logger.info("   ✅ Todos os documentos adicionados com sucesso")
    except Exception as e:
        import traceback
        logger.error(f"   ❌ Erro ao adicionar documentos: {e}")
        logger.error(f"[DEBUG] Traceback completo:\n{traceback.format_exc()}")
        return
    
    # Estatísticas finais
    logger.info("\n" + "=" * 70)
    logger.info("✅ Base de Conhecimento Construída com Sucesso!")
    logger.info("=" * 70)
    
    try:
        stats = vector_store.get_stats()
        logger.info(f"📊 Estatísticas:")
        logger.info(f"   • Documentos indexados: {stats.num_docs}")
        logger.info(f"   • Dimensão dos vetores: {stats.vector_dimension}")
        logger.info(f"   • Vector Store: {stats.store_type}")
    except Exception as e:
        logger.warning(f"⚠️  Não foi possível obter estatísticas: {e}")
    
    # Teste rápido de retrieval
    logger.info("\n🧪 Executando teste rápido...")
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
            logger.info(f"\n   📄 Melhor resultado:")
            logger.info(f"      Fonte: {results[0].metadata.get('source', 'N/A')}")
            logger.info(f"      Score: {results[0].score:.4f}")
            logger.info(f"      Preview: {results[0].content[:150]}...")
        else:
            logger.warning("   ⚠️  Nenhum resultado encontrado")
    except Exception as e:
        logger.error(f"   ❌ Erro no teste: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info("🎉 Pipeline de Ingestão Completo!")
    logger.info("=" * 70)
    logger.info("💡 Próximos passos:")
    logger.info("   1. Testar retrieval com queries reais")
    logger.info("   2. Ajustar parâmetros de chunking se necessário")
    logger.info("   3. Avaliar qualidade dos resultados")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
