import unicodedata
from datetime import timedelta
from typing import List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Farmacia, Medicamento, Precio, PrincipioActivo, utcnow
from app.normalizador import normalizar
from app.scrapers.base import ProductoRaw


def _normalizar_lab(lab: str | None) -> str:
    if not lab:
        return ""
    s = "".join(
        c
        for c in unicodedata.normalize("NFD", lab.lower())
        if unicodedata.category(c) != "Mn"
    )
    for sufijo in [" s.a", " sa", " spa", " ltda", " limitada", " chile"]:
        s = s.replace(sufijo, "")
    return s.strip()


def get_or_create_farmacia_cadena(db: Session, cadena: str) -> Farmacia:
    f = (
        db.query(Farmacia)
        .filter(Farmacia.cadena == cadena, Farmacia.nombre == f"{cadena} online")
        .first()
    )
    if f:
        return f
    f = Farmacia(cadena=cadena, nombre=f"{cadena} online", comuna="online")
    db.add(f)
    db.flush()
    return f


def get_or_create_principio(
    db: Session, nombre: str, dosis: str | None
) -> PrincipioActivo:
    p = (
        db.query(PrincipioActivo)
        .filter(PrincipioActivo.nombre == nombre, PrincipioActivo.dosis == dosis)
        .first()
    )
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
    lab_norm = _normalizar_lab(laboratorio)
    candidatos = (
        db.query(Medicamento)
        .filter(Medicamento.principio_activo_id == principio_id)
        .all()
    )
    for c in candidatos:
        if _normalizar_lab(c.laboratorio) == lab_norm:
            return c

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
    db = SessionLocal()
    insertados = 0
    try:
        ahora = utcnow()
        hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        manana = hoy_inicio + timedelta(days=1)

        for p in productos:
            principio_nombre, dosis_mg = normalizar(p.nombre, p.marca)
            dosis = f"{dosis_mg}mg" if dosis_mg is not None else None
            principio = get_or_create_principio(db, principio_nombre, dosis)
            medicamento = get_or_create_medicamento(
                db,
                nombre_comercial=p.nombre,
                laboratorio=p.marca,
                es_bio=p.es_bioequivalente,
                principio_id=principio.id,
            )
            farmacia = get_or_create_farmacia_cadena(db, p.cadena)

            # Un único punto por día y farmacia: si ya existe hoy, se actualiza.
            existente = (
                db.query(Precio)
                .filter(
                    Precio.medicamento_id == medicamento.id,
                    Precio.farmacia_id == farmacia.id,
                    Precio.fecha_scrape >= hoy_inicio,
                    Precio.fecha_scrape < manana,
                )
                .first()
            )

            if existente:
                existente.precio = p.precio_actual
                existente.stock = p.stock
                existente.url = p.url or None
                existente.fecha_scrape = ahora
            else:
                db.add(
                    Precio(
                        medicamento_id=medicamento.id,
                        farmacia_id=farmacia.id,
                        precio=p.precio_actual,
                        stock=p.stock,
                        url=p.url or None,
                        fecha_scrape=ahora,
                    )
                )
                insertados += 1

        db.commit()
        return insertados
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
