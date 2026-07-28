"""
parser.py — Procesamiento de exports Sportcode para River Plate Formativo
Lógica: datos individuales en columna Ungrouped (tags separados por coma)
"""

import io
from pathlib import Path
import pandas as pd

# ─── Categorías colectivas ───────────────────────────────────────────────────

CATS_PROPIAS = [
    "Goles Propios", "Situaciones de Gol Propias", "Llegadas Propias",
    "Salidas Propias", "Salidas propias bajo presion",
    "Inicios de juego", "Circulaciones", "Bloque", "Bloques",
    "Transicion Ofensiva", "Transicion Defensiva",
    "Centros Propios", "Detenidas Propias",
    "Perdidas", "Recuperadas",
    "Posesiones", "Chocar Pared", "Cortar Pared",
]

CATS_RIVALES = [
    "Goles Rivales", "Situaciones de Gol Rival",
    "Llegadas Rivales", "Salidas Rivales",
    "Salidas rivales bajo presion", "Inicios de juego Rival",
    "Centros Rivales", "Detenidas Rivales",
]

COLS_MULTI = [
    "Remates", "Amplitud", "Finalización", "Donde",
    "Tipo", "Tipo de Jugada", "Resultado", "Sector", "cual",
]

UMBRAL_SEG = 300  # 5 min

# ─── Cancha (Nacsport 120×80, ataque a la derecha) ───────────────────────────
CANCHA_LARGO = 120
CANCHA_ANCHO = 80
AREA_X_MIN = 102          # último tramo antes del arco
AREA_Y_MIN, AREA_Y_MAX = 18, 62
ULTIMO_TERCIO_X = 80      # x ≥ 80 = último tercio
PROGRESION_MIN = 10       # progresivo si avanza ≥ 10 metros en x


# ─── Pre-procesado de coordenadas ────────────────────────────────────────────

def _parse_coord(v):
    """Devuelve (origen, destino). Acepta '64' o '64, 69'."""
    if pd.isna(v):
        return (None, None)
    s = str(v).strip()
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
        try:
            o = float(parts[0]) if parts[0] else None
            d = float(parts[1]) if len(parts) > 1 and parts[1] else None
            return (o, d)
        except ValueError:
            return (None, None)
    try:
        return (float(s), None)
    except ValueError:
        return (None, None)


def _zona_x(x):
    if x is None or pd.isna(x): return None
    if x >= ULTIMO_TERCIO_X: return "alto"
    if x >= 40: return "medio"
    return "bajo"


def _en_area(x, y):
    if x is None or y is None or pd.isna(x) or pd.isna(y): return False
    return x >= AREA_X_MIN and AREA_Y_MIN <= y <= AREA_Y_MAX


