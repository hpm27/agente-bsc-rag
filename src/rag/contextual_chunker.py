"""
Contextual Chunking - Anthropic's Contextual Retrieval Technique.

Esta técnica adiciona contexto explicativo a cada chunk ANTES de embedar,
reduzindo falhas de retrieval em 35-49% segundo paper da Anthropic (Set/2024).

Referência: https://www.anthropic.com/news/contextual-retrieval
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from loguru import logger
from anthropic import Anthropic

from .chunker import SemanticChunker, TableAwareChunker
from config.settings import settings


@dataclass
class ContextualChunk:
    """Chunk com contexto explicativo adicionado."""
    original_content: str
    contextual_content: str  # Content com contexto prepended
    context: str  # Apenas o contexto gerado
    metadata: Dict[str, Any]
    chunk_index: int
    total_chunks: int


class ContextualChunker:
    """
    Chunker que adiciona contexto explicativo usando LLM.
    
    Processo:
    1. Chunking semântico normal
    2. Para cada chunk, gera contexto usando LLM
    3. Prefixa contexto ao chunk
    4. Embeda o chunk contextualizado
    
    Benefícios:
    - Chunks isolados têm mais informação
    - Melhora retrieval de chunks que perderam contexto
    - Reduz alucinações por contexto insuficiente
    """
    
    def __init__(
        self,
        base_chunker: Optional[SemanticChunker] = None,
        use_table_aware: bool = True,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        cache_dir: Optional[str] = None,
        enable_caching: bool = True
    ):
        """
        Inicializa Contextual Chunker.
        
        Args:
            base_chunker: Chunker base (se None, cria um novo)
            use_table_aware: Se True, usa TableAwareChunker
            api_key: Chave API Anthropic (usa settings se None)
            model: Modelo Claude a usar
            cache_dir: Diretório para cache de contextos
            enable_caching: Se True, cacheia contextos gerados
        """
        # Chunker base
        if base_chunker is None:
            self.base_chunker = TableAwareChunker() if use_table_aware else SemanticChunker()
        else:
            self.base_chunker = base_chunker
        
        # Cliente Anthropic
        self.client = Anthropic(api_key=api_key or getattr(settings, 'anthropic_api_key', None))
        self.model = model
        
        # Cache
        self.enable_caching = enable_caching
        self.cache_dir = Path(cache_dir or "./data/contextual_cache")
        if self.enable_caching:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ContextualChunker inicializado com modelo {model}")
    
    def chunk_document(
        self,
        document: Dict[str, Any],
        document_summary: Optional[str] = None,
        use_cache: bool = True
    ) -> List[ContextualChunk]:
        """
        Divide documento em chunks contextualizados.
        
        Args:
            document: Documento com 'content' e metadados
            document_summary: Resumo do documento (gerado se None)
            use_cache: Se True, usa cache de contextos
            
        Returns:
            Lista de ContextualChunk
        """
        # 1. Chunking básico
        base_chunks = self.base_chunker.chunk_document(document)
        
        # 2. Gera resumo do documento se não fornecido
        if document_summary is None:
            document_summary = self._generate_document_summary(
                document.get('content', ''),
                document
            )
        
        # 3. Gera contexto para cada chunk
        contextual_chunks = []
        for chunk_data in base_chunks:
            # Verifica cache
            cache_key = self._get_cache_key(chunk_data['content'], document_summary)
            cached_context = self._get_from_cache(cache_key) if use_cache else None
            
            if cached_context:
                context = cached_context
                logger.debug(f"Contexto recuperado do cache para chunk {chunk_data.get('chunk_index', 0)}")
            else:
                # Gera contexto usando LLM
                context = self._generate_context(
                    chunk_content=chunk_data['content'],
                    document_summary=document_summary,
                    document=document
                )
                
                # Salva no cache
                if use_cache:
                    self._save_to_cache(cache_key, context)
            
            # Cria chunk contextualizado
            contextual_content = f"{context}\n\n{chunk_data['content']}"
            
            contextual_chunks.append(ContextualChunk(
                original_content=chunk_data['content'],
                contextual_content=contextual_content,
                context=context,
                metadata={k: v for k, v in chunk_data.items() if k != 'content'},
                chunk_index=chunk_data.get('chunk_index', 0),
                total_chunks=chunk_data.get('total_chunks', len(base_chunks))
            ))
        
        logger.info(f"Documento dividido em {len(contextual_chunks)} chunks contextualizados")
        return contextual_chunks
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None,
        text_summary: Optional[str] = None
    ) -> List[ContextualChunk]:
        """
        Divide texto em chunks contextualizados.
        
        Args:
            text: Texto para dividir
            metadata: Metadados
            text_summary: Resumo do texto
            
        Returns:
            Lista de ContextualChunk
        """
        document = {'content': text}
        if metadata:
            document.update(metadata)
        
        return self.chunk_document(document, text_summary)
    
    def _generate_document_summary(
        self,
        content: str,
        document: Dict[str, Any]
    ) -> str:
        """
        Gera resumo do documento inteiro.
        
        Args:
            content: Conteúdo do documento
            document: Documento completo com metadados
            
        Returns:
            Resumo do documento
        """
        # Trunca conteúdo se muito longo (max 10k caracteres para resumo)
        truncated_content = content[:10000] if len(content) > 10000 else content
        
        # Metadados relevantes
        source = document.get('source', 'documento desconhecido')
        title = document.get('title', '')
        
        prompt = f"""Analise o documento abaixo e crie um resumo conciso (2-3 sentenças) descrevendo:
