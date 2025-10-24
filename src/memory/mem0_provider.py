"""Implementação Mem0 do MemoryProvider Protocol.

Este módulo implementa a interface MemoryProvider usando Mem0 Platform
como backend de memória persistente. Delega todas operações para
Mem0ClientWrapper já validado na FASE 1.4.
"""

import logging

from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile

logger = logging.getLogger(__name__)


class Mem0Provider:
    """Memory provider usando Mem0 Platform como backend.

    Implementa MemoryProvider Protocol delegando todas operações para
    Mem0ClientWrapper. Usa composition over inheritance para reutilizar
    código já testado e validado.

    Attributes:
        client: Instância do Mem0ClientWrapper

    Examples:
        >>> provider = Mem0Provider(api_key="your_api_key")
        >>> profile = ClientProfile(...)
        >>> provider.save_profile(profile)
        >>> loaded = provider.load_profile(profile.client_id)
    """

    def __init__(self, api_key: str | None = None):
        """Inicializa provider Mem0.

        Args:
            api_key: Chave API do Mem0 Platform. Se None, busca de MEM0_API_KEY env var.

        Raises:
            Mem0ClientError: Se API key não for encontrada ou inválida
        """
        self.client = Mem0ClientWrapper(api_key=api_key)
        logger.info("[OK] Mem0Provider inicializado com sucesso")

    def save_profile(self, profile: ClientProfile) -> str:
        """Salva ClientProfile no Mem0.

        Delega para Mem0ClientWrapper.save_profile().

        Args:
            profile: ClientProfile a ser salvo

        Returns:
            str: client_id do perfil salvo

        Raises:
            ProfileValidationError: Se profile for inválido
            Mem0ClientError: Outros erros de comunicação
        """
        return self.client.save_profile(profile)

    def load_profile(self, user_id: str) -> ClientProfile:
        """Carrega ClientProfile do Mem0.

        Delega para Mem0ClientWrapper.load_profile().

        Args:
            user_id: ID único do cliente (client_id)

        Returns:
            ClientProfile: Perfil completo do cliente

        Raises:
            ProfileNotFoundError: Se user_id não existir no Mem0
            ProfileValidationError: Se dados estiverem corrompidos
            Mem0ClientError: Outros erros de comunicação
        """
        return self.client.load_profile(user_id)

    def update_profile(self, user_id: str, updates: dict) -> ClientProfile:
        """Atualiza ClientProfile parcialmente no Mem0.

        Delega para Mem0ClientWrapper.update_profile().

        Args:
            user_id: ID único do cliente (client_id)
            updates: Dicionário com campos a atualizar (nested dict suportado)

        Returns:
            ClientProfile: Perfil atualizado

        Raises:
            ProfileNotFoundError: Se user_id não existir
            ProfileValidationError: Se updates resultarem em profile inválido
            Mem0ClientError: Outros erros de comunicação
        """
        return self.client.update_profile(user_id, updates)

    def search_profiles(self, query: str, limit: int = 10) -> list[ClientProfile]:
        """Busca ClientProfiles usando busca semântica no Mem0.

        Delega para Mem0ClientWrapper.search_profiles().

        Args:
            query: Query de busca em linguagem natural
            limit: Número máximo de resultados (default: 10)

        Returns:
            list[ClientProfile]: Lista de perfis encontrados (ordenados por relevância)

        Raises:
            Mem0ClientError: Erros de comunicação ou API
        """
        return self.client.search_profiles(query, limit)

