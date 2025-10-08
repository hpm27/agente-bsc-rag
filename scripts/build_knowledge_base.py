"""
Script para construir a base de conhecimento a partir dos documentos BSC.
"""
import os
import sys
from pathlib import Path
from tqdm import tqdm
from loguru import logger

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pypdf import PdfReader
from src.rag.vector_store import RedisVectorStore
from src.rag.embeddings import EmbeddingManager
from src.rag.chunker import TableAwareChunker
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
    """Função principal."""
    logger.info("=" * 60)
    logger.info("Construindo Base de Conhecimento BSC")
    logger.info("=" * 60)
    
    # Inicializa componentes
    logger.info("Inicializando componentes...")
    vector_store = RedisVectorStore()
    embedding_manager = EmbeddingManager()
    chunker = TableAwareChunker()
    
    # Cria índice
    logger.info("Criando índice Redis...")
    vector_store.create_index(force_recreate=True)
    
    # Carrega documentos
    literature_dir = Path(settings.literature_dir)
    pdf_files = list(literature_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"Nenhum arquivo PDF encontrado em {literature_dir}")
        logger.info("Por favor, adicione arquivos PDF da literatura BSC neste diretório.")
        return
    
    logger.info(f"Encontrados {len(pdf_files)} arquivos PDF")
    
    all_chunks = []
    
    # Processa cada PDF
    for pdf_file in tqdm(pdf_files, desc="Processando PDFs"):
        logger.info(f"Processando: {pdf_file.name}")
        
        # Carrega PDF
        doc = load_pdf(str(pdf_file))
        if not doc:
            continue
        
        # Divide em chunks
        chunks = chunker.chunk_text(
            doc["content"],
            metadata={
                "source": doc["source"],
                "num_pages": doc["num_pages"]
            }
        )
        
        all_chunks.extend(chunks)
        logger.info(f"  → {len(chunks)} chunks criados")
    
    logger.info(f"\nTotal de chunks: {len(all_chunks)}")
    
    # Gera embeddings
    logger.info("Gerando embeddings...")
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = embedding_manager.embed_batch(texts, batch_size=32)
    
    # Adiciona ao vector store
    logger.info("Adicionando ao vector store...")
    
    # Adiciona IDs únicos
    for i, chunk in enumerate(all_chunks):
        chunk["id"] = i
    
    vector_store.add_documents(all_chunks, embeddings)
    
    # Estatísticas finais
    stats = vector_store.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Base de Conhecimento Construída com Sucesso!")
    logger.info("=" * 60)
    logger.info(f"Documentos indexados: {stats.get('num_docs', 0)}")
    logger.info(f"Termos únicos: {stats.get('num_terms', 0)}")
    logger.info(f"Tamanho do índice invertido: {stats.get('inverted_sz_mb', 0):.2f} MB")
    logger.info(f"Tamanho do índice vetorial: {stats.get('vector_index_sz_mb', 0):.2f} MB")
    logger.info("=" * 60)
    
    # Teste rápido
    logger.info("\nExecutando teste rápido...")
    test_query = "O que é Balanced Scorecard?"
    test_embedding = embedding_manager.embed_text(test_query)
    results = vector_store.vector_search(test_embedding, k=3)
    
    logger.info(f"\nQuery de teste: '{test_query}'")
    logger.info(f"Resultados encontrados: {len(results)}")
    
    if results:
        logger.info("\nPrimeiro resultado:")
        logger.info(f"  Fonte: {results[0]['source']}")
        logger.info(f"  Score: {results[0]['score']:.4f}")
        logger.info(f"  Conteúdo: {results[0]['content'][:200]}...")
    
    logger.info("\n✅ Pronto! A base de conhecimento está pronta para uso.")


if __name__ == "__main__":
    main()
