"""Cliente wrapper para Mem0 Platform API.

Este módulo encapsula a comunicação com a API Mem0 para operações
de persistência de ClientProfile, incluindo serialização, deserialização,
error handling robusto e retry logic.
"""

import logging
import os
import time
from typing import Any

from mem0 import MemoryClient
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.memory.exceptions import (
    Mem0ClientError,
    ProfileNotFoundError,
    ProfileValidationError,
)
from src.memory.schemas import ClientProfile

logger = logging.getLogger(__name__)


class Mem0ClientWrapper:
    """Wrapper para operações de ClientProfile no Mem0 Platform.

    Encapsula toda comunicação com a API Mem0, incluindo serialização,
    deserialização, error handling e retry logic.

    Attributes:
        client: Cliente Mem0 autenticado

    Examples:
        >>> mem0_client = Mem0ClientWrapper(api_key="your_api_key")
        >>> profile = ClientProfile(...)
        >>> mem0_client.save_profile(profile)
        >>> loaded = mem0_client.load_profile(profile.client_id)
    """

    def __init__(self, api_key: str | None = None):
        """Inicializa cliente Mem0.

        Args:
            api_key: Chave API do Mem0 Platform. Se None, busca de MEM0_API_KEY env var.

        Raises:
            Mem0ClientError: Se API key não for encontrada ou inválida
        """
        self.api_key = api_key or os.getenv("MEM0_API_KEY")

        if not self.api_key:
            raise Mem0ClientError(
                "API key do Mem0 não encontrada. "
                "Configure MEM0_API_KEY no .env ou passe como parâmetro."
            )

        try:
            # Configura API key no environment para o MemoryClient
            os.environ["MEM0_API_KEY"] = self.api_key
            self.client = MemoryClient()
            logger.info("[OK] Mem0 Client inicializado com sucesso")
        except Exception as e:
            raise Mem0ClientError(f"Falha ao inicializar Mem0 Client: {e!s}") from e

    def _serialize_profile(self, profile: ClientProfile) -> dict:
        """Serializa ClientProfile para formato Mem0.

        Args:
            profile: ClientProfile a ser serializado

        Returns:
            dict: Dados serializados prontos para Mem0
        """
        try:
            data = profile.to_mem0()
            logger.debug(
                "[OK] Profile %r serializado (%d campos)", profile.client_id, len(data)
            )
            return data
        except Exception as e:
            raise ProfileValidationError(profile.client_id, e) from e

    def _deserialize_profile(self, user_id: str, data: dict) -> ClientProfile:
        """Deserializa dados Mem0 para ClientProfile.

        Args:
            user_id: ID do usuário (para error messages)
            data: Dados recuperados do Mem0

        Returns:
            ClientProfile: Instância validada

        Raises:
            ProfileValidationError: Se dados não forem válidos
        """
        try:
            # Pré-validações mínimas para evitar aceitar dados corrompidos
            if not isinstance(data, dict):
                raise ProfileValidationError(user_id, ValueError("profile_data inválido: esperado dict"))
            company = data.get('company')
            if not isinstance(company, dict):
                raise ProfileValidationError(user_id, ValueError("profile_data.company ausente ou inválido"))
            if not company.get('name'):
                raise ProfileValidationError(user_id, ValueError("company.name ausente ou vazio"))

            profile = ClientProfile.from_mem0(data)
            logger.debug("[OK] Profile %r deserializado com sucesso", user_id)
            return profile
        except ProfileValidationError:
            raise
        except ValidationError as e:
            raise ProfileValidationError(user_id, e) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def save_profile(self, profile: ClientProfile) -> str:
        """Salva ClientProfile no Mem0.

        Serializa e persiste o perfil completo do cliente no Mem0 Platform.
        Usa retry logic para falhas transientes de rede (3 tentativas).

        Args:
            profile: ClientProfile a ser salvo

        Returns:
            str: client_id do perfil salvo

        Raises:
            ProfileValidationError: Se profile for inválido
            Mem0ClientError: Outros erros de comunicação

        Examples:
            >>> client = Mem0ClientWrapper()
            >>> profile = ClientProfile(...)
            >>> client_id = client.save_profile(profile)
            >>> print(f"Profile salvo: {client_id}")
        """
        try:
            # Serializa profile
            data = self._serialize_profile(profile)

            # [CORREÇÃO] Criar mensagens mais "memorable" para Mem0
            # O Extraction Filter do Mem0 rejeita informações genéricas/abstratas
            # Solução: Tornar mensagens contextuais, pessoais e específicas

            # Construir contexto rico com detalhes pessoais do cliente
            challenges_text = ", ".join(profile.context.current_challenges) if profile.context.current_challenges else "ainda não identificados"
            objectives_text = ", ".join(profile.context.strategic_objectives) if profile.context.strategic_objectives else "em definição"

            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Minha empresa é {profile.company.name}, "
                        f"atuamos no setor de {profile.company.sector} "
                        f"na indústria {profile.company.industry}. "
                        f"Somos uma empresa de porte {profile.company.size}. "
                        f"Nossos principais desafios são: {challenges_text}. "
                        f"Nossos objetivos estratégicos: {objectives_text}. "
                        f"Estamos na fase {profile.engagement.current_phase} do processo de consultoria BSC."
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Entendido! Registrei que {profile.company.name} é do setor {profile.company.sector}, "
                        f"porte {profile.company.size}, com foco em: {challenges_text}. "
                        f"Vou lembrar disso para nossas próximas interações na fase {profile.engagement.current_phase}."
                    )
                }
            ]

            # [CORREÇÃO] Deletar todas as memórias antigas ANTES de adicionar
            # Isso garante que sempre há apenas 1 memória por user_id
            # Solução para o problema: client.add() sempre CRIA nova memória
            try:
                self.client.delete_all(user_id=profile.client_id)

                # ⏱️ CRÍTICO: Aguardar delete_all completar (eventual consistency)
                # Sem isso, add pode criar memória ANTES de delete processar,
                # causando condição de corrida onde delete apaga a nova memória!
                time.sleep(1)

                logger.debug(
                    "[CLEANUP] Memórias antigas deletadas para client_id=%r (sleep 1s)",
                    profile.client_id
                )

            except Exception as delete_error:
                # Se delete falhar (ex: nenhuma memória existe), continuar
                logger.debug(
                    "[CLEANUP] Nenhuma memória para deletar (client_id=%r): %s",
                    profile.client_id,
                    delete_error
                )

            # Agora salva no Mem0 usando user_id como chave
            self.client.add(
                messages=messages,
                user_id=profile.client_id,
                metadata={
                    "profile_data": data,
                    "company_name": profile.company.name,
                    "sector": profile.company.sector,
                    "phase": profile.engagement.current_phase,
                }
            )

            logger.info(
                "[OK] Profile salvo para client_id=%r (empresa: %s)",
                profile.client_id,
                profile.company.name,
            )

            return profile.client_id

        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao salvar profile: %s", e)
            raise  # Retry automático via decorator
        except ProfileValidationError:
            # Propaga erro de validação de perfil conforme esperado pelos testes
            raise
        except ValidationError as e:
            raise ProfileValidationError(profile.client_id, e) from e
        except Exception as e:
            logger.error("[ERRO] Falha ao salvar profile: %s", e)
            raise Mem0ClientError(f"Erro ao salvar profile: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def load_profile(self, user_id: str) -> ClientProfile:
        """Carrega ClientProfile do Mem0.

        Recupera e deserializa o perfil completo do cliente do Mem0 Platform.
        Usa retry logic para falhas transientes de rede (3 tentativas).

        Args:
            user_id: ID único do cliente (client_id)

        Returns:
            ClientProfile: Perfil completo do cliente

        Raises:
            ProfileNotFoundError: Se user_id não existir no Mem0
            ProfileValidationError: Se dados estiverem corrompidos
            Mem0ClientError: Outros erros de comunicação

        Examples:
            >>> client = Mem0ClientWrapper()
            >>> profile = client.load_profile("cliente_123")
            >>> print(f"Empresa: {profile.company.name}")
        """
        try:
            # Busca memórias do user_id com paginação defensiva
            memories = None
            try:
                # Alguns backends do Mem0 exigem paginação explícita quando sem filtros adicionais
                memories = self.client.get_all(user_id=user_id, page=1, page_size=50)
            except TypeError:
                # Versões antigas do client não aceitam page/page_size
                memories = self.client.get_all(user_id=user_id)

            if not memories:
                raise ProfileNotFoundError(user_id)

            # [CORREÇÃO] Verificar se há múltiplas memórias (não deveria acontecer)
            # Com save_profile() usando delete_all + add, deve haver APENAS 1 memória
            if isinstance(memories, list) and len(memories) > 1:
                logger.warning(
                    "[WARN] Múltiplas memórias encontradas para user_id=%r (total: %d). "
                    "Usando a primeira. Considere investigar.",
                    user_id,
                    len(memories)
                )

            # Pegar a primeira (e única esperada) memória
            latest_memory = memories[0] if isinstance(memories, list) else memories

            # Tenta extrair do metadata
            if hasattr(latest_memory, 'metadata') and 'profile_data' in latest_memory.metadata:
                profile_data = latest_memory.metadata['profile_data']
            elif isinstance(latest_memory, dict) and 'metadata' in latest_memory:
                profile_data = latest_memory['metadata'].get('profile_data')
            else:
                raise ProfileNotFoundError(user_id)

            # Deserializa
            profile = self._deserialize_profile(user_id, profile_data)

            logger.info(
                "[OK] Profile carregado para user_id=%r (empresa: %s)",
                user_id,
                profile.company.name,
            )

            return profile

        except ProfileNotFoundError:
            raise  # Re-raise sem log (já é esperado)
        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao carregar profile: %s", e)
            raise  # Retry automático via decorator
        except ValidationError as e:
            raise ProfileValidationError(user_id, e) from e
        except Exception as e:
            logger.error("[ERRO] Falha ao carregar profile: %s", e)
            raise Mem0ClientError(f"Erro ao carregar profile: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def update_profile(
        self,
        user_id: str,
        updates: dict[str, Any]
    ) -> ClientProfile:
        """Atualiza ClientProfile parcialmente no Mem0.

        Carrega o perfil existente, aplica updates parciais, e salva novamente.
        Suporta updates em campos específicos sem sobrescrever o perfil completo.
        Usa retry logic para falhas transientes de rede (3 tentativas).

        Args:
            user_id: ID único do cliente (client_id)
            updates: Dicionário com campos a atualizar (nested dict suportado)

        Returns:
            ClientProfile: Perfil atualizado

        Raises:
            ProfileNotFoundError: Se user_id não existir
            ProfileValidationError: Se updates resultarem em profile inválido
            Mem0ClientError: Outros erros de comunicação

        Examples:
            >>> client = Mem0ClientWrapper()
            >>> updated = client.update_profile(
            ...     "cliente_123",
            ...     {"company": {"sector": "Technology"}}
            ... )
            >>> print(f"Setor atualizado: {updated.company.sector}")
        """
        try:
            # Carrega profile existente
            profile = self.load_profile(user_id)

            # Converte para dict
            profile_dict = profile.to_mem0()

            # Aplica updates recursivamente
            self._deep_update(profile_dict, updates)

            # Reconstrói profile validado
            updated_profile = ClientProfile.from_mem0(profile_dict)

            # Salva de volta
            self.save_profile(updated_profile)

            logger.info(
                "[OK] Profile atualizado para user_id=%r (%d campos atualizados)",
                user_id,
                len(updates),
            )

            return updated_profile

        except (ProfileNotFoundError, ProfileValidationError):
            raise  # Re-raise específico
        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao atualizar profile: %s", e)
            raise  # Retry automático via decorator
        except Exception as e:
            logger.error("[ERRO] Falha ao atualizar profile: %s", e)
            raise Mem0ClientError(f"Erro ao atualizar profile: {e!s}") from e

    def _deep_update(self, base_dict: dict, updates: dict) -> None:
        """Atualiza dicionário recursivamente (in-place).

        Args:
            base_dict: Dicionário base a ser atualizado
            updates: Dicionário com atualizações
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                # Merge recursivo para dicts nested
                self._deep_update(base_dict[key], value)
            else:
                # Atualização direta para valores simples
                base_dict[key] = value

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def search_profiles(
        self,
        query: str,
        limit: int = 10
    ) -> list[ClientProfile]:
        """Busca ClientProfiles usando busca semântica no Mem0.

        Usa a capacidade de busca semântica do Mem0 para encontrar
        perfis relevantes baseados em uma query em linguagem natural.
        Usa retry logic para falhas transientes de rede (3 tentativas).

        Args:
            query: Query de busca em linguagem natural
            limit: Número máximo de resultados (default: 10)

        Returns:
            list[ClientProfile]: Lista de perfis encontrados (ordenados por relevância)

        Raises:
            Mem0ClientError: Erros de comunicação ou API

        Examples:
            >>> client = Mem0ClientWrapper()
            >>> profiles = client.search_profiles("empresas de tecnologia em São Paulo")
            >>> for profile in profiles:
            ...     print(f"Empresa: {profile.company.name}")
        """
        try:
            # Busca semântica no Mem0
            # NOTA: search() sem user_id busca em todos os perfis
            results = self.client.search(
                query=query,
                limit=limit
            )

            if not results:
                logger.info("[OK] Busca retornou 0 resultados para query: %r", query)
                return []

            # Extrai profiles dos resultados
            profiles = []
            for result in results:
                try:
                    # Extrai metadata com profile_data
                    if hasattr(result, 'metadata') and 'profile_data' in result.metadata:
                        profile_data = result.metadata['profile_data']
                        user_id = result.metadata.get('user_id', 'unknown')
                    elif isinstance(result, dict):
                        profile_data = result.get('metadata', {}).get('profile_data')
                        user_id = result.get('user_id', 'unknown')
                    else:
                        continue  # Pula resultado sem profile_data

                    # Deserializa
                    profile = self._deserialize_profile(user_id, profile_data)
                    profiles.append(profile)

                except (ValidationError, ProfileValidationError) as e:
                    # Log mas não falha toda a busca por 1 resultado corrompido
                    logger.warning("[WARN] Profile corrompido ignorado na busca: %s", e)
                    continue

            logger.info(
                "[OK] Busca retornou %d profiles para query: %r",
                len(profiles),
                query,
            )

            return profiles

        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao buscar profiles: %s", e)
            raise  # Retry automático via decorator
        except Exception as e:
            logger.error("[ERRO] Falha ao buscar profiles: %s", e)
            raise Mem0ClientError(f"Erro ao buscar profiles: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def save_benchmark_report(self, client_id: str, report: Any) -> str:
        """Salva BenchmarkReport no Mem0.
        
        Persiste o relatório de benchmarking BSC no Mem0 Platform usando
        metadata.benchmark_report_data para armazenar o report serializado.
        
        Args:
            client_id: ID do cliente
            report: BenchmarkReport a ser salvo
        
        Returns:
            str: client_id do report salvo
        
        Raises:
            Mem0ClientError: Erros de comunicação ou API
        
        Example:
            >>> client = Mem0ClientWrapper()
            >>> report = BenchmarkReport(...)
            >>> client.save_benchmark_report("cliente_123", report)
        """
        try:
            # Serializa report para dict
            report_data = report.model_dump() if hasattr(report, 'model_dump') else report.dict()
            
            # Cria mensagens contextuais para Mem0
            num_comps = len(report_data.get('comparisons', []))
            performance = report_data.get('overall_performance', 'unknown')
            
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Realizei análise de benchmarking BSC com {num_comps} comparações. "
                        f"Nossa performance geral está {performance} em relação ao mercado."
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Entendido! Registrei seu benchmark report com {num_comps} comparações "
                        f"e performance {performance}. Vou guardar para análises futuras."
                    )
                }
            ]
            
            # Deleta benchmarks antigos
            try:
                # Buscar memórias com benchmark_report_data
                all_memories = self.client.get_all(user_id=client_id)
                for memory in (all_memories if isinstance(all_memories, list) else [all_memories]):
                    if isinstance(memory, dict) and 'metadata' in memory:
                        metadata = memory['metadata']
                    elif hasattr(memory, 'metadata'):
                        metadata = memory.metadata
                    else:
                        continue
                    
                    if 'benchmark_report_data' in metadata:
                        # Encontrou benchmark antigo, deletar
                        memory_id = memory.get('id') if isinstance(memory, dict) else getattr(memory, 'id', None)
                        if memory_id:
                            self.client.delete(memory_id=memory_id)
                            logger.debug(
                                "[CLEANUP] Benchmark antigo deletado (client_id=%r)",
                                client_id
                            )
            except Exception as delete_error:
                logger.debug(
                    "[CLEANUP] Nenhum benchmark para deletar (client_id=%r): %s",
                    client_id,
                    delete_error
                )
            
            # Salva novo benchmark
            self.client.add(
                messages=messages,
                user_id=client_id,
                metadata={
                    "benchmark_report_data": report_data,
                    "report_type": "benchmark_bsc",
                    "num_comparisons": num_comps,
                    "performance": performance
                }
            )
            
            logger.info(
                "[OK] Benchmark report salvo para client_id=%r (%d comparações)",
                client_id,
                num_comps
            )
            
            return client_id
        
        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao salvar benchmark: %s", e)
            raise
        except Exception as e:
            logger.error("[ERRO] Falha ao salvar benchmark report: %s", e)
            raise Mem0ClientError(f"Erro ao salvar benchmark report: {e!s}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def get_benchmark_report(self, client_id: str) -> Any | None:
        """Carrega BenchmarkReport do Mem0.
        
        Recupera o relatório de benchmarking BSC do Mem0 Platform.
        
        Args:
            client_id: ID do cliente
        
        Returns:
            dict com dados do BenchmarkReport, ou None se não encontrado
        
        Raises:
            Mem0ClientError: Erros de comunicação ou API
        
        Example:
            >>> client = Mem0ClientWrapper()
            >>> report_data = client.get_benchmark_report("cliente_123")
            >>> if report_data:
            ...     report = BenchmarkReport(**report_data)
        """
        try:
            # Busca todas memórias do client_id
            memories = self.client.get_all(user_id=client_id)
            
            if not memories:
                logger.debug("[INFO] Nenhuma memória encontrada para client_id=%r", client_id)
                return None
            
            # Procura memória com benchmark_report_data
            for memory in (memories if isinstance(memories, list) else [memories]):
                try:
                    if isinstance(memory, dict) and 'metadata' in memory:
                        metadata = memory['metadata']
                    elif hasattr(memory, 'metadata'):
                        metadata = memory.metadata
                    else:
                        continue
                    
                    if 'benchmark_report_data' in metadata:
                        report_data = metadata['benchmark_report_data']
                        logger.info(
                            "[OK] Benchmark report carregado para client_id=%r",
                            client_id
                        )
                        return report_data
                
                except Exception as e:
                    logger.warning(
                        "[WARN] Erro ao processar memória (ignorando): %s",
                        e
                    )
                    continue
            
            # Nenhum benchmark encontrado
            logger.debug(
                "[INFO] Nenhum benchmark report encontrado para client_id=%r",
                client_id
            )
            return None
        
        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao carregar benchmark: %s", e)
            raise
        except Exception as e:
            logger.error("[ERRO] Falha ao carregar benchmark report: %s", e)
            raise Mem0ClientError(f"Erro ao carregar benchmark report: {e!s}") from e

