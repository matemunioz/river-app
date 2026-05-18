"""
pdf_gen.py — Informe estructurado de Videoanálisis · River Plate Formativo
- Colectivo: cover + página por partido + acumulado + plantel + conclusiones
- Individual: cover + KPIs + mapa posicional + percentiles + FODA + análisis
"""

import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ─── Paleta ──────────────────────────────────────────────────────────────────
NEGRO  = colors.HexColor("#0a0a0a")
ROJO   = colors.HexColor("#CC0000")
ROJO2  = colors.HexColor("#990000")
BLANCO = colors.white
GRIS0  = colors.HexColor("#111111")
GRIS1  = colors.HexColor("#1a1a1a")
GRIS2  = colors.HexColor("#222222")
GRIS3  = colors.HexColor("#2e2e2e")
GRIS4  = colors.HexColor("#444444")
GRIS5  = colors.HexColor("#777777")
GRISC  = colors.HexColor("#bbbbbb")
VERDE  = colors.HexColor("#3ecf8e")
AMBAR  = colors.HexColor("#f5a623")
AZUL   = colors.HexColor("#4a90d9")  # legacy — evitar junto a AMBAR
TURQ   = colors.HexColor("#16a085")  # alternativa a AZUL para mezclar con AMBAR
MAGENTA = colors.HexColor("#e8267e")  # para destacar líneas sobre heatmap caliente

W, H = landscape(A4)  # 841.89 × 595.28 pt
MX = 36               # margen lateral

LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "logo.png")


def _logo_transparente():
    """Carga el escudo y vuelve transparente todo lo que sea casi negro.
    Devuelve un PIL Image (o None si no se puede). Se cachea en módulo."""
    if not os.path.exists(LOGO_PATH):
        return None
    try:
        from PIL import Image
        im = Image.open(LOGO_PATH).convert("RGBA")
        pix = list(im.getdata())
        out = [
            (0, 0, 0, 0) if (r + g + b) < 36 else (r, g, b, a)
            for r, g, b, a in pix
        ]
        im.putdata(out)
        return im
    except Exception:
        return None


_LOGO_PIL = _logo_transparente()


# ─── Primitivas de página ────────────────────────────────────────────────────

def fondo(c, color=NEGRO):
    c.setFillColor(color)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def header_pagina(c, titulo, subtitulo="", partido=""):
    """Header común de página interna."""
    c.setFillColor(GRIS1)
    c.rect(0, H - 46, W, 46, fill=1, stroke=0)
    c.setFillColor(ROJO)
    c.rect(0, H - 49, W, 3, fill=1, stroke=0)

    if _LOGO_PIL is not None:
        try:
            c.drawImage(ImageReader(_LOGO_PIL), 12, H - 46, width=30, height=38, mask="auto", preserveAspectRatio=False)
        except Exception:
            pass

    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(52, H - 22, titulo.upper())
    c.setFillColor(GRISC)
    c.setFont("Helvetica", 8)
    c.drawString(52, H - 35, subtitulo.upper())

    if partido:
        c.setFillColor(ROJO)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(W - 14, H - 22, partido.upper())
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - 14, H - 36, datetime.now().strftime("%d/%m/%Y · %H:%M"))


def footer(c, num_pag):
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 7.5)
    c.drawString(MX, 18, "Departamento de Análisis de Datos · CARP · Fútbol Formativo")
    c.drawRightString(W - MX, 18, f"Página {num_pag}")


def section_title(c, x, y, texto, ancho=None, color=ROJO):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, texto.upper())
    c.setStrokeColor(GRIS3)
    c.setLineWidth(0.5)
    c.line(x, y - 5, (x + ancho) if ancho else (W - MX), y - 5)


# ─── Componentes ─────────────────────────────────────────────────────────────

def kpi_card(c, x, y, w, h, label, valor, sub="", color_val=BLANCO):
    c.setFillColor(GRIS1)
    c.setStrokeColor(GRIS3)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 10, y + h - 14, label.upper())
    c.setFillColor(color_val)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(x + 10, y + h - 40, str(valor))
    if sub:
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 7.5)
        c.drawString(x + 10, y + 8, sub)


def kpi_row(c, x, y, w, items):
    """Renderiza una fila de N KPIs con ancho `w` total."""
    n = len(items)
    gap = 8
    cw = (w - gap * (n - 1)) / n
    ch = 64
    for i, it in enumerate(items):
        cx = x + i * (cw + gap)
        kpi_card(c, cx, y - ch, cw, ch, it["label"], it["val"], it.get("sub", ""), it.get("color", BLANCO))
    return ch


def compare_bar(c, x, y, w, label, v_river, v_rival):
    """Barra comparativa River (rojo) vs Rival (gris) con valores."""
    tot = max(1, v_river + v_rival)
    pct_river = v_river / tot
    bar_h = 8
    inner_w = w - 130
    # Label central
    c.setFillColor(GRISC)
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + w / 2, y + 18, label)
    # Valor River
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(x + 38, y + 4, str(v_river))
    # Valor Rival
    c.setFillColor(GRISC)
    c.drawString(x + w - 38, y + 4, str(v_rival))
    # Barra River (derecha→izquierda desde el centro)
    mid_x = x + w / 2
    river_w = (inner_w / 2) * pct_river
    rival_w = (inner_w / 2) * (v_rival / tot)
    c.setFillColor(ROJO)
    c.rect(mid_x - river_w, y, river_w, bar_h, fill=1, stroke=0)
    c.setFillColor(GRIS5)
    c.rect(mid_x, y, rival_w, bar_h, fill=1, stroke=0)
    # Línea central
    c.setStrokeColor(GRIS3)
    c.setLineWidth(0.3)
    c.line(mid_x, y - 2, mid_x, y + bar_h + 2)


def bloque_mini(c, x, y, w, h, label, val, color_val=BLANCO):
    c.setFillColor(GRIS1)
    c.setStrokeColor(GRIS3)
    c.setLineWidth(0.4)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(x + w / 2, y + h - 10, label.upper())
    c.setFillColor(color_val)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x + w / 2, y + 8, str(val))


def matriz_tabla(c, x, y, w, titulo, mat, filas, cols):
    """Tabla coloreada — Tipo × Carril."""
    if not mat:
        return 0
    filas = [f for f in filas if f in mat]
    cols = [col for col in cols if any(mat.get(f, {}).get(col) for f in filas)]
    if not filas or not cols:
        return 0

    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, titulo.upper())
    y_top = y - 14

    # Calcular max para intensidad
    mx = 0
    total = 0
    for f in filas:
        for col in cols:
            v = mat[f].get(col, 0)
            mx = max(mx, v)
            total += v

    row_h = 22
    col_w = (w - 90) / (len(cols) + 1)  # 90 = ancho de columna nombre fila
    # Header
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 7)
    for j, col in enumerate(cols):
        c.drawCentredString(x + 90 + j * col_w + col_w / 2, y_top - 10, col)
    c.drawCentredString(x + 90 + len(cols) * col_w + col_w / 2, y_top - 10, "TOTAL")

    for i, f in enumerate(filas):
        yy = y_top - 16 - (i + 1) * row_h
        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x + 84, yy + row_h / 2 - 3, f)
        fila_tot = 0
        for j, col in enumerate(cols):
            v = mat[f].get(col, 0)
            fila_tot += v
            cx = x + 90 + j * col_w
            inten = (v / mx) if mx else 0
            # Color de fondo con intensidad
            c.setFillColorRGB(0.8, 0, 0, alpha=0.12 + inten * 0.55)
            c.rect(cx + 1, yy + 1, col_w - 2, row_h - 2, fill=1, stroke=0)
            c.setFillColor(BLANCO)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(cx + col_w / 2, yy + row_h / 2 - 1, str(v))
            c.setFillColor(GRIS5)
            c.setFont("Helvetica", 6.5)
            pct = round(v / total * 100) if total else 0
            c.drawCentredString(cx + col_w / 2, yy + 3, f"{pct}%" if pct else "")
        # Total fila
        cx = x + 90 + len(cols) * col_w
        c.setFillColor(GRIS2)
        c.rect(cx + 1, yy + 1, col_w - 2, row_h - 2, fill=1, stroke=0)
        c.setFillColor(GRISC)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(cx + col_w / 2, yy + row_h / 2 - 1, str(fila_tot))

    return 14 + 16 + row_h * len(filas) + 8


def lista_goles(c, x, y, w, goles, max_items=8):
    """Lista compacta de goles."""
    if not goles:
        c.setFillColor(GRIS5)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(x, y, "Sin goles registrados.")
        return 20
    row_h = 18
    for i, g in enumerate(goles[:max_items]):
        yy = y - i * row_h
        c.setFillColor(GRIS1)
        c.setStrokeColor(GRIS3)
        c.setLineWidth(0.3)
        c.roundRect(x, yy - row_h + 2, w, row_h - 2, 3, fill=1, stroke=1)
        c.setFillColor(ROJO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 8, yy - 9, g.get("minuto", "—"))
        eq_color = ROJO if g.get("equipo") == "Propio" else GRIS5
        c.setFillColor(eq_color)
        c.setFont("Helvetica-Bold", 7.5)
        eq_lbl = "RIVER" if g.get("equipo") == "Propio" else "RIVAL"
        c.drawString(x + 58, yy - 9, eq_lbl)
        c.setFillColor(BLANCO)
        c.setFont("Helvetica", 8)
        c.drawString(x + 110, yy - 9, f"{g.get('tipo','—')} · {g.get('carril','—')}")
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 7.5)
        c.drawRightString(x + w - 8, yy - 9, str(g.get("remate", "")))
    return row_h * min(len(goles), max_items) + 4


def bullet_lectura(c, x, y, w, bullets):
    """Lista con bullets rojos."""
    line_h = 16
    for i, b in enumerate(bullets):
        yy = y - i * line_h
        c.setFillColor(ROJO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, yy, "▸")
        c.setFillColor(BLANCO)
        c.setFont("Helvetica", 9.5)
        # Wrap simple — corte por palabras a aprox 92 chars / línea de w
        max_chars = int(w / 5.2)
        wrapped = _wrap(b, max_chars)
        for j, ln in enumerate(wrapped):
            c.drawString(x + 12, yy - j * 11, ln)
        # Si wrapped es > 1, ajustar próximo
        if len(wrapped) > 1:
            y -= (len(wrapped) - 1) * 11
    return line_h * len(bullets) + 6


def _wrap(text, max_chars):
    if len(text) <= max_chars:
        return [text]
    words = text.split(" ")
    out, cur = [], ""
    for w_ in words:
        if len(cur) + len(w_) + 1 <= max_chars:
            cur = (cur + " " + w_).strip()
        else:
            if cur:
                out.append(cur)
            cur = w_
    if cur:
        out.append(cur)
    return out


# ─── CANCHA DE FÚTBOL VECTORIAL ──────────────────────────────────────────────

