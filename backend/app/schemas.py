from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PrecioResponse(BaseModel):
    cadena: str
    precio: float
    stock: bool
    fecha_scrape: datetime


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