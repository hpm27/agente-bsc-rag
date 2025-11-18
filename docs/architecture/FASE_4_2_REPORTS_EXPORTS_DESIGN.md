# FASE 4.2 - Reports & Exports: Design Técnico

**Data:** 2025-11-18  
**Versão:** 1.0  
**Status:** 📐 DESIGN APROVADO - Pronto para implementação

---

## 🎯 Objetivos

Implementar sistema completo de exports e relatórios profissionais para diagnósticos BSC:

1. **PDF Export** - Diagnósticos BSC completos formatados profissionalmente
2. **CSV Export** - Lista de clientes do dashboard (pandas DataFrame)
3. **Templates Jinja2** - HTML intermediário para consistência visual
4. **Integração Streamlit** - Botões de download no dashboard e páginas de diagnóstico

**Estimativa:** 3-4h (1 sessão)  
**Dependências:** FASE 4.1 completa (Multi-Client Dashboard) ✅

---

## 📊 Stack Tecnológico (Decisões Fundamentadas)

### **1. WeasyPrint para PDF Export**

**Escolha:** WeasyPrint  
**Alternativas consideradas:** ReportLab, pdfkit, xhtml2pdf

**Razões:**
- ✅ Converte HTML/CSS → PDF (templates Jinja2 reutilizáveis)
- ✅ Suporta CSS moderno (Flexbox, Grid)
- ✅ Manutenção mais fácil que ReportLab (low-level API)
- ✅ Output profissional (fontes, cores, layouts complexos)
- ✅ Open-source, ativo (last update 2024)

**Instalação:**
```bash
pip install weasyprint==62.3  # Python 3.12 compatible
```

---

### **2. Jinja2 para Templates**

**Escolha:** Jinja2  
**Razões:**
- ✅ Padrão da indústria Python (Flask, Django, Ansible)
- ✅ Sintaxe clara e poderosa (loops, condicionais, filtros)
- ✅ Herança de templates (base.html → report.html)
- ✅ Auto-escaping para segurança
- ✅ Já instalado (dependência Streamlit)

**Uso:**
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates/reports"))
template = env.get_template("diagnostic_report.html")
html = template.render(diagnostic=diagnostic, profile=profile)
```

---

### **3. pandas para CSV Export**

**Escolha:** pandas  
**Razões:**
- ✅ Standard para manipulação tabular
- ✅ `.to_csv()` robusto (encoding, separators, etc)
- ✅ Já instalado (projeto usa pandas)

---

## 🗂️ Estrutura de Arquivos (Nova)

```
agente-bsc-rag/
├── src/
│   └── exports/                    # NOVO - Módulo de exports
│       ├── __init__.py
│       ├── pdf_exporter.py         # PdfExporter class
│       ├── csv_exporter.py         # CsvExporter class
│       └── template_manager.py     # TemplateManager class
│
├── templates/                      # NOVO - Templates Jinja2
│   └── reports/
│       ├── base.html               # Template base (header, footer, CSS)
│       ├── diagnostic_full.html    # Diagnóstico BSC completo
│       ├── diagnostic_perspective.html  # 1 perspectiva (Financial, Customer, etc)
│       └── styles.css              # CSS compartilhado
│
├── tests/
│   └── test_exports/               # NOVO - Testes de exports
│       ├── test_pdf_exporter.py    # 10+ testes unitários PDF
│       ├── test_csv_exporter.py    # 8+ testes unitários CSV
│       └── test_template_manager.py # 8+ testes templates
│
└── docs/
    ├── architecture/
    │   └── FASE_4_2_REPORTS_EXPORTS_DESIGN.md  # Este documento
    └── exports/                    # NOVO - Docs de exports
        └── EXPORT_GUIDE.md         # Guia de uso dos exports

```

---

## 🔧 Contratos de API (3 Classes Principais)

### **1. PdfExporter** (`src/exports/pdf_exporter.py`)

```python
from typing import Optional
from pathlib import Path
from src.memory.schemas import CompleteDiagnostic, ClientProfile

