"""Reglas de alerta de bajada de precio (reglas/alertas.json).

Regla soportada:
    {"tipo": "bajada_porcentaje", "producto": "*" | "<id>", "umbral": <pct>}
Dispara cuando el ultimo precio bajo mas de ``umbral``% respecto del punto
anterior. Las reglas son datos, no codigo: se editan en reglas/alertas.json.
"""


def evaluar_alertas(historial: dict, reglas: list[dict]) -> list[dict]:
    alertas: list[dict] = []
    for regla in reglas:
        if regla.get("tipo") != "bajada_porcentaje":
            continue
        umbral = float(regla.get("umbral", 0))
        for id_prod, prod in historial.get("productos", {}).items():
            if regla.get("producto", "*") not in ("*", id_prod):
                continue
            puntos = prod.get("precios", [])
            if len(puntos) < 2:
                continue
            anterior, actual = puntos[-2]["precio"], puntos[-1]["precio"]
            if anterior <= 0:
                continue
            bajada = (anterior - actual) / anterior * 100
            if bajada >= umbral:
                alertas.append(
                    {
                        "producto": id_prod,
                        "titulo": prod.get("titulo", id_prod),
                        "precio_anterior": anterior,
                        "precio_actual": actual,
                        "bajada_pct": round(bajada, 1),
                        "umbral": umbral,
                        "ts": puntos[-1]["ts"],
                    }
                )
    return alertas
