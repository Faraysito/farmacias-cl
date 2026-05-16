"""Scraper Salcobrand vía API Algolia directa (sin browser)."""
import httpx
from typing import List
from app.scrapers.base import ProductoRaw

ALGOLIA_APP_ID = "GM3RP06HJG"
ALGOLIA_API_KEY = "0259fe250b3be4b1326eb85e47aa7d81"
ALGOLIA_HOST = f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net"
ALGOLIA_INDEX = "sb_variant_production"

CADENA = "salcobrand"
BASE_PRODUCT_URL = "https://salcobrand.cl/products/"


async def buscar(query: str, limite: int = 24) -> List[ProductoRaw]:
    url = f"{ALGOLIA_HOST}/1/indexes/*/queries"
    params = {
        "x-algolia-agent": "Algolia for JavaScript (4.14.3); Browser (lite)",
        "x-algolia-api-key": ALGOLIA_API_KEY,
        "x-algolia-application-id": ALGOLIA_APP_ID,
    }
    algolia_params = (
        "clickAnalytics=true"
        f"&hitsPerPage={limite}"
        "&page=0"
        f"&query={query}"
        "&tagFilters="
    )
    body = {
        "requests": [
            {"indexName": ALGOLIA_INDEX, "params": algolia_params}
        ]
    }
    headers = {
        "Origin": "https://salcobrand.cl",
        "Referer": "https://salcobrand.cl/",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, params=params, json=body, headers=headers)
        r.raise_for_status()
        data = r.json()

    hits = data["results"][0].get("hits", [])
    return [_a_producto_raw(h) for h in hits]


def _a_producto_raw(hit: dict) -> ProductoRaw:
    normal = int(hit.get("normal_price") or 0)
    descuento_raw = hit.get("direct_discount")
    actual = int(float(descuento_raw)) if descuento_raw else normal

    descuento_pct = None
    if normal and actual and actual < normal:
        descuento_pct = round((1 - actual / normal) * 100, 2)

    slug = hit.get("slug") or ""
    return ProductoRaw(
        cadena=CADENA,
        sku=str(hit.get("sku") or hit.get("objectID")),
        nombre=hit.get("name", ""),
        marca=(hit.get("brand") or "").strip(),
        precio_actual=actual,
        precio_normal=normal,
        descuento_pct=descuento_pct,
        stock=bool(hit.get("has_stock")),
        es_bioequivalente=bool(
            (hit.get("bioequivalent_filter") or {}).get("has_bioequivalent")
        ),
        url=f"{BASE_PRODUCT_URL}{slug}" if slug else "",
        imagen=hit.get("catalog_image_url", ""),
    )