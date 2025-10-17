"""
Script de teste comparativo: ThreadPoolExecutor vs AsyncIO
Mede ganho real de performance entre as duas implementacoes.

Uso:
    python tests/test_parallel_comparison.py
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from config.settings import settings
from src.agents.orchestrator import Orchestrator


@pytest.mark.skip(reason="Benchmark comparativo não faz parte da suíte unitária CI; instável em paralelo")
def test_threadpool_executor(orchestrator: Orchestrator, query: str, agent_names: list) -> dict:
    """
    Testa execucao paralela com ThreadPoolExecutor (invoke_agents).
    
    Args:
        orchestrator: Instancia do Orchestrator
        query: Pergunta para os agentes
        agent_names: Lista de agentes a executar
        
    Returns:
        Dicionario com resultados e metricas
    """
    print("\n" + "="*70)
    print("[TESTE 1] ThreadPoolExecutor (invoke_agents)")
    print("="*70)
    
    start_time = time.time()
    responses = orchestrator.invoke_agents(query, agent_names)
    total_time = time.time() - start_time
    
    # Calcular tempo individual de cada agente
    agent_times = {r["agent_name"]: r["execution_time"] for r in responses}
    sum_individual = sum(agent_times.values())
    
    return {
        "method": "ThreadPoolExecutor",
        "total_time": total_time,
        "sum_individual": sum_individual,
        "speedup": sum_individual / total_time if total_time > 0 else 0,
        "num_agents": len(responses),
        "agent_times": agent_times
    }


@pytest.mark.skip(reason="Benchmark comparativo não faz parte da suíte unitária CI; instável em paralelo")
async def test_asyncio(orchestrator: Orchestrator, query: str, agent_names: list) -> dict:
    """
    Testa execucao paralela com AsyncIO (ainvoke_agents).
    
    Args:
        orchestrator: Instancia do Orchestrator
        query: Pergunta para os agentes
        agent_names: Lista de agentes a executar
        
    Returns:
        Dicionario com resultados e metricas
    """
    print("\n" + "="*70)
    print("[TESTE 2] AsyncIO (ainvoke_agents)")
    print("="*70)
    
    start_time = time.time()
    responses = await orchestrator.ainvoke_agents(query, agent_names)
    total_time = time.time() - start_time
    
    # Calcular tempo individual de cada agente
    agent_times = {r["agent_name"]: r["execution_time"] for r in responses}
    sum_individual = sum(agent_times.values())
    
    return {
        "method": "AsyncIO",
        "total_time": total_time,
        "sum_individual": sum_individual,
        "speedup": sum_individual / total_time if total_time > 0 else 0,
        "num_agents": len(responses),
        "agent_times": agent_times
    }


def print_comparison(result_threadpool: dict, result_asyncio: dict):
    """
    Imprime comparacao detalhada entre os dois metodos.
    
    Args:
        result_threadpool: Resultados do ThreadPoolExecutor
        result_asyncio: Resultados do AsyncIO
    """
    print("\n" + "="*70)
    print("COMPARACAO DE PERFORMANCE")
    print("="*70)
    
    # Tabela de resultados
    print(f"\n{'Metrica':<30} {'ThreadPool':<20} {'AsyncIO':<20}")
    print("-" * 70)
    
    print(f"{'Tempo Total (s)':<30} {result_threadpool['total_time']:<20.3f} {result_asyncio['total_time']:<20.3f}")
    print(f"{'Soma Individual (s)':<30} {result_threadpool['sum_individual']:<20.3f} {result_asyncio['sum_individual']:<20.3f}")
    print(f"{'Speedup':<30} {result_threadpool['speedup']:<20.2f}x {result_asyncio['speedup']:<20.2f}x")
    print(f"{'Num Agentes':<30} {result_threadpool['num_agents']:<20} {result_asyncio['num_agents']:<20}")
    
    # Calcular ganho de AsyncIO sobre ThreadPool
    if result_threadpool['total_time'] > 0:
        improvement = ((result_threadpool['total_time'] - result_asyncio['total_time']) / result_threadpool['total_time']) * 100
        time_saved = result_threadpool['total_time'] - result_asyncio['total_time']
        
        print("\n" + "="*70)
        print("GANHO DE PERFORMANCE: AsyncIO vs ThreadPoolExecutor")
        print("="*70)
        print(f"Tempo economizado: {time_saved:.3f}s")
        print(f"Melhoria percentual: {improvement:.2f}%")
        
        if improvement > 0:
            print(f"\n[OK] AsyncIO foi {improvement:.2f}% mais rapido que ThreadPoolExecutor")
        elif improvement < 0:
            print(f"\n[WARN] ThreadPoolExecutor foi {abs(improvement):.2f}% mais rapido que AsyncIO")
        else:
            print(f"\n[INFO] Performance identica entre os dois metodos")
    
    # Tempos individuais por agente
    print("\n" + "="*70)
    print("TEMPOS INDIVIDUAIS POR AGENTE")
    print("="*70)
    print(f"\n{'Agente':<30} {'ThreadPool (s)':<20} {'AsyncIO (s)':<20}")
    print("-" * 70)
    
    all_agents = set(result_threadpool['agent_times'].keys()) | set(result_asyncio['agent_times'].keys())
    for agent in sorted(all_agents):
        tp_time = result_threadpool['agent_times'].get(agent, 0)
        async_time = result_asyncio['agent_times'].get(agent, 0)
        print(f"{agent:<30} {tp_time:<20.3f} {async_time:<20.3f}")


async def main():
    """
    Funcao principal - executa testes comparativos.
    """
    print("\n" + "="*70)
    print("TESTE COMPARATIVO: ThreadPoolExecutor vs AsyncIO")
    print("="*70)
    print(f"Configuracao: MAX_WORKERS = {settings.agent_max_workers}")
    
    # Query de teste
    query = """
    Como uma organizacao pode usar o Balanced Scorecard para alinhar 
    estrategia com operacoes e melhorar performance financeira?
    """
    
    # Agentes a testar (todos os 4) - usar nomes em portugues
    agent_names = ["financeira", "cliente", "processos", "aprendizado"]
    
    # Inicializar Orchestrator
    print("\n[SETUP] Inicializando Orchestrator...")
    orchestrator = Orchestrator()
    
    # Teste 1: ThreadPoolExecutor
    result_threadpool = test_threadpool_executor(orchestrator, query, agent_names)
    
    # Pausa entre testes (evitar rate limiting)
    print("\n[WAIT] Aguardando 3s entre testes...")
    await asyncio.sleep(3)
    
    # Teste 2: AsyncIO
    result_asyncio = await test_asyncio(orchestrator, query, agent_names)
    
    # Comparacao final
    print_comparison(result_threadpool, result_asyncio)
    
    print("\n[OK] Teste comparativo concluido!")


if __name__ == "__main__":
    # Executar main async
    asyncio.run(main())

