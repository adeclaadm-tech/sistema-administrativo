"""Pagos: los registra el staff, el afiliado los consulta."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import Admin, Administrador, DbSession, UsuarioActual
from app.models.afiliado import Afiliado
from app.models.enums import EstadoAfiliado, RolUsuario
from app.models.pago import Pago
from app.schemas.common import Mensaje, Pagina
from app.schemas.pago import PagoActualizar, PagoConProformaOut, PagoCrear, PagoOut
from app.services import correo
from app.services.proformas import crear_proforma

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.get("/me", response_model=list[PagoOut], summary="Mis pagos")
def mis_pagos(usuario: UsuarioActual, db: DbSession) -> list[PagoOut]:
    if usuario.rol != RolUsuario.AFILIADO or usuario.afiliado is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Esta ruta es del portal de afiliados."
        )
    pagos = db.scalars(
        select(Pago)
        .where(Pago.afiliado_id == usuario.afiliado.id)
        .order_by(Pago.fecha.desc())
    ).all()
    return [PagoOut.model_validate(p) for p in pagos]


@router.get("", response_model=Pagina[PagoOut], summary="Listar pagos")
def listar(
    _: Admin,
    db: DbSession,
    afiliado_id: uuid.UUID | None = None,
    periodo: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 20,
) -> Pagina[PagoOut]:
    consulta = select(Pago)
    if afiliado_id:
        consulta = consulta.where(Pago.afiliado_id == afiliado_id)
    if periodo:
        consulta = consulta.where(Pago.periodo == periodo)
    if desde:
        consulta = consulta.where(Pago.fecha >= desde)
    if hasta:
        consulta = consulta.where(Pago.fecha <= hasta)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Pago.fecha.desc()).offset((page - 1) * per_page).limit(per_page)
    ).all()
    return Pagina[PagoOut](
        items=[PagoOut.model_validate(p) for p in filas],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "/afiliado/{afiliado_id}",
    response_model=PagoConProformaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago",
)
def registrar(
    afiliado_id: uuid.UUID, datos: PagoCrear, admin: Administrador, db: DbSession
) -> PagoConProformaOut:
    afiliado = db.get(Afiliado, afiliado_id)
    if afiliado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Afiliado no encontrado.")

    pago = Pago(
        afiliado_id=afiliado.id,
        monto=datos.monto,
        moneda=datos.moneda,
        fecha=datos.fecha,
        metodo=datos.metodo,
        referencia=datos.referencia,
        concepto=datos.concepto or f"Cuota anual {datos.periodo or datos.fecha.year}",
        periodo=datos.periodo or datos.fecha.year,
        comprobante_url=datos.comprobante_url,
        notas=datos.notas,
        registrado_por_usuario_id=admin.id,
    )
    db.add(pago)
    db.flush()

    proforma = None
    if datos.generar_proforma:
        proforma = crear_proforma(
            db,
            afiliado=afiliado,
            monto=datos.monto,
            concepto=pago.concepto,
            pago_id=pago.id,
            fecha_generacion=datos.fecha,
        )

    if datos.renovar_afiliacion:
        # Un pago de cuota mueve el vencimiento al 31 de diciembre del período
        # cubierto y devuelve al afiliado a estado activo.
        anio = datos.periodo or datos.fecha.year
        afiliado.fecha_vencimiento = date(anio, 12, 31)
        afiliado.estado = EstadoAfiliado.ACTIVO

    db.commit()
    db.refresh(pago)

    if afiliado.email:
        correo.enviar(
            correo.pago_registrado(
                para=afiliado.email,
                empresa=afiliado.nombre,
                monto=f"RD$ {pago.monto:,.2f}",
                periodo=pago.periodo,
                proforma=proforma.numero if proforma else None,
            )
        )

    return PagoConProformaOut(
        pago=PagoOut.model_validate(pago),
        proforma_numero=proforma.numero if proforma else None,
        proforma_id=proforma.id if proforma else None,
    )


@router.get("/{pago_id}", response_model=PagoOut, summary="Ver pago")
def detalle(pago_id: uuid.UUID, usuario: UsuarioActual, db: DbSession) -> PagoOut:
    pago = db.get(Pago, pago_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")
    if usuario.rol == RolUsuario.AFILIADO and (
        usuario.afiliado is None or pago.afiliado_id != usuario.afiliado.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pago de otro afiliado.")
    return PagoOut.model_validate(pago)


@router.patch("/{pago_id}", response_model=PagoOut, summary="Corregir pago")
def actualizar(
    pago_id: uuid.UUID, datos: PagoActualizar, admin: Administrador, db: DbSession
) -> PagoOut:
    pago = db.get(Pago, pago_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(pago, campo, valor)
    db.commit()
    db.refresh(pago)
    return PagoOut.model_validate(pago)


@router.delete("/{pago_id}", response_model=Mensaje, summary="Anular pago")
def eliminar(pago_id: uuid.UUID, admin: Administrador, db: DbSession) -> Mensaje:
    pago = db.get(Pago, pago_id)
    if pago is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")
    db.delete(pago)
    db.commit()
    return Mensaje(detail="Pago anulado. La proforma asociada queda sin pago vinculado.")
