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

Resumo
- Para programação, combine ddmin + SFL para redução/localização técnica, 5 Whys/Ishikawa para causalidade humana e FTA/KT/8D quando o problema é sistêmico/recorrente.  
- Feche sempre com postmortem blameless e plano de ações.