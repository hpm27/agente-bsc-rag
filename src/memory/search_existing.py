"""Helper para buscar profiles existentes antes de criar duplicatas.

SPRINT 4 - Solucao para problema de duplicatas:
Antes de criar novo profile, buscar se empresa ja existe no Mem0.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import logging

logger = logging.getLogger(__name__)


def search_existing_company(company_name: str) -> str | None:
    """Busca se ja existe profile para empresa no Mem0.

    Usa search() API para buscar memorias que mencionam o nome da empresa.
    Se encontrar, retorna user_id existente para REUSAR.
    Se nao encontrar, retorna None (criar novo profile).

    Args:
        company_name: Nome da empresa para buscar (ex: "Engelar", "TechCorp")

    Returns:
        user_id existente se encontrado, None se nao existe

    Example:
        >>> # Antes de criar profile novo
        >>> existing_user_id = search_existing_company("Engelar")
        >>> if existing_user_id:
        ...     print(f"[OK] Empresa ja existe! Reusar user_id: {existing_user_id}")
        ...     user_id = existing_user_id
        ... else:
        ...     print("[INFO] Empresa nova. Criar novo profile")
        ...     user_id = str(uuid4())
    """
    try:
        from config.settings import settings
        from mem0 import MemoryClient

        client = MemoryClient(api_key=settings.mem0_api_key)

        # Buscar memorias que mencionam o nome da empresa
        # search() aceita user_id como parametro direto (diferente de get_all)
        # Mas aqui queremos buscar SEM user_id especifico (busca global)

        # WORKAROUND: Como search() sem entity retorna erro, buscar em chunks
        # Buscar em users() primeiro, depois search por empresa em cada user

        logger.info(f"[SEARCH] Buscando empresa existente: '{company_name}'")

        # Listar todos users
        users_response = client.users()

        # Parsear estrutura
        if isinstance(users_response, dict) and "results" in users_response:
            users = users_response["results"]
        elif isinstance(users_response, list):
            users = users_response
        else:
            logger.warning(f"[WARN] Estrutura inesperada users(): {type(users_response)}")
            return None

        # Para cada user, buscar se metadata.company_name bate
        for user in users:
            user_id = user.get("name") if isinstance(user, dict) else getattr(user, "name", None)

            if not user_id:
                continue

            try:
                # Buscar 1 memoria deste user para verificar metadata.company_name
                memories = client.search(
                    query="empresa",  # Query generica
                    user_id=user_id,
                    limit=1,  # Apenas 1 para verificar metadata
                )

                # Parsear resposta
                if isinstance(memories, dict) and "results" in memories:
                    mems = memories["results"]
                elif isinstance(memories, list):
                    mems = memories
                else:
                    mems = []

                # Verificar metadata.company_name (SPRINT 4: salvo no metadata)
                if mems and len(mems) > 0:
                    first_mem = mems[0]
                    if isinstance(first_mem, dict) and "metadata" in first_mem:
                        meta = first_mem["metadata"]
                        if isinstance(meta, dict):
                            stored_company = meta.get("company_name", "")

                            # Match case-insensitive
                            if stored_company.lower() == company_name.lower():
                                logger.info(
                                    f"[OK] Empresa '{company_name}' JA EXISTE! "
                                    f"user_id: {user_id[:8]}..."
                                )
                                return user_id  # REUSAR este user_id!

            except Exception as e:
                logger.debug(f"[SKIP] Erro ao buscar em user {user_id[:8]}...: {e}")
                continue

        # Se chegou aqui, empresa nao existe
        logger.info(f"[INFO] Empresa '{company_name}' nao encontrada no Mem0. Criar novo profile")
        return None

    except Exception as e:
        logger.error(f"[ERRO] Falha ao buscar empresa existente: {e}", exc_info=True)
        return None  # Em caso de erro, criar novo (safe default)
