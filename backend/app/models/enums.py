"""Enums del dominio.

Lo que se guarda en Postgres son los strings en minúscula. Al crear los tipos
ENUM con `values_callable` evitamos que Alembic escriba los nombres de los
miembros en mayúscula.
"""

from enum import Enum


class RolUsuario(str, Enum):
    AFILIADO = "afiliado"
    ADMIN = "admin"


class SubRolAdmin(str, Enum):
    """Solo aplica a usuarios con rol `admin`.

    - administrador: gestiona todo, incluidos los usuarios del staff.
    - consultor: consulta y exporta, pero no aprueba documentos ni registra pagos.
    """

    ADMINISTRADOR = "administrador"
    CONSULTOR = "consultor"


class EstadoAfiliado(str, Enum):
    ACTIVO = "activo"
    PENDIENTE = "pendiente"
    VENCIDO = "vencido"


class CategoriaAfiliado(str, Enum):
    CLASE_A = "clase_a"
    CLASE_B = "clase_b"
    CLASE_C = "clase_c"


class TipoDocumento(str, Enum):
    RNC_NID = "rnc_nid"
    CEDULA = "cedula"
    SOPORTE_PAGO = "soporte_pago"
    DOC_REPRESENTANTE = "doc_representante"


class EstadoDocumento(str, Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class AreaContacto(str, Enum):
    CONTABILIDAD = "contabilidad"
    MARKETING = "marketing"
    COMERCIAL = "comercial"


class MetodoPago(str, Enum):
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    OTRO = "otro"
