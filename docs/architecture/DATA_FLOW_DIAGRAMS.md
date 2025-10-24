# Data Flow Diagrams - Agente Consultor BSC

**Data**: 2025-10-19  
**Versao**: 1.0  
**Objetivo**: Visualizar fluxos de dados criticos entre agentes, schemas e workflow para acelerar desenvolvimento FASE 3

---

## EXECUTIVE SUMMARY

Este documento apresenta **5 diagramas Mermaid** que mapeiam os fluxos de dados do sistema consultor BSC:

1. **ClientProfile Lifecycle**: Criacao → Persistencia Mem0 → Recuperacao
2. **Diagnostic Workflow**: DISCOVERY state → DiagnosticAgent → CompleteDiagnostic
3. **Schema Dependencies**: Relacoes Pydantic entre ClientProfile, BSCState, DiagnosticResult
4. **Agent Interactions**: Comunicacao entre OnboardingAgent, ClientProfileAgent, DiagnosticAgent
5. **State Transitions**: Estados LangGraph (ONBOARDING → DISCOVERY → APPROVAL_PENDING)

**ROI Esperado**: Reducao de 15-20 min para 2-3 min por consulta de fluxo (economia 4.5h em 12 tarefas FASE 3)

---

## DIAGRAMA 1: ClientProfile Lifecycle

**Objetivo**: Mostrar como ClientProfile e criado, persistido no Mem0 e recuperado em sessoes futuras.

**Pontos Criticos**:
- Eventual consistency: sleep(1s) apos add() e update()
- ProfileNotFoundError trigger para criar novo profile
- Delete-then-add pattern garante 1 memoria por user_id

```mermaid
sequenceDiagram
    participant User
    participant Workflow as BSCWorkflow
    participant LoadMem as load_client_memory
    participant Mem0 as Mem0Client
    participant Profile as ClientProfile
    participant SaveMem as save_client_memory

    User->>Workflow: run(user_id="cliente_001")
    Workflow->>LoadMem: load_client_memory(state)
    LoadMem->>Mem0: get_profile(user_id)
    
    alt Profile Nao Existe
        Mem0-->>LoadMem: ProfileNotFoundError
        LoadMem->>Profile: create_placeholder_profile()
        Profile-->>LoadMem: ClientProfile vazio
        LoadMem->>Mem0: add(profile, user_id)
        Note over Mem0: sleep(1s)<br/>Eventual consistency
        Mem0-->>LoadMem: memory_id criado
        LoadMem-->>Workflow: state.client_profile + current_phase=ONBOARDING
    else Profile Existe
        Mem0-->>LoadMem: profile existente
        LoadMem-->>Workflow: state.client_profile + current_phase=DISCOVERY
    end
    
    Note over Workflow: Workflow executa<br/>(onboarding, discovery, etc)
    
    Workflow->>SaveMem: save_client_memory(state)
    SaveMem->>Mem0: update_profile(user_id, profile)
    Note over Mem0: sleep(1s)<br/>Eventual consistency
    Mem0-->>SaveMem: profile atualizado
    SaveMem-->>Workflow: state atualizado
    Workflow-->>User: response + profile persistido
```

**Arquivos Relacionados**:
- `src/graph/memory_nodes.py`: load_client_memory(), save_client_memory()
- `src/memory/mem0_client.py`: Mem0Client.get_profile(), add(), update_profile()
- `src/memory/schemas.py`: ClientProfile schema Pydantic

---

## DIAGRAMA 2: Diagnostic Workflow

**Objetivo**: Mapear fluxo DISCOVERY state desde deteccao ate geracao de CompleteDiagnostic.

**Pontos Criticos**:
- Analise paralela AsyncIO das 4 perspectivas BSC
- Fallback para ONBOARDING se ClientProfile ausente
- Transicao automatica DISCOVERY → APPROVAL_PENDING

