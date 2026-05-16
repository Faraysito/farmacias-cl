import os
import asyncio
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from app.scrape_orchestrator import scrape_todas

router = APIRouter()

TOP_MEDICAMENTOS = [
    "losartan", "metformina", "atorvastatina", "paracetamol",
    "ibuprofeno", "omeprazol", "enalapril", "amoxicilina",
    "sertralina", "aspirina", "diclofenaco", "ranitidina",
]


def _verificar_token(token: str | None):
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(500, "ADMIN_TOKEN no configurado en el server")
    if token != expected:
        raise HTTPException(401, "token inválido")


@router.post("/admin/scrape-top")
async def scrape_top(
    background: BackgroundTasks,
    x_admin_token: str | None = Header(default=None),
):
    """Endpoint para el cron de GitHub Actions. Dispara scrape en background."""
    _verificar_token(x_admin_token)
    background.add_task(_correr_scrapes)
    return {"ok": True, "encolados": len(TOP_MEDICAMENTOS)}


async def _correr_scrapes():
    resumen_total = {}
    for med in TOP_MEDICAMENTOS:
        try:
            r = await scrape_todas(med)
            resumen_total[med] = r
            print(f"[cron] {med}: {r}")
        except Exception as e:
            print(f"[cron] {med} falló: {e}")
        await asyncio.sleep(1)  # respiro entre cadenas
    print(f"[cron] terminado: {resumen_total}")