"""
Utilitários para a interface Streamlit.
"""
from typing import Dict, Any, List
import streamlit as st
from datetime import datetime


def format_timestamp(timestamp: datetime = None) -> str:
    """Formata timestamp no padrão brasileiro."""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%d/%m/%Y %H:%M:%S")


def format_confidence(confidence: float) -> str:
    """Formata confiança como porcentagem."""
    return f"{confidence * 100:.1f}%"


def get_perspective_emoji(perspective: str) -> str:
    """Retorna emoji para cada perspectiva BSC."""
    emojis = {
        "financial": "💰",
        "customer": "👥",
        "process": "⚙️",
        "learning": "📚"
    }
    return emojis.get(perspective.lower(), "📊")


def get_perspective_name(perspective: str) -> str:
    """Retorna nome em português da perspectiva."""
    names = {
        "financial": "Perspectiva Financeira",
        "customer": "Perspectiva do Cliente",
        "process": "Perspectiva de Processos Internos",
        "learning": "Perspectiva de Aprendizado e Crescimento"
    }
    return names.get(perspective.lower(), perspective)


def format_source(source: Dict[str, Any], index: int) -> str:
    """Formata fonte para exibição."""
    doc_id = source.get("doc_id", f"doc_{index}")
    score = source.get("score", 0.0)
    content = source.get("content", "")
    
    # Truncar conteúdo se muito longo
    if len(content) > 200:
        content = content[:200] + "..."
    
    return f"""
**Documento {index + 1}** (Score: {score:.3f})
```
{content}
```
"""


def initialize_session_state():
    """Inicializa o estado da sessão Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0


def add_message(role: str, content: str, metadata: Dict[str, Any] = None):
    """Adiciona mensagem ao histórico."""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "metadata": metadata or {},
        "timestamp": datetime.now()
    })


def clear_chat_history():
    """Limpa o histórico de chat."""
    st.session_state.messages = []
    st.session_state.query_count = 0


def format_latency(seconds: float) -> str:
    """Formata latência em formato legível."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    else:
        return f"{seconds:.2f}s"


def create_metrics_display(metadata: Dict[str, Any]):
    """Cria display de métricas do resultado."""
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            "Perspectivas",
            len(metadata.get("perspectives_used", []))
        )
    
    with cols[1]:
        st.metric(
            "Score do Judge",
            format_confidence(metadata.get("judge_score", 0.0))
        )
    
    with cols[2]:
        st.metric(
            "Fontes",
            metadata.get("total_sources", 0)
        )
    
    with cols[3]:
        st.metric(
            "Refinamentos",
            metadata.get("refinement_iterations", 0)
        )


def display_perspective_responses(perspectives: List[Dict[str, Any]]):
    """Exibe respostas de cada perspectiva em expansíveis."""
    for perspective in perspectives:
        perspective_type = perspective.get("perspective", "")
        emoji = get_perspective_emoji(perspective_type)
        name = get_perspective_name(perspective_type)
        confidence = perspective.get("confidence", 0.0)
        
        with st.expander(f"{emoji} {name} (Confiança: {format_confidence(confidence)})"):
            st.markdown(perspective.get("content", ""))
            
            # Exibir fontes se disponíveis
            sources = perspective.get("sources", [])
            if sources:
                st.markdown("**Fontes consultadas:**")
                for idx, source in enumerate(sources[:3]):  # Limitar a 3 fontes
                    st.markdown(format_source(source, idx))
            
            # Exibir raciocínio se disponível
            reasoning = perspective.get("reasoning")
            if reasoning:
                st.markdown("**Raciocínio:**")
                st.info(reasoning)


def display_judge_evaluation(evaluation: Dict[str, Any]):
    """Exibe avaliação do Judge Agent."""
    if not evaluation:
        return
    
    approved = evaluation.get("approved", False)
    score = evaluation.get("score", 0.0)
    feedback = evaluation.get("feedback", "")
    
    # Status visual
    if approved:
        st.success(f"✅ Resposta aprovada (Score: {format_confidence(score)})")
    else:
        st.warning(f"⚠️ Resposta necessitou refinamento (Score: {format_confidence(score)})")
    
    # Feedback
    st.markdown("**Avaliação do Judge:**")
    st.markdown(feedback)
    
    # Issues (se houver)
    issues = evaluation.get("issues", [])
    if issues:
        st.markdown("**Problemas identificados:**")
        for issue in issues:
            st.markdown(f"- {issue}")
    
    # Sugestões (se houver)
    suggestions = evaluation.get("suggestions", [])
    if suggestions:
        st.markdown("**Sugestões:**")
        for suggestion in suggestions:
            st.markdown(f"- {suggestion}")



