"""Lógica de afiliados que comparten varios endpoints."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.afiliado import Afiliado
from app.models.contacto import ContactoAfiliado
from app.models.documento import Documento
from app.models.enums import EstadoAfiliado, EstadoDocumento
from app.models.pago import Pago
from app.schemas.afiliado import ResumenAfiliado
from app.schemas.contacto import ContactosAfiliado


def aplicar_contactos(db: Session, afiliado: Afiliado, entrada: ContactosAfiliado) -> None:
    """Crea o actualiza el contacto de cada área que venga en el payload.

    Las áreas que no vienen se dejan como están: el formulario del portal
    puede mandar solo la sección que el usuario tocó.
    """
    existentes = {c.area: c for c in afiliado.contactos}
    for nuevo in entrada.como_lista():
        actual = existentes.get(nuevo.area)
        if actual is None:
            db.add(
                ContactoAfiliado(
                    afiliado_id=afiliado.id,
                    area=nuevo.area,
                    nombre=nuevo.nombre,
                    cargo=nuevo.cargo,
                    telefono=nuevo.telefono,
                    email=str(nuevo.email) if nuevo.email else None,
                )
            )
        else:
            actual.nombre = nuevo.nombre
            actual.cargo = nuevo.cargo
            actual.telefono = nuevo.telefono
            actual.email = str(nuevo.email) if nuevo.email else None


def estado_por_vencimiento(afiliado: Afiliado, hoy: date | None = None) -> EstadoAfiliado:
    """El estado que le toca al afiliado según su fecha de vencimiento.

    No se guarda automáticamente: el endpoint decide cuándo persistirlo, para
    que el staff pueda dejar a alguien en `pendiente` aunque la fecha diga otra
    cosa.
    """
    hoy = hoy or date.today()
    if afiliado.fecha_vencimiento is None:
        return afiliado.estado
    if afiliado.fecha_vencimiento < hoy:
        return EstadoAfiliado.VENCIDO
    if afiliado.estado == EstadoAfiliado.VENCIDO:
        return EstadoAfiliado.ACTIVO
    return afiliado.estado


def construir_resumen(db: Session, afiliado: Afiliado) -> ResumenAfiliado:
    """Datos de la cabecera del portal: vencimiento, avance y documentos."""
    hoy = date.today()

    dias = None
    progreso = 0.0
    if afiliado.fecha_vencimiento:
        dias = (afiliado.fecha_vencimiento - hoy).days
        inicio = afiliado.fecha_afiliacion or date(afiliado.fecha_vencimiento.year, 1, 1)
        total = max((afiliado.fecha_vencimiento - inicio).days, 1)
        transcurrido = (hoy - inicio).days
        progreso = min(max(transcurrido / total, 0.0), 1.0)

    conteo = dict(
        db.execute(
            select(Documento.estado, func.count())
            .where(Documento.afiliado_id == afiliado.id)
            .group_by(Documento.estado)
        ).all()
    )
    ultimo_pago = db.scalar(
        select(func.max(Pago.fecha)).where(Pago.afiliado_id == afiliado.id)
    )

    return ResumenAfiliado(
        afiliado=afiliado,
        dias_para_vencer=dias,
        progreso_anual=round(progreso, 4),
        documentos_aprobados=conteo.get(EstadoDocumento.APROBADO, 0),
        documentos_totales=sum(conteo.values()),
        documentos_pendientes=conteo.get(EstadoDocumento.PENDIENTE, 0),
        ultimo_pago=ultimo_pago,
    )
