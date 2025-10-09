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
    logger.info(f"\n🔨 Criando índice '{settings.vector_store_index}'...")
    try:
        vector_store.create_index(
            index_name=settings.vector_store_index,
            dimension=embedding_manager.embedding_dim,
            force_recreate=True
        )
        logger.info("   ✅ Índice criado com sucesso")
    except Exception as e:
        logger.error(f"   ❌ Erro ao criar índice: {e}")
        return
    
    # Carrega documentos
    literature_dir = Path(settings.literature_dir)
    pdf_files = list(literature_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"\n⚠️  Nenhum arquivo PDF encontrado em {literature_dir}")
        logger.info("💡 Por favor, adicione arquivos PDF da literatura BSC neste diretório.")
        logger.info("   Exemplo: papers sobre Balanced Scorecard, livros, artigos, etc.")
        return
    
    logger.info(f"\n📄 Encontrados {len(pdf_files)} arquivos PDF")
    
    all_chunks: List[Dict[str, Any]] = []
    
    # Processa cada PDF
    logger.info("\n📚 Processando documentos...")
    for pdf_file in tqdm(pdf_files, desc="PDFs"):
        logger.info(f"   📖 {pdf_file.name}")
        
        # Carrega PDF
        doc = load_pdf(str(pdf_file))
        if not doc:
            logger.error(f"      ❌ Erro ao carregar")
            continue
        
        # Divide em chunks
        chunks = chunker.chunk_text(
            doc["content"],
            metadata={
                "source": doc["source"],
                "num_pages": doc["num_pages"]
            }
        )
        
        # Aplica Contextual Retrieval se habilitado
        if contextual_chunker:
            logger.info(f"      🔍 Aplicando Contextual Retrieval...")
            chunks = contextual_chunker.add_context_to_chunks(
                chunks=chunks,
                document_context=f"Documento: {doc['source']}"
            )
        
        all_chunks.extend(chunks)
        logger.info(f"      ✅ {len(chunks)} chunks criados")
    
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
        doc_dict = {
            "id": f"doc_{i}",
            "content": chunk["content"],
            "metadata": chunk.get("metadata", {})
        }
        documents_to_add.append(doc_dict)
        embeddings_list.append(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
    
    try:
        vector_store.add_documents(
            documents=documents_to_add,
            embeddings=embeddings_list
        )
        logger.info("   ✅ Documentos adicionados com sucesso")
    except Exception as e:
        logger.error(f"   ❌ Erro ao adicionar documentos: {e}")
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
        test_embedding = embedding_manager.embed_text(test_query).tolist()
        results = vector_store.vector_search(
            query_embedding=test_embedding,
            limit=3
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
