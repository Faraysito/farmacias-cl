"""Alertas de precio por email. Envío vía Resend (opcional)."""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import ALERTAS_FROM_EMAIL, RESEND_API_KEY
from app.database import get_db
from app.models import AlertaPrecio, Medicamento, Precio, utcnow
from app.schemas import AlertaCrear, AlertaResponse

router = APIRouter()


@router.post("/alertas", response_model=AlertaResponse, status_code=201)
def crear_alerta(data: AlertaCrear, db: Session = Depends(get_db)):
    """Crea una alerta. Si el precio ya está bajo el objetivo, notifica al instante."""
    med = db.query(Medicamento).filter(Medicamento.id == data.medicamento_id).first()
    if not med:
        raise HTTPException(404, "medicamento no encontrado")

    alerta = AlertaPrecio(
        email=str(data.email),
        medicamento_id=data.medicamento_id,
        precio_objetivo=data.precio_objetivo,
        activa=True,
    )
    db.add(alerta)
    db.commit()
    db.refresh(alerta)

    # Si ya hay un precio actual por debajo del objetivo, avisar de inmediato.
    mejor = (
        db.query(Precio)
        .filter(Precio.medicamento_id == data.medicamento_id)
        .order_by(Precio.precio.asc())
        .first()
    )
    if mejor and mejor.precio <= data.precio_objetivo:
        _enviar_email(
            alerta.email,
            f"{med.nombre_comercial} ya está a ${int(mejor.precio):,}".replace(",", "."),
            f"El precio bajó a ${int(mejor.precio):,} (tu objetivo: "
            f"${int(data.precio_objetivo):,}).".replace(",", "."),
        )
        alerta.ultima_notificacion = utcnow()
        db.commit()

    return alerta


@router.delete("/alertas/{alerta_id}", status_code=204)
def borrar_alerta(alerta_id: int, db: Session = Depends(get_db)):
    alerta = db.query(AlertaPrecio).filter(AlertaPrecio.id == alerta_id).first()
    if not alerta:
        raise HTTPException(404, "alerta no encontrada")
    alerta.activa = False  # baja lógica; no se borra el histórico
    db.commit()
    return None


def _enviar_email(to: str, asunto: str, cuerpo: str) -> bool:
    """Envía con Resend si hay API key; si no, lo registra y sigue (modo dev)."""
    if not RESEND_API_KEY:
        print(f"[alertas] (sin RESEND_API_KEY) email a {to}: {asunto}")
        return False
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": ALERTAS_FROM_EMAIL,
                "to": [to],
                "subject": asunto,
                "text": cuerpo,
            },
            timeout=10,
        )
        return True
    except Exception as e:
        print(f"[alertas] error enviando email: {e}")
        return False
