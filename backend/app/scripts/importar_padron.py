"""Importa el padrón real de afiliados de ADECLA.

    python -m app.scripts.importar_padron
    python -m app.scripts.importar_padron --archivo otro.json --vence 2026-12-31

El JSON viene del sistema de inscripciones al torneo, que a su vez lo sacó del
Excel que mantiene la asociación. Son las mismas empresas, así que una
constructora significa lo mismo en los dos sistemas.

Lo que trae ese listado: nombre, tipo de afiliación, persona de contacto,
teléfono y correo. Lo que **no** trae: RNC, fechas de afiliación y
vencimiento, y montos de cuota. Esos campos quedan vacíos a propósito para
que el staff los complete desde el panel; inventarlos haría imposible
distinguir después un dato real de uno de relleno.

Es idempotente: reconoce a las empresas por nombre y actualiza en vez de
duplicar, así que se puede correr de nuevo cuando el Excel cambie.
"""

import argparse
import json
import pathlib
import sys
import unicodedata
from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Afiliado, AreaContacto, CategoriaAfiliado, ContactoAfiliado, EstadoAfiliado

ARCHIVO_POR_DEFECTO = pathlib.Path(__file__).parent / "datos" / "padron-adecla.json"

CATEGORIAS = {
    "CONSTRUCTOR": CategoriaAfiliado.CONSTRUCTOR,
    "PROVEEDOR": CategoriaAfiliado.PROVEEDOR,
    "DESARROLLADOR": CategoriaAfiliado.DESARROLLADOR,
}

ESTADOS = {
    "ACTIVO": EstadoAfiliado.ACTIVO,
    "PENDIENTE": EstadoAfiliado.PENDIENTE,
    "VENCIDO": EstadoAfiliado.VENCIDO,
}


def clave_de_nombre(nombre: str) -> str:
    """Normaliza para comparar: sin acentos, sin puntuación, en minúscula.

    "Abreu-Medina" y "Abreu Medina" son la misma empresa escrita por dos
    personas distintas; sin esto, la segunda corrida crearía un duplicado.
    """
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return " ".join(sin_acentos.lower().replace("-", " ").split())


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa el padrón de afiliados de ADECLA.")
    parser.add_argument("--archivo", type=pathlib.Path, default=ARCHIVO_POR_DEFECTO)
    parser.add_argument(
        "--vence",
        help="Fecha de vencimiento a aplicar a todos, formato AAAA-MM-DD. "
        "Sin esto la fecha queda vacía y se asigna una por una desde el panel.",
    )
    parser.add_argument(
        "--estado",
        choices=sorted(ESTADOS),
        help="Fuerza el estado de todos. Por defecto se respeta el del archivo.",
    )
    return parser.parse_args()


def importar() -> int:
    args = parsear_argumentos()

    if not args.archivo.exists():
        print(f"No encuentro el archivo: {args.archivo}", file=sys.stderr)
        return 1

    vence: date | None = None
    if args.vence:
        try:
            vence = date.fromisoformat(args.vence)
        except ValueError:
            print(f"Fecha inválida: {args.vence}. Usa AAAA-MM-DD.", file=sys.stderr)
            return 1

    registros = json.loads(args.archivo.read_text(encoding="utf-8"))
    estado_forzado = ESTADOS[args.estado] if args.estado else None

    creados = actualizados = 0

    with SessionLocal() as db:
        existentes = {
            clave_de_nombre(a.nombre): a for a in db.scalars(select(Afiliado)).all()
        }

        for registro in registros:
            nombre = (registro.get("name") or "").strip()
            if not nombre:
                continue

            categoria = CATEGORIAS.get(registro.get("affiliationType") or "")
            estado = estado_forzado or ESTADOS.get(registro.get("status") or "", EstadoAfiliado.ACTIVO)
            contacto = (registro.get("contactName") or "").strip() or None
            telefono = (registro.get("phone") or "").strip() or None
            email = (registro.get("email") or "").strip().lower() or None

            afiliado = existentes.get(clave_de_nombre(nombre))

            if afiliado is None:
                afiliado = Afiliado(
                    nombre=nombre,
                    categoria=categoria,
                    estado=estado,
                    representante=contacto,
                    telefono=telefono,
                    email=email,
                )
                if vence:
                    afiliado.fecha_vencimiento = vence
                db.add(afiliado)
                db.flush()
                existentes[clave_de_nombre(nombre)] = afiliado
                creados += 1
            else:
                # Solo se rellenan huecos: lo que el staff ya corrigió en el
                # panel pesa más que el Excel de origen.
                afiliado.categoria = afiliado.categoria or categoria
                afiliado.representante = afiliado.representante or contacto
                afiliado.telefono = afiliado.telefono or telefono
                afiliado.email = afiliado.email or email
                if vence:
                    afiliado.fecha_vencimiento = vence
                actualizados += 1

            # El contacto del padrón es la persona con la que ADECLA ya habla;
            # entra como contacto comercial, que es el trato que tiene hoy.
            if contacto and not any(c.area == AreaContacto.COMERCIAL for c in afiliado.contactos):
                db.add(
                    ContactoAfiliado(
                        afiliado_id=afiliado.id,
                        area=AreaContacto.COMERCIAL,
                        nombre=contacto,
                        telefono=telefono,
                        email=email,
                    )
                )

            if registro.get("previousName"):
                nota = f"Antes: {registro['previousName']}"
                if not afiliado.notas:
                    afiliado.notas = nota
                elif nota not in afiliado.notas:
                    afiliado.notas = f"{afiliado.notas}\n{nota}"

        db.commit()

    print(f"Padrón importado: {creados} creados, {actualizados} actualizados.")
    if not vence:
        print(
            "Las fechas de vencimiento quedaron vacías. Asígnalas desde la ficha de "
            "cada afiliado, o vuelve a correr con --vence AAAA-MM-DD para ponerlas todas."
        )
    print("El RNC y la cuota anual también quedan vacíos: no vienen en el padrón.")
    return 0


if __name__ == "__main__":
    raise SystemExit(importar())
