"""Crea el primer administrador del panel.

    python -m app.scripts.crear_admin

Existe por un problema de huevo y gallina: el registro abierto solo da de alta
afiliados, y `/usuarios` exige una sesión de administrador. En una base recién
migrada no hay forma de entrar al panel sin esto. El seed también crea cuentas
de staff, pero arrastra afiliados de mentira: no sirve para producción.

Las credenciales llegan por variable de entorno o por argumento:

    ADMIN_EMAIL=gestion@adecla.do ADMIN_PASSWORD=... python -m app.scripts.crear_admin
    python -m app.scripts.crear_admin --email gestion@adecla.do --password ... --nombre "Laura Méndez"

En Railway se corre una sola vez desde la consola del servicio.
"""

import argparse
import os
import sys

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import RolUsuario, SubRolAdmin, Usuario

LARGO_MINIMO = 8


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea el primer administrador del panel.")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
    parser.add_argument("--nombre", default=os.getenv("ADMIN_NOMBRE", "Administrador ADECLA"))
    parser.add_argument(
        "--consultor",
        action="store_true",
        help="Crea la cuenta como consultor (solo lectura) en vez de administrador.",
    )
    return parser.parse_args()


def crear_admin() -> int:
    args = parsear_argumentos()

    if not args.email or not args.password:
        print(
            "Faltan credenciales. Pasa --email y --password, o define ADMIN_EMAIL "
            "y ADMIN_PASSWORD en el entorno.",
            file=sys.stderr,
        )
        return 1

    if len(args.password) < LARGO_MINIMO:
        print(f"La contraseña necesita al menos {LARGO_MINIMO} caracteres.", file=sys.stderr)
        return 1

    email = args.email.strip().lower()
    sub_rol = SubRolAdmin.CONSULTOR if args.consultor else SubRolAdmin.ADMINISTRADOR

    with SessionLocal() as db:
        existente = db.scalar(select(Usuario).where(func.lower(Usuario.email) == email))
        if existente is not None:
            # No se pisa la contraseña de una cuenta que ya existe: si alguien
            # corre esto dos veces por error, no debería quedar fuera de su
            # propio panel.
            print(f"Ya existe una cuenta con {email} (rol: {existente.rol.value}). Sin cambios.")
            return 0

        db.add(
            Usuario(
                email=email,
                nombre=args.nombre,
                password_hash=hash_password(args.password),
                rol=RolUsuario.ADMIN,
                sub_rol=sub_rol,
            )
        )
        db.commit()

    print(f"Cuenta creada: {email} ({sub_rol.value}).")
    print("Entra en /admin/login y cambia la contraseña desde el panel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(crear_admin())
