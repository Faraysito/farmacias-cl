from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PrecioResponse(BaseModel):
    cadena: str
    precio: float
    stock: bool
    fecha_scrape: datetime
    url: Optional[str] = None


class MedicamentoResponse(BaseModel):
    id: int
    nombre_comercial: str
    laboratorio: Optional[str]
    es_bioequivalente: bool
    principio_activo: Optional[str]
    dosis: Optional[str]
    precios: list[PrecioResponse]

    class Config:
        from_attributes = True


class MedicamentoEnGrupo(BaseModel):
    id: int
    nombre_comercial: str
    laboratorio: str | None
    es_bioequivalente: bool
    precios: list[PrecioResponse]

    class Config:
        from_attributes = True


class GrupoResponse(BaseModel):
    principio_activo: str
    dosis: str | None
    cantidad_medicamentos: int
    medicamentos: list[MedicamentoEnGrupo]