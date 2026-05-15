from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Medicamento, Precio, Farmacia, PrincipioActivo
from app.schemas import MedicamentoResponse, PrecioResponse

router = APIRouter()


@router.get("/buscar", response_model=list[MedicamentoResponse])
def buscar_medicamentos(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    db: Session = Depends(get_db),
):
    """
    Busca medicamentos por nombre comercial o principio activo.
    Devuelve cada medicamento con su último precio por cadena.
    """
    # 1. Buscar medicamentos cuyo nombre o principio activo matchee
    query_lower = f"%{q.lower()}%"
    medicamentos = (
        db.query(Medicamento)
        .options(joinedload(Medicamento.principio_activo))
        .outerjoin(PrincipioActivo)
        .filter(
            func.lower(Medicamento.nombre_comercial).like(query_lower)
            | func.lower(PrincipioActivo.nombre).like(query_lower)
        )
        .limit(50)
        .all()
    )

    if not medicamentos:
        return []

    # 2. Para cada medicamento, traer el último precio por farmacia
    resultado = []
    for med in medicamentos:
        # Subquery: último precio por farmacia para este medicamento
        ultimos_precios = (
            db.query(Precio, Farmacia)
            .join(Farmacia, Farmacia.id == Precio.farmacia_id)
            .filter(Precio.medicamento_id == med.id)
            .order_by(desc(Precio.fecha_scrape))
            .all()
        )

        # Quedarse con el más reciente por farmacia
        vistos = set()
        precios_unicos = []
        for precio, farmacia in ultimos_precios:
            if farmacia.id in vistos:
                continue
            vistos.add(farmacia.id)
            precios_unicos.append(PrecioResponse(
                cadena=farmacia.cadena,
                precio=precio.precio,
                stock=precio.stock or False,
                fecha_scrape=precio.fecha_scrape,
            ))

        resultado.append(MedicamentoResponse(
            id=med.id,
            nombre_comercial=med.nombre_comercial,
            laboratorio=med.laboratorio,
            es_bioequivalente=med.es_bioequivalente or False,
            principio_activo=med.principio_activo.nombre if med.principio_activo else None,
            dosis=med.principio_activo.dosis if med.principio_activo else None,
            precios=precios_unicos,
        ))

    # 3. Ordenar por precio mínimo ascendente
    resultado.sort(key=lambda m: min((p.precio for p in m.precios), default=float('inf')))
    return resultado