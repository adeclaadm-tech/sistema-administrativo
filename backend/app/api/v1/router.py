from fastapi import APIRouter

from app.api.v1.endpoints import (
    afiliados,
    auth,
    documentos,
    pagos,
    proformas,
    reportes,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(afiliados.router)
api_router.include_router(documentos.router)
api_router.include_router(pagos.router)
api_router.include_router(proformas.router)
api_router.include_router(reportes.router)
api_router.include_router(usuarios.router)
