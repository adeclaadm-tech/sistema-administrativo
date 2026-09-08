"""Datos de prueba para desarrollo local.

    python -m app.scripts.seed

Crea dos cuentas de staff (administrador y consultor) y ocho afiliados con
contactos, documentos y pagos, para que las pantallas del panel no se vean
vacías. Es idempotente: si el correo ya existe, no duplica nada.

No se ejecuta en producción. En Railway se corre solo `alembic upgrade head`.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Afiliado,
    AreaContacto,
    CategoriaAfiliado,
    ContactoAfiliado,
    Documento,
    EstadoAfiliado,
    EstadoDocumento,
    MetodoPago,
    Pago,
    RolUsuario,
    SubRolAdmin,
    TipoDocumento,
    Usuario,
)
from app.services.proformas import crear_proforma

STAFF = [
    ("gestion@adecla.do", "Laura Méndez", SubRolAdmin.ADMINISTRADOR, "adecla2026"),
    ("consulta@adecla.do", "Ramón Espinal", SubRolAdmin.CONSULTOR, "adecla2026"),
]

EMPRESAS = [
    ("Constructora Bávaro SRL", "1-31-45678-9", "Julio Morales", CategoriaAfiliado.CLASE_B, EstadoAfiliado.PENDIENTE),
    ("Grupo Inmobiliario Cana", "1-30-11902-4", "Marisol Peña", CategoriaAfiliado.CLASE_A, EstadoAfiliado.ACTIVO),
    ("Edificaciones del Este SA", "1-31-77410-2", "Rafael Guzmán", CategoriaAfiliado.CLASE_A, EstadoAfiliado.ACTIVO),
    ("Punta Cana Builders SA", "1-30-55218-7", "Elena Ferreras", CategoriaAfiliado.CLASE_A, EstadoAfiliado.ACTIVO),
    ("Constructora Verón SRL", "1-32-00841-5", "Andrés Batista", CategoriaAfiliado.CLASE_C, EstadoAfiliado.VENCIDO),
    ("Arquitectura Macao SRL", "1-31-63077-1", "Yolanda Reyes", CategoriaAfiliado.CLASE_B, EstadoAfiliado.PENDIENTE),
    ("Desarrollos Uvero Alto", "1-30-98123-6", "Tomás Fernández", CategoriaAfiliado.CLASE_B, EstadoAfiliado.ACTIVO),
    ("Ingeniería Friusa SRL", "1-32-14456-8", "Carla Núñez", CategoriaAfiliado.CLASE_C, EstadoAfiliado.VENCIDO),
]

CUOTA = {
    CategoriaAfiliado.CLASE_A: Decimal("60000.00"),
    CategoriaAfiliado.CLASE_B: Decimal("45000.00"),
    CategoriaAfiliado.CLASE_C: Decimal("28000.00"),
}


def sembrar() -> None:
    random.seed(2026)
    hoy = date.today()

    with SessionLocal() as db:
        for email, nombre, sub_rol, password in STAFF:
            if db.scalar(select(Usuario).where(func.lower(Usuario.email) == email)):
                continue
            db.add(
                Usuario(
                    email=email,
                    nombre=nombre,
                    password_hash=hash_password(password),
                    rol=RolUsuario.ADMIN,
                    sub_rol=sub_rol,
                )
            )

        for i, (nombre, rnc, representante, categoria, estado) in enumerate(EMPRESAS):
            if db.scalar(select(Afiliado).where(Afiliado.rnc_cedula == rnc)):
                continue

            slug = nombre.lower().split()[-1].replace(".", "")
            email = f"admin@{slug}.do"

            usuario = Usuario(
                email=email,
                nombre=representante,
                password_hash=hash_password("afiliado2026"),
                rol=RolUsuario.AFILIADO,
            )
            db.add(usuario)
            db.flush()

            vence = (
                hoy - timedelta(days=random.randint(10, 120))
                if estado == EstadoAfiliado.VENCIDO
                else date(hoy.year, 12, 31)
            )
            afiliado = Afiliado(
                usuario_id=usuario.id,
                rnc_cedula=rnc,
                nombre=nombre,
                categoria=categoria,
                estado=estado,
                representante=representante,
                email=email,
                telefono=f"809-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                direccion=f"Av. Barceló {random.randint(2, 90)}, Bávaro",
                fecha_afiliacion=date(hoy.year - random.randint(1, 7), random.randint(1, 12), 14),
                fecha_vencimiento=vence,
                cuota_anual=CUOTA[categoria],
            )
            db.add(afiliado)
            db.flush()

            for area, cargo in (
                (AreaContacto.CONTABILIDAD, "Encargada de contabilidad"),
                (AreaContacto.MARKETING, "Coordinador de marketing"),
                (AreaContacto.COMERCIAL, "Gerente comercial"),
            ):
                db.add(
                    ContactoAfiliado(
                        afiliado_id=afiliado.id,
                        area=area,
                        nombre=f"{area.value.capitalize()} {nombre.split()[0]}",
                        cargo=cargo,
                        telefono=f"809-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                        email=f"{area.value}@{slug}.do",
                    )
                )

            for tipo in TipoDocumento:
                if tipo == TipoDocumento.SOPORTE_PAGO and estado != EstadoAfiliado.ACTIVO:
                    doc_estado = EstadoDocumento.PENDIENTE
                else:
                    doc_estado = EstadoDocumento.APROBADO
                db.add(
                    Documento(
                        afiliado_id=afiliado.id,
                        tipo=tipo,
                        estado=doc_estado,
                        archivo_url=f"documentos/{hoy.year}/{afiliado.id}/demo-{tipo.value}.pdf",
                        nombre_archivo=f"{tipo.value}-{slug}.pdf",
                        content_type="application/pdf",
                        tamano_bytes=random.randint(180_000, 1_400_000),
                    )
                )

            if estado != EstadoAfiliado.VENCIDO:
                for offset in range(random.randint(1, 3)):
                    anio = hoy.year - offset
                    pago = Pago(
                        afiliado_id=afiliado.id,
                        monto=CUOTA[categoria] - Decimal(offset * 3000),
                        fecha=date(anio, random.randint(1, 3), random.randint(3, 27)),
                        metodo=random.choice(list(MetodoPago)),
                        referencia=f"TRF-{random.randint(100000, 999999)}",
                        concepto=f"Cuota anual {anio}",
                        periodo=anio,
                    )
                    db.add(pago)
                    db.flush()
                    crear_proforma(
                        db,
                        afiliado=afiliado,
                        monto=pago.monto,
                        concepto=pago.concepto,
                        pago_id=pago.id,
                        fecha_generacion=pago.fecha,
                        subir_pdf=False,
                    )

        db.commit()

    print("Datos de prueba cargados.")
    print("  Panel admin  gestion@adecla.do / adecla2026   (administrador)")
    print("               consulta@adecla.do / adecla2026  (consultor)")
    print("  Portal       admin@srl.do / afiliado2026      (u otro correo de la lista)")
    if not settings.storage_configurado:
        print("  Nota: sin storage configurado, los documentos son referencias sin archivo real.")


if __name__ == "__main__":
    sembrar()
