"""Dibujo de la factura proforma.

Réplica del formato que ADECLA emite hoy y del que ya genera el sistema de
inscripciones al torneo: dirección arriba a la izquierda, imagotipo a la
derecha, caja gris con los datos del cliente, tabla con borde negro y bloque
bancario al pie. La diferencia es que aquí el cobro es la cuota de afiliación
en pesos, no una inscripción en dólares, y el documento lleva el sello de la
asociación.

Las medidas están en puntos (1/72") y replican las del documento original.
"""

import io
import pathlib
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas as pdf_canvas

from app.core.config import settings

ASSETS = pathlib.Path(__file__).parent / "assets"
LOGO = ASSETS / "adecla-logo.png"
SELLO = ASSETS / "sello-adecla.png"

ANCHO, ALTO = LETTER
MARGEN = 48
MARGEN_SUP = 46
CONTENIDO = ANCHO - MARGEN * 2

NEGRO = colors.HexColor("#111111")
GRIS_CAJA = colors.HexColor("#ececec")
GRIS_CABECERA = colors.HexColor("#d9d9d9")
GRIS_TEXTO = colors.HexColor("#333333")

# Anchos de columna del original.
COL_CANT = 46
COL_PU = 78
COL_SUB = 82
ALTO_CUERPO = 190


def _money(valor: Decimal | float | None) -> str:
    """1234.5 -> 1,234.50 — el mismo formato es-DO del documento original."""
    return f"{Decimal(valor or 0):,.2f}"


