"""CsvExporter: Exporta dados tabulares para CSV (lista clientes, métricas, etc).

Este módulo usa pandas DataFrame para manipulação e export robusto de dados.
Suporta encoding UTF-8, separadores customizados, e formatação brasileira.

Fase: 4.2 - Reports & Exports
Versão: 1.0
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.memory.schemas import ClientProfile, CompleteDiagnostic

logger = logging.getLogger(__name__)


class CsvExporter:
    """Exporta dados tabulares para CSV (lista clientes, métricas, etc).

    Usa pandas DataFrame para manipulação e export robusto.
    Suporta encoding UTF-8, separadores customizados.

    Attributes:
        output_dir: Diretório padrão para CSVs (default: "exports/csv")
        encoding: Encoding padrão (default: "utf-8-sig" para Excel compatibility)
        separator: Separador CSV (default: ",")

    Example:
        >>> exporter = CsvExporter()
        >>> csv_path = exporter.export_clients_list(profiles)
        >>> print(f"CSV salvo em: {csv_path}")
        CSV salvo em: exports/csv/clients_list_20251118_193045.csv
    """

    def __init__(
        self, output_dir: str = "exports/csv", encoding: str = "utf-8-sig", separator: str = ","
    ):
        """Inicializa exporter com configurações padrão.

        Args:
            output_dir: Diretório de saída para CSVs
            encoding: Encoding do CSV (utf-8-sig para Excel)
            separator: Separador de colunas (vírgula por padrão)
        """
        self.output_dir = Path(output_dir)
        self.encoding = encoding
        self.separator = separator

        # Criar diretório se não existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_clients_list(
        self, profiles: list[ClientProfile], output_path: Path | None = None
    ) -> Path:
        """Exporta lista de clientes para CSV.

        Colunas geradas:
        - client_id
        - company_name
        - sector
        - size
        - current_phase (ONBOARDING, DISCOVERY, etc)
        - approval_status (APPROVED, PENDING, etc)
        - created_at
        - updated_at
        - total_challenges
        - total_objectives

        Args:
            profiles: Lista de ClientProfile
            output_path: Caminho de saída (opcional). Se None:
                        {output_dir}/clients_list_{timestamp}.csv

        Returns:
            Path: Caminho do CSV gerado

        Raises:
            ValueError: Se profiles vazio
            IOError: Se erro ao escrever arquivo

        Example:
            >>> exporter = CsvExporter()
            >>> csv_path = exporter.export_clients_list(profiles)
            >>> csv_path.exists()
            True
        """
        logger.info(f"[CSV_EXPORT] Exportando lista de clientes | count={len(profiles)}")

        if not profiles:
            raise ValueError("Lista de profiles vazia. Nada para exportar.")

        # Determinar output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clients_list_{timestamp}.csv"
            output_path = self.output_dir / filename

        # Construir DataFrame
        data = []
        for profile in profiles:
            row = {
                "client_id": profile.client_id,
                "company_name": profile.company.name,
                "sector": profile.company.sector,
                "size": profile.company.size if profile.company.size else "N/A",
                "current_phase": profile.engagement.current_phase if profile.engagement else "N/A",
                "approval_status": (
                    profile.metadata.get("approval_status", "N/A") if profile.metadata else "N/A"
                ),  # approval_status está em metadata
                "created_at": (
                    profile.created_at.strftime("%d/%m/%Y %H:%M") if profile.created_at else "N/A"
                ),
                "updated_at": (
                    profile.updated_at.strftime("%d/%m/%Y %H:%M") if profile.updated_at else "N/A"
                ),
                "total_challenges": (
                    len(profile.context.current_challenges)
                    if profile.context and profile.context.current_challenges
                    else 0
                ),
                "total_objectives": (
                    len(profile.context.strategic_objectives)
                    if profile.context and profile.context.strategic_objectives
                    else 0
                ),
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Exportar para CSV
        df.to_csv(output_path, sep=self.separator, encoding=self.encoding, index=False)

        logger.info(
            f"[CSV_EXPORT] Lista de clientes exportada | "
            f"path={output_path} | rows={len(df)} | size={output_path.stat().st_size} bytes"
        )

        return output_path

    def export_recommendations(
        self,
        diagnostic: CompleteDiagnostic,
        profile: ClientProfile,
        output_path: Path | None = None,
    ) -> Path:
        """Exporta recomendações priorizadas para CSV.

        Colunas:
        - company_name
        - priority (HIGH, MEDIUM, LOW)
        - title
        - description
        - impact (HIGH, MEDIUM, LOW)
        - effort (HIGH, MEDIUM, LOW)
        - quick_win (True/False)
        - timeframe
        - expected_outcomes (concatenado)

        Útil para tracking de implementação.

        Args:
            diagnostic: CompleteDiagnostic com recommendations
            profile: ClientProfile (para metadata)
            output_path: Caminho de saída (opcional)

        Returns:
            Path: Caminho do CSV gerado

        Raises:
            ValueError: Se diagnostic sem recomendações
            IOError: Se erro ao escrever arquivo

        Example:
            >>> csv_path = exporter.export_recommendations(diagnostic, profile)
            >>> csv_path.exists()
            True
        """
        logger.info(
            f"[CSV_EXPORT] Exportando recomendações | "
            f"company={profile.company.name} | count={len(diagnostic.recommendations)}"
        )

        if not diagnostic.recommendations:
            raise ValueError("Diagnostic sem recomendações. Nada para exportar.")

        # Determinar output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_slug = self._slugify(profile.company.name)
            filename = f"{company_slug}_recommendations_{timestamp}.csv"
            output_path = self.output_dir / filename

        # Construir DataFrame
        data = []
        for i, rec in enumerate(diagnostic.recommendations, 1):
            row = {
                "order": i,
                "company_name": profile.company.name,
                "priority": rec.priority,
                "title": rec.title,
                "description": rec.description,
                "impact": rec.impact,
                "effort": rec.effort,
                "quick_win": rec.quick_win,
                "timeframe": rec.timeframe,
                "expected_outcomes": (
                    " | ".join(rec.expected_outcomes) if rec.expected_outcomes else "N/A"
                ),
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Ordenar por priority (HIGH > MEDIUM > LOW)
        priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        df["priority_rank"] = df["priority"].map(priority_order)
        df = df.sort_values("priority_rank").drop(columns=["priority_rank"])

        # Exportar para CSV
        df.to_csv(output_path, sep=self.separator, encoding=self.encoding, index=False)

        logger.info(
            f"[CSV_EXPORT] Recomendações exportadas | "
            f"path={output_path} | rows={len(df)} | size={output_path.stat().st_size} bytes"
        )

        return output_path

    def export_perspectives_summary(
        self,
        diagnostic: CompleteDiagnostic,
        profile: ClientProfile,
        output_path: Path | None = None,
    ) -> Path:
        """Exporta resumo das 4 perspectivas BSC para CSV.

        Colunas:
        - perspective (Financeira, Clientes, etc)
        - priority (HIGH, MEDIUM, LOW)
        - total_gaps
        - total_opportunities
        - current_state (truncado)

        Args:
            diagnostic: CompleteDiagnostic completo
            profile: ClientProfile
            output_path: Caminho de saída (opcional)

        Returns:
            Path: Caminho do CSV gerado
        """
        logger.info(
            f"[CSV_EXPORT] Exportando resumo perspectivas | " f"company={profile.company.name}"
        )

        # Determinar output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_slug = self._slugify(profile.company.name)
            filename = f"{company_slug}_perspectives_{timestamp}.csv"
            output_path = self.output_dir / filename

        # Construir DataFrame
        perspectives = [
            ("Financeira", diagnostic.financial),
            ("Clientes", diagnostic.customer),
            ("Processos Internos", diagnostic.process),
            ("Aprendizado e Crescimento", diagnostic.learning),
        ]

        data = []
        for name, persp in perspectives:
            row = {
                "perspective": name,
                "priority": persp.priority,
                "total_gaps": len(persp.gaps) if persp.gaps else 0,
                "total_opportunities": len(persp.opportunities) if persp.opportunities else 0,
                "current_state": (
                    persp.current_state[:200] + "..."
                    if len(persp.current_state) > 200
                    else persp.current_state
                ),
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Exportar para CSV
        df.to_csv(output_path, sep=self.separator, encoding=self.encoding, index=False)

        logger.info(
            f"[CSV_EXPORT] Resumo perspectivas exportado | "
            f"path={output_path} | size={output_path.stat().st_size} bytes"
        )

        return output_path

    # ========== MÉTODOS PRIVADOS ==========

    def _slugify(self, text: str) -> str:
        """Converte texto para slug válido para filename.

        Args:
            text: Texto a converter

        Returns:
            str: Slug (lowercase, sem espaços, sem acentos)
        """
        import re
        import unicodedata

        # Normalizar acentos
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")

        # Lowercase + substituir espaços por underscore
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "_", text)

        return text.strip("_")