def _cancha(c, x, y, w, h, fill_bg=GRIS0, line_col=GRIS4, lw=0.6):
    """Dibuja una cancha 120×80 escalada a (x,y,w,h). Atacando a la derecha.
    y_data=0 → fondo bajo (PDF y bajo); y_data=80 → fondo alto."""
    sx = lambda px: x + px / 120.0 * w
    sy = lambda py: y + (py / 80.0) * h

    c.setFillColor(fill_bg)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setStrokeColor(line_col); c.setLineWidth(lw); c.setFillColor(line_col)
    # Outer
    c.rect(x, y, w, h, fill=0, stroke=1)
    # Halfway
    c.line(sx(60), y, sx(60), y + h)
    # Center circle
    rc = w * 9.15 / 120
    c.setStrokeColor(line_col); c.circle(sx(60), sy(40), rc, fill=0, stroke=1)
    c.setFillColor(line_col); c.circle(sx(60), sy(40), max(0.8, w * 0.004), fill=1, stroke=0)
    # Áreas y manchones — derecha
    c.setFillColor(fill_bg)
    c.rect(sx(102), sy(18), w * 18 / 120, h * 44 / 80, fill=0, stroke=1)
    c.rect(sx(114), sy(30), w * 6 / 120,  h * 20 / 80, fill=0, stroke=1)
    c.setFillColor(line_col); c.circle(sx(108), sy(40), max(0.7, w * 0.003), fill=1, stroke=0)
    # Áreas izquierda
    c.setFillColor(fill_bg)
    c.rect(sx(0), sy(18), w * 18 / 120, h * 44 / 80, fill=0, stroke=1)
    c.rect(sx(0), sy(30), w * 6 / 120,  h * 20 / 80, fill=0, stroke=1)
    c.setFillColor(line_col); c.circle(sx(12), sy(40), max(0.7, w * 0.003), fill=1, stroke=0)
    # Arcos
    c.setFillColor(line_col)
    c.rect(sx(120), sy(36), w * 0.5 / 120, h * 8 / 80, fill=1, stroke=0)
    c.rect(sx(0) - w * 0.5 / 120, sy(36), w * 0.5 / 120, h * 8 / 80, fill=1, stroke=0)
    # → ATAQUE
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 6)
    c.drawRightString(sx(118), y + 4, "→ ATAQUE")
    return sx, sy


def _thermal(ratio):
    """Escala térmica discreta: devuelve (color, alpha) o None si la celda no se renderiza."""
    if ratio < 0.15:        return None
    if ratio < 0.35:        return (colors.HexColor("#7a4a1c"), 0.32)  # marrón / amber muy oscuro
    if ratio < 0.55:        return (colors.HexColor("#cf7a1f"), 0.50)  # naranja
    if ratio < 0.75:        return (colors.HexColor("#dc3030"), 0.65)  # rojo medio
    if ratio < 0.92:        return (colors.HexColor("#ff1a1a"), 0.80)  # rojo intenso
    return (colors.HexColor("#ffd02a"), 0.92)                          # hot spot (top 8%)


def _cancha_heatmap(c, x, y, w, h, acciones, color_hex="#CC0000", thermal=False):
    """Heatmap por binning 12×8. thermal=True usa escala graduada que destaca los hot spots."""
    if not acciones:
        return
    cellW, cellH = 10.0, 10.0
    bins = {}
    for a in acciones:
        ax = max(0, min(119.999, a["x"]))
        ay = max(0, min(79.999, a["y"]))
        cx_ = int(ax // cellW)
        cy_ = int(ay // cellH)
        bins[(cx_, cy_)] = bins.get((cx_, cy_), 0) + 1
    mx = max(bins.values())
    single = colors.HexColor(color_hex)
    cellPxW = w / 12.0
    cellPxH = h / 8.0
    for (cx_, cy_), count in bins.items():
        ratio = count / mx
        if thermal:
            t = _thermal(ratio)
            if t is None:
                continue
            color, op = t
        else:
            color = single
            op = 0.10 + ratio * 0.60
        c.saveState()
        try: c.setFillAlpha(op)
        except Exception: pass
        c.setFillColor(color)
        c.rect(x + cx_ * cellPxW, y + cy_ * cellPxH, cellPxW, cellPxH, fill=1, stroke=0)
        c.restoreState()


def _cancha_punto(c, x, y, w, h, px, py, radio, color, alpha=1.0, label=None):
    sxv = x + px / 120.0 * w
    syv = y + (py / 80.0) * h
    c.saveState()
    try:
        c.setFillAlpha(alpha)
    except Exception:
        pass
    c.setFillColor(color)
    c.circle(sxv, syv, radio, fill=1, stroke=0)
    c.restoreState()
    if label:
        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 5.5)
        c.drawString(sxv + radio + 1, syv - 1.5, str(label))


def _cancha_flecha(c, x, y, w, h, p0, p1, color, lw=1):
    sxv = lambda px: x + px / 120.0 * w
    syv = lambda py: y + (py / 80.0) * h
    c.setStrokeColor(color); c.setLineWidth(lw)
    c.line(sxv(p0[0]), syv(p0[1]), sxv(p1[0]), syv(p1[1]))
    c.setFillColor(color)
    c.circle(sxv(p1[0]), syv(p1[1]), 1.4, fill=1, stroke=0)


def _lineas_equipo(c, x, y, w, h, lineas):
    """Marcadores de líneas (defensa/mediocampo/delantera) sobre la cancha.
    `lineas` = [(nombre, x_promedio, color, jugadores_list), ...]
    """
    for nombre, cg_x, color, jugadores in lineas:
        sx_ = x + cg_x / 120.0 * w
        c.saveState()
        try: c.setStrokeAlpha(0.95)
        except: pass
        # Línea punteada vertical con grosor reforzado
        c.setStrokeColor(color); c.setLineWidth(2.2)
        c.setDash(5, 3)
        c.line(sx_, y + 4, sx_, y + h - 4)
        c.setDash()
        c.restoreState()
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(sx_, y + h + 4, nombre.upper())
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(sx_, y + h - 8, f"x̄ = {cg_x:.0f}")


# ─── PIE CHART simple ────────────────────────────────────────────────────────

def _pie(c, cx, cy, r, segments, titulo=""):
    """segments = [(label, value, color), ...]"""
    total = sum(s[1] for s in segments)
    if total <= 0:
        return
    from reportlab.graphics.shapes import Path, Drawing
    import math
    # Manual arcs via canvas paths
    ang0 = math.pi / 2  # empezar arriba
    for label, val, color in segments:
        if val <= 0:
            continue
        ang1 = ang0 - (val / total) * 2 * math.pi
        # Aprox con muchos puntos
        path = c.beginPath()
        path.moveTo(cx, cy)
        steps = max(8, int(abs(ang0 - ang1) / 0.08))
        for i in range(steps + 1):
            t = ang0 + (ang1 - ang0) * (i / steps)
            path.lineTo(cx + r * math.cos(t), cy + r * math.sin(t))
        path.close()
        c.setFillColor(color); c.setStrokeColor(NEGRO); c.setLineWidth(0.5)
        c.drawPath(path, fill=1, stroke=1)
        ang0 = ang1
    # Centro vacío para dona
    c.setFillColor(GRIS0); c.setStrokeColor(GRIS4); c.setLineWidth(0.4)
    c.circle(cx, cy, r * 0.45, fill=1, stroke=1)
    if titulo:
        c.setFillColor(GRIS5)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx, cy - 3, titulo.upper())
    # Leyenda vertical (evita superposición entre pies)
    visibles = [(l, v, col) for l, v, col in segments if v > 0]
    legend_y0 = cy - r - 14
    for i, (label, val, color) in enumerate(visibles):
        pct = round(val / total * 100)
        yy = legend_y0 - i * 11
        c.setFillColor(color)
        c.rect(cx - r, yy, 7, 7, fill=1, stroke=0)
        c.setFillColor(BLANCO)
        c.setFont("Helvetica", 7)
        c.drawString(cx - r + 11, yy + 1, f"{label}  {pct}% ({val})")


# ─── Análisis textual (reglas) ───────────────────────────────────────────────

def lectura_equipo(col, etiqueta="del partido"):
    lp = col.get("llegadas_prop", {})
    lr = col.get("llegadas_riv", {})
    gp = col.get("goles_propios", {})
    cp = col.get("centros_prop", {})
    sg = col.get("sit_gol_prop", 0)
    out = []

    if lp.get("total") and lr.get("total"):
        ratio = lp["total"] / lr["total"]
        if ratio >= 1.5:
            out.append(f"River dominó territorialmente: {lp['total']} llegadas contra {lr['total']} del rival.")
        elif ratio <= 0.7:
            out.append(f"El rival fue superior en generación: {lr['total']} llegadas contra {lp['total']} de River.")
        else:
            out.append(f"Partido parejo en llegadas ({lp['total']} River — {lr['total']} rival).")

    carriles = [("izquierda", lp.get("izq", 0)), ("eje", lp.get("eje", 0)), ("derecha", lp.get("der", 0))]
    tot_car = sum(v for _, v in carriles)
    if tot_car:
        ganador = max(carriles, key=lambda x: x[1])
        pct = round(ganador[1] / tot_car * 100)
        if pct >= 45:
            out.append(f"El equipo concentró el {pct}% de sus llegadas por el carril {ganador[0]} ({ganador[1]} de {tot_car}).")
        else:
            out.append(f"Llegadas distribuidas entre los tres carriles (izq {lp.get('izq',0)}, eje {lp.get('eje',0)}, der {lp.get('der',0)}).")

    tot_tipo = lp.get("asociado", 0) + lp.get("directo", 0) + lp.get("detenidas", 0)
    if tot_tipo:
        aso_pct = round(lp.get("asociado", 0) / tot_tipo * 100)
        if aso_pct >= 60:
            out.append(f"Predominó el juego asociado en las llegadas ({aso_pct}%).")
        elif aso_pct <= 30:
            out.append(f"El equipo apostó al juego directo (sólo {aso_pct}% asociado).")

    if sg:
        if gp.get("total"):
            conv = round(gp["total"] / sg * 100)
            out.append(f"Conversión de {conv}% — {gp['total']} goles en {sg} situaciones de gol.")
        else:
            out.append(f"Generó {sg} situaciones de gol pero no las concretó.")

    if col.get("recuperadas") or col.get("perdidas"):
        bal = col.get("recuperadas", 0) - col.get("perdidas", 0)
        if abs(bal) >= 5:
            sign = "positivo" if bal > 0 else "negativo"
            out.append(f"Balance {sign} de balones: {col.get('recuperadas',0)} recuperadas vs {col.get('perdidas',0)} pérdidas ({'+' if bal>0 else ''}{bal}).")

    if cp.get("total"):
        ef = round(cp.get("completos", 0) / cp["total"] * 100) if cp["total"] else 0
        if ef >= 50:
            out.append(f"Centros eficientes: {cp.get('completos',0)}/{cp['total']} completados ({ef}%).")
        elif cp["total"] >= 5:
            out.append(f"Baja eficacia de centros ({cp.get('completos',0)}/{cp['total']}, {ef}%).")

    return out[:7]


