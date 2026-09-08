"""CRUD de afiliados (panel) y ficha propia (portal)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.core.config import settings
from app.core.deps import Admin, Administrador, DbSession, UsuarioActual
from app.core.security import hash_password
from app.models.afiliado import Afiliado
from app.models.contacto import ContactoAfiliado
from app.models.enums import AreaContacto, CategoriaAfiliado, EstadoAfiliado, RolUsuario
from app.models.usuario import Usuario
from app.schemas.afiliado import (
    AfiliadoActualizar,
    AfiliadoCrear,
    AfiliadoListaOut,
    AfiliadoOut,
    AfiliadoPerfilActualizar,
    ResumenAfiliado,
)
from app.schemas.common import Mensaje, Pagina
from app.schemas.contacto import ContactoActualizar, ContactoOut
from app.services.afiliados import aplicar_contactos, construir_resumen

router = APIRouter(prefix="/afiliados", tags=["afiliados"])


def _obtener(db, afiliado_id: uuid.UUID) -> Afiliado:
    afiliado = db.get(Afiliado, afiliado_id)
    if afiliado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Afiliado no encontrado.")
    return afiliado


def _mi_afiliado(db, usuario: Usuario) -> Afiliado:
    if usuario.rol != RolUsuario.AFILIADO or usuario.afiliado is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta ruta es del portal de afiliados.",
        )
    return usuario.afiliado


# --------------------------------------------------------------------------
# Portal del afiliado
# --------------------------------------------------------------------------


@router.get("/me", response_model=ResumenAfiliado, summary="Mi ficha y estado")
def mi_ficha(usuario: UsuarioActual, db: DbSession) -> ResumenAfiliado:
    return construir_resumen(db, _mi_afiliado(db, usuario))


@router.patch("/me", response_model=AfiliadoOut, summary="Actualizar mis datos de contacto")
def actualizar_mi_ficha(
    datos: AfiliadoPerfilActualizar, usuario: UsuarioActual, db: DbSession
) -> AfiliadoOut:
    afiliado = _mi_afiliado(db, usuario)
    campos = datos.model_dump(exclude_unset=True, exclude={"contactos"})
    for campo, valor in campos.items():
        setattr(afiliado, campo, str(valor) if campo == "email" and valor else valor)
    if datos.contactos:
        aplicar_contactos(db, afiliado, datos.contactos)
    db.commit()
    db.refresh(afiliado)
    return AfiliadoOut.model_validate(afiliado)


# --------------------------------------------------------------------------
# Panel administrativo
# --------------------------------------------------------------------------


@router.get("", response_model=Pagina[AfiliadoListaOut], summary="Listar afiliados")
def listar(
    _: Admin,
    db: DbSession,
    q: Annotated[str | None, Query(description="Nombre, RNC o representante")] = None,
    estado: EstadoAfiliado | None = None,
    categoria: CategoriaAfiliado | None = None,
    vence_en_dias: Annotated[int | None, Query(ge=0, le=365)] = None,
    orden: Annotated[str, Query(pattern="^(nombre|vencimiento|creado)$")] = "nombre",
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 20,
) -> Pagina[AfiliadoListaOut]:
    consulta = select(Afiliado)

    if q:
        patron = f"%{q.strip()}%"
        consulta = consulta.where(
            or_(
                Afiliado.nombre.ilike(patron),
                Afiliado.rnc_cedula.ilike(patron),
                Afiliado.representante.ilike(patron),
            )
        )
    if estado:
        consulta = consulta.where(Afiliado.estado == estado)
    if categoria:
        consulta = consulta.where(Afiliado.categoria == categoria)
    if vence_en_dias is not None:
        consulta = consulta.where(
            Afiliado.fecha_vencimiento.is_not(None),
            Afiliado.fecha_vencimiento <= func.current_date() + vence_en_dias,
        )

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0

    columna = {
        "nombre": Afiliado.nombre.asc(),
        "vencimiento": Afiliado.fecha_vencimiento.asc().nullslast(),
        "creado": Afiliado.creado_en.desc(),
    }[orden]
    filas = db.scalars(
        consulta.order_by(columna).offset((page - 1) * per_page).limit(per_page)
    ).all()

    return Pagina[AfiliadoListaOut](
        items=[AfiliadoListaOut.model_validate(f) for f in filas],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "", response_model=AfiliadoOut, status_code=status.HTTP_201_CREATED, summary="Crear afiliado"
)
def crear(datos: AfiliadoCrear, admin: Administrador, db: DbSession) -> AfiliadoOut:
    if db.scalar(select(Afiliado).where(Afiliado.rnc_cedula == datos.rnc_cedula)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya hay un afiliado con este RNC."
        )

    usuario_id = None
    if datos.crear_usuario_email:
        if not datos.crear_usuario_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para crear la cuenta del portal hace falta una contraseña.",
            )
        email = datos.crear_usuario_email.lower()
        if db.scalar(select(Usuario).where(func.lower(Usuario.email) == email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Ya existe una cuenta con este correo."
            )
        usuario = Usuario(
            email=email,
            password_hash=hash_password(datos.crear_usuario_password),
            nombre=datos.representante or datos.nombre,
            rol=RolUsuario.AFILIADO,
        )
        db.add(usuario)
        db.flush()
        usuario_id = usuario.id

    campos = datos.model_dump(
        exclude={"contactos", "crear_usuario_email", "crear_usuario_password"}
    )
    if campos.get("email"):
        campos["email"] = str(campos["email"])
    if campos.get("cuota_anual") is None:
        campos["cuota_anual"] = settings.CUOTA_ANUAL_DEFAULT

    afiliado = Afiliado(usuario_id=usuario_id, **campos)
    db.add(afiliado)
    db.flush()

    if datos.contactos:
        aplicar_contactos(db, afiliado, datos.contactos)

    db.commit()
    db.refresh(afiliado)
    return AfiliadoOut.model_validate(afiliado)


@router.get("/{afiliado_id}", response_model=AfiliadoOut, summary="Ficha de afiliado")
def detalle(afiliado_id: uuid.UUID, _: Admin, db: DbSession) -> AfiliadoOut:
    return AfiliadoOut.model_validate(_obtener(db, afiliado_id))


@router.patch("/{afiliado_id}", response_model=AfiliadoOut, summary="Actualizar afiliado")
def actualizar(
    afiliado_id: uuid.UUID, datos: AfiliadoActualizar, admin: Administrador, db: DbSession
) -> AfiliadoOut:
    afiliado = _obtener(db, afiliado_id)

    if datos.rnc_cedula and datos.rnc_cedula != afiliado.rnc_cedula:
        if db.scalar(select(Afiliado).where(Afiliado.rnc_cedula == datos.rnc_cedula)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Ya hay un afiliado con este RNC."
            )

    for campo, valor in datos.model_dump(exclude_unset=True, exclude={"contactos"}).items():
        setattr(afiliado, campo, str(valor) if campo == "email" and valor else valor)
    if datos.contactos:
        aplicar_contactos(db, afiliado, datos.contactos)

    db.commit()
    db.refresh(afiliado)
    return AfiliadoOut.model_validate(afiliado)


@router.delete("/{afiliado_id}", response_model=Mensaje, summary="Eliminar afiliado")
def eliminar(afiliado_id: uuid.UUID, admin: Administrador, db: DbSession) -> Mensaje:
    afiliado = _obtener(db, afiliado_id)
    db.delete(afiliado)
    db.commit()
    return Mensaje(detail="Afiliado eliminado junto con sus documentos, pagos y proformas.")


# --------------------------------------------------------------------------
# Contactos por área
# --------------------------------------------------------------------------


@router.get(
    "/{afiliado_id}/contactos",
    response_model=list[ContactoOut],
    summary="Contactos de contabilidad, marketing y comercial",
)
def listar_contactos(afiliado_id: uuid.UUID, _: Admin, db: DbSession) -> list[ContactoOut]:
    afiliado = _obtener(db, afiliado_id)
    return [ContactoOut.model_validate(c) for c in afiliado.contactos]


@router.put(
    "/{afiliado_id}/contactos/{area}",
    response_model=ContactoOut,
    summary="Crear o reemplazar el contacto de un área",
)
def guardar_contacto(
    afiliado_id: uuid.UUID,
    area: AreaContacto,
    datos: ContactoActualizar,
    admin: Administrador,
    db: DbSession,
) -> ContactoOut:
    afiliado = _obtener(db, afiliado_id)
    contacto = next((c for c in afiliado.contactos if c.area == area), None)

    if contacto is None:
        if not datos.nombre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un contacto nuevo necesita al menos el nombre.",
            )
        contacto = ContactoAfiliado(afiliado_id=afiliado.id, area=area, nombre=datos.nombre)
        db.add(contacto)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(contacto, campo, str(valor) if campo == "email" and valor else valor)

    db.commit()
    db.refresh(contacto)
    return ContactoOut.model_validate(contacto)


@router.delete(
    "/{afiliado_id}/contactos/{area}", response_model=Mensaje, summary="Eliminar contacto de un área"
)
def eliminar_contacto(
    afiliado_id: uuid.UUID, area: AreaContacto, admin: Administrador, db: DbSession
) -> Mensaje:
    afiliado = _obtener(db, afiliado_id)
    contacto = next((c for c in afiliado.contactos if c.area == area), None)
    if contacto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Este afiliado no tiene contacto en esa área."
        )
    db.delete(contacto)
    db.commit()
    return Mensaje(detail=f"Contacto de {area.value} eliminado.")
