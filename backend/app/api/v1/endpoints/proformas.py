"""Proformas: numeración consecutiva y PDF descargable."""

import uuid

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.deps import Admin, Administrador, DbSession, UsuarioActual
from app.models.afiliado import Afiliado
from app.models.enums import RolUsuario
from app.models.proforma import Proforma
from app.schemas.proforma import ProformaCrear, ProformaOut
from app.services import correo, storage
from app.services.proformas import crear_proforma, generar_pdf

router = APIRouter(prefix="/proformas", tags=["proformas"])


def _salida(p: Proforma) -> ProformaOut:
    salida = ProformaOut.model_validate(p)
    if p.pdf_url:
        try:
            salida.url = storage.url_publica(p.pdf_url)
        except storage.StorageError:
            salida.url = None
    return salida


@router.get("/me", response_model=list[ProformaOut], summary="Mis proformas")
def mis_proformas(usuario: UsuarioActual, db: DbSession) -> list[ProformaOut]:
    if usuario.rol != RolUsuario.AFILIADO or usuario.afiliado is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Esta ruta es del portal de afiliados."
        )
    filas = db.scalars(
        select(Proforma)
        .where(Proforma.afiliado_id == usuario.afiliado.id)
        .order_by(Proforma.fecha_generacion.desc())
    ).all()
    return [_salida(p) for p in filas]


@router.get("", response_model=list[ProformaOut], summary="Listar proformas")
def listar(_: Admin, db: DbSession, afiliado_id: uuid.UUID | None = None) -> list[ProformaOut]:
    consulta = select(Proforma).order_by(Proforma.fecha_generacion.desc())
    if afiliado_id:
        consulta = consulta.where(Proforma.afiliado_id == afiliado_id)
    return [_salida(p) for p in db.scalars(consulta).all()]


@router.post(
    "", response_model=ProformaOut, status_code=status.HTTP_201_CREATED, summary="Emitir proforma"
)
def emitir(
    datos: ProformaCrear,
    admin: Administrador,
    db: DbSession,
    enviar: Annotated[bool, Query(description="Manda la proforma al afiliado por correo")] = True,
) -> ProformaOut:
    afiliado = db.get(Afiliado, datos.afiliado_id)
    if afiliado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Afiliado no encontrado.")
    proforma = crear_proforma(
        db,
        afiliado=afiliado,
        monto=datos.monto,
        concepto=datos.concepto,
        pago_id=datos.pago_id,
        fecha_generacion=datos.fecha_generacion,
    )
    db.commit()
    db.refresh(proforma)

    # La proforma es un cobro: sirve de poco si se queda esperando a que el
    # afiliado entre al portal por su cuenta. Va adjunta en PDF, que es lo que
    # se reenvía a contabilidad.
    if enviar and afiliado.email:
        correo.enviar(
            correo.proforma_emitida(
                para=afiliado.email,
                empresa=afiliado.nombre,
                numero=proforma.numero,
                monto=f"RD$ {proforma.monto or 0:,.2f}",
                concepto=proforma.concepto or "la cuota de afiliación",
                pdf=generar_pdf(proforma, afiliado).getvalue(),
            )
        )

    return _salida(proforma)


@router.get("/{proforma_id}/pdf", summary="Descargar el PDF")
def descargar(proforma_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    proforma = db.get(Proforma, proforma_id)
    if proforma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proforma no encontrada.")
    if usuario.rol == RolUsuario.AFILIADO and (
        usuario.afiliado is None or proforma.afiliado_id != usuario.afiliado.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Proforma de otro afiliado."
        )

    # Se regenera al vuelo: sirve igual con o sin bucket, y siempre refleja los
    # datos actuales del afiliado.
    pdf = generar_pdf(proforma, proforma.afiliado)
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{proforma.numero}.pdf"'},
    )
