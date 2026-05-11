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


# ─── I/O ─────────────────────────────────────────────────────────────────────

def leer_desde_bytes(data: bytes, ext: str) -> pd.DataFrame:
    buf = io.BytesIO(data)
    if ext == ".csv":
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                buf.seek(0)
                return pd.read_csv(buf, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("No se pudo leer el CSV.")
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(buf)
    raise ValueError(f"Formato no soportado: {ext}")


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
    if isinstance(out.get("minutos"), float):
        out["minutos"] = round(out["minutos"], 1)
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

    p_total = p_compl + p_incompl
    p_efect = round(p_compl / p_total * 100) if p_total else 0

    # Goles y asistencias cruzando con goles propios
    goles_jug = tiro_gol  # ya contados arriba desde los tags del jugador
    asistencias = 0
    # La asistencia la buscamos en los goles propios
    goles_prop_df = df[df["Row"] == "Goles Propios"]
    for _, grow in goles_prop_df.iterrows():
        t_gol = grow["Start time"]
        previas = sub[(sub["Start time"] <= t_gol + 2) & (sub["Start time"] >= t_gol - 30)]
        for _, prev_row in previas.iterrows():
            prev_tags = get_tags(prev_row)
            if ("CCompletos" in prev_tags or "PCompletos" in prev_tags) and ("Clave" in prev_tags or "CAsistencia" in prev_tags):
                asistencias += 1
                break

    return {
        "jugador":          jugador,
        "minutos":          minutos,
        "condicion":        "Titular" if es_tit else "Suplente",
        "intervenciones":   intervenciones,
        "goles":            goles_jug,
        "asistencias":      asistencias,
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
    }
