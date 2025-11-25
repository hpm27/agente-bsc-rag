"""Pagina Streamlit - Chat Consultor BSC.

Interface conversacional com workflow consultivo BSC multi-fase:
ONBOARDING -> DISCOVERY -> APPROVAL -> SOLUTION_DESIGN -> IMPLEMENTATION

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import asyncio
from uuid import uuid4

import streamlit as st

# Carregar .env
from dotenv import load_dotenv

load_dotenv()

from src.graph.states import BSCState
from src.graph.workflow import get_workflow
from ui.helpers.chat_loader import load_chat_history, save_chat_to_checkpoint
from ui.helpers.mem0_loader import load_all_clients_sqlite

st.set_page_config(page_title="Consultor BSC", layout="wide", page_icon="[BSC]")

# CSS customizado para chat
st.markdown(
    """
<style>
.user-message {
    background-color: #E3F2FD;
    padding: 12px;
    border-radius: 8px;
    margin: 8px 0;
    color: #1f1f1f;
}
.assistant-message {
    background-color: #F5F5F5;
    padding: 12px;
    border-radius: 8px;
    margin: 8px 0;
    color: #1f1f1f;
}
.phase-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    margin-left: 8px;
}
.phase-onboarding { background-color: #FFF9C4; color: #1f1f1f; }
.phase-discovery { background-color: #E3F2FD; color: #1f1f1f; }
.phase-approval { background-color: #FFEBEE; color: #1f1f1f; }
.phase-design { background-color: #E8F5E9; color: #1f1f1f; }
.phase-implementation { background-color: #F3E5F5; color: #1f1f1f; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Consultor BSC - Chat Interativo")

# Inicializar session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# CRITICAL FIX: Usar query_params para persistir user_id entre reloads e páginas
# Isso garante que Strategy Map e Action Plan usam o MESMO user_id do workflow
#
# CORREÇÃO SESSAO 43 (2025-11-24): Usar APENAS st.query_params (API moderna)
# Streamlit NÃO permite misturar experimental_get_query_params + query_params
# StreamlitAPIException se misturadas. Fonte: Streamlit Docs 2025
if "user_id" not in st.session_state:
    # Tentar ler user_id da URL primeiro (persiste entre reloads)
    user_id_from_url = st.query_params.get("uid")

    if user_id_from_url:
        # Reutilizar user_id existente da URL
        st.session_state.user_id = user_id_from_url
    else:
        # Gerar novo user_id e salvar na URL
        new_uid = str(uuid4())
        st.session_state.user_id = new_uid

# CORREÇÃO SESSAO 40: SEMPRE sincronizar query_params com session_state
# Garante que URL SEMPRE tem uid atualizado (mesmo se carregado de URL)
# CORREÇÃO SESSAO 43: Substituir experimental_set_query_params (deprecated após 2024-04-11)
st.query_params["uid"] = st.session_state.user_id

# CORREÇÃO SESSAO 43 (2025-11-24): Carregar histórico de chat do LangGraph checkpoint
# IMPORTANTE: Deve vir DEPOIS da inicialização de user_id acima!
# Outras páginas persistem porque carregam do SQLite, chat precisa carregar do checkpoint
if not st.session_state.messages and st.session_state.get("user_id"):
    loaded_messages = load_chat_history(st.session_state.user_id)
    if loaded_messages:
        st.session_state.messages = loaded_messages

if "current_phase" not in st.session_state:
    st.session_state.current_phase = "ONBOARDING"

# NOTA: LangGraph checkpointer persiste automaticamente:
# - client_profile, onboarding_progress, metadata, partial_profile
# Nao precisamos gerenciar manualmente no session_state!

# Sidebar com informações
with st.sidebar:
    st.header("Gerenciar Consultas")

    # ============================================================================
    # SESSAO 49: SELETOR DE CLIENTES PARA RETOMAR CONSULTAS ANTERIORES
    # Permite fechar Streamlit e retomar trabalho depois
    # ============================================================================

    # Carregar lista de clientes do SQLite (mais confiavel que Mem0)
    existing_clients, clients_error = load_all_clients_sqlite()

    # Botao para nova consulta (sempre visivel)
    if st.button("Nova Consulta", type="primary", use_container_width=True):
        # Gerar novo UUID
        new_uid = str(uuid4())
        st.session_state.user_id = new_uid
        st.session_state.messages = []
        st.session_state.current_phase = "ONBOARDING"
        st.query_params["uid"] = new_uid
        st.rerun()

    # Seletor de consultas anteriores
    if existing_clients:
        st.markdown("---")
        st.subheader("Retomar Consulta Anterior")

        # Criar opcoes para selectbox
        options = ["-- Selecione uma consulta --"] + [c["display_name"] for c in existing_clients]

        # Map display_name -> user_id
        client_map = {c["display_name"]: c["user_id"] for c in existing_clients}

        selected = st.selectbox(
            "Consultas salvas:",
            options,
            index=0,
            key="client_selector",
            help="Selecione uma consulta anterior para retomar o trabalho",
        )

        if selected != "-- Selecione uma consulta --":
            selected_uid = client_map[selected]

            # Verificar se precisa trocar de cliente
            if selected_uid != st.session_state.user_id:
                if st.button("Carregar Consulta", type="secondary", use_container_width=True):
                    # Trocar para o cliente selecionado
                    st.session_state.user_id = selected_uid
                    st.query_params["uid"] = selected_uid

                    # Limpar mensagens atuais e carregar historico do cliente selecionado
                    st.session_state.messages = []
                    loaded_messages = load_chat_history(selected_uid)
                    if loaded_messages:
                        st.session_state.messages = loaded_messages

                    # Resetar fase (sera atualizada pelo workflow)
                    st.session_state.current_phase = "ONBOARDING"

                    st.success(f"Consulta carregada: {selected[:50]}...")
                    st.rerun()
    elif clients_error:
        st.caption(clients_error)

    st.markdown("---")

    # Informacoes da sessao atual
    st.subheader("Sessao Atual")
    st.metric("ID", st.session_state.user_id[:8] + "...")
    st.metric("Fase", st.session_state.current_phase)
    st.metric("Mensagens", len(st.session_state.messages))

    st.markdown("---")

    st.subheader("Fases do Workflow")
    st.markdown(
        """
    1. **ONBOARDING** - Coleta de informacoes
    2. **DISCOVERY** - Diagnostico BSC
    3. **APPROVAL** - Aprovacao
    4. **SOLUTION_DESIGN** - Strategy Map
    5. **IMPLEMENTATION** - Action Plan
    """
    )

    st.markdown("---")

    if st.button("Reiniciar Sessao", type="secondary", use_container_width=True):
        st.session_state.messages = []
        # MANTÉM o mesmo user_id (NÃO gerar novo!) para preservar acesso ao profile
        # Usuário pode continuar acessando Strategy Map e Action Plan após reiniciar
        st.session_state.current_phase = "ONBOARDING"
        # NOTA: Workflow usa singleton get_workflow() (não armazenado em session_state)
        # O checkpointer mantém o state do workflow, reset apenas limpa UI
        st.rerun()

# Exibir histórico de mensagens
st.subheader("Conversa")

for msg in st.session_state.messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")

    if role == "user":
        st.markdown(
            f'<div class="user-message"><b>Voce:</b><br>{content}</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="assistant-message"><b>Consultor BSC:</b><br>{content}</div>',
            unsafe_allow_html=True,
        )

# Input do usuário
user_input = st.chat_input("Digite sua mensagem aqui...")

if user_input:
    # Adicionar mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Exibir mensagem do usuário imediatamente
    st.markdown(
        f'<div class="user-message"><b>Voce:</b><br>{user_input}</div>', unsafe_allow_html=True
    )

    # Executar workflow
    with st.spinner("Consultor BSC processando..."):
        try:
            # CORREÇÃO SESSAO 43: Usar singleton get_workflow() para consistência
            # ANTES: st.session_state.workflow = BSCWorkflow() criava instância separada
            # PROBLEMA: chat_loader.py usava get_workflow() (singleton diferente!)
            # SOLUÇÃO: Ambos usam get_workflow() -> mesma instância, mesmo checkpointer
            workflow = get_workflow()
            print("[DEBUG STREAMLIT] Usando workflow singleton (get_workflow)")

            # Config com thread_id (LangGraph checkpointer persiste state automaticamente!)
            config = {"configurable": {"thread_id": st.session_state.user_id}}

            # CORREÇÃO SESSAO 43: Passar chat_history para o workflow
            # Isso permite que o workflow tenha contexto da conversa
            chat_history_for_workflow = st.session_state.messages.copy()

            # Criar state MINIMO (LangGraph checkpointer carrega resto do checkpoint!)
            # CORREÇÃO SESSAO 45: Converter para dict - ainvoke() espera dict[str, Any]
            # BSCState.model_dump() garante serialização correta para checkpoints
            # CORREÇÃO SESSAO 45: Incluir session_id para consistência com workflow.run()
            initial_state = BSCState(
                query=user_input,
                session_id=st.session_state.user_id,  # Usar user_id como session_id
                user_id=st.session_state.user_id,
                metadata={"chat_history": chat_history_for_workflow},
            ).model_dump()

            print(
                f"[DEBUG STREAMLIT] Invocando workflow | thread_id={st.session_state.user_id[:8]}... | "
                f"chat_history={len(chat_history_for_workflow)} msgs"
            )

            # Executar workflow (checkpointer carrega estado anterior automaticamente!)
            # CORREÇÃO SESSAO 44-45 (2025-11-24): Usar ainvoke() ASYNC com AsyncSqliteSaver
            # ROOT CAUSE: Handlers async (execute_agents, implementation_handler) requerem ainvoke()
            # ainvoke() requer checkpointer async (AsyncSqliteSaver) criado dinamicamente
            # Fonte: Medium "Async, Parameters and LangGraph" (Apr 2025),
            #        Medium "Conversational AI with Streamlit" (Jul 2025)
            #
            # CORREÇÃO SESSAO 45: SEMPRE criar novo event loop
            # PROBLEMA: get_running_loop() + run_until_complete() causa RuntimeError:
            #           "This event loop is already running"
            # SOLUÇÃO: Criar novo loop isolado (pattern validado em workflow.run())
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(workflow.ainvoke(initial_state, config=config))
            finally:
                # CORREÇÃO SESSAO 45: Cleanup completo antes de fechar loop
                # Sequência recomendada por Python asyncio docs:
                # 1. shutdown_asyncgens() - limpa async generators
                # 2. shutdown_default_executor() - limpa thread pool threads
                # 3. close() - fecha o loop
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except Exception:
                    pass  # Ignorar erros de cleanup
                try:
                    loop.run_until_complete(loop.shutdown_default_executor())
                except Exception:
                    pass  # Ignorar erros de cleanup (executor pode não existir)
                loop.close()  # Sempre fechar loop que criamos

            print(
                f"[DEBUG STREAMLIT] Workflow concluido | metadata keys: {list(result.get('metadata', {}).keys())}"
            )

            # Extrair resposta
            response = result.get("final_response", "[ERRO] Nenhuma resposta gerada")

            # Atualizar session_state apenas com info de exibicao
            # NOTA: LangGraph checkpointer JA persiste tudo automaticamente!
            if result.get("current_phase"):
                phase_value = (
                    result["current_phase"].value
                    if hasattr(result["current_phase"], "value")
                    else str(result["current_phase"])
                )
                st.session_state.current_phase = phase_value
                print(f"[DEBUG STREAMLIT] Fase atualizada: {phase_value}")

            # Adicionar resposta ao histórico
            st.session_state.messages.append({"role": "assistant", "content": response})

            # CORREÇÃO SESSAO 43: Salvar chat no checkpoint para persistir após reload
            save_chat_to_checkpoint(st.session_state.user_id, st.session_state.messages)

            # Recarregar página para mostrar nova mensagem
            st.rerun()

        except Exception as e:
            st.error(f"[ERRO] Falha ao processar mensagem: {e}")
            st.exception(e)

# Mensagem de boas-vindas
if len(st.session_state.messages) == 0:
    st.info(
        """
    **Bem-vindo ao Consultor BSC!**

    Este e um consultor estrategico especializado em Balanced Scorecard (BSC).

    **Como funciona:**
    1. Comece se apresentando e falando sobre sua empresa
    2. O consultor fara perguntas para entender sua situacao
    3. Apos coletar informacoes, gerara um diagnostico BSC completo
    4. Voce aprovara o diagnostico
    5. O sistema criara um Strategy Map BSC personalizado
    6. Por fim, gerara um Action Plan detalhado

    **Digite sua primeira mensagem abaixo para comecar!**

    Exemplo: "Ola, sou gestor da empresa Engelar, do setor metalurgico. Queremos implementar BSC."
    """
    )

# Footer
st.divider()
st.caption(
    f"BSC RAG Agent - Sessao 49 (Nov 25, 2025) - Persistencia de Sessoes | User ID: {st.session_state.user_id[:13]}..."
)
