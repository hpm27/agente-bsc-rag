### Principais metodologias (com foco em programação/SRE)
- 5 Whys (com postmortem blameless)
  - Quando usar: incidentes simples a moderados; acelerar entendimento causal humano.
  - Dicas: combine com timeline e evidências; evite “culpa”; considere o “How, not Why” em cadeias multifatoriais.
  - Fontes: [Atlassian — 5 Whys](https://www.atlassian.com/incident-management/postmortem/5-whys), [Google SRE — Blameless Postmortem](https://sre.google/sre-book/postmortem-culture/), [Salesforce Eng — How, Not Why](https://engineering.salesforce.com/how-not-why-an-alternative-to-the-five-whys-for-post-mortems-4518098cca17/)

- Diagrama de Ishikawa (Fishbone)
  - Quando usar: bugs multifatoriais (pessoas, processo, código, ambiente, ferramentas, dados).
  - Vantagem: ótimo para brainstorming estruturado e mapeamento de hipóteses.
  - Fontes: [ASQ — Fishbone](https://asq.org/quality-resources/fishbone), [Fishbone para defeitos de software](https://www.researchgate.net/figure/Fishbone-diagram-for-software-defects_fig3_238327248)

- Fault Tree Analysis (FTA)
  - Quando usar: outages complexos, falhas sistêmicas com portas lógicas (AND/OR), dependências encadeadas.
  - Vantagem: dedutivo e visual; bom para riscos e “o que precisa coincidir para falhar”.
  - Fontes: [Fault Tree Analysis Guide](https://reliability.com/resources/articles/fault-tree-analysis-fta-guide/), [Wikipedia — FTA](https://en.wikipedia.org/wiki/Fault_tree_analysis)

- Kepner‑Tregoe (KT)
  - Quando usar: análise estruturada de problemas/decisões em incidentes de TI; padronização em times grandes.
  - Vantagem: separa claramente “o que é/ não é”, isola variáveis críticas, define ações.
  - Fontes: [Kepner‑Tregoe RCA](https://kepner-tregoe.com/training/root-cause-analysis/)

- 8D Problem Solving
  - Quando usar: problemas crônicos/recorrentes; quando é exigido por compliance/cliente.
  - Vantagem: processo completo (D0–D8) com contenção, causa raiz, ações e prevenção.
  - Fontes: [ASQ — 8D](https://asq.org/quality-resources/eight-disciplines-8d)

- Delta Debugging (ddmin, Andreas Zeller)
  - Quando usar: reproduções de bug; inputs/testes grandes que precisam ser minimizados até o caso mínimo que falha.
  - Vantagem: altíssima eficácia técnica; automatiza isolamento do “failure‑inducing input/change”.
  - Fontes: [Zeller — Simplifying and Isolating Failure-Inducing Input (PDF)](https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf), [Debugging Book — DeltaDebugger](https://www.debuggingbook.org/html/DeltaDebugger.html)

- Spectrum‑Based Fault Localization (SFL: Ochiai, Tarantula, Jaccard)
  - Quando usar: há suíte de testes; precisa rankear linhas/blocos mais suspeitos a partir de cobertura x falhas.
  - Vantagem: acelera muito o “onde olhar no código”; funciona bem com boa cobertura e casos negativos.
  - Fontes: [Survey SFL (arXiv)](https://arxiv.org/pdf/1607.04347), [Boosting SFL (TSE 2019)](https://lingming.cs.illinois.edu/publications/tse2019.pdf)

- Postmortem blameless + templates
  - Quando usar: sempre após incidentes relevantes; institucionaliza aprendizado e follow‑ups.
  - Fontes: [Google SRE — Workbook/Template](https://sre.google/workbook/postmortem-culture/), [Coleção de templates (GitHub)](https://github.com/dastergon/postmortem-templates)

- RCA com grafos causais / AI‑assist (em evolução)
  - Quando usar: ambientes altamente observáveis com topologia de serviços e muitos sinais (logs, métricas, traces).
  - Fontes: [Honeycomb — Incident Reviews](https://www.honeycomb.io/blog/incident-management-best-practices), [incident.io — AI SRE](https://incident.io/ai-sre), [RADICE — Causal Graph RCA (2025)](https://arxiv.org/html/2501.11545v1)

### O que costuma ser mais eficiente para times de software
- Muito eficaz (rápido/alto ROI técnico):
  - Delta Debugging (reduz caso de teste/entrada até o mínimo que falha).
  - Spectrum‑Based Fault Localization (prioriza trechos suspeitos com base em testes).
  - Postmortem blameless com timeline/fatos (garante aprendizado e ações).

- Eficaz (moderado):
  - 5 Whys (com evidências e timeline) + Ishikawa para multifatores.
  - Kepner‑Tregoe para padronizar análise em times grandes.

- Eficaz porém pesado (quando necessário):
  - FTA para outages complexos; 8D para problemas crônicos/compliance.
  - Grafos causais/AI quando há boa observabilidade e volume de sinais.

### Fluxo recomendado (prático e rápido)
1) Coletar fatos e timeline (logs, métricas, traces, diffs, mudanças recentes).  
2) ddmin (Delta Debugging) se houver input/state grande ou mudança extensa.  
3) Rodar SFL com cobertura de testes (Ochiai/Tarantula) para priorizar arquivos/linhas.  
4) 5 Whys com evidências; use Ishikawa se multifatorial.  
5) Se sistêmico, modelar via FTA; se organizacional/recorrente, 8D/KT.  
6) Registrar postmortem blameless e ações preventivas (template SRE).  

### Links-chave (comunidade)
- 5 Whys e Postmortem: [Atlassian](https://www.atlassian.com/incident-management/postmortem/5-whys), [Google SRE](https://sre.google/sre-book/postmortem-culture/)  
- Ishikawa: [ASQ](https://asq.org/quality-resources/fishbone)  
- FTA: [Reliability.com](https://reliability.com/resources/articles/fault-tree-analysis-fta-guide/)  
- KT: [Kepner‑Tregoe](https://kepner-tregoe.com/training/root-cause-analysis/)  
- 8D: [ASQ](https://asq.org/quality-resources/eight-disciplines-8d)  
- Delta Debugging: [Zeller PDF](https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf)  
- SFL: [Survey arXiv](https://arxiv.org/pdf/1607.04347)  
- Templates: [Google Workbook](https://sre.google/workbook/postmortem-culture/), [Templates GitHub](https://github.com/dastergon/postmortem-templates)

### Case Study: 5 Whys Meta-Análise - Debugging Testes (Sessão 19 - 2025-10-19)

**Context**: Durante implementação do KPI Definer Tool (FASE 3.4), 2 de 19 testes unitários falharam com erro Pydantic: `customer_kpis` continha KPIs com `perspective="Financeira"` ao invés de `"Clientes"`. Aplicamos **5 Whys Root Cause Analysis ao próprio debugging** (meta-análise metodológica).

**5 Whys Aplicado**:

1. **WHY 1**: Por que o teste falha?
   - **Resposta**: `customer_kpis` contém KPIs com perspectiva errada
   - **Evidência**: `ValidationError` linha 178 de `kpi_definer.py`

2. **WHY 2**: Por que `customer_kpis` tem perspectiva errada?
   - **Resposta**: Mock LLM retorna sempre os mesmos 3 KPIs (perspectiva Financeira)
   - **Evidência**: Mock configurado com `return_value` estático

3. **WHY 3**: Por que `side_effect` não diferencia perspectivas?
   - **Resposta**: String matching no prompt ("Financeira" in prompt) falhou
   - **Evidência**: Formato do prompt não foi validado antes de criar lógica

4. **WHY 4**: Por que detecção de perspectiva no prompt falha?
   - **Resposta**: Prompt tem encoding/contexto complexo, string matching simples é frágil
   - **Evidência**: "Clientes" aparece múltiplas vezes em diferentes contextos

5. **WHY 5** (ROOT CAUSE): Por que não validei o formato do prompt?
   - **Resposta**: Assumi estrutura sem testar. **Root Cause Verdadeiro**: Mock estático não considera múltiplas chamadas sequenciais com outputs diferentes
   - **Pergunta-chave não feita**: "Quantas vezes o mock será invocado e com quais diferenças nos outputs esperados?"

**Solução**: `itertools.cycle` para retornar valores sequencialmente
```python
from itertools import cycle

perspective_order = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
perspective_cycle = cycle(perspective_order)

def mock_side_effect(prompt: str):
    perspective = next(perspective_cycle)  # Retorna próxima perspectiva na ordem
    kpis = kpis_by_perspective[perspective]
    return KPIListOutput(kpis=kpis)

mock.side_effect = mock_side_effect
```

**Resultado**: 19/19 testes passando (100%), 77% coverage, 19.10s execução

**Lição-Chave**: **5 Whys funciona para debugging técnico**, não apenas problemas de negócio. Root cause identificado sistematicamente (WHY 1-5) resultou em solução elegante (`itertools.cycle`) ao invés de gambiarra (regex frágil).

**ROI**: Sequential Thinking + 5 Whys economizou **15-20 minutos** vs trial-and-error (testar múltiplas tentativas sem diagnóstico).

**Aplicabilidade**: Qualquer debugging complexo (não apenas testes). Performance issues, bugs produção, arquitetura bottlenecks.

**Lição Detalhada**: `docs/lessons/lesson-kpi-testing-5whys-methodology-2025-10-19.md` (950+ linhas com checklist completo, código exemplos, antipadrões evitados)

Resumo
- Para programação, combine ddmin + SFL para redução/localização técnica, 5 Whys/Ishikawa para causalidade humana e FTA/KT/8D quando o problema é sistêmico/recorrente.  
- Feche sempre com postmortem blameless e plano de ações.