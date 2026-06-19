"""Tests del normalizador de nombres -> (principio_activo, dosis)."""
import pytest

from app.normalizador import normalizar


@pytest.mark.parametrize(
    "nombre,principio_esperado,dosis_esperada",
    [
        ("Cozaar (R) Losartán 50mg 30 Comprimidos Recubiertos", "losartan", 50),
        ("Losartan (B) 50mg 30 Comprimidos Recubiertos", "losartan", 50),
        ("Losartán Potásico 50 mg", "losartan", 50),
        ("Metformina Clorhidrato 850mg 30 Comprimidos", "metformina clorhidrato", 850),
        ("Paracetamol 500 mg", "paracetamol", 500),
    ],
)
def test_normalizar_casos(nombre, principio_esperado, dosis_esperada):
    principio, dosis = normalizar(nombre)
    assert dosis == dosis_esperada
    assert principio_esperado.split()[0] in principio


def test_normalizar_elimina_marca():
    principio, _ = normalizar("Cozaar Losartán 50mg", marca="Cozaar")
    assert "cozaar" not in principio
    assert "losartan" in principio


def test_normalizar_sin_dosis():
    _, dosis = normalizar("Ibuprofeno Comprimidos")
    assert dosis is None


def test_normalizar_quita_formas_farmaceuticas():
    principio, _ = normalizar("Omeprazol 20mg Cápsulas")
    assert "capsulas" not in principio
    assert "omeprazol" in principio
