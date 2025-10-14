"""
Exemplo de uso do LangGraph Workflow BSC.

Este script demonstra como usar o workflow completo para processar queries BSC.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Carregar variáveis de ambiente do .env
load_dotenv(project_root / ".env")

from loguru import logger
from src.graph.workflow import get_workflow


def setup_logging():
    """Configura logging para o exemplo."""
    logger.remove()  # Remove handlers padrão
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def run_example_queries():
    """Executa queries de exemplo usando o workflow."""
    
    # Inicializar workflow
    logger.info("Inicializando BSCWorkflow...")
    workflow = get_workflow()
    logger.info("Workflow inicializado com sucesso!\n")
    
    # Queries de exemplo
    example_queries = [
        {
            "query": "O que é Balanced Scorecard?",
            "description": "Query geral sobre BSC (deve acionar todas as perspectivas)"
        },
        {
            "query": "Quais são os principais KPIs da perspectiva financeira?",
            "description": "Query específica (deve acionar apenas perspectiva financeira)"
        },
        {
            "query": "Como a satisfação do cliente impacta a lucratividade?",
            "description": "Query multi-perspectiva (cliente + financeira)"
        },
        {
            "query": "Qual a relação entre capacitação de funcionários e qualidade dos processos?",
            "description": "Query multi-perspectiva (aprendizado + processos)"
        }
    ]
    
    results = []
    
    for i, example in enumerate(example_queries, 1):
        logger.info(f"\n{'='*100}")
        logger.info(f"EXEMPLO {i}/{len(example_queries)}")
        logger.info(f"Descrição: {example['description']}")
        logger.info(f"{'='*100}\n")
        
        try:
            # Executar workflow
            result = workflow.run(
                query=example["query"],
                session_id=f"example-{i}"
            )
            
            # Exibir resultado
            print_result(result)
            
            results.append({
                "query": example["query"],
                "success": True,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"[ERRO] Falha ao processar query: {e}")
            results.append({
                "query": example["query"],
                "success": False,
                "error": str(e)
            })
    
    # Sumário final
    print_summary(results)


def print_result(result: dict):
    """
    Imprime resultado formatado.
    
    Args:
        result: Resultado do workflow
    """
    print("\n" + "-"*100)
    print("RESULTADO")
    print("-"*100)
    
    print(f"\n[INFO] Query: {result['query']}")
    
    print(f"\n[INFO] Perspectivas Consultadas ({len(result['perspectives'])}):")
    for perspective in result['perspectives']:
        print(f"  - {perspective}")
    
    print(f"\n[INFO] Agentes Executados ({len(result['agent_responses'])}):")
    for agent_resp in result['agent_responses']:
        print(f"  - {agent_resp['perspective']}: confidence={agent_resp['confidence']:.2f}")
    
    if result.get('judge_evaluation'):
        judge = result['judge_evaluation']
        print(f"\n[INFO] Avaliação do Judge:")
        print(f"  - Score: {judge['score']:.2f}")
        print(f"  - Aprovado: {'SIM' if judge['approved'] else 'NÃO'}")
        print(f"  - Feedback: {judge['feedback'][:100]}...")
    
    print(f"\n[INFO] Refinamentos: {result['refinement_iterations']}")
    
    print(f"\n[INFO] Resposta Final:")
    print("-"*100)
    print(result['final_response'])
    print("-"*100 + "\n")


def print_summary(results: list):
    """
    Imprime sumário dos resultados.
    
    Args:
        results: Lista de resultados
    """
    print("\n" + "="*100)
    print("SUMÁRIO DOS EXEMPLOS")
    print("="*100 + "\n")
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    print(f"Total de queries: {total}")
    print(f"Bem-sucedidas: {successful} ({successful/total*100:.1f}%)")
    print(f"Falhas: {failed} ({failed/total*100:.1f}%)")
    
    if failed > 0:
        print("\n[WARN] Queries que falharam:")
        for r in results:
            if not r["success"]:
                print(f"  - '{r['query']}': {r['error']}")
    
    print("\n" + "="*100 + "\n")


def run_interactive_mode():
    """Modo interativo: permite fazer queries manualmente."""
    logger.info("Modo Interativo - LangGraph Workflow BSC")
    logger.info("Digite 'sair' para encerrar\n")
    
    workflow = get_workflow()
    session_id = "interactive-session"
    query_count = 0
    
    while True:
        try:
            # Solicitar query
            query = input("\n[PERGUNTA] Sua query BSC: ").strip()
            
            if query.lower() in ["sair", "exit", "quit", "q"]:
                logger.info("Encerrando modo interativo...")
                break
            
            if not query:
                logger.warning("Query vazia. Tente novamente.")
                continue
            
            query_count += 1
            
            # Executar workflow
            logger.info(f"\n[INFO] Processando query #{query_count}...\n")
            result = workflow.run(
                query=query,
                session_id=f"{session_id}-{query_count}"
            )
            
            # Exibir resultado
            print_result(result)
            
        except KeyboardInterrupt:
            logger.info("\n\nInterrompido pelo usuário. Encerrando...")
            break
        except Exception as e:
            logger.error(f"[ERRO] {e}")


def main():
    """Função principal."""
    setup_logging()
    
    logger.info("="*100)
    logger.info("EXEMPLO DE USO - LangGraph Workflow BSC")
    logger.info("="*100 + "\n")
    
    # Verificar variáveis de ambiente
    required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "COHERE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"[AVISO] Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
        logger.warning("O workflow pode falhar sem essas configurações.\n")
    
    # Menu de opções
    print("\nEscolha uma opção:")
    print("1. Executar queries de exemplo")
    print("2. Modo interativo (fazer suas próprias perguntas)")
    print("3. Visualizar estrutura do grafo")
    print("4. Sair")
    
    choice = input("\nOpção: ").strip()
    
    if choice == "1":
        run_example_queries()
    elif choice == "2":
        run_interactive_mode()
    elif choice == "3":
        workflow = get_workflow()
        print("\n" + workflow.get_graph_visualization())
    elif choice == "4":
        logger.info("Saindo...")
    else:
        logger.warning("Opção inválida. Saindo...")


if __name__ == "__main__":
    main()

