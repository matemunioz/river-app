"""
app.py — River Plate Videoanálisis · Backend Flask
"""

import io
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file
import parser as sc
import pdf_gen as pg

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


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
    """Devuelve lista de DataFrames a partir de uno o más uploads bajo 'archivo'."""
    files = req.files.getlist("archivo")
    if not files:
        raise ValueError("No se recibió archivo")
    dfs = []
    for f in files:
        df = leer_archivo(f)
        if "Row" not in df.columns:
            raise ValueError(f"'{f.filename}' no tiene columna 'Row'. ¿Es un export de Sportcode?")
        df = _aplicar_tiempo(df, req)
        dfs.append(df)
    return dfs


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
    return jsonify(sc.combinar_partidos(resultados))


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
            coords.append({
                "x":  float(r["x_start"]),
                "y":  float(r["y_start"]),
                "xe": float(r["x_end"]) if pd.notna(r.get("x_end")) else None,
                "ye": float(r["y_end"]) if pd.notna(r.get("y_end")) else None,
                "prog": bool(r.get("progresivo", False)),
                "tags": str(r.get("Ungrouped") or "") if pd.notna(r.get("Ungrouped")) else "",
            })

    pdf_bytes = pg.generar_pdf_individual(ind, partido, agg["minutos"], todos_jug=todos_jug, coords=coords)
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
    import pandas as pd
    acciones = []
    for df in dfs:
        sub = df[(df["Row"] == jugador) & df["x_start"].notna() & df["y_start"].notna()]
        for _, r in sub.iterrows():
            acciones.append({
                "x":  float(r["x_start"]),
                "y":  float(r["y_start"]),
                "xe": float(r["x_end"]) if pd.notna(r.get("x_end")) else None,
                "ye": float(r["y_end"]) if pd.notna(r.get("y_end")) else None,
                "prog": bool(r.get("progresivo", False)),
                "area": bool(r.get("en_area_start", False)),
                "t":  float(r["Start time"]) if pd.notna(r.get("Start time")) else 0,
                "tags":    str(r.get("Ungrouped") or "") if pd.notna(r.get("Ungrouped")) else "",
                "partido": str(r.get("Timeline") or "") if pd.notna(r.get("Timeline")) else "",
            })
    return jsonify(acciones)


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
