"""Storage de documentos sobre S3 (Cloudflare R2 por defecto).

Nada se escribe en el disco del servidor. El contenedor de Railway es efímero
y un droplet se reconstruye: si el comprobante de un pago vive en el
filesystem, se pierde en el próximo deploy. Todo va al bucket.

Cambiar de R2 a S3, Spaces de DigitalOcean o MinIO es cuestión de mover
S3_ENDPOINT_URL y las llaves en el `.env`; el código no distingue.
"""

import uuid
from datetime import date
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageError(RuntimeError):
    pass


def _cliente():
    if not settings.storage_configurado:
        raise StorageError(
            "El storage no está configurado. Define S3_ACCESS_KEY_ID, "
            "S3_SECRET_ACCESS_KEY y S3_BUCKET en el entorno."
        )
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        # R2 solo habla SigV4 y no admite el estilo de host virtual.
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def construir_llave(prefijo: str, afiliado_id: uuid.UUID, nombre_archivo: str) -> str:
    """documentos/2026/<afiliado>/<uuid>-<nombre>.pdf

    El año adelante mantiene el bucket navegable cuando haya varios ciclos de
    afiliación encima.
    """
    limpio = nombre_archivo.strip().replace("/", "-").replace("\\", "-")[:120]
    return f"{prefijo}/{date.today().year}/{afiliado_id}/{uuid.uuid4().hex[:12]}-{limpio}"


def subir_archivo(
    fichero: BinaryIO, llave: str, content_type: str | None = None
) -> str:
    """Sube el objeto y devuelve la llave con la que se guarda en la base."""
    extra = {"ContentType": content_type} if content_type else {}
    try:
        _cliente().upload_fileobj(fichero, settings.S3_BUCKET, llave, ExtraArgs=extra)
    except ClientError as exc:  # pragma: no cover - depende del proveedor
        raise StorageError(f"No se pudo subir el archivo: {exc}") from exc
    return llave


def url_publica(llave: str) -> str:
    """URL para mostrarle el archivo al usuario.

    Con dominio público configurado devuelve el enlace directo; si no, firma
    una URL temporal para que el bucket pueda seguir siendo privado.
    """
    if not llave:
        return ""
    if llave.startswith("http://") or llave.startswith("https://"):
        return llave
    if settings.S3_PUBLIC_BASE_URL:
        return f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{llave}"
    return url_firmada(llave)


def url_firmada(llave: str, ttl: int | None = None) -> str:
    try:
        return _cliente().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": llave},
            ExpiresIn=ttl or settings.S3_SIGNED_URL_TTL,
        )
    except ClientError as exc:  # pragma: no cover
        raise StorageError(f"No se pudo firmar la URL: {exc}") from exc


def eliminar_archivo(llave: str) -> None:
    try:
        _cliente().delete_object(Bucket=settings.S3_BUCKET, Key=llave)
    except ClientError as exc:  # pragma: no cover
        raise StorageError(f"No se pudo eliminar el archivo: {exc}") from exc
