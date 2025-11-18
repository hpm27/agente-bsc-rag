"""Módulo de exports (PDF, CSV) para relatórios BSC.

Este módulo fornece funcionalidades para exportar diagnósticos BSC e dados
de clientes em formatos profissionais (PDF com WeasyPrint, CSV com pandas).

Classes principais:
- PdfExporter: Export diagnósticos para PDF formatado
- CsvExporter: Export dados tabulares para CSV
- TemplateManager: Gerencia templates Jinja2 para HTML

Usage:
    >>> from src.exports import PdfExporter, CsvExporter, TemplateManager
    >>> 
    >>> # PDF Export
    >>> template_manager = TemplateManager()
    >>> pdf_exporter = PdfExporter(template_manager)
    >>> pdf_path = pdf_exporter.export_full_diagnostic(diagnostic, profile)
    >>> 
    >>> # CSV Export
    >>> csv_exporter = CsvExporter()
    >>> csv_path = csv_exporter.export_clients_list(profiles)

Fase: 4.2 - Reports & Exports
Versão: 1.0
Data: 2025-11-18
"""

from src.exports.pdf_exporter import PdfExporter
from src.exports.csv_exporter import CsvExporter
from src.exports.template_manager import TemplateManager

__all__ = [
    "PdfExporter",
    "CsvExporter",
    "TemplateManager",
]

__version__ = "1.0.0"

