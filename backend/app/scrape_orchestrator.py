"""Coordina scraping en paralelo de las 3 cadenas."""
import asyncio
from app.config import DISABLE_CRUZVERDE
from app.scrapers.salcobrand import buscar as buscar_sb
from app.scrapers.ahumada import buscar as buscar_ah
from app.persistencia import guardar_productos


async def scrape_todas(query: str) -> dict[str, int]:
    """Scrapea las cadenas activas en paralelo y guarda en DB."""
    tareas = [
        _safe(buscar_sb, query, "salcobrand"),
        _safe(buscar_ah, query, "ahumada"),
    ]
    if not DISABLE_CRUZVERDE:
        from app.scrapers.cruzverde import buscar as buscar_cv
        tareas.insert(0, _safe(buscar_cv, query, "cruzverde"))

    resultados = await asyncio.gather(*tareas, return_exceptions=False)
    resumen = {}
    for nombre, productos in resultados:
        if productos:
            try:
                guardar_productos(productos)
                resumen[nombre] = len(productos)
            except Exception as e:
                resumen[nombre] = f"error guardando: {e}"
        else:
            resumen[nombre] = 0
    return resumen


async def _safe(fn, query: str, nombre: str):
    try:
        productos = await fn(query)
        return (nombre, productos)
    except Exception as e:
        print(f"[scrape on-demand] {nombre} falló: {e}")
        return (nombre, [])