def enriquecer_df(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas derivadas de coordenadas. Idempotente."""
    if "x" in df.columns:
        xs = df["x"].apply(_parse_coord)
        df["x_start"] = [t[0] for t in xs]
        df["x_end"]   = [t[1] for t in xs]
    else:
        df["x_start"] = df["x_end"] = None
    if "y" in df.columns:
        ys = df["y"].apply(_parse_coord)
        df["y_start"] = [t[0] for t in ys]
        df["y_end"]   = [t[1] for t in ys]
    else:
        df["y_start"] = df["y_end"] = None

    df["x_start"] = pd.to_numeric(df["x_start"], errors="coerce")
    df["y_start"] = pd.to_numeric(df["y_start"], errors="coerce")
    df["x_end"]   = pd.to_numeric(df["x_end"], errors="coerce")
    df["y_end"]   = pd.to_numeric(df["y_end"], errors="coerce")

    df["zona_start"] = df["x_start"].apply(_zona_x)
    df["zona_end"]   = df["x_end"].apply(_zona_x)
    df["ultimo_tercio_start"] = df["x_start"] >= ULTIMO_TERCIO_X
    df["ultimo_tercio_end"]   = df["x_end"]   >= ULTIMO_TERCIO_X
    df["en_area_start"] = df.apply(lambda r: _en_area(r["x_start"], r["y_start"]), axis=1)
    df["en_area_end"]   = df.apply(lambda r: _en_area(r["x_end"],   r["y_end"]),   axis=1)

    df["progresion_x"] = df["x_end"] - df["x_start"]
    df["distancia"]    = ((df["x_end"] - df["x_start"]) ** 2 +
                          (df["y_end"] - df["y_start"]) ** 2) ** 0.5
    df["progresivo"]   = df["progresion_x"] >= PROGRESION_MIN
    return df


# ─── I/O ─────────────────────────────────────────────────────────────────────

def leer_desde_bytes(data: bytes, ext: str) -> pd.DataFrame:
    buf = io.BytesIO(data)
    df = None
    if ext == ".csv":
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                buf.seek(0)
                df = pd.read_csv(buf, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise ValueError("No se pudo leer el CSV.")
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(buf)
    else:
        raise ValueError(f"Formato no soportado: {ext}")
    return enriquecer_df(df)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def seg_a_min(seg: float) -> str:
    seg = int(round(max(seg, 0)))
    return f"{seg // 60}'{seg % 60:02d}\""


def contar(serie: pd.Series) -> dict:
    c = {}
    for v in serie.dropna():
        for p in [x.strip() for x in str(v).split(",")]:
            if p:
                c[p] = c.get(p, 0) + 1
    return c


def get_tags(row) -> set:
    """Extrae set de tags de la columna Ungrouped de una fila."""
    val = row.get("Ungrouped", "")
    if pd.isna(val) or not val:
        return set()
    return {t.strip() for t in str(val).split(",")}


def detectar_jugadores(df: pd.DataFrame) -> list:
    conocidas = set(CATS_PROPIAS + CATS_RIVALES + ["PT", "ST"])
    return sorted(set(df["Row"].dropna().unique()) - conocidas)


def nombre_partido(df: pd.DataFrame, fname: str = "") -> str:
    if "Timeline" in df.columns:
        v = df["Timeline"].dropna()
        return str(v.iloc[0]) if not v.empty else fname
    return fname


# ─── Colectivas ──────────────────────────────────────────────────────────────

def _n(df, cat):
    return len(df[df["Row"] == cat])


def _crosstab(df: pd.DataFrame, cat: str, col1: str, col2: str) -> dict:
    """Tabla de contingencia col1 × col2 para filas de `cat`. Soporta multi-valor con comas."""
    sub = df[df["Row"] == cat]
    if sub.empty or col1 not in sub.columns or col2 not in sub.columns:
        return {}
    out = {}
    for _, r in sub[[col1, col2]].dropna().iterrows():
        v1s = [x.strip() for x in str(r[col1]).split(",") if x.strip()]
        v2s = [x.strip() for x in str(r[col2]).split(",") if x.strip()]
        for v1 in v1s:
            for v2 in v2s:
                out.setdefault(v1, {}).setdefault(v2, 0)
                out[v1][v2] += 1
    return out


def calcular_colectivas(df: pd.DataFrame) -> dict:

    def llegadas_detalle(cat):
        sub = df[df["Row"] == cat]
        n = len(sub)
        tipos = contar(sub["Tipo de Jugada"]) if "Tipo de Jugada" in sub.columns else {}
        amplitud = contar(sub["Amplitud"]) if "Amplitud" in sub.columns else {}
        finalizacion = contar(sub["Finalización"]) if "Finalización" in sub.columns else {}
        remates = contar(sub["Remates"]) if "Remates" in sub.columns else {}
        tiros_arco = sum(v for k, v in remates.items() if "Arco" in k)
        goles = sum(v for k, v in remates.items() if "Gol" in k)
        return {
            "total": n,
            "asociado": tipos.get("Asociado", 0),
            "directo": tipos.get("Directo", 0),
            "detenidas": tipos.get("Detenidas", 0),
            "1carril": amplitud.get("1 Carril", 0),
            "2carriles": amplitud.get("2 Carriles", 0),
            "3carriles": amplitud.get("3 Carriles", 0),
            "izq": finalizacion.get("Izquierda", 0),
            "eje": finalizacion.get("Eje", 0),
            "der": finalizacion.get("Derecha", 0),
            "tiros_arco": tiros_arco,
            "goles": goles,
            "afuera": remates.get("Afuera", 0),
            "bloqueado": remates.get("Bloqueado", 0),
            "incompleto": remates.get("Incompleto", 0),
        }

    def salidas_detalle(cat):
        sub = df[df["Row"] == cat]
        tipo = contar(sub["Tipo"]) if "Tipo" in sub.columns else {}
        resultado = contar(sub["Resultado"]) if "Resultado" in sub.columns else {}
        sector = contar(sub["Sector"]) if "Sector" in sub.columns else {}
        return {
            "total": len(sub),
            "cortas": tipo.get("Corta", 0),
            "largas": tipo.get("Larga", 0),
            "progresa": resultado.get("Progresa", 0),
            "no_progresa": resultado.get("No Progresa", 0),
            "izq": sector.get("Izquierda", 0),
            "eje": sector.get("Eje", 0),
            "der": sector.get("Derecha", 0),
        }

    def goles_detalle(cat):
        sub = df[df["Row"] == cat]
        tipos = contar(sub["Tipo de Jugada"]) if "Tipo de Jugada" in sub.columns else {}
        fin = contar(sub["Finalización"]) if "Finalización" in sub.columns else {}
        return {
            "total": len(sub),
            "asociado": tipos.get("Asociado", 0),
            "directo": tipos.get("Directo", 0),
            "detenidas": tipos.get("Detenidas", 0),
            "izq": fin.get("Izquierda", 0),
            "eje": fin.get("Eje", 0),
            "der": fin.get("Derecha", 0),
        }

    def centros(cat):
        sub = df[df["Row"] == cat]
        res = contar(sub["Resultado"]) if "Resultado" in sub.columns else {}
        return {
            "total": len(sub),
            "completos": res.get("Completo", 0),
            "incompletos": res.get("Incompleto", 0),
        }

    corners_p = contar(df[df["Row"] == "Detenidas Propias"]["cual"]).get("Corner", 0) if "cual" in df.columns else 0
    corners_r = contar(df[df["Row"] == "Detenidas Rivales"]["cual"]).get("Corner", 0) if "cual" in df.columns else 0

    return {
        "partido":        nombre_partido(df),
        "goles_propios":  goles_detalle("Goles Propios"),
        "goles_rivales":  goles_detalle("Goles Rivales"),
        "llegadas_prop":  llegadas_detalle("Llegadas Propias"),
        "llegadas_riv":   llegadas_detalle("Llegadas Rivales"),
        "sit_gol_prop":   _n(df, "Situaciones de Gol Propias"),
        "sit_gol_riv":    _n(df, "Situaciones de Gol Rival"),
        "centros_prop":   centros("Centros Propios"),
        "centros_riv":    centros("Centros Rivales"),
        "detenidas_prop": _n(df, "Detenidas Propias"),
        "detenidas_riv":  _n(df, "Detenidas Rivales"),
        "salidas_prop":   salidas_detalle("Salidas Propias"),
        "salidas_riv":    salidas_detalle("Salidas Rivales"),
        "trans_of":       _n(df, "Transicion Ofensiva"),
        "trans_def":      _n(df, "Transicion Defensiva"),
        "circulaciones":  _n(df, "Circulaciones"),
        "bloques":        _n(df, "Bloque") + _n(df, "Bloques"),
        "perdidas":       _n(df, "Perdidas"),
        "recuperadas":    _n(df, "Recuperadas"),
        "corners_prop":   corners_p,
        "corners_riv":    corners_r,
        # Matrices cruzadas — para análisis de carril/tipo
        "matriz_llegadas":     _crosstab(df, "Llegadas Propias",       "Tipo de Jugada", "Finalización"),
        "matriz_amp_carril":   _crosstab(df, "Llegadas Propias",       "Amplitud",       "Finalización"),
        "matriz_sit_gol":      _crosstab(df, "Situaciones de Gol Propias", "Tipo de Jugada", "Finalización"),
    }


# ─── Minutos jugados y cambios ───────────────────────────────────────────────

def calcular_minutos(df: pd.DataFrame) -> list:
    jugadores = detectar_jugadores(df)
    t_inicio = df["Start time"].min()
    filas = []
    for jug in jugadores:
        sub = df[df["Row"] == jug]
        if sub.empty:
            continue
        entrada_s = sub["Start time"].min()
        salida_s = (sub["Start time"] + sub["Duration"].fillna(17)).max()
        minutos = round((salida_s - entrada_s) / 60, 1)
        es_tit = (entrada_s - t_inicio) < UMBRAL_SEG
        filas.append({
            "jugador": jug,
            "condicion": "Titular" if es_tit else "Suplente",
            "entrada": seg_a_min(entrada_s),
            "salida": seg_a_min(salida_s),
            "minutos": minutos,
        })
    filas.sort(key=lambda x: (x["condicion"] != "Titular", x["jugador"]))
    return filas


def inferir_cambios(df: pd.DataFrame) -> list:
    jugadores = detectar_jugadores(df)
    t_inicio = df["Start time"].min()
    t_fin = df["Start time"].max()
    entradas_tarde, salidas_antes = [], []
    for jug in jugadores:
        sub = df[df["Row"] == jug]
        entrada_s = sub["Start time"].min()
        salida_s = (sub["Start time"] + sub["Duration"].fillna(17)).max()
        if (entrada_s - t_inicio) > UMBRAL_SEG:
            entradas_tarde.append((jug, entrada_s))
        if (t_fin - salida_s) > UMBRAL_SEG:
            salidas_antes.append((jug, salida_s))
    entradas_tarde.sort(key=lambda x: x[1])
    salidas_antes.sort(key=lambda x: x[1])
    cambios, usados = [], set()
    for jug_entra, t_entra in entradas_tarde:
        mejor, mejor_diff = None, float("inf")
        for jug_sale, t_sale in salidas_antes:
            if jug_sale in usados:
                continue
            diff = abs(t_entra - t_sale)
            if diff < mejor_diff:
                mejor_diff, mejor = diff, (jug_sale, t_sale)
        sale = mejor[0] if mejor else "?"
        usados.add(sale)
        cambios.append({
            "minuto": seg_a_min(t_entra),
            "sale": sale,
            "entra": jug_entra,
            "equipo": "Propio",
        })
    return cambios


# ─── Acumulación multi-partido ───────────────────────────────────────────────

def analizar_partido(df: pd.DataFrame) -> dict:
    """Empaqueta el análisis completo de un solo partido."""
    return {
        "partido":    nombre_partido(df),
        "jugadores":  detectar_jugadores(df),
        "colectivas": calcular_colectivas(df),
        "minutos":    calcular_minutos(df),
        "cambios":    inferir_cambios(df),
        "goles":      tabla_goles(df),
    }


def _sumar_numericos(dst: dict, src: dict) -> dict:
    """Suma recursivamente claves numéricas; preserva strings del primero."""
    for k, v in src.items():
        if isinstance(v, dict):
            dst[k] = _sumar_numericos(dst.get(k, {}), v)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            dst[k] = dst.get(k, 0) + v
        else:
            dst.setdefault(k, v)
    return dst


def combinar_colectivas(lista: list, etiqueta: str) -> dict:
    out = {}
    for col in lista:
        _sumar_numericos(out, {k: v for k, v in col.items() if k != "partido"})
    out["partido"] = etiqueta
    return out


def combinar_minutos(lista_por_partido: list) -> list:
    por_jug = {}
    for mins in lista_por_partido:
        for p in mins:
            j = p["jugador"]
            if j not in por_jug:
                por_jug[j] = {
                    "jugador": j,
                    "condicion": p["condicion"],
                    "minutos": 0.0,
                    "partidos": 0,
                    "entrada": "—",
                    "salida": "—",
                }
            por_jug[j]["minutos"] += float(p.get("minutos") or 0)
            por_jug[j]["partidos"] += 1
            if p["condicion"] == "Titular":
                por_jug[j]["condicion"] = "Titular"
    out = list(por_jug.values())
    for p in out:
        p["minutos"] = round(p["minutos"], 1)
    out.sort(key=lambda x: (x["condicion"] != "Titular", -x["minutos"], x["jugador"]))
    return out


def _etiquetar(lista: list, etiqueta: str, campo: str = "minuto") -> list:
    return [{**item, campo: f"[{etiqueta}] {item.get(campo, '')}"} for item in lista]


def combinar_partidos(resultados: list) -> dict:
    """Toma una lista de dicts de analizar_partido y los fusiona."""
    if len(resultados) == 1:
        return resultados[0]

    nombres = [r["partido"] for r in resultados]
    etiqueta = f"Acumulado · {len(resultados)} partidos"

    jugadores = sorted({j for r in resultados for j in r["jugadores"]})
    colectivas = combinar_colectivas([r["colectivas"] for r in resultados], etiqueta)
    minutos = combinar_minutos([r["minutos"] for r in resultados])

    cambios, goles = [], []
    for r in resultados:
        tag = (r["partido"] or "P")[:20]
        cambios += _etiquetar(r["cambios"], tag, "minuto")
        goles += _etiquetar(r["goles"], tag, "minuto")

    return {
        "partido":    etiqueta,
        "partidos":   nombres,
        "jugadores":  jugadores,
        "colectivas": colectivas,
        "minutos":    minutos,
        "cambios":    cambios,
        "goles":      goles,
    }


def combinar_individuales(lista: list) -> dict:
    """Suma estadísticas individuales del mismo jugador entre partidos."""
    lista = [x for x in lista if x]
    if not lista:
        return {}
    if len(lista) == 1:
        return lista[0]

    out = {}
    titular = False
    for ind in lista:
        for k, v in ind.items():
            if k in ("jugador", "condicion"):
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[k] = out.get(k, 0) + v
        if ind.get("condicion") == "Titular":
            titular = True

    out["jugador"] = lista[0]["jugador"]
    out["condicion"] = "Titular" if titular else "Suplente"
    out["partidos"] = len(lista)
    p_tot = out.get("pases_total", 0)
    out["pases_efect"] = round(out.get("pases_completos", 0) / p_tot * 100) if p_tot else 0

    # Recalcular efectividades de remate (totales y por superficie) sobre las sumas
    def _rec_rem_ef(prefijo):
        arco = out.get(f"{prefijo}arco", 0)
        gol  = out.get(f"{prefijo}gol", 0)
        tot  = out.get(f"{prefijo}total", 0)
        out[f"{prefijo}efect"] = round((arco + gol) / tot * 100) if tot else 0
    # Total global
    rt_arco = out.get("remates_arco", 0); rt_gol = out.get("remates_gol", 0)
    rt_tot = out.get("remates_total", 0)
    out["remates_efect"] = round((rt_arco + rt_gol) / rt_tot * 100) if rt_tot else 0
    for pre in ("rem_cab_", "rem_pieh_", "rem_piei_"):
        _rec_rem_ef(pre)
    if isinstance(out.get("minutos"), float):
        out["minutos"] = round(out["minutos"], 1)

    # Recalcular derivados posicionales desde las sumas crudas
    n_xy = out.get("acciones_xy", 0)
    if n_xy:
        sx, sy = out.get("_sum_x", 0), out.get("_sum_y", 0)
        sx2, sy2 = out.get("_sum_x2", 0), out.get("_sum_y2", 0)
        out["centro_grav_x"] = round(sx / n_xy, 1)
        out["centro_grav_y"] = round(sy / n_xy, 1)
        var_x = sx2 / n_xy - (sx / n_xy) ** 2
        var_y = sy2 / n_xy - (sy / n_xy) ** 2
        out["dispersion_x"] = round(var_x ** 0.5, 1) if var_x > 0 else 0
        out["dispersion_y"] = round(var_y ** 0.5, 1) if var_y > 0 else 0
        out["pct_ultimo_tercio"] = round(out.get("acciones_ult3", 0) / n_xy * 100)
        out["pct_area"] = round(out.get("acciones_area", 0) / n_xy * 100)
    n_dest = out.get("acciones_destino", 0)
    if n_dest:
        out["progresion_media"] = round(out.get("_sum_prog", 0) / n_dest, 1)
        out["distancia_media"] = round(out.get("_sum_dist", 0) / n_dest, 1)
        out["pct_progresivo"] = round(out.get("acciones_progresivas", 0) / n_dest * 100)
    return out


def tabla_goles(df: pd.DataFrame) -> list:
    goles = []
    for _, row in df[df["Row"].isin(["Goles Propios", "Goles Rivales"])].iterrows():
        equipo = "Propio" if row["Row"] == "Goles Propios" else "Rival"
        goles.append({
            "minuto": seg_a_min(row["Start time"]),
            "equipo": equipo,
            "tipo":   str(row.get("Tipo de Jugada") or "—"),
            "remate": str(row.get("Remates") or "—"),
            "carril": str(row.get("Finalización") or "—"),
        })
    return sorted(goles, key=lambda x: x["minuto"])


# ─── Individuales (leyendo desde Ungrouped) ──────────────────────────────────

def _tiene(tags: set, *args) -> bool:
    """True si todos los args están en el set de tags."""
    return all(a in tags for a in args)


_TILDES = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")

def _norm_tag(s: str) -> str:
    """Normaliza un tag para comparación: lowercase, sin tildes, espacios colapsados."""
    return " ".join(str(s).translate(_TILDES).lower().split())


def estadisticas_individuales(df: pd.DataFrame, jugador: str) -> dict:
    """
    Extrae métricas individuales desde la columna Ungrouped.
    Cada fila del jugador tiene tags separados por coma que describen la acción.
    """
    sub = df[df["Row"] == jugador]
    if sub.empty:
        return {}

    t_inicio = df["Start time"].min()
    entrada_s = sub["Start time"].min()
    salida_s = (sub["Start time"] + sub["Duration"].fillna(17)).max()
    minutos = round((salida_s - entrada_s) / 60, 1)
    es_tit = (entrada_s - t_inicio) < UMBRAL_SEG

    # Contadores
    p_compl = p_incompl = 0
    p_adelante = p_atras = p_lateral = 0
    p_largo_c = p_largo_i = p_filtrado = p_clave = p_apoyo = 0
    c_compl = c_incompl = 0
    tiro_arco = tiro_afuera = tiro_bloq = tiro_gol = 0
    # Remates por superficie (cab=cabeza, pieh=pie hábil, piei=pie inhábil, sd=sin dato)
    rem_sup = {s: {"arco": 0, "gol": 0, "afuera": 0, "bloq": 0} for s in ("cab", "pieh", "piei", "sd")}
    duelo_o_g = duelo_o_p = duelo_d_g = duelo_d_p = 0
    aereo_o_g = aereo_o_p = aereo_d_g = aereo_d_p = 0
    regate_c = regate_i = 0
    recup_posic = recup_interv = recup_tras = 0
    perd_pase = perd_ctrl = perd_gamb = 0
    interv_entrada_g = interv_entrada_p = 0
    interv_anticipo_g = interv_anticipo_p = 0
    interv_intercep = 0
    interv_bloqueo = 0
    toques_area = recep_lineas = recep_espal = recep_espacio = ruptura = 0
    despeje_or = despeje_no = 0
    falta_rec = falta_hec = 0
    positivos = negativos = 0
    intervenciones = len(sub)

    for _, row in sub.iterrows():
        t = get_tags(row)
        if not t:
            continue

        # ── PASES ────────────────────────────────────────────────────────
        if "PCompletos" in t:
            p_compl += 1
            if "Adelante" in t: p_adelante += 1
            elif "Atras" in t:  p_atras += 1
            elif "Lateral" in t: p_lateral += 1
            if "Largo Completo" in t: p_largo_c += 1
            if "Filtrado" in t: p_filtrado += 1
            if "Clave" in t:    p_clave += 1
            if "Apoyo" in t:    p_apoyo += 1

        elif "PIncompletos" in t:
            p_incompl += 1
            if "Largo Incompleto" in t: p_largo_i += 1

        # ── CENTROS ──────────────────────────────────────────────────────
        if "CCompletos" in t:
            c_compl += 1
            if "Clave" in t or "CAsistencia" in t: p_clave += 1

        elif "CIncompletos" in t:
            c_incompl += 1

        # ── TIROS ────────────────────────────────────────────────────────
        if "Tiros" in t or "Arco" in t or "Afuera" in t or "Bloqueado" in t or "Gol" in t:
            if "Arco" in t:      tiro_arco += 1
            if "Gol" in t:       tiro_gol += 1
            if "Afuera" in t:    tiro_afuera += 1
            if "Bloqueado" in t: tiro_bloq += 1
            # Superficie de remate (cabeza / pie hábil / pie inhábil). Matching insensible a
            # mayúsculas y tildes para cubrir variaciones de tagging ("Pie habil", "Pie Hábil", etc.)
            t_norm = {_norm_tag(x) for x in t}
            sup = "sd"
            if "cabeza" in t_norm or "cabezazo" in t_norm:
                sup = "cab"
            elif "pie inhabil" in t_norm or "pie no habil" in t_norm or "inhabil" in t_norm:
                sup = "piei"  # chequear inhábil PRIMERO (contiene "habil" como substring)
            elif "pie habil" in t_norm or "habil" in t_norm:
                sup = "pieh"
            if "Arco" in t:      rem_sup[sup]["arco"]   += 1
            if "Gol" in t:       rem_sup[sup]["gol"]    += 1
            if "Afuera" in t:    rem_sup[sup]["afuera"] += 1
            if "Bloqueado" in t: rem_sup[sup]["bloq"]   += 1

        # ── DUELOS 1V1 ───────────────────────────────────────────────────
        if "Duelos 1V1" in t or "1v1O+" in t or "1v1O-" in t or "1v1D+" in t or "1v1D-" in t:
            if "1v1O+" in t: duelo_o_g += 1
            if "1v1O-" in t: duelo_o_p += 1
            if "1v1D+" in t: duelo_d_g += 1
            if "1v1D-" in t: duelo_d_p += 1

        # ── DUELOS AÉREOS ────────────────────────────────────────────────
        if "Duelos Aereos" in t or "DAO+" in t or "DAO-" in t or "DAD+" in t or "DAD-" in t:
            if "DAO+" in t: aereo_o_g += 1
            if "DAO-" in t: aereo_o_p += 1
            if "DAD+" in t: aereo_d_g += 1
            if "DAD-" in t: aereo_d_p += 1

        # ── REGATES ──────────────────────────────────────────────────────
        if "R+" in t: regate_c += 1
        if "R-" in t: regate_i += 1

        # ── RECUPERADAS ──────────────────────────────────────────────────
        if "RECUPERACION xPosicional" in t:  recup_posic += 1
        if "RECUPERACION xIntervencion" in t: recup_interv += 1
        if "Tras Perdida" in t:              recup_tras += 1

        # ── PÉRDIDAS ─────────────────────────────────────────────────────
        if "PERDIDAS: xPase" in t:    perd_pase += 1
        if "PERDIDAS: xControl" in t: perd_ctrl += 1
        if "PERDIDAS: xGambeta" in t: perd_gamb += 1

        # ── INTERVENCIONES DEFENSIVAS ────────────────────────────────────
        if "Intervencion Defensiva" in t:
            if "E+" in t: interv_entrada_g += 1
            if "E-" in t: interv_entrada_p += 1
            if "A+" in t: interv_anticipo_g += 1
            if "A-" in t: interv_anticipo_p += 1
            if "I+" in t or "I-" in t: interv_intercep += 1
            if "B+" in t or "B-" in t: interv_bloqueo += 1

        # ── TÁCTICO ──────────────────────────────────────────────────────
        if "Toques en Area Rival" in t:           toques_area += 1
        if "Recepcion entre Lineas" in t:         recep_lineas += 1
        if "Recepcion a espaldas del volante" in t: recep_espal += 1
        if "Recepcion al espacio" in t:           recep_espacio += 1
        if "Ruptura en conduccion" in t:          ruptura += 1

        # ── DESPEJES ─────────────────────────────────────────────────────
        if "Despeje" in t:
            if "D+" in t: despeje_or += 1
            else:         despeje_no += 1

        # ── FALTAS ───────────────────────────────────────────────────────
        if "Faltas Recibidas" in t: falta_rec += 1
        if "Faltas Hechas" in t:   falta_hec += 1

        # ── POSITIVO / NEGATIVO ──────────────────────────────────────────
        if "POSITIVO" in t: positivos += 1
        if "NEGATIVO" in t: negativos += 1

    # ── MÉTRICAS POSICIONALES (desde x,y) ────────────────────────────────
    con_xy = sub[sub["x_start"].notna() & sub["y_start"].notna()]
    n_xy = len(con_xy)
    sum_x = float(con_xy["x_start"].sum()) if n_xy else 0
    sum_y = float(con_xy["y_start"].sum()) if n_xy else 0
    sum_x2 = float((con_xy["x_start"] ** 2).sum()) if n_xy else 0
    sum_y2 = float((con_xy["y_start"] ** 2).sum()) if n_xy else 0
    n_ult = int(con_xy["ultimo_tercio_start"].sum()) if n_xy else 0
    n_area = int(con_xy["en_area_start"].sum()) if n_xy else 0
    cg_x = round(sum_x / n_xy, 1) if n_xy else 0
    cg_y = round(sum_y / n_xy, 1) if n_xy else 0
    var_x = (sum_x2 / n_xy - (sum_x / n_xy) ** 2) if n_xy else 0
    var_y = (sum_y2 / n_xy - (sum_y / n_xy) ** 2) if n_xy else 0
    disp_x = round(var_x ** 0.5, 1) if var_x > 0 else 0
    disp_y = round(var_y ** 0.5, 1) if var_y > 0 else 0
    pct_ult = round(n_ult / n_xy * 100) if n_xy else 0
    pct_area = round(n_area / n_xy * 100) if n_xy else 0

    con_destino = sub[sub["x_start"].notna() & sub["x_end"].notna()]
    n_dest = len(con_destino)
    sum_prog = float(con_destino["progresion_x"].sum()) if n_dest else 0
    sum_dist = float(con_destino["distancia"].sum()) if n_dest else 0
    n_prog = int(con_destino["progresivo"].sum()) if n_dest else 0
    prog_media = round(sum_prog / n_dest, 1) if n_dest else 0
    dist_media = round(sum_dist / n_dest, 1) if n_dest else 0
    pct_prog = round(n_prog / n_dest * 100) if n_dest else 0

    p_total = p_compl + p_incompl
    p_efect = round(p_compl / p_total * 100) if p_total else 0

    # Totales y efectividades por superficie de remate.
    # Efectividad = (al arco + goles) / total de remates con esa superficie.
    rem_totales = {s: sum(v.values()) for s, v in rem_sup.items()}
    def _ef(s):
        tot = rem_totales[s]
        return round((rem_sup[s]["arco"] + rem_sup[s]["gol"]) / tot * 100) if tot else 0
    rem_efect = {s: _ef(s) for s in rem_sup}

    # Asistencias — se leen DIRECTAMENTE del tag individual del jugador:
    #   PAsistencia = asistencia de pase   ·   CAsistencia = asistencia de centro
    # El analista ya marca la acción como asistencia al taggearla, así que se cuentan
    # 1:1. (Antes se cruzaba con "Goles Propios" —dato colectivo— dentro de una ventana
    #  temporal; fallaba cuando el timestamp del centro/pase quedaba fuera de esa ventana,
    #  p. ej. si el centro se taggeaba unos segundos DESPUÉS del gol. Reporte de A. Urricelqui.)
    goles_jug = tiro_gol
    asist_pases = 0
    asist_centros = 0
    for _, row in sub.iterrows():
        tn = {_norm_tag(x) for x in get_tags(row)}
        if "pasistencia" in tn:
            asist_pases += 1
        if "casistencia" in tn:
            asist_centros += 1
    asistencias = asist_pases + asist_centros

    return {
        "jugador":          jugador,
        "minutos":          minutos,
        "condicion":        "Titular" if es_tit else "Suplente",
        "intervenciones":   intervenciones,
        "goles":            goles_jug,
        "asistencias":      asistencias,
        "asist_pases":      asist_pases,    # asistencias provenientes de pase clave
        "asist_centros":    asist_centros,  # asistencias provenientes de centro
        # pases
        "pases_total":      p_total,
        "pases_completos":  p_compl,
        "pases_incompletos": p_incompl,
        "pases_efect":      p_efect,
        "pases_adelante":   p_adelante,
        "pases_atras":      p_atras,
        "pases_lateral":    p_lateral,
        "pases_largo_c":    p_largo_c,
        "pases_largo_i":    p_largo_i,
        "pases_filtrado":   p_filtrado,
        "pases_clave":      p_clave,
        "pases_apoyo":      p_apoyo,
        # centros
        "centros_c":        c_compl,
        "centros_i":        c_incompl,
        # remates
        "remates_arco":     tiro_arco,
        "remates_gol":      tiro_gol,
        "remates_afuera":   tiro_afuera,
        "remates_bloq":     tiro_bloq,
        "remates_total":    tiro_arco + tiro_gol + tiro_afuera + tiro_bloq,
        "remates_efect":    round((tiro_arco + tiro_gol) / (tiro_arco + tiro_gol + tiro_afuera + tiro_bloq) * 100) if (tiro_arco + tiro_gol + tiro_afuera + tiro_bloq) else 0,
        # remates por superficie
        "rem_cab_arco":     rem_sup["cab"]["arco"],
        "rem_cab_gol":      rem_sup["cab"]["gol"],
        "rem_cab_afuera":   rem_sup["cab"]["afuera"],
        "rem_cab_bloq":     rem_sup["cab"]["bloq"],
        "rem_cab_total":    rem_totales["cab"],
        "rem_cab_efect":    rem_efect["cab"],
        "rem_pieh_arco":    rem_sup["pieh"]["arco"],
        "rem_pieh_gol":     rem_sup["pieh"]["gol"],
        "rem_pieh_afuera":  rem_sup["pieh"]["afuera"],
        "rem_pieh_bloq":    rem_sup["pieh"]["bloq"],
        "rem_pieh_total":   rem_totales["pieh"],
        "rem_pieh_efect":   rem_efect["pieh"],
        "rem_piei_arco":    rem_sup["piei"]["arco"],
        "rem_piei_gol":     rem_sup["piei"]["gol"],
        "rem_piei_afuera":  rem_sup["piei"]["afuera"],
        "rem_piei_bloq":    rem_sup["piei"]["bloq"],
        "rem_piei_total":   rem_totales["piei"],
        "rem_piei_efect":   rem_efect["piei"],
        "rem_sd_total":     rem_totales["sd"],
        # duelos 1v1
        "dao_plus":         duelo_o_g,
        "dao_minus":        duelo_o_p,
        "dad_plus":         duelo_d_g,
        "dad_minus":        duelo_d_p,
        # duelos aéreos
        "aereo_og":         aereo_o_g,
        "aereo_op":         aereo_o_p,
        "aereo_dg":         aereo_d_g,
        "aereo_dp":         aereo_d_p,
        # regates
        "regate_c":         regate_c,
        "regate_i":         regate_i,
        # recuperadas
        "recup_posic":      recup_posic,
        "recup_interv":     recup_interv,
        "recup_tras":       recup_tras,
        "recup_total":      recup_posic + recup_interv + recup_tras,
        # pérdidas
        "perd_pase":        perd_pase,
        "perd_control":     perd_ctrl,
        "perd_gambeta":     perd_gamb,
        "perd_total":       perd_pase + perd_ctrl + perd_gamb,
        # intervenciones def
        "interv_entrada_g":  interv_entrada_g,
        "interv_entrada_p":  interv_entrada_p,
        "interv_anticipo_g": interv_anticipo_g,
        "interv_anticipo_p": interv_anticipo_p,
        "intercepciones":    interv_intercep,
        "bloqueos":          interv_bloqueo,
        # táctico
        "toques_area":      toques_area,
        "recep_lineas":     recep_lineas,
        "recep_espal":      recep_espal,
        "recep_espacio":    recep_espacio,
        "ruptura":          ruptura,
        "apoyos":           p_apoyo,
        # despejes
        "despeje_or":       despeje_or,
        "despeje_no":       despeje_no,
        # otros
        "faltas_rec":       falta_rec,
        "faltas_hec":       falta_hec,
        "positivos":        positivos,
        "negativos":        negativos,
        # posicionales (derivados)
        "acciones_xy":      n_xy,
        "centro_grav_x":    cg_x,
        "centro_grav_y":    cg_y,
        "dispersion_x":     disp_x,
        "dispersion_y":     disp_y,
        "pct_ultimo_tercio": pct_ult,
        "pct_area":         pct_area,
        "acciones_area":    n_area,
        "acciones_ult3":    n_ult,
        "acciones_destino": n_dest,
        "progresion_media": prog_media,
        "distancia_media":  dist_media,
        "pct_progresivo":   pct_prog,
        "acciones_progresivas": n_prog,
        # posicionales (sumas crudas, para combinar entre partidos)
        "_sum_x":  sum_x,
        "_sum_y":  sum_y,
        "_sum_x2": sum_x2,
        "_sum_y2": sum_y2,
        "_sum_prog": sum_prog,
        "_sum_dist": sum_dist,
    }
