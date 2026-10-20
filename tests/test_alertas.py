"""Tests de las reglas de alerta de bajada de precio."""

from scraper.alertas import evaluar_alertas


def historial_con_precios(precios):
    return {
        "productos": {
            "libro-1": {
                "titulo": "Libro 1",
                "precios": [
                    {"ts": f"2026-10-{10 + i}T00:00:00Z", "precio": p, "disponible": True}
                    for i, p in enumerate(precios)
                ],
            }
        }
    }


def test_bajada_mayor_al_umbral_dispara_alerta():
    hist = historial_con_precios([100.0, 89.0])  # -11%
    reglas = [{"tipo": "bajada_porcentaje", "producto": "*", "umbral": 10}]

    alertas = evaluar_alertas(hist, reglas)

    assert len(alertas) == 1
    assert alertas[0]["producto"] == "libro-1"
    assert alertas[0]["precio_anterior"] == 100.0
    assert alertas[0]["precio_actual"] == 89.0


def test_bajada_menor_al_umbral_no_dispara():
    hist = historial_con_precios([100.0, 95.0])  # -5%
    reglas = [{"tipo": "bajada_porcentaje", "producto": "*", "umbral": 10}]
    assert evaluar_alertas(hist, reglas) == []


def test_subida_de_precio_no_es_alerta():
    hist = historial_con_precios([100.0, 120.0])
    reglas = [{"tipo": "bajada_porcentaje", "producto": "*", "umbral": 10}]
    assert evaluar_alertas(hist, reglas) == []


def test_regla_por_producto_solo_aplica_a_ese():
    hist = historial_con_precios([100.0, 80.0])
    reglas = [{"tipo": "bajada_porcentaje", "producto": "otro-libro", "umbral": 10}]
    assert evaluar_alertas(hist, reglas) == []


def test_producto_con_un_solo_punto_no_evalua():
    hist = historial_con_precios([100.0])
    reglas = [{"tipo": "bajada_porcentaje", "producto": "*", "umbral": 10}]
    assert evaluar_alertas(hist, reglas) == []
