"""Configuración de la aplicación.

Todo lo que cambia entre entornos (local, Railway, DigitalOcean) vive aquí y
llega por variable de entorno. Ningún valor de infraestructura está escrito
en el código: mover el backend de Railway a un droplet propio debería ser
cuestión de copiar el .env, no de tocar Python.
"""

import sys
from functools import lru_cache

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Aplicación ---
    APP_NAME: str = "ADECLA · Sistema de afiliados"
    APP_ENV: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    # Vuelca cada consulta al log. Va aparte de DEBUG: querer trazas de la app
    # no es querer el SQL de cada petición encima.
    SQL_ECHO: bool = False

    # --- Base de datos ---
    # Acepta tal cual la URL que entregan Neon, Supabase o Railway.
    DATABASE_URL: str = "postgresql+psycopg://adecla:adecla@localhost:5432/adecla"

    # --- Autenticación ---
    JWT_SECRET: str = "cambiame-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14

    # --- CORS ---
    # Coma separada: "https://afiliados.adecla.do,https://adecla.vercel.app"
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Storage compatible con S3 (Cloudflare R2 por defecto) ---
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "auto"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "adecla-documentos"
    # Dominio público del bucket (R2 custom domain). Si queda vacío se firman
    # URLs temporales en lugar de devolver enlaces públicos.
    S3_PUBLIC_BASE_URL: str = ""
    S3_SIGNED_URL_TTL: int = 3600
    MAX_UPLOAD_MB: int = 10

    # --- Correo (Resend) ---
    RESEND_API_KEY: str = ""
    # El remitente tiene que estar en un dominio verificado en Resend, o
    # rebota todo. Mientras se verifica adecla.do sirve onboarding@resend.dev.
    EMAIL_FROM: str = "ADECLA <onboarding@resend.dev>"
    EMAIL_REPLY_TO: str = ""
    # Se usa para los enlaces y el logo de los correos, así que apunta al
    # frontend, no a la API.
    FRONTEND_URL: str = "http://localhost:5173"

    # --- Datos de la asociación (cabecera y pie de la proforma) ---
    # Salen de la factura proforma que ADECLA emite hoy. Van por entorno para
    # poder corregir una dirección o una cuenta sin tocar el código.
    ORG_DIRECCION: str = (
        "Boulevar 1ro. De Noviembre|Edificio Cedro, Suite 1002P|"
        "Punta Cana Village, Punta Cana, Rep. Dom."
    )
    ORG_RNC: str = "430134309"
    BANCO_NOMBRE: str = "Banco Popular"
    BANCO_TIPO_CUENTA: str = "Cuenta corriente"
    BANCO_CUENTA: str = "782705941"
    BANCO_TITULAR: str = "ADECLA"

    # --- Reglas de negocio ---
    CUOTA_ANUAL_DEFAULT: float = 45000.00
    MONEDA: str = "DOP"
    DIAS_AVISO_VENCIMIENTO: int = 30

    @field_validator("DATABASE_URL")
    @classmethod
    def normalizar_driver(cls, v: str) -> str:
        """Neon y Railway entregan `postgres://` o `postgresql://`.

        SQLAlchemy necesita saber qué driver usar; forzamos psycopg 3 sin
        obligar a nadie a editar la URL que copió del proveedor.

        Si la variable llega vacía se corta aquí con el motivo escrito: dejarla
        pasar produce un `Could not parse SQLAlchemy URL from string ''` a
        cuarenta líneas de profundidad dentro de Alembic, que no dice nada de
        lo que hay que arreglar.
        """
        v = (v or "").strip()
        if not v:
            raise ValueError(
                "DATABASE_URL llegó vacía. En Railway suele ser que la referencia "
                "${{Postgres.DATABASE_URL}} no resolvió: revisa que el servicio de "
                "Postgres esté en el mismo proyecto y que su nombre coincida con el "
                "de la referencia. Con Neon o Supabase, pega la cadena de conexión."
            )

        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def direccion_lineas(self) -> list[str]:
        return [l.strip() for l in self.ORG_DIRECCION.split("|") if l.strip()]

    @property
    def correo_configurado(self) -> bool:
        return bool(self.RESEND_API_KEY and self.EMAIL_FROM)

    @property
    def storage_configurado(self) -> bool:
        return bool(self.S3_ACCESS_KEY_ID and self.S3_SECRET_ACCESS_KEY and self.S3_BUCKET)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        # Una configuración incompleta es un error de operación, no un bug: se
        # informa qué falta en dos líneas y se sale. El traceback de pydantic
        # enterrado dentro de Alembic no le sirve a nadie.
        print("No se pudo iniciar: revisa las variables de entorno.", file=sys.stderr)
        for error in exc.errors():
            campo = ".".join(str(parte) for parte in error["loc"])
            print(f"  · {campo}: {error['msg']}", file=sys.stderr)
        raise SystemExit(1) from None


settings = get_settings()
