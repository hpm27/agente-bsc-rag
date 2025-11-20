"""Router de relatórios e exports - /api/v1/reports/*.

4 endpoints para geração de relatórios PDF e CSV:
- POST /pdf/diagnostic - Gerar PDF diagnóstico completo
- POST /pdf/perspective - Gerar PDF por perspectiva
- POST /csv/clients - Export CSV lista de clientes
- GET /{id}/download - Download de relatório gerado

Fase: 4.3 - Integration APIs
"""

import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse

from api.dependencies import verify_api_key
from api.schemas.requests import GenerateCsvRequest, GeneratePdfRequest
from api.schemas.responses import ReportResponse
from api.utils.rate_limit import LIMIT_HEAVY, LIMIT_READ, LIMIT_WRITE, limiter
from src.exports import CsvExporter, PdfExporter, TemplateManager
from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile, CompleteDiagnostic

logger = logging.getLogger(__name__)

router = APIRouter()

# Storage temporário de relatórios gerados (em produção, usar Redis/DB)
_reports_storage: dict[str, dict] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_diagnostic(diagnostic_id: str) -> CompleteDiagnostic:
    """Busca diagnóstico completo por ID."""
    # TODO: Implementar busca real no Mem0ClientWrapper
    # Por enquanto, retorna erro
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Diagnóstico com ID '{diagnostic_id}' não encontrado.",
    )


