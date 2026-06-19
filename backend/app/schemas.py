from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PrecioResponse(BaseModel):
    cadena: str
    precio: float
    stock: bool
    fecha_scrape: datetime
    url: str | None = None


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
    # Resumen de ahorro: el gancho comercial de la app.
    precio_min: float | None = None
    precio_max: float | None = None
    ahorro_abs: float | None = None
    ahorro_pct: float | None = None
    actualizado: datetime | None = None
    medicamentos: list[MedicamentoEnGrupo]


class BusquedaResponse(BaseModel):
    """Respuesta paginada de /api/buscar."""

    query: str
    total: int
    pagina: int
    por_pagina: int
    grupos: list[GrupoResponse]


# --- Histórico ---
class PuntoHistorico(BaseModel):
    fecha: str
    precio: float


class ResumenHistorico(BaseModel):
    min: float | None = None
    max: float | None = None
    promedio: float | None = None
    actual: float | None = None
    tendencia: str | None = None  # "baja" | "sube" | "estable"
    variacion_pct: float | None = None


# --- Alertas ---
class AlertaCrear(BaseModel):
    email: EmailStr
    medicamento_id: int
    precio_objetivo: float = Field(gt=0)


class AlertaResponse(BaseModel):
    id: int
    email: str
    medicamento_id: int
    precio_objetivo: float
    activa: bool

    class Config:
        from_attributes = True
