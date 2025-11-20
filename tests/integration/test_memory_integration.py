"""Testes de integração E2E para memória persistente Mem0.

OBJETIVO (FASE 1.8):
Validar integração completa entre LangGraph workflow e Mem0 Platform,
incluindo criação, carregamento, atualização e persistência de ClientProfile.

ESCOPO DOS TESTES:
1. Criação de profile novo (primeiro uso)
2. Carregamento de profile existente
3. Atualização de engagement state (progressão workflow)
4. Verificação de persistência real no Mem0
5. Fluxo E2E completo (onboarding -> delivery)

SETUP REQUERIDO:
- MEM0_API_KEY configurado em .env
- Fixtures: test_user_id, mem0_client, cleanup_test_profile
- Cleanup automático de profiles de teste

FASE: 1.8 | PRIORITY: P0 | COVERAGE TARGET: 90%+
"""

import time

from src.graph.memory_nodes import (
    create_placeholder_profile,
    load_client_memory,
    save_client_memory,
)
from src.graph.states import BSCState
from src.memory.schemas import ClientProfile, CompanyInfo, EngagementState, StrategicContext

# ============================================================================
# ETAPA 2: Test New Client Creates Profile
# ============================================================================


def test_new_client_creates_profile(cleanup_test_profile):
    """Valida que cliente novo cria profile do zero no Mem0.

    Cenário:
    1. user_id novo (não existe no Mem0)
    2. load_client_memory retorna None (cliente novo)
    3. Criar profile placeholder manualmente
    4. save_client_memory persiste no Mem0
    5. Profile é recuperável via load_client_memory

    Args:
        cleanup_test_profile: Tuple (mem0_client, test_user_id) com cleanup automático
    """
    # Desempacotar fixture
    _mem0_client, test_user_id = cleanup_test_profile

    # Arrange: Criar state inicial sem profile
    initial_state = BSCState(
        query="Como implementar BSC?", user_id=test_user_id, client_profile=None
    )

    # Act 1: Carregar memória (deve retornar None para cliente novo)
    state_after_load = load_client_memory(initial_state)

    # Assert 1: load_client_memory deve retornar None para cliente novo
    assert (
        state_after_load["client_profile"] is None
    ), "load_client_memory deve retornar None para cliente novo"

    # Act 2: Criar profile placeholder (simulando onboarding)
    new_profile = create_placeholder_profile(test_user_id, "Empresa Teste LTDA")

    # Modificar profile com dados completos
    new_profile.company = CompanyInfo(
        name="Empresa Teste LTDA",
        sector="Tecnologia",
        size="média",
        industry="Software as a Service",
    )
    new_profile.context = StrategicContext(
        current_challenges=["Implementar BSC pela primeira vez"],
        strategic_objectives=["Estruturar metas", "Alinhar equipes"],
    )

    # Adicionar profile ao state
    initial_state.client_profile = new_profile

    # Act 3: Salvar profile no Mem0
    state_after_save = save_client_memory(initial_state)

    # Assert 2: user_id deve ser retornado
    assert state_after_save.get("user_id") == test_user_id or "user_id" in state_after_save

    # [TIMER] Aguardar propagação da API Mem0 (eventual consistency)
    time.sleep(1)

    # Act 4: Tentar carregar o profile novamente para verificar persistência
    reloaded_state = load_client_memory(
        BSCState(query="reload", user_id=test_user_id, client_profile=None)
    )

    # Assert 3: O profile recarregado deve existir e ter os mesmos dados
    assert reloaded_state["client_profile"] is not None, "Profile não foi persistido no Mem0"
    assert reloaded_state["client_profile"].company.name == "Empresa Teste LTDA"
    assert reloaded_state["client_profile"].company.sector == "Tecnologia"
    assert reloaded_state["client_profile"].engagement.current_phase == "ONBOARDING"


# ============================================================================
# ETAPA 3: Test Existing Client Loads Profile
# ============================================================================