```mermaid
flowchart TD
    Start([DISCOVERY State Detectado]) --> CheckProfile{ClientProfile<br/>existe?}
    
    CheckProfile -->|NAO| ReturnOnboarding[Retornar ONBOARDING<br/>fallback]
    CheckProfile -->|SIM| RunDiagnostic[DiagnosticAgent.run_diagnostic]
    
    RunDiagnostic --> ParallelAnalysis[run_parallel_analysis<br/>AsyncIO]
    
    ParallelAnalysis --> Financial[analyze_perspective<br/>Financeira]
    ParallelAnalysis --> Customer[analyze_perspective<br/>Clientes]
    ParallelAnalysis --> Process[analyze_perspective<br/>Processos Internos]
    ParallelAnalysis --> Learning[analyze_perspective<br/>Aprendizado e Crescimento]
    
    Financial --> Results1[DiagnosticResult<br/>Financial]
    Customer --> Results2[DiagnosticResult<br/>Customer]
    Process --> Results3[DiagnosticResult<br/>Process]
    Learning --> Results4[DiagnosticResult<br/>Learning]
    
    Results1 --> Consolidate[consolidate_diagnostic]
    Results2 --> Consolidate
    Results3 --> Consolidate
    Results4 --> Consolidate
    
    Consolidate --> GenRec[generate_recommendations]
    GenRec --> CompleteDiag[CompleteDiagnostic<br/>4 perspectivas + recommendations]
    
    CompleteDiag --> SaveState[BSCState.diagnostic = result]
    SaveState --> Transition[current_phase = APPROVAL_PENDING]
    
    Transition --> End([Retornar para Workflow])
    ReturnOnboarding --> End

    style Financial fill:#90EE90
    style Customer fill:#87CEEB
    style Process fill:#FFD700
    style Learning fill:#FFA07A
    style CompleteDiag fill:#9370DB
```

**Arquivos Relacionados**:
- `src/graph/workflow.py`: discovery_handler()
- `src/agents/diagnostic_agent.py`: run_diagnostic(), run_parallel_analysis()
- `src/prompts/diagnostic_prompts.py`: Prompts das 4 perspectivas
- `src/memory/schemas.py`: DiagnosticResult, Recommendation, CompleteDiagnostic

---

## DIAGRAMA 3: Schema Dependencies

**Objetivo**: Visualizar relacoes de composicao e heranca entre schemas Pydantic core.

**Pontos Criticos**:
- ClientProfile e schema raiz que agrega todos sub-schemas
- CompleteDiagnostic tem 4 campos individuais (financial, customer, process, learning)
- Recommendation tem priority logic no model_validator (HIGH impact + LOW effort = HIGH priority auto)

```mermaid
classDiagram
    class BaseModel {
        <<Pydantic>>
        +model_dump()
        +model_validate()
    }
    
    class ClientProfile {
        +client_id: str
        +company: CompanyInfo
        +context: StrategicContext
        +diagnostic_data: DiagnosticData
        +engagement: EngagementState
        +complete_diagnostic: Optional~Dict~
        +created_at: datetime
        +updated_at: datetime
        +to_mem0(): Dict
        +from_mem0(data): ClientProfile
    }
    
    class CompanyInfo {
        +name: str
        +sector: Literal[...]
        +size: Literal[pequena, media, grande]
        +description: Optional~str~
    }
    
    class StrategicContext {
        +current_challenges: List~str~
        +strategic_objectives: List~str~
        +time_horizon: Optional~str~
    }
    
    class DiagnosticData {
        +assessment_date: Optional~datetime~
        +swot_analysis: Optional~SWOTAnalysis~
        +key_findings: List~str~
    }
    
    class EngagementState {
        +phase: Literal[IDLE, ONBOARDING, DISCOVERY, ...]
        +last_interaction: datetime
        +metadata: Dict
    }
    
    class DiagnosticResult {
        +perspective: Literal[Financeira, Clientes, ...]
        +current_state: str (min 20 chars)
        +gaps: List~str~ (min 1 item)
        +opportunities: List~str~ (min 1 item)
        +priority: Literal[HIGH, MEDIUM, LOW]
        +key_insights: List~str~
    }
    
    class Recommendation {
        +title: str (min 10 chars)
        +description: str (min 50 chars)
        +impact: Literal[HIGH, MEDIUM, LOW]
        +effort: Literal[HIGH, MEDIUM, LOW]
        +priority: Literal[HIGH, MEDIUM, LOW]
        +timeframe: str
        +next_steps: List~str~ (min 1 item)
        +model_validator: priority logic
    }
    
    class CompleteDiagnostic {
        +financial: DiagnosticResult
        +customer: DiagnosticResult
        +process: DiagnosticResult
        +learning: DiagnosticResult
        +recommendations: List~Recommendation~ (min 3)
        +cross_perspective_synergies: List~str~
        +executive_summary: str (min 100 chars)
        +next_phase: str
        +model_validator: verifica perspectivas
    }
    
    BaseModel <|-- ClientProfile
    BaseModel <|-- CompanyInfo
    BaseModel <|-- StrategicContext
    BaseModel <|-- DiagnosticData
    BaseModel <|-- EngagementState
    BaseModel <|-- DiagnosticResult
    BaseModel <|-- Recommendation
    BaseModel <|-- CompleteDiagnostic
    
    ClientProfile *-- CompanyInfo : contem
    ClientProfile *-- StrategicContext : contem
    ClientProfile *-- DiagnosticData : contem
    ClientProfile *-- EngagementState : contem
    
    CompleteDiagnostic *-- DiagnosticResult : 4x (financial, customer, process, learning)
    CompleteDiagnostic *-- Recommendation : 3+ recommendations
```

