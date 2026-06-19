"""Tests de los schemas Pydantic (validación de entrada de alertas)."""
import pytest
from pydantic import ValidationError

from app.schemas import AlertaCrear, GrupoResponse


def test_alerta_email_invalido():
    with pytest.raises(ValidationError):
        AlertaCrear(email="no-es-email", medicamento_id=1, precio_objetivo=1000)


def test_alerta_precio_no_positivo():
    with pytest.raises(ValidationError):
        AlertaCrear(email="a@b.cl", medicamento_id=1, precio_objetivo=0)


def test_alerta_valida():
    a = AlertaCrear(email="a@b.cl", medicamento_id=1, precio_objetivo=1500)
    assert a.precio_objetivo == 1500


def test_grupo_response_ahorro_opcional():
    g = GrupoResponse(
        principio_activo="losartan",
        dosis="50mg",
        cantidad_medicamentos=2,
        medicamentos=[],
    )
    assert g.ahorro_abs is None