def _calcular_lineas(todos_jug, min_minutos=20):
    """Detecta línea defensiva / mediocampo / delantera a partir de centros de gravedad."""
    jugadores = []
    for nombre, st in (todos_jug or {}).items():
        if (st.get("minutos") or 0) < min_minutos:
            continue
        if not (st.get("acciones_xy") or 0):
            continue
        jugadores.append((nombre, st.get("centro_grav_x", 0) or 0, st.get("centro_grav_y", 0) or 0))
    if len(jugadores) < 6:
        return []
    jugadores.sort(key=lambda j: j[1])
    n = len(jugadores)
    # Aprox: cuartil inferior = defensa, 2 cuartiles medios = mediocampo, superior = ataque
    n_def = max(3, n // 3)
    n_atk = max(2, n // 4)
    n_mid = n - n_def - n_atk
    if n_mid <= 0:
        n_mid = max(1, n - n_def - n_atk)
        n_atk = n - n_def - n_mid
    defensa = jugadores[:n_def]
    medio = jugadores[n_def:n_def + n_mid]
    ataque = jugadores[n_def + n_mid:]
    def avg(grp):
        return sum(j[1] for j in grp) / len(grp) if grp else 0
    return [
        ("Defensa", avg(defensa), VERDE, defensa),
        ("Mediocampo", avg(medio), BLANCO, medio),
        ("Ataque", avg(ataque), ROJO, ataque),
    ]


def _etiquetas_jugadores(todos_jug):
    """Genera etiquetas únicas: 'Cabral T.' / 'Cabral B.' cuando hay apellidos repetidos."""
    from collections import Counter
    apellidos = Counter()
    for nombre in (todos_jug or {}).keys():
        partes = nombre.split()
        if partes:
            apellidos[partes[-1].lower()] += 1
    out = {}
    for nombre in (todos_jug or {}).keys():
        partes = nombre.split()
        if not partes:
            out[nombre] = "?"
            continue
        apellido = partes[-1]
        if apellidos[apellido.lower()] > 1 and len(partes) > 1:
            inicial = partes[0][0].upper()
            out[nombre] = f"{apellido[:11]} {inicial}."
        else:
            out[nombre] = apellido[:13]
    return out


def _pagina_mapa_territorial(c, agg, todos_jug, eventos, n_pag, partido_label):
    fondo(c)
    rival = _rival_de(partido_label)
    subtitulo = "Posición media por línea del equipo"
    header_pagina(c, "Mapa territorial", subtitulo, partido_label)
    if rival:
        sub_w = c.stringWidth(subtitulo.upper(), "Helvetica", 8)
        c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawString(52 + sub_w + 12, H - 35, f"VS {rival.upper()[:24]}")

    # Cancha grande arriba (sin heatmap — sólo posiciones y líneas)
    pitch_x, pitch_y, pitch_w, pitch_h = MX, H - 360, W - 2 * MX, 270
    _cancha(c, pitch_x, pitch_y, pitch_w, pitch_h)
    # Líneas del equipo (def/medio/ataque)
    lineas = _calcular_lineas(todos_jug)
    _lineas_equipo(c, pitch_x, pitch_y, pitch_w, pitch_h, lineas)
    # Dots de centros de gravedad de cada jugador
    sx = lambda px: pitch_x + px / 120.0 * pitch_w
    sy = lambda py: pitch_y + (py / 80.0) * pitch_h
    line_color_por_jug = {}
    for nombre_l, cg_x_l, color_l, jugs_l in lineas:
        for j in jugs_l:
            line_color_por_jug[j[0]] = color_l
    etiquetas = _etiquetas_jugadores(todos_jug)
    for nombre, st in (todos_jug or {}).items():
        if (st.get("minutos") or 0) < 20: continue
        cg_x = st.get("centro_grav_x", 0) or 0
        cg_y = st.get("centro_grav_y", 0) or 0
        if cg_x == 0 and cg_y == 0: continue
        color_dot = line_color_por_jug.get(nombre, BLANCO)
        c.setFillColor(NEGRO)
        c.circle(sx(cg_x), sy(cg_y), 6, fill=1, stroke=0)
        c.setFillColor(color_dot)
        c.circle(sx(cg_x), sy(cg_y), 5, fill=1, stroke=0)
        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(sx(cg_x) + 8, sy(cg_y) - 2, etiquetas.get(nombre, nombre)[:14])

    # Resumen de líneas debajo de la cancha
    y_box = pitch_y - 90
    section_title(c, MX, y_box + 80, "Composición por líneas")
    n_box = len(lineas) or 1
    box_w = (W - 2 * MX - (n_box - 1) * 10) / n_box
    for i, (nombre, cg_x, color, jugs) in enumerate(lineas):
        bx = MX + i * (box_w + 10)
        c.setFillColor(GRIS1); c.setStrokeColor(color); c.setLineWidth(1.2)
        c.roundRect(bx, y_box, box_w, 70, 6, fill=1, stroke=1)
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(bx + 12, y_box + 55, nombre.upper())
        c.setFillColor(GRIS5)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(bx + 12, y_box + 42, f"POSICIÓN MEDIA  ·  x̄ = {cg_x:.0f}")
        c.setFillColor(BLANCO)
        c.setFont("Helvetica", 7.5)
        nombres = ", ".join(etiquetas.get(j[0], j[0].split()[-1]) for j in jugs[:6])
        for j, ln in enumerate(_wrap(nombres, 38)[:2]):
            c.drawString(bx + 12, y_box + 28 - j * 10, ln)

    footer(c, n_pag)
    c.showPage()


def _pagina_acciones_valor(c, agg, eventos, n_pag, partido_label):
    fondo(c)
    header_pagina(c, "Acciones de alto valor", "Pases filtrados y zonas de pérdida/recuperación", partido_label)

    half_w = (W - 2 * MX - 20) / 2
    pitch_h = 200

    # Izquierda — Pases filtrados
    px1, py1 = MX, H - 280
    section_title(c, px1, py1 + 210, "Pases filtrados", half_w)
    _cancha(c, px1, py1, half_w, pitch_h)
    pf = eventos.get("pases_filtrados", [])
    comp = sum(1 for p in pf if p.get("completo"))
    inc = len(pf) - comp
    for p in pf:
        color = VERDE if p.get("completo") else ROJO
        _cancha_punto(c, px1, py1, half_w, pitch_h, p["x"], p["y"], 1.8, color, 0.85)
        if p.get("completo") and p.get("xe") is not None and p.get("ye") is not None:
            _cancha_flecha(c, px1, py1, half_w, pitch_h, (p["x"], p["y"]), (p["xe"], p["ye"]), VERDE, 0.6)
    # Mini stats abajo de la cancha izq
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 8)
    c.drawString(px1, py1 - 14, f"Total: {len(pf)}    ·    Completos: {comp}    ·    Incompletos: {inc}")
    if pf:
        ef = round(comp / len(pf) * 100)
        c.setFillColor(VERDE if ef >= 60 else AMBAR if ef >= 40 else ROJO)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(px1 + 220, py1 - 14, f"Efectividad: {ef}%")

    # Derecha — Pérdidas vs Recuperadas (mismo cancha, dos colores)
    px2, py2 = MX + half_w + 20, H - 280
    section_title(c, px2, py2 + 210, "Pérdidas (rojo) vs Recuperadas (verde)", half_w)
    _cancha(c, px2, py2, half_w, pitch_h)
    _cancha_heatmap(c, px2, py2, half_w, pitch_h, eventos.get("perdidas_coords", []), color_hex="#CC0000")
    _cancha_heatmap(c, px2, py2, half_w, pitch_h, eventos.get("recuperadas_coords", []), color_hex="#3ecf8e")
    # Altura promedio del bloque defensivo (avg x de recuperadas)
    rec = eventos.get("recuperadas_coords", [])
    per = eventos.get("perdidas_coords", [])
    if rec:
        h_def = sum(r["x"] for r in rec) / len(rec)
        sx_ = px2 + h_def / 120 * half_w
        c.setStrokeColor(VERDE); c.setLineWidth(0.8)
        c.saveState()
        c.setDash(3, 2)
        c.line(sx_, py2, sx_, py2 + pitch_h)
        c.restoreState()
        c.setFillColor(VERDE)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(sx_ + 2, py2 + pitch_h - 8, f"BLOQUE x̄={h_def:.0f}")
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 8)
    c.drawString(px2, py2 - 14, f"Pérdidas: {len(per)}    ·    Recuperadas: {len(rec)}")
    if rec and per:
        bal = len(rec) - len(per)
        c.setFillColor(VERDE if bal > 0 else ROJO if bal < 0 else AMBAR)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(px2 + 220, py2 - 14, f"Balance: {'+' if bal>0 else ''}{bal}")

    # Pie charts abajo: tipo + carril
    col = agg["colectivas"]
    lp = col["llegadas_prop"]
    y_pie = py2 - 90
    section_title(c, MX, y_pie + 60, "Distribución de llegadas propias")
    # Pie 1: Tipo
    _pie(c, MX + 60, y_pie + 20, 32, [
        ("Asociado", lp.get("asociado", 0), ROJO),
        ("Directo", lp.get("directo", 0), AMBAR),
        ("Detenidas", lp.get("detenidas", 0), GRISC),
    ], "Tipo")
    # Pie 2: Carril
    _pie(c, MX + 260, y_pie + 20, 32, [
        ("Izq", lp.get("izq", 0), ROJO),
        ("Eje", lp.get("eje", 0), AMBAR),
        ("Der", lp.get("der", 0), GRISC),
    ], "Carril")
    # Pie 3: Amplitud
    _pie(c, MX + 460, y_pie + 20, 32, [
        ("1C", lp.get("1carril", 0), GRISC),
        ("2C", lp.get("2carriles", 0), AMBAR),
        ("3C", lp.get("3carriles", 0), ROJO),
    ], "Amplitud")

    footer(c, n_pag)
    c.showPage()


# ─── INFORME COLECTIVO ───────────────────────────────────────────────────────