1. Do que se trata o documento
2. Principais temas abordados
3. Contexto ou domínio (ex: gestão, finanças, BSC, etc.)

Fonte: {source}
{f"Título: {title}" if title else ""}

Conteúdo:
{truncated_content}

Resumo (2-3 sentenças):"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            summary = response.content[0].text.strip()
            logger.debug(f"Resumo do documento gerado: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo do documento: {e}")
            return f"Documento sobre {source}"
    
    def _generate_context(
        self,
        chunk_content: str,
        document_summary: str,
        document: Dict[str, Any]
    ) -> str:
        """
        Gera contexto explicativo para um chunk.
        
        Args:
            chunk_content: Conteúdo do chunk
            document_summary: Resumo do documento
            document: Documento completo
            
        Returns:
            Contexto explicativo
        """
        # Cria prompt usando técnica da Anthropic
        prompt = f"""Você receberá um resumo de documento e um trecho (chunk) desse documento.
Sua tarefa é criar uma frase de contexto curta (1-2 sentenças) que explica sobre o que este trecho trata, situando-o no contexto do documento maior.

Esta contextualização será usada para melhorar a busca semântica.

Diretrizes:
- Seja conciso (máximo 2 sentenças)
- Mencione o tópico principal do chunk
- Se relevante, mencione a perspectiva BSC (Financeira, Clientes, Processos, Aprendizado)
- NÃO repita o conteúdo do chunk, apenas contextualize-o
- Use linguagem clara e objetiva

Resumo do documento:
{document_summary}

Trecho do documento:
{chunk_content[:500]}...

Contexto (1-2 sentenças):"""

        try:
            # Usa Prompt Caching da Anthropic para reduzir custos
            # O document_summary é cacheado entre chunks do mesmo documento
            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": "Você é um especialista em contextualização de documentos para sistemas de busca semântica.",
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": prompt}]
            )
            
            context = response.content[0].text.strip()
            
            # Remove aspas se houver
            context = context.strip('"\'')
            
            return context
            
        except Exception as e:
            logger.error(f"Erro ao gerar contexto: {e}")
            # Fallback: usa resumo do documento como contexto
            return f"Contexto: {document_summary}"
    
    def _get_cache_key(self, content: str, summary: str) -> str:
        """
        Gera chave de cache para chunk.
        
        Args:
            content: Conteúdo do chunk
            summary: Resumo do documento
            
        Returns:
            Hash MD5 como chave
        """
        combined = f"{summary}||{content}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Recupera contexto do cache.
        
        Args:
            cache_key: Chave do cache
            
        Returns:
            Contexto ou None se não encontrado
        """
        if not self.enable_caching:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data['context']
            except Exception as e:
                logger.warning(f"Erro ao ler cache {cache_key}: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, context: str):
        """
        Salva contexto no cache.
        
        Args:
            cache_key: Chave do cache
            context: Contexto a salvar
        """
        if not self.enable_caching:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'context': context,
                    'cache_key': cache_key
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar cache {cache_key}: {e}")
    
    def clear_cache(self):
        """Remove todos os contextos cacheados."""
        if not self.enable_caching:
            return
        
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cache de contextos limpo")


def create_contextual_chunker(
    use_table_aware: bool = True,
    enable_caching: bool = True
) -> ContextualChunker:
    """
    Factory para criar ContextualChunker com configurações padrão.
    
    Args:
        use_table_aware: Se True, preserva tabelas intactas
        enable_caching: Se True, cacheia contextos gerados
        
    Returns:
        ContextualChunker configurado
    """
    return ContextualChunker(
        use_table_aware=use_table_aware,
        enable_caching=enable_caching
    )