**Arquivos Relacionados**:
- `src/memory/schemas.py`: Todos schemas Pydantic
- `tests/test_memory_schemas.py`: Validacoes Pydantic (25 testes)
- `tests/test_diagnostic_agent.py`: Testes de DiagnosticResult/CompleteDiagnostic

---

## DIAGRAMA 4: Agent Interactions

**Objetivo**: Mostrar comunicacao entre agentes durante workflows ONBOARDING e DISCOVERY.

**Pontos Criticos**:
- Multi-turn loop em ONBOARDING (ate 3 steps: COMPANY → STRATEGIC → ENGAGEMENT)
- Lazy loading de agentes em ConsultingOrchestrator (previne circular imports)
- ClientProfile criado automaticamente ao completar onboarding

```mermaid
sequenceDiagram
    participant Workflow as BSCWorkflow
    participant Orchestrator as ConsultingOrchestrator
    participant OnbAgent as OnboardingAgent
    participant ProfAgent as ClientProfileAgent
    participant DiagAgent as DiagnosticAgent
    participant State as BSCState
    
    Note over Workflow: FLUXO ONBOARDING
    
    Workflow->>Orchestrator: coordinate_onboarding(state)
    Orchestrator->>OnbAgent: start_onboarding()
    OnbAgent-->>Orchestrator: {"question": "Qual o nome da empresa?"}
    Orchestrator-->>Workflow: response inicial
    
    loop Multi-turn (ate 3 steps)
        Workflow->>Orchestrator: coordinate_onboarding(state, user_input)
        Orchestrator->>OnbAgent: process_turn(state, user_input)
        OnbAgent->>State: Atualizar onboarding_progress
        
        alt Step Incompleto
            OnbAgent-->>Orchestrator: {"response": "...", "is_complete": False}
            Orchestrator-->>Workflow: Proxima pergunta
        else Step Completo
            OnbAgent->>ProfAgent: extract_profile(conversation_history)
            ProfAgent->>ProfAgent: extract_company_info()
            ProfAgent->>ProfAgent: identify_challenges()
            ProfAgent->>ProfAgent: define_objectives()
            ProfAgent-->>OnbAgent: ClientProfile completo
            OnbAgent->>State: current_phase = DISCOVERY
            OnbAgent-->>Orchestrator: {"response": "...", "is_complete": True}
            Orchestrator-->>Workflow: Transicao DISCOVERY
        end
    end
    
    Note over Workflow: FLUXO DISCOVERY
    
    Workflow->>Orchestrator: coordinate_discovery(state)
    Orchestrator->>DiagAgent: run_diagnostic(client_profile)
    DiagAgent->>DiagAgent: run_parallel_analysis() (AsyncIO 4 perspectivas)
    DiagAgent->>DiagAgent: consolidate_diagnostic()
    DiagAgent->>DiagAgent: generate_recommendations()
    DiagAgent-->>Orchestrator: CompleteDiagnostic
    Orchestrator->>State: diagnostic + current_phase = APPROVAL_PENDING
    Orchestrator-->>Workflow: Diagnostic completo
```

**Arquivos Relacionados**:
- `src/graph/workflow.py`: onboarding_handler(), discovery_handler()
- `src/graph/consulting_orchestrator.py`: coordinate_onboarding(), coordinate_discovery()
- `src/agents/onboarding_agent.py`: start_onboarding(), process_turn()
- `src/agents/client_profile_agent.py`: extract_profile(), process_onboarding()
- `src/agents/diagnostic_agent.py`: run_diagnostic()

---

## DIAGRAMA 5: State Transitions

**Objetivo**: Mapear estados LangGraph e transicoes condicionais do workflow consultivo.

**Pontos Criticos**:
- IDLE e estado inicial (cliente sem interacao)
- ProfileNotFoundError trigger automatico para ONBOARDING
- APPROVAL_PENDING pode retornar para DISCOVERY se rejeitado