def _cover_colectivo(c, agg):
    fondo(c, NEGRO)
    # Banda roja superior
    c.setFillColor(ROJO)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)
    # Logo grande con transparencia
    if _LOGO_PIL is not None:
        try:
            c.drawImage(ImageReader(_LOGO_PIL), MX, H - 112, width=58, height=70, mask="auto", preserveAspectRatio=False)
        except Exception:
            pass
    # Brand
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MX + 76, H - 60, "DEPARTAMENTO DE ANÁLISIS DE DATOS")
    c.setFillColor(ROJO)
    c.drawString(MX + 76, H - 73, "CLUB ATLÉTICO RIVER PLATE")
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 7.5)
    c.drawString(MX + 76, H - 92, "FÚTBOL FORMATIVO · INFORME COLECTIVO")

    # Título grande
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 44)
    titulo = "ANÁLISIS"
    c.drawString(MX, H - 200, titulo)
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MX, H - 235, "COLECTIVO")

    # Partido
    partido = agg["colectivas"].get("partido", "")
    c.setFillColor(BLANCO)
    c.setFont("Helvetica", 15)
    if "Acumulado" in partido:
        nombres = agg.get("partidos", [])
        c.drawString(MX, H - 270, f"ACUMULADO · {len(nombres)} PARTIDOS")
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 10)
        for i, n in enumerate(nombres[:6]):
            c.drawString(MX, H - 295 - i * 14, f"·  {n}")
    else:
        c.drawString(MX, H - 270, partido.upper())

    # Score
    gp = agg["colectivas"]["goles_propios"]["total"]
    gr = agg["colectivas"]["goles_rivales"]["total"]
    cx = W - 230
    c.setFillColor(GRIS1)
    c.setStrokeColor(ROJO)
    c.setLineWidth(1.5)
    c.roundRect(cx, H - 280, 180, 130, 12, fill=1, stroke=1)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(cx + 45, H - 165, "RIVER")
    c.drawCentredString(cx + 135, H - 165, "RIVAL")
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 60)
    c.drawCentredString(cx + 45, H - 230, str(gp))
    c.setFillColor(GRISC)
    c.drawCentredString(cx + 135, H - 230, str(gr))
    c.setFillColor(GRIS4)
    c.setFont("Helvetica", 40)
    c.drawCentredString(cx + 90, H - 225, "–")

    # Footer cover
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 8)
    c.drawString(MX, 30, f"Generado · {datetime.now().strftime('%d de %B de %Y · %H:%M')}")
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - MX, 30, "CONFIDENCIAL · USO INTERNO")

    c.showPage()


def _rival_de(partido):
    """Extrae el nombre del rival desde 'River vs X' o 'vs X'."""
    if not partido:
        return ""
    import re
    m = re.search(r'\bvs\.?\s+(.+?)$', partido, re.IGNORECASE)
    return m.group(1).strip().title() if m else ""


def _pagina_resumen(c, partido_data, n_pag, subtitulo="Resumen del partido"):
    fondo(c)
    col = partido_data["colectivas"]
    partido_nom = col.get("partido", "")
    rival_nom = _rival_de(partido_nom) or "RIVAL"
    header_pagina(c, "Resumen", subtitulo, partido_nom)

    gp = col["goles_propios"]["total"]
    gr = col["goles_rivales"]["total"]
    lp = col["llegadas_prop"]
    lr = col["llegadas_riv"]

    # Rival prominente al lado del subtítulo del header
    if rival_nom and rival_nom != "RIVAL":
        sub_w = c.stringWidth(subtitulo.upper(), "Helvetica", 8)
        c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawString(52 + sub_w + 12, H - 35, f"VS {rival_nom.upper()[:24]}")

    # Score box arriba
    c.setFillColor(GRIS1)
    c.setStrokeColor(GRIS3)
    c.setLineWidth(0.5)
    c.roundRect(MX, H - 130, W - 2 * MX, 60, 6, fill=1, stroke=1)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W / 2 - 60, H - 92, "RIVER")
    c.drawCentredString(W / 2 + 60, H - 92, "RIVAL")
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(W / 2 - 60, H - 122, str(gp))
    c.setFillColor(GRISC)
    c.drawCentredString(W / 2 + 60, H - 122, str(gr))
    c.setFillColor(GRIS4)
    c.setFont("Helvetica", 26)
    c.drawCentredString(W / 2, H - 120, "–")

    # 4 KPIs
    items = [
        {"label": "Llegadas", "val": lp.get("total", 0), "sub": f"{lr.get('total', 0)} del rival", "color": ROJO},
        {"label": "Sit. de Gol", "val": col.get("sit_gol_prop", 0), "sub": f"{col.get('sit_gol_riv', 0)} del rival", "color": AMBAR},
        {"label": "Remates al arco", "val": lp.get("tiros_arco", 0), "sub": f"{lr.get('tiros_arco', 0)} del rival", "color": ROJO},
        {"label": "Recuperadas", "val": col.get("recuperadas", 0), "sub": f"{col.get('perdidas', 0)} pérdidas", "color": VERDE},
    ]
    kpi_row(c, MX, H - 150, W - 2 * MX, items)

    # Comparativa River vs Rival
    y = H - 250
    section_title(c, MX, y, "Comparativa River vs Rival")
    rows = [
        ("Llegadas", lp.get("total", 0), lr.get("total", 0)),
        ("Situaciones de gol", col.get("sit_gol_prop", 0), col.get("sit_gol_riv", 0)),
        ("Remates al arco", lp.get("tiros_arco", 0), lr.get("tiros_arco", 0)),
        ("Centros", col.get("centros_prop", {}).get("total", 0), col.get("centros_riv", {}).get("total", 0)),
        ("Detenidas", col.get("detenidas_prop", 0), col.get("detenidas_riv", 0)),
        ("Salidas", col.get("salidas_prop", {}).get("total", 0), col.get("salidas_riv", {}).get("total", 0)),
    ]
    by = y - 30
    bar_h_total = 26
    for i, (lbl, vr, vv) in enumerate(rows):
        compare_bar(c, MX, by - i * bar_h_total, W - 2 * MX, lbl, vr, vv)

    # Lista de goles (lado derecho de la página) — desplazada a otra columna no, mejor abajo
    y2 = by - len(rows) * bar_h_total - 30
    section_title(c, MX, y2, f"Goles · {gp} – {gr}")
    lista_goles(c, MX, y2 - 18, W - 2 * MX, partido_data.get("goles", []), max_items=6)

    footer(c, n_pag)
    c.showPage()


def _pagina_ofensivo(c, col, n_pag, titulo_partido):
    fondo(c)
    rival = _rival_de(titulo_partido)
    subtitulo = "Eficiencia y distribución de llegadas"
    header_pagina(c, "Ofensivo", subtitulo, titulo_partido)
    if rival:
        sub_w = c.stringWidth(subtitulo.upper(), "Helvetica", 8)
        c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawString(52 + sub_w + 12, H - 35, f"VS {rival.upper()[:24]}")

    lp = col["llegadas_prop"]
    gp = col["goles_propios"]
    cp = col["centros_prop"]
    sg = col.get("sit_gol_prop", 0)
    tot = lp.get("total", 0)
    goles = gp.get("total", 0)
    conv = round(goles / sg * 100) if sg else 0
    gen = round(sg / tot * 100) if tot else 0
    ef_rem = round(lp.get("tiros_arco", 0) / tot * 100) if tot else 0
    ef_cen = round(cp.get("completos", 0) / cp.get("total", 1) * 100) if cp.get("total") else 0

    # KPIs eficiencia
    items = [
        {"label": "Conversión", "val": f"{conv}%", "sub": f"{goles} gol / {sg} sit.gol",
         "color": VERDE if conv >= 25 else AMBAR if conv >= 12 else ROJO},
        {"label": "Generación", "val": f"{gen}%", "sub": f"{sg} sit.gol / {tot} llegadas",
         "color": VERDE if gen >= 30 else AMBAR if gen >= 15 else ROJO},
        {"label": "Remate al arco", "val": f"{ef_rem}%", "sub": f"{lp.get('tiros_arco',0)} / {tot}",
         "color": VERDE if ef_rem >= 40 else AMBAR if ef_rem >= 25 else ROJO},
        {"label": "Centros completos", "val": f"{ef_cen}%", "sub": f"{cp.get('completos',0)}/{cp.get('total',0)}",
         "color": VERDE if ef_cen >= 40 else AMBAR if ef_cen >= 25 else ROJO},
    ]
    kpi_row(c, MX, H - 130, W - 2 * MX, items)

    # Matrices
    section_title(c, MX, H - 220, "Distribución de llegadas · Tipo × Carril")
    half_w = (W - 2 * MX - 24) / 2
    matriz_tabla(c, MX, H - 250, half_w, "Por tipo de jugada", col.get("matriz_llegadas", {}),
                 ["Asociado", "Directo", "Detenidas"], ["Izquierda", "Eje", "Derecha"])
    matriz_tabla(c, MX + half_w + 24, H - 250, half_w, "Por amplitud usada", col.get("matriz_amp_carril", {}),
                 ["1 Carril", "2 Carriles", "3 Carriles"], ["Izquierda", "Eje", "Derecha"])

    # Mini-grid: llegadas detalle por tipo / carril (propias y rivales)
    y_mini = H - 420
    section_title(c, MX, y_mini, "Llegadas propias · detalle")
    mb_y = y_mini - 60
    mini_w = (W - 2 * MX - 5 * 6) / 6
    minis = [
        ("Asociado", lp.get("asociado", 0)),
        ("Directo", lp.get("directo", 0)),
        ("Detenidas", lp.get("detenidas", 0)),
        ("Eje", lp.get("eje", 0)),
        ("Izquierda", lp.get("izq", 0)),
        ("Derecha", lp.get("der", 0)),
    ]
    for i, (lbl, v) in enumerate(minis):
        bloque_mini(c, MX + i * (mini_w + 6), mb_y, mini_w, 50, lbl, v, ROJO)

    footer(c, n_pag)
    c.showPage()


