from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductoRaw:
    cadena: str                   # "cruzverde", "salcobrand", "ahumada"
    sku: str                      # ID del producto en su sistema
    nombre: str
    marca: Optional[str]
    precio_actual: float
    precio_normal: Optional[float]
    descuento_pct: Optional[int]
    stock: bool
    es_bioequivalente: bool
    url: str
    imagen: Optional[str]