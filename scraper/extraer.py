"""Parser del catalogo de books.toscrape.com (estructura: article.product_pod)."""

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass(frozen=True)
class Libro:
    id: str
    titulo: str
    precio: float
    disponible: bool
    rating: int
    url: str


def precio_a_float(texto: str) -> float:
    """'£1,234.56' -> 1234.56. Los simbolos de moneda se descartan."""
    limpio = re.sub(r"[^\d.,]", "", texto).replace(",", "")
    return float(limpio)


def rating_a_numero(palabra: str) -> int:
    return _RATINGS.get(palabra, 0)


def _id_desde_url(href: str) -> str:
    # 'a-light-in-the-attic_1000/index.html' -> 'a-light-in-the-attic_1000'
    partes = href.strip("/").split("/")
    return partes[-2] if "/index.html" in href else partes[-1]


def extraer_libros(html: str, base_url: str) -> list[Libro]:
    """Extrae los productos de una pagina de catalogo."""
    sopa = BeautifulSoup(html, "html.parser")
    libros: list[Libro] = []
    for articulo in sopa.select("article.product_pod"):
        enlace = articulo.select_one("h3 a")
        precio_el = articulo.select_one("p.price_color")
        if not enlace or not precio_el:
            continue
        href = str(enlace.get("href", ""))
        rating_el = articulo.select_one("p.star-rating")
        clases = list(rating_el.get("class") or []) if rating_el else []
        rating = next((rating_a_numero(c) for c in clases if c in _RATINGS), 0)
        stock = articulo.select_one("p.availability")
        libros.append(
            Libro(
                id=_id_desde_url(href),
                titulo=str(enlace.get("title") or enlace.get_text(strip=True)),
                precio=precio_a_float(precio_el.get_text(strip=True)),
                disponible=bool(stock and "instock" in (stock.get("class") or [])),
                rating=rating,
                url=urljoin(base_url, href),
            )
        )
    return libros
