"""Descarga respetuosa: UA identificable, ritmo lento y chequeo de robots.txt."""

import time
import urllib.robotparser
from collections.abc import Callable, Iterator
from urllib.parse import urljoin, urlparse

import httpx

# UA identificable: dice que es, de que proyecto viene y donde leerlo.
USER_AGENT = (
    "seguimiento-de-precios-demo/0.1 "
    "(+https://github.com/USUARIO/seguimiento-de-precios; scraper educativo)"
)


def permite_robots(url: str, cliente: httpx.Client) -> bool:
    """True si robots.txt permite la URL (o no existe robots.txt)."""
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    robots_url = urljoin(base, "/robots.txt")
    robots = urllib.robotparser.RobotFileParser(robots_url)
    try:
        resp = cliente.get(robots_url)
    except httpx.HTTPError:
        return True  # sin robots.txt accesible, se asume permitido
    if resp.status_code >= 400:
        return True
    robots.parse(resp.text.splitlines())
    return robots.can_fetch(USER_AGENT, url)


def descargar_paginas(
    base_url: str,
    paginas: int,
    demora: float = 2.0,
    dormir: Callable[[float], None] = time.sleep,
    cliente: httpx.Client | None = None,
) -> Iterator[tuple[str, str]]:
    """Itera (url, html) de las primeras ``paginas`` del catalogo.

    Espera ``demora`` segundos entre pedidos para no cargar el sitio.
    """
    cli = cliente or httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30
    )
    for n in range(1, paginas + 1):
        url = base_url if n == 1 else urljoin(base_url, f"catalogue/page-{n}.html")
        resp = cli.get(url)
        resp.raise_for_status()
        yield url, resp.text
        if n < paginas:
            dormir(demora)
