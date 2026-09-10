"""Numeración y PDF de proformas.

El formato es PRF-<año>-<consecutivo de 4 dígitos>, el mismo que usa hoy el
staff en papel (PRF-2026-0184). El consecutivo se calcula dentro de la
transacción que crea la proforma para que dos cobros simultáneos no repitan
número.
"""

import io
import pathlib
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.afiliado import Afiliado
from app.models.proforma import Proforma
from app.services import storage

# El imagotipo viaja con el backend: el PDF se genera aquí y no puede depender
# de que el frontend esté desplegado.
LOGO = pathlib.Path(__file__).parent / "assets" / "adecla-logo.png"


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
    """PDF de una página con la cabecera de ADECLA y el detalle del cobro."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas

    tinta = colors.HexColor("#233738")
    teal = colors.HexColor("#00776d")
    gris = colors.HexColor("#e9e9e9")

    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=LETTER)
    ancho, alto = LETTER

    # Cabecera clara con el imagotipo oficial: sobre la banda teal el texto
    # oscuro del logo no se lee, y recolorearlo rompería el isotipo.
    c.setFillColor(colors.white)
    c.rect(0, alto - 32 * mm, ancho, 32 * mm, stroke=0, fill=1)

    if LOGO.exists():
        from reportlab.lib.utils import ImageReader

        logo = ImageReader(str(LOGO))
        ancho_px, alto_px = logo.getSize()
        alto_logo = 13 * mm
        c.drawImage(
            logo,
            20 * mm,
            alto - 25 * mm,
            width=alto_logo * (ancho_px / alto_px),
            height=alto_logo,
            mask="auto",  # respeta la transparencia del PNG
        )
    else:  # pragma: no cover - solo si falta el asset
        c.setFillColor(tinta)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(20 * mm, alto - 20 * mm, "ADECLA")

    c.setFillColor(teal)
    c.setLineWidth(1.2)
    c.line(20 * mm, alto - 32 * mm, ancho - 20 * mm, alto - 32 * mm)

    c.setFillColor(tinta)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(ancho - 20 * mm, alto - 20 * mm, proforma.numero)

    y = alto - 45 * mm
    c.setFillColor(tinta)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, "Proforma de pago")

    y -= 12 * mm
    filas = [
        ("Afiliado", afiliado.nombre),
        ("RNC / Cédula", afiliado.rnc_cedula or "—"),
        ("Representante", afiliado.representante or "—"),
        ("Concepto", proforma.concepto or "—"),
        ("Fecha", proforma.fecha_generacion.strftime("%d/%m/%Y")),
    ]
    for etiqueta, valor in filas:
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#5b6b6c"))
        c.drawString(20 * mm, y, etiqueta.upper())
        c.setFont("Helvetica", 11)
        c.setFillColor(tinta)
        c.drawString(60 * mm, y, str(valor))
        y -= 8 * mm

    y -= 4 * mm
    c.setStrokeColor(gris)
    c.line(20 * mm, y, ancho - 20 * mm, y)

    y -= 14 * mm
    monto = proforma.monto or Decimal("0.00")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#5b6b6c"))
    c.drawString(20 * mm, y, "MONTO A PAGAR")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(tinta)
    c.drawRightString(ancho - 20 * mm, y - 2 * mm, f"RD$ {monto:,.2f}")

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#5b6b6c"))
    c.drawString(
        20 * mm,
        20 * mm,
        "Asociación de Desarrolladores y Constructores de la Altagracia · Punta Cana, R.D. · "
        "Documento generado por el sistema de afiliados. No requiere firma.",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
