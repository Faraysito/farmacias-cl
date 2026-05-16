import asyncio
import sys
from app.scrapers.salcobrand import buscar
from app.persistencia import guardar_productos


async def main(query: str):
    print(f"Scrapeando Salcobrand para '{query}'...")
    productos = await buscar(query)
    print(f"  {len(productos)} productos encontrados")
    
    if not productos:
        return
    
    insertados = guardar_productos(productos)
    print(f"  {insertados} precios guardados en DB")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "losartan"
    asyncio.run(main(query))