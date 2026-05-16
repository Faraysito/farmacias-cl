from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Medicamento, Precio, Farmacia, PrincipioActivo

router = APIRouter()


@router.get("/historico/{med_id}")
def historico(med_id: int, dias: int = 90, db: Session = Depends(get_db)):
    med = db.query(Medicamento).filter(Medicamento.id == med_id).first()
    if not med:
        raise HTTPException(404, "medicamento no encontrado")

    desde = datetime.utcnow() - timedelta(days=dias)

    rows = (
        db.query(Precio.precio, Precio.fecha_scrape, Farmacia.cadena)
        .join(Farmacia, Farmacia.id == Precio.farmacia_id)
        .filter(Precio.medicamento_id == med_id, Precio.fecha_scrape >= desde)
        .order_by(asc(Precio.fecha_scrape))
        .all()
    )

    # agrupar por cadena
    series = {}
    for precio, fecha, cadena in rows:
        series.setdefault(cadena, []).append({
            "fecha": fecha.isoformat(),
            "precio": precio,
        })

    principio = db.query(PrincipioActivo).filter(
        PrincipioActivo.id == med.principio_activo_id
    ).first()

    return {
        "medicamento": {
            "id": med.id,
            "nombre_comercial": med.nombre_comercial,
            "laboratorio": med.laboratorio,
            "principio_activo": principio.nombre if principio else None,
            "dosis": principio.dosis if principio else None,
        },
        "series": series,
        "dias": dias,
    }