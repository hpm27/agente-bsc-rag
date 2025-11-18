"""PdfExporter: Exporta diagnósticos BSC para PDF formatado profissionalmente.

Este módulo usa WeasyPrint para converter templates HTML (Jinja2) em PDF de alta qualidade.
Suporta export completo (4 perspectivas) ou por perspectiva individual.

Fase: 4.2 - Reports & Exports
Versão: 1.0
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

# Lazy import de WeasyPrint (requer GTK+ no Windows)
# Importar apenas quando métodos forem chamados
# from weasyprint import HTML, CSS
# from weasyprint.text.fonts import FontConfiguration

from src.exports.template_manager import TemplateManager
from src.memory.schemas import ClientProfile, CompleteDiagnostic

logger = logging.getLogger(__name__)


class PdfExporter:
    """Exporta diagnósticos BSC para PDF formatado profissionalmente.
    
    Usa WeasyPrint para converter templates HTML (Jinja2) em PDF de alta qualidade.
    Suporta export completo (4 perspectivas) ou por perspectiva individual.
    
    Attributes:
        template_manager: TemplateManager para renderizar HTML
        output_dir: Diretório padrão para salvar PDFs (default: "exports/pdf")
    
    Example:
        >>> template_manager = TemplateManager()
        >>> exporter = PdfExporter(template_manager)
        >>> pdf_path = exporter.export_full_diagnostic(diagnostic, profile)
        >>> print(f"PDF salvo em: {pdf_path}")
        PDF salvo em: exports/pdf/TechCorp_diagnostic_20251118_193045.pdf
    """
    
    def __init__(self, template_manager: TemplateManager, output_dir: str = "exports/pdf"):
        """Inicializa exporter com template manager.
        
        Args:
            template_manager: TemplateManager configurado
            output_dir: Diretório de saída para PDFs
        """
        self.template_manager = template_manager
        self.output_dir = Path(output_dir)
        
        # Criar diretório se não existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar fontes para WeasyPrint (lazy, quando necessário)
        self.font_config = None
    
    def export_full_diagnostic(
        self, 
        diagnostic: CompleteDiagnostic, 
        profile: ClientProfile,
        output_path: Optional[Path] = None
    ) -> Path:
        """Exporta diagnóstico BSC completo (4 perspectivas) para PDF.
        
        Gera PDF formatado profissionalmente com:
        - Capa com logo e dados da empresa
        - Executive summary
        - Análise detalhada das 4 perspectivas
        - Recomendações priorizadas
        - Cross-perspective synergies
        
        Args:
            diagnostic: CompleteDiagnostic com 4 perspectivas
            profile: ClientProfile com dados da empresa
            output_path: Caminho de saída (opcional). Se None, usa padrão:
                        {output_dir}/{company_name}_diagnostic_{timestamp}.pdf
        
        Returns:
            Path: Caminho completo do PDF gerado
        
        Raises:
            ValueError: Se diagnostic incompleto (missing perspectives)
            IOError: Se erro ao escrever arquivo
        
        Example:
            >>> exporter = PdfExporter(template_manager)
            >>> pdf_path = exporter.export_full_diagnostic(diagnostic, profile)
            >>> pdf_path.exists()
            True
        """
        logger.info(
            f"[PDF_EXPORT] Exportando diagnóstico completo | "
            f"company={profile.company.name}"
        )
        
        # Validar diagnostic completo
        self._validate_complete_diagnostic(diagnostic)
        
        # Determinar output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_slug = self._slugify(profile.company.name)
            filename = f"{company_slug}_diagnostic_{timestamp}.pdf"
            output_path = self.output_dir / filename
        
        # Renderizar HTML
        html_content = self.template_manager.render_full_diagnostic(
            diagnostic, profile
        )
        
        # Converter HTML → PDF
        self._html_to_pdf(html_content, output_path)
        
        logger.info(
            f"[PDF_EXPORT] Diagnóstico completo exportado com sucesso | "
            f"path={output_path} | size={output_path.stat().st_size} bytes"
        )
        
        return output_path
    
    def export_perspective(
        self, 
        diagnostic: CompleteDiagnostic, 
        profile: ClientProfile,
        perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"],
        output_path: Optional[Path] = None
    ) -> Path:
        """Exporta apenas 1 perspectiva BSC para PDF.
        
        Útil para reports focados em área específica (ex: C-level Financeiro).
        
        Args:
            diagnostic: CompleteDiagnostic completo
            profile: ClientProfile
            perspective: Nome da perspectiva a exportar
            output_path: Caminho de saída (opcional)
        
        Returns:
            Path: Caminho do PDF gerado
        
        Raises:
            ValueError: Se perspectiva inválida
            IOError: Se erro ao escrever arquivo
        
        Example:
            >>> pdf_path = exporter.export_perspective(
            ...     diagnostic, profile, perspective="Financeira"
            ... )
            >>> "Financeira" in pdf_path.name
            True
        """
        logger.info(
            f"[PDF_EXPORT] Exportando perspectiva | "
            f"company={profile.company.name} | perspective={perspective}"
        )
        
        # Validar perspectiva
        valid_perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        if perspective not in valid_perspectives:
            raise ValueError(
                f"Perspectiva inválida: {perspective}. "
                f"Válidas: {', '.join(valid_perspectives)}"
            )
        
        # Determinar output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            company_slug = self._slugify(profile.company.name)
            perspective_slug = self._slugify(perspective)
            filename = f"{company_slug}_{perspective_slug}_{timestamp}.pdf"
            output_path = self.output_dir / filename
        
        # Renderizar HTML
        html_content = self.template_manager.render_perspective(
            diagnostic, profile, perspective
        )
        
        # Converter HTML → PDF
        self._html_to_pdf(html_content, output_path)
        
        logger.info(
            f"[PDF_EXPORT] Perspectiva exportada com sucesso | "
            f"path={output_path} | size={output_path.stat().st_size} bytes"
        )
        
        return output_path
    
    # ========== MÉTODOS PRIVADOS ==========
    
    def _html_to_pdf(self, html_content: str, output_path: Path) -> None:
        """Converte HTML para PDF usando WeasyPrint.
        
        Args:
            html_content: HTML string renderizado
            output_path: Caminho de saída do PDF
        
        Raises:
            IOError: Se erro ao escrever arquivo
            ImportError: Se WeasyPrint não instalado ou GTK+ ausente (Windows)
        """
        try:
            # Import lazy de WeasyPrint (apenas quando necessário)
            try:
                from weasyprint import HTML
                from weasyprint.text.fonts import FontConfiguration
            except OSError as weasy_error:
                logger.error(
                    f"[PDF_EXPORT] WeasyPrint requer GTK+ no Windows. "
                    f"Veja docs/exports/WINDOWS_SETUP.md | Error: {weasy_error}"
                )
                raise ImportError(
                    "WeasyPrint requer GTK+ libraries. "
                    "No Windows, instale MSYS2 + GTK. "
                    "Veja: docs/exports/WINDOWS_SETUP.md"
                ) from weasy_error
            
            # Inicializar font_config se necessário
            if self.font_config is None:
                self.font_config = FontConfiguration()
            
            # Criar documento HTML
            html_doc = HTML(string=html_content)
            
            # Gerar PDF
            html_doc.write_pdf(
                target=str(output_path),
                font_config=self.font_config
            )
            
        except ImportError:
            raise  # Re-raise ImportError
        except Exception as e:
            logger.error(f"[PDF_EXPORT] Erro ao gerar PDF: {e}")
            raise IOError(f"Erro ao gerar PDF: {e}") from e
    
    def _validate_complete_diagnostic(self, diagnostic: CompleteDiagnostic) -> None:
        """Valida se diagnostic tem todas as 4 perspectivas.
        
        Args:
            diagnostic: CompleteDiagnostic a validar
        
        Raises:
            ValueError: Se alguma perspectiva está faltando
        """
        missing = []
        
        if not diagnostic.financial:
            missing.append("Financeira")
        if not diagnostic.customer:
            missing.append("Clientes")
        if not diagnostic.process:
            missing.append("Processos Internos")
        if not diagnostic.learning:
            missing.append("Aprendizado e Crescimento")
        
        if missing:
            raise ValueError(
                f"Diagnóstico incompleto. Perspectivas faltando: {', '.join(missing)}"
            )
    
    def _slugify(self, text: str) -> str:
        """Converte texto para slug válido para filename.
        
        Args:
            text: Texto a converter
        
        Returns:
            str: Slug (lowercase, sem espaços, sem acentos)
        
        Example:
            >>> exporter._slugify("TechCorp Brasil")
            'techcorp_brasil'
            >>> exporter._slugify("Processos Internos")
            'processos_internos'
        """
        import unicodedata
        import re
        
        # Normalizar acentos
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Lowercase + substituir espaços por underscore
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        
        return text.strip('_')

