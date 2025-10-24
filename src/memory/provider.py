"""Protocol para provedores de memória persistente.

Este módulo define a interface abstrata (Protocol) que todos memory providers
devem implementar, permitindo substituição transparente entre Mem0, Supabase,
Redis, ou qualquer outro backend de memória.
"""

from typing import Protocol, runtime_checkable

from src.memory.schemas import ClientProfile


@runtime_checkable
class MemoryProvider(Protocol):
    """Interface abstrata para provedores de memória persistente.

    Define os métodos obrigatórios que qualquer memory provider deve implementar
    para armazenar, recuperar, atualizar e buscar perfis de clientes.

    Este é um Protocol (PEP 544), permitindo duck typing estrutural ao invés de
    herança explícita. Qualquer classe que implemente esses métodos é considerada
    um MemoryProvider válido.

    Examples:
        >>> from src.memory.factory import MemoryFactory
        >>> provider = MemoryFactory.get_provider("mem0")
        >>> isinstance(provider, MemoryProvider)
        True
    """

    def save_profile(self, profile: ClientProfile) -> str:
        """Salva ClientProfile no backend de memória.

        Args:
            profile: ClientProfile completo a ser persistido

        Returns:
            str: client_id do perfil salvo (confirmação)

        Raises:
            Exception: Erros específicos do provider (e.g. ProfileValidationError)
        """
        ...

    def load_profile(self, user_id: str) -> ClientProfile:
        """Carrega ClientProfile do backend de memória.

        Args:
            user_id: ID único do cliente (client_id)

        Returns:
            ClientProfile: Perfil completo recuperado

        Raises:
            ProfileNotFoundError: Se user_id não existir
            Exception: Outros erros específicos do provider
        """
        ...

    def update_profile(self, user_id: str, updates: dict) -> ClientProfile:
        """Atualiza ClientProfile parcialmente no backend de memória.

        Args:
            user_id: ID único do cliente
            updates: Dicionário com campos a atualizar (nested dict suportado)

        Returns:
            ClientProfile: Perfil atualizado

        Raises:
            ProfileNotFoundError: Se user_id não existir
            Exception: Outros erros específicos do provider
        """
        ...

    def search_profiles(self, query: str, limit: int = 10) -> list[ClientProfile]:
        """Busca ClientProfiles usando busca semântica.

        Args:
            query: Query de busca em linguagem natural
            limit: Número máximo de resultados (default: 10)

        Returns:
            list[ClientProfile]: Lista de perfis encontrados (ordenados por relevância)

        Raises:
            Exception: Erros específicos do provider
        """
        ...

