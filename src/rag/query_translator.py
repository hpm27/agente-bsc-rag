"""
Módulo de tradução e expansão de queries para busca multilíngue.

Implementa:
- Tradução PT-BR <-> EN usando OpenAI GPT-4o-mini
- Cache de traduções para otimização
- Detecção automática de idioma
"""
from typing import Literal, Optional, Dict
from functools import lru_cache
import hashlib
import re
from loguru import logger
from openai import OpenAI

from config.settings import settings


class QueryTranslator:
    """Tradutor de queries com cache e detecção de idioma."""
    
    def __init__(self):
        """Inicializa o tradutor."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Barato e rápido para tradução
        self._cache: Dict[str, str] = {}
        logger.info(f"[INIT] Query Translator inicializado (modelo: {self.model})")
    
    def _detect_language(self, text: str) -> Literal["pt-br", "en", "other"]:
        """
        Detecta o idioma do texto (mesma heurística do reranker).
        
        Args:
            text: Texto para detectar idioma
            
        Returns:
            "pt-br", "en" ou "other"
        """
        text_lower = text.lower()
        
        # Acentuação portuguesa
        has_pt_accents = bool(re.search(r'[áàâãéêíóôõúüç]', text_lower))
        
        # Palavras comuns em português
        pt_keywords = [
            "o que", "como", "por que", "porque", "quando", "onde", "qual", "quais",
            "é", "são", "está", "estão", "foi", "foram", "ser", "estar",
            "implementar", "gestão", "estratégia", "plano", "objetivo"
        ]
        
        # Palavras exclusivas EN
        en_keywords = ["what", "how", "why", "when", "where", "which", "is", "are", "was", "were"]
        
        # Contagem de keywords
        pt_count = sum(1 for kw in pt_keywords if kw in text_lower)
        en_count = sum(1 for kw in en_keywords if kw in text_lower)
        
        # Decisão
        if has_pt_accents:
            return "pt-br"
        elif pt_count >= 1 and en_count == 0:
            return "pt-br"
        elif en_count >= 1 and pt_count == 0:
            return "en"
        elif pt_count > en_count:
            return "pt-br"
        elif en_count > pt_count:
            return "en"
        else:
            return "other"
    
    def _get_cache_key(self, text: str, target_lang: str) -> str:
        """Gera chave de cache para tradução."""
        combined = f"{text}||{target_lang}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def translate(
        self,
        query: str,
        target_lang: Literal["pt-br", "en"],
        use_cache: bool = True
    ) -> str:
        """
        Traduz query para o idioma alvo.
        
        Args:
            query: Query original
            target_lang: Idioma alvo ("pt-br" ou "en")
            use_cache: Se True, usa cache de traduções
            
        Returns:
            Query traduzida
        """
        # Verificar cache
        if use_cache:
            cache_key = self._get_cache_key(query, target_lang)
            if cache_key in self._cache:
                logger.debug(f"[CACHE HIT] Tradução recuperada do cache")
                return self._cache[cache_key]
        
        # Detectar idioma da query
        source_lang = self._detect_language(query)
        
        # Se já está no idioma alvo, retornar original
        if source_lang == target_lang:
            logger.debug(f"[SKIP] Query já está em {target_lang}")
            return query
        
        # Traduzir usando GPT-4o-mini
        try:
            if target_lang == "en":
                system_prompt = "You are a professional translator. Translate the following Portuguese query to English. Keep it concise and preserve technical terms like 'Balanced Scorecard', 'BSC', etc. Return ONLY the translated text, no explanations."
            else:  # pt-br
                system_prompt = "Você é um tradutor profissional. Traduza a seguinte query em inglês para português brasileiro. Mantenha conciso e preserve termos técnicos como 'Balanced Scorecard', 'BSC', etc. Retorne APENAS o texto traduzido, sem explicações."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            translated = response.choices[0].message.content.strip()
            
            # Armazenar no cache
            if use_cache:
                cache_key = self._get_cache_key(query, target_lang)
                self._cache[cache_key] = translated
            
            logger.info(f"[TRANSLATE] '{query}' -> '{translated}' ({source_lang} -> {target_lang})")
            return translated
            
        except Exception as e:
            logger.error(f"[ERRO] Falha na tradução: {e}")
            return query  # Fallback para query original
    
    def expand_query(self, query: str) -> Dict[str, str]:
        """
        Expande query para ambos idiomas (PT-BR e EN).
        
        Args:
            query: Query original
            
        Returns:
            Dict com queries em ambos idiomas: {"pt-br": ..., "en": ...}
        """
        source_lang = self._detect_language(query)
        
        if source_lang == "pt-br":
            return {
                "pt-br": query,
                "en": self.translate(query, "en")
            }
        elif source_lang == "en":
            return {
                "pt-br": self.translate(query, "pt-br"),
                "en": query
            }
        else:
            # Idioma desconhecido, assumir PT-BR
            logger.warning(f"[WARN] Idioma desconhecido, assumindo PT-BR")
            return {
                "pt-br": query,
                "en": self.translate(query, "en")
            }
    
    def clear_cache(self):
        """Limpa cache de traduções."""
        self._cache.clear()
        logger.info("[CACHE] Cache de traduções limpo")
    
    @property
    def cache_size(self) -> int:
        """Retorna tamanho atual do cache."""
        return len(self._cache)

