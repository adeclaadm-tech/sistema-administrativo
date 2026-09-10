"""Numeración y PDF de proformas.

El formato es PRF-<año>-<consecutivo de 4 dígitos>, el mismo que usa hoy el
staff en papel (PRF-2026-0184). El consecutivo se calcula dentro de la
transacción que crea la proforma para que dos cobros simultáneos no repitan
número.
"""

import io
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.afiliado import Afiliado
from app.models.proforma import Proforma
from app.models.enums import CategoriaAfiliado
from app.services import proforma_pdf, storage

# El imagotipo viaja con el backend: el PDF se genera aquí y no puede depender
# de que el frontend esté desplegado.
ETIQUETA_CATEGORIA = {
    CategoriaAfiliado.CONSTRUCTOR: "Constructor",
    CategoriaAfiliado.PROVEEDOR: "Proveedor",
    CategoriaAfiliado.DESARROLLADOR: "Desarrollador",
}

NOTA_PAGO = (
    "El pago puede realizarse por transferencia o cheque a nombre de ADECLA. "
    "Envía el comprobante desde el portal de afiliados para que quede registrado."
)


def siguiente_numero(db: Session, anio: int | None = None) -> str:
    anio = anio or date.today().year
    prefijo = f"PRF-{anio}-"
    ultimo = db.scalar(
        select(func.max(Proforma.numero)).where(Proforma.numero.like(f"{prefijo}%"))
    )
    consecutivo = int(ultimo.rsplit("-", 1)[1]) + 1 if ultimo else 1
    return f"{prefijo}{consecutivo:04d}"


def crear_proforma(
    db: Session,
    *,
    afiliado: Afiliado,
    monto: Decimal | None = None,
    concepto: str | None = None,
    pago_id: uuid.UUID | None = None,
    fecha_generacion: date | None = None,
    subir_pdf: bool = True,
) -> Proforma:
    fecha_generacion = fecha_generacion or date.today()
    proforma = Proforma(
        afiliado_id=afiliado.id,
        pago_id=pago_id,
        numero=siguiente_numero(db, fecha_generacion.year),
        fecha_generacion=fecha_generacion,
        monto=monto if monto is not None else afiliado.cuota_anual,
        concepto=concepto or f"Cuota anual {fecha_generacion.year}",
    )
    db.add(proforma)
    db.flush()

    if subir_pdf and settings.storage_configurado:
        pdf = generar_pdf(proforma, afiliado)
        llave = storage.construir_llave("proformas", afiliado.id, f"{proforma.numero}.pdf")
        proforma.pdf_url = storage.subir_archivo(pdf, llave, "application/pdf")

    return proforma


def generar_pdf(proforma: Proforma, afiliado: Afiliado) -> io.BytesIO:
    """Factura proforma con el formato que ya usa la asociación."""
    anio = proforma.fecha_generacion.year
    monto = proforma.monto or afiliado.cuota_anual or Decimal("0.00")

    detalle = []
    if afiliado.categoria:
        detalle.append(f"Tipo de afiliación: {ETIQUETA_CATEGORIA[afiliado.categoria]}")
    if afiliado.fecha_vencimiento:
        detalle.append(f"Vigencia hasta: {afiliado.fecha_vencimiento:%d/%m/%Y}")

    return proforma_pdf.construir(
        numero=proforma.numero,
        emitida=proforma.fecha_generacion,
        cliente=afiliado.nombre,
        cliente_rnc=afiliado.rnc_cedula,
        atencion=afiliado.representante,
        descripcion=proforma.concepto or f"Membresía ADECLA {anio}",
        detalle=detalle,
        cantidad=1,
        precio_unitario=monto,
        total=monto,
        nota=NOTA_PAGO,
    )
