from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import PrincipioActivo, Medicamento, Farmacia, Precio
from app.scrapers.base import ProductoRaw
from app.utils import parsear_medicamento


def get_or_create_farmacia_cadena(db: Session, cadena: str) -> Farmacia:
    """
    Para precios online de cadenas (no sucursales físicas), usamos una farmacia
    "virtual" por cadena. Después agregamos sucursales reales.
    """
    f = db.query(Farmacia).filter(
        Farmacia.cadena == cadena,
        Farmacia.nombre == f"{cadena} online"
    ).first()
    if f:
        return f
    f = Farmacia(cadena=cadena, nombre=f"{cadena} online", comuna="online")
    db.add(f)
    db.flush()
    return f


def get_or_create_principio(db: Session, nombre: str, dosis: str | None) -> PrincipioActivo:
    p = db.query(PrincipioActivo).filter(
        PrincipioActivo.nombre == nombre,
        PrincipioActivo.dosis == dosis
    ).first()
    if p:
        return p
    p = PrincipioActivo(nombre=nombre, dosis=dosis)
    db.add(p)
    db.flush()
    return p


def get_or_create_medicamento(
    db: Session,
    nombre_comercial: str,
    laboratorio: str | None,
    es_bio: bool,
    principio_id: int,
) -> Medicamento:
    m = db.query(Medicamento).filter(
        Medicamento.nombre_comercial == nombre_comercial,
        Medicamento.principio_activo_id == principio_id,
    ).first()
    if m:
        return m
    m = Medicamento(
        nombre_comercial=nombre_comercial,
        laboratorio=laboratorio,
        es_bioequivalente=es_bio,
        principio_activo_id=principio_id,
    )
    db.add(m)
    db.flush()
    return m


def guardar_productos(productos: List[ProductoRaw]) -> int:
    """Guarda productos scrapeados. Retorna número de precios insertados."""
    db = SessionLocal()
    insertados = 0
    try:
        for p in productos:
            principio_nombre, dosis = parsear_medicamento(p.nombre)
            principio = get_or_create_principio(db, principio_nombre, dosis)
            medicamento = get_or_create_medicamento(
                db,
                nombre_comercial=p.nombre,
                laboratorio=p.marca,
                es_bio=p.es_bioequivalente,
                principio_id=principio.id,
            )
            farmacia = get_or_create_farmacia_cadena(db, p.cadena)
            
            precio = Precio(
                medicamento_id=medicamento.id,
                farmacia_id=farmacia.id,
                precio=p.precio_actual,
                stock=p.stock,
            )
            db.add(precio)
            insertados += 1
        
        db.commit()
        return insertados
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()