def _pagina_plantel(c, agg, n_pag):
    fondo(c)
    partido = agg["colectivas"].get("partido", "")
    header_pagina(c, "Plantel", "Minutos jugados y cambios", partido)

    minutos = agg.get("minutos", [])
    cambios_raw = agg.get("cambios", [])

    # Limpieza de cambios: sacar same-player swaps, ordenar por partido + minuto
    def _parse_min(m):
        # "[partido] 12'34\"" o "12'34\""
        s = m
        if s.startswith("["):
            i = s.find("]")
            if i != -1: s = s[i+1:].strip()
        try:
            mins, rest = s.split("'", 1)
            secs = rest.replace('"', '').strip() or "0"
            return int(mins) * 60 + int(secs)
        except Exception:
            return 0
    def _partido_de(m):
        if m.startswith("["):
            i = m.find("]")
            if i != -1: return m[1:i]
        return ""
    cambios = []
    for ch in cambios_raw:
        sale = (ch.get("sale") or "—").strip()
        entra = (ch.get("entra") or "—").strip()
        if sale == entra and sale != "—":
            continue
        if sale == "?": sale = "—"
        if entra == "?": entra = "—"
        cambios.append({**ch, "sale": sale, "entra": entra,
                        "_part": _partido_de(ch.get("minuto", "")),
                        "_sec": _parse_min(ch.get("minuto", ""))})
    cambios.sort(key=lambda x: (x.get("_part", ""), x.get("_sec", 0)))

    # Minutos por jugador — barras
    section_title(c, MX, H - 90, f"Minutos por jugador ({len(minutos)})")
    if minutos:
        max_m = max(p.get("minutos", 0) or 0 for p in minutos) or 90
        col_a = MX
        col_b = MX + (W - 2 * MX) / 2 + 10
        mid = len(minutos) // 2 + len(minutos) % 2
        row_h = 16
        for i, p in enumerate(minutos):
            col_x = col_a if i < mid else col_b
            idx = i if i < mid else i - mid
            yy = H - 115 - idx * row_h
            es_tit = p.get("condicion") == "Titular"
            c.setFillColor(ROJO if es_tit else GRIS5)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(col_x, yy, p.get("jugador", "")[:22])
            # Barra
            bw = (W - 2 * MX) / 2 - 100
            bar_x = col_x + 110
            c.setFillColor(GRIS2)
            c.rect(bar_x, yy - 2, bw, 6, fill=1, stroke=0)
            fill = (p.get("minutos", 0) or 0) / max(1, max_m) * bw
            c.setFillColor(ROJO if es_tit else GRIS5)
            c.rect(bar_x, yy - 2, fill, 6, fill=1, stroke=0)
            c.setFillColor(BLANCO)
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(col_x + (W - 2 * MX) / 2 - 5, yy, f"{p.get('minutos',0)}m")

    # Cambios
    y_cam = H - 380
    section_title(c, MX, y_cam, f"Cambios ({len(cambios)})")
    if cambios:
        row_h = 18
        max_per_col = 8
        for i, ch in enumerate(cambios[:16]):
            col = i // max_per_col
            row = i % max_per_col
            cx = MX + col * (W / 2 - MX)
            yy = y_cam - 22 - row * row_h
            c.setFillColor(GRIS1)
            c.roundRect(cx, yy - 8, W / 2 - MX - 6, 16, 3, fill=1, stroke=0)
            # Sacar prefijo "[partido] " del minuto si existe
            m_raw = str(ch.get("minuto", "—"))
            partido_lbl = ""
            if m_raw.startswith("["):
                idx = m_raw.find("]")
                if idx != -1:
                    partido_lbl = m_raw[1:idx]
                    m_raw = m_raw[idx + 1:].strip()
            c.setFillColor(ROJO)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(cx + 8, yy - 4, m_raw[:8])
            # ↓ sale (rojo) — el que abandona el campo
            c.setFillColor(colors.HexColor("#ff6666"))
            c.setFont("Helvetica", 8)
            c.drawString(cx + 56, yy - 4, f"↓ {ch.get('sale','—')[:16]}")
            # ↑ entra (verde) — el que ingresa
            c.setFillColor(colors.HexColor("#66ff99"))
            c.drawString(cx + 170, yy - 4, f"↑ {ch.get('entra','—')[:16]}")
            if partido_lbl:
                c.setFillColor(GRIS5)
                c.setFont("Helvetica", 6)
                c.drawRightString(cx + (W / 2 - MX - 6) - 6, yy - 4, partido_lbl[:14])
    else:
        c.setFillColor(GRIS5)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(MX, y_cam - 24, "Sin cambios registrados.")

    footer(c, n_pag)
    c.showPage()


def _pagina_conclusiones(c, agg, n_pag, etiqueta="del partido"):
    fondo(c)
    partido = agg["colectivas"].get("partido", "")
    header_pagina(c, "Conclusiones", "Lectura táctica automática", partido)

    bullets = lectura_equipo(agg["colectivas"], etiqueta)
    section_title(c, MX, H - 90, f"📖 Lectura {etiqueta}")
    bullet_lectura(c, MX, H - 120, W - 2 * MX, bullets)

    # Highlight: cuadro grande con el dato más impactante
    col = agg["colectivas"]
    gp = col["goles_propios"]["total"]
    gr = col["goles_rivales"]["total"]
    resultado = "Victoria" if gp > gr else "Derrota" if gp < gr else "Empate"
    resultado_color = VERDE if gp > gr else ROJO if gp < gr else AMBAR

    y_caja = H - 300
    c.setFillColor(GRIS1)
    c.setStrokeColor(resultado_color)
    c.setLineWidth(2)
    c.roundRect(MX, y_caja - 90, W - 2 * MX, 90, 10, fill=1, stroke=1)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MX + 16, y_caja - 16, "RESULTADO FINAL")
    c.setFillColor(resultado_color)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(MX + 16, y_caja - 48, f"{resultado.upper()} {gp}–{gr}")
    # Key stats al lado
    c.setFillColor(GRISC)
    c.setFont("Helvetica", 9)
    lp = col["llegadas_prop"]
    lr = col["llegadas_riv"]
    stat_lines = [
        f"Llegadas: {lp.get('total',0)}  vs  {lr.get('total',0)}",
        f"Remates al arco: {lp.get('tiros_arco',0)}  vs  {lr.get('tiros_arco',0)}",
        f"Recup. / Pérdidas: {col.get('recuperadas',0)} / {col.get('perdidas',0)}",
    ]
    for i, sl in enumerate(stat_lines):
        c.drawString(W - 320, y_caja - 20 - i * 16, sl)

    footer(c, n_pag)
    c.showPage()


