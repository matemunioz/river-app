"""
destacados.py — Jugador destacado de cada división en una jornada.

Usa la metodología de candidatura del proyecto de análisis (Sports Data Campus):
métricas normalizadas por 90 minutos y evaluadas con z-score contra un grupo de
referencia, promediando los z para un score único.

La diferencia con aquel: allá el benchmark es (división, posición) sobre toda la
temporada, para decidir ascensos. Acá la pregunta es otra —"¿quién se destacó
ESTE fin de semana?"— así que el grupo de referencia son los compañeros de ese
mismo partido. Es más barato y responde justo eso.
"""

import statistics

import parser as sc
import biblioteca as bib

# Métrica → cómo se llama en las estadísticas individuales de la app.
# Son las 8 de _CAND_METRICS del proyecto; "POSITIVO" no existe como tal acá y
# se reemplaza por pases clave, que mide lo mismo (acción que genera peligro).
METRICAS = [
    ("Goles", "goles"),
    ("Remates", "remates_total"),
    ("Toques en área", "toques_area"),
    ("Duelos of. ganados", "dao_plus"),
    ("Pases completos", "pases_completos"),
    ("Pases filtrados", "pases_filtrado"),
    ("Regates", "regate_c"),
    ("Pases clave", "pases_clave"),
]

MIN_MINUTOS = 45          # menos que eso no es una actuación comparable
MIN_JUGADORES = 5         # sin grupo no hay z-score que valga


def _por90(valor, minutos):
    if not minutos or minutos <= 0:
        return 0.0
    return (float(valor or 0) / float(minutos)) * 90.0


def destacado_de_partido(pid: str) -> dict | None:
    """El jugador que más se destacó en un partido, con por qué."""
    try:
        df = bib.leer_df(pid)
    except Exception:
        return None

    jugadores = sc.detectar_jugadores(df)
    if not jugadores:
        return None

    filas = []
    for j in jugadores:
        st = sc.estadisticas_individuales(df, j)
        if not st:
            continue
        min_j = float(st.get("minutos") or 0)
        if min_j < MIN_MINUTOS:
            continue
        filas.append({
            "jugador": j,
            "minutos": round(min_j, 1),
            "stats": st,
            "p90": {campo: _por90(st.get(campo), min_j) for _, campo in METRICAS},
        })

    if len(filas) < MIN_JUGADORES:
        return None

    # z-score de cada métrica contra los compañeros de ese partido
    for _, campo in METRICAS:
        vals = [f["p90"][campo] for f in filas]
        media = statistics.fmean(vals)
        desvio = statistics.pstdev(vals)
        for f in filas:
            f.setdefault("z", {})[campo] = (
                (f["p90"][campo] - media) / desvio if desvio > 0 else 0.0
            )

    for f in filas:
        f["score"] = statistics.fmean(f["z"].values())

    mejor = max(filas, key=lambda f: f["score"])

    # Las tres métricas en las que más se despegó del resto, para explicar el por qué
    top = sorted(METRICAS, key=lambda m: mejor["z"][m[1]], reverse=True)[:3]
    razones = [
        {"label": label, "valor": mejor["stats"].get(campo) or 0, "z": round(mejor["z"][campo], 2)}
        for label, campo in top
        if mejor["z"][campo] > 0.4 and (mejor["stats"].get(campo) or 0) > 0
    ]

    st = mejor["stats"]
    return {
        "jugador": mejor["jugador"],
        "minutos": mejor["minutos"],
        "score": round(mejor["score"], 2),
        "goles": st.get("goles") or 0,
        "asistencias": st.get("asistencias") or 0,
        "razones": razones,
        "de": len(filas),
    }


def de_la_jornada(fecha: int | None = None) -> dict:
    """Un destacado por división, de la última jornada con datos (o la pedida)."""
    inv = bib.listar()
    if not inv["disponible"]:
        return {"disponible": False, "destacados": []}

    import fixture as fx

    # Fecha de fixture de cada partido cargado
    porDiv: dict[str, list[tuple[int, dict]]] = {}
    for p in inv["partidos"]:
        f = fx.fecha_de_rival(p["rival"])
        if f and p["division"]:
            porDiv.setdefault(p["division"], []).append((f, p))

    objetivo = fecha
    if objetivo is None:
        objetivo = max((f for lista in porDiv.values() for f, _ in lista), default=None)
    if objetivo is None:
        return {"disponible": False, "destacados": []}

    out = []
    for div, lista in porDiv.items():
        # El partido de la jornada objetivo. Si esa división todavía no la
        # cargó, se muestra el último que sí tiene: es preferible mostrar su
        # último destacado (avisando de qué fecha es) que dejar el hueco.
        cand = [(f, p) for f, p in lista if f == objetivo]
        if not cand:
            cand = [max(lista, key=lambda x: x[0])]
        f_usada, partido = cand[0]
        d = destacado_de_partido(partido["id"])
        if d:
            out.append({
                **d,
                "division": div,
                "rival": partido["rival"],
                "fecha": f_usada,
                "es_ultima_jornada": f_usada == objetivo,
            })

    orden = {d: i for i, d in enumerate(["4ta", "5ta", "6ta", "7ma", "8va", "9na"])}
    out.sort(key=lambda x: orden.get(x["division"], 99))
    return {"disponible": True, "fecha": objetivo, "destacados": out}