```mermaid
stateDiagram-v2
    [*] --> IDLE: Sistema inicializa
    
    IDLE --> ONBOARDING: ProfileNotFoundError<br/>(cliente novo)
    IDLE --> DISCOVERY: ClientProfile existe<br/>(cliente retornando)
    
    ONBOARDING --> ONBOARDING: is_complete=False<br/>(mais perguntas)
    ONBOARDING --> DISCOVERY: is_complete=True<br/>(profile criado)
    
    DISCOVERY --> APPROVAL_PENDING: CompleteDiagnostic completo<br/>(diagnostic pronto)
    
    APPROVAL_PENDING --> END: approval_status=APPROVED<br/>(cliente aprova)
    APPROVAL_PENDING --> DISCOVERY: approval_status=REJECTED/MODIFIED<br/>(refazer diagnostic)
    APPROVAL_PENDING --> END: approval_status=TIMEOUT<br/>(sem resposta)
    
    END --> [*]: Workflow finalizado
    
    note right of IDLE
        Estado inicial
        Routing: route_by_phase()
    end note
    
    note right of ONBOARDING
        Multi-turn conversacional
        Handler: onboarding_handler()
        Sessions: _onboarding_sessions dict
    end note
    
    note right of DISCOVERY
        Analise 4 perspectivas BSC
        Handler: discovery_handler()
        Output: CompleteDiagnostic
    end note
    
    note right of APPROVAL_PENDING
        Human-in-the-loop
        Handler: approval_handler()
        Routing: route_by_approval()
    end note
```

**Arquivos Relacionados**:
- `src/graph/consulting_states.py`: Enum ConsultingPhase, ApprovalStatus, TransitionTrigger
- `src/graph/workflow.py`: route_by_phase(), route_by_approval()
- `src/graph/consulting_orchestrator.py`: validate_transition()
- `docs/consulting/workflow-design.md`: Transition rules completas (1000+ linhas)

---

## NOTAS TECNICAS

### Mermaid Syntax Validada

Todos diagramas usam **Mermaid.js v11.1.0+** syntax:
- `sequenceDiagram`: Temporal flows com participantes e messages
- `flowchart TD`: Top-to-bottom decision flows
- `classDiagram`: UML class relationships (composicao `*--`, heranca `<|--`)
- `stateDiagram-v2`: Finite state machines com transitions

### Best Practices Aplicadas (2024-2025)

1. **LangGraph StateGraph Pattern** (LangChain Sep 2025):
   - Nodes como Python functions
   - Conditional edges com routing functions
   - State como TypedDict/Pydantic
   
2. **AsyncIO Parallelism** (validado FASE 2):
   - run_parallel_analysis() executa 4 perspectivas simultaneamente
   - 3.34x speedup vs serial (70s → 21s P50)
   
3. **Eventual Consistency Mem0** (validado FASE 1.8):
   - sleep(1s) apos add() e update()
   - Delete-then-add pattern previne duplicatas
   - 100% success rate em testes E2E

4. **Pydantic V2 Validators** (Sep 2024):
   - field_validator: Validacao individual (listas nao vazias, min_length)
   - model_validator(mode='after'): Cross-field validation (priority logic)
   
5. **TYPE_CHECKING Pattern** (PEP 484 + PEP 563):
   - `from __future__ import annotations` (postponed annotations)
   - `if TYPE_CHECKING:` imports para type hints (zero circular imports runtime)

### Ferramentas de Validacao

Para verificar diagramas Mermaid:
- **Mermaid Live Editor**: https://mermaid.live/
- **VS Code Extension**: Mermaid Preview (bierner.markdown-mermaid)
- **Markdown Preview Enhanced**: Suporta Mermaid nativamente

---

## REFERENCIAS

1. **LangGraph Architecture** (Medium, Sep 2024): https://medium.com/@shuv.sdr/langgraph-architecture-and-design-280c365aaf2c
2. **AI Agent Architectures 2025** (DEV Community, May 2025): https://dev.to/sohail-akbar/the-ultimate-guide-to-ai-agent-architectures-in-2025-2j1c
3. **Mermaid Architecture Diagrams** (Official Docs, v11.1.0+): https://mermaid.js.org/syntax/architecture.html
4. **LangGraph Multi-Agent Workflows** (LangChain Blog, Sep 2025): https://blog.langchain.com/building-langgraph/
5. **Lesson Regression Prevention** (Interno, Out 2025): `docs/lessons/lesson-regression-prevention-methodology-2025-10-17.md`

---

**Ultima Atualizacao**: 2025-10-19 (Sessao 15, FASE 3 - Tarefa 3.0.1)  
**Autores**: Agente BSC RAG + Sequential Thinking + Brightdata Research  
**Proximo**: Tarefa 3.0.2 - API Contracts Documentation