def _get_client_profile(client_id: str) -> ClientProfile:
    """Busca ClientProfile por ID."""
    mem0_client = Mem0ClientWrapper()
    profile = mem0_client.get_client_profile(client_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID '{client_id}' não encontrado.",
        )

    return profile


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/pdf/diagnostic",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar PDF diagnóstico completo",
    description="Gera PDF formatado profissionalmente com diagnóstico BSC completo (4 perspectivas).",
)
@limiter.limit(LIMIT_HEAVY)
async def generate_pdf_diagnostic(
    request: Request,
    response: Response,
    body: GeneratePdfRequest,
    auth: dict = Depends(verify_api_key),
):
    """Gera PDF do diagnóstico BSC completo."""
    logger.info(
        f"[API] generate_pdf_diagnostic | diagnostic_id={body.diagnostic_id} | "
        f"client_id={body.client_id}"
    )

    try:
        # Validar que diagnostic_id ou client_id foi fornecido
        if not body.diagnostic_id and not body.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="É necessário fornecer 'diagnostic_id' ou 'client_id'.",
            )

        # Buscar diagnóstico e profile
        if body.diagnostic_id:
            diagnostic = _get_diagnostic(body.diagnostic_id)
            profile = _get_client_profile(diagnostic.client_id)
        else:
            # Buscar diagnóstico mais recente do cliente
            profile = _get_client_profile(body.client_id)
            # TODO: Implementar busca de diagnóstico mais recente
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Busca de diagnóstico mais recente ainda não implementada. Use 'diagnostic_id'.",
            )

        # Gerar PDF
        template_manager = TemplateManager()
        pdf_exporter = PdfExporter(template_manager)

        pdf_path = pdf_exporter.export_full_diagnostic(
            diagnostic=diagnostic,
            profile=profile,
        )

        # Criar registro de relatório
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        _reports_storage[report_id] = {
            "report_id": report_id,
            "report_type": "pdf_diagnostic",
            "file_path": str(pdf_path),
            "file_size_bytes": pdf_path.stat().st_size,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "client_id": profile.client_id,
        }

        logger.info(f"[API] PDF gerado: {pdf_path} | report_id={report_id}")

        # Construir response
        return ReportResponse(
            report_id=report_id,
            report_type="pdf_diagnostic",
            status="completed",
            download_url=f"/api/v1/reports/{report_id}/download",
            expires_at=_reports_storage[report_id]["expires_at"],
            file_size_bytes=_reports_storage[report_id]["file_size_bytes"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao gerar PDF diagnóstico: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao gerar PDF: {e!s}"
        )


@router.post(
    "/pdf/perspective",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar PDF por perspectiva",
    description="Gera PDF formatado para uma perspectiva BSC específica.",
)
@limiter.limit(LIMIT_HEAVY)
async def generate_pdf_perspective(
    request: Request,
    response: Response,
    body: GeneratePdfRequest,
    auth: dict = Depends(verify_api_key),
):
    """Gera PDF de uma perspectiva específica."""
    logger.info(
        f"[API] generate_pdf_perspective | diagnostic_id={body.diagnostic_id} | "
        f"perspective={request.perspective}"
    )

    try:
        # Validar perspectiva
        if not request.perspective:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="É necessário fornecer 'perspective' (financial, customer, process, learning).",
            )

        # Buscar diagnóstico e profile
        if body.diagnostic_id:
            diagnostic = _get_diagnostic(body.diagnostic_id)
            profile = _get_client_profile(diagnostic.client_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="É necessário fornecer 'diagnostic_id' para PDF por perspectiva.",
            )

        # Gerar PDF
        template_manager = TemplateManager()
        pdf_exporter = PdfExporter(template_manager)

        pdf_path = pdf_exporter.export_perspective_diagnostic(
            diagnostic=diagnostic,
            profile=profile,
            perspective=request.perspective,
        )

        # Criar registro de relatório
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        _reports_storage[report_id] = {
            "report_id": report_id,
            "report_type": f"pdf_perspective_{request.perspective}",
            "file_path": str(pdf_path),
            "file_size_bytes": pdf_path.stat().st_size,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "client_id": profile.client_id,
        }

        logger.info(f"[API] PDF perspectiva gerado: {pdf_path} | report_id={report_id}")

        # Construir response
        return ReportResponse(
            report_id=report_id,
            report_type=f"pdf_perspective_{request.perspective}",
            status="completed",
            download_url=f"/api/v1/reports/{report_id}/download",
            expires_at=_reports_storage[report_id]["expires_at"],
            file_size_bytes=_reports_storage[report_id]["file_size_bytes"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao gerar PDF perspectiva: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar PDF perspectiva: {e!s}",
        )


@router.post(
    "/csv/clients",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Export CSV lista de clientes",
    description="Gera CSV com lista de clientes (filtros opcionais).",
)
@limiter.limit(LIMIT_WRITE)
async def generate_csv_clients(
    request: Request,
    response: Response,
    body: GenerateCsvRequest,
    auth: dict = Depends(verify_api_key),
):
    """Gera CSV com lista de clientes."""
    logger.info(f"[API] generate_csv_clients | export_type={body.export_type}")

    try:
        # Validar export_type
        if body.export_type != "clients_list":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export type '{body.export_type}' não suportado para CSV. Use 'clients_list'.",
            )

        # Buscar perfis de clientes
        mem0_client = Mem0ClientWrapper()
        profiles = mem0_client.list_all_profiles(
            limit=1000,  # TODO: Implementar filtros do request.filters
            offset=0,
        )

        if not profiles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum cliente encontrado para export.",
            )

        # Gerar CSV
        csv_exporter = CsvExporter()
        csv_path = csv_exporter.export_clients_list(profiles)

        # Criar registro de relatório
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        _reports_storage[report_id] = {
            "report_id": report_id,
            "report_type": "csv_clients_list",
            "file_path": str(csv_path),
            "file_size_bytes": csv_path.stat().st_size,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "client_id": None,  # CSV não é específico de cliente
        }

        logger.info(f"[API] CSV gerado: {csv_path} | report_id={report_id}")

        # Construir response
        return ReportResponse(
            report_id=report_id,
            report_type="csv_clients_list",
            status="completed",
            download_url=f"/api/v1/reports/{report_id}/download",
            expires_at=_reports_storage[report_id]["expires_at"],
            file_size_bytes=_reports_storage[report_id]["file_size_bytes"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao gerar CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao gerar CSV: {e!s}"
        )


@router.get(
    "/{report_id}/download",
    summary="Download de relatório",
    description="Baixa relatório gerado (PDF ou CSV) por ID.",
)
@limiter.limit(LIMIT_READ)
async def download_report(
    request: Request, response: Response, report_id: str, auth: dict = Depends(verify_api_key)
):
    """Baixa relatório gerado por ID."""
    logger.info(f"[API] download_report | report_id={report_id}")

    try:
        # Buscar registro de relatório
        report_data = _reports_storage.get(report_id)

        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relatório com ID '{report_id}' não encontrado ou expirado.",
            )

        # Verificar expiração
        expires_at = datetime.fromisoformat(report_data["expires_at"])
        if datetime.now() > expires_at:
            # Remover relatório expirado
            del _reports_storage[report_id]
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Relatório '{report_id}' expirou em {expires_at.isoformat()}.",
            )

        # Verificar se arquivo existe
        file_path = Path(report_data["file_path"])
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo do relatório não encontrado: {file_path}",
            )

        # Determinar media_type baseado na extensão
        media_type_map = {
            ".pdf": "application/pdf",
            ".csv": "text/csv",
        }
        media_type = media_type_map.get(file_path.suffix, "application/octet-stream")

        # Retornar arquivo
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao baixar relatório {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao baixar relatório: {e!s}",
        )
