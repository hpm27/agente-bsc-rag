"""Serviço de performance monitoring para observability do sistema.

Este serviço captura e armazena métricas de performance do BSC RAG Agent,
permitindo monitorar latência, throughput, tokens LLM, e custos.

Features:
- Captura automática de métricas via middleware FastAPI
- Armazenamento persistente no Mem0
- Agregação de estatísticas (P50, P95, Mean latency)
- Filtros por endpoint, user_id, status_code
- Cálculo de custo estimado baseado em tokens LLM

Fase: 4.8 - Performance Monitoring
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from statistics import mean, median
from collections import defaultdict

from mem0 import MemoryClient
import os

from src.memory.schemas import PerformanceMetrics

logger = logging.getLogger(__name__)


# Pricing LLM (USD por 1M tokens) - GPT-5 family (Nov 2025)
LLM_PRICING = {
    "gpt-5-2025-08-07": {"input": 2.50, "output": 10.00},
    "gpt-5-mini-2025-08-07": {"input": 0.10, "output": 0.40},
    "claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
}


class PerformanceService:
    """Serviço para gerenciar métricas de performance do sistema BSC RAG Agent.
    
    Armazena métricas no Mem0 com estrutura:
    - Memory Type: "performance_metric"
    - Metadata: endpoint, method, status_code, user_id, timestamp_unix
    - Content: "endpoint={endpoint} method={method} duration_ms={duration_ms} status={status_code}"
    
    Usage:
        service = PerformanceService()
        metric_id = service.create_metric(metric)
        metrics = service.get_metrics(endpoint="/api/v1/diagnostics", limit=100)
        stats = service.aggregate_stats(hours=24)
    """
    
    def __init__(self, mem0_client: Optional[MemoryClient] = None):
        """Inicializa PerformanceService.
        
        Args:
            mem0_client: MemoryClient do Mem0 (opcional, cria se None)
        """
        if mem0_client is None:
            api_key = os.getenv("MEM0_API_KEY")
            if not api_key:
                raise ValueError(
                    "MEM0_API_KEY não encontrada. Configure no .env ou passe mem0_client."
                )
            os.environ["MEM0_API_KEY"] = api_key
            self.client = MemoryClient()
        else:
            self.client = mem0_client
        
        logger.info("[PERFORMANCE] PerformanceService inicializado")
    
    def create_metric(self, metric: PerformanceMetrics) -> str:
        """Cria e armazena métrica de performance no Mem0.
        
        Args:
            metric: Instância de PerformanceMetrics a ser armazenada
            
        Returns:
            metric_id: ID único da métrica (metric.id)
            
        Raises:
            ValueError: Se metric for inválida
            Exception: Erros de comunicação com Mem0
            
        Example:
            >>> metric = PerformanceMetrics(
            ...     endpoint="/api/v1/diagnostics",
            ...     method="POST",
            ...     duration_ms=12345.67,
            ...     status_code=200,
            ...     tokens_in=5678,
            ...     tokens_out=2345
            ... )
            >>> metric_id = service.create_metric(metric)
            >>> print(metric_id)
            metric_20251119143045_a1b2c3d4
        """
        try:
            logger.info(
                f"[PERFORMANCE] [CREATE] Criando métrica | "
                f"endpoint={metric.endpoint} | method={metric.method} | "
                f"duration_ms={metric.duration_ms:.2f} | status={metric.status_code}"
            )
            
            # Validar metric
            if not metric.endpoint or len(metric.endpoint) < 5:
                raise ValueError("endpoint inválido (mín 5 caracteres)")
            
            if metric.duration_ms < 0:
                raise ValueError("duration_ms deve ser >= 0")
            
            if metric.status_code < 100 or metric.status_code > 599:
                raise ValueError("status_code deve estar entre 100-599")
            
            # Preparar content e metadata para Mem0
            content = (
                f"endpoint={metric.endpoint} method={metric.method} "
                f"duration_ms={metric.duration_ms:.2f} status={metric.status_code}"
            )
            
            # Metadata inclui todos campos importantes para busca
            metadata = {
                "metric_id": metric.id,
                "endpoint": metric.endpoint,
                "method": metric.method,
                "status_code": metric.status_code,
                "timestamp_unix": int(metric.timestamp.timestamp()),
                "duration_ms": metric.duration_ms,
            }
            
            # Adicionar campos opcionais se presentes
            if metric.user_id:
                metadata["user_id"] = metric.user_id
            if metric.diagnostic_id:
                metadata["diagnostic_id"] = metric.diagnostic_id
            if metric.tokens_in is not None:
                metadata["tokens_in"] = metric.tokens_in
            if metric.tokens_out is not None:
                metadata["tokens_out"] = metric.tokens_out
            if metric.model_name:
                metadata["model_name"] = metric.model_name
            if metric.error_message:
                metadata["error_message"] = metric.error_message[:200]  # Truncar para metadata
            
            # Adicionar metadata customizado
            if metric.metadata:
                for key, value in metric.metadata.items():
                    # Evitar sobrescrever metadata crítico
                    if key not in metadata:
                        metadata[f"custom_{key}"] = value
            
            # Adicionar ao Mem0
            result = self.client.add(
                messages=content,
                metadata=metadata,
                user_id="system_performance"  # User ID padrão para métricas
            )
            
            # Eventual consistency sleep (Mem0 API v2)
            time.sleep(1)
            
            logger.info(
                f"[PERFORMANCE] [CREATE] Métrica criada | metric_id={metric.id} | "
                f"mem0_id={result.get('id', 'N/A')}"
            )
            
            return metric.id
            
        except ValueError as e:
            logger.error(f"[PERFORMANCE] [CREATE] Validação falhou: {e}")
            raise
        except Exception as e:
            logger.error(f"[PERFORMANCE] [CREATE] Erro ao criar métrica: {e}", exc_info=True)
            raise
    
    def get_metrics(
        self,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        user_id: Optional[str] = None,
        status_code: Optional[int] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[PerformanceMetrics]:
        """Lista métricas de performance com filtros opcionais.
        
        Args:
            endpoint: Filtrar por endpoint específico (opcional)
            method: Filtrar por método HTTP (opcional)
            user_id: Filtrar por usuário (opcional)
            status_code: Filtrar por código HTTP (opcional)
            hours: Buscar métricas das últimas N horas (default: 24h)
            limit: Limite de resultados (default: 100, max: 1000)
            
        Returns:
            Lista de PerformanceMetrics ordenada por timestamp (mais recentes primeiro)
            
        Example:
            >>> metrics = service.get_metrics(
            ...     endpoint="/api/v1/diagnostics",
            ...     status_code=200,
            ...     hours=24,
            ...     limit=50
            ... )
            >>> print(f"Total: {len(metrics)} métricas")
            Total: 42 métricas
        """
        try:
            logger.info(
                f"[PERFORMANCE] [LIST] Listando métricas | "
                f"endpoint={endpoint} | method={method} | user_id={user_id} | "
                f"status={status_code} | hours={hours} | limit={limit}"
            )
            
            # Validar limit
            if limit < 1 or limit > 1000:
                raise ValueError("limit deve estar entre 1-1000")
            
            # Calcular timestamp mínimo (últimas N horas)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            cutoff_unix = int(cutoff_time.timestamp())
            
            # Buscar métricas no Mem0 (wildcard filters)
            filters = {"AND": [{"user_id": "system_performance"}]}
            
            try:
                results = self.client.get_all(
                    filters=filters,
                    page=1,
                    page_size=limit
                )
            except Exception as e:
                logger.warning(f"[PERFORMANCE] [LIST] get_all falhou: {e}. Tentando search...")
                results = self.client.search(
                    query="endpoint method duration_ms status",
                    filters=filters,
                    limit=limit
                )
            
            # Parsing defensivo (Mem0 API v2 estrutura imprevisível)
            if isinstance(results, dict) and 'results' in results:
                memories_list = results['results']
            elif isinstance(results, list):
                memories_list = results
            else:
                memories_list = [results] if results else []
            
            logger.info(f"[PERFORMANCE] [LIST] Mem0 retornou {len(memories_list)} memories brutos")
            
            # Converter memories para PerformanceMetrics
            metrics = []
            for memory in memories_list:
                try:
                    metadata = memory.get("metadata", {}) if isinstance(memory, dict) else {}
                    
                    # Filtrar por timestamp (últimas N horas)
                    timestamp_unix = metadata.get("timestamp_unix", 0)
                    if timestamp_unix < cutoff_unix:
                        continue
                    
                    # Aplicar filtros opcionais
                    if endpoint and metadata.get("endpoint") != endpoint:
                        continue
                    if method and metadata.get("method") != method:
                        continue
                    if user_id and metadata.get("user_id") != user_id:
                        continue
                    if status_code and metadata.get("status_code") != status_code:
                        continue
                    
                    # Reconstruir PerformanceMetrics
                    metric = PerformanceMetrics(
                        id=metadata.get("metric_id", f"metric_unknown_{timestamp_unix}"),
                        timestamp=datetime.fromtimestamp(timestamp_unix, tz=timezone.utc),
                        endpoint=metadata.get("endpoint", "/unknown"),
                        method=metadata.get("method", "GET"),
                        duration_ms=metadata.get("duration_ms", 0.0),
                        status_code=metadata.get("status_code", 200),
                        user_id=metadata.get("user_id"),
                        diagnostic_id=metadata.get("diagnostic_id"),
                        tokens_in=metadata.get("tokens_in"),
                        tokens_out=metadata.get("tokens_out"),
                        model_name=metadata.get("model_name"),
                        error_message=metadata.get("error_message"),
                        metadata={
                            k.replace("custom_", ""): v
                            for k, v in metadata.items()
                            if k.startswith("custom_")
                        }
                    )
                    
                    metrics.append(metric)
                    
                except Exception as e:
                    logger.warning(f"[PERFORMANCE] [LIST] Erro ao converter memory: {e}")
                    continue
            
            # Ordenar por timestamp (mais recentes primeiro)
            metrics.sort(key=lambda m: m.timestamp, reverse=True)
            
            logger.info(f"[PERFORMANCE] [LIST] Retornando {len(metrics)} métricas filtradas")
            
            return metrics
            
        except ValueError as e:
            logger.error(f"[PERFORMANCE] [LIST] Validação falhou: {e}")
            raise
        except Exception as e:
            logger.error(f"[PERFORMANCE] [LIST] Erro ao listar métricas: {e}", exc_info=True)
            raise
    
    def aggregate_stats(
        self,
        endpoint: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Agrega estatísticas de performance das métricas.
        
        Calcula:
        - Latência P50, P95, Mean
        - Total de requests
        - Taxa de erro (status >= 400)
        - Throughput (requests/min)
        - Tokens consumidos (in/out por modelo)
        - Custo estimado (baseado em pricing LLM)
        
        Args:
            endpoint: Filtrar por endpoint específico (opcional, None = todos)
            hours: Agregar métricas das últimas N horas (default: 24h)
            
        Returns:
            Dict com estatísticas agregadas
            
        Example:
            >>> stats = service.aggregate_stats(hours=24)
            >>> print(f"P95 latency: {stats['latency']['p95_ms']:.2f}ms")
            P95 latency: 15234.56ms
        """
        try:
            logger.info(
                f"[PERFORMANCE] [STATS] Agregando estatísticas | "
                f"endpoint={endpoint or 'ALL'} | hours={hours}"
            )
            
            # Buscar métricas
            metrics = self.get_metrics(endpoint=endpoint, hours=hours, limit=1000)
            
            if not metrics:
                logger.warning("[PERFORMANCE] [STATS] Nenhuma métrica encontrada")
                return {
                    "total_requests": 0,
                    "error_rate": 0.0,
                    "throughput_per_min": 0.0,
                    "latency": {},
                    "tokens": {},
                    "cost_usd": 0.0,
                    "period_hours": hours
                }
            
            # Calcular latências (P50, P95, Mean)
            durations = [m.duration_ms for m in metrics]
            durations_sorted = sorted(durations)
            
            p50_index = int(len(durations_sorted) * 0.50)
            p95_index = int(len(durations_sorted) * 0.95)
            
            latency_stats = {
                "p50_ms": durations_sorted[p50_index] if durations_sorted else 0.0,
                "p95_ms": durations_sorted[p95_index] if durations_sorted else 0.0,
                "mean_ms": mean(durations) if durations else 0.0,
                "min_ms": min(durations) if durations else 0.0,
                "max_ms": max(durations) if durations else 0.0
            }
            
            # Calcular taxa de erro
            total_requests = len(metrics)
            error_requests = len([m for m in metrics if m.status_code >= 400])
            error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0.0
            
            # Calcular throughput (requests/min)
            throughput_per_min = total_requests / (hours * 60) if hours > 0 else 0.0
            
            # Agregar tokens por modelo
            tokens_by_model = defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0})
            total_cost_usd = 0.0
            
            for metric in metrics:
                if metric.model_name and (metric.tokens_in or metric.tokens_out):
                    model = metric.model_name
                    tokens_by_model[model]["tokens_in"] += metric.tokens_in or 0
                    tokens_by_model[model]["tokens_out"] += metric.tokens_out or 0
                    
                    # Calcular custo se pricing disponível
                    if model in LLM_PRICING:
                        pricing = LLM_PRICING[model]
                        cost_in = (metric.tokens_in or 0) * pricing["input"] / 1_000_000
                        cost_out = (metric.tokens_out or 0) * pricing["output"] / 1_000_000
                        total_cost_usd += cost_in + cost_out
            
            # Converter defaultdict para dict normal
            tokens_stats = {
                model: {
                    "tokens_in": data["tokens_in"],
                    "tokens_out": data["tokens_out"],
                    "total_tokens": data["tokens_in"] + data["tokens_out"]
                }
                for model, data in tokens_by_model.items()
            }
            
            stats = {
                "total_requests": total_requests,
                "error_requests": error_requests,
                "error_rate": round(error_rate, 2),
                "throughput_per_min": round(throughput_per_min, 2),
                "latency": {k: round(v, 2) for k, v in latency_stats.items()},
                "tokens": tokens_stats,
                "cost_usd": round(total_cost_usd, 4),
                "period_hours": hours,
                "endpoint": endpoint or "ALL"
            }
            
            logger.info(
                f"[PERFORMANCE] [STATS] Estatísticas calculadas | "
                f"total={stats['total_requests']} | error_rate={stats['error_rate']}% | "
                f"p95={stats['latency']['p95_ms']:.2f}ms | cost=${stats['cost_usd']:.4f}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"[PERFORMANCE] [STATS] Erro ao agregar estatísticas: {e}", exc_info=True)
            raise


def get_performance_service(mem0_client: Optional[MemoryClient] = None) -> PerformanceService:
    """Factory function para PerformanceService (singleton pattern).
    
    Args:
        mem0_client: MemoryClient opcional (útil para testes)
        
    Returns:
        PerformanceService instance
    """
    return PerformanceService(mem0_client=mem0_client)