def test_existing_client_loads_profile(cleanup_test_profile):
    """Valida que cliente existente carrega profile corretamente do Mem0.

    Cenário:
    1. Profile já existe no Mem0 (criado no setup)
    2. load_client_memory recupera profile existente
    3. Dados estão corretos e completos

    Args:
        cleanup_test_profile: Tuple (mem0_client, test_user_id) com cleanup automático
    """
    # Desempacotar fixture
    _mem0_client, test_user_id = cleanup_test_profile

    # Arrange: Criar profile existente no Mem0
    existing_profile = ClientProfile(
        client_id=test_user_id,
        company=CompanyInfo(
            name="Empresa Existente SA",
            sector="Saúde",
            size="grande",
            industry="Healthcare Technology",
        ),
        context=StrategicContext(
            current_challenges=["Escalar operações mantendo qualidade"],
            strategic_objectives=["Aumentar EBITDA 20%", "Melhorar NPS 30pts"],
        ),
        engagement=EngagementState(current_phase="DISCOVERY"),
    )

    # Salvar profile existente no Mem0
    _mem0_client.save_profile(existing_profile)

    # [TIMER] Aguardar propagação da API Mem0 (eventual consistency)
    time.sleep(1)

    # Act: Carregar profile existente via load_client_memory
    state = BSCState(query="Status do projeto?", user_id=test_user_id, client_profile=None)
    state_after_load = load_client_memory(state)

    # Assert: Profile carregado deve corresponder ao existente
    assert state_after_load["client_profile"] is not None, "Profile existente não foi carregado"
    loaded_profile = state_after_load["client_profile"]
    assert loaded_profile.company.name == "Empresa Existente SA"
    assert loaded_profile.company.sector == "Saúde"
    assert loaded_profile.engagement.current_phase == "DISCOVERY"
    assert "Escalar operações mantendo qualidade" in loaded_profile.context.current_challenges


# ============================================================================
# ETAPA 4: Test Engagement State Updates
# ============================================================================


def test_engagement_state_updates(cleanup_test_profile):
    """Valida atualização de engagement state durante progressão workflow.

    Cenário:
    1. Profile em fase ONBOARDING
    2. Atualizar para DISCOVERY (progressão)
    3. save_client_memory persiste mudança
    4. Carregar novamente e validar fase atualizada

    Args:
        cleanup_test_profile: Tuple (mem0_client, test_user_id) com cleanup automático
    """
    # Desempacotar fixture
    _mem0_client, test_user_id = cleanup_test_profile

    # Arrange: Criar profile em ONBOARDING
    profile = ClientProfile(
        client_id=test_user_id,
        company=CompanyInfo(
            name="Startup Inovadora LTDA", sector="Tecnologia", size="pequena", industry="Fintech"
        ),
        context=StrategicContext(
            current_challenges=["Estruturar processos"],
            strategic_objectives=["Crescer 100% ao ano"],
        ),
        engagement=EngagementState(current_phase="ONBOARDING"),
    )

    # Salvar profile inicial
    _mem0_client.save_profile(profile)

    # Act 1: Carregar profile via load_client_memory
    state = BSCState(query="Vamos para discovery", user_id=test_user_id, client_profile=None)
    state_after_load = load_client_memory(state)

    # Assert 1: Profile carregado está em ONBOARDING
    assert state_after_load["client_profile"].engagement.current_phase == "ONBOARDING"

    # Act 2: Atualizar engagement state para DISCOVERY
    profile_updated = state_after_load["client_profile"]
    profile_updated.engagement.current_phase = "DISCOVERY"
    state_updated = BSCState(
        query="Iniciando discovery", user_id=test_user_id, client_profile=profile_updated
    )
    save_client_memory(state_updated)

    # [TIMER] Aguardar propagação da API Mem0
    time.sleep(1)

    # Act 3: Carregar novamente para validar persistência
    state_reloaded = load_client_memory(
        BSCState(query="check phase", user_id=test_user_id, client_profile=None)
    )

    # Assert 2: Fase deve estar atualizada para DISCOVERY
    assert state_reloaded["client_profile"] is not None, "Profile não foi recarregado"
    assert state_reloaded["client_profile"].engagement.current_phase == "DISCOVERY"


# ============================================================================
# ETAPA 5: Test Profile Persistence (Real Mem0)
# ============================================================================


def test_profile_persistence_real_mem0(cleanup_test_profile):
    """Valida persistência real no Mem0 Platform (não mock).

    Cenário:
    1. Criar profile completo com todos os campos
    2. Salvar via save_client_memory
    3. Aguardar alguns segundos
    4. Carregar em nova instância do mem0_client
    5. Validar todos os dados persistidos corretamente

    Args:
        cleanup_test_profile: Tuple (mem0_client, test_user_id) com cleanup automático
    """
    # Desempacotar fixture
    _mem0_client, test_user_id = cleanup_test_profile

    # Arrange: Criar profile completo
    profile = ClientProfile(
        client_id=test_user_id,
        company=CompanyInfo(
            name="Corporação Global SA",
            sector="Manufatura",
            size="grande",
            industry="Automotiva",
            founded_year=1980,
        ),
        context=StrategicContext(
            mission="Liderar transformação sustentável",
            vision="Ser referência global até 2030",
            core_values=["Inovação", "Sustentabilidade", "Excelência"],
            current_challenges=["Transformação digital", "ESG compliance"],
            strategic_objectives=["Reduzir emissões 50%", "Digitalizar 100% processos"],
        ),
        engagement=EngagementState(current_phase="DESIGN"),
    )

    # Act 1: Salvar profile
    state = BSCState(query="save profile", user_id=test_user_id, client_profile=profile)
    save_client_memory(state)

    # Act 2: Aguardar propagação (Mem0 API pode ter latência)
    time.sleep(2)

    # Act 3: Carregar profile em nova requisição
    state_reloaded = load_client_memory(
        BSCState(query="reload", user_id=test_user_id, client_profile=None)
    )

    # Assert: Validar todos os campos persistidos
    assert state_reloaded["client_profile"] is not None, "Profile não foi persistido no Mem0"
    reloaded = state_reloaded["client_profile"]

    # Validar CompanyInfo
    assert reloaded.company.name == "Corporação Global SA"
    assert reloaded.company.sector == "Manufatura"
    assert reloaded.company.size == "grande"
    assert reloaded.company.industry == "Automotiva"
    assert reloaded.company.founded_year == 1980

    # Validar StrategicContext
    assert reloaded.context.mission == "Liderar transformação sustentável"
    assert reloaded.context.vision == "Ser referência global até 2030"
    assert len(reloaded.context.core_values) == 3
    assert "Transformação digital" in reloaded.context.current_challenges
    assert len(reloaded.context.strategic_objectives) == 2

    # Validar EngagementState
    assert reloaded.engagement.current_phase == "DESIGN"


