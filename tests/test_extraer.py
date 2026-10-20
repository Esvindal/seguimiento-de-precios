"""Tests del parser de catalogo (HTML real guardado de books.toscrape.com)."""

from pathlib import Path

import pytest

from scraper.extraer import extraer_libros, precio_a_float, rating_a_numero

BASE = "https://books.toscrape.com/catalogue/"


@pytest.fixture
def html() -> str:
    return (Path(__file__).parent / "fixtures" / "libros.html").read_text(encoding="utf-8")


def test_extrae_los_tres_productos_del_fixture(html):
    libros = extraer_libros(html, BASE)
    assert len(libros) == 3


def test_titulo_precio_disponibilidad_y_url(html):
    libros = extraer_libros(html, BASE)
    primero = libros[0]
    assert primero.titulo == "A Light in the Attic"
    assert primero.precio == pytest.approx(51.77)
    assert primero.disponible is True
    assert primero.rating == 3
    assert primero.url.startswith("https://books.toscrape.com/")
    assert primero.id == "a-light-in-the-attic_1000"


def test_precio_a_float_limpia_simbolos():
    assert precio_a_float("£51.77") == pytest.approx(51.77)
    assert precio_a_float("£1,234.56") == pytest.approx(1234.56)


def test_rating_palabra_a_numero():
    assert rating_a_numero("One") == 1
    assert rating_a_numero("Five") == 5
    assert rating_a_numero("???") == 0


def test_html_sin_productos_devuelve_lista_vacia():
    assert extraer_libros("<html><body>nada</body></html>", BASE) == []
