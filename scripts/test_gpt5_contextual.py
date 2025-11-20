"""
Script de teste rapido para validar configuracao GPT-5 no Contextual Retrieval.

Testa:
1. Carregamento das configuracoes
2. Inicializacao do ContextualChunker com GPT-5
3. Geracao de contexto para um chunk de exemplo
4. Comparacao de tempo/qualidade GPT-5 vs Claude (opcional)
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import time

from config.settings import settings
from loguru import logger

from src.rag.contextual_chunker import ContextualChunker

# Documento de teste (sobre BSC)
TEST_DOCUMENT = {
    "content": """
    O Balanced Scorecard (BSC) eh um sistema de gestao estrategica que traduz a missao e
    estrategia de uma organizacao em um conjunto abrangente de medidas de desempenho.
    Desenvolvido por Robert Kaplan e David Norton na decada de 1990, o BSC organiza
    objetivos estrategicos em quatro perspectivas principais:

    1. Perspectiva Financeira: Foca em medidas financeiras tradicionais como ROI, receita e lucratividade.
    2. Perspectiva do Cliente: Avalia satisfacao, retencao e aquisicao de clientes.
    3. Perspectiva dos Processos Internos: Mede eficiencia operacional e qualidade dos processos.
    4. Perspectiva de Aprendizado e Crescimento: Foca em competencias, tecnologia e cultura organizacional.

    O BSC cria um mapa estrategico que mostra relacoes de causa-efeito entre objetivos,
    facilitando a comunicacao da estrategia e o alinhamento organizacional.
    """,
    "source": "test_bsc_intro.md",
    "title": "Introducao ao Balanced Scorecard",
}

# Chunk de exemplo para contextualizar
TEST_CHUNK = """
A Perspectiva Financeira no BSC tipicamente inclui indicadores como:
- Retorno sobre Investimento (ROI)
- Crescimento de Receita
- Reducao de Custos Operacionais
- EBITDA e Margem Liquida

