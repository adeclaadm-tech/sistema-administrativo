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
    """Tipo de afiliación que maneja ADECLA en su padrón.

    Son las mismas tres del sistema de inscripciones al torneo, para que una
    empresa signifique lo mismo en los dos lados. Queda nula cuando el padrón
    no la trae: once de las 51 empresas importadas no la tienen asignada.
    """

    CONSTRUCTOR = "constructor"
    PROVEEDOR = "proveedor"
    DESARROLLADOR = "desarrollador"


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
