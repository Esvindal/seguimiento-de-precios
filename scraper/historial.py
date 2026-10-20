"""Historial de precios en data/precios.json.

Estructura:
{
  "fuente": "https://books.toscrape.com",
  "aviso": "...",
  "actualizado_en": "<iso>",
  "productos": {
    "<id>": {"titulo": ..., "url": ..., "precios": [{ts, precio, disponible}]}
  }
}
"""

from .extraer import Libro

FUENTE = "https://books.toscrape.com"
AVISO = (
    "Datos de books.toscrape.com, sitio publicado para practicar scraping. "
    "Los precios son ficticios y pueden no cambiar entre corridas."
)


def historial_vacio() -> dict:
    return {"fuente": FUENTE, "aviso": AVISO, "actualizado_en": "", "productos": {}}


def actualizar_historial(historial: dict, libros: list[Libro], ts: str) -> tuple[dict, bool]:
    """Agrega un punto de precio por producto solo si algo cambio.

    Devuelve (historial_actualizado, cambio): ``cambio`` es True cuando se
    agrego al menos un punto nuevo (precio o disponibilidad distintos, o
    producto nuevo), que es lo que dispara el commit en GitHub Actions.
    """
    historial.setdefault("productos", {})
    cambio = False
    for libro in libros:
        prod = historial["productos"].setdefault(
            libro.id, {"titulo": libro.titulo, "url": libro.url, "precios": []}
        )
        prod["titulo"] = libro.titulo
        prod["url"] = libro.url
        ultimo = prod["precios"][-1] if prod["precios"] else None
        if (
            ultimo is None
            or ultimo["precio"] != libro.precio
            or ultimo["disponible"] != libro.disponible
        ):
            prod["precios"].append(
                {"ts": ts, "precio": libro.precio, "disponible": libro.disponible}
            )
            cambio = True
    if cambio:
        historial["actualizado_en"] = ts
    return historial, cambio
