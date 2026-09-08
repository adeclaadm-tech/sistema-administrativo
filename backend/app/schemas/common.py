from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=False)


class Pagina(BaseModel, Generic[T]):
    """Respuesta paginada estándar: la tabla del panel la lee tal cual."""

    items: list[T]
    total: int
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=200)

    @property
    def paginas(self) -> int:
        return max(1, -(-self.total // self.per_page))


class Mensaje(BaseModel):
    detail: str
