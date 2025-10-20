# API Contracts Documentation - Agente Consultor BSC

**Data**: 2025-10-19  
**Versao**: 1.0.0  
**Objetivo**: Documentar interfaces publicas de todos os agentes consultorios BSC para acelerar desenvolvimento FASE 3

---

## EXECUTIVE SUMMARY

Este documento especifica os **contratos API** de 8 agentes/classes do sistema consultor BSC:

1. **ClientProfileAgent**: Extracao inteligente de contexto empresarial (onboarding)
2. **OnboardingAgent**: Orquestrador conversacional multi-turn
3. **DiagnosticAgent**: Analise diagnostica BSC multi-perspectiva
4. **Specialist Agents** (4 agentes): Financial, Customer, Process, Learning - Analise por perspectiva
5. **ConsultingOrchestrator**: Coordenador dos agentes especialistas (RAG tradicional)
6. **JudgeAgent**: Avaliacao de qualidade das respostas

**Formato de Documentacao**:
- **Signature**: Assinatura completa com type hints
- **Parameters**: Parametros com tipos e descricao
- **Returns**: Tipo de retorno e estrutura
- **Raises**: Excecoes esperadas e quando ocorrem
- **Pydantic Schemas**: Schemas envolvidos com validacoes
- **Added**: Versao quando metodo foi adicionado
- **Example**: Code snippet minimo testavel
- **Notes**: Observacoes tecnicas (timeouts, retry, etc)
- **Visual Reference**: Link para diagrama em DATA_FLOW_DIAGRAMS.md

**ROI Esperado**: ~1h economizada em FASE 3 (agente nao precisa ler codigo fonte)

**Best Practices Aplicadas**:
- Pydantic AI Framework patterns (type hints + runtime validation) - DataCamp Sep 2025
- OpenAPI-style documentation (Speakeasy Sep 2024)
- Semantic versioning + deprecation timelines (DeepDocs Oct 2025)
- Error handling comprehensive (DEV Community Jul 2024)

---

## TABLE OF CONTENTS

