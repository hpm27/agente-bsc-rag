"""
Módulo de tradução e expansão de queries para busca multilíngue.

Implementa:
- Tradução PT-BR <-> EN usando OpenAI GPT-5 mini
- Cache de traduções para otimização
- Detecção automática de idioma
"""

import hashlib
import re
from typing import Literal

from config.settings import settings
from loguru import logger
from openai import OpenAI


class QueryTranslator:
    """Tradutor de queries com cache e detecção de idioma."""

    def __init__(self):
        """Inicializa o tradutor."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.translation_llm_model  # Configurável via .env
        self._cache: dict[str, str] = {}
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
        has_pt_accents = bool(re.search(r"[áàâãéêíóôõúüç]", text_lower))

        # Sufixos típicos do português (não existem em inglês)
        has_pt_suffixes = bool(
            re.search(r"\b\w*(ção|ões|ário|ários|eira|eiras|eiro|eiros)\b", text_lower)
        )

        # Palavras comuns em português (expandidas com termos BSC)
        pt_keywords = [
            "o que",
            "como",
            "por que",
            "porque",
            "quando",
            "onde",
            "qual",
            "quais",
            "é",
            "são",
            "está",
            "estão",
            "foi",
            "foram",
            "ser",
            "estar",
            "implementar",
            "gestão",
            "estratégia",
            "plano",
            "objetivo",
            "perspectiva",
            "perspectivas",
            "criar",
            "desenvolver",
            "medir",
            "indicador",
            "indicadores",
            "meta",
            "metas",
            "processo",
            "processos",
            "financeira",
            "financeiro",
            "financeiros",
            "cliente",
            "clientes",
            "aprendizado",
            "crescimento",
            "interno",
            "internos",
            "completo",
            "completa",
        ]

        # Palavras exclusivas EN (expandidas)
        en_keywords = [
            "what",
            "how",
            "why",
            "when",
            "where",
            "which",
            "is",
            "are",
            "was",
            "were",
            "perspective",
            "perspectives",
            "create",
            "develop",
            "measure",
            "indicator",
            "indicators",
            "goal",
            "goals",
            "process",
            "processes",
            "financial",
            "customer",
            "customers",
            "learning",
            "growth",
            "internal",
            "complete",
        ]

        # Contagem de keywords (usando word boundaries para evitar substrings)
        pt_count = sum(
            1 for kw in pt_keywords if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)
        )
        en_count = sum(
            1 for kw in en_keywords if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)
        )

        # Decisão
        if has_pt_accents:
            return "pt-br"
        if has_pt_suffixes:
            # Sufixos portugueses são forte indicador
            return "pt-br"
        if pt_count >= 1 and en_count == 0:
            return "pt-br"
        if en_count >= 1 and pt_count == 0:
            return "en"
        if pt_count > en_count:
            return "pt-br"
        if en_count > pt_count:
            return "en"
        if pt_count == 0 and en_count == 0:
            # Caso especial: nenhuma keyword encontrada
            # Assumir PT-BR como padrão (contexto brasileiro)
            logger.debug(
                f"[DETECT] Query sem keywords detectáveis: '{text[:50]}...' - Assumindo PT-BR"
            )
            return "pt-br"
        # Empate com keywords: situação ambígua
        logger.debug(
            f"[DETECT] Query ambígua (PT={pt_count}, EN={en_count}): '{text[:50]}...' - Retornando 'other'"
        )
        return "other"

    def _get_cache_key(self, text: str, target_lang: str) -> str:
        """Gera chave de cache para tradução."""
        combined = f"{text}||{target_lang}"
        return hashlib.md5(combined.encode()).hexdigest()

    def translate(
        self, query: str, target_lang: Literal["pt-br", "en"], use_cache: bool = True
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
                logger.debug("[CACHE HIT] Tradução recuperada do cache")
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
                    {"role": "user", "content": query},
                ],
                temperature=1.0,  # GPT-5 mini requer temperature=1.0 (unico valor aceito)
                max_completion_tokens=settings.gpt5_max_completion_tokens,  # usar máximo suportado
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

    def expand_query(self, query: str) -> dict[str, str]:
        """
        Expande query para ambos idiomas (PT-BR e EN).

        Args:
            query: Query original

        Returns:
            Dict com queries em ambos idiomas: {"pt-br": ..., "en": ...}
        """
        source_lang = self._detect_language(query)

        if source_lang == "pt-br":
            logger.debug(f"[DETECT] Query detectada como PT-BR: '{query[:50]}...'")
            return {"pt-br": query, "en": self.translate(query, "en")}
        if source_lang == "en":
            logger.debug(f"[DETECT] Query detectada como EN: '{query[:50]}...'")
            return {"pt-br": self.translate(query, "pt-br"), "en": query}
        # Idioma ambíguo/desconhecido, assumir PT-BR como fallback
        logger.warning(
            f"[DETECT] Idioma ambíguo para query '{query[:50]}...' - Assumindo PT-BR como fallback"
        )
        return {"pt-br": query, "en": self.translate(query, "en")}

    def clear_cache(self):
        """Limpa cache de traduções."""
        self._cache.clear()
        logger.info("[CACHE] Cache de traduções limpo")

    @property
    def cache_size(self) -> int:
        """Retorna tamanho atual do cache."""
        return len(self._cache)
