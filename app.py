"""
app.py — River Plate Videoanálisis · Backend Flask
"""

import io
from pathlib import Path
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file
import parser as sc
import pdf_gen as pg
import pdf_individual_v2 as pg_v2
import biblioteca as bib

app = Flask(__name__)
# 25 MB alcanza de sobra: el CSV más pesado de un partido ronda los 130 KB.
# Con 200 MB, un archivo grande arrastrado por error revienta la RAM del server.
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def leer_archivo(archivo):
    nombre = archivo.filename or "archivo"
    ext = Path(nombre).suffix.lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise ValueError(f"Formato no soportado: {ext}")
    return sc.leer_desde_bytes(archivo.read(), ext)


def _aplicar_tiempo(df, req):
    """Filtra rows por rango de tiempo (Start time en segundos)."""
    t_min = req.form.get("t_min")
    t_max = req.form.get("t_max")
    if not t_min and not t_max:
        return df
    mask = df["Start time"].notna()
    if t_min:
        mask &= df["Start time"] >= float(t_min)
    if t_max:
        mask &= df["Start time"] <= float(t_max)
    return df[mask].copy()


def leer_todos(req):
    """Lista de DataFrames del request. Dos fuentes, combinables:

      · 'archivo'  → uploads (el analista arrastra un CSV suelto)
      · 'partido'  → ids de la biblioteca (carpeta del área; el CSV nunca viaja
                     por el navegador, que es lo que queremos para datos de menores)

    Como todos los endpoints entran por acá, soportan las dos sin cambios.
    """
    dfs = []

    for pid in req.form.getlist("partido"):
        try:
            df = bib.leer_df(pid)
        except FileNotFoundError as e:
            raise ValueError(str(e))
        if "Row" not in df.columns:
            raise ValueError(f"El partido '{pid}' no tiene columna 'Row'. ¿Es un export de Sportcode?")
        dfs.append(_aplicar_tiempo(df, req))

    for f in req.files.getlist("archivo"):
        df = leer_archivo(f)
        if "Row" not in df.columns:
            raise ValueError(f"'{f.filename}' no tiene columna 'Row'. ¿Es un export de Sportcode?")
        dfs.append(_aplicar_tiempo(df, req))

    if not dfs:
        raise ValueError("No se recibió ningún partido")
    return dfs


@app.route("/api/biblioteca", methods=["GET"])
def api_biblioteca():
    """Inventario de la carpeta del área: qué partidos hay para analizar.

    Devuelve sólo metadatos (división, fecha, rival) — nunca el contenido del
    CSV, que puede tener nombres de menores.
    """
    try:
        return jsonify(bib.listar())
    except Exception as e:
        return jsonify({"disponible": False, "error": str(e), "partidos": []}), 500


@app.route("/api/panel", methods=["GET"])
def api_panel():
    """Resumen de toda la biblioteca para la pantalla principal: registro por
    división, forma reciente y últimos partidos cargados. Lee sólo la columna
    con el tipo de fila, así que es barato aun con 90+ partidos."""
    try:
        return jsonify(bib.panel())
    except Exception as e:
        return jsonify({"disponible": False, "error": str(e),
                        "divisiones": [], "ultimos": []}), 500


@app.route("/api/biblioteca/refrescar", methods=["POST"])
def api_biblioteca_refrescar():
    """Vuelve a leer la carpeta desde cero (tras agregar partidos nuevos)."""
    bib.limpiar_cache()
    return jsonify(bib.listar())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analizar", methods=["POST"])
def analizar():
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    resultados = [sc.analizar_partido(df) for df in dfs]
    out = sc.combinar_partidos(resultados)
    # Adjunto las colectivas por partido para drill-down en el hero
    out["partidos_data"] = [r["colectivas"] for r in resultados]
    return jsonify(out)


# ─── Endpoints de CARGA DIFERIDA (cálculos pesados, se piden aparte) ─────────
# El frontend v3 los llama por su cuenta cuando entra a la pantalla que los usa,
# con lazy loading, para no pesar el request principal (/api/analizar).

@app.route("/api/momentum", methods=["POST"])
def momentum():
    """Match Momentum (xT por minuto). Se calcula solo cuando se pide."""
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(sc.calcular_momentum(dfs))


