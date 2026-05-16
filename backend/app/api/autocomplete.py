from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.database import get_db
from app.models import Medicamento, PrincipioActivo

router = APIRouter()


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    limit: int = 8,
):
    qlow = f"{q.lower()}%"  # prefijo, no contains, así es más rápido y útil

    principios = (
        db.query(distinct(PrincipioActivo.nombre))
        .filter(func.lower(PrincipioActivo.nombre).like(qlow))
        .order_by(PrincipioActivo.nombre)
        .limit(limit)
        .all()
    )
    nombres = (
        db.query(distinct(Medicamento.nombre_comercial))
        .filter(func.lower(Medicamento.nombre_comercial).like(qlow))
        .order_by(Medicamento.nombre_comercial)
        .limit(limit)
        .all()
    )

    out = []
    seen = set()
    for (n,) in principios:
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append({"valor": n, "tipo": "principio"})
    for (n,) in nombres:
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append({"valor": n, "tipo": "medicamento"})

    return out[:limit]