Estes indicadores devem estar alinhados com a estrategia de crescimento da empresa.
"""


def test_configuration():
    """Testa se as configuracoes foram carregadas corretamente."""
    logger.info("[TEST] Testando Configuracao...")

    logger.info(f"   Provider: {settings.contextual_provider}")
    logger.info(f"   Contextual Retrieval: {settings.enable_contextual_retrieval}")

    if settings.contextual_provider == "openai":
        logger.info(f"   GPT-5 Model: {settings.gpt5_model}")
        logger.info(f"   Max Completion Tokens: {settings.gpt5_max_completion_tokens}")
        logger.info(f"   Reasoning Effort: {settings.gpt5_reasoning_effort}")
    else:
        logger.info(f"   Claude Model: {settings.contextual_model}")

    logger.info("[OK] Configuracao carregada com sucesso\n")


def test_chunker_initialization():
    """Testa inicializacao do ContextualChunker."""
    logger.info("[TEST] Testando Inicializacao do ContextualChunker...")

    try:
        chunker = ContextualChunker(enable_caching=False)
        logger.info(
            f"[OK] Chunker inicializado: provider={chunker.provider}, model={chunker.model}\n"
        )
        return chunker
    except Exception as e:
        logger.error(f"[ERRO] Falha ao inicializar chunker: {e}")
        return None


def test_context_generation(chunker: ContextualChunker):
    """Testa geracao de contexto para um chunk."""
    logger.info("[TEST] Testando Geracao de Contexto...")

    try:
        # Gera resumo do documento
        logger.info("   [STEP] Gerando resumo do documento...")
        start_time = time.time()

        summary = chunker._generate_document_summary(
            content=TEST_DOCUMENT["content"], document=TEST_DOCUMENT
        )

        summary_time = time.time() - start_time
        logger.info(f"   [OK] Resumo gerado em {summary_time:.2f}s")
        logger.info(f"   Resumo: {summary}\n")

        # Gera contexto para o chunk
        logger.info("   [STEP] Gerando contexto para chunk...")
        start_time = time.time()

        context = chunker._generate_context(
            chunk_content=TEST_CHUNK, document_summary=summary, document=TEST_DOCUMENT
        )

        context_time = time.time() - start_time
        logger.info(f"   [OK] Contexto gerado em {context_time:.2f}s")
        logger.info(f"   Contexto: {context}\n")

        # Resultado final
        contextual_content = f"{context}\n\n{TEST_CHUNK}"
        logger.info("[OK] Chunk Contextualizado:")
        logger.info(f"{contextual_content}\n")

        return {
            "summary_time": summary_time,
            "context_time": context_time,
            "total_time": summary_time + context_time,
            "context": context,
        }

    except Exception as e:
        logger.error(f"[ERRO] Falha ao gerar contexto: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return None


def compare_providers():
    """Compara GPT-5 vs Claude (opcional)."""
    logger.info("[TEST] Comparando Providers (GPT-5 vs Claude)...\n")

    results = {}

    # Testa GPT-5
    logger.info("=" * 70)
    logger.info("[PROVIDER] GPT-5 (OpenAI)")
    logger.info("=" * 70)
    chunker_gpt5 = ContextualChunker(provider="openai", enable_caching=False)
    results["gpt5"] = test_context_generation(chunker_gpt5)

    # Testa Claude (se configurado)
    if settings.anthropic_api_key:
        logger.info("=" * 70)
        logger.info("[PROVIDER] Claude Sonnet 4.5 (Anthropic)")
        logger.info("=" * 70)
        chunker_claude = ContextualChunker(provider="anthropic", enable_caching=False)
        results["claude"] = test_context_generation(chunker_claude)
    else:
        logger.warning("[SKIP] Claude nao configurado (ANTHROPIC_API_KEY ausente)")

    # Comparacao
    if "gpt5" in results and "claude" in results and results["gpt5"] and results["claude"]:
        logger.info("\n" + "=" * 70)
        logger.info("[COMPARACAO] Resultados")
        logger.info("=" * 70)

        gpt5_time = results["gpt5"]["total_time"]
        claude_time = results["claude"]["total_time"]

        logger.info(f"GPT-5 Tempo Total: {gpt5_time:.2f}s")
        logger.info(f"Claude Tempo Total: {claude_time:.2f}s")
        logger.info(
            f"Diferenca: {abs(gpt5_time - claude_time):.2f}s ({((gpt5_time / claude_time - 1) * 100):.1f}%)"
        )

        if gpt5_time < claude_time:
            logger.info(
                f"[VENCEDOR] GPT-5 foi {((claude_time / gpt5_time - 1) * 100):.1f}% mais rapido"
            )
        else:
            logger.info(
                f"[VENCEDOR] Claude foi {((gpt5_time / claude_time - 1) * 100):.1f}% mais rapido"
            )


def main():
    """Funcao principal."""
    logger.info("=" * 70)
    logger.info("[START] Teste de Configuracao GPT-5 para Contextual Retrieval")
    logger.info("=" * 70 + "\n")

    # 1. Testa configuracao
    test_configuration()

    # 2. Testa inicializacao
    chunker = test_chunker_initialization()
    if not chunker:
        logger.error("[ERRO] Nao foi possivel inicializar chunker. Abortando testes.")
        return

    # 3. Testa geracao de contexto
    result = test_context_generation(chunker)
    if not result:
        logger.error("[ERRO] Falha ao gerar contexto. Verifique configuracao da API.")
        return

    # 4. Comparacao de providers (opcional)
    # Descomente a linha abaixo para comparar providers
    # compare_providers()

    logger.info("\n" + "=" * 70)
    logger.info("[SUCCESS] Todos os testes concluidos!")
    logger.info("=" * 70)
    logger.info("\nProximos passos:")
    logger.info("1. Execute: python scripts/build_knowledge_base.py")
    logger.info("2. Verifique os logs para confirmar uso do GPT-5")
    logger.info("3. Compare custos e performance no painel OpenAI")


if __name__ == "__main__":
    main()
