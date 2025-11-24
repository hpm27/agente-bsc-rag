#!/usr/bin/env python3
"""
Teste rápido da visualização do Strategy Map
Valida que as melhorias visuais FASE 1 estão funcionando
"""

import sqlite3
import json
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar componente
from ui.components.bsc_network_graph import BSCNetworkGraph
from src.memory.schemas import StrategicObjective, CauseEffectConnection


def main():
    print("[INFO] Carregando Strategy Map do banco...")

    conn = sqlite3.connect("data/bsc_data.db")
    cursor = conn.cursor()

    # Buscar Strategy Map mais recente
    cursor.execute(
        """
        SELECT objectives, connections
        FROM strategy_maps
        ORDER BY created_at DESC
        LIMIT 1
    """
    )

    result = cursor.fetchone()

    if not result:
        print("[ERRO] Nenhum Strategy Map encontrado")
        return

    objectives_json, connections_json = result

    # Converter para Pydantic
    objectives_data = json.loads(objectives_json)
    connections_data = json.loads(connections_json)

    objectives = [StrategicObjective(**obj) for obj in objectives_data]
    connections = [CauseEffectConnection(**conn) for conn in connections_data]

    print(f"[OK] Carregados: {len(objectives)} objetivos, {len(connections)} conexoes")

    # Criar componente
    print("[INFO] Criando BSCNetworkGraph com conexoes...")
    graph = BSCNetworkGraph(objectives, connections=connections)

    # Build graph
    g = graph.build_graph()
    print(f"[OK] Grafo construido: {g.number_of_nodes()} nos, {g.number_of_edges()} arestas")

    # Criar figura Plotly
    print("[INFO] Criando figura Plotly com melhorias visuais...")
    fig = graph.create_plotly_figure()

    # Validar componentes visuais
    print("\n[VALIDACAO] Componentes visuais:")
    print(f"  - Annotations: {len(fig.layout.annotations)} (texto + setas + labels)")
    print(f"  - Shapes: {len(fig.layout.shapes)} (faixas de perspectiva)")
    print(f"  - Traces: {len(fig.data)} (nos + legenda)")
    print(f"  - Legenda: {fig.layout.showlegend}")

    # Contar tipos de annotations (Annotation é objeto Plotly, não dict)
    arrow_count = sum(
        1 for ann in fig.layout.annotations if hasattr(ann, "showarrow") and ann.showarrow
    )
    text_count = len(fig.layout.annotations) - arrow_count

    print(f"\n[OK] Setas direcionadas: {arrow_count}")
    print(f"[OK] Labels de texto: {text_count}")
    print(f"[OK] Faixas de perspectiva: {len(fig.layout.shapes)}")

    if arrow_count == 0:
        print("\n[ATENCAO] Nenhuma seta criada! Verificar mapeamento de IDs.")
    else:
        print(f"\n[SUCESSO] Strategy Map completo com {arrow_count} conexoes causa-efeito!")

    print("\n[INFO] Arestas no grafo NetworkX:")
    for i, (source, target, data) in enumerate(g.edges(data=True), 1):
        print(f"  {i}. {source[:40]}... -> {target[:40]}...")

    conn.close()


if __name__ == "__main__":
    main()
