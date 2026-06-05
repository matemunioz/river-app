"""
gen_baremos.py — Genera baremos (escala de referencia p10/p90 por métrica) a partir
del histórico completo de las formativas (todos_los_partidos-2.csv, 6 divisiones).

Salida: static/baremos.json — usado por el radar individual para escalar cada eje
cuando el CSV subido tiene un solo jugador (sin plantel con quien comparar).

Uso: .venv_mac/bin/python gen_baremos.py
"""
import json
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
import parser as sc

HIST = "/Users/usuario/Desktop/RIVER/Activos/testeo-softwares/Software/todos_los_partidos-2.csv"
OUT = "static/baremos.json"
MIN_INTERV = 10  # descartar jugador-partidos con muy pocas acciones (ruido)

# Mapeo de la columna "Posición" del histórico a línea def/med/atk
POS_A_LINEA = {
    "Defensor": "def",
    "Defensor Lateral": "def",
    "Mediocampista": "med",
    "Delantero": "atk",
}

# Métricas que exponemos para el radar (todas las numéricas útiles del parser)
METRICAS = [
    "pases_total", "pases_completos", "pases_efect", "pases_adelante", "pases_atras",
    "pases_lateral", "pases_largo_c", "pases_filtrado", "pases_clave", "apoyos",
    "centros_c", "centros_i",
    "remates_arco", "remates_gol", "remates_afuera", "remates_bloq", "remates_total", "remates_efect",
    "goles", "asistencias",
    "dao_plus", "dao_minus", "dad_plus", "dad_minus",
    "aereo_og", "aereo_op", "aereo_dg", "aereo_dp",
    "regate_c", "regate_i",
    "recup_posic", "recup_interv", "recup_tras", "recup_total",
    "perd_pase", "perd_control", "perd_gambeta", "perd_total",
    "interv_entrada_g", "intercepciones", "bloqueos",
    "toques_area", "recep_lineas", "recep_espal", "recep_espacio", "ruptura",
    "despeje_or", "despeje_no", "faltas_rec", "faltas_hec",
    "pct_ultimo_tercio", "pct_area", "progresion_media", "distancia_media", "pct_progresivo",
]


