"""Cores BSC consistentes para visualizacoes.

Paleta baseada em Material Design com alto contraste.
Seguir memoria [[10230062]] - Streamlit UI best practices.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

# Cores por perspectiva BSC (tons pasteis para backgrounds)
PERSPECTIVE_COLORS = {
    "Financeira": "#FFEBEE",  # Vermelho pastel
    "Clientes": "#FFF9C4",  # Amarelo pastel
    "Processos Internos": "#E3F2FD",  # Azul pastel
    "Aprendizado e Crescimento": "#E8F5E9",  # Verde pastel
}

# Cores por prioridade (Material Design - alto contraste)
PRIORITY_COLORS = {
    "HIGH": "#EF5350",  # Vermelho
    "MEDIUM": "#FFA726",  # Laranja
    "LOW": "#66BB6A",  # Verde
    "Alta": "#EF5350",  # Portugues
    "Media": "#FFA726",
    "Baixa": "#66BB6A",
}

# Cores por effort (tons azul-cinza)
EFFORT_COLORS = {
    "HIGH": "#546E7A",  # Azul-cinza escuro
    "MEDIUM": "#78909C",  # Azul-cinza medio
    "LOW": "#B0BEC5",  # Azul-cinza claro
}

# Cores para status (futuro)
STATUS_COLORS = {
    "TODO": "#BDBDBD",  # Cinza
    "IN_PROGRESS": "#42A5F5",  # Azul
    "COMPLETED": "#66BB6A",  # Verde
    "BLOCKED": "#EF5350",  # Vermelho
}

# Cores neutras (texto, backgrounds)
NEUTRAL_COLORS = {
    "dark_text": "#1f1f1f",  # Texto escuro
    "light_text": "#757575",  # Texto claro
    "background": "#f8f9fb",  # Background claro
    "border": "#e0e0e0",  # Bordas
    "white": "#ffffff",
}

# Cores para grafos (NetworkX edges)
GRAPH_COLORS = {
    "edge": "#888888",  # Cinza para arestas
    "edge_highlight": "#EF5350",  # Vermelho para highlight
    "node_border": "#424242",  # Borda dos nos
}


def get_perspective_color(perspective: str) -> str:
    """Retorna cor para perspectiva BSC.

    Args:
        perspective: Nome da perspectiva BSC

    Returns:
        Codigo hexadecimal da cor
    """
    return PERSPECTIVE_COLORS.get(perspective, NEUTRAL_COLORS["background"])


def get_priority_color(priority: str) -> str:
    """Retorna cor para prioridade.

    Args:
        priority: Prioridade (HIGH/MEDIUM/LOW ou Alta/Media/Baixa)

    Returns:
        Codigo hexadecimal da cor
    """
    return PRIORITY_COLORS.get(priority, NEUTRAL_COLORS["light_text"])


def get_effort_color(effort: str) -> str:
    """Retorna cor para esforco.

    Args:
        effort: Esforco (HIGH/MEDIUM/LOW)

    Returns:
        Codigo hexadecimal da cor
    """
    return EFFORT_COLORS.get(effort, NEUTRAL_COLORS["light_text"])
