import asyncio
from typing import List
from playwright.async_api import async_playwright
from app.scrapers.base import ProductoRaw


async def buscar(query: str, timeout_ms: int = 30000) -> List[ProductoRaw]:
    api_response = {"value": None}
    captured = asyncio.Event()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-CL",
        )
        page = await context.new_page()

        async def handle_response(response):
            if "/product-service/products/search" in response.url and api_response["value"] is None:
                try:
                    data = await response.json()
                    if data.get("hits"):
                        api_response["value"] = data
                        captured.set()
                except Exception:
                    pass

        page.on("response", handle_response)
        url = f"https://www.cruzverde.cl/search?query={query}"
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            await asyncio.wait_for(captured.wait(), timeout=15)
        except asyncio.TimeoutError:
            pass
        await browser.close()

    data = api_response["value"]
    if not data:
        return []

    productos = []
    for hit in data.get("hits", []):
        prices = hit.get("prices", {})
        precio_actual = prices.get("price-sale-cl") or prices.get("price-list-cl")
        precio_normal = prices.get("price-list-cl")
        if precio_actual is None:
            continue
        productos.append(ProductoRaw(
            cadena="cruzverde",
            sku=str(hit.get("productId", "")),
            nombre=hit.get("productName", "").strip(),
            marca=hit.get("brand"),
            precio_actual=float(precio_actual),
            precio_normal=float(precio_normal) if precio_normal else None,
            descuento_pct=hit.get("discountPercentage"),
            stock=hit.get("stock", 0) > 0,
            es_bioequivalente=hit.get("isBioequivalent", False),
            url=hit.get("link", ""),
            imagen=hit.get("image", {}).get("link") if isinstance(hit.get("image"), dict) else None,
        ))
    return productos    