@app.route("/api/heatmap-informe", methods=["POST"])
def heatmap_informe():
    """Heatmap de remates + matriz sit. gol rival para el informe anual.
    Se calcula solo cuando se pide."""
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(sc.calcular_heatmap_informe(dfs))


@app.route("/api/red-pases", methods=["POST"])
def red_pases():
    """Red de conexiones de pases (inferida por secuencia temporal).
    Carga diferida: se pide solo al abrir la sección."""
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(sc.red_pases(dfs))


@app.route("/api/pdf/colectivo", methods=["POST"])
def pdf_colectivo():
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    resultados = [sc.analizar_partido(df) for df in dfs]
    agg = sc.combinar_partidos(resultados)

    import pandas as pd

    def _datos_partido(df):
        jugs = sorted(set(sc.detectar_jugadores(df)))
        tj = {}
        for j in jugs:
            s = sc.estadisticas_individuales(df, j)
            if s: tj[j] = s
        ev = {"team_coords": [], "pases_filtrados": [],
              "llegadas_coords": [], "perdidas_coords": [], "recuperadas_coords": []}
        sub_j = df[df["Row"].isin(jugs) & df["x_start"].notna() & df["y_start"].notna()]
        for _, r in sub_j.iterrows():
            xy = {"x": float(r["x_start"]), "y": float(r["y_start"])}
            ev["team_coords"].append(xy)
            tags = str(r.get("Ungrouped") or "")
            if "PERDIDAS" in tags:
                ev["perdidas_coords"].append(xy)
            if "RECUPERACION" in tags or "Tras Perdida" in tags:
                ev["recuperadas_coords"].append(xy)
            if "Filtrado" in tags:
                ev["pases_filtrados"].append({
                    **xy,
                    "xe": float(r["x_end"]) if pd.notna(r.get("x_end")) else None,
                    "ye": float(r["y_end"]) if pd.notna(r.get("y_end")) else None,
                    "completo": "PCompletos" in tags or "CCompletos" in tags,
                })
        sub_lp = df[(df["Row"] == "Llegadas Propias") & df["x_start"].notna() & df["y_start"].notna()]
        for _, r in sub_lp.iterrows():
            ev["llegadas_coords"].append({"x": float(r["x_start"]), "y": float(r["y_start"])})
        return {"todos_jug": tj, "eventos": ev}

    partidos_jug = [_datos_partido(df) for df in dfs]

    # Acumulado: combinar todos_jug + concatenar eventos
    all_jugadores = sorted({j for p in partidos_jug for j in p["todos_jug"]})
    todos_jug_agg = {}
    for j in all_jugadores:
        inds = [p["todos_jug"][j] for p in partidos_jug if j in p["todos_jug"]]
        if inds:
            todos_jug_agg[j] = sc.combinar_individuales(inds)
    eventos_agg = {k: [] for k in partidos_jug[0]["eventos"]}
    for p in partidos_jug:
        for k in eventos_agg:
            eventos_agg[k].extend(p["eventos"][k])

    pdf_bytes = pg.generar_pdf_colectivo(
        resultados, agg,
        todos_jug=todos_jug_agg, eventos=eventos_agg,
        partidos_jug=partidos_jug,
    )
    partido = agg["colectivas"].get("partido", "partido")
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Colectivo_{partido}.pdf",
    )


