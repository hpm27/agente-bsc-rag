"""TemplateManager: Gerencia templates Jinja2 para relatórios BSC.

Este módulo fornece gerenciamento centralizado de templates HTML usando Jinja2,
com filtros customizados para formatação brasileira e contexto rico para exports.

Fase: 4.2 - Reports & Exports
Versão: 1.0
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from jinja2 import Environment, FileSystemLoader, Template

from src.memory.schemas import ClientProfile, CompleteDiagnostic


class TemplateManager:
    """Gerencia templates Jinja2 para geração de relatórios HTML.

    Carrega templates do diretório templates/reports/ e renderiza
    com contexto (diagnostic, profile, metadata).

    Suporta herança de templates (base.html) e filtros customizados para
    formatação brasileira (datas, moeda, números).

    Attributes:
        env: Jinja2 Environment configurado
        template_dir: Diretório dos templates (default: "templates/reports")

    Example:
        >>> manager = TemplateManager()
        >>> html = manager.render_full_diagnostic(diagnostic, profile)
        >>> len(html) > 1000  # HTML renderizado
        True
    """

    def __init__(self, template_dir: str = "templates/reports"):
        """Inicializa manager com diretório de templates.

        Args:
            template_dir: Diretório contendo templates .html

        Raises:
            FileNotFoundError: Se template_dir não existe
        """
        template_path = Path(template_dir)

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template directory não encontrado: {template_path.absolute()}"
            )

        # Configurar Jinja2 Environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=True,  # Segurança - escape HTML automaticamente
            trim_blocks=True,  # Remove primeiro \n após tag block
            lstrip_blocks=True,  # Remove whitespace antes de tags block
        )

        self.template_dir = template_dir

        # Registrar filtros customizados
        self.env.filters["format_date"] = self._format_date
        self.env.filters["format_datetime"] = self._format_datetime
        self.env.filters["format_number"] = self._format_number
        self.env.filters["priority_badge"] = self._priority_badge_class

    def render_full_diagnostic(
        self,
        diagnostic: CompleteDiagnostic,
        profile: ClientProfile,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Renderiza diagnóstico completo para HTML.

        Usa template 'diagnostic_full.html' que herda de 'base.html'.
        Injeta dados do diagnostic e profile no contexto.

        Args:
            diagnostic: CompleteDiagnostic com 4 perspectivas
            profile: ClientProfile com dados da empresa
            metadata: Dict opcional com metadados extras (ex: gerado_em, versão)

        Returns:
            str: HTML renderizado pronto para WeasyPrint

        Raises:
            TemplateNotFound: Se template 'diagnostic_full.html' não existe
            ValidationError: Se diagnostic ou profile inválidos

        Example:
            >>> manager = TemplateManager()
            >>> html = manager.render_full_diagnostic(diagnostic, profile)
            >>> "Executive Summary" in html
            True
            >>> profile.company.name in html
            True
        """
        template = self.env.get_template("diagnostic_full.html")

        # Preparar contexto
        context = {
            "diagnostic": diagnostic,
            "profile": profile,
            "now": datetime.now(),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "metadata": metadata or {},
            # Helpers para template
            "perspective_names": {
                "financial": "Financeira",
                "customer": "Clientes",
                "process": "Processos Internos",
                "learning": "Aprendizado e Crescimento",
            },
        }

        html = template.render(**context)
        return html

    def render_perspective(
        self,
        diagnostic: CompleteDiagnostic,
        profile: ClientProfile,
        perspective: Literal[
            "Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"
        ],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Renderiza apenas 1 perspectiva para HTML.

        Usa template 'diagnostic_perspective.html'.

        Args:
            diagnostic: CompleteDiagnostic completo
            profile: ClientProfile
            perspective: Nome da perspectiva (ex: "Financeira")
            metadata: Dict opcional

        Returns:
            str: HTML renderizado da perspectiva

        Raises:
            TemplateNotFound: Se template não existe
            ValueError: Se perspectiva inválida

        Example:
            >>> html = manager.render_perspective(
            ...     diagnostic, profile, perspective="Financeira"
            ... )
            >>> "Financeira" in html
            True
        """
        # Validar perspectiva
        valid_perspectives = [
            "Financeira",
            "Clientes",
            "Processos Internos",
            "Aprendizado e Crescimento",
        ]
        if perspective not in valid_perspectives:
            raise ValueError(
                f"Perspectiva inválida: {perspective}. " f"Válidas: {', '.join(valid_perspectives)}"
            )

        template = self.env.get_template("diagnostic_perspective.html")

        # Mapear nome perspectiva para campo do diagnostic
        perspective_map = {
            "Financeira": diagnostic.financial,
            "Clientes": diagnostic.customer,
            "Processos Internos": diagnostic.process,
            "Aprendizado e Crescimento": diagnostic.learning,
        }

        perspective_result = perspective_map[perspective]

        context = {
            "diagnostic": diagnostic,
            "profile": profile,
            "perspective": perspective_result,
            "perspective_name": perspective,
            "now": datetime.now(),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "metadata": metadata or {},
        }

        html = template.render(**context)
        return html

    # ========== FILTROS JINJA2 CUSTOMIZADOS ==========

    def _format_date(self, dt: datetime) -> str:
        """Filtro Jinja2 customizado para formatar datas brasileiras.

        Args:
            dt: datetime object

        Returns:
            str: Data formatada "DD/MM/AAAA"

        Example:
            >>> from datetime import datetime
            >>> manager = TemplateManager()
            >>> dt = datetime(2025, 11, 18)
            >>> manager._format_date(dt)
            '18/11/2025'
        """
        if dt is None:
            return "N/A"

        if isinstance(dt, str):
            # Se já é string, retornar como está
            return dt

        try:
            return dt.strftime("%d/%m/%Y")
        except AttributeError:
            return str(dt)

    def _format_datetime(self, dt: datetime) -> str:
        """Filtro para formatar data/hora completa.

        Args:
            dt: datetime object

        Returns:
            str: Data/hora formatada "DD/MM/AAAA HH:MM"
        """
        if dt is None:
            return "N/A"

        if isinstance(dt, str):
            return dt

        try:
            return dt.strftime("%d/%m/%Y %H:%M")
        except AttributeError:
            return str(dt)

    def _format_number(self, value: float, decimals: int = 2) -> str:
        """Filtro para formatar números no padrão brasileiro.

        Args:
            value: Número a formatar
            decimals: Casas decimais (default: 2)

        Returns:
            str: Número formatado "1.234,56"

        Example:
            >>> manager = TemplateManager()
            >>> manager._format_number(1234.56)
            '1.234,56'
        """
        if value is None:
            return "N/A"

        try:
            # Formatar com separador de milhares (ponto) e decimais (vírgula)
            formatted = f"{float(value):,.{decimals}f}"
            # Substituir separadores para padrão BR
            formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted
        except (ValueError, TypeError):
            return str(value)

    def _priority_badge_class(self, priority: str) -> str:
        """Filtro para mapear priority para classe CSS de badge.

        Args:
            priority: Priority (HIGH, MEDIUM, LOW)

        Returns:
            str: Classe CSS ("badge-high", "badge-medium", "badge-low")

        Example:
            >>> manager = TemplateManager()
            >>> manager._priority_badge_class("HIGH")
            'badge-high'
        """
        priority_upper = str(priority).upper()

        mapping = {
            "HIGH": "badge-high",
            "MEDIUM": "badge-medium",
            "LOW": "badge-low",
        }

        return mapping.get(priority_upper, "badge-medium")  # Default: medium

    def get_template(self, template_name: str) -> Template:
        """Carrega template pelo nome.

        Args:
            template_name: Nome do arquivo template (ex: "base.html")

        Returns:
            Template: Template Jinja2 carregado

        Raises:
            TemplateNotFound: Se template não existe
        """
        return self.env.get_template(template_name)

    def list_templates(self) -> list[str]:
        """Lista todos templates disponíveis.

        Returns:
            list[str]: Nomes dos templates .html

        Example:
            >>> manager = TemplateManager()
            >>> templates = manager.list_templates()
            >>> "base.html" in templates
            True
        """
        template_path = Path(self.template_dir)
        templates = [f.name for f in template_path.glob("*.html") if f.is_file()]
        return sorted(templates)
