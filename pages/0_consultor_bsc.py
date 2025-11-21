"""Pagina Streamlit - Chat Consultor BSC.

Interface conversacional com workflow consultivo BSC multi-fase:
ONBOARDING -> DISCOVERY -> APPROVAL -> SOLUTION_DESIGN -> IMPLEMENTATION

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

from uuid import uuid4

import streamlit as st

# Carregar .env
from dotenv import load_dotenv

load_dotenv()

from src.graph.states import BSCState
from src.graph.workflow import BSCWorkflow

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
if "user_id" not in st.session_state:
    # Tentar ler user_id da URL primeiro (persiste entre reloads)
    user_id_from_url = st.query_params.get("uid", None)

    if user_id_from_url:
        # Reutilizar user_id existente da URL
        st.session_state.user_id = user_id_from_url
    else:
        # Gerar novo user_id e salvar na URL
        new_uid = str(uuid4())
        st.session_state.user_id = new_uid
        st.query_params.uid = new_uid

if "current_phase" not in st.session_state:
    st.session_state.current_phase = "ONBOARDING"

# NOTA: LangGraph checkpointer persiste automaticamente:
# - client_profile, onboarding_progress, metadata, partial_profile
# Nao precisamos gerenciar manualmente no session_state!

# Sidebar com informações
with st.sidebar:
    st.header("Informacoes da Sessao")

    st.metric("User ID", st.session_state.user_id[:8] + "...")
    st.metric("Fase Atual", st.session_state.current_phase)
    st.metric("Mensagens", len(st.session_state.messages))

    st.divider()

    st.subheader("Fases do Workflow")
    st.markdown(
        """
    1. **ONBOARDING** - Coleta de informacoes basicas
    2. **DISCOVERY** - Diagnostico BSC completo
    3. **APPROVAL** - Aprovacao do diagnostico
    4. **SOLUTION_DESIGN** - Criacao do Strategy Map
    5. **IMPLEMENTATION** - Geracao do Action Plan
    """
    )

    st.divider()

    if st.button("Reiniciar Sessao", type="secondary"):
        st.session_state.messages = []
        # MANTÉM o mesmo user_id (NÃO gerar novo!) para preservar acesso ao profile
        # Usuário pode continuar acessando Strategy Map e Action Plan após reiniciar
        st.session_state.current_phase = "ONBOARDING"
        if "workflow" in st.session_state:
            del st.session_state.workflow  # Forcar recriar workflow
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
            # Inicializar workflow UMA VEZ e reusar (critical para checkpointer!)
            if "workflow" not in st.session_state:
                st.session_state.workflow = BSCWorkflow()
                print("[DEBUG STREAMLIT] Workflow inicializado PELA PRIMEIRA VEZ")

            workflow = st.session_state.workflow

            # Config com thread_id (LangGraph checkpointer persiste state automaticamente!)
            config = {"configurable": {"thread_id": st.session_state.user_id}}

            # Criar state MINIMO (LangGraph checkpointer carrega resto do checkpoint!)
            initial_state = BSCState(query=user_input, user_id=st.session_state.user_id)

            print(
                f"[DEBUG STREAMLIT] Invocando workflow | thread_id={st.session_state.user_id[:8]}..."
            )

            # Executar workflow (checkpointer carrega estado anterior automaticamente!)
            result = workflow.graph.invoke(initial_state, config=config)

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
    f"BSC RAG Agent - Sessao 40 (Nov 21, 2025) - Sprint 4: Chat + UI Visualization | User ID: {st.session_state.user_id[:13]}..."
)
