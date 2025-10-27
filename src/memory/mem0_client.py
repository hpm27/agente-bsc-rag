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

            # [CORREÇÃO] Sanitizar metadata para ficar < 2000 chars (limite Mem0)
            # BEST PRACTICE: Metadata deve conter apenas campos searchable/filterable
            # Profile completo já está armazenado em messages, não precisa duplicar
            import json as _json
            
            def _truncate(text: str, max_len: int) -> str:
                """Trunca texto garantindo que não ultrapasse max_len."""
                return text if len(text) <= max_len else text[: max_len - 3] + "..."
            
            def _calculate_metadata_size(metadata: dict) -> int:
                """Calcula tamanho real do metadata JSON serializado."""
                return len(_json.dumps(metadata, separators=(",", ":"), ensure_ascii=False))
            
            # Campos essenciais para busca/filtro (não dados completos)
            company_name = _truncate(profile.company.name or "", 150)
            sector = _truncate(profile.company.sector or "", 150)
            industry = _truncate(profile.company.industry or "", 150)
            phase = _truncate(profile.engagement.current_phase or "", 80)
            
            # ESTRATÉGIA 1: Tentar metadata sem profile_data (recomendado Mem0)
            # Profile completo já está em messages, metadata apenas para busca
            metadata_compact = {
                "company_name": company_name,
                "sector": sector,
                "industry": industry,
                "phase": phase,
            }
            
            metadata_size = _calculate_metadata_size(metadata_compact)
            
            # ESTRATÉGIA 2: Se ainda > 2000 (improvável), truncar fields progressivamente
            if metadata_size > 2000:
                logger.warning(
                    "[WARN] Metadata essencial > 2000 chars (%d). Truncando fields...",
                    metadata_size
                )
                # Reduzir fields pela metade
                company_name = _truncate(company_name, 75)
                sector = _truncate(sector, 75)
                industry = _truncate(industry, 75)
                phase = _truncate(phase, 40)
                
                metadata_compact = {
                    "company_name": company_name,
                    "sector": sector,
                    "industry": industry,
                    "phase": phase,
                }
                
                metadata_size = _calculate_metadata_size(metadata_compact)
                
                if metadata_size > 2000:
                    # Último recurso: apenas company e sector
                    metadata_compact = {
                        "company_name": _truncate(company_name, 100),
                        "sector": _truncate(sector, 100),
                    }
                    metadata_size = _calculate_metadata_size(metadata_compact)
                    logger.warning(
                        "[WARN] Metadata reduzido para campos mínimos (size: %d)",
                        metadata_size
                    )
            
            logger.debug(
                "[OK] Metadata sanitizado: %d chars (limit: 2000)",
                metadata_size
            )

            # Agora salva no Mem0 usando user_id como chave
            self.client.add(
                messages=messages,
                user_id=profile.client_id,
                metadata=metadata_compact
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
                # API v2 requer filters estruturados (docs.mem0.ai/platform/features/v2-memory-filters)
                filters = {"AND": [{"user_id": user_id}]}
                memories = self.client.get_all(filters=filters, page=1, page_size=50)
            except TypeError:
                # Fallback: versões antigas do client ou sem paginação
                filters = {"AND": [{"user_id": user_id}]}
                memories = self.client.get_all(filters=filters)

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
                # Buscar memórias com benchmark_report_data (API v2 filters)
                filters = {"AND": [{"user_id": client_id}]}
                all_memories = self.client.get_all(filters=filters)
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
            # Busca todas memórias do client_id (API v2 filters)
            filters = {"AND": [{"user_id": client_id}]}
            memories = self.client.get_all(filters=filters)
            
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def save_tool_output(self, client_id: str, tool_output: Any) -> str:
        """Salva ToolOutput de ferramenta consultiva no Mem0.
        
        Persiste o output de qualquer ferramenta consultiva (SWOT, Five Whys,
        Issue Tree, KPI, Strategic Objectives, Benchmarking) no Mem0 Platform.
        
        Usa metadata.tool_output_data para armazenar dados estruturados e messages
        contextuais para busca semântica futura.
        
        Args:
            client_id: ID do cliente
            tool_output: ToolOutput a ser salvo (já serializado)
        
        Returns:
            str: client_id do output salvo
        
        Raises:
            Mem0ClientError: Erros de comunicação ou API
        
        Example:
            >>> client = Mem0ClientWrapper()
            >>> tool_output = ToolOutput(
            ...     tool_name="SWOT",
            ...     tool_output_data=swot_analysis.model_dump(),
            ...     client_context="TechCorp - empresa de tecnologia"
            ... )
            >>> client.save_tool_output("cliente_123", tool_output)
        """
        try:
            # Valida que tool_output é ToolOutput válido
            if not hasattr(tool_output, 'tool_name') or not hasattr(tool_output, 'tool_output_data'):
                raise ValueError("tool_output deve ser uma instância de ToolOutput")
            
            # Serializa dados
            tool_data = tool_output.tool_output_data if not isinstance(tool_output.tool_output_data, dict) else tool_output.tool_output_data
            client_context = tool_output.client_context or ""
            
            # Cria mensagens contextuais para Mem0
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Realizei análise com ferramenta consultiva '{tool_output.tool_name}'. "
                        f"{'Contexto: ' + client_context + '. ' if client_context else ''}"
                        f"Results serializados para uso futuro."
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Entendido! Registrei output da ferramenta '{tool_output.tool_name}' "
                        f"com dados estruturados. Vou guardar para análises futuras e referência."
                    )
                }
            ]
            
            # Deleta outputs antigos da mesma ferramenta (garante 1 output atualizado)
            try:
                filters = {"AND": [{"user_id": client_id}]}
                all_memories = self.client.get_all(filters=filters)
                for memory in (all_memories if isinstance(all_memories, list) else [all_memories]):
                    try:
                        if isinstance(memory, dict) and 'metadata' in memory:
                            metadata = memory['metadata']
                        elif hasattr(memory, 'metadata'):
                            metadata = memory.metadata
                        else:
                            continue
                        
                        # Verifica se é output desta ferramenta
                        if 'tool_output_data' in metadata:
                            tool_name_in_memory = metadata.get('tool_name', '')
                            if tool_name_in_memory == tool_output.tool_name:
                                # Encontrou output antigo desta ferramenta, deletar
                                memory_id = memory.get('id') if isinstance(memory, dict) else getattr(memory, 'id', None)
                                if memory_id:
                                    self.client.delete(memory_id=memory_id)
                                    logger.debug(
                                        "[CLEANUP] Tool output antigo deletado (client_id=%r, tool=%r)",
                                        client_id,
                                        tool_output.tool_name
                                    )
                    except Exception as e:
                        logger.debug(
                            "[CLEANUP] Erro ao processar memória (ignorando): %s",
                            e
                        )
                        continue
            except Exception as delete_error:
                logger.debug(
                    "[CLEANUP] Nenhum tool output para deletar (client_id=%r, tool=%r): %s",
                    client_id,
                    tool_output.tool_name,
                    delete_error
                )
            
            # Salva novo tool output
            self.client.add(
                messages=messages,
                user_id=client_id,
                metadata={
                    "tool_output_data": tool_data,
                    "tool_name": tool_output.tool_name,
                    "report_type": f"tool_output_{tool_output.tool_name.lower()}",
                    "created_at": tool_output.created_at.isoformat() if hasattr(tool_output.created_at, 'isoformat') else str(tool_output.created_at)
                }
            )
            
            logger.info(
                "[OK] Tool output salvo para client_id=%r (tool=%r)",
                client_id,
                tool_output.tool_name
            )
            
            return client_id
        
        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao salvar tool output: %s", e)
            raise
        except Exception as e:
            logger.error("[ERRO] Falha ao salvar tool output: %s", e)
            raise Mem0ClientError(f"Erro ao salvar tool output: {e!s}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def get_tool_output(self, client_id: str, tool_name: str) -> Any | None:
        """Carrega ToolOutput específico do Mem0.
        
        Recupera o output de uma ferramenta consultiva específica do Mem0 Platform.
        
        Args:
            client_id: ID do cliente
            tool_name: Nome da ferramenta (SWOT, FIVE_WHYS, ISSUE_TREE, etc)
        
        Returns:
            dict com dados do ToolOutput, ou None se não encontrado
        
        Raises:
            Mem0ClientError: Erros de comunicação ou API
        
        Example:
            >>> client = Mem0ClientWrapper()
            >>> swot_data = client.get_tool_output("cliente_123", "SWOT")
            >>> if swot_data:
            ...     from src.memory.schemas import ToolOutput
            ...     tool_output = ToolOutput(**swot_data)
        """
        try:
            # WORKAROUND: Usar filtro mínimo obrigatório da API v2 (issue #3284)
            # A API v2 exige filtros, mas os filtros de metadata não funcionam corretamente
            # Usamos filtro básico por user_id e filtramos manualmente depois
            filters = {"AND": [{"user_id": client_id}]}
            memories = self.client.get_all(filters=filters)
            
            # Mem0 retorna {'results': [...]} ao invés de lista direta
            if isinstance(memories, dict) and 'results' in memories:
                memories_list = memories['results']
            elif isinstance(memories, list):
                memories_list = memories
            else:
                memories_list = [memories] if memories else []
            
            if not memories_list:
                logger.debug("[INFO] Nenhuma memória encontrada para client_id=%r", client_id)
                return None
            
            # Procura memória com tool_output_data e tool_name correspondente
            for memory in memories_list:
                try:
                    if isinstance(memory, dict) and 'metadata' in memory:
                        metadata = memory['metadata']
                    elif hasattr(memory, 'metadata'):
                        metadata = memory.metadata
                    else:
                        continue
                    
                    # Verifica se é output da ferramenta solicitada
                    if 'tool_output_data' in metadata and metadata.get('tool_name') == tool_name:
                        output_data = metadata['tool_output_data']
                        logger.info(
                            "[OK] Tool output carregado para client_id=%r (tool=%r)",
                            client_id,
                            tool_name
                        )
                        return output_data
                
                except Exception as e:
                    logger.warning(
                        "[WARN] Erro ao processar memória (ignorando): %s",
                        e
                    )
                    continue
            
            # Nenhum output encontrado
            logger.debug(
                "[INFO] Nenhum tool output encontrado para client_id=%r (tool=%r)",
                client_id,
                tool_name
            )
            return None
        
        except (ConnectionError, TimeoutError) as e:
            logger.warning("[RETRY] Falha de rede ao carregar tool output: %s", e)
            raise
        except Exception as e:
            logger.error("[ERRO] Falha ao carregar tool output: %s", e)
            raise Mem0ClientError(f"Erro ao carregar tool output: {e!s}") from e

