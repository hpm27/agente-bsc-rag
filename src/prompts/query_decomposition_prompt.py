"""
Prompt template para decomposição de queries BSC complexas.

Este módulo contém o prompt usado pelo QueryDecomposer para quebrar
queries complexas em sub-queries independentes e focadas.
"""

QUERY_DECOMPOSITION_PROMPT = """Você é um especialista em Balanced Scorecard (BSC), metodologia estratégica desenvolvida por Kaplan & Norton.

Sua tarefa é decompor queries complexas sobre BSC em sub-queries independentes e focadas.

QUERY ORIGINAL:
{query}

INSTRUÇÕES:
1. Analise a query e identifique os diferentes aspectos/conceitos BSC abordados
2. Decomponha em 2-4 sub-queries independentes que:
   - Sejam específicas e focadas em um único aspecto BSC
   - NÃO se sobreponham (cada uma cobre aspecto diferente)
   - Juntas, respondam COMPLETAMENTE à query original
   - Sejam adequadas para busca em literatura conceitual BSC (livros Kaplan & Norton)
3. Mantenha o contexto BSC em cada sub-query

FORMATO DE SAÍDA:
- Retorne APENAS as sub-queries
- Uma sub-query por linha
- SEM numeração, marcadores ou prefixos
- SEM explicações adicionais

EXEMPLO:
Query original: "Como implementar BSC considerando perspectivas financeira e de clientes?"
Saída:
Como implementar a perspectiva financeira no Balanced Scorecard?
Como implementar a perspectiva de clientes no Balanced Scorecard?

AGORA DECOMPONHA A QUERY ORIGINAL:"""


# Heurísticas de decisão para quando decompor queries
# Documentação das regras implementadas em QueryDecomposer.should_decompose()
DECOMPOSITION_HEURISTICS_DOC = """
HEURÍSTICAS PARA DECISÃO DE DECOMPOSIÇÃO

O QueryDecomposer usa um sistema de pontuação baseado em 5 heurísticas:

1. COMPRIMENTO DA QUERY (pré-requisito)
   - Condição: len(query) > DECOMPOSITION_MIN_LENGTH (padrão: 50 caracteres)
   - Rationale: Queries curtas geralmente são simples e focadas

2. PALAVRAS DE LIGAÇÃO (AND-words) [+1 ponto]
   - Palavras: "e", "também", "além", "além disso", "considerando", "assim como"
   - Rationale: Indicam múltiplas partes/aspectos na query

3. MÚLTIPLAS PERSPECTIVAS BSC [+2 pontos]
   - Perspectivas: "financeira", "cliente", "clientes", "processo", "processos", 
                    "aprendizado", "crescimento", "aprendizado e crescimento"
   - Condição: 2+ perspectivas mencionadas
   - Rationale: Queries multi-perspectiva são naturalmente complexas no contexto BSC

4. MÚLTIPLAS PERGUNTAS [+1 ponto]
   - Condição: 2+ pontos de interrogação (?) na query
   - Rationale: Múltiplas perguntas explícitas indicam complexidade

5. PALAVRAS DE COMPLEXIDADE [+1 ponto]
   - Palavras: "implementar", "implementação", "interconexão", "interconexões", 
               "relação", "relações", "diferença", "diferenças", "comparar", "comparação"
   - Rationale: Indicam análise complexa ou multi-facetada necessária

DECISÃO FINAL:
- SE pontuação >= DECOMPOSITION_SCORE_THRESHOLD (padrão: 2) E len(query) > min_length:
    → DECOMPOR query
- SENÃO:
    → NÃO DECOMPOR (usar retrieval normal)

EXEMPLOS:

Query: "O que é BSC?"
- Comprimento: 12 chars (< 50) → NÃO DECOMPOR
- Score: N/A (não passa pré-requisito)

Query: "Como implementar BSC considerando as perspectivas financeira, clientes e processos internos?"
- Comprimento: 95 chars (> 50) ✓
- Score: +1 (considerando) +2 (3 perspectivas) +1 (implementar) = 4 pontos
- Decisão: DECOMPOR (score 4 >= threshold 2)

Query: "Quais são os principais KPIs da perspectiva financeira do Balanced Scorecard?"
- Comprimento: 80 chars (> 50) ✓
- Score: 0 (nenhuma heurística trigada)
- Decisão: NÃO DECOMPOR (score 0 < threshold 2)
"""

