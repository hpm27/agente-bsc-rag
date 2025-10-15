"""Factory para criação de memory providers.

Este módulo implementa o Factory Pattern para abstrair a criação
de memory providers, permitindo troca transparente entre backends
(Mem0, Supabase, Redis, etc) via configuração.
"""

import logging
from typing import Any, ClassVar

from src.memory.mem0_provider import Mem0Provider
from src.memory.provider import MemoryProvider

logger = logging.getLogger(__name__)


class MemoryProviderNotFoundError(Exception):
    """Levantado quando provider type não está registrado no factory."""

    def __init__(self, provider_type: str):
        self.provider_type = provider_type
        super().__init__(
            f"Memory provider '{provider_type}' não encontrado. "
            f"Providers disponíveis: {list(MemoryFactory._registry.keys())}"
        )


class MemoryFactory:
    """Factory para criação de memory providers com registry pattern.

    Gerencia registro e criação de memory providers, permitindo extensão
    fácil com novos backends sem modificar código cliente (Open/Closed Principle).

    Attributes:
        _registry: Dicionário mapeando provider_type -> classe implementadora

    Examples:
        >>> # Uso básico
        >>> provider = MemoryFactory.get_provider("mem0", api_key="key")
        >>> isinstance(provider, MemoryProvider)
        True

        >>> # Adicionar novo provider
        >>> MemoryFactory.register("redis", RedisProvider)
        >>> redis_provider = MemoryFactory.get_provider("redis", host="localhost")
    """

    # Registry de providers disponíveis
    _registry: ClassVar[dict[str, type[MemoryProvider]]] = {
        "mem0": Mem0Provider,
        # Futuros providers:
        # "supabase": SupabaseProvider,
        # "redis": RedisProvider,
    }

    @classmethod
    def get_provider(
        cls,
        provider_type: str = "mem0",
        **kwargs: Any
    ) -> MemoryProvider:
        """Cria instância de memory provider baseado no tipo.

        Args:
            provider_type: Tipo do provider ("mem0", "supabase", "redis", etc)
            **kwargs: Argumentos específicos do provider (api_key, host, etc)

        Returns:
            MemoryProvider: Instância do provider solicitado

        Raises:
            MemoryProviderNotFoundError: Se provider_type não estiver registrado
            Mem0ClientError: Erros de inicialização específicos do provider

        Examples:
            >>> # Mem0 provider (default)
            >>> provider = MemoryFactory.get_provider()

            >>> # Mem0 com API key explícita
            >>> provider = MemoryFactory.get_provider("mem0", api_key="xyz")

            >>> # Futuro: Supabase provider
            >>> provider = MemoryFactory.get_provider("supabase", url="...", key="...")
        """
        if provider_type not in cls._registry:
            raise MemoryProviderNotFoundError(provider_type)

        provider_class = cls._registry[provider_type]

        try:
            provider = provider_class(**kwargs)
            logger.info(
                "[OK] Memory provider %r inicializado com sucesso",
                provider_type
            )
            return provider
        except Exception as e:
            logger.error(
                "[ERRO] Falha ao inicializar provider %r: %s",
                provider_type,
                e
            )
            raise

    @classmethod
    def register(cls, provider_type: str, provider_class: type[MemoryProvider]) -> None:
        """Registra novo memory provider no factory.

        Permite extensão dinâmica com novos backends sem modificar código.

        Args:
            provider_type: Identificador único do provider (e.g. "redis")
            provider_class: Classe que implementa MemoryProvider Protocol

        Examples:
            >>> class RedisProvider:
            ...     # Implementa MemoryProvider Protocol
            ...     pass
            >>> MemoryFactory.register("redis", RedisProvider)
        """
        cls._registry[provider_type] = provider_class
        logger.info("[OK] Provider %r registrado no factory", provider_type)

    @classmethod
    def list_providers(cls) -> list[str]:
        """Lista todos providers disponíveis no registry.

        Returns:
            list[str]: Nomes dos providers registrados

        Examples:
            >>> MemoryFactory.list_providers()
            ['mem0']
        """
        return list(cls._registry.keys())

