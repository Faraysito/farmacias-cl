import asyncio
import secrets

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from app.config import ADMIN_TOKEN
from app.scrape_orchestrator import scrape_todas

router = APIRouter()

TOP_MEDICAMENTOS = [
    "losartan", "metformina", "atorvastatina", "paracetamol",
    "ibuprofeno", "omeprazol", "enalapril", "amoxicilina",
    "sertralina", "aspirina", "diclofenaco", "ranitidina",
]


def _verificar_token(token: str | None) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(500, "ADMIN_TOKEN no configurado en el server")
    # Comparación en tiempo constante para no filtrar el token por timing.
    if not token or not secrets.compare_digest(token, ADMIN_TOKEN):
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


async def _correr_scrapes() -> None:
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
