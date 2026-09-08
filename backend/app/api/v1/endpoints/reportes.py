"""Métricas del dashboard y exportación de reportes.

El consultor entra aquí: puede leer y descargar, es lo suyo. Lo que no puede
es aprobar documentos ni registrar pagos.
"""

from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.deps import Admin, DbSession
from app.models.enums import CategoriaAfiliado, EstadoAfiliado
from app.schemas.reporte import (
    FiltrosReporte,
    FormatoReporte,
    MetricaDashboard,
    ReporteResumen,
    TipoReporte,
)
from app.services import reportes

router = APIRouter(prefix="/reportes", tags=["reportes"])

MEDIA_TYPES = {
    FormatoReporte.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    FormatoReporte.PDF: "application/pdf",
}


@router.get("/dashboard", response_model=MetricaDashboard, summary="Métricas del panel")
def dashboard(_: Admin, db: DbSession) -> MetricaDashboard:
    return reportes.metricas_dashboard(db, settings.DIAS_AVISO_VENCIMIENTO)


@router.get("/resumen", response_model=ReporteResumen, summary="Resumen para la pantalla de reportes")
def resumen(
    _: Admin,
    db: DbSession,
    tipo: TipoReporte = TipoReporte.AFILIACIONES,
    desde: date | None = None,
    hasta: date | None = None,
    estado: EstadoAfiliado | None = None,
    categoria: CategoriaAfiliado | None = None,
) -> ReporteResumen:
    return reportes.resumen(
        db, FiltrosReporte(tipo=tipo, desde=desde, hasta=hasta, estado=estado, categoria=categoria)
    )


@router.get("/export", summary="Descargar el reporte en Excel o PDF")
def exportar(
    _: Admin,
    db: DbSession,
    formato: FormatoReporte = FormatoReporte.XLSX,
    tipo: TipoReporte = TipoReporte.AFILIACIONES,
    desde: date | None = None,
    hasta: date | None = None,
    estado: EstadoAfiliado | None = Query(None, description="Filtra afiliados por estado"),
    categoria: CategoriaAfiliado | None = None,
) -> StreamingResponse:
    filtros = FiltrosReporte(
        tipo=tipo, desde=desde, hasta=hasta, estado=estado, categoria=categoria
    )
    sufijo = f"-{estado.value}" if estado else ""
    nombre = f"adecla-{tipo.value}{sufijo}-{date.today():%Y%m%d}.{formato.value}"

    buffer = (
        reportes.exportar_excel(db, filtros)
        if formato == FormatoReporte.XLSX
        else reportes.exportar_pdf(db, filtros)
    )

    return StreamingResponse(
        buffer,
        media_type=MEDIA_TYPES[formato],
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
