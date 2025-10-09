"""
Interface Streamlit para o Agente BSC RAG.
"""
import streamlit as st
import asyncio
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.workflow import create_bsc_workflow
from app.utils import (
    initialize_session_state,
    add_message,
    clear_chat_history,
    format_timestamp,
    format_latency,
    create_metrics_display,
    display_perspective_responses,
    display_judge_evaluation
)
from config.settings import settings


# Configuração da página
st.set_page_config(
    page_title="Agente BSC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Função principal da aplicação."""
    
    # Inicializar estado
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">📊 Agente BSC</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Sistema RAG Multi-Agente para Balanced Scorecard</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Informações do sistema
        st.subheader("Sistema")
        st.info(f"""
        **Versão**: {settings.app_version}
        **Modelo**: {settings.openai_model}
        **Vector Store**: {settings.vector_store_type.upper()}
        **Sessão**: {st.session_state.session_id}
        """)
        
        # Configurações de execução
        st.subheader("Execução")
        
        enable_perspectives = st.multiselect(
            "Perspectivas Ativas",
            options=["financial", "customer", "process", "learning"],
            default=["financial", "customer", "process", "learning"],
            format_func=lambda x: {
                "financial": "💰 Financeira",
                "customer": "👥 Cliente",
                "process": "⚙️ Processos",
                "learning": "📚 Aprendizado"
            }[x]
        )
        
        show_details = st.checkbox("Mostrar Detalhes", value=True)
        show_sources = st.checkbox("Mostrar Fontes", value=True)
        show_judge = st.checkbox("Mostrar Avaliação Judge", value=True)
        
        st.divider()
        
        # Estatísticas
        st.subheader("📈 Estatísticas")
        st.metric("Queries Realizadas", st.session_state.query_count)
        st.metric("Mensagens no Chat", len(st.session_state.messages))
        
        st.divider()
        
        # Ações
        if st.button("🗑️ Limpar Chat", use_container_width=True):
            clear_chat_history()
            st.rerun()
        
        if st.button("🔄 Reiniciar Sessão", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat")
        
        # Container para mensagens
        chat_container = st.container()
        
        with chat_container:
            # Exibir histórico de mensagens
            for message in st.session_state.messages:
                role = message["role"]
                content = message["content"]
                metadata = message.get("metadata", {})
                timestamp = message.get("timestamp")
                
                with st.chat_message(role):
                    st.markdown(content)
                    
                    if role == "assistant" and show_details and metadata:
                        # Métricas
                        if "judge_score" in metadata:
                            create_metrics_display(metadata)
                        
                        # Perspectivas
                        perspectives = metadata.get("perspectives", [])
                        if perspectives and show_sources:
                            st.markdown("---")
                            display_perspective_responses(perspectives)
                        
                        # Judge
                        judge_eval = metadata.get("judge_evaluation")
                        if judge_eval and show_judge:
                            st.markdown("---")
                            display_judge_evaluation(judge_eval)
                    
                    # Timestamp
                    if timestamp:
                        st.caption(f"🕐 {format_timestamp(timestamp)}")
        
        # Input de query
        query = st.chat_input("Faça sua pergunta sobre Balanced Scorecard...")
        
        if query:
            # Adicionar mensagem do usuário
            add_message("user", query)
            st.session_state.query_count += 1
            
            # Exibir mensagem do usuário imediatamente
            with st.chat_message("user"):
                st.markdown(query)
                st.caption(f"🕐 {format_timestamp()}")
            
            # Processar query
            with st.chat_message("assistant"):
                with st.spinner("Processando sua pergunta..."):
                    try:
                        # Executar workflow
                        start_time = datetime.now()
                        
                        # Criar workflow
                        workflow = create_bsc_workflow()
                        
                        # Executar
                        result = asyncio.run(workflow.run(
                            query=query,
                            session_id=st.session_state.session_id
                        ))
                        
                        end_time = datetime.now()
                        latency = (end_time - start_time).total_seconds()
                        
                        # Resposta
                        response = result.get("response", "Desculpe, não consegui gerar uma resposta.")
                        metadata = result.get("metadata", {})
                        metadata["latency"] = latency
                        
                        # Adicionar metadados do resultado
                        metadata["judge_evaluation"] = result.get("judge_evaluation")
                        metadata["perspectives"] = result.get("perspectives", [])
                        
                        # Exibir resposta
                        st.markdown(response)
                        
                        # Exibir latência
                        st.caption(f"⚡ Processado em {format_latency(latency)}")
                        
                        # Exibir detalhes
                        if show_details:
                            # Métricas
                            if "judge_score" in metadata:
                                create_metrics_display(metadata)
                            
                            # Perspectivas
                            perspectives = metadata.get("perspectives", [])
                            if perspectives and show_sources:
                                st.markdown("---")
                                display_perspective_responses(perspectives)
                            
                            # Judge
                            judge_eval = metadata.get("judge_evaluation")
                            if judge_eval and show_judge:
                                st.markdown("---")
                                display_judge_evaluation(judge_eval)
                        
                        # Timestamp
                        st.caption(f"🕐 {format_timestamp()}")
                        
                        # Adicionar mensagem do assistente ao histórico
                        add_message("assistant", response, metadata)
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar query: {e}")
                        error_msg = f"❌ Erro ao processar sua pergunta: {str(e)}"
                        st.error(error_msg)
                        add_message("assistant", error_msg)
    
    with col2:
        st.subheader("📚 Exemplos de Queries")
        
        st.markdown("""
        **Queries Factuais:**
        - Quais são os principais KPIs da perspectiva financeira?
        - Como medir a satisfação do cliente no BSC?
        - Que métricas são usadas na perspectiva de aprendizado?
        
        **Queries Conceituais:**
        - Como implementar BSC em uma empresa?
        - Qual a relação entre as perspectivas do BSC?
        - Por que o BSC é importante para estratégia?
        
        **Queries Comparativas:**
        - Qual a diferença entre KPIs financeiros e de clientes?
        - Como BSC se compara com outros frameworks?
        - Quais perspectivas impactam mais a lucratividade?
        
        **Queries Complexas:**
        - Como alinhar objetivos estratégicos com métricas BSC?
        - Quais são as melhores práticas para implementação?
        - Como criar um mapa estratégico BSC completo?
        """)
        
        st.divider()
        
        st.subheader("ℹ️ Sobre")
        st.markdown("""
        Este sistema utiliza:
        - **RAG (Retrieval-Augmented Generation)** com vector store moderno
        - **Multi-Agentes** especializados em cada perspectiva BSC
        - **LangGraph** para orquestração inteligente
        - **Judge Agent** para validação de qualidade
        - **Contextual Retrieval** para melhor precisão
        """)


if __name__ == "__main__":
    main()

