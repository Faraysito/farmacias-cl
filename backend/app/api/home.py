from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import Medicamento, Precio, Farmacia, PrincipioActivo

router = APIRouter()

# Categorías hardcoded — query = búsqueda que dispara
CATEGORIAS = [
    {"id": "presion", "nombre": "Presión arterial", "icono": "🩺", "query": "losartan", "color": "from-red-500 to-pink-500"},
    {"id": "colesterol", "nombre": "Colesterol", "icono": "💊", "query": "atorvastatina", "color": "from-amber-500 to-orange-500"},
    {"id": "diabetes", "nombre": "Diabetes", "icono": "🩸", "query": "metformina", "color": "from-purple-500 to-indigo-500"},
    {"id": "dolor", "nombre": "Dolor y fiebre", "icono": "🤕", "query": "paracetamol", "color": "from-blue-500 to-cyan-500"},
    {"id": "antiinflamatorio", "nombre": "Antiinflamatorios", "icono": "🔥", "query": "ibuprofeno", "color": "from-orange-500 to-red-500"},
    {"id": "antibiotico", "nombre": "Antibióticos", "icono": "🦠", "query": "amoxicilina", "color": "from-teal-500 to-emerald-500"},
    {"id": "gastrico", "nombre": "Gástrico", "icono": "🫃", "query": "omeprazol", "color": "from-lime-500 to-green-500"},
    {"id": "mental", "nombre": "Salud mental", "icono": "🧠", "query": "sertralina", "color": "from-violet-500 to-purple-500"},
]


@router.get("/home/categorias")
def get_categorias():
    return CATEGORIAS


@router.get("/home/top")
def get_top(db: Session = Depends(get_db), limit: int = 8):
    """Top medicamentos: 1 por principio activo, el más barato disponible."""
    # Subquery: precio mínimo por medicamento (última lectura por cadena)
    sub = (
        db.query(
            Precio.medicamento_id.label("med_id"),
            func.min(Precio.precio).label("precio_min"),
            func.count(func.distinct(Farmacia.cadena)).label("n_cadenas"),
        )
        .join(Farmacia, Farmacia.id == Precio.farmacia_id)
        .group_by(Precio.medicamento_id)
        .subquery()
    )

    rows = (
        db.query(
            Medicamento.id,
            Medicamento.nombre_comercial,
            Medicamento.laboratorio,
            Medicamento.es_bioequivalente,
            PrincipioActivo.nombre.label("principio"),
            PrincipioActivo.dosis,
            sub.c.precio_min,
            sub.c.n_cadenas,
        )
        .join(PrincipioActivo, PrincipioActivo.id == Medicamento.principio_activo_id)
        .join(sub, sub.c.med_id == Medicamento.id)
        .order_by(desc(sub.c.n_cadenas), sub.c.precio_min)
        .all()
    )

    # Deduplicar por principio activo (quedarse con el más barato de cada uno)
    vistos = set()
    out = []
    for r in rows:
        if r.principio in vistos:
            continue
        vistos.add(r.principio)
        out.append({
            "id": r.id,
            "nombre_comercial": r.nombre_comercial,
            "laboratorio": r.laboratorio,
            "es_bioequivalente": r.es_bioequivalente or False,
            "principio_activo": r.principio,
            "dosis": r.dosis,
            "precio_min": r.precio_min,
            "n_cadenas": r.n_cadenas,
        })
        if len(out) >= limit:
            break

    return out


@router.get("/home/stats")
def get_stats(db: Session = Depends(get_db)):
    """Estadísticas para mostrar en el hero."""
    n_meds = db.query(func.count(Medicamento.id)).scalar() or 0
    n_precios = db.query(func.count(Precio.id)).scalar() or 0
    n_principios = db.query(func.count(PrincipioActivo.id)).scalar() or 0
    return {
        "medicamentos": n_meds,
        "precios": n_precios,
        "principios_activos": n_principios,
        "cadenas": 3,
    }