@app.route("/api/pdf/individual", methods=["POST"])
def pdf_individual():
    jugador = request.form.get("jugador", "")
    if not jugador:
        return jsonify({"error": "No se especificó jugador"}), 400
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    inds = [sc.estadisticas_individuales(df, jugador) for df in dfs]
    ind = sc.combinar_individuales(inds)
    resultados = [sc.analizar_partido(df) for df in dfs]
    agg = sc.combinar_partidos(resultados)
    partido = agg["colectivas"].get("partido", "partido")

    # Stats del plantel para habilitar FODA + percentiles en el PDF
    jugadores = sorted({j for df in dfs for j in sc.detectar_jugadores(df)})
    todos_jug = {}
    for j in jugadores:
        per = [sc.estadisticas_individuales(df, j) for df in dfs]
        per = [x for x in per if x]
        if per:
            todos_jug[j] = sc.combinar_individuales(per)

    import pandas as pd
    coords = []
    for df in dfs:
        sub = df[(df["Row"] == jugador) & df["x_start"].notna() & df["y_start"].notna()]
        for _, r in sub.iterrows():
            # Remates en la última coordenada (donde se remata), igual que el mapa web
            if sc.es_remate(r):
                px, py = sc.coord_remate(r)
            else:
                px, py = float(r["x_start"]), float(r["y_start"])
            coords.append({
                "x":  px,
                "y":  py,
                "xe": float(r["x_end"]) if pd.notna(r.get("x_end")) else None,
                "ye": float(r["y_end"]) if pd.notna(r.get("y_end")) else None,
                "prog": bool(r.get("progresivo", False)),
                "tags": str(r.get("Ungrouped") or "") if pd.notna(r.get("Ungrouped")) else "",
            })

    pdf_bytes = pg_v2.generar_pdf_individual_v2(ind, partido, agg["minutos"], todos_jug=todos_jug, coords=coords)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Individual_{jugador}_{partido}.pdf",
    )


@app.route("/api/jugadores-stats", methods=["POST"])
def jugadores_stats():
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    jugadores = sorted({j for df in dfs for j in sc.detectar_jugadores(df)})
    out = {}
    for j in jugadores:
        inds = [sc.estadisticas_individuales(df, j) for df in dfs]
        inds = [i for i in inds if i]
        if inds:
            out[j] = sc.combinar_individuales(inds)
    return jsonify(out)


@app.route("/api/coords-jugador", methods=["POST"])
def coords_jugador():
    jugador = request.form.get("jugador", "")
    if not jugador:
        return jsonify({"error": "Falta jugador"}), 400
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(_coords_de_jugadores(dfs, [jugador]))


@app.route("/api/coords-multi", methods=["POST"])
def coords_multi():
    jugs_raw = request.form.getlist("jugador")
    if not jugs_raw:
        return jsonify({"error": "Falta jugador"}), 400
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(_coords_de_jugadores(dfs, jugs_raw))


def _coords_de_jugadores(dfs, jugadores):
    import pandas as pd
    jugs_set = set(jugadores)
    acciones = []
    for df in dfs:
        sub = df[df["Row"].isin(jugs_set) & df["x_start"].notna() & df["y_start"].notna()]
        for _, r in sub.iterrows():
            video_raw = r.get("video") if "video" in df.columns else None
            # Remates: el punto del mapa es DONDE se remata (última coordenada
            # de la jugada), no donde arranca (pedido A.U.: un gol tras jugada
            # individual quedaba dibujado en mitad de cancha).
            if sc.es_remate(r):
                px, py = sc.coord_remate(r)
                en_area = bool(r.get("en_area_end", False) or r.get("en_area_start", False))
            else:
                px, py = float(r["x_start"]), float(r["y_start"])
                en_area = bool(r.get("en_area_start", False))
            acciones.append({
                "x":  px,
                "y":  py,
                "xe": float(r["x_end"]) if pd.notna(r.get("x_end")) else None,
                "ye": float(r["y_end"]) if pd.notna(r.get("y_end")) else None,
                "prog": bool(r.get("progresivo", False)),
                "area": en_area,
                "t":  sc.seg_num(r.get("Start time")) or 0,
                "duration": float(r["Duration"]) if "Duration" in df.columns and pd.notna(r.get("Duration")) else None,
                "video":   str(video_raw) if pd.notna(video_raw) else None,
                "tags":    str(r.get("Ungrouped") or "") if pd.notna(r.get("Ungrouped")) else "",
                "partido": str(r.get("Timeline") or "") if pd.notna(r.get("Timeline")) else "",
                "jugador": str(r["Row"]),
            })
    return acciones


