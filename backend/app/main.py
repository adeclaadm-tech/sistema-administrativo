"""Punto de entrada de la API.

Sin estado en el proceso: la base y el storage viven fuera, así que escalar a
más réplicas en Railway o mover el contenedor a un droplet no cambia nada del
código.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger("adecla")

if settings.SQL_ECHO:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=(
        "Backend del portal de afiliados y del panel administrativo de ADECLA "
        "(Asociación de Constructores, Punta Cana)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # el frontend lee el nombre del archivo exportado
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    """Mensajes en español y en singular, que es lo que ve el usuario final."""
    detalles = [
        {"campo": ".".join(str(p) for p in e["loc"][1:]), "mensaje": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Revisa los datos del formulario.", "errores": detalles},
    )


@app.get("/", tags=["salud"], summary="Ping")
def raiz() -> dict[str, str]:
    return {"servicio": settings.APP_NAME, "estado": "ok", "docs": "/docs"}


@app.get("/health", tags=["salud"], summary="Health check con base de datos")
def health() -> dict[str, str]:
    """Railway y DigitalOcean usan esta ruta como health check del contenedor."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        base = "ok"
    except Exception as exc:  # pragma: no cover
        logger.warning("Health check falló al conectar con la base: %s", exc)
        base = "error"
    return {
        "estado": "ok" if base == "ok" else "degradado",
        "base_de_datos": base,
        "storage": "ok" if settings.storage_configurado else "sin configurar",
        "entorno": settings.APP_ENV,
    }