# ============================================================================
# ETAPA 6: Test Workflow Complete E2E
# ============================================================================


def test_workflow_complete_e2e(cleanup_test_profile):
    """Teste E2E completo simulando workflow real BSC.

    Cenário:
    1. Cliente novo inicia (ONBOARDING)
    2. Preenche dados iniciais
    3. Progride para DISCOVERY
    4. Progride para DESIGN
    5. Cada transição persiste no Mem0
    6. Validar histórico completo ao final

    Args:
        cleanup_test_profile: Tuple (mem0_client, test_user_id) com cleanup automático
    """
    # Desempacotar fixture
    _mem0_client, test_user_id = cleanup_test_profile

    # ===== FASE 1: ONBOARDING =====

    # Act 1: Cliente novo chega
    state = BSCState(query="Quero implementar BSC", user_id=test_user_id, client_profile=None)
    state_after_load = load_client_memory(state)

    # Assert 1: Cliente novo não tem profile
    assert state_after_load["client_profile"] is None

    # Act 2: Criar profile inicial (onboarding)
    profile = create_placeholder_profile(test_user_id, "E2E Test Company")
    profile.company = CompanyInfo(
        name="E2E Test Company", sector="Tecnologia", size="média", industry="SaaS"
    )
    profile.context = StrategicContext(
        current_challenges=["Crescimento desorganizado"],
        strategic_objectives=["Estruturar gestão estratégica"],
    )
    state.client_profile = profile
    save_client_memory(state)

    # [TIMER] Aguardar propagação da API Mem0
    time.sleep(1)

    # ===== FASE 2: DISCOVERY =====

    # Act 3: Carregar profile e progredir para DISCOVERY
    state_discovery = BSCState(query="Fazer diagnóstico", user_id=test_user_id, client_profile=None)
    state_discovery_loaded = load_client_memory(state_discovery)

    # Assert 2: Profile carregado está em ONBOARDING
    assert state_discovery_loaded["client_profile"].engagement.current_phase == "ONBOARDING"

    # Act 4: Atualizar para DISCOVERY
    profile_discovery = state_discovery_loaded["client_profile"]
    profile_discovery.engagement.current_phase = "DISCOVERY"
    state_discovery.client_profile = profile_discovery
    save_client_memory(state_discovery)

    # [TIMER] Aguardar propagação da API Mem0
    time.sleep(1)

    # ===== FASE 3: DESIGN =====

    # Act 5: Carregar e progredir para DESIGN
    state_design = BSCState(
        query="Criar mapa estratégico", user_id=test_user_id, client_profile=None
    )
    state_design_loaded = load_client_memory(state_design)

    # Assert 3: Profile está em DISCOVERY
    assert state_design_loaded["client_profile"].engagement.current_phase == "DISCOVERY"

    # Act 6: Atualizar para DESIGN
    profile_design = state_design_loaded["client_profile"]
    profile_design.engagement.current_phase = "DESIGN"
    state_design.client_profile = profile_design
    save_client_memory(state_design)

    # [TIMER] Aguardar propagação da API Mem0
    time.sleep(1)

    # ===== VALIDAÇÃO FINAL =====

    # Act 7: Carregar profile final
    state_final = load_client_memory(
        BSCState(query="status", user_id=test_user_id, client_profile=None)
    )

    # Assert 4: Validar estado final completo
    final_profile = state_final["client_profile"]
    assert final_profile is not None, "Profile final não foi carregado"
    assert final_profile.company.name == "E2E Test Company"
    assert final_profile.engagement.current_phase == "DESIGN"
    assert final_profile.context is not None
    assert len(final_profile.context.current_challenges) > 0