1. [ClientProfileAgent](#1-clientprofileagent)
2. [OnboardingAgent](#2-onboardingagent)
3. [DiagnosticAgent](#3-diagnosticagent)
4. [Specialist Agents](#4-specialist-agents)
5. [ConsultingOrchestrator](#5-consultingorchestrator)
6. [JudgeAgent](#6-judgeagent)
7. [Pydantic Schemas Reference](#7-pydantic-schemas-reference)
8. [Changelog](#8-changelog)

---

## 1. ClientProfileAgent

**Purpose**: Extrai e estrutura informacoes da empresa durante fase ONBOARDING do workflow consultivo BSC.

**Location**: `src/agents/client_profile_agent.py`

**LLM**: GPT-5 mini (cost-effective para onboarding)

**Visual Reference**: Ver Diagrama 1 (ClientProfile Lifecycle) e Diagrama 4 (Agent Interactions) em `DATA_FLOW_DIAGRAMS.md`

---

### 1.1 ClientProfileAgent.extract_company_info

**Signature**:
```python
def extract_company_info(self, conversation: str) -> CompanyInfo
```

**Purpose**: Extrai CompanyInfo estruturado de conversa natural usando LLM structured output.

**Parameters**:
- `conversation` (str): Texto completo da conversacao de onboarding. Deve conter mencoes a nome da empresa, setor e porte. Minimo 50 caracteres.

**Returns**:
- `CompanyInfo`: Objeto Pydantic validado com campos:
  - `name` (str): Nome da empresa (1-200 chars)
  - `sector` (str): Setor de atuacao (1-100 chars)
  - `size` (Literal["Pequena", "Media", "Grande"]): Porte da empresa

**Raises**:
- `ValidationError` (Pydantic): Se conversation vazia ou CompanyInfo invalido (campos fora dos limites)
- `ValueError`: Se LLM retorna JSON invalido ou nao parseable
- `TimeoutError`: Se LLM excede timeout (600s)
- `APIError` (OpenAI): Se API key invalida ou rate limit

**Pydantic Schemas**:
- `CompanyInfo`: Ver secao 7.1

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.agents.client_profile_agent import ClientProfileAgent
from src.memory.schemas import CompanyInfo
from pydantic import ValidationError
from config.settings import get_llm

agent = ClientProfileAgent(llm=get_llm("gpt-5-mini-2025-08-07"))

try:
    company_info = agent.extract_company_info(
        conversation="Nossa empresa e a TechCorp, atuamos no setor de tecnologia e somos uma empresa de porte medio."
    )
    print(company_info.name)  # "TechCorp"
    print(company_info.sector)  # "Tecnologia"
    print(company_info.size)  # "Media"
except ValidationError as e:
    logger.error(f"Dados invalidos: {e}")
except TimeoutError:
    logger.error("LLM timeout apos 600s")
```

**Notes**:
- Usa LangChain `with_structured_output()` (2025 feature)
- Few-shot prompt com 3 exemplos (setor tecnologia, varejo, saude)
- Retry automatico: 3 tentativas com exponential backoff (2^n segundos)
- Temperature: 0.1 (precisao maxima para extracao)

---

### 1.2 ClientProfileAgent.identify_challenges

**Signature**:
```python
def identify_challenges(
    self,
    conversation: str,
    company_info: CompanyInfo
) -> list[str]
```

**Purpose**: Identifica desafios estrategicos do cliente a partir de conversacao.

**Parameters**:
- `conversation` (str): Texto completo da conversacao. Deve conter mencoes a problemas, dificuldades, ou objetivos. Minimo 50 caracteres.
- `company_info` (CompanyInfo): Contexto da empresa ja extraido (usado para contextualizar challenges)

**Returns**:
- `list[str]`: Lista de 3-7 desafios estrategicos identificados. Cada challenge tem 20-500 caracteres.

**Raises**:
- `ValidationError` (Pydantic): Se lista vazia ou challenges fora dos limites (min 3, max 7)
- `ValueError`: Se LLM retorna JSON invalido
- `TimeoutError`: Se LLM excede timeout (600s)
- `APIError` (OpenAI): Se API key invalida ou rate limit

**Pydantic Schemas**:
- `ChallengesList`: Schema interno com validacao `min_length=3, max_length=7`
- `CompanyInfo`: Ver secao 7.1

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.agents.client_profile_agent import ClientProfileAgent
from src.memory.schemas import CompanyInfo

agent = ClientProfileAgent(llm=get_llm("gpt-5-mini-2025-08-07"))

company_info = CompanyInfo(name="TechCorp", sector="Tecnologia", size="Media")

challenges = agent.identify_challenges(
    conversation="Estamos com dificuldade em reter clientes e precisamos melhorar nossos processos internos.",
    company_info=company_info
)

print(challenges)
# ["Baixa retencao de clientes", "Processos internos ineficientes", ...]
```

**Notes**:
- Usa structured output Pydantic `ChallengesList`
- Prompt system contextualiza com setor da empresa
- Retry automatico: 3 tentativas
- Se retornar < 3 ou > 7 challenges, relanca ValidationError

---

### 1.3 ClientProfileAgent.define_objectives

**Signature**:
```python
def define_objectives(
    self,
    conversation: str,
    challenges: list[str]
) -> list[str]
```

**Purpose**: Define objetivos estrategicos BSC alinhados aos desafios identificados.

**Parameters**:
- `conversation` (str): Texto completo da conversacao. Deve conter mencoes a metas, objetivos, ou resultados desejados. Minimo 50 caracteres.
- `challenges` (list[str]): Lista de desafios ja identificados (output de `identify_challenges`)

**Returns**:
- `list[str]`: Lista de 3-7 objetivos estrategicos BSC. Cada objetivo tem 20-500 caracteres.

**Raises**:
- `ValidationError` (Pydantic): Se lista vazia ou objectives fora dos limites (min 3, max 7)
- `ValueError`: Se LLM retorna JSON invalido
- `TimeoutError`: Se LLM excede timeout (600s)
- `APIError` (OpenAI): Se API key invalida ou rate limit

**Pydantic Schemas**:
- `ObjectivesList`: Schema interno com validacao `min_length=3, max_length=7`

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
objectives = agent.define_objectives(
    conversation="Queremos aumentar retencao em 20% e reduzir custos operacionais em 15%.",
    challenges=["Baixa retencao de clientes", "Processos ineficientes"]
)

print(objectives)
# ["Aumentar retencao de clientes em 20%", "Reduzir custos operacionais em 15%", ...]
```

**Notes**:
- Objetivos devem ser SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Prompt system enfatiza alinhamento com challenges
- Retry automatico: 3 tentativas

---

### 1.4 ClientProfileAgent.process_onboarding

**Signature**:
```python
def process_onboarding(self, state: BSCState) -> dict[str, Any]
```

**Purpose**: Orquestra workflow completo de onboarding BSC em 3 steps progressivos.

**Parameters**:
- `state` (BSCState): Estado atual do workflow LangGraph com:
  - `query` (str): Input do usuario (conversacao ou comando)
  - `onboarding_progress` (dict): Tracking de progresso (steps 1-3)
  - `conversation_history` (list): Historico multi-turn

**Returns**:
- `dict[str, Any]`: Update parcial de BSCState com:
  - `onboarding_progress` (dict): Progresso atualizado
  - `response` (str): Mensagem para usuario (follow-up ou confirmacao)
  - `next_phase` (ConsultingPhase): ONBOARDING ou DISCOVERY (se completo)

**Raises**:
- `ValidationError` (Pydantic): Se state.query vazio ou invalido
- `ProfileNotFoundError`: Se tentou carregar profile inexistente do Mem0
- `Mem0APIError`: Se Mem0Client falha (network, auth, etc)

**Pydantic Schemas**:
- `BSCState`: Ver secao 7.3
- `ConsultingPhase`: Enum (IDLE, ONBOARDING, DISCOVERY, APPROVAL_PENDING)

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.graph.states import BSCState
from src.graph.consulting_states import ConsultingPhase

state = BSCState(
    query="Ola, gostaria de iniciar um diagnostico BSC.",
    phase=ConsultingPhase.ONBOARDING,
    onboarding_progress={}
)

result = agent.process_onboarding(state)

print(result["response"])  # "Para comecar, qual o nome da sua empresa?"
print(result["onboarding_progress"]["step"])  # 1
```

**Notes**:
- Workflow de 3 steps: (1) CompanyInfo, (2) Challenges, (3) Objectives
- Cada step chama metodos especificos: extract_company_info, identify_challenges, define_objectives
- Transiciona para DISCOVERY quando step 3 completo
- Usa conversation_history para contexto multi-turn

**Visual Reference**: Ver Diagrama 4 (Agent Interactions) em `DATA_FLOW_DIAGRAMS.md` para fluxo completo

---

### 1.5 ClientProfileAgent.extract_profile

**Signature**:
```python
def extract_profile(self, state: BSCState) -> ClientProfile
```

**Purpose**: Extrai/retorna ClientProfile a partir do estado atual. Se ja existir no estado, apenas retorna.

**Parameters**:
- `state` (BSCState): Estado atual do workflow com `onboarding_progress` completo

**Returns**:
- `ClientProfile`: Objeto Pydantic validado completo com:
  - `company` (CompanyInfo)
  - `context` (StrategicContext): challenges + objectives
  - `diagnostic_data` (dict): Vazio inicialmente
  - `engagement` (dict): Metadata de engajamento

**Raises**:
- `ValidationError` (Pydantic): Se onboarding_progress incompleto (steps 1-3 nao finalizados)
- `ValueError`: Se dados extraidos sao inconsistentes

**Pydantic Schemas**:
- `ClientProfile`: Ver secao 7.2
- `CompanyInfo`: Ver secao 7.1
- `StrategicContext`: Ver secao 7.2

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
# Apos onboarding completo
state_completo = BSCState(
    query="Finalizar onboarding",
    onboarding_progress={
        "step": 3,
        "company_info": {...},
        "challenges": [...],
        "objectives": [...]
    }
)

profile = agent.extract_profile(state_completo)

print(profile.company.name)  # "TechCorp"
print(len(profile.context.current_challenges))  # 3-7
```

**Notes**:
- Consolida informacoes de onboarding_progress em ClientProfile estruturado
- Se ClientProfile ja existir em state, retorna diretamente (evita reprocessamento)
- Profile e salvo automaticamente no Mem0 apos extracao

**Visual Reference**: Ver Diagrama 1 (ClientProfile Lifecycle) em `DATA_FLOW_DIAGRAMS.md`

---

## 2. OnboardingAgent

**Purpose**: Orquestrador conversacional multi-turn para fase ONBOARDING. Gerencia dialogo progressivo com cliente.

**Location**: `src/agents/onboarding_agent.py`

**LLM**: GPT-5 mini (via ClientProfileAgent)

**Visual Reference**: Ver Diagrama 4 (Agent Interactions) e Diagrama 5 (State Transitions) em `DATA_FLOW_DIAGRAMS.md`

---

### 2.1 OnboardingAgent.start_onboarding

**Signature**:
```python
def start_onboarding(self, user_id: str, state: BSCState) -> dict[str, Any]
```

**Purpose**: Inicia processo de onboarding com cliente. Primeira mensagem de boas-vindas.

**Parameters**:
- `user_id` (str): Identificador unico do cliente (usado para tracking multi-turn)
- `state` (BSCState): Estado inicial do workflow

**Returns**:
- `dict[str, Any]`: Update de BSCState com:
  - `response` (str): Mensagem de boas-vindas + primeira pergunta
  - `onboarding_progress` (dict): Inicializado com step=1
  - `conversation_history` (list): Primeiro turno registrado

**Raises**:
- `ValidationError` (Pydantic): Se user_id vazio ou state invalido

**Pydantic Schemas**:
- `BSCState`: Ver secao 7.3

**Added**: v1.0.0 (FASE 2.4)

**Example**:
```python
from src.agents.onboarding_agent import OnboardingAgent
from src.graph.states import BSCState

agent = OnboardingAgent(
    llm=get_llm("gpt-5-mini-2025-08-07"),
    client_profile_agent=ClientProfileAgent(llm=get_llm("gpt-5-mini-2025-08-07")),
    mem0_client=Mem0ClientWrapper()
)

state = BSCState(query="Iniciar onboarding")

result = agent.start_onboarding(user_id="user_123", state=state)

print(result["response"])
# "Ola! Bem-vindo ao diagnostico BSC. Para comecar, qual o nome da sua empresa?"
```

**Notes**:
- Cria sessao in-memory para tracking multi-turn
- Primeira mensagem e padronizada (nao usa LLM)
- Inicializa onboarding_progress com step=1 (COMPANY_INFO)

---

### 2.2 OnboardingAgent.process_turn

**Signature**:
```python
def process_turn(self, user_id: str, user_message: str, state: BSCState) -> dict[str, Any]
```

**Purpose**: Processa um turn da conversacao de onboarding. Follow-up inteligente quando informacoes incompletas.

**Parameters**:
- `user_id` (str): Identificador unico do cliente
- `user_message` (str): Mensagem do usuario neste turno
- `state` (BSCState): Estado atual do workflow

**Returns**:
- `dict[str, Any]`: Update de BSCState com:
  - `response` (str): Resposta do agente (follow-up ou confirmacao)
  - `onboarding_progress` (dict): Progresso atualizado (step 1-3)
  - `conversation_history` (list): Turno atual adicionado

**Raises**:
- `ValidationError` (Pydantic): Se user_message vazio ou state invalido
- `ValueError`: Se sessao onboarding nao encontrada (start_onboarding nao chamado)

**Pydantic Schemas**:
- `BSCState`: Ver secao 7.3

**Added**: v1.0.0 (FASE 2.4)

**Example**:
```python
# Turn 1: Usuario responde nome da empresa
result = agent.process_turn(
    user_id="user_123",
    user_message="Minha empresa e a TechCorp.",
    state=state
)

print(result["response"])
# "Otimo! Agora, em qual setor a TechCorp atua?"
print(result["onboarding_progress"]["step"])  # 1 (ainda coletando CompanyInfo)

# Turn 2: Usuario responde setor
result2 = agent.process_turn(
    user_id="user_123",
    user_message="Atuamos no setor de tecnologia.",
    state=state
)

print(result2["response"])
# "Perfeito! Qual o porte da sua empresa? (Pequena, Media, ou Grande)"
```

**Notes**:
- Usa ClientProfileAgent internamente para extracao progressiva
- Implementa follow-up inteligente: se informacao incompleta, faz nova pergunta
- Tracking de progresso: step 1 (CompanyInfo) → step 2 (Challenges) → step 3 (Objectives)
- Conversation_history acumula todos os turnos

---

### 2.3 OnboardingAgent.is_onboarding_complete

**Signature**:
```python
def is_onboarding_complete(self, state: BSCState) -> bool
```

**Purpose**: Verifica se onboarding esta completo (3 steps finalizados).

**Parameters**:
- `state` (BSCState): Estado atual do workflow

**Returns**:
- `bool`: True se onboarding completo (pode transicionar para DISCOVERY), False caso contrario

**Raises**:
- Nenhuma (metodo safe)

**Pydantic Schemas**:
- `BSCState`: Ver secao 7.3

**Added**: v1.0.0 (FASE 2.4)

**Example**:
```python
state_incompleto = BSCState(
    onboarding_progress={"step": 2, "company_info": {...}}
)

is_complete = agent.is_onboarding_complete(state_incompleto)
print(is_complete)  # False

state_completo = BSCState(
    onboarding_progress={
        "step": 3,
        "company_info": {...},
        "challenges": [...],
        "objectives": [...]
    }
)

is_complete2 = agent.is_onboarding_complete(state_completo)
print(is_complete2)  # True
```

**Notes**:
- Verifica se step == 3 E company_info, challenges, objectives preenchidos
- Usado pelo workflow para decidir transicao ONBOARDING → DISCOVERY

**Visual Reference**: Ver Diagrama 5 (State Transitions) em `DATA_FLOW_DIAGRAMS.md`

---

## 3. DiagnosticAgent

**Purpose**: Conduz diagnostico organizacional estruturado nas 4 perspectivas do Balanced Scorecard durante fase DISCOVERY.

**Location**: `src/agents/diagnostic_agent.py`

**LLM**: GPT-5 mini (cost-effective) + structured output

**Visual Reference**: Ver Diagrama 2 (Diagnostic Workflow) em `DATA_FLOW_DIAGRAMS.md`

---

### 3.1 DiagnosticAgent.analyze_perspective

**Signature**:
```python
def analyze_perspective(
    self,
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"],
    client_profile: ClientProfile,
    retrieval_context: str
) -> DiagnosticResult
```

**Purpose**: Analisa uma perspectiva BSC individual usando contexto do cliente e literatura BSC recuperada via RAG.

**Parameters**:
- `perspective` (Literal): Uma das 4 perspectivas BSC (validacao em compile-time)
- `client_profile` (ClientProfile): Contexto completo da empresa (company, challenges, objectives)
- `retrieval_context` (str): Documentos relevantes recuperados via RAG (chunks BSC literature)

**Returns**:
- `DiagnosticResult`: Objeto Pydantic validado com:
  - `perspective` (str): Nome da perspectiva analisada
  - `current_state` (str): Estado atual da empresa nesta perspectiva (min 20 chars)
  - `gaps` (list[str]): Gaps identificados (min 3 items, cada 20-500 chars)
  - `opportunities` (list[str]): Oportunidades de melhoria (min 3 items, cada 20-500 chars)
  - `kpis_suggested` (list[str]): KPIs sugeridos (opcional, 0-10 items)

**Raises**:
- `ValidationError` (Pydantic): Se DiagnosticResult invalido (campos fora dos limites)
- `ValueError`: Se LLM retorna JSON invalido
- `TimeoutError`: Se LLM excede timeout (600s)
- `APIError` (OpenAI): Se API key invalida ou rate limit

**Pydantic Schemas**:
- `DiagnosticResult`: Ver secao 7.5
- `ClientProfile`: Ver secao 7.2

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
from src.agents.diagnostic_agent import DiagnosticAgent
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

agent = DiagnosticAgent(llm=get_llm("gpt-5-mini-2025-08-07"))

profile = ClientProfile(
    company=CompanyInfo(name="TechCorp", sector="Tecnologia", size="Media"),
    context=StrategicContext(
        current_challenges=["Baixa retencao clientes"],
        strategic_objectives=["Aumentar retencao em 20%"]
    )
)

result = agent.analyze_perspective(
    perspective="Clientes",
    client_profile=profile,
    retrieval_context="[RAG chunks sobre perspectiva Cliente no BSC]"
)

print(result.current_state)  # "Empresa tem churn alto de 25% ao ano..."
print(len(result.gaps))  # >= 3
print(len(result.opportunities))  # >= 3
```

**Notes**:
- Usa prompt system especifico por perspectiva (4 prompts diferentes)
- Structured output Pydantic com validacao automatica
- Retry automatico: 3 tentativas
- Retrieval_context deve ter <= 32000 tokens (limite configurado)

---

### 3.2 DiagnosticAgent.consolidate_diagnostic

**Signature**:
```python
def consolidate_diagnostic(
    self,
    perspective_results: dict[str, DiagnosticResult],
) -> dict[str, Any]
```

**Purpose**: Consolida analises das 4 perspectivas identificando synergies cross-perspective e executive summary.

**Parameters**:
- `perspective_results` (dict): Mapa perspectiva → DiagnosticResult das 4 analises individuais

**Returns**:
- `dict[str, Any]`: Consolidacao com:
  - `synergies` (list[str]): Synergies identificadas entre perspectivas (min 2, max 5)
  - `executive_summary` (str): Resumo executivo do diagnostico (100-2000 chars)
  - `priority_areas` (list[str]): Areas prioritarias de atencao (min 2, max 4)

**Raises**:
- `ValidationError` (Pydantic): Se perspective_results incompleto (faltam perspectivas)
- `ValueError`: Se LLM retorna JSON invalido
- `TimeoutError`: Se LLM excede timeout (600s)

**Pydantic Schemas**:
- `DiagnosticResult`: Ver secao 7.5

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
perspective_results = {
    "Financeira": DiagnosticResult(...),
    "Clientes": DiagnosticResult(...),
    "Processos Internos": DiagnosticResult(...),
    "Aprendizado e Crescimento": DiagnosticResult(...)
}

consolidated = agent.consolidate_diagnostic(perspective_results)

print(consolidated["synergies"])
# ["Melhoria processos internos impacta diretamente satisfacao cliente",
#  "Investimento em aprendizado reduz custos operacionais"]

print(consolidated["executive_summary"])
# "Diagnostico identificou 3 areas criticas..."
```

**Notes**:
- Usa LLM para identificar conexoes entre perspectivas (pattern multi-agent)
- Synergies sao insights cross-perspective que não aparecem em analises isoladas
- Priority_areas sao top 2-4 focos recomendados

---

### 3.3 DiagnosticAgent.generate_recommendations

**Signature**:
```python
def generate_recommendations(
    self,
    perspective_results: dict[str, DiagnosticResult],
    consolidated: dict[str, Any],
) -> list[Recommendation]
```

**Purpose**: Gera recomendacoes priorizadas (impacto vs esforco) baseadas em diagnostico completo.

**Parameters**:
- `perspective_results` (dict): Mapa perspectiva → DiagnosticResult das 4 analises
- `consolidated` (dict): Resultado de consolidate_diagnostic com synergies

**Returns**:
- `list[Recommendation]`: Lista de 5-15 recomendacoes priorizadas. Cada recomendacao:
  - `title` (str): Titulo da recomendacao (10-200 chars)
  - `description` (str): Descricao detalhada (min 50 chars)
  - `impact` (Literal["HIGH", "MEDIUM", "LOW"]): Impacto esperado
  - `effort` (Literal["LOW", "MEDIUM", "HIGH"]): Esforco de implementacao
  - `priority` (int): Prioridade calculada (1 mais alta, N mais baixa)
  - `related_perspectives` (list[str]): Perspectivas BSC impactadas

**Raises**:
- `ValidationError` (Pydantic): Se recomendacoes invalidas (< 5 ou > 15, campos fora dos limites)
- `ValueError`: Se LLM retorna JSON invalido
- `TimeoutError`: Se LLM excede timeout (600s)

**Pydantic Schemas**:
- `Recommendation`: Ver secao 7.6

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
recommendations = agent.generate_recommendations(
    perspective_results=perspective_results,
    consolidated=consolidated
)

print(len(recommendations))  # 5-15

top_rec = recommendations[0]  # Priority 1
print(top_rec.title)  # "Implementar programa de fidelizacao clientes"
print(top_rec.impact)  # "HIGH"
print(top_rec.effort)  # "MEDIUM"
print(top_rec.related_perspectives)  # ["Clientes", "Financeira"]
```

**Notes**:
- Usa matriz impacto vs esforco para priorizacao
- Priority calculado automaticamente: HIGH impact + LOW effort = prioridade alta
- Recomendacoes incluem cross-references a perspectivas BSC impactadas
- Structured output Pydantic garante formato consistente

---

### 3.4 DiagnosticAgent.run_diagnostic

**Signature**:
```python
def run_diagnostic(
    self,
    state: BSCState,
) -> CompleteDiagnostic
```

**Purpose**: Orquestra diagnostico completo: analise paralela de 4 perspectivas + consolidacao + recomendacoes.

**Parameters**:
- `state` (BSCState): Estado atual do workflow com ClientProfile ja extraido

**Returns**:
- `CompleteDiagnostic`: Objeto Pydantic validado com:
  - `financial` (DiagnosticResult): Analise perspectiva Financeira
  - `customer` (DiagnosticResult): Analise perspectiva Clientes
  - `process` (DiagnosticResult): Analise perspectiva Processos Internos
  - `learning` (DiagnosticResult): Analise perspectiva Aprendizado e Crescimento
  - `synergies` (list[str]): Synergies cross-perspective
  - `executive_summary` (str): Resumo executivo
  - `recommendations` (list[Recommendation]): Lista de recomendacoes priorizadas

**Raises**:
- `ValidationError` (Pydantic): Se state.client_profile ausente ou invalido
- `ProfileNotFoundError`: Se ClientProfile nao encontrado no state
- `TimeoutError`: Se diagnostico excede timeout total (paralelo: ~600s)
- `asyncio.CancelledError`: Se alguma analise paralela e cancelada

**Pydantic Schemas**:
- `CompleteDiagnostic`: Ver secao 7.7
- `BSCState`: Ver secao 7.3
- `ClientProfile`: Ver secao 7.2

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
from src.graph.states import BSCState
from src.memory.schemas import ClientProfile

state = BSCState(
    client_profile=ClientProfile(...),  # Profile completo
    phase=ConsultingPhase.DISCOVERY
)

complete_diagnostic = agent.run_diagnostic(state)

print(complete_diagnostic.financial.current_state)
print(len(complete_diagnostic.recommendations))  # 5-15
print(complete_diagnostic.executive_summary)
```

**Notes**:
- Analise das 4 perspectivas e executada em PARALELO via AsyncIO (economia ~3x tempo)
- Ordem de execucao: (1) Analise paralela 4 perspectivas, (2) Consolidacao cross-perspective, (3) Geracao recomendacoes
- Usa specialist agents internamente (Financial, Customer, Process, Learning)
- Resultado completo e salvo automaticamente em state.diagnostic
- Transiciona automaticamente para APPROVAL_PENDING apos conclusao

**Visual Reference**: Ver Diagrama 2 (Diagnostic Workflow) em `DATA_FLOW_DIAGRAMS.md` para fluxo completo paralelo

---

## 4. Specialist Agents

**Purpose**: Agentes especializados em cada perspectiva BSC (Financeira, Clientes, Processos Internos, Aprendizado e Crescimento). Usados para RAG tradicional e analise diagnostica.

**Location**: 
- `src/agents/financial_agent.py`
- `src/agents/customer_agent.py`
- `src/agents/process_agent.py`
- `src/agents/learning_agent.py`

**LLM**: GPT-5 (gpt-5-2025-08-07) com reasoning_effort="high"

**Shared Signature**: Todos os 4 agentes compartilham mesma interface `invoke()`

**Visual Reference**: Ver Diagrama 2 (Diagnostic Workflow) em `DATA_FLOW_DIAGRAMS.md` para uso em analise paralela

---

### 4.1 SpecialistAgent.invoke (Compartilhado)

**Signature**:
```python
def invoke(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]
```

**Purpose**: Processa uma query sobre a perspectiva BSC especifica do agente. Usa RAG para recuperar documentos relevantes e LLM para gerar resposta contextualizada.

**Parameters**:
- `query` (str): Pergunta do usuario sobre a perspectiva BSC
- `chat_history` (List[Dict[str, str]], optional): Historico de conversacao para contexto multi-turn. Formato: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

**Returns**:
- `Dict[str, Any]`: Resposta estruturada com:
  - `response` (str): Resposta do agente em texto
  - `context` (List[str]): Documentos recuperados via RAG (top-10)
  - `metadata` (Dict): Metadata adicional (latencia, tokens, etc)
  - `agent_name` (str): Nome do agente (ex: "Financial Agent")
  - `perspective` (str): Perspectiva BSC (ex: "Financeira")

**Raises**:
- `ValueError`: Se query vazia
- `TimeoutError`: Se LLM excede timeout (600s)
- `APIError` (OpenAI): Se API key invalida ou rate limit
- `RetrievalError`: Se RAG falha ao recuperar documentos

**Pydantic Schemas**:
- Nenhum (retorna dict plain)

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
from src.agents.financial_agent import FinancialAgent

agent = FinancialAgent()

result = agent.invoke(
    query="Quais sao os principais KPIs financeiros recomendados por Kaplan e Norton?",
    chat_history=None
)

print(result["response"])
# "De acordo com Kaplan e Norton, os principais KPIs financeiros incluem ROI, crescimento de receita, margem operacional..."

print(len(result["context"]))  # 10 documentos recuperados
print(result["perspective"])  # "Financeira"
```

**Notes**:
- Cada agente tem retriever especializado filtrado por perspectiva BSC
- FinancialAgent: foca metricas financeiras, ROI, lucratividade
- CustomerAgent: foca experiencia cliente, satisfacao, retencao
- ProcessAgent: foca eficiencia processos, qualidade, inovacao
- LearningAgent: foca capital humano, cultura, aprendizado organizacional
- Usa Cohere Rerank para refinar top-10 docs mais relevantes
- Timeout configurado em 600s (10 minutos) para queries complexas

**Differences by Perspective**:

| Agente | Perspectiva BSC | Foco Principal | Exemplos KPIs |
|---|---|---|---|
| FinancialAgent | Financeira | Metricas financeiras, ROI, custos | ROI, crescimento receita, margem operacional |
| CustomerAgent | Clientes | Experiencia cliente, satisfacao, retencao | NPS, churn rate, CSAT |
| ProcessAgent | Processos Internos | Eficiencia, qualidade, inovacao | Tempo ciclo, taxa defeitos, throughput |
| LearningAgent | Aprendizado e Crescimento | Capital humano, cultura, aprendizado | Horas treinamento, engagement, turnover |

---

### 4.2 SpecialistAgent.get_perspective

**Signature**:
```python
def get_perspective(self) -> str
```

**Purpose**: Retorna a perspectiva BSC do agente.

**Parameters**: Nenhum

**Returns**:
- `str`: Nome da perspectiva ("Financeira", "Clientes", "Processos Internos", ou "Aprendizado e Crescimento")

**Raises**: Nenhum (metodo safe)

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
agent = FinancialAgent()
print(agent.get_perspective())  # "Financeira"
```

---

### 4.3 SpecialistAgent.get_name

**Signature**:
```python
def get_name(self) -> str
```

**Purpose**: Retorna o nome do agente.

**Parameters**: Nenhum

**Returns**:
- `str`: Nome do agente ("Financial Agent", "Customer Agent", "Process Agent", ou "Learning Agent")

**Raises**: Nenhum (metodo safe)

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
agent = FinancialAgent()
print(agent.get_name())  # "Financial Agent"
```

---

## 5. ConsultingOrchestrator

**Purpose**: Coordenador dos agentes especialistas para RAG tradicional (workflow original MVP). Roteia queries, invoca agentes, sintetiza respostas multi-agente.

**Location**: `src/agents/orchestrator.py`

**LLM**: GPT-5 mini para routing, GPT-4o para sintese

**Visual Reference**: Ver Diagrama 4 (Agent Interactions) em `DATA_FLOW_DIAGRAMS.md`

---

### 5.1 ConsultingOrchestrator.route_query

**Signature**:
```python
def route_query(self, query: str) -> RoutingDecision
```

**Purpose**: Determina quais agentes especialistas devem processar a query. Usa heuristicas + LLM para decisao inteligente.

**Parameters**:
- `query` (str): Pergunta do usuario

**Returns**:
- `RoutingDecision`: Objeto Pydantic com:
  - `agents_to_use` (List[str]): Lista de perspectivas a acionar ("financeira", "cliente", "processos", "aprendizado")
  - `reasoning` (str): Justificativa da escolha dos agentes
  - `is_general_question` (bool): Se e pergunta geral sobre BSC (acionar todos 4 agentes)

**Raises**:
- `ValueError`: Se query vazia
- `ValidationError` (Pydantic): Se RoutingDecision invalido

**Pydantic Schemas**:
- `RoutingDecision`: Schema interno do orchestrator

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
from src.agents.orchestrator import ConsultingOrchestrator

orchestrator = ConsultingOrchestrator()

decision = orchestrator.route_query("Como melhorar a retencao de clientes?")

print(decision.agents_to_use)  # ["cliente", "financeira"]
print(decision.reasoning)  # "Query foca em retencao clientes (perspectiva Cliente) com impacto em receita (perspectiva Financeira)"
print(decision.is_general_question)  # False
```

**Notes**:
- Usa Query Router interno (ver ROUTER.md) para classificacao inicial
- Heuristicas: palavras-chave por perspectiva (ex: "retencao" → cliente, "ROI" → financeira)
- Fallback LLM: se heuristicas incertas, usa GPT-5 mini para classificacao
- Queries gerais (ex: "O que e BSC?") acionam todos 4 agentes

---

### 5.2 ConsultingOrchestrator.invoke_agents

**Signature**:
```python
def invoke_agents(
    self,
    query: str,
    agent_names: List[str],
    chat_history: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, Any]]
```

**Purpose**: Invoca agentes especialistas selecionados em paralelo (AsyncIO ou ThreadPoolExecutor).

**Parameters**:
- `query` (str): Pergunta do usuario
- `agent_names` (List[str]): Lista de agentes a acionar ("financeira", "cliente", "processos", "aprendizado")
- `chat_history` (Optional[List[Dict[str, str]]]): Historico de conversacao para contexto

**Returns**:
- `List[Dict[str, Any]]`: Lista de respostas dos agentes invocados. Cada resposta:
  - `response` (str): Resposta do agente
  - `agent_name` (str): Nome do agente
  - `perspective` (str): Perspectiva BSC
  - `context` (List[str]): Documentos recuperados
  - `metadata` (Dict): Metadata (latencia, tokens)

**Raises**:
- `ValueError`: Se agent_names vazio ou contem nomes invalidos
- `TimeoutError`: Se algum agente excede timeout (600s)
- `Exception`: Se algum agente falha (capturado e logged, nao relancado)

**Pydantic Schemas**: Nenhum

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
agent_responses = orchestrator.invoke_agents(
    query="Como melhorar retencao?",
    agent_names=["cliente", "financeira"],
    chat_history=None
)

print(len(agent_responses))  # 2
print(agent_responses[0]["agent_name"])  # "Customer Agent"
print(agent_responses[1]["agent_name"])  # "Financial Agent"
```

**Notes**:
- Invocacao paralela: ThreadPoolExecutor para simultaneidade
- Se algum agente falha, continua com agentes restantes (fault-tolerant)
- Cada agente executa RAG independente na sua perspectiva
- Logs detalhados para debugging (latencia por agente, tokens, etc)

---

### 5.3 ConsultingOrchestrator.synthesize_responses

**Signature**:
```python
def synthesize_responses(
    self,
    original_query: str,
    agent_responses: List[Dict[str, Any]]
) -> str
```

**Purpose**: Combina e sintetiza respostas de multiplos agentes em resposta unificada e coerente.

**Parameters**:
- `original_query` (str): Pergunta original do usuario
- `agent_responses` (List[Dict[str, Any]]): Respostas dos agentes (output de invoke_agents)

**Returns**:
- `str`: Resposta sintetizada combinando insights de multiplos agentes. Texto coerente e bem estruturado.

**Raises**:
- `ValidationError` (Pydantic): Se agent_responses vazio ou invalido
- `TimeoutError`: Se sintese excede timeout (600s)
- `APIError` (OpenAI): Se API key invalida ou rate limit

**Pydantic Schemas**: Nenhum (input/output plain types)

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
agent_responses = [
    {"response": "Cliente: Retencao pode ser melhorada via programa fidelidade...", ...},
    {"response": "Financeira: Retencao impacta diretamente LTV e ROI...", ...}
]

synthesized = orchestrator.synthesize_responses(
    original_query="Como melhorar retencao?",
    agent_responses=agent_responses
)

print(synthesized)
# "Para melhorar a retencao de clientes, considerando as perspectivas de Clientes e Financeira:
#  1. Implementar programa de fidelidade... 
#  2. Impacto financeiro esperado: aumento de 15-20% no LTV..."
```

**Notes**:
- Usa GPT-4o (modelo mais capaz) com temperature 0.1 para sintese precisa
- Prompt system instrui: evitar repeticao, manter coerencia, destacar synergies
- Timeout 600s (sintese pode processar grandes inputs de 4 agentes)
- Logs completos: tamanho input (~X tokens), tempo decorrido, confidence

---

### 5.4 ConsultingOrchestrator.process_query

**Signature**:
```python
def process_query(
    self,
    query: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    use_judge: bool = False
) -> Dict[str, Any]
```

**Purpose**: Orquestra workflow completo RAG tradicional: routing → invocacao → sintese (→ judge opcional).

**Parameters**:
- `query` (str): Pergunta do usuario
- `chat_history` (Optional[List[Dict[str, str]]]): Historico de conversacao para contexto
- `use_judge` (bool): Se True, usa JudgeAgent para avaliar qualidade da resposta final

**Returns**:
- `Dict[str, Any]`: Resposta completa com:
  - `response` (str): Resposta sintetizada final
  - `routing_decision` (Dict): Decisao de routing (agentes escolhidos, reasoning)
  - `agent_responses` (List[Dict]): Respostas individuais dos agentes
  - `metadata` (Dict): Metadata completa (latencia total, tokens, etc)
  - `judge_evaluation` (Dict, optional): Avaliacao do Judge (se use_judge=True)

**Raises**:
- `ValueError`: Se query vazia
- `TimeoutError`: Se workflow excede timeout total
- `Exception`: Erros gerais (logged mas nao relancados, retorna erro em metadata)

**Pydantic Schemas**: Nenhum (dict plain)

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
result = orchestrator.process_query(
    query="Como implementar BSC em empresa de tecnologia?",
    chat_history=None,
    use_judge=True
)

print(result["response"])
# "Para implementar BSC em empresa de tecnologia, considerando as 4 perspectivas..."

print(result["routing_decision"]["agents_to_use"])  # ["financeira", "cliente", "processos", "aprendizado"]

print(result["judge_evaluation"]["approved"])  # True
print(result["judge_evaluation"]["score"])  # 0.92
```

**Notes**:
- Workflow completo: (1) Routing, (2) Invocacao paralela, (3) Sintese, (4) Judge (opcional)
- Metadata inclui: latencia por etapa, tokens gastos, agentes acionados
- Fault-tolerant: se alguma etapa falha, retorna erro em metadata mas nao crashea
- Logs estruturados em JSON para analytics

**Visual Reference**: Ver Diagrama 4 (Agent Interactions) em `DATA_FLOW_DIAGRAMS.md` para fluxo completo

---

## 6. JudgeAgent

**Purpose**: Avaliacao de qualidade das respostas geradas pelos agentes. Valida precisao factual, relevancia, e completude.

**Location**: `src/agents/judge_agent.py`

**LLM**: GPT-5 mini (cost-effective para evaluation)

**Visual Reference**: Ver Diagrama 4 (Agent Interactions) em `DATA_FLOW_DIAGRAMS.md`

---

### 6.1 JudgeAgent.evaluate

**Signature**:
```python
def evaluate(
    self,
    original_query: str,
    agent_response: str,
    context: Optional[List[str]] = None
) -> Dict[str, Any]
```

**Purpose**: Avalia qualidade de uma resposta individual de agente.

**Parameters**:
- `original_query` (str): Pergunta original do usuario
- `agent_response` (str): Resposta do agente a ser avaliada
- `context` (Optional[List[str]]): Documentos RAG usados (para validar precisao factual)

**Returns**:
- `Dict[str, Any]`: Avaliacao com:
  - `approved` (bool): Se resposta aprovada (score >= threshold)
  - `score` (float): Score de qualidade (0.0 a 1.0)
  - `feedback` (str): Feedback detalhado sobre a resposta
  - `criteria_scores` (Dict[str, float]): Scores por criterio (relevancia, precisao, completude)

**Raises**:
- `ValueError`: Se original_query ou agent_response vazios
- `TimeoutError`: Se evaluation excede timeout (180s)

**Pydantic Schemas**: Nenhum (dict plain)

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
from src.agents.judge_agent import JudgeAgent

judge = JudgeAgent()

evaluation = judge.evaluate(
    original_query="Quais os KPIs financeiros do BSC?",
    agent_response="Os principais KPIs financeiros incluem ROI, crescimento de receita...",
    context=["[DOC 1: Kaplan & Norton sobre KPIs financeiros]"]
)

print(evaluation["approved"])  # True
print(evaluation["score"])  # 0.88
print(evaluation["feedback"])  # "Resposta precisa e completa. Cita corretamente Kaplan & Norton..."
```

**Notes**:
- Criterios de avaliacao: (1) Relevancia a query, (2) Precisao factual vs context, (3) Completude, (4) Clareza
- Threshold de aprovacao: score >= 0.7 (configuravel)
- Timeout 180s (evaluation e mais rapida que geracao)

---

### 6.2 JudgeAgent.evaluate_multiple

**Signature**:
```python
def evaluate_multiple(
    self,
    original_query: str,
    agent_responses: List[Dict[str, Any]],
) -> Dict[str, Any]
```

**Purpose**: Avalia qualidade de multiplas respostas (output de invoke_agents). Retorna melhor resposta e ranking.

**Parameters**:
- `original_query` (str): Pergunta original do usuario
- `agent_responses` (List[Dict[str, Any]]): Lista de respostas dos agentes (output de invoke_agents)

**Returns**:
- `Dict[str, Any]`: Avaliacao agregada com:
  - `best_response` (Dict): Resposta com maior score
  - `ranking` (List[Dict]): Respostas ordenadas por score (melhor primeiro)
  - `average_score` (float): Score medio de todas respostas
  - `all_approved` (bool): Se todas respostas aprovadas

**Raises**:
- `ValueError`: Se agent_responses vazio
- `TimeoutError`: Se evaluation excede timeout (180s * N respostas)

**Pydantic Schemas**: Nenhum

**Added**: v1.0.0 (FASE 1.0 MVP)

**Example**:
```python
agent_responses = [
    {"response": "...", "agent_name": "Financial Agent", "context": [...]},
    {"response": "...", "agent_name": "Customer Agent", "context": [...]}
]

evaluation = judge.evaluate_multiple(
    original_query="Como melhorar retencao?",
    agent_responses=agent_responses
)

print(evaluation["best_response"]["agent_name"])  # "Customer Agent"
print(evaluation["average_score"])  # 0.85
print(evaluation["all_approved"])  # True
```

**Notes**:
- Avalia cada resposta individualmente e depois agrega
- Useful para debug: identificar qual agente gerou melhor resposta
- Timeout linear: 180s * N respostas (pode ser longo para 4 agentes)

---

## 7. Pydantic Schemas Reference

Esta secao documenta os principais schemas Pydantic usados pelos agentes. Para definicoes completas, ver `src/memory/schemas.py` e `src/graph/states.py`.

---

### 7.1 CompanyInfo

**Location**: `src/memory/schemas.py`

**Purpose**: Informacoes basicas da empresa extraidas durante onboarding.

**Fields**:
- `name` (str): Nome da empresa (1-200 chars)
- `sector` (str): Setor de atuacao (1-100 chars)
- `size` (Literal["Pequena", "Media", "Grande"]): Porte da empresa

**Validators**:
- `name`: min_length=1, max_length=200
- `sector`: min_length=1, max_length=100
- `size`: Literal validation (apenas 3 valores permitidos)

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.memory.schemas import CompanyInfo

company = CompanyInfo(
    name="TechCorp",
    sector="Tecnologia",
    size="Media"
)
```

---

### 7.2 StrategicContext

**Location**: `src/memory/schemas.py`

**Purpose**: Contexto estrategico da empresa (desafios e objetivos).

**Fields**:
- `current_challenges` (list[str]): Desafios estrategicos (3-7 items, cada 20-500 chars)
- `strategic_objectives` (list[str]): Objetivos estrategicos (3-7 items, cada 20-500 chars)

**Validators**:
- `current_challenges`: min_length=3, max_length=7, cada item min 20 chars
- `strategic_objectives`: min_length=3, max_length=7, cada item min 20 chars

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.memory.schemas import StrategicContext

context = StrategicContext(
    current_challenges=[
        "Baixa retencao de clientes",
        "Processos internos ineficientes",
        "Falta de cultura de inovacao"
    ],
    strategic_objectives=[
        "Aumentar retencao em 20%",
        "Reduzir custos operacionais em 15%",
        "Implementar programa de inovacao"
    ]
)
```

---

### 7.3 ClientProfile

**Location**: `src/memory/schemas.py`

**Purpose**: Profile completo do cliente consolidando todas informacoes de onboarding.

**Fields**:
- `client_id` (str): Identificador unico do cliente (UUID ou user_id)
- `company` (CompanyInfo): Informacoes da empresa
- `context` (StrategicContext): Contexto estrategico (challenges + objectives)
- `diagnostic_data` (dict): Dados de diagnostico (vazio inicialmente, preenchido em DISCOVERY)
- `engagement` (dict): Metadata de engajamento (created_at, updated_at, phase)
- `complete_diagnostic` (Optional[Dict]): Diagnostico BSC completo (None ate DISCOVERY finalizado)

**Validators**:
- `client_id`: min_length=1
- `company`: CompanyInfo valido
- `context`: StrategicContext valido
- `diagnostic_data`: dict (default {})
- `engagement`: dict (default {})

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

profile = ClientProfile(
    client_id="user_123",
    company=CompanyInfo(...),
    context=StrategicContext(...),
    diagnostic_data={},
    engagement={"created_at": "2025-10-19", "phase": "DISCOVERY"}
)
```

**Visual Reference**: Ver Diagrama 1 (ClientProfile Lifecycle) e Diagrama 3 (Schema Dependencies) em `DATA_FLOW_DIAGRAMS.md`

---

### 7.4 BSCState

**Location**: `src/graph/states.py`

**Purpose**: Estado global do workflow LangGraph. Rastreia progresso completo do cliente atraves das fases consultivas.

**Fields**:
- `query` (str): Input do usuario no turno atual (obrigatorio, sem default)
- `phase` (ConsultingPhase): Fase atual do workflow (IDLE, ONBOARDING, DISCOVERY, APPROVAL_PENDING)
- `client_profile` (Optional[ClientProfile]): Profile do cliente (None ate onboarding completo)
- `onboarding_progress` (dict): Tracking de progresso onboarding (steps 1-3)
- `conversation_history` (list): Historico multi-turn
- `diagnostic` (Optional[CompleteDiagnostic]): Diagnostico BSC completo (None ate DISCOVERY completo)
- `response` (str): Resposta para usuario (gerada pelos agentes)

**Validators**:
- `query`: obrigatorio (sem default), min_length=1
- `phase`: ConsultingPhase enum
- `onboarding_progress`: dict (default_factory=dict)
- `conversation_history`: list (default_factory=list)

**Added**: v1.0.0 (FASE 2.3)

**Example**:
```python
from src.graph.states import BSCState
from src.graph.consulting_states import ConsultingPhase

state = BSCState(
    query="Ola, gostaria de iniciar diagnostico BSC.",
    phase=ConsultingPhase.IDLE,
    client_profile=None,
    onboarding_progress={},
    conversation_history=[],
    response=""
)
```

**Visual Reference**: Ver Diagrama 5 (State Transitions) em `DATA_FLOW_DIAGRAMS.md`

---

### 7.5 DiagnosticResult

**Location**: `src/memory/schemas.py`

**Purpose**: Resultado de analise de uma perspectiva BSC individual.

**Fields**:
- `perspective` (str): Nome da perspectiva analisada
- `current_state` (str): Estado atual da empresa nesta perspectiva (min 20 chars)
- `gaps` (list[str]): Gaps identificados (min 3 items, cada 20-500 chars)
- `opportunities` (list[str]): Oportunidades de melhoria (min 3 items, cada 20-500 chars)
- `kpis_suggested` (list[str]): KPIs sugeridos (0-10 items, opcional)

**Validators**:
- `current_state`: min_length=20
- `gaps`: min_length=3, cada item 20-500 chars
- `opportunities`: min_length=3, cada item 20-500 chars
- `kpis_suggested`: max_length=10

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
from src.memory.schemas import DiagnosticResult

result = DiagnosticResult(
    perspective="Clientes",
    current_state="Empresa tem churn alto de 25% ao ano, NPS de 45 (zona neutra)...",
    gaps=[
        "Falta programa de fidelizacao estruturado",
        "Ausencia de metricas de satisfacao em tempo real",
        "Canais de feedback limitados"
    ],
    opportunities=[
        "Implementar NPS transacional em pontos de contato criticos",
        "Criar programa de recompensas para clientes recorrentes",
        "Estabelecer Customer Success team dedicado"
    ],
    kpis_suggested=["NPS", "Churn rate", "Customer Lifetime Value"]
)
```

---

### 7.6 Recommendation

**Location**: `src/memory/schemas.py`

**Purpose**: Recomendacao priorizada de acao baseada em diagnostico.

**Fields**:
- `title` (str): Titulo da recomendacao (10-200 chars)
- `description` (str): Descricao detalhada (min 50 chars)
- `impact` (Literal["HIGH", "MEDIUM", "LOW"]): Impacto esperado
- `effort` (Literal["LOW", "MEDIUM", "HIGH"]): Esforco de implementacao
- `priority` (int): Prioridade calculada (1 mais alta, N mais baixa)
- `related_perspectives` (list[str]): Perspectivas BSC impactadas (1-4 items)

**Validators**:
- `title`: min_length=10, max_length=200
- `description`: min_length=50
- `impact`: Literal["HIGH", "MEDIUM", "LOW"]
- `effort`: Literal["LOW", "MEDIUM", "HIGH"]
- `priority`: int >= 1
- `related_perspectives`: min_length=1, max_length=4

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
from src.memory.schemas import Recommendation

rec = Recommendation(
    title="Implementar programa de fidelizacao clientes",
    description="Criar programa de recompensas para clientes recorrentes com pontos e beneficios exclusivos...",
    impact="HIGH",
    effort="MEDIUM",
    priority=1,
    related_perspectives=["Clientes", "Financeira"]
)
```

---

### 7.7 CompleteDiagnostic

**Location**: `src/memory/schemas.py`

**Purpose**: Diagnostico BSC completo consolidando analises de todas 4 perspectivas + synergies + recomendacoes.

**Fields**:
- `financial` (DiagnosticResult): Analise perspectiva Financeira
- `customer` (DiagnosticResult): Analise perspectiva Clientes
- `process` (DiagnosticResult): Analise perspectiva Processos Internos
- `learning` (DiagnosticResult): Analise perspectiva Aprendizado e Crescimento
- `synergies` (list[str]): Synergies cross-perspective (2-5 items)
- `executive_summary` (str): Resumo executivo (100-2000 chars)
- `recommendations` (list[Recommendation]): Lista de recomendacoes priorizadas (5-15 items)

**Validators**:
- `synergies`: min_length=2, max_length=5
- `executive_summary`: min_length=100, max_length=2000
- `recommendations`: min_length=5, max_length=15

**Added**: v1.0.0 (FASE 2.5)

**Example**:
```python
from src.memory.schemas import CompleteDiagnostic, DiagnosticResult, Recommendation

diagnostic = CompleteDiagnostic(
    financial=DiagnosticResult(...),
    customer=DiagnosticResult(...),
    process=DiagnosticResult(...),
    learning=DiagnosticResult(...),
    synergies=[
        "Melhoria processos internos impacta diretamente satisfacao cliente",
        "Investimento em aprendizado reduz custos operacionais"
    ],
    executive_summary="Diagnostico identificou 3 areas criticas...",
    recommendations=[Recommendation(...), ...]  # 5-15 items
)
```

**Visual Reference**: Ver Diagrama 2 (Diagnostic Workflow) e Diagrama 3 (Schema Dependencies) em `DATA_FLOW_DIAGRAMS.md`

---

## 8. Changelog

### v1.0.0 (2025-10-15) - FASE 2 Baseline

**Added**:
- ClientProfileAgent: 5 metodos publicos (extract_company_info, identify_challenges, define_objectives, process_onboarding, extract_profile)
- OnboardingAgent: 3 metodos publicos (start_onboarding, process_turn, is_onboarding_complete)
- DiagnosticAgent: 4 metodos publicos (analyze_perspective, consolidate_diagnostic, generate_recommendations, run_diagnostic)
- Specialist Agents (4): 3 metodos compartilhados (invoke, get_perspective, get_name)
- ConsultingOrchestrator: 5 metodos publicos (route_query, invoke_agents, synthesize_responses, process_query, get_name)
- JudgeAgent: 3 metodos publicos (evaluate, evaluate_multiple, get_name)
- Pydantic Schemas: 7 schemas principais (CompanyInfo, StrategicContext, ClientProfile, BSCState, DiagnosticResult, Recommendation, CompleteDiagnostic)

**Breaking Changes**: Nenhum (versao inicial)

**Deprecated**: Nenhum

**Notes**:
- Todos os metodos usam type hints completos (Python 3.10+)
- Validacao Pydantic em todos os inputs/outputs estruturados
- Retry automatico em operacoes LLM (3 tentativas, exponential backoff)
- Timeouts configurados: LLM 600s, Judge 180s
- Logs estruturados para debugging e analytics

---

### v1.1.0 (Futuro - FASE 3) - Planejado

**Planned Additions**:
- DiagnosticAgent.run_swot_analysis(): Analise SWOT estruturada
- DiagnosticAgent.run_five_whys(): Analise 5 Whys para root cause
- DiagnosticAgent.suggest_kpis(): Sugestao de KPIs customizados
- ConsultingOrchestrator.coordinate_onboarding(): Orquestracao onboarding (transferido de OnboardingAgent)
- ConsultingOrchestrator.coordinate_discovery(): Orquestracao discovery (transferido de DiagnosticAgent)

**Planned Breaking Changes**: Nenhum (apenas adições)

**Planned Deprecated**: Nenhum

---

## CROSS-REFERENCES

### API Contracts ↔ Data Flow Diagrams

- **ClientProfileAgent.extract_company_info**: Ver Diagrama 1 (ClientProfile Lifecycle) para fluxo Mem0 save/load
- **ClientProfileAgent.process_onboarding**: Ver Diagrama 4 (Agent Interactions) para workflow completo onboarding
- **OnboardingAgent.start_onboarding**: Ver Diagrama 4 (Agent Interactions) e Diagrama 5 (State Transitions) para fluxo multi-turn
- **DiagnosticAgent.run_diagnostic**: Ver Diagrama 2 (Diagnostic Workflow) para paralelismo AsyncIO 4 perspectivas
- **SpecialistAgent.invoke**: Ver Diagrama 2 (Diagnostic Workflow) para uso em analise paralela
- **ConsultingOrchestrator.process_query**: Ver Diagrama 4 (Agent Interactions) para fluxo RAG tradicional completo
- **BSCState**: Ver Diagrama 5 (State Transitions) para transicoes de fase
- **ClientProfile**: Ver Diagrama 1 (ClientProfile Lifecycle) e Diagrama 3 (Schema Dependencies) para lifecycle completo
- **CompleteDiagnostic**: Ver Diagrama 2 (Diagnostic Workflow) e Diagrama 3 (Schema Dependencies) para estrutura completa

---

## BEST PRACTICES APLICADAS

### 1. Type Safety (Pydantic AI Framework)

- **Fonte**: DataCamp Sep 2025, Speakeasy Sep 2024
- **Aplicacao**: Todos os metodos usam type hints completos + Pydantic models para runtime validation
- **Beneficio**: Erros capturados em desenvolvimento (mypy/pyright) e runtime (Pydantic ValidationError)

### 2. OpenAPI-Style Documentation

- **Fonte**: Speakeasy Sep 2024
- **Aplicacao**: Formato Signature → Parameters → Returns → Raises → Example
- **Beneficio**: Documentacao clara e consistente, similar a OpenAPI specs

### 3. Semantic Versioning

- **Fonte**: DeepDocs Oct 2025
- **Aplicacao**: Versionamento v1.0.0 (MAJOR.MINOR.PATCH), changelog estruturado
- **Beneficio**: Breaking changes claramente comunicados, migracoes facilitadas

### 4. Error Handling Comprehensive

- **Fonte**: DEV Community Jul 2024
- **Aplicacao**: Documentacao completa de todas excecoes esperadas por metodo
- **Beneficio**: Previne bugs de exceções não tratadas (40% bugs Sessão 14)

### 5. Structured Output Validation

- **Fonte**: Pydantic AI Framework (oficial)
- **Aplicacao**: Todos os outputs LLM validados por Pydantic models
- **Beneficio**: Formato consistente, sem parsing manual JSON

---

## NOTAS TECNICAS

### LLMs Utilizados

- **GPT-5 mini**: ClientProfileAgent, OnboardingAgent, DiagnosticAgent, ConsultingOrchestrator (routing), JudgeAgent
  - Cost-effective para tarefas simples (extracao, classificacao, avaliacao)
  - Temperature 0.1 (precisao maxima)
  
- **GPT-5 (gpt-5-2025-08-07)**: Specialist Agents (Financial, Customer, Process, Learning)
  - Reasoning_effort="high" para analise profunda
  - Max_completion_tokens=128000 (outputs longos)
  
- **GPT-4o**: ConsultingOrchestrator (sintese multi-agente)
  - Temperature 0.1 para sintese precisa
  - Max_tokens=64000

### Timeouts Configurados

- **LLM Operations**: 600s (10 minutos) - queries complexas, diagnosticos, sintese
- **Judge Evaluation**: 180s (3 minutos) - avaliacao mais rapida
- **Parallel Execution**: AsyncIO sem timeout global (timeout individual por agente)

### Retry Policies

- **Tenacity**: 3 tentativas com exponential backoff (2^n segundos)
- **Retry_if_exception_type**: ValidationError, APIError, TimeoutError (temporarios)
- **No Retry**: ValueError, ProfileNotFoundError (erros permanentes)

### AsyncIO Patterns

- **Diagnostic Workflow**: 4 perspectivas em paralelo via `asyncio.gather()`
- **Orchestrator**: ThreadPoolExecutor para specialist agents (paralelismo multi-thread)
- **Benefit**: 3-4x speedup vs execucao sequencial

---

## CONTATO E SUPORTE

- **Documentacao Completa**: Ver `docs/` directory
- **Data Flow Diagrams**: Ver `docs/architecture/DATA_FLOW_DIAGRAMS.md`
- **Testes**: Ver `tests/` directory (351 testes, 99.4% success rate)
- **Issues**: Reportar em GitHub issues (quando disponivel)

**Ultima Atualizacao**: 2025-10-19 (v1.0.0)
**Proxima Revisao**: FASE 3 (adicao de SWOT, 5 Whys, KPIs customizados)

