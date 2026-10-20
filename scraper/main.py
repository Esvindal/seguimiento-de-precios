"""Orquesta: robots -> descarga -> parseo -> merge -> guarda solo si cambio.

Uso: python -m scraper.main --paginas 3 --salida data/precios.json
Codigo de salida: 0 siempre; imprime "CAMBIO" si el archivo se modifico
(el workflow lo usa para decidir el commit).
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .alertas import evaluar_alertas
from .descargar import USER_AGENT, descargar_paginas, permite_robots
from .extraer import extraer_libros
from .historial import FUENTE, actualizar_historial, historial_vacio

log = logging.getLogger(__name__)


def correr(
    paginas: int, salida: Path, demora: float, reglas: Path, espejo_docs: Path | None
) -> bool:
    cliente = httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30
    )
    if not permite_robots(FUENTE, cliente):
        log.error("robots.txt no permite descargar %s; se aborta", FUENTE)
        return False

    libros = []
    for url, html in descargar_paginas(FUENTE, paginas, demora=demora, cliente=cliente):
        hallados = extraer_libros(html, url)
        log.info("%s -> %d productos", url, len(hallados))
        libros.extend(hallados)

    if salida.exists():
        historial = json.loads(salida.read_text(encoding="utf-8"))
    else:
        historial = historial_vacio()

    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    historial, cambio = actualizar_historial(historial, libros, ts)

    if cambio:
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(
            json.dumps(historial, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("CAMBIO: precios.json actualizado")
    else:
        print("SIN CAMBIOS: no se toca el archivo")

    if espejo_docs is not None:
        espejo_docs.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(salida, espejo_docs / "precios.json")
        reglas_datos = json.loads(reglas.read_text(encoding="utf-8"))
        evaluadas = evaluar_alertas(historial, reglas_datos)
        (espejo_docs / "alertas-evaluadas.json").write_text(
            json.dumps({"evaluadas_en": ts, "alertas": evaluadas}, ensure_ascii=False,
                       indent=2),
            encoding="utf-8",
        )
        log.info("espejo docs/: %d productos, %d alertas", len(historial["productos"]),
                 len(evaluadas))
    return True


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="scraper")
    parser.add_argument("--paginas", type=int, default=3)
    parser.add_argument("--salida", type=Path, default=Path("data/precios.json"))
    parser.add_argument("--demora", type=float, default=2.0, help="seg entre pedidos")
    parser.add_argument("--reglas", type=Path, default=Path("reglas/alertas.json"))
    parser.add_argument(
        "--espejo-docs",
        type=Path,
        default=Path("docs/data"),
        help="carpeta del sitio donde copiar precios.json y las alertas evaluadas",
    )
    args = parser.parse_args(argv)
    return (
        0
        if correr(args.paginas, args.salida, args.demora, args.reglas, args.espejo_docs)
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