@app.route("/api/notas-tagging", methods=["POST"])
def notas_tagging():
    """Detecta acciones con tagging incompleto para que el analista las pueda corregir
    en Sportcode (devuelve partido, minuto, jugador, tags actuales y qué falta)."""
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    REMATE_TAGS_NORM = {"tiros", "arco", "afuera", "bloqueado", "gol"}
    SUP_TAGS_NORM   = {"cabeza", "cabezazo", "pie habil", "pie inhabil", "habil", "inhabil"}
    RESULTADO_REMATE_NORM = {"arco", "afuera", "bloqueado", "gol"}
    PASE_RES_NORM      = {"pcompletos", "pincompletos"}
    CENTRO_RES_NORM    = {"ccompletos", "cincompletos", "casistencia"}

    issues = []
    for df in dfs:
        partido = sc.nombre_partido(df)
        jugadores = set(sc.detectar_jugadores(df))
        sub = df[df["Row"].isin(jugadores)]
        for _, r in sub.iterrows():
            tags = sc.get_tags(r)
            if not tags:
                continue
            tags_norm = {sc._norm_tag(t) for t in tags}
            jug   = str(r["Row"])
            mins  = sc.seg_a_min(r["Start time"]) if pd.notna(r.get("Start time")) else "?"
            tag_str = str(r.get("Ungrouped") or "")

            def add(tipo, detalle):
                issues.append({
                    "tipo": tipo, "partido": partido, "minuto": mins,
                    "jugador": jug, "tags": tag_str, "detalle": detalle,
                })

            # 1) Remate sin tag de superficie
            es_remate = any(t in tags_norm for t in REMATE_TAGS_NORM)
            if es_remate:
                if not any(t in tags_norm for t in SUP_TAGS_NORM):
                    add("remate_sin_superficie",
                        "Remate sin superficie (falta Cabeza / Pie habil / Pie inhabil)")
                if not any(t in tags_norm for t in RESULTADO_REMATE_NORM):
                    add("remate_sin_resultado",
                        "Remate sin resultado (falta Arco / Afuera / Bloqueado / Gol)")

            # 2) Pase con tag PCompletos/PIncompletos pero ambos a la vez (contradicción)
            if "pcompletos" in tags_norm and "pincompletos" in tags_norm:
                add("pase_contradictorio",
                    "Pase taggeado como Completo e Incompleto a la vez")

            # 3) Centro con tag CCompletos/CIncompletos pero ambos a la vez
            if "ccompletos" in tags_norm and "cincompletos" in tags_norm:
                add("centro_contradictorio",
                    "Centro taggeado como Completo e Incompleto a la vez")

            # 4) Acción del jugador sin coordenada de origen (x_start, y_start)
            if pd.isna(r.get("x_start")) or pd.isna(r.get("y_start")):
                accionables = REMATE_TAGS_NORM | PASE_RES_NORM | CENTRO_RES_NORM | {
                    "perdidas: xpase", "perdidas: xcontrol", "perdidas: xgambeta",
                    "recuperacion xposicional", "recuperacion xintervencion", "tras perdida",
                    "1v1o+", "1v1o-", "1v1d+", "1v1d-", "dao+", "dao-", "dad+", "dad-",
                }
                if any(t in tags_norm for t in accionables):
                    add("sin_coordenada",
                        "Acción sin coordenada (x,y) — no aparece en mapas")

            # 5) 1v1 ofensivo ganado debe tener origen Y destino (4 ejes).
            # El resto de duelos solo necesita origen — esta regla solo aplica a 1v1O+.
            if "1v1o+" in tags_norm:
                tiene_inicio = pd.notna(r.get("x_start")) and pd.notna(r.get("y_start"))
                tiene_fin    = pd.notna(r.get("x_end"))   and pd.notna(r.get("y_end"))
                if tiene_inicio and not tiene_fin:
                    add("1v1o_sin_destino",
                        "1v1 ofensivo ganado sin destino (x_end, y_end) — falta el segundo punto de la jugada")

    # Resumen por tipo
    resumen = {}
    for it in issues:
        resumen[it["tipo"]] = resumen.get(it["tipo"], 0) + 1

    return jsonify({"total": len(issues), "resumen": resumen, "issues": issues})


@app.route("/api/individual", methods=["POST"])
def individual():
    jugador = request.form.get("jugador", "")
    if not jugador:
        return jsonify({"error": "No se especificó jugador"}), 400
    try:
        dfs = leer_todos(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    inds = [sc.estadisticas_individuales(df, jugador) for df in dfs]
    return jsonify(sc.combinar_individuales(inds))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
