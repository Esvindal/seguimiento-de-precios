"""Tests del historial de precios (merge solo cuando cambia algo)."""

from scraper.extraer import Libro
from scraper.historial import actualizar_historial, historial_vacio


def libro(id="libro-1", precio=10.0, disponible=True) -> Libro:
    return Libro(
        id=id,
        titulo="Libro " + id,
        precio=precio,
        disponible=disponible,
        rating=3,
        url="https://ejemplo.test/" + id,
    )


def test_primera_corrida_registra_punto_inicial():
    hist = historial_vacio()
    nuevo, cambio = actualizar_historial(hist, [libro()], "2026-10-20T00:00:00Z")

    assert cambio is True
    assert len(nuevo["productos"]["libro-1"]["precios"]) == 1
    assert nuevo["productos"]["libro-1"]["precios"][0]["precio"] == 10.0


def test_mismo_precio_no_agrega_punto_ni_marca_cambio():
    hist = historial_vacio()
    hist, _ = actualizar_historial(hist, [libro()], "2026-10-20T00:00:00Z")
    nuevo, cambio = actualizar_historial(hist, [libro()], "2026-10-20T06:00:00Z")

    assert cambio is False
    assert len(nuevo["productos"]["libro-1"]["precios"]) == 1


def test_bajada_de_precio_agrega_punto_y_marca_cambio():
    hist = historial_vacio()
    hist, _ = actualizar_historial(hist, [libro()], "2026-10-20T00:00:00Z")
    nuevo, cambio = actualizar_historial(hist, [libro(precio=8.0)], "2026-10-20T06:00:00Z")

    assert cambio is True
    puntos = nuevo["productos"]["libro-1"]["precios"]
    assert [p["precio"] for p in puntos] == [10.0, 8.0]


def test_cambio_de_disponibilidad_tambien_registra():
    hist = historial_vacio()
    hist, _ = actualizar_historial(hist, [libro()], "2026-10-20T00:00:00Z")
    nuevo, cambio = actualizar_historial(
        hist, [libro(disponible=False)], "2026-10-20T06:00:00Z"
    )

    assert cambio is True
    assert nuevo["productos"]["libro-1"]["precios"][-1]["disponible"] is False
