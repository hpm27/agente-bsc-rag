"""Serviço de métricas para armazenamento e recuperação de analytics.

Este serviço gerencia todas as métricas coletadas pelo AnalyticsMiddleware,
armazenando-as em Redis com estrutura time-series para análise histórica.

Métricas suportadas:
- Requests por endpoint (volume)
- Latência (P50, P95, P99)
- Erros (4xx, 5xx)
- Uso por cliente (API key)
- Rate limit hits
- Webhook deliveries

Fase: 4.4 - Advanced Analytics Dashboard
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import redis.asyncio as aioredis

from api.dependencies import get_redis
from config.settings import settings

logger = logging.getLogger(__name__)


class MetricsService:
    """Serviço para gerenciar métricas de analytics da API.
    
    Armazena métricas em Redis com estrutura time-series:
    - Keys: metrics:{type}:{dimension}:{timestamp}
    - Values: JSON com dados agregados
    - TTL: 7 dias (minutos), 30 dias (horas), 90 dias (dias)
    
    Usage:
        service = MetricsService()
        await service.record_request(...)
        data = await service.get_requests_by_endpoint(...)
    """
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        """Inicializa MetricsService.
        
        Args:
            redis_client: Redis client async (opcional, cria se None)
        """
        self.redis_client = redis_client
        logger.info("[METRICS] MetricsService inicializado")
    
    async def _get_redis(self) -> aioredis.Redis:
        """Retorna Redis client (lazy loading).
        
        Returns:
            Redis client async
        """
        if self.redis_client is None:
            self.redis_client = await get_redis()
        return self.redis_client
    
    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        api_key: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Registra uma requisição HTTP nas métricas.
        
        Args:
            endpoint: Caminho do endpoint (ex: /api/v1/clients)
            method: Método HTTP (GET, POST, etc)
            status_code: Status code da resposta
            latency_ms: Latência em milissegundos
            api_key: API key do cliente (opcional)
            error: Mensagem de erro se houver (opcional)
        """
        try:
            redis_client = await self._get_redis()
            now = datetime.now()
            
            # Timestamp formatado (minuto)
            timestamp_minute = now.strftime("%Y-%m-%d:%H:%M")
            timestamp_hour = now.strftime("%Y-%m-%d:%H")
            timestamp_day = now.strftime("%Y-%m-%d")
            
            # 1. Requests por endpoint (minuto)
            key_requests = f"metrics:requests:{endpoint}:{timestamp_minute}"
            await self._increment_counter(redis_client, key_requests, "count")
            
            # Contar erros (4xx, 5xx)
            if status_code >= 400:
                await self._increment_counter(redis_client, key_requests, "errors")
                if status_code >= 500:
                    await self._increment_counter(redis_client, key_requests, "5xx")
                else:
                    await self._increment_counter(redis_client, key_requests, "4xx")
            
            # 2. Latência por endpoint (minuto)
            key_latency = f"metrics:latency:{endpoint}:{timestamp_minute}"
            await self._record_latency(redis_client, key_latency, latency_ms)
            
            # 3. Uso por API key (hora)
            if api_key:
                key_consumer = f"metrics:consumer:{api_key}:{timestamp_hour}"
                await self._increment_counter(redis_client, key_consumer, "requests")
                # Adicionar endpoint à lista de endpoints únicos
                await redis_client.sadd(f"{key_consumer}:endpoints", endpoint)
            
            # 4. Total requests (dia)
            key_total = f"metrics:requests:total:{timestamp_day}"
            await self._increment_counter(redis_client, key_total, "count")
            
            # Configurar TTL (7 dias para minutos, 30 dias para horas, 90 dias para dias)
            await redis_client.expire(key_requests, 7 * 24 * 60 * 60)  # 7 dias
            await redis_client.expire(key_latency, 7 * 24 * 60 * 60)  # 7 dias
            if api_key:
                await redis_client.expire(key_consumer, 30 * 24 * 60 * 60)  # 30 dias
            await redis_client.expire(key_total, 90 * 24 * 60 * 60)  # 90 dias
            
        except Exception as e:
            # Não falhar se métricas não puderem ser registradas
            logger.warning(f"[METRICS] Erro ao registrar métrica: {e}")
    
    async def _increment_counter(
        self,
        redis_client: aioredis.Redis,
        key: str,
        field: str
    ) -> None:
        """Incrementa contador em hash Redis.
        
        Args:
            redis_client: Redis client
            key: Chave do hash
            field: Campo do hash a incrementar
        """
        # Usar hash para armazenar múltiplos contadores
        await redis_client.hincrby(key, field, 1)
    
    async def _record_latency(
        self,
        redis_client: aioredis.Redis,
        key: str,
        latency_ms: float
    ) -> None:
        """Registra latência em sorted set para cálculo de percentis.
        
        Args:
            redis_client: Redis client
            key: Chave do sorted set
            latency_ms: Latência em milissegundos
        """
        # Usar sorted set para armazenar latências (permite cálculo de percentis)
        sorted_set_key = f"{key}:samples"
        await redis_client.zadd(sorted_set_key, {str(latency_ms): latency_ms})
        
        # Manter apenas últimas 1000 amostras (evitar crescimento infinito)
        await redis_client.zremrangebyrank(sorted_set_key, 0, -1001)
        
        # Calcular e armazenar percentis
        total_samples = await redis_client.zcard(sorted_set_key)
        if total_samples > 0:
            p50_idx = int(total_samples * 0.5)
            p95_idx = int(total_samples * 0.95)
            p99_idx = int(total_samples * 0.99)
            
            p50 = await redis_client.zrange(sorted_set_key, p50_idx, p50_idx)
            p95 = await redis_client.zrange(sorted_set_key, p95_idx, p95_idx)
            p99 = await redis_client.zrange(sorted_set_key, p99_idx, p99_idx)
            
            # Armazenar percentis em hash
            latency_data = {
                "p50": float(p50[0]) if p50 else latency_ms,
                "p95": float(p95[0]) if p95 else latency_ms,
                "p99": float(p99[0]) if p99 else latency_ms,
                "samples": total_samples
            }
            
            await redis_client.setex(
                key,
                7 * 24 * 60 * 60,  # TTL 7 dias
                json.dumps(latency_data)
            )
    
    async def get_requests_by_endpoint(
        self,
        endpoint: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = "minute"
    ) -> List[Dict[str, Any]]:
        """Recupera requests agregados por endpoint e intervalo de tempo.
        
        Args:
            endpoint: Endpoint específico (None para todos)
            start_time: Início do período
            end_time: Fim do período
            interval: Intervalo de agregação (minute, hour, day)
            
        Returns:
            Lista de dicts com {timestamp, endpoint, count, errors}
        """
        redis_client = await self._get_redis()
        
        # Default: últimas 24 horas
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()
        
        results = []
        current_time = start_time
        
        while current_time <= end_time:
            if interval == "minute":
                timestamp = current_time.strftime("%Y-%m-%d:%H:%M")
                current_time += timedelta(minutes=1)
            elif interval == "hour":
                timestamp = current_time.strftime("%Y-%m-%d:%H")
                current_time += timedelta(hours=1)
            else:  # day
                timestamp = current_time.strftime("%Y-%m-%d")
                current_time += timedelta(days=1)
            
            if endpoint:
                key = f"metrics:requests:{endpoint}:{timestamp}"
            else:
                key = f"metrics:requests:total:{timestamp}"
            
            data = await redis_client.hgetall(key)
            if data:
                results.append({
                    "timestamp": timestamp,
                    "endpoint": endpoint or "total",
                    "count": int(data.get("count", 0)),
                    "errors": int(data.get("errors", 0)),
                    "4xx": int(data.get("4xx", 0)),
                    "5xx": int(data.get("5xx", 0))
                })
        
        return results
    
    async def get_latency_percentiles(
        self,
        endpoint: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Recupera percentis de latência para um endpoint.
        
        Args:
            endpoint: Endpoint específico
            start_time: Início do período
            end_time: Fim do período
            
        Returns:
            Dict com {p50, p95, p99, mean, max, samples}
        """
        redis_client = await self._get_redis()
        
        # Default: última hora
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=1)
        if end_time is None:
            end_time = datetime.now()
        
        # Buscar todas latências no período
        latencies = []
        current_time = start_time
        
        while current_time <= end_time:
            timestamp = current_time.strftime("%Y-%m-%d:%H:%M")
            key = f"metrics:latency:{endpoint}:{timestamp}"
            
            data_json = await redis_client.get(key)
            if data_json:
                data = json.loads(data_json)
                latencies.append(data)
            
            current_time += timedelta(minutes=1)
        
        if not latencies:
            return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "max": 0, "samples": 0}
        
        # Agregar percentis (média dos percentis de cada minuto)
        p50_values = [l["p50"] for l in latencies]
        p95_values = [l["p95"] for l in latencies]
        p99_values = [l["p99"] for l in latencies]
        total_samples = sum(l["samples"] for l in latencies)
        
        return {
            "p50": sum(p50_values) / len(p50_values) if p50_values else 0,
            "p95": sum(p95_values) / len(p95_values) if p95_values else 0,
            "p99": sum(p99_values) / len(p99_values) if p99_values else 0,
            "mean": sum(p50_values) / len(p50_values) if p50_values else 0,  # Aproximação
            "max": max(p99_values) if p99_values else 0,
            "samples": total_samples
        }
    
    async def get_errors_by_endpoint(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Recupera taxa de erros por endpoint.
        
        Args:
            start_time: Início do período
            end_time: Fim do período
            
        Returns:
            Lista de dicts com {endpoint, total_requests, errors, error_rate}
        """
        # Buscar todos endpoints únicos
        redis_client = await self._get_redis()
        
        # Buscar todas keys de requests
        endpoints = set()
        async for key in redis_client.scan_iter(match="metrics:requests:*:*", count=100):
            parts = key.split(":")
            if len(parts) >= 4:
                endpoint = parts[2]
                if endpoint != "total":
                    endpoints.add(endpoint)
        
        results = []
        for endpoint in endpoints:
            requests_data = await self.get_requests_by_endpoint(
                endpoint=endpoint,
                start_time=start_time,
                end_time=end_time
            )
            
            total_requests = sum(r["count"] for r in requests_data)
            total_errors = sum(r["errors"] for r in requests_data)
            
            if total_requests > 0:
                results.append({
                    "endpoint": endpoint,
                    "total_requests": total_requests,
                    "errors": total_errors,
                    "error_rate": total_errors / total_requests
                })
        
        # Ordenar por taxa de erro (maior primeiro)
        results.sort(key=lambda x: x["error_rate"], reverse=True)
        
        return results
    
    async def get_top_consumers(
        self,
        limit: int = 10,
        period: str = "24h"
    ) -> List[Dict[str, Any]]:
        """Recupera top API keys por volume de requests.
        
        Args:
            limit: Número de top consumers a retornar
            period: Período (1h, 24h, 7d, 30d)
            
        Returns:
            Lista de dicts com {api_key, requests, unique_endpoints, last_request}
        """
        redis_client = await self._get_redis()
        
        # Calcular start_time baseado no período
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(hours=24)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        else:  # 30d
            start_time = datetime.now() - timedelta(days=30)
        
        # Buscar todas keys de consumers
        consumers = {}
        async for key in redis_client.scan_iter(match="metrics:consumer:*:*", count=100):
            parts = key.split(":")
            if len(parts) >= 4:
                api_key = parts[2]
                timestamp = ":".join(parts[3:])
                
                # Verificar se timestamp está no período
                try:
                    if ":" in timestamp:
                        key_time = datetime.strptime(timestamp, "%Y-%m-%d:%H")
                    else:
                        key_time = datetime.strptime(timestamp, "%Y-%m-%d")
                    
                    if key_time >= start_time:
                        if api_key not in consumers:
                            consumers[api_key] = {
                                "api_key": api_key,
                                "requests": 0,
                                "unique_endpoints": set(),
                                "last_request": key_time
                            }
                        
                        # Buscar dados do consumer
                        data = await redis_client.hgetall(key)
                        consumers[api_key]["requests"] += int(data.get("requests", 0))
                        
                        # Buscar endpoints únicos
                        endpoints_key = f"{key}:endpoints"
                        endpoints = await redis_client.smembers(endpoints_key)
                        consumers[api_key]["unique_endpoints"].update(endpoints)
                        
                        if key_time > consumers[api_key]["last_request"]:
                            consumers[api_key]["last_request"] = key_time
                except ValueError:
                    continue
        
        # Converter para lista e ordenar por requests
        results = []
        for api_key, data in consumers.items():
            results.append({
                "api_key": api_key,
                "requests": data["requests"],
                "unique_endpoints": len(data["unique_endpoints"]),
                "last_request": data["last_request"].isoformat()
            })
        
        results.sort(key=lambda x: x["requests"], reverse=True)
        
        return results[:limit]
    
    async def get_top_endpoints(
        self,
        metric: str = "requests",
        limit: int = 10,
        period: str = "24h"
    ) -> List[Dict[str, Any]]:
        """Recupera top endpoints por métrica específica.
        
        Args:
            metric: Métrica para ordenação (requests, latency, errors)
            limit: Número de endpoints a retornar
            period: Período (1h, 24h, 7d, 30d)
            
        Returns:
            Lista de dicts com métricas por endpoint
        """
        # Calcular start_time baseado no período
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(hours=24)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        else:  # 30d
            start_time = datetime.now() - timedelta(days=30)
        
        if metric == "requests":
            requests_data = await self.get_requests_by_endpoint(
                start_time=start_time,
                end_time=datetime.now()
            )
            
            # Agregar por endpoint
            endpoints = {}
            for data in requests_data:
                endpoint = data["endpoint"]
                if endpoint not in endpoints:
                    endpoints[endpoint] = {
                        "endpoint": endpoint,
                        "requests": 0,
                        "errors": 0
                    }
                endpoints[endpoint]["requests"] += data["count"]
                endpoints[endpoint]["errors"] += data["errors"]
            
            results = list(endpoints.values())
            results.sort(key=lambda x: x["requests"], reverse=True)
            
        elif metric == "latency":
            # Buscar todos endpoints únicos
            redis_client = await self._get_redis()
            endpoints_set = set()
            async for key in redis_client.scan_iter(match="metrics:latency:*:*", count=100):
                parts = key.split(":")
                if len(parts) >= 4:
                    endpoints_set.add(parts[2])
            
            results = []
            for endpoint in endpoints_set:
                latency_data = await self.get_latency_percentiles(
                    endpoint=endpoint,
                    start_time=start_time,
                    end_time=datetime.now()
                )
                if latency_data["samples"] > 0:
                    results.append({
                        "endpoint": endpoint,
                        "p50": latency_data["p50"],
                        "p95": latency_data["p95"],
                        "p99": latency_data["p99"],
                        "mean": latency_data["mean"]
                    })
            
            results.sort(key=lambda x: x["p95"], reverse=True)
            
        else:  # errors
            results = await self.get_errors_by_endpoint(
                start_time=start_time,
                end_time=datetime.now()
            )
        
        return results[:limit]