def _fecha(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def dibujar(
    c: pdf_canvas.Canvas,
    *,
    numero: str,
    emitida: date,
    cliente: str,
    cliente_rnc: str | None,
    atencion: str | None,
    descripcion: str,
    detalle: list[str],
    cantidad: int,
    precio_unitario: Decimal,
    total: Decimal,
    nota: str | None = None,
) -> None:
    c.setFillColor(NEGRO)
    c.setFont("Helvetica", 9)

    # --- Cabecera: dirección a la izquierda, imagotipo a la derecha ---------
    y = ALTO - MARGEN_SUP - 9
    for linea in settings.direccion_lineas:
        c.drawString(MARGEN, y, linea)
        y -= 12
    c.drawString(MARGEN, y, f"RNC: {settings.ORG_RNC}")

    if LOGO.exists():
        logo = ImageReader(str(LOGO))
        px_ancho, px_alto = logo.getSize()
        ancho_logo = 190
        alto_logo = ancho_logo * (px_alto / px_ancho)
        c.drawImage(
            logo,
            ANCHO - MARGEN - ancho_logo,
            ALTO - MARGEN_SUP - alto_logo,
            width=ancho_logo,
            height=alto_logo,
            mask="auto",
        )

    # --- Título ------------------------------------------------------------
    y = ALTO - MARGEN_SUP - 100
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(ANCHO / 2, y, "FACTURA PROFORMA")

    # --- Caja de datos del cliente ----------------------------------------
    filas = [
        ("Señores:", cliente),
        ("RNC:", cliente_rnc or "—"),
        ("Atención:", atencion or "—"),
        ("Fecha:", _fecha(emitida)),
    ]
    alto_caja = 8 * 2 + len(filas) * 12
    y -= 26
    tope_caja = y
    c.setFillColor(GRIS_CAJA)
    c.setStrokeColor(NEGRO)
    c.setLineWidth(1.2)
    c.rect(MARGEN, tope_caja - alto_caja, CONTENIDO, alto_caja, fill=1, stroke=1)

    c.setFillColor(NEGRO)
    fila_y = tope_caja - 8 - 9
    for etiqueta, valor in filas:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGEN + 8, fila_y, etiqueta)
        # El original subraya las etiquetas; se replica con una línea fina.
        ancho_etiqueta = c.stringWidth(etiqueta, "Helvetica-Bold", 9)
        c.setLineWidth(0.5)
        c.line(MARGEN + 8, fila_y - 1.5, MARGEN + 8 + ancho_etiqueta, fila_y - 1.5)
        c.setFont("Helvetica", 9)
        c.drawString(MARGEN + 8 + 58, fila_y, str(valor))
        fila_y -= 12

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(ANCHO - MARGEN - 8, tope_caja - 8 - 10, f"No.{numero}")

    # --- Tabla -------------------------------------------------------------
    x_cant = MARGEN
    x_desc = x_cant + COL_CANT
    x_pu = ANCHO - MARGEN - COL_PU - COL_SUB
    x_sub = ANCHO - MARGEN - COL_SUB

    tope_tabla = tope_caja - alto_caja - 14
    alto_encabezado = 16

    c.setLineWidth(1.2)
    c.setStrokeColor(NEGRO)
    c.setFillColor(GRIS_CABECERA)
    c.rect(MARGEN, tope_tabla - alto_encabezado, CONTENIDO, alto_encabezado, fill=1, stroke=0)

    c.setFillColor(NEGRO)
    c.setFont("Helvetica-Bold", 9)
    base = tope_tabla - 11
    c.drawCentredString(x_cant + COL_CANT / 2, base, "Cant.")
    c.drawCentredString((x_desc + x_pu) / 2, base, "Descripción")
    c.drawCentredString(x_pu + COL_PU / 2, base, "P.U. RD$")
    c.drawCentredString(x_sub + COL_SUB / 2, base, "Sub-Total RD$")

    base_cuerpo = tope_tabla - alto_encabezado - ALTO_CUERPO

    # Bloque de totales, debajo del cuerpo.
    lineas_totales = [
        ("Sub-total General RD$", _money(total), True),
        ("Itbis", "-", False),
        ("TOTAL ORDEN RD$", _money(total), True),
    ]
    alto_totales = 6 * 2 + len(lineas_totales) * 12
    base_totales = base_cuerpo - alto_totales

    c.setFillColor(GRIS_CAJA)
    c.rect(MARGEN, base_totales, CONTENIDO, alto_totales, fill=1, stroke=0)

    # Marco exterior y separadores, encima de los rellenos.
    c.setFillColor(NEGRO)
    c.setLineWidth(1.2)
    c.rect(MARGEN, base_totales, CONTENIDO, tope_tabla - base_totales, fill=0, stroke=1)
    c.setLineWidth(1)
    c.line(MARGEN, tope_tabla - alto_encabezado, ANCHO - MARGEN, tope_tabla - alto_encabezado)
    c.line(MARGEN, base_cuerpo, ANCHO - MARGEN, base_cuerpo)
    for x in (x_desc, x_pu, x_sub):
        c.line(x, tope_tabla, x, base_cuerpo)
    c.line(x_sub, base_cuerpo, x_sub, base_totales)

    # Fila del cobro.
    c.setFont("Helvetica", 9)
    fila = base_cuerpo + ALTO_CUERPO - 13
    c.drawCentredString(x_cant + COL_CANT / 2, fila, str(cantidad))
    c.drawRightString(x_pu + COL_PU - 4, fila, _money(precio_unitario))
    c.drawRightString(x_sub + COL_SUB - 4, fila, _money(total))

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_desc + 4, fila, descripcion.upper())
    c.setFont("Helvetica", 9)
    c.setFillColor(GRIS_TEXTO)
    for linea in detalle:
        fila -= 11
        c.drawString(x_desc + 4, fila, linea)
    c.setFillColor(NEGRO)

    # Totales.
    y_total = base_totales + alto_totales - 6 - 9
    for etiqueta, valor, fuerte in lineas_totales:
        c.setFont("Helvetica-Bold" if fuerte else "Helvetica", 9)
        c.drawRightString(x_sub - 8, y_total, etiqueta)
        c.drawRightString(ANCHO - MARGEN - 4, y_total, valor)
        y_total -= 12

    # --- Nota y pie --------------------------------------------------------
    y = base_totales - 20
    if nota:
        c.setFont("Helvetica", 8.5)
        c.setFillColor(GRIS_TEXTO)
        # La nota no cabe en una línea: sin partirla, reportlab la dibuja
        # entera y se sale de la página por la derecha, cortada.
        for linea in simpleSplit(nota, "Helvetica", 8.5, CONTENIDO):
            c.drawString(MARGEN, y, linea)
            y -= 11
        c.setFillColor(NEGRO)
        y -= 13
    else:
        y -= 14

    tope_banco = y
    c.setFont("Helvetica-Bold", 9)
    for linea in (
        settings.BANCO_NOMBRE,
        settings.BANCO_TIPO_CUENTA,
        f"No. {settings.BANCO_CUENTA}",
        settings.BANCO_TITULAR,
        f"RNC-{settings.ORG_RNC}",
    ):
        c.drawString(MARGEN, y, linea)
        y -= 12

    if SELLO.exists():
        # A la derecha y centrado sobre el bloque bancario, como en el
        # documento que emite hoy la asociación.
        sello = ImageReader(str(SELLO))
        lado = 110
        alto_banco = tope_banco - y
        c.drawImage(
            sello,
            MARGEN + CONTENIDO * 0.55,
            tope_banco - alto_banco / 2 - lado / 2,
            width=lado,
            height=lado,
            mask="auto",
        )


def construir(**campos) -> io.BytesIO:
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=LETTER)
    c.setTitle(f"Proforma {campos.get('numero', '')}")
    c.setAuthor("ADECLA")
    dibujar(c, **campos)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
