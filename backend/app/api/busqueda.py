from collections import defaultdict

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal, get_db
from app.models import Farmacia, Medicamento, Precio, PrincipioActivo
from app.ratelimit import limiter
from app.config import RATE_LIMIT_BUSCAR
from app.schemas import (
    BusquedaResponse,
    GrupoResponse,
    MedicamentoEnGrupo,
    PrecioResponse,
)
from app.scrape_orchestrator import scrape_todas

router = APIRouter()

UMBRAL_PRODUCTOS_MIN = 3


@router.get("/buscar", response_model=BusquedaResponse)
@limiter.limit(RATE_LIMIT_BUSCAR)
async def buscar_medicamentos(
    request: Request,
    q: str = Query(..., min_length=2),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
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

    total = len(grupos)
    inicio = (pagina - 1) * por_pagina
    pagina_grupos = grupos[inicio : inicio + por_pagina]

    return BusquedaResponse(
        query=q,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        grupos=pagina_grupos,
    )


def _buscar_en_db(db: Session, q: str) -> list[GrupoResponse]:
    qlow = f"%{q.lower()}%"
    medicamentos = (
        db.query(Medicamento)
        .options(joinedload(Medicamento.principio_activo))
        .outerjoin(PrincipioActivo)
        .filter(
            func.lower(Medicamento.nombre_comercial).like(qlow)
            | func.lower(PrincipioActivo.nombre).like(qlow)
        )
        .all()
    )
    if not medicamentos:
        return []

    grupos = defaultdict(list)
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
            precios.append(
                PrecioResponse(
                    cadena=farmacia.cadena,
                    precio=precio.precio,
                    stock=precio.stock or False,
                    fecha_scrape=precio.fecha_scrape,
                    url=precio.url,
                )
            )
        if not precios:
            continue

        grupos[key].append(
            MedicamentoEnGrupo(
                id=med.id,
                nombre_comercial=med.nombre_comercial,
                laboratorio=med.laboratorio,
                es_bioequivalente=med.es_bioequivalente or False,
                precios=precios,
            )
        )

    resultado = []
    for (principio, dosis), meds in grupos.items():
        meds.sort(key=lambda m: min((p.precio for p in m.precios), default=float("inf")))
        todos_precios = [p.precio for m in meds for p in m.precios]
        fechas = [p.fecha_scrape for m in meds for p in m.precios]
        precio_min = min(todos_precios) if todos_precios else None
        precio_max = max(todos_precios) if todos_precios else None

        ahorro_abs = ahorro_pct = None
        if precio_min is not None and precio_max is not None and precio_max > 0:
            ahorro_abs = round(precio_max - precio_min, 0)
            ahorro_pct = round((1 - precio_min / precio_max) * 100, 1)

        resultado.append(
            (
                precio_min if precio_min is not None else float("inf"),
                GrupoResponse(
                    principio_activo=principio,
                    dosis=dosis,
                    cantidad_medicamentos=len(meds),
                    precio_min=precio_min,
                    precio_max=precio_max,
                    ahorro_abs=ahorro_abs,
                    ahorro_pct=ahorro_pct,
                    actualizado=max(fechas) if fechas else None,
                    medicamentos=meds,
                ),
            )
        )
    resultado.sort(key=lambda x: x[0])
    return [g for _, g in resultado]
