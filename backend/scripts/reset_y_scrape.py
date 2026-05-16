"""Borra precios/medicamentos/principios y re-scrapea todo desde 0."""
import asyncio
from app.database import SessionLocal
from app.models import Precio, Medicamento, PrincipioActivo
from app.scrapers.cruzverde import buscar as buscar_cv
from app.scrapers.salcobrand import buscar as buscar_sb
from app.scrapers.ahumada import buscar as buscar_ah
from app.persistencia import guardar_productos

MEDICAMENTOS = [
    "losartan", "metformina", "atorvastatina", "paracetamol",
    "ibuprofeno", "omeprazol", "enalapril", "amoxicilina",
]


def limpiar_db():
    db = SessionLocal()
    try:
        db.query(Precio).delete()
        db.query(Medicamento).delete()
        db.query(PrincipioActivo).delete()
        db.commit()
        print("✓ DB limpiada (precios, medicamentos, principios)")
    finally:
        db.close()


async def scrape_uno(query: str):
    print(f"\n--- {query} ---")
    for nombre, fn in [("cruzverde", buscar_cv), ("salcobrand", buscar_sb), ("ahumada", buscar_ah)]:
        try:
            productos = await fn(query)
            n = guardar_productos(productos)
            print(f"  {nombre}: {n} precios")
        except Exception as e:
            print(f"  {nombre}: ERROR {e}")


async def main():
    limpiar_db()
    for med in MEDICAMENTOS:
        await scrape_uno(med)
    print("\n✓ Listo")


if __name__ == "__main__":
    asyncio.run(main())