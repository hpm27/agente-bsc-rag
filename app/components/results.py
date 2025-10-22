"""
Componente para exibicao de resultados do workflow BSC.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional, cast
from app.utils import (
    format_perspective_name,
    get_perspective_color,
    format_confidence_score,
    format_document_source,
    truncate_text,
)


def render_results(result: Dict[str, Any]) -> None:
    """
    Renderiza resultados completos do workflow BSC.

    Args:
        result: Dicionario com resultados do workflow (BSCState)
    """
    # Resumo estruturado do diagnóstico (executive summary + recomendações)
    render_diagnostic_section(result)

    # Expanders para detalhes (resposta principal pode ter sido exibida em app/main.py)
    render_perspectives_section(result)
    render_documents_section(result)
    render_judge_section(result)

def _coerce_to_dict(obj: Any) -> Dict[str, Any]:
    """Converte objeto Pydantic ou dataclass para dict de forma segura."""
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return cast(Dict[str, Any], obj.model_dump())
    if hasattr(obj, "dict"):
        return cast(Dict[str, Any], obj.dict())  # type: ignore[no-any-return]
    if isinstance(obj, dict):
        return obj
    # Fallback raso via vars
    try:
        return {k: getattr(obj, k) for k in dir(obj) if not k.startswith("_")}
    except Exception:
        return {}


def _bullets_from_paragraph(text: str, max_items: int = 7) -> List[str]:
    """Quebra parágrafo longo em bullets curtos para escaneabilidade."""
    if not text:
        return []
    # Quebras por pontuação comum; remove espaços extras e linhas vazias
    import re
    parts = re.split(r"[.;]\s+|\n+", text.strip())
    # Filtrar bullets com mínimo 20 chars (evitar fragmentos incompletos)
    bullets = [p.strip("- • ") for p in parts if p and len(p.strip()) >= 20]
    return bullets[:max_items]


def render_diagnostic_section(result: Dict[str, Any]) -> None:
    """
    Renderiza visão executiva do diagnóstico (cards/colunas, bullets, top 3 recomendações).
    """
    diagnostic_obj = result.get("diagnostic")
    diagnostic = _coerce_to_dict(diagnostic_obj)

    if not diagnostic:
        return

    executive_summary = diagnostic.get("executive_summary", "")
    recommendations = diagnostic.get("recommendations", []) or []
    synergies = diagnostic.get("cross_perspective_synergies", []) or []
    next_phase = diagnostic.get("next_phase", "APPROVAL_PENDING")

    # Separador visual discreto
    st.markdown("---")

    # Tudo dentro de um expander organizado
    with st.expander("[CHECK] Diagnóstico BSC Completo", expanded=True):
        # Métricas rápidas (cards)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Perspectivas analisadas", f"{len(result.get('agent_responses', []))}")
        with col2:
            st.metric("Recomendações", f"{len(recommendations)}")
        with col3:
            st.metric("Synergies", f"{len(synergies)}")
        with col4:
            st.metric("Próxima fase", next_phase)

        st.divider()

        # Resumo Executivo em expander
        if executive_summary:
            with st.expander("Resumo Executivo (bullet points)", expanded=False):
                bullets = _bullets_from_paragraph(executive_summary)
                if bullets:
                    for b in bullets:
                        st.markdown(f"- {b}")
                else:
                    st.markdown(executive_summary)

        # Synergies em expander
        if synergies:
            with st.expander(f"Synergies cross-perspective ({len(synergies)})", expanded=False):
                for s in synergies:
                    st.markdown(f"- {s}")

        st.markdown("\n")
        st.markdown("### Top 3 Recomendações")

        # Normalizar recomendações (podem ser objetos Pydantic)
        norm_recs: List[Dict[str, Any]] = []
        for r in recommendations[:3]:
            rec = _coerce_to_dict(r)
            norm_recs.append(rec)

        # Exibir cards empilhados verticalmente (largura total para mais espaço horizontal)
        if norm_recs:
            for rec in norm_recs:
                title = rec.get("title", "Recomendação")
                desc = rec.get("description", "")
                impact = rec.get("impact", "-")
                priority = rec.get("priority", "-")
                timeframe = rec.get("timeframe", "-")
                next_steps = rec.get("next_steps", []) or []

                # Truncar description para legibilidade (máx 300 chars com mais espaço)
                desc_short = truncate_text(desc, 300) if desc else "Sem detalhes disponíveis"

                st.markdown(
                    f"<div style='background:#f8f9fb;border:1px solid #e6e9ef;padding:16px;border-radius:8px;margin-bottom:16px;'>"
                    f"<div style='font-weight:700;font-size:1.1rem;color:#1f1f1f;margin-bottom:8px;'>{title}</div>"
                    f"<div style='font-size:0.95rem;color:#333;margin-bottom:12px;line-height:1.5;'>{desc_short}</div>"
                    f"<div style='margin-bottom:12px;'>"
                    f"<span style='background:#34a853;color:#fff;border-radius:6px;padding:4px 10px;margin-right:8px;font-size:0.88rem;font-weight:600;'>Impacto: {impact}</span>"
                    f"<span style='background:#4285f4;color:#fff;border-radius:6px;padding:4px 10px;margin-right:8px;font-size:0.88rem;font-weight:600;'>Prioridade: {priority}</span>"
                    f"<span style='background:#fbbc04;color:#000;border-radius:6px;padding:4px 10px;font-size:0.88rem;font-weight:600;'>Prazo: {timeframe}</span>"
                    f"</div>"
                    f"<div style='font-size:0.90rem;color:#444;'>"
                    f"<strong>Proximos passos:</strong>"
                    f"<ul style='margin:6px 0 0 20px;line-height:1.6;'>"
                    + "".join(f"<li>{ns}</li>" for ns in next_steps[:3]) +
                    "</ul>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.divider()



def render_perspectives_section(result: Dict[str, Any]) -> None:
    """
    Renderiza secao de perspectivas consultadas.

    Args:
        result: Resultado do workflow
    """
    agent_responses = result.get("agent_responses", [])

    if not agent_responses:
        return

    with st.expander(f"Perspectivas Consultadas ({len(agent_responses)})", expanded=False):
        # Criar tabs para cada perspectiva
        tab_names = [format_perspective_name(resp["perspective"]) for resp in agent_responses]
        tabs = st.tabs(tab_names)

        for tab, response in zip(tabs, agent_responses):
            with tab:
                render_single_perspective(response)


def render_single_perspective(response: Dict[str, Any]) -> None:
    """
    Renderiza resposta de uma unica perspectiva.

    Args:
        response: Resposta do agente (AgentResponse)
    """
    perspective = response.get("perspective", "unknown")
    agent_name = format_perspective_name(perspective)
    answer = response.get("content", "Sem resposta")
    confidence = response.get("confidence", 0.0)
    sources = response.get("sources", [])

    # Header com cor da perspectiva
    color = get_perspective_color(perspective)
    st.markdown(
        f'<div style="background-color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">'
        f'<strong style="color: white;">{agent_name}</strong>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Resposta
    st.markdown("**Analise:**")
    st.markdown(answer)

    # Confianca
    st.markdown("**Confianca:**")
    st.markdown(format_confidence_score(confidence))

    # Fontes
    if sources:
        st.markdown(f"**Fontes Consultadas:** {len(sources)} documento(s)")
        with st.expander("Ver fontes"):
            for idx, source in enumerate(sources, 1):
                st.caption(f"{idx}. {source}")


def render_documents_section(result: Dict[str, Any]) -> None:
    """
    Renderiza secao de documentos recuperados.

    Args:
        result: Resultado do workflow
    """
    documents = result.get("retrieved_documents", [])

    if not documents:
        return

    with st.expander(f"Documentos Relevantes ({len(documents)})", expanded=False):
        render_documents_table(documents)


def render_documents_table(documents: List[Dict[str, Any]]) -> None:
    """
    Renderiza tabela de documentos recuperados.

    Args:
        documents: Lista de documentos com scores
    """
    if not documents:
        st.info("[INFO] Nenhum documento recuperado.")
        return

    # Preparar dados para DataFrame
    data = []
    for idx, doc in enumerate(documents, 1):
        content = doc.get("page_content", doc.get("content", ""))
        metadata = doc.get("metadata", {})
        score = doc.get("score", metadata.get("score", 0.0))

        data.append(
            {
                "#": idx,
                "Score": f"{score:.3f}",
                "Fonte": format_document_source(doc),
                "Conteudo": truncate_text(content, 150),
            }
        )

    # Criar DataFrame
    df = pd.DataFrame(data)

    # Exibir tabela
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn("#", width="small"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Fonte": st.column_config.TextColumn("Fonte", width="medium"),
            "Conteudo": st.column_config.TextColumn("Conteudo", width="large"),
        },
    )

    # Opcionalmente, mostrar documentos completos
    show_full = st.checkbox("Mostrar documentos completos", value=False)

    if show_full:
        for idx, doc in enumerate(documents, 1):
            with st.expander(f"Documento {idx}"):
                content = doc.get("page_content", doc.get("content", ""))
                st.markdown(content)
                st.caption(f"Score: {doc.get('score', 0.0):.3f}")


def render_judge_section(result: Dict[str, Any]) -> None:
    """
    Renderiza secao de avaliacao do Judge Agent.

    Args:
        result: Resultado do workflow
    """
    judge_evaluation = result.get("judge_evaluation", None)

    if not judge_evaluation:
        return

    verdict = judge_evaluation.get("verdict", "unknown")
    score = judge_evaluation.get("score", 0.0)
    feedback = judge_evaluation.get("feedback", "Sem feedback")
    issues = judge_evaluation.get("issues", [])
    suggestions = judge_evaluation.get("suggestions", [])

    # Determinar cor baseado no veredito
    if verdict == "approved":
        verdict_text = "APROVADO"
        verdict_color = "#2ca02c"  # Verde
        icon = "[OK]"
    elif verdict == "needs_refinement":
        verdict_text = "NECESSITA REFINAMENTO"
        verdict_color = "#ff7f0e"  # Laranja
        icon = "[WARN]"
    else:
        verdict_text = "REPROVADO"
        verdict_color = "#d62728"  # Vermelho
        icon = "[ERRO]"

    with st.expander("Avaliacao do Judge Agent", expanded=False):
        # Header com veredito
        st.markdown(
            f'<div style="background-color: {verdict_color}; padding: 15px; '
            f'border-radius: 5px; margin-bottom: 15px;">'
            f'<h3 style="color: white; margin: 0;">{icon} {verdict_text}</h3>'
            f'<p style="color: white; margin: 5px 0 0 0;">Score: {score:.2f}/1.0</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Metricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Score Geral", f"{score:.2f}")

        with col2:
            is_complete = judge_evaluation.get("is_complete", False)
            completeness_display = "Sim" if is_complete else "Nao"
            st.metric("Completude", completeness_display)

        with col3:
            is_grounded = judge_evaluation.get("is_grounded", False)
            grounding_display = "Sim" if is_grounded else "Nao"
            st.metric("Fundamentacao", grounding_display)

        with col4:
            has_sources = judge_evaluation.get("has_sources", False)
            sources_display = "Sim" if has_sources else "Nao"
            st.metric("Cita Fontes", sources_display)

        # Feedback
        st.markdown("**Feedback:**")
        st.markdown(feedback)

        # Issues (se houver)
        if issues:
            st.markdown("**Problemas Identificados:**")
            for issue in issues:
                st.warning(f"[WARN] {issue}")

        # Sugestoes (se houver)
        if suggestions:
            st.markdown("**Sugestoes de Melhoria:**")
            for suggestion in suggestions:
                st.info(f"[INFO] {suggestion}")

