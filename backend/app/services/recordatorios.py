"""Recordatorios de vencimiento: a quién, con qué y cuándo.

Un afiliado recibe el aviso en dos momentos: antes de que venza —para que
pague a tiempo— y después, si dejó pasar la fecha. Los días de cada tanda
salen de la configuración (`DIAS_AVISO_VENCIMIENTO` y
`DIAS_AVISO_POSVENCIMIENTO`), no del código, porque es una decisión de la
asociación y va a cambiar.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.afiliado import Afiliado
from app.models.enums import AreaContacto
from app.models.proforma import Proforma
from app.schemas.recordatorio import (
    CandidatoRecordatorio,
    DestinatarioPosible,
    DestinoRecordatorio,
)

AREAS = {
    DestinoRecordatorio.CONTABILIDAD: AreaContacto.CONTABILIDAD,
    DestinoRecordatorio.COMERCIAL: AreaContacto.COMERCIAL,
    DestinoRecordatorio.MARKETING: AreaContacto.MARKETING,
}


def destinatarios(afiliado: Afiliado) -> list[DestinatarioPosible]:
    """Las direcciones disponibles para esta empresa, en orden de preferencia."""
    opciones: list[DestinatarioPosible] = []
    contactos = {c.area: c for c in afiliado.contactos}

    for destino, area in AREAS.items():
        contacto = contactos.get(area)
        if contacto and contacto.email:
            opciones.append(
                DestinatarioPosible(
                    destino=destino,
                    etiqueta=f"{area.value.capitalize()} · {contacto.nombre}",
                    email=contacto.email,
                    area=area,
                )
            )

    if afiliado.email:
        opciones.append(
            DestinatarioPosible(
                destino=DestinoRecordatorio.EMPRESA,
                etiqueta="Correo general de la empresa",
                email=afiliado.email,
            )
        )
    return opciones


def resolver_email(afiliado: Afiliado, destino: DestinoRecordatorio, suelto: str | None) -> str | None:
    if destino == DestinoRecordatorio.OTRO:
        return suelto

    opciones = destinatarios(afiliado)
    if destino == DestinoRecordatorio.AUTOMATICO:
        # Contabilidad primero: es quien paga. Si no hay, lo que haya.
        return opciones[0].email if opciones else None

    return next((o.email for o in opciones if o.destino == destino), None)


def proforma_pendiente(db: Session, afiliado: Afiliado) -> Proforma | None:
    return db.scalar(
        select(Proforma)
        .where(Proforma.afiliado_id == afiliado.id, Proforma.pago_id.is_(None))
        .order_by(Proforma.fecha_generacion.desc())
        .limit(1)
    )


def dias_posvencimiento() -> list[int]:
    """Días después del vencimiento en los que se insiste. Ej.: "7,30,60"."""
    valores = []
    for parte in settings.DIAS_AVISO_POSVENCIMIENTO.split(","):
        parte = parte.strip()
        if parte.isdigit():
            valores.append(int(parte))
    return sorted(set(valores))


def candidatos(db: Session, hoy: date | None = None) -> list[CandidatoRecordatorio]:
    """Quiénes toca avisar hoy, según los días configurados.

    Se compara con el día exacto, no con un rango: así una tanda diaria no
    manda el mismo aviso tres días seguidos a la misma empresa.
    """
    hoy = hoy or date.today()
    objetivo = {}

    antes = settings.DIAS_AVISO_VENCIMIENTO
    if antes:
        objetivo[hoy.fromordinal(hoy.toordinal() + antes)] = (
            f"vence en {antes} días",
            antes,
        )
    for dias in dias_posvencimiento():
        objetivo[hoy.fromordinal(hoy.toordinal() - dias)] = (
            f"venció hace {dias} días",
            -dias,
        )

    if not objetivo:
        return []

    filas = db.scalars(
        select(Afiliado).where(Afiliado.fecha_vencimiento.in_(list(objetivo)))
    ).all()

    salida = []
    for afiliado in filas:
        motivo, dias = objetivo[afiliado.fecha_vencimiento]
        pendiente = proforma_pendiente(db, afiliado)
        salida.append(
            CandidatoRecordatorio(
                afiliado_id=afiliado.id,
                afiliado_nombre=afiliado.nombre,
                email=resolver_email(afiliado, DestinoRecordatorio.AUTOMATICO, None),
                fecha_vencimiento=afiliado.fecha_vencimiento,
                dias=dias,
                motivo=motivo,
                proforma=pendiente.numero if pendiente else None,
            )
        )
    return salida
