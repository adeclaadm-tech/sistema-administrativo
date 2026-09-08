from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from app.models.enums import CategoriaAfiliado, EstadoAfiliado


class FormatoReporte(str, Enum):
    XLSX = "xlsx"
    PDF = "pdf"


class TipoReporte(str, Enum):
    AFILIACIONES = "afiliaciones"
    RECAUDACION = "recaudacion"
    VENCIMIENTOS = "vencimientos"
    DOCUMENTOS = "documentos"


class FiltrosReporte(BaseModel):
    tipo: TipoReporte = TipoReporte.AFILIACIONES
    desde: date | None = None
    hasta: date | None = None
    estado: EstadoAfiliado | None = None
    categoria: CategoriaAfiliado | None = None


class MetricaDashboard(BaseModel):
    """Las cuatro tarjetas del dashboard admin (pantalla 1f)."""

    total_afiliados: int = 0
    activos: int = 0
    pendientes: int = 0
    vencidos: int = 0
    proximos_a_vencer: int = 0
    documentos_por_revisar: int = 0
    nuevos_en_el_ano: int = 0
    recaudado_periodo: Decimal = Decimal("0.00")
    variacion_recaudacion: float | None = None


class FilaCategoria(BaseModel):
    categoria: CategoriaAfiliado
    total: int = 0
    activos: int = 0
    pendientes: int = 0
    vencidos: int = 0
    recaudado: Decimal = Decimal("0.00")


class BarraMes(BaseModel):
    mes: str = Field(description="Etiqueta corta: ENE, FEB, MAR…")
    anio: int
    activos: int = 0
    pendientes: int = 0
    vencidos: int = 0
    recaudado: Decimal = Decimal("0.00")


class ReporteResumen(BaseModel):
    """Payload de la pantalla de reportes: encabezado, barras y tabla."""

    tipo: TipoReporte
    desde: date | None = None
    hasta: date | None = None
    nuevas_afiliaciones: int = 0
    renovaciones: int = 0
    bajas: int = 0
    recaudado: Decimal = Decimal("0.00")
    por_mes: list[BarraMes] = []
    por_categoria: list[FilaCategoria] = []
    total_afiliados: int = 0
