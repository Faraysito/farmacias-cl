"""Scraper Ahumada vía HTML (Salesforce Commerce Cloud, sin API JSON)."""
import re
import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import ProductoRaw

CADENA = "ahumada"
BASE_URL = "https://www.farmaciasahumada.cl"
SEARCH_URL = f"{BASE_URL}/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9",
}


async def buscar(query: str) -> List[ProductoRaw]:
    params = {"q": query, "search-button": "", "lang": "null"}

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(SEARCH_URL, params=params, headers=HEADERS)
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "html.parser")
    tiles = soup.select("div.product-tile[data-pid]")
    productos = []
    for tile in tiles:
        p = _parsear_tile(tile)
        if p:
            productos.append(p)
    return productos


def _parsear_tile(tile) -> ProductoRaw | None:
    pid = tile.get("data-pid", "").strip()
    if not pid:
        return None

    # Nombre + URL
    pdp_link = tile.select_one("div.pdp-link a")
    if not pdp_link:
        return None
    nombre = pdp_link.get_text(strip=True)
    href = pdp_link.get("href", "")
    url = href if href.startswith("http") else f"{BASE_URL}{href}"

    # Marca
    marca_el = tile.select_one("div.product-tile-brand .link")
    marca = marca_el.get_text(strip=True) if marca_el else ""

    # Imagen
    img_el = tile.select_one("img.tile-image")
    imagen = img_el.get("src", "") if img_el else ""

    # Precios
    precio_actual = _extraer_precio_actual(tile)
    precio_normal = _extraer_precio_normal(tile)
    if precio_actual is None:
        return None
    if precio_normal is None:
        precio_normal = precio_actual

    descuento_pct = None
    if precio_normal > precio_actual:
        descuento_pct = round((1 - precio_actual / precio_normal) * 100, 2)

    # Bioequivalente: existe el badge container con contenido
    bio_el = tile.select_one(".bioequivalent-badge-container")
    es_bio = bool(bio_el and bio_el.get_text(strip=True))

    return ProductoRaw(
        cadena=CADENA,
        sku=pid,
        nombre=nombre,
        marca=marca,
        precio_actual=precio_actual,
        precio_normal=precio_normal,
        descuento_pct=descuento_pct,
        stock=True,
        es_bioequivalente=es_bio,
        url=url,
        imagen=imagen,
    )


_PRECIO_RE = re.compile(r"\$\s*([\d.]+)")


def _extraer_precio_actual(tile) -> int | None:
    sales = tile.select_one(".sales")
    if not sales:
        return None
    texto = sales.get_text(" ", strip=True)
    m = _PRECIO_RE.search(texto)
    if not m:
        return None
    return int(m.group(1).replace(".", ""))


def _extraer_precio_normal(tile) -> int | None:
    el = tile.select_one("del span.value[content]")
    if not el:
        return None
    try:
        return int(el["content"])
    except (ValueError, KeyError):
        return None