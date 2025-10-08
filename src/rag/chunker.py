"""
Chunking semântico de documentos.
"""
from typing import List, Dict, Any
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from config.settings import settings


class SemanticChunker:
    """Chunker que respeita limites semânticos dos documentos."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Inicializa o chunker.
        
        Args:
            chunk_size: Tamanho máximo do chunk em caracteres
            chunk_overlap: Sobreposição entre chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Separadores em ordem de prioridade
        # Prioriza quebras lógicas (seções, parágrafos) sobre quebras arbitrárias
        self.separators = [
            "\n\n\n",  # Múltiplas quebras de linha (seções)
            "\n\n",    # Parágrafos
            "\n",      # Linhas
            ". ",      # Sentenças
            "! ",
            "? ",
            "; ",
            ": ",
            ", ",
            " ",       # Palavras
            ""         # Caracteres
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len
        )
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Divide texto em chunks semânticos.
        
        Args:
            text: Texto para dividir
            metadata: Metadados do documento
            
        Returns:
            Lista de chunks com metadados
        """
        # Remove espaços em branco excessivos
        text = self._clean_text(text)
        
        # Divide em chunks
        chunks = self.splitter.split_text(text)
        
        # Adiciona metadados
        result = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            if metadata:
                chunk_data.update(metadata)
            
            result.append(chunk_data)
        
        logger.debug(f"Texto dividido em {len(chunks)} chunks")
        return result
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Divide documento completo em chunks.
        
        Args:
            document: Documento com 'content' e metadados
            
        Returns:
            Lista de chunks
        """
        text = document.get("content", "")
        metadata = {k: v for k, v in document.items() if k != "content"}
        
        return self.chunk_text(text, metadata)
    
    def chunk_by_sections(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Divide texto respeitando seções identificadas por títulos.
        
        Args:
            text: Texto para dividir
            metadata: Metadados do documento
            
        Returns:
            Lista de chunks por seção
        """
        # Identifica seções (títulos em maiúsculas ou com marcadores)
        section_pattern = r'\n\n([A-Z][A-Z\s]+)\n\n|\n\n(\d+\.\s+[^\n]+)\n\n'
        sections = re.split(section_pattern, text)
        
        chunks = []
        current_section = None
        
        for i, section in enumerate(sections):
            if section is None:
                continue
            
            # Verifica se é um título
            if re.match(r'^[A-Z][A-Z\s]+$', section) or re.match(r'^\d+\.\s+', section):
                current_section = section.strip()
                continue
            
            # Processa conteúdo da seção
            if section.strip():
                section_chunks = self.chunk_text(section, metadata)
                
                # Adiciona informação da seção
                for chunk in section_chunks:
                    chunk["section"] = current_section
                    chunks.append(chunk)
        
        logger.debug(f"Documento dividido em {len(chunks)} chunks por seção")
        return chunks
    
    def chunk_with_context(
        self,
        text: str,
        metadata: Dict[str, Any] = None,
        context_size: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Divide texto adicionando contexto dos chunks adjacentes.
        
        Args:
            text: Texto para dividir
            metadata: Metadados do documento
            context_size: Tamanho do contexto a adicionar
            
        Returns:
            Lista de chunks com contexto
        """
        # Divide em chunks básicos
        base_chunks = self.chunk_text(text, metadata)
        
        # Adiciona contexto
        for i, chunk in enumerate(base_chunks):
            # Contexto anterior
            if i > 0:
                prev_content = base_chunks[i-1]["content"]
                chunk["context_before"] = prev_content[-context_size:]
            
            # Contexto posterior
            if i < len(base_chunks) - 1:
                next_content = base_chunks[i+1]["content"]
                chunk["context_after"] = next_content[:context_size]
        
        return base_chunks
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Limpa texto removendo espaços excessivos.
        
        Args:
            text: Texto para limpar
            
        Returns:
            Texto limpo
        """
        # Remove múltiplos espaços
        text = re.sub(r' +', ' ', text)
        
        # Remove múltiplas quebras de linha (mantém no máximo 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove espaços no início e fim de linhas
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        return text.strip()
    
    def estimate_chunks(self, text: str) -> int:
        """
        Estima número de chunks sem processar o texto.
        
        Args:
            text: Texto para estimar
            
        Returns:
            Número estimado de chunks
        """
        text_length = len(text)
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        return max(1, text_length // effective_chunk_size)


class TableAwareChunker(SemanticChunker):
    """Chunker que preserva tabelas intactas."""
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Divide texto preservando tabelas.
        
        Args:
            text: Texto para dividir
            metadata: Metadados
            
        Returns:
            Lista de chunks
        """
        # Identifica tabelas (padrão simples: linhas com | ou múltiplos tabs)
        table_pattern = r'(\n[|\t].+[|\t].+\n)+'
        
        # Separa texto e tabelas
        parts = re.split(f'({table_pattern})', text)
        
        chunks = []
        for part in parts:
            if not part.strip():
                continue
            
            # Se é uma tabela, mantém intacta
            if re.match(table_pattern, part):
                chunk_data = {
                    "content": part,
                    "type": "table"
                }
                if metadata:
                    chunk_data.update(metadata)
                chunks.append(chunk_data)
            else:
                # Texto normal: chunk normalmente
                text_chunks = super().chunk_text(part, metadata)
                for chunk in text_chunks:
                    chunk["type"] = "text"
                chunks.extend(text_chunks)
        
        return chunks
