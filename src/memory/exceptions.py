"""Exceções customizadas para o módulo de memória Mem0.

Este módulo define exceções específicas para operações de memória,
facilitando o tratamento de erros e debugging.
"""


class Mem0ClientError(Exception):
    """Erro base para todas as exceções do cliente Mem0.

    Usado para capturar erros gerais de comunicação com a API Mem0,
    problemas de configuração, ou falhas de rede.

    Examples:
        >>> raise Mem0ClientError("API key não configurada")
        >>> raise Mem0ClientError("Falha de conexão com Mem0 API")
    """


class ProfileNotFoundError(Mem0ClientError):
    """Perfil de cliente não encontrado no Mem0.

    Levantado quando tentamos carregar ou atualizar um perfil que
    não existe para o user_id especificado.

    Attributes:
        user_id: ID do usuário cujo perfil não foi encontrado

    Examples:
        >>> raise ProfileNotFoundError("cliente_123")
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"Perfil não encontrado para user_id: {user_id!r}")


class ProfileValidationError(Mem0ClientError):
    """Erro de validação ao serializar/deserializar ClientProfile.

    Levantado quando os dados recuperados do Mem0 não podem ser
    convertidos para um ClientProfile válido (schema Pydantic).

    Attributes:
        user_id: ID do usuário cujo perfil está corrompido
        original_error: Erro de validação Pydantic original

    Examples:
        >>> raise ProfileValidationError("cliente_123", validation_error)
    """

    def __init__(self, user_id: str, original_error: Exception):
        self.user_id = user_id
        self.original_error = original_error
        super().__init__(f"Erro ao validar perfil para user_id {user_id!r}: {original_error!s}")


class Mem0APIError(Mem0ClientError):
    """Erro retornado pela API Mem0.

    Levantado quando a API Mem0 retorna um erro explícito
    (rate limit, quota excedida, etc).

    Attributes:
        status_code: Código HTTP do erro (opcional)
        api_message: Mensagem da API Mem0

    Examples:
        >>> raise Mem0APIError(429, "Rate limit exceeded")
    """

    def __init__(self, status_code: int | None = None, api_message: str = ""):
        self.status_code = status_code
        self.api_message = api_message
        msg = "Erro da API Mem0"
        if status_code:
            msg += f" (HTTP {status_code})"
        if api_message:
            msg += f": {api_message}"
        super().__init__(msg)
