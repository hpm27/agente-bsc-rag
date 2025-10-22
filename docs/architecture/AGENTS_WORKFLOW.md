# Workflow dos Agentes RAG (DISCOVERY) - Mermaid

```mermaid
flowchart TD
    A[START: DISCOVERY detectado] --> B{ClientProfile existe?}
    B -->|Nao| Z1[Retornar ONBOARDING]
    B -->|Sim| C[DiagnosticAgent.run_diagnostic]

    C --> D[run_parallel_analysis (asyncio.gather)]
    D --> D1[Financeira]
    D --> D2[Clientes]
    D --> D3[Processos Internos]
    D --> D4[Aprendizado e Crescimento]

    D1 --> R1[DiagnosticResult Financeira]
    D2 --> R2[DiagnosticResult Clientes]
    D3 --> R3[DiagnosticResult Processos]
    D4 --> R4[DiagnosticResult Aprendizado]

    R1 & R2 & R3 & R4 --> E[consolidate_diagnostic (structured output)]
    E --> F[generate_recommendations (structured output + fallback json_mode)]

    F --> G[CompleteDiagnostic]
    G --> H[orchestrator.synthesize_responses]
    H --> I[judge_evaluation]
    I --> J{Aprovado?}

    J -->|Sim| K[finalize]
    J -->|Nao e iter < max| L[refine (decide_next_step)]
    J -->|Nao e iter >= max| K

    K --> M[route_by_approval]
    M -->|APPROVED| END1[[END]]
    M -->|REJECTED/MODIFIED/TIMEOUT| DISC[DISCOVERY]
    M -->|PENDING/None| END2[[END]]
```

Notas:
- Consolidação e recomendações usam with_structured_output; fallback para json_mode quando necessário.
- As quatro análises executam em paralelo via asyncio.gather.
- Roteamento final considera approval_status.
