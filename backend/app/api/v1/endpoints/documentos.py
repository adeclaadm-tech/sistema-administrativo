"""Documentos: el afiliado sube, el staff revisa.

Los archivos van al bucket S3/R2 configurado. En ningún punto se escribe en
el disco del contenedor.
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import Admin, Administrador, DbSession, UsuarioActual
from app.models.afiliado import Afiliado
from app.models.documento import Documento
from app.models.enums import EstadoDocumento, RolUsuario, TipoDocumento
from app.models.usuario import Usuario
from app.schemas.common import Mensaje, Pagina
from app.schemas.documento import (
    DocumentoEnCola,
    DocumentoOut,
    DocumentoSubidoOut,
    RevisionDocumento,
)
from app.services import correo, storage

router = APIRouter(prefix="/documentos", tags=["documentos"])

TIPOS_PERMITIDOS = {"application/pdf", "image/jpeg", "image/jpg", "image/png"}

ETIQUETA_DOCUMENTO = {
    TipoDocumento.RNC_NID: "Registro Nacional del Contribuyente",
    TipoDocumento.CEDULA: "Cédula del representante",
    TipoDocumento.SOPORTE_PAGO: "Soporte de pago de la cuota",
    TipoDocumento.DOC_REPRESENTANTE: "Documentos del representante",
}


def _salida(doc: Documento) -> DocumentoOut:
    salida = DocumentoOut.model_validate(doc)
    try:
        salida.url = storage.url_publica(doc.archivo_url)
    except storage.StorageError:
        # Sin storage configurado (desarrollo temprano) la ficha igual se ve.
        salida.url = None
    return salida


def _mi_afiliado(usuario: Usuario) -> Afiliado:
    if usuario.rol != RolUsuario.AFILIADO or usuario.afiliado is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Esta ruta es del portal de afiliados."
        )
    return usuario.afiliado


# --------------------------------------------------------------------------
# Portal del afiliado
# --------------------------------------------------------------------------


@router.get("/me", response_model=list[DocumentoOut], summary="Mis documentos")
def mis_documentos(usuario: UsuarioActual, db: DbSession) -> list[DocumentoOut]:
    afiliado = _mi_afiliado(usuario)
    docs = db.scalars(
        select(Documento)
        .where(Documento.afiliado_id == afiliado.id)
        .order_by(Documento.fecha_subida.desc())
    ).all()
    return [_salida(d) for d in docs]


@router.post(
    "/me",
    response_model=DocumentoSubidoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un documento",
)
async def subir(
    usuario: UsuarioActual,
    db: DbSession,
    tipo: Annotated[TipoDocumento, Form()],
    archivo: Annotated[UploadFile, File()],
) -> DocumentoSubidoOut:
    afiliado = _mi_afiliado(usuario)

    if archivo.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo aceptamos PDF, JPG o PNG.",
        )

    contenido = await archivo.read()
    limite = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(contenido) > limite:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo pasa de {settings.MAX_UPLOAD_MB} MB.",
        )

    import io

    llave = storage.construir_llave("documentos", afiliado.id, archivo.filename or "documento")
    try:
        storage.subir_archivo(io.BytesIO(contenido), llave, archivo.content_type)
    except storage.StorageError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    # Reemplazar el documento de un tipo deja el anterior fuera de la ficha:
    # la revisión se hace siempre sobre la última versión.
    anterior = db.scalar(
        select(Documento).where(
            Documento.afiliado_id == afiliado.id,
            Documento.tipo == tipo,
            Documento.estado != EstadoDocumento.RECHAZADO,
        )
    )
    if anterior is not None:
        db.delete(anterior)

    doc = Documento(
        afiliado_id=afiliado.id,
        tipo=tipo,
        estado=EstadoDocumento.PENDIENTE,
        archivo_url=llave,
        nombre_archivo=archivo.filename,
        content_type=archivo.content_type,
        tamano_bytes=len(contenido),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentoSubidoOut(documento=_salida(doc))


# --------------------------------------------------------------------------
# Panel administrativo
# --------------------------------------------------------------------------


@router.get("/cola", response_model=list[DocumentoEnCola], summary="Cola de revisión")
def cola_revision(
    _: Admin, db: DbSession, limite: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[DocumentoEnCola]:
    filas = db.execute(
        select(Documento, Afiliado.nombre)
        .join(Afiliado, Afiliado.id == Documento.afiliado_id)
        .where(Documento.estado == EstadoDocumento.PENDIENTE)
        .order_by(Documento.fecha_subida.asc())
        .limit(limite)
    ).all()

    ahora = datetime.now(timezone.utc)
    return [
        DocumentoEnCola(
            id=doc.id,
            afiliado_id=doc.afiliado_id,
            afiliado_nombre=nombre,
            tipo=doc.tipo,
            nombre_archivo=doc.nombre_archivo,
            fecha_subida=doc.fecha_subida,
            dias_en_espera=(ahora - doc.fecha_subida).days,
        )
        for doc, nombre in filas
    ]


@router.get("", response_model=Pagina[DocumentoOut], summary="Listar documentos")
def listar(
    _: Admin,
    db: DbSession,
    afiliado_id: uuid.UUID | None = None,
    estado: EstadoDocumento | None = None,
    tipo: TipoDocumento | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 20,
) -> Pagina[DocumentoOut]:
    consulta = select(Documento)
    if afiliado_id:
        consulta = consulta.where(Documento.afiliado_id == afiliado_id)
    if estado:
        consulta = consulta.where(Documento.estado == estado)
    if tipo:
        consulta = consulta.where(Documento.tipo == tipo)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Documento.fecha_subida.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    return Pagina[DocumentoOut](
        items=[_salida(d) for d in filas], total=total, page=page, per_page=per_page
    )


@router.get("/{documento_id}", response_model=DocumentoOut, summary="Ver documento")
def detalle(documento_id: uuid.UUID, usuario: UsuarioActual, db: DbSession) -> DocumentoOut:
    doc = db.get(Documento, documento_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    # Un afiliado solo ve lo suyo.
    if usuario.rol == RolUsuario.AFILIADO and (
        usuario.afiliado is None or doc.afiliado_id != usuario.afiliado.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Documento de otro afiliado.")
    return _salida(doc)


@router.post(
    "/{documento_id}/revision", response_model=DocumentoOut, summary="Aprobar o rechazar"
)
def revisar(
    documento_id: uuid.UUID, datos: RevisionDocumento, admin: Administrador, db: DbSession
) -> DocumentoOut:
    doc = db.get(Documento, documento_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")

    try:
        datos.validar()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    doc.estado = EstadoDocumento.APROBADO if datos.aprobado else EstadoDocumento.RECHAZADO
    doc.motivo_rechazo = None if datos.aprobado else datos.motivo_rechazo
    doc.fecha_revision = datetime.now(timezone.utc)
    doc.revisado_por_usuario_id = admin.id

    db.commit()
    db.refresh(doc)

    # El afiliado tiene que enterarse sin entrar a mirar: un rechazo sin aviso
    # es una renovación que se queda parada semanas. Si el correo falla, la
    # revisión ya está guardada y no se deshace por eso.
    afiliado = doc.afiliado
    destino = afiliado.email
    if destino:
        correo.enviar(
            correo.documento_revisado(
                para=destino,
                empresa=afiliado.nombre,
                documento=ETIQUETA_DOCUMENTO.get(doc.tipo, doc.tipo.value),
                aprobado=datos.aprobado,
                motivo=datos.motivo_rechazo,
            )
        )

    return _salida(doc)


@router.delete("/{documento_id}", response_model=Mensaje, summary="Eliminar documento")
def eliminar(documento_id: uuid.UUID, admin: Administrador, db: DbSession) -> Mensaje:
    doc = db.get(Documento, documento_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    llave = doc.archivo_url
    db.delete(doc)
    db.commit()
    try:
        storage.eliminar_archivo(llave)
    except storage.StorageError:
        # El registro ya se fue; el objeto huérfano lo limpia el ciclo de vida
        # del bucket. No vale la pena devolver un error por esto.
        pass
    return Mensaje(detail="Documento eliminado.")
