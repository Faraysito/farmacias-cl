from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from collections import defaultdict
from app.database import get_db, SessionLocal
from app.models import Medicamento, Precio, Farmacia, PrincipioActivo
from app.schemas import GrupoResponse, MedicamentoEnGrupo, PrecioResponse
from app.scrape_orchestrator import scrape_todas

router = APIRouter()

UMBRAL_PRODUCTOS_MIN = 3  # bajo esto, dispara scrape on-demand


@router.get("/buscar", response_model=list[GrupoResponse])
async def buscar_medicamentos(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """Busca y agrupa por (principio_activo, dosis). Scrapea on-demand si hay pocos datos."""
    grupos = _buscar_en_db(db, q)

    total_productos = sum(g.cantidad_medicamentos for g in grupos)
    print(f"[buscar] q='{q}' productos_en_db={total_productos}")
    
    if total_productos < UMBRAL_PRODUCTOS_MIN:
        print(f"[buscar] disparando scrape on-demand para '{q}'")
        try:
            resumen = await scrape_todas(q)
            print(f"[buscar] scrape terminado: {resumen}")
        except Exception as e:
            print(f"[buscar] scrape falló: {type(e).__name__}: {e}")
        
        db_fresh = SessionLocal()
        try:
            grupos = _buscar_en_db(db_fresh, q)
        finally:
            db_fresh.close()
        print(f"[buscar] después de scrape: {len(grupos)} grupos")

    return grupos


def _buscar_en_db(db: Session, q: str) -> list[GrupoResponse]:
    query_lower = f"%{q.lower()}%"
    medicamentos = (
        db.query(Medicamento)
        .options(joinedload(Medicamento.principio_activo))
        .outerjoin(PrincipioActivo)
        .filter(
            func.lower(Medicamento.nombre_comercial).like(query_lower)
            | func.lower(PrincipioActivo.nombre).like(query_lower)
        )
        .all()
    )
    if not medicamentos:
        return []

    grupos: dict[tuple, list[MedicamentoEnGrupo]] = defaultdict(list)
    for med in medicamentos:
        if not med.principio_activo or not med.principio_activo.nombre.strip():
            continue
        principio = med.principio_activo.nombre.strip()
        dosis = med.principio_activo.dosis
        key = (principio, dosis)

        precios_raw = (
            db.query(Precio, Farmacia)
            .join(Farmacia, Farmacia.id == Precio.farmacia_id)
            .filter(Precio.medicamento_id == med.id)
            .order_by(desc(Precio.fecha_scrape))
            .all()
        )
        vistos = set()
        precios = []
        for precio, farmacia in precios_raw:
            if farmacia.cadena in vistos:
                continue
            vistos.add(farmacia.cadena)
            precios.append(PrecioResponse(
                cadena=farmacia.cadena,
                precio=precio.precio,
                stock=precio.stock or False,
                fecha_scrape=precio.fecha_scrape,
            ))
        if not precios:
            continue

        grupos[key].append(MedicamentoEnGrupo(
            id=med.id,
            nombre_comercial=med.nombre_comercial,
            laboratorio=med.laboratorio,
            es_bioequivalente=med.es_bioequivalente or False,
            precios=precios,
        ))

    resultado = []
    for (principio, dosis), meds in grupos.items():
        meds.sort(key=lambda m: min((p.precio for p in m.precios), default=float('inf')))
        precio_min = min(
            (p.precio for m in meds for p in m.precios),
            default=float('inf'),
        )
        resultado.append((precio_min, GrupoResponse(
            principio_activo=principio,
            dosis=dosis,
            cantidad_medicamentos=len(meds),
            medicamentos=meds,
        )))
    resultado.sort(key=lambda x: x[0])
    return [g for _, g in resultado]