def generar_pdf_colectivo(resultados, agg, todos_jug=None, eventos=None, partidos_jug=None):
    """Genera informe colectivo completo con canchas + análisis por líneas."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    pag = 1
    partido_agg = agg["colectivas"].get("partido", "")

    _cover_colectivo(c, agg)

    if len(resultados) > 1:
        for idx, p in enumerate(resultados):
            partido_nom = p["colectivas"].get("partido", "")
            _pagina_resumen(c, p, pag, subtitulo="Resumen del partido")
            pag += 1
            _pagina_ofensivo(c, p["colectivas"], pag, partido_nom)
            pag += 1
            if partidos_jug and idx < len(partidos_jug):
                _pagina_mapa_territorial(c, p, partidos_jug[idx]["todos_jug"],
                                         partidos_jug[idx]["eventos"], pag, partido_nom)
                pag += 1
        _pagina_resumen(c, agg, pag, subtitulo=f"Acumulado · {len(resultados)} partidos")
        pag += 1
        _pagina_ofensivo(c, agg["colectivas"], pag, "Acumulado")
        pag += 1
        if todos_jug and eventos:
            _pagina_mapa_territorial(c, agg, todos_jug, eventos, pag, "Acumulado")
            pag += 1
    else:
        partido_nom = resultados[0]["colectivas"].get("partido", "")
        _pagina_resumen(c, resultados[0], pag)
        pag += 1
        _pagina_ofensivo(c, resultados[0]["colectivas"], pag, partido_nom)
        pag += 1
        if todos_jug and eventos:
            _pagina_mapa_territorial(c, resultados[0], todos_jug, eventos, pag, partido_nom)
            pag += 1

    if todos_jug and eventos:
        _pagina_acciones_valor(c, agg, eventos, pag, partido_agg)
        pag += 1

    _pagina_plantel(c, agg, pag)
    pag += 1
    _pagina_conclusiones(c, agg, pag,
                         etiqueta="acumulada" if len(resultados) > 1 else "del partido")

    c.save()
    return buf.getvalue()


# ─── ESTILO de juego (Python — paralelo a JS) ────────────────────────────────

ESTILOS_PY = [
    ('area',         'Atacante de área',     ['pct_area', 'remates_arco', 'goles', 'toques_area']),
    ('creativo',     'Generador creativo',   ['pases_clave', 'pases_filtrado', 'recep_lineas', 'asistencias']),
    ('conductor',    'Encarador / Conductor',['dao_plus', 'ruptura', 'regate_c', 'pct_progresivo']),
    ('distribuidor', 'Distribuidor',          ['pases_efect', 'pases_largo_c', 'pases_total']),
    ('recuperador',  'Recuperador alto',      ['recup_interv', 'recup_tras', 'pct_ultimo_tercio']),
    ('cierre',       'Cierre defensivo',      ['intercepciones', 'bloqueos', 'dad_plus', 'recup_posic']),
]


def detectar_estilo_py(ind, todos):
    if not todos:
        return None
    candidatos = [j for j in todos.values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) < 4:
        return None
    scores = []
    for id_, nombre, metricas in ESTILOS_PY:
        suma, n = 0, 0
        for m in metricas:
            valores = [j.get(m, 0) or 0 for j in candidatos]
            if max(valores) == 0: continue
            pct = _percentil_py(ind.get(m, 0) or 0, valores)
            suma += pct; n += 1
        if n:
            scores.append({'id': id_, 'nombre': nombre, 'pct': round(suma / n), 'metricas': metricas})
    scores.sort(key=lambda x: -x['pct'])
    if not scores or scores[0]['pct'] < 55:
        return {'nombre': 'Perfil mixto', 'pct': scores[0]['pct'] if scores else 0, 'detalle': 'Sin dominancia clara'}
    top = scores[0]
    detalle = f"Promedio percentil {top['pct']} en {' · '.join(top['metricas'][:3])}"
    if len(scores) > 1 and scores[1]['pct'] >= 60 and top['pct'] - scores[1]['pct'] < 8:
        return {'nombre': f"{top['nombre']} + {scores[1]['nombre']}", 'pct': top['pct'], 'detalle': detalle}
    return {'nombre': top['nombre'], 'pct': top['pct'], 'detalle': detalle}


# ─── PIZZA CHART de un jugador ──────────────────────────────────────────────

METRICAS_PIZZA_PDF = [
    ('pases_efect',     '% Pase',     '%'),
    ('pct_progresivo',  '% Progresivo','%'),
    ('pases_clave',     'P. clave',   ''),
    ('pases_filtrado',  'P. filtrado',''),
    ('pct_area',        '% Área',     '%'),
    ('remates_arco',    'Remates',    ''),
    ('recup_interv',    'Recup. act.',''),
    ('intercepciones',  'Intercep.',  ''),
]


def _pizza_jugador(c, cx, cy, r_out, ind, todos):
    candidatos = [j for j in (todos or {}).values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) < 4:
        return
    import math
    n = len(METRICAS_PIZZA_PDF)
    slice_ang = 2 * math.pi / n
    start_ang = -math.pi / 2
    r_min = r_out * 0.16

    # Anillos guía 25/50/75/100
    for rp in [0.25, 0.5, 0.75, 1.0]:
        rr = r_min + (r_out - r_min) * rp
        c.setStrokeColor(GRIS3); c.setLineWidth(0.4); c.setFillColor(GRIS0)
        c.circle(cx, cy, rr, fill=0, stroke=1)

    # Ejes radiales
    for i in range(n):
        ang = start_ang + i * slice_ang
        c.setStrokeColor(GRIS3); c.setLineWidth(0.3)
        c.line(cx, cy, cx + math.cos(ang) * r_out, cy + math.sin(ang) * r_out)

    # Slices
    for i, (k, label, unit) in enumerate(METRICAS_PIZZA_PDF):
        v = ind.get(k, 0) or 0
        valores = [j.get(k, 0) or 0 for j in candidatos]
        if max(valores) == 0: continue
        pct = _percentil_py(v, valores)
        r_s = r_min + (r_out - r_min) * (pct / 100.0)
        a0 = start_ang + i * slice_ang - slice_ang / 2
        a1 = start_ang + i * slice_ang + slice_ang / 2
        color = VERDE if pct >= 70 else (AMBAR if pct >= 40 else ROJO)
        path = c.beginPath()
        path.moveTo(cx, cy)
        steps = 16
        for s in range(steps + 1):
            ang = a0 + (a1 - a0) * (s / steps)
            path.lineTo(cx + math.cos(ang) * r_s, cy + math.sin(ang) * r_s)
        path.close()
        c.saveState()
        try: c.setFillAlpha(0.86)
        except Exception: pass
        c.setFillColor(color); c.setStrokeColor(NEGRO); c.setLineWidth(0.6)
        c.drawPath(path, fill=1, stroke=1)
        c.restoreState()

    # Labels exteriores
    for i, (k, label, unit) in enumerate(METRICAS_PIZZA_PDF):
        v = ind.get(k, 0) or 0
        valores = [j.get(k, 0) or 0 for j in candidatos]
        if max(valores) == 0: continue
        pct = _percentil_py(v, valores)
        ang = start_ang + i * slice_ang
        rx = cx + math.cos(ang) * (r_out + 22)
        ry = cy + math.sin(ang) * (r_out + 22)
        c.setFillColor(GRISC); c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(rx, ry + 3, label)
        c.setFillColor(VERDE if pct >= 70 else AMBAR if pct >= 40 else ROJO)
        c.setFont('Helvetica-Bold', 7.5)
        c.drawCentredString(rx, ry - 7, f"{v}{unit} · p{pct}")


# ─── INFORME INDIVIDUAL ──────────────────────────────────────────────────────

def _cover_individual(c, ind, partido):
    fondo(c, NEGRO)
    c.setFillColor(ROJO)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)
    if _LOGO_PIL is not None:
        try:
            c.drawImage(ImageReader(_LOGO_PIL), MX, H - 112, width=58, height=70, mask="auto", preserveAspectRatio=False)
        except Exception:
            pass
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MX + 76, H - 60, "DEPARTAMENTO DE ANÁLISIS DE DATOS")
    c.setFillColor(ROJO)
    c.drawString(MX + 76, H - 73, "CLUB ATLÉTICO RIVER PLATE")
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 7.5)
    c.drawString(MX + 76, H - 92, "INFORME INDIVIDUAL · FÚTBOL FORMATIVO")

    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(MX, H - 200, "ANÁLISIS")
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MX, H - 235, "INDIVIDUAL")

    c.setFillColor(BLANCO)
    c.setFont("Helvetica", 15)
    c.drawString(MX, H - 270, partido.upper())

    # Tarjeta del jugador
    cx, cy, cw, ch = MX, H - 410, W - 2 * MX, 110
    c.setFillColor(GRIS1)
    c.setStrokeColor(ROJO)
    c.setLineWidth(1)
    c.roundRect(cx, cy, cw, ch, 10, fill=1, stroke=1)
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(cx + 20, cy + 70, ind.get("jugador", "—"))
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 10)
    c.drawString(cx + 20, cy + 50, f"{ind.get('condicion','—')}  ·  {ind.get('minutos','—')} min  ·  {ind.get('intervenciones','—')} intervenciones")
    # Mini KPIs en la tarjeta
    kpis = [
        ("Goles", ind.get("goles", 0), ROJO),
        ("Asistencias", ind.get("asistencias", 0), AMBAR),
        ("Pases clave", ind.get("pases_clave", 0), BLANCO),
        ("Recuperadas", (ind.get("recup_posic", 0) or 0) + (ind.get("recup_interv", 0) or 0) + (ind.get("recup_tras", 0) or 0), VERDE),
    ]
    kx = cx + cw - 360
    for i, (lbl, v, col) in enumerate(kpis):
        cx_k = kx + i * 90
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(cx_k + 35, cy + 50, str(v))
        c.setFillColor(GRIS5)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx_k + 35, cy + 30, lbl.upper())

    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 8)
    c.drawString(MX, 30, f"Generado · {datetime.now().strftime('%d de %B de %Y · %H:%M')}")
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - MX, 30, "CONFIDENCIAL · USO INTERNO")
    c.showPage()


def _pagina_individual_stats(c, ind, n_pag, partido):
    fondo(c)
    header_pagina(c, "Estadísticas", ind.get("jugador", "—"), partido)

    # 4 bloques verticales: Pases / Duelos+Remates / Posicional / Defensa
    cols = 4
    gap = 10
    cw = (W - 2 * MX - gap * (cols - 1)) / cols
    ch = H - 110
    y_top = H - 70

    bloques = [
        ("Pases", [
            ("Efectividad", f"{ind.get('pases_efect',0)}%"),
            ("Total", ind.get("pases_total", 0)),
            ("Completos", ind.get("pases_completos", 0)),
            ("Incompletos", ind.get("pases_incompletos", 0)),
            ("Adelante", ind.get("pases_adelante", 0)),
            ("Atrás", ind.get("pases_atras", 0)),
            ("Lateral", ind.get("pases_lateral", 0)),
            ("Filtrados", ind.get("pases_filtrado", 0)),
            ("Largos +", ind.get("pases_largo_c", 0)),
            ("Centros +", ind.get("centros_c", 0)),
        ]),
        ("Duelos y Remates", [
            ("1v1 Of. +", ind.get("dao_plus", 0)),
            ("1v1 Of. −", ind.get("dao_minus", 0)),
            ("1v1 Def. +", ind.get("dad_plus", 0)),
            ("1v1 Def. −", ind.get("dad_minus", 0)),
            ("Regate +/−", f"{ind.get('regate_c', 0)} / {ind.get('regate_i', 0)}"),
            ("Remates (ef.)", f"{ind.get('remates_total', 0)} · {ind.get('remates_efect', 0)}%"),
            ("Cabeza (ef.)", f"{ind.get('rem_cab_total', 0)} · {ind.get('rem_cab_efect', 0)}%"),
            ("Pie hábil (ef.)", f"{ind.get('rem_pieh_total', 0)} · {ind.get('rem_pieh_efect', 0)}%"),
            ("Pie inhábil (ef.)", f"{ind.get('rem_piei_total', 0)} · {ind.get('rem_piei_efect', 0)}%"),
        ]),
        ("Posicional", [
            ("Centro grav.", f"({ind.get('centro_grav_x',0)},{ind.get('centro_grav_y',0)})"),
            ("Dispersión", f"{ind.get('dispersion_x',0)} · {ind.get('dispersion_y',0)}"),
            ("Acciones c/coord.", ind.get("acciones_xy", 0)),
            ("% último tercio", f"{ind.get('pct_ultimo_tercio',0)}%"),
            ("% área rival", f"{ind.get('pct_area',0)}%"),
            ("Toques en área", ind.get("toques_area", 0)),
            ("Progresión media", f"{ind.get('progresion_media',0)}m"),
            ("Distancia media", f"{ind.get('distancia_media',0)}m"),
            ("% progresivas", f"{ind.get('pct_progresivo',0)}%"),
        ]),
        ("Defensa y Movimiento", [
            ("Recup. posicional", ind.get("recup_posic", 0)),
            ("Recup. por interv.", ind.get("recup_interv", 0)),
            ("Tras pérdida", ind.get("recup_tras", 0)),
            ("Pérdidas total", ind.get("perd_total", 0)),
            ("Intercepciones", ind.get("intercepciones", 0)),
            ("Bloqueos", ind.get("bloqueos", 0)),
            ("Recep. entre líneas", ind.get("recep_lineas", 0)),
            ("Recep. al espacio", ind.get("recep_espacio", 0)),
            ("Ruptura conducción", ind.get("ruptura", 0)),
        ]),
    ]

    for i, (titulo, items) in enumerate(bloques):
        cx = MX + i * (cw + gap)
        # Card
        c.setFillColor(GRIS1)
        c.setStrokeColor(GRIS3)
        c.setLineWidth(0.5)
        c.roundRect(cx, MX + 20, cw, y_top - MX - 20, 8, fill=1, stroke=1)
        # Título
        c.setFillColor(ROJO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cx + 12, y_top - 18, titulo.upper())
        c.setStrokeColor(GRIS3)
        c.setLineWidth(0.4)
        c.line(cx + 12, y_top - 22, cx + cw - 12, y_top - 22)
        # Rows
        for j, (lbl, val) in enumerate(items):
            yy = y_top - 38 - j * 18
            c.setFillColor(GRISC)
            c.setFont("Helvetica", 8.5)
            c.drawString(cx + 12, yy, lbl)
            c.setFillColor(BLANCO)
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(cx + cw - 12, yy, str(val))

    footer(c, n_pag)
    c.showPage()


def _pagina_individual_foda_analisis(c, ind, todos_jug, n_pag, partido):
    """Genera FODA + análisis textual."""
    fondo(c)
    header_pagina(c, "FODA + Lectura", ind.get("jugador", "—"), partido)

    # Para el FODA, necesitamos percentiles del plantel
    cuadros = analisis_foda_py(ind, todos_jug)

    # 4 cuadros 2x2
    cw = (W - 2 * MX - 16) / 2
    ch = 180
    posiciones = [
        ("F", "💪 FORTALEZAS",   VERDE, cuadros["fortalezas"],  MX, H - 90 - ch),
        ("O", "📈 OPORTUNIDADES", TURQ,  cuadros["oportunidades"], MX + cw + 16, H - 90 - ch),
        ("D", "⚠ DEBILIDADES",   AMBAR, cuadros["debilidades"], MX, H - 90 - ch * 2 - 16),
        ("A", "🔻 AMENAZAS",      ROJO,  cuadros["amenazas"],    MX + cw + 16, H - 90 - ch * 2 - 16),
    ]

    section_title(c, MX, H - 78, "Análisis FODA del jugador")

    for k, titulo, color, items, x, y in posiciones:
        c.setFillColor(GRIS1)
        c.setStrokeColor(color)
        c.setLineWidth(1.2)
        c.roundRect(x, y, cw, ch, 8, fill=1, stroke=1)
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 14, y + ch - 18, titulo)
        if not items:
            c.setFillColor(GRIS5)
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(x + 14, y + ch - 42, "Sin señales destacadas en este rubro.")
            continue
        for j, it in enumerate(items[:5]):
            yy = y + ch - 38 - j * 18
            c.setFillColor(BLANCO)
            c.setFont("Helvetica", 9)
            c.drawString(x + 14, yy, it["label"][:42])
            c.setFillColor(color)
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(x + cw - 14, yy, str(it["valor"]))

    footer(c, n_pag)
    c.showPage()


def lectura_jugador_py(ind, todos):
    """Versión Python de la lectura textual del jugador."""
    out = []
    if not ind:
        return out
    candidatos = [j for j in (todos or {}).values() if (j.get("intervenciones") or 0) >= 8]
    if len(candidatos) < 4:
        candidatos = list((todos or {}).values())

    # Apertura
    cnt = f"{ind.get('intervenciones',0)} intervenciones en {ind.get('minutos',0)} min"
    out.append(f"{ind.get('jugador','—')} acumuló {cnt}.")

    # Posición
    if (ind.get("acciones_xy") or 0) >= 10:
        x = ind.get("centro_grav_x", 0)
        dx = ind.get("dispersion_x", 0)
        dy = ind.get("dispersion_y", 0)
        if x >= 78:
            zona = "muy cerca del arco rival"
        elif x >= 60:
            zona = "en zona alta-media"
        elif x >= 42:
            zona = "en zona media"
        else:
            zona = "en zona baja, cerca de su propio arco"
        mov = ", con alta movilidad por la cancha" if (dx >= 25 or dy >= 22) else (
              ", con posicionamiento muy estático" if (dx <= 14 and dy <= 12) else "")
        out.append(f"Operó {zona} (CG x={x}, y={ind.get('centro_grav_y',0)}){mov}.")

    # Aporte directo
    partes = []
    g = ind.get("goles", 0) or 0
    a = ind.get("asistencias", 0) or 0
    pk = ind.get("pases_clave", 0) or 0
    recup = (ind.get("recup_posic", 0) or 0) + (ind.get("recup_interv", 0) or 0) + (ind.get("recup_tras", 0) or 0)
    if g:  partes.append(f"{g} gol{'es' if g > 1 else ''}")
    if a:  partes.append(f"{a} asistencia{'s' if a > 1 else ''}")
    if not a and pk >= 2: partes.append(f"{pk} pases clave")
    if recup >= 6: partes.append(f"{recup} recuperaciones")
    if partes:
        out.append(f"Aporte directo en el partido: {' + '.join(partes)}.")

    # Cierre
    if (ind.get("pct_progresivo") or 0) >= 35:
        out.append(f"Su juego fue marcadamente vertical: {ind.get('pct_progresivo')}% de sus acciones con destino avanzaron hacia el arco rival.")
    elif (ind.get("pases_efect") or 0) >= 85 and (ind.get("pases_total") or 0) >= 30:
        out.append(f"Mostró efectividad de pase del {ind.get('pases_efect')}% sobre {ind.get('pases_total')} pases.")

    return out[:6]


def _percentil_py(valor, valores):
    if not valores:
        return 0
    orden = sorted(valores)
    pos = sum(1 for v in orden if v <= valor)
    return round(pos / len(orden) * 100)


METRICAS_FODA = [
    ("pases_efect", "Efectividad de pase", 20, "%"),
    ("pases_clave", "Pases clave", 1, ""),
    ("pases_filtrado", "Pases filtrados", 1, ""),
    ("pct_progresivo", "% acciones progresivas", 8, "%"),
    ("progresion_media", "Progresión media", 2, "m"),
    ("pct_area", "% área rival", 0, "%"),
    ("toques_area", "Toques en área rival", 1, ""),
    ("remates_arco", "Remates al arco", 1, ""),
    ("dao_plus", "1v1 ofensivos ganados", 1, ""),
    ("dad_plus", "1v1 defensivos ganados", 1, ""),
    ("recup_posic", "Recup. posicionales", 2, ""),
    ("intercepciones", "Intercepciones", 1, ""),
    ("centros_c", "Centros completados", 1, ""),
]


def analisis_foda_py(ind, todos):
    out = {"fortalezas": [], "oportunidades": [], "debilidades": [], "amenazas": []}
    if not todos:
        return out
    candidatos = [j for j in todos.values() if (j.get("intervenciones") or 0) >= 8]
    if len(candidatos) < 4:
        return out

    for k, label, min_v, unidad in METRICAS_FODA:
        v = ind.get(k, 0) or 0
        if v < min_v:
            continue
        valores = [j.get(k, 0) or 0 for j in candidatos]
        if max(valores) == 0:
            continue
        pct = _percentil_py(v, valores)
        item = {"label": label, "valor": f"{v}{unidad}", "pct": pct}
        if pct >= 80:
            out["fortalezas"].append(item)
        elif pct <= 25:
            out["debilidades"].append(item)

    out["fortalezas"].sort(key=lambda x: -x["pct"])
    out["debilidades"].sort(key=lambda x: x["pct"])

    # Oportunidades / Amenazas
    if (ind.get("pct_ultimo_tercio") or 0) >= 30 and (ind.get("acciones_xy") or 0) >= 15 and (ind.get("remates_arco") or 0) <= 1:
        out["oportunidades"].append({"label": "Llega al último tercio pero remata poco", "valor": f"{ind.get('remates_arco',0)} rem."})
    if (ind.get("pases_clave") or 0) >= 2 and (ind.get("asistencias") or 0) == 0:
        out["oportunidades"].append({"label": "Genera juego pero sin asistencias", "valor": f"{ind.get('pases_clave',0)} clave"})
    if (ind.get("toques_area") or 0) >= 3 and (ind.get("remates_arco") or 0) == 0:
        out["oportunidades"].append({"label": "Llega al área pero no define", "valor": f"{ind.get('toques_area',0)} toques"})
    # Amenazas
    if (ind.get("perd_total") or 0) >= 5 and (ind.get("centro_grav_x") or 50) < 50:
        out["amenazas"].append({"label": "Pérdidas en zona propia", "valor": f"{ind.get('perd_total',0)} pérd."})
    dad = (ind.get("dad_plus") or 0) + (ind.get("dad_minus") or 0)
    if dad >= 3 and (ind.get("dad_minus") or 0) > (ind.get("dad_plus") or 0):
        out["amenazas"].append({"label": "Pierde duelos defensivos", "valor": f"{ind.get('dad_minus',0)}/{dad}"})
    if (ind.get("pases_total") or 0) >= 30 and (ind.get("pases_efect") or 0) < 60:
        out["amenazas"].append({"label": "Baja efectividad con alto volumen", "valor": f"{ind.get('pases_efect',0)}%"})

    out["fortalezas"]    = out["fortalezas"][:5]
    out["debilidades"]   = out["debilidades"][:5]
    out["oportunidades"] = out["oportunidades"][:3]
    out["amenazas"]      = out["amenazas"][:3]
    return out


def _pagina_individual_lectura(c, ind, todos_jug, n_pag, partido):
    fondo(c)
    header_pagina(c, "Lectura", ind.get("jugador", "—"), partido)
    bullets = lectura_jugador_py(ind, todos_jug)
    section_title(c, MX, H - 90, "📖 Análisis del jugador")
    bullet_lectura(c, MX, H - 120, W - 2 * MX, bullets)
    footer(c, n_pag)
    c.showPage()


def _pagina_perfil_pizza(c, ind, todos, n_pag, partido):
    """Página con pizza chart + badge de estilo + listas top/bottom."""
    fondo(c)
    header_pagina(c, "Perfil & Percentiles", ind.get("jugador", "—"), partido)

    # Pizza chart a la izquierda
    pizza_cx, pizza_cy, pizza_r = MX + 220, H/2 - 30, 160
    _pizza_jugador(c, pizza_cx, pizza_cy, pizza_r, ind, todos)

    # Leyenda del pizza
    leg_y = H - 460
    c.setFillColor(GRIS5); c.setFont("Helvetica-Bold", 7)
    c.drawString(MX + 40, leg_y, "PERCENTIL EN EL PLANTEL")
    leg_x0 = MX + 40
    items = [("Top (≥70)", VERDE), ("Medio (40-69)", AMBAR), ("Bajo (<40)", ROJO)]
    for i, (lbl, col) in enumerate(items):
        c.setFillColor(col); c.rect(leg_x0 + i * 110, leg_y - 14, 10, 10, fill=1, stroke=0)
        c.setFillColor(BLANCO); c.setFont("Helvetica", 8)
        c.drawString(leg_x0 + i * 110 + 14, leg_y - 12, lbl)

    # Lado derecho — Estilo + top/bottom métricas
    est = detectar_estilo_py(ind, todos)
    sx0 = MX + 470
    sw = W - MX - sx0

    # Badge estilo grande
    by, bh = H - 130, 88
    if est and not est['nombre'].startswith('Perfil mixto'):
        c.setFillColor(ROJO2)
        c.roundRect(sx0, by - bh, sw, bh, 8, fill=1, stroke=0)
        c.setFillColor(ROJO)
        c.roundRect(sx0, by - bh, sw, bh, 8, fill=0, stroke=1)
        c.setFillColor(BLANCO); c.setFont("Helvetica-Bold", 7)
        c.drawString(sx0 + 16, by - 18, "ESTILO DETECTADO")
        c.setFillColor(BLANCO); c.setFont("Helvetica-Bold", 16)
        for j, ln in enumerate(_wrap(est['nombre'], 28)[:2]):
            c.drawString(sx0 + 16, by - 38 - j * 18, ln)
        c.setFillColor(colors.HexColor("#ffd0d0")); c.setFont("Helvetica", 8)
        for j, ln in enumerate(_wrap(est['detalle'], 50)[:2]):
            c.drawString(sx0 + 16, by - bh + 22 - j * 10, ln)
    else:
        c.setFillColor(GRIS1); c.setStrokeColor(GRIS4); c.setLineWidth(1)
        c.roundRect(sx0, by - bh, sw, bh, 8, fill=1, stroke=1)
        c.setFillColor(GRIS5); c.setFont("Helvetica-Bold", 7)
        c.drawString(sx0 + 16, by - 18, "ESTILO DETECTADO")
        c.setFillColor(GRISC); c.setFont("Helvetica-Bold", 14)
        c.drawString(sx0 + 16, by - 42, "Perfil mixto")
        c.setFillColor(GRIS5); c.setFont("Helvetica", 8)
        c.drawString(sx0 + 16, by - 60, "Sin dominancia estadística clara en un rol")

    # Top 4 + Bottom 3 métricas
    candidatos = [j for j in (todos or {}).values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) >= 4:
        rankings = []
        for k, label, unit in METRICAS_PIZZA_PDF + [
            ('toques_area', 'Toques en área', ''),
            ('dao_plus', '1v1 Of. +', ''),
            ('dad_plus', '1v1 Def. +', ''),
            ('recup_posic', 'Recup. posic.', ''),
        ]:
            v = ind.get(k, 0) or 0
            valores = [j.get(k, 0) or 0 for j in candidatos]
            if max(valores) == 0: continue
            rankings.append({'k': k, 'l': label, 'u': unit, 'v': v, 'p': _percentil_py(v, valores)})
        top = sorted(rankings, key=lambda x: -x['p'])[:4]
        bottom = [r for r in sorted(rankings, key=lambda x: x['p']) if r['v'] > 0][:3]

        ty = by - bh - 24
        c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 8)
        c.drawString(sx0, ty, "TOP DEL JUGADOR")
        c.setStrokeColor(GRIS3); c.line(sx0, ty - 4, sx0 + sw, ty - 4)
        for i, r in enumerate(top):
            yy = ty - 16 - i * 16
            c.setFillColor(BLANCO); c.setFont("Helvetica", 8)
            c.drawString(sx0 + 4, yy, r['l'][:24])
            c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 9)
            c.drawRightString(sx0 + sw - 4, yy, f"{r['v']}{r['u']} (p{r['p']})")

        ty2 = ty - 16 * (len(top) + 1) - 14
        c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawString(sx0, ty2, "A POTENCIAR")
        c.setStrokeColor(GRIS3); c.line(sx0, ty2 - 4, sx0 + sw, ty2 - 4)
        for i, r in enumerate(bottom):
            yy = ty2 - 16 - i * 16
            c.setFillColor(BLANCO); c.setFont("Helvetica", 8)
            c.drawString(sx0 + 4, yy, r['l'][:24])
            c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 9)
            c.drawRightString(sx0 + sw - 4, yy, f"{r['v']}{r['u']} (p{r['p']})")

    footer(c, n_pag)
    c.showPage()


def _pagina_rankings(c, ind, todos, n_pag, partido):
    """Página con 6 rankings: top-5 del plantel + el jugador destacado."""
    fondo(c)
    header_pagina(c, "Rankings en el plantel", ind.get("jugador", "—"), partido)
    section_title(c, MX, H - 78, "Comparación con el resto del plantel · 6 métricas clave")

    metricas = [
        ('pases_total',    'Volumen de pases', ''),
        ('pases_efect',    'Efectividad de pase', '%'),
        ('pct_progresivo', '% Acciones progresivas', '%'),
        ('toques_area',    'Toques en área rival', ''),
        ('remates_arco',   'Remates al arco', ''),
        ('recup_interv',   'Recuperaciones activas', ''),
    ]
    cols = 3
    gap = 14
    gw = (W - 2 * MX - gap * (cols - 1)) / cols
    rh = 190
    candidatos = [j for j in (todos or {}).values() if (j.get('intervenciones') or 0) >= 8]
    if not candidatos:
        footer(c, n_pag); c.showPage(); return
    etiquetas = _etiquetas_jugadores(todos)
    jugador_nom = ind.get('jugador', '')

    for i, (k, lbl, unit) in enumerate(metricas):
        col = i % cols
        row = i // cols
        gx = MX + col * (gw + gap)
        gy = H - 110 - row * (rh + 20)

        c.setFillColor(GRIS1); c.setStrokeColor(GRIS3); c.setLineWidth(0.5)
        c.roundRect(gx, gy - rh, gw, rh, 8, fill=1, stroke=1)
        c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 9)
        c.drawString(gx + 12, gy - 18, lbl.upper())

        ranked = sorted(candidatos, key=lambda j: -(j.get(k, 0) or 0))[:5]
        # Asegurar que el jugador focal esté
        if not any(j.get('jugador') == jugador_nom for j in ranked) and ind in candidatos:
            ranked.append(ind)
        max_v = max((j.get(k, 0) or 0) for j in ranked) or 1

        for r_idx, j in enumerate(ranked):
            yy = gy - 36 - r_idx * 22
            es_focal = j.get('jugador') == jugador_nom
            v = j.get(k, 0) or 0
            color_bar = ROJO if es_focal else GRIS5
            color_text = ROJO if es_focal else GRISC
            # Número de posición
            pos_real = next((idx + 1 for idx, x in enumerate(sorted(candidatos, key=lambda x: -(x.get(k, 0) or 0))) if x.get('jugador') == j.get('jugador')), '?')
            c.setFillColor(GRIS5); c.setFont("Helvetica-Bold", 7)
            c.drawString(gx + 8, yy + 3, f"{pos_real}º")
            # Nombre
            c.setFillColor(color_text); c.setFont("Helvetica-Bold" if es_focal else "Helvetica", 8)
            label = etiquetas.get(j.get('jugador'), (j.get('jugador') or '?').split()[-1])
            c.drawString(gx + 26, yy + 3, label[:13])
            # Barra
            bar_x = gx + 110
            bar_w = gw - 120 - 36
            c.setFillColor(GRIS3)
            c.rect(bar_x, yy, bar_w, 7, fill=1, stroke=0)
            fill = (v / max_v) * bar_w
            c.setFillColor(color_bar)
            c.rect(bar_x, yy, fill, 7, fill=1, stroke=0)
            # Valor
            c.setFillColor(color_text); c.setFont("Helvetica-Bold", 8)
            c.drawRightString(gx + gw - 8, yy + 3, f"{v}{unit}")

    # Nota al pie
    c.setFillColor(GRIS5); c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(MX, 36, f"Barras rojas = {ind.get('jugador','—')}.   Sólo se consideran jugadores con ≥ 8 intervenciones.")

    footer(c, n_pag)
    c.showPage()


def _pagina_individual_cancha(c, ind, coords, n_pag, partido):
    fondo(c)
    header_pagina(c, "Mapa en cancha", ind.get("jugador", "—"), partido)

    # Cancha grande con heatmap + flechas progresivas
    pitch_x, pitch_y, pitch_w, pitch_h = MX, H - 360, W - 2 * MX - 220, 270
    _cancha(c, pitch_x, pitch_y, pitch_w, pitch_h)
    _cancha_heatmap(c, pitch_x, pitch_y, pitch_w, pitch_h, coords or [])
    # Flechas para acciones progresivas
    for a in (coords or []):
        if a.get("prog") and a.get("xe") is not None and a.get("ye") is not None:
            tags = a.get("tags", "")
            neg = any(n in tags for n in ["PIncompletos", "CIncompletos", "PERDIDAS", "Afuera", "Bloqueado", "Largo Incompleto"])
            destEnArea = a["xe"] >= 102 and 18 <= a["ye"] <= 62
            color = ROJO if neg else (AMBAR if destEnArea else VERDE)
            _cancha_flecha(c, pitch_x, pitch_y, pitch_w, pitch_h,
                           (a["x"], a["y"]), (a["xe"], a["ye"]), color, 0.55)

    # Sidebar derecha con stats clave
    sx0 = pitch_x + pitch_w + 16
    c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 8)
    c.drawString(sx0, pitch_y + pitch_h - 4, "DATOS POSICIONALES")
    c.setStrokeColor(GRIS3); c.setLineWidth(0.4)
    c.line(sx0, pitch_y + pitch_h - 10, sx0 + 200, pitch_y + pitch_h - 10)

    stats = [
        ("Centro de gravedad", f"({ind.get('centro_grav_x',0)}, {ind.get('centro_grav_y',0)})"),
        ("Dispersión x · y", f"{ind.get('dispersion_x',0)} · {ind.get('dispersion_y',0)}"),
        ("Acciones con coord.", str(ind.get('acciones_xy', 0))),
        ("% último tercio", f"{ind.get('pct_ultimo_tercio',0)}%"),
        ("% área rival", f"{ind.get('pct_area',0)}%"),
        ("Progresión media", f"{ind.get('progresion_media',0)} m"),
        ("Distancia media", f"{ind.get('distancia_media',0)} m"),
        ("% progresivas", f"{ind.get('pct_progresivo',0)}%"),
    ]
    for i, (lbl, val) in enumerate(stats):
        yy = pitch_y + pitch_h - 30 - i * 22
        c.setFillColor(GRIS5); c.setFont("Helvetica-Bold", 7)
        c.drawString(sx0, yy, lbl.upper())
        c.setFillColor(BLANCO); c.setFont("Helvetica-Bold", 13)
        c.drawString(sx0, yy - 13, val)

    # Leyenda flechas
    c.setFillColor(GRIS5); c.setFont("Helvetica", 7)
    leg_y = pitch_y - 18
    c.drawString(pitch_x, leg_y, "Flechas: ")
    c.setFillColor(VERDE); c.rect(pitch_x + 38, leg_y + 1, 14, 2, fill=1, stroke=0)
    c.setFillColor(BLANCO); c.drawString(pitch_x + 56, leg_y, "Completa")
    c.setFillColor(AMBAR); c.rect(pitch_x + 110, leg_y + 1, 14, 2, fill=1, stroke=0)
    c.setFillColor(BLANCO); c.drawString(pitch_x + 128, leg_y, "Llega al área")
    c.setFillColor(ROJO); c.rect(pitch_x + 210, leg_y + 1, 14, 2, fill=1, stroke=0)
    c.setFillColor(BLANCO); c.drawString(pitch_x + 228, leg_y, "Incompleta / pérdida")
    c.setFillColor(GRIS5)
    c.drawString(pitch_x + 360, leg_y, "Heatmap rojo = densidad de acciones en esa zona")

    # Descriptor de métricas posicionales
    y_def = pitch_y - 40
    section_title(c, MX, y_def, "¿Cómo leer estas métricas?")
    defs = [
        ("Centro de gravedad",  "Posición promedio (x, y) de todas las acciones. Indica dónde se posicionó habitualmente. x crece hacia el arco rival (0-120)."),
        ("Dispersión x · y",    "Desvío estándar de las coordenadas. Alto = jugador móvil que cubre mucho terreno. Bajo = jugador anclado a una zona."),
        ("% último tercio",     "Porcentaje de acciones que ocurrieron en x ≥ 80 (último tercio ofensivo)."),
        ("% área rival",        "Porcentaje de acciones dentro del área rival (x > 102, y entre 18 y 62)."),
        ("Progresión media",    "Metros promedio que avanza hacia el arco rival por acción con destino. Positivo = avanza, negativo = retrocede."),
        ("Distancia media",     "Distancia euclídea promedio entre origen y destino. Mide qué tan largas son sus acciones."),
        ("% progresivas",       "Porcentaje de acciones con destino que avanzaron ≥ 10 metros hacia el arco rival."),
    ]
    col_w = (W - 2 * MX) / 2
    for i, (lbl, desc) in enumerate(defs):
        col = i % 2
        row = i // 2
        xx = MX + col * col_w
        yy = y_def - 18 - row * 18
        c.setFillColor(ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawString(xx, yy, lbl + ":")
        c.setFillColor(GRISC); c.setFont("Helvetica", 7.5)
        c.drawString(xx + len(lbl) * 4.6 + 8, yy, desc[:78])

    footer(c, n_pag)
    c.showPage()


def generar_pdf_individual(ind, partido, minutos, todos_jug=None, coords=None):
    """Genera informe individual con pizza, rankings, cancha, stats, FODA y lectura."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    _cover_individual(c, ind, partido)
    pag = 1
    if todos_jug and len(todos_jug) >= 4:
        _pagina_perfil_pizza(c, ind, todos_jug, pag, partido)
        pag += 1
        _pagina_rankings(c, ind, todos_jug, pag, partido)
        pag += 1
    if coords:
        _pagina_individual_cancha(c, ind, coords, pag, partido)
        pag += 1
    _pagina_individual_stats(c, ind, pag, partido)
    pag += 1
    if todos_jug:
        _pagina_individual_foda_analisis(c, ind, todos_jug, pag, partido)
        pag += 1
    _pagina_individual_lectura(c, ind, todos_jug, pag, partido)
    c.save()
    return buf.getvalue()