class PdfExporter:
    """Exporta diagnósticos BSC para PDF formatado profissionalmente.
    
    Usa WeasyPrint para converter templates HTML (Jinja2) em PDF de alta qualidade.
    Suporta export completo (4 perspectivas) ou por perspectiva individual.
    
    Attributes:
        template_manager: TemplateManager para renderizar HTML
        output_dir: Diretório padrão para salvar PDFs (default: "exports/pdf")
    """
    
    def __init__(self, template_manager: TemplateManager, output_dir: str = "exports/pdf"):
        """Inicializa exporter com template manager.
        
        Args:
            template_manager: TemplateManager configurado
            output_dir: Diretório de saída para PDFs
        """
        pass
    
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
            >>> print(f"PDF salvo em: {pdf_path}")
            PDF salvo em: exports/pdf/TechCorp_diagnostic_20251118_193045.pdf
        """
        pass
    
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
        
        Example:
            >>> pdf_path = exporter.export_perspective(
            ...     diagnostic, profile, perspective="Financeira"
            ... )
        """
        pass
```

---

### **2. CsvExporter** (`src/exports/csv_exporter.py`)

```python
import pandas as pd
from typing import List, Optional
from pathlib import Path
from src.memory.schemas import ClientProfile

class CsvExporter:
    """Exporta dados tabulares para CSV (lista clientes, métricas, etc).
    
    Usa pandas DataFrame para manipulação e export robusto.
    Suporta encoding UTF-8, separadores customizados.
    
    Attributes:
        output_dir: Diretório padrão para CSVs (default: "exports/csv")
        encoding: Encoding padrão (default: "utf-8-sig" para Excel compatibility)
        separator: Separador CSV (default: ",")
    """
    
    def __init__(
        self, 
        output_dir: str = "exports/csv",
        encoding: str = "utf-8-sig",
        separator: str = ","
    ):
        """Inicializa exporter com configurações padrão."""
        pass
    
    def export_clients_list(
        self, 
        profiles: List[ClientProfile], 
        output_path: Optional[Path] = None
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
        
        Example:
            >>> exporter = CsvExporter()
            >>> csv_path = exporter.export_clients_list(profiles)
            >>> print(f"CSV salvo em: {csv_path}")
            CSV salvo em: exports/csv/clients_list_20251118_193045.csv
        """
        pass
    
    def export_recommendations(
        self, 
        diagnostic: CompleteDiagnostic, 
        profile: ClientProfile,
        output_path: Optional[Path] = None
    ) -> Path:
        """Exporta recomendações priorizadas para CSV.
        
        Colunas:
        - priority (HIGH, MEDIUM, LOW)
        - title
        - description
        - impact (HIGH, MEDIUM, LOW)
        - effort (HIGH, MEDIUM, LOW)
        - quick_win (True/False)
        - timeframe
        - perspective (Financeira, Clientes, etc)
        
        Útil para tracking de implementação.
        
        Args:
            diagnostic: CompleteDiagnostic com recommendations
            profile: ClientProfile (para metadata)
            output_path: Caminho de saída (opcional)
        
        Returns:
            Path: Caminho do CSV gerado
        """
        pass
```

---

### **3. TemplateManager** (`src/exports/template_manager.py`)

```python
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any
from src.memory.schemas import CompleteDiagnostic, ClientProfile

class TemplateManager:
    """Gerencia templates Jinja2 para geração de relatórios HTML.
    
    Carrega templates do diretório templates/reports/ e renderiza
    com contexto (diagnostic, profile, metadata).
    
    Suporta herança de templates (base.html) e filtros customizados.
    
    Attributes:
        env: Jinja2 Environment configurado
        template_dir: Diretório dos templates (default: "templates/reports")
    """
    
    def __init__(self, template_dir: str = "templates/reports"):
        """Inicializa manager com diretório de templates.
        
        Args:
            template_dir: Diretório contendo templates .html
        
        Raises:
            FileNotFoundError: Se template_dir não existe
        """
        pass
    
    def render_full_diagnostic(
        self, 
        diagnostic: CompleteDiagnostic, 
        profile: ClientProfile,
        metadata: Optional[Dict[str, Any]] = None
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
        
        Example:
            >>> manager = TemplateManager()
            >>> html = manager.render_full_diagnostic(diagnostic, profile)
            >>> len(html)
            15234  # ~15KB HTML
        """
        pass
    
    def render_perspective(
        self, 
        diagnostic: CompleteDiagnostic, 
        profile: ClientProfile,
        perspective: str,
        metadata: Optional[Dict[str, Any]] = None
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
        """
        pass
    
    def _format_date(self, dt: datetime) -> str:
        """Filtro Jinja2 customizado para formatar datas brasileiras.
        
        Args:
            dt: datetime object
        
        Returns:
            str: Data formatada "DD/MM/AAAA HH:MM"
        """
        pass
```

---

## 🎨 Templates Jinja2 (Estrutura)

### **1. base.html** - Template Base

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Relatório BSC{% endblock %}</title>
    <style>
        /* CSS embutido para WeasyPrint */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 20mm;
            color: #1f1f1f;
            font-size: 11pt;
            line-height: 1.6;
        }
        
        h1 { color: #2563eb; font-size: 24pt; margin-bottom: 10mm; }
        h2 { color: #1e40af; font-size: 18pt; margin-top: 8mm; }
        h3 { color: #3b82f6; font-size: 14pt; margin-top: 6mm; }
        
        .header {
            border-bottom: 2px solid #2563eb;
            padding-bottom: 5mm;
            margin-bottom: 10mm;
        }
        
        .footer {
            position: fixed;
            bottom: 10mm;
            left: 20mm;
            right: 20mm;
            border-top: 1px solid #e5e7eb;
            padding-top: 2mm;
            font-size: 9pt;
            color: #6b7280;
        }
        
        .badge {
            display: inline-block;
            padding: 2mm 4mm;
            border-radius: 2mm;
            font-weight: 600;
            font-size: 9pt;
        }
        
        .badge-high { background: #fecaca; color: #991b1b; }
        .badge-medium { background: #fed7aa; color: #9a3412; }
        .badge-low { background: #d1fae5; color: #065f46; }
        
        /* Mais estilos... */
    </style>
</head>
<body>
    <div class="header">
        <h1>{% block header_title %}{% endblock %}</h1>
        <p><strong>Empresa:</strong> {{ profile.company.name }} | <strong>Gerado em:</strong> {{ now | format_date }}</p>
    </div>
    
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    
    <div class="footer">
        <p>Agente BSC RAG | Balanced Scorecard Consulting | Pág. <span class="page-number"></span></p>
    </div>
</body>
</html>
```

---

### **2. diagnostic_full.html** - Diagnóstico Completo

```html
{% extends "base.html" %}

{% block title %}Diagnóstico BSC - {{ profile.company.name }}{% endblock %}

{% block header_title %}Diagnóstico BSC Completo{% endblock %}

{% block content %}
    <section class="executive-summary">
        <h2>Executive Summary</h2>
        <p>{{ diagnostic.executive_summary }}</p>
    </section>
    
    <section class="perspectives">
        <h2>Análise por Perspectiva</h2>
        
        {% for perspective_name in ["financial", "customer", "process", "learning"] %}
            {% set perspective = diagnostic[perspective_name] %}
            <div class="perspective">
                <h3>{{ perspective.perspective }}</h3>
                <span class="badge badge-{{ perspective.priority | lower }}">{{ perspective.priority }}</span>
                
                <h4>Estado Atual</h4>
                <p>{{ perspective.current_state }}</p>
                
                <h4>Gaps Identificados</h4>
                <ul>
                    {% for gap in perspective.gaps %}
                    <li>{{ gap }}</li>
                    {% endfor %}
                </ul>
                
                <h4>Oportunidades</h4>
                <ul>
                    {% for opp in perspective.opportunities %}
                    <li>{{ opp }}</li>
                    {% endfor %}
                </ul>
            </div>
        {% endfor %}
    </section>
    
    <section class="recommendations">
        <h2>Recomendações Priorizadas</h2>
        <p><strong>Total:</strong> {{ diagnostic.recommendations | length }} recomendações</p>
        
        {% for rec in diagnostic.recommendations %}
            <div class="recommendation">
                <h4>{{ loop.index }}. {{ rec.title }}</h4>
                <span class="badge badge-{{ rec.impact | lower }}">Impacto: {{ rec.impact }}</span>
                <span class="badge badge-{{ rec.effort | lower }}">Esforço: {{ rec.effort }}</span>
                {% if rec.quick_win %}
                <span class="badge badge-high">Quick Win</span>
                {% endif %}
                
                <p>{{ rec.description }}</p>
                <p><strong>Timeframe:</strong> {{ rec.timeframe }}</p>
            </div>
        {% endfor %}
    </section>
    
    {% if diagnostic.cross_perspective_synergies %}
    <section class="synergies">
        <h2>Sinergias Cross-Perspective</h2>
        <ul>
            {% for synergy in diagnostic.cross_perspective_synergies %}
            <li>{{ synergy }}</li>
            {% endfor %}
        </ul>
    </section>
    {% endif %}
{% endblock %}
```

---

## 🔌 Integração Streamlit

### **1. Página de Diagnóstico** (`src/ui/pages/diagnostic_detail.py`)

```python
import streamlit as st
from src.exports.pdf_exporter import PdfExporter
from src.exports.csv_exporter import CsvExporter
from src.exports.template_manager import TemplateManager

def render_diagnostic_detail(diagnostic: CompleteDiagnostic, profile: ClientProfile):
    """Renderiza página de detalhe do diagnóstico com botões de export."""
    
    st.header(f"Diagnóstico BSC - {profile.company.name}")
    
    # Botões de export no topo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Exportar PDF Completo"):
            # Gerar PDF
            template_manager = TemplateManager()
            pdf_exporter = PdfExporter(template_manager)
            pdf_path = pdf_exporter.export_full_diagnostic(diagnostic, profile)
            
            # Download button
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=f.read(),
                    file_name=pdf_path.name,
                    mime="application/pdf"
                )
            
            st.success(f"PDF gerado com sucesso! ({pdf_path.name})")
    
    with col2:
        if st.button("📊 Exportar Recomendações CSV"):
            # Gerar CSV
            csv_exporter = CsvExporter()
            csv_path = csv_exporter.export_recommendations(diagnostic, profile)
            
            # Download button
            with open(csv_path, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar CSV",
                    data=f.read(),
                    file_name=csv_path.name,
                    mime="text/csv"
                )
            
            st.success(f"CSV gerado com sucesso! ({csv_path.name})")
    
    with col3:
        # Selector de perspectiva
        perspective = st.selectbox(
            "Exportar Perspectiva Individual:",
            ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        )
        
        if st.button("📄 Exportar PDF Perspectiva"):
            pdf_exporter = PdfExporter(TemplateManager())
            pdf_path = pdf_exporter.export_perspective(diagnostic, profile, perspective)
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar PDF Perspectiva",
                    data=f.read(),
                    file_name=pdf_path.name,
                    mime="application/pdf"
                )
    
    # Resto da página (exibir diagnostic)...
```

---

### **2. Dashboard** (`src/ui/pages/multi_client_dashboard.py`)

```python
# Adicionar botão de export CSV da lista de clientes

if st.button("📊 Exportar Lista Clientes CSV"):
    csv_exporter = CsvExporter()
    csv_path = csv_exporter.export_clients_list(all_profiles)
    
    with open(csv_path, "rb") as f:
        st.download_button(
            label="⬇️ Baixar Lista Clientes",
            data=f.read(),
            file_name=csv_path.name,
            mime="text/csv"
        )
```

---

## 🧪 Estratégia de Testes

### **1. Testes Unitários** (26+ testes total)

#### **test_pdf_exporter.py** (10 testes)
- ✅ `test_export_full_diagnostic_success()` - Export completo bem-sucedido
- ✅ `test_export_full_diagnostic_generates_pdf_file()` - Arquivo PDF criado
- ✅ `test_export_full_diagnostic_uses_custom_output_path()` - Path customizado respeitado
- ✅ `test_export_perspective_financial()` - Export perspectiva Financeira
- ✅ `test_export_perspective_customer()` - Export perspectiva Clientes
- ✅ `test_export_invalid_perspective_raises_error()` - Valida perspectiva inválida
- ✅ `test_export_incomplete_diagnostic_raises_error()` - Valida diagnostic incompleto
- ✅ `test_pdf_contains_company_name()` - PDF contém nome da empresa
- ✅ `test_pdf_contains_all_4_perspectives()` - PDF completo tem 4 perspectivas
- ✅ `test_pdf_file_size_reasonable()` - Tamanho PDF ~200-500KB (não > 1MB)

#### **test_csv_exporter.py** (8 testes)
- ✅ `test_export_clients_list_success()` - CSV criado
- ✅ `test_export_clients_list_has_correct_columns()` - Colunas esperadas presentes
- ✅ `test_export_clients_list_row_count()` - Número de linhas = len(profiles)
- ✅ `test_export_clients_list_encoding_utf8()` - Encoding UTF-8 correto
- ✅ `test_export_recommendations_success()` - CSV recomendações criado
- ✅ `test_export_recommendations_priority_high_first()` - Ordenação por priority
- ✅ `test_empty_profiles_list_creates_empty_csv()` - Lista vazia = CSV header only
- ✅ `test_csv_parseable_by_pandas()` - CSV pode ser lido de volta por pandas

#### **test_template_manager.py** (8 testes)
- ✅ `test_template_manager_loads_templates()` - Templates carregados
- ✅ `test_render_full_diagnostic_returns_html()` - HTML retornado
- ✅ `test_rendered_html_contains_company_name()` - HTML contém empresa
- ✅ `test_rendered_html_contains_executive_summary()` - HTML contém summary
- ✅ `test_render_perspective_financial()` - Render perspectiva individual
- ✅ `test_format_date_filter_brazilian_format()` - Data formatada "DD/MM/AAAA"
- ✅ `test_template_not_found_raises_error()` - Template inexistente = erro
- ✅ `test_html_length_reasonable()` - HTML ~10-20KB (não > 50KB)

---

### **2. Testes E2E** (3 testes)

#### **test_exports_e2e.py**
- ✅ `test_full_export_workflow()` - Workflow completo: carregar diagnostic → export PDF + CSV
- ✅ `test_streamlit_download_buttons()` - Botões de download funcionam
- ✅ `test_exported_files_readable()` - Arquivos exportados podem ser lidos novamente

---

## 📦 Dependências Novas (requirements.txt)

```txt
# FASE 4.2 - Reports & Exports
weasyprint==62.3        # HTML → PDF conversion (Python 3.12 compatible)
jinja2==3.1.4           # Template engine (já instalado via Streamlit)
pandas==2.2.2           # CSV export (já instalado)
```

---

## ⚡ ROI Esperado

### **Antes da FASE 4.2:**
- Usuário copia/cola dados do Streamlit para Word/Excel manualmente (~30 min por diagnóstico)
- Sem relatórios profissionais para apresentar para C-level
- Dados não estruturados para tracking

### **Após FASE 4.2:**
- ✅ Export PDF profissional em 1 clique (~5 segundos)
- ✅ CSV pronto para tracking/análise (~3 segundos)
- ✅ Templates customizáveis (fácil manutenção)
- ✅ Branding profissional (logo, cores, layout)

**Economia:** ~29 min por diagnóstico × 10 diagnósticos/mês = **4.8h/mês economizadas**

---

## 🔄 Workflow de Implementação (6 etapas)

### **Etapa 1:** Setup Dependências (10 min)
- Instalar WeasyPrint
- Criar estrutura de diretórios (`src/exports/`, `templates/reports/`)
- Configurar .gitignore para exports/

### **Etapa 2:** TemplateManager (40 min)
- Implementar `TemplateManager` class
- Criar `base.html` template
- Criar `diagnostic_full.html` template
- Criar `diagnostic_perspective.html` template
- Escrever 8 testes

### **Etapa 3:** PdfExporter (50 min)
- Implementar `PdfExporter` class
- Integração WeasyPrint + TemplateManager
- Métodos `export_full_diagnostic()` e `export_perspective()`
- Escrever 10 testes

### **Etapa 4:** CsvExporter (30 min)
- Implementar `CsvExporter` class
- Métodos `export_clients_list()` e `export_recommendations()`
- Escrever 8 testes

### **Etapa 5:** Integração Streamlit (40 min)
- Adicionar botões de export em `diagnostic_detail.py`
- Adicionar botão CSV em `multi_client_dashboard.py`
- Testar UX dos downloads

### **Etapa 6:** Documentação (30 min)
- Criar `docs/exports/EXPORT_GUIDE.md`
- Atualizar `consulting-progress.md`
- Criar entrada no DOCS_INDEX.md

**TOTAL:** ~3h 20min (dentro da estimativa 3-4h)

---

## 📚 Referências

- **WeasyPrint Docs:** https://doc.courtbouillon.org/weasyprint/stable/
- **Jinja2 Docs:** https://jinja.palletsprojects.com/en/3.1.x/
- **pandas.to_csv():** https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
- **Best Practices PDF Reports:** Procore 360 Reporting, Cascade PDF Export (2024)

---

## ✅ Checklist de Conclusão

**Implementação:**
- [ ] WeasyPrint instalado e configurado
- [ ] 3 classes implementadas (PdfExporter, CsvExporter, TemplateManager)
- [ ] 3 templates HTML criados (base, full, perspective)
- [ ] 26+ testes unitários passando (100%)
- [ ] 3 testes E2E passando (100%)

**Integração:**
- [ ] Botões de export em diagnostic_detail.py funcionando
- [ ] Botão CSV em dashboard funcionando
- [ ] PDFs gerados com branding profissional
- [ ] CSVs parseáveis por Excel/pandas

**Documentação:**
- [ ] EXPORT_GUIDE.md criado
- [ ] consulting-progress.md atualizado
- [ ] DOCS_INDEX.md atualizado
- [ ] Lição aprendida registrada

---

**Próximo Passo:** Implementação da Etapa 1 (Setup Dependências) 🚀