def main():
    print(f"Cargando histórico: {HIST}")
    raw = pd.read_csv(HIST, low_memory=False)
    print(f"  {len(raw)} filas · {raw['Timeline'].nunique()} partidos")

    # Posición por jugador (tomamos la más frecuente por jugador)
    pos_por_jug = (
        raw.dropna(subset=["Jugador", "Posición"])
        .groupby("Jugador")["Posición"]
        .agg(lambda s: s.astype(str).str.strip().mode().iloc[0])
        .to_dict()
    )

    registros = []  # cada item: dict de stats + linea
    for timeline, sub in raw.groupby("Timeline"):
        df = sub.copy()
        # Adaptar al formato que espera el parser: Row = Jugador
        df["Row"] = df["Jugador"]
        df = sc.enriquecer_df(df)
        jugadores = [j for j in df["Row"].dropna().unique() if isinstance(j, str)]
        for jug in jugadores:
            st = sc.estadisticas_individuales(df, jug)
            if not st or (st.get("intervenciones", 0) < MIN_INTERV):
                continue
            pos = str(pos_por_jug.get(jug, "")).strip()
            st["__linea"] = POS_A_LINEA.get(pos, None)
            registros.append(st)

    print(f"  {len(registros)} jugador-partidos válidos (≥{MIN_INTERV} interv.)")

    def percentiles(valores):
        arr = np.array([v for v in valores if v is not None], dtype=float)
        if len(arr) < 5:
            return None
        return {
            "p10": round(float(np.percentile(arr, 10)), 2),
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "min": round(float(arr.min()), 2),
            "max": round(float(arr.max()), 2),
            "n": len(arr),
        }

    def baremo_de(regs):
        out = {}
        for m in METRICAS:
            vals = [r.get(m, 0) or 0 for r in regs]
            p = percentiles(vals)
            if p:
                out[m] = p
        return out

    # Division por jugador-partido: para cada registro, guardamos también la división
    # del partido. Usamos la columna 'División' del histórico (cuarta, quinta, ..., novena).
    # Re-mapeamos: ya viene capturada arriba a través de partido_de(); ahora la sacamos del df.
    # Para simplicidad: cada registro ya tiene la división porque el partido del histórico
    # tiene una única división (todos los jugadores de un partido son de la misma).
    # La asignamos en el loop principal — adaptamos abajo.

    # Re-procesar agregando división por registro (necesitamos el df por partido)
    registros_por_division = {d: [] for d in ["cuarta", "quinta", "sexta", "séptima", "octava", "novena"]}
    # Cargamos de nuevo el mapeo timeline → división
    div_por_timeline = (
        raw.dropna(subset=["Timeline", "División"])
        .groupby("Timeline")["División"]
        .agg(lambda s: s.astype(str).str.strip().mode().iloc[0])
        .to_dict()
    )
    # Re-correr el loop con tracking de división — eficiencia importa menos que claridad
    for timeline, sub in raw.groupby("Timeline"):
        divis = div_por_timeline.get(timeline, "")
        if divis not in registros_por_division:
            continue
        df = sub.copy()
        df["Row"] = df["Jugador"]
        df = sc.enriquecer_df(df)
        for jug in [j for j in df["Row"].dropna().unique() if isinstance(j, str)]:
            st = sc.estadisticas_individuales(df, jug)
            if not st or (st.get("intervenciones", 0) < MIN_INTERV):
                continue
            pos = str(pos_por_jug.get(jug, "")).strip()
            st["__linea"] = POS_A_LINEA.get(pos, None)
            registros_por_division[divis].append(st)

    def por_linea(regs):
        return {
            "global": baremo_de(regs),
            "def": baremo_de([r for r in regs if r["__linea"] == "def"]),
            "med": baremo_de([r for r in regs if r["__linea"] == "med"]),
            "atk": baremo_de([r for r in regs if r["__linea"] == "atk"]),
        }

    baremos = {
        # Histórico global (todas las divisiones mezcladas) — fallback de último recurso
        "global": baremo_de(registros),
        "def": baremo_de([r for r in registros if r["__linea"] == "def"]),
        "med": baremo_de([r for r in registros if r["__linea"] == "med"]),
        "atk": baremo_de([r for r in registros if r["__linea"] == "atk"]),
        # Baremos por división — más justo porque compara contra jugadores de la misma categoría
        "divisiones": {
            divis: por_linea(regs)
            for divis, regs in registros_por_division.items()
            if regs  # solo incluir divisiones con datos
        },
        "_meta": {
            "fuente": "todos_los_partidos-2.csv (6 divisiones formativas)",
            "jugador_partidos": len(registros),
            "min_intervenciones": MIN_INTERV,
            "conteo_por_linea": {
                "def": sum(1 for r in registros if r["__linea"] == "def"),
                "med": sum(1 for r in registros if r["__linea"] == "med"),
                "atk": sum(1 for r in registros if r["__linea"] == "atk"),
                "sin_pos": sum(1 for r in registros if r["__linea"] is None),
            },
            "conteo_por_division": {d: len(rs) for d, rs in registros_por_division.items() if rs},
        },
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(baremos, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {OUT}")
    print("Conteo por línea:", baremos["_meta"]["conteo_por_linea"])
    # Ejemplo
    print("\nEjemplo (global · remates_arco):", baremos["global"].get("remates_arco"))
    print("Ejemplo (atk · remates_arco):", baremos["atk"].get("remates_arco"))
    print("Ejemplo (def · intercepciones):", baremos["def"].get("intercepciones"))


if __name__ == "__main__":
    main()
