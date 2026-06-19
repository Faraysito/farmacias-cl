from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Farmacia, Medicamento, Precio, PrincipioActivo, utcnow

router = APIRouter()


def _resumen(precios: list[float]) -> dict:
    if not precios:
        return {
            "min": None, "max": None, "promedio": None,
            "actual": None, "tendencia": None, "variacion_pct": None,
        }
    actual = precios[-1]
    primero = precios[0]
    variacion = None
    tendencia = "estable"
    if primero:
        variacion = round((actual / primero - 1) * 100, 1)
        if variacion <= -1:
            tendencia = "baja"
        elif variacion >= 1:
            tendencia = "sube"
    return {
        "min": min(precios),
        "max": max(precios),
        "promedio": round(sum(precios) / len(precios), 0),
        "actual": actual,
        "tendencia": tendencia,
        "variacion_pct": variacion,
    }


@router.get("/historico/{med_id}")
def historico(med_id: int, dias: int = 90, db: Session = Depends(get_db)):
    med = db.query(Medicamento).filter(Medicamento.id == med_id).first()
    if not med:
        raise HTTPException(404, "medicamento no encontrado")

    desde = utcnow() - timedelta(days=dias)

    rows = (
        db.query(Precio.precio, Precio.fecha_scrape, Farmacia.cadena)
        .join(Farmacia, Farmacia.id == Precio.farmacia_id)
        .filter(Precio.medicamento_id == med_id, Precio.fecha_scrape >= desde)
        .order_by(asc(Precio.fecha_scrape))
        .all()
    )

    series = {}
    todos = []
    for precio, fecha, cadena in rows:
        series.setdefault(cadena, []).append(
            {"fecha": fecha.isoformat(), "precio": precio}
        )
        todos.append(precio)

    principio = (
        db.query(PrincipioActivo)
        .filter(PrincipioActivo.id == med.principio_activo_id)
        .first()
    )

    return {
        "medicamento": {
            "id": med.id,
            "nombre_comercial": med.nombre_comercial,
            "laboratorio": med.laboratorio,
            "es_bioequivalente": med.es_bioequivalente or False,
            "principio_activo": principio.nombre if principio else None,
            "dosis": principio.dosis if principio else None,
        },
        "series": series,
        "resumen": _resumen(todos),
        "dias": dias,
    }
