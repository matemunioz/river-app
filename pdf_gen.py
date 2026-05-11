"""
pdf_gen.py — Generador de informes PDF estilo River Plate Videoanálisis
"""

import io
import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ─── Paleta ───────────────────────────────────────────────────────────────────
NEGRO  = colors.HexColor("#0a0a0a")
ROJO   = colors.HexColor("#CC0000")
ROJO2  = colors.HexColor("#990000")
BLANCO = colors.white
GRIS1  = colors.HexColor("#1a1a1a")
GRIS2  = colors.HexColor("#222222")
GRIS3  = colors.HexColor("#2e2e2e")
GRIS4  = colors.HexColor("#444444")
GRIS5  = colors.HexColor("#777777")
GRISC  = colors.HexColor("#bbbbbb")
VERDE  = colors.HexColor("#3ecf8e")
AMBAR  = colors.HexColor("#f5a623")

W, H = landscape(A4)   # 841.89 x 595.28 pt

LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "logo.png")

# ─── Primitivas ───────────────────────────────────────────────────────────────

def fondo(c):
    c.setFillColor(NEGRO)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def encabezado(c, titulo: str, subtitulo: str, partido: str):
    c.setFillColor(GRIS1)
    c.rect(0, H - 50, W, 50, fill=1, stroke=0)
    c.setFillColor(ROJO)
    c.rect(0, H - 53, W, 3, fill=1, stroke=0)

    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(ImageReader(LOGO_PATH), 12, H - 47, width=36, height=36, mask="auto")
        except Exception:
            pass

    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(56, H - 22, titulo.upper())
    c.setFillColor(GRISC)
    c.setFont("Helvetica", 8)
    c.drawString(56, H - 36, subtitulo.upper())

    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(W - 14, H - 22, partido.upper())
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - 14, H - 36, "ÁREA DE VIDEOANÁLISIS · FÚTBOL FORMATIVO")


def footer(c):
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 6)
    c.drawCentredString(W / 2, 9, "Club Atlético River Plate · Área de Videoanálisis · Fútbol Formativo")


def sec_titulo(c, x, y, w, texto):
    """Banda roja con título de sección."""
    c.setFillColor(ROJO)
    c.roundRect(x, y, w, 14, 3, fill=1, stroke=0)
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x + w / 2, y + 4, texto.upper())
    return y - 16   # devuelve y de la próxima línea


def badge_grande(c, x, y, w, h, label, valor, color_val=BLANCO, color_bg=GRIS2):
    """Tarjeta métrica grande."""
    c.setFillColor(color_bg)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=0)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + w / 2, y + h - 12, label.upper())
    c.setFillColor(color_val)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(x + w / 2, y + 5, str(valor))


def badge_mini(c, x, y, w, h, label, valor, color_val=BLANCO, color_bg=GRIS2):
    """Tarjeta métrica pequeña."""
    c.setFillColor(color_bg)
    c.roundRect(x, y, w, h, 3, fill=1, stroke=0)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(x + w / 2, y + h - 9, label.upper())
    c.setFillColor(color_val)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(x + w / 2, y + 3, str(valor))


def trio(c, x, y, w, v1, l1, v2, l2, v3, l3, color_v=BLANCO):
    """Tres valores en línea con etiqueta."""
    col = w / 3
    for i, (v, l) in enumerate([(v1, l1), (v2, l2), (v3, l3)]):
        cx = x + col * i + col / 2
        c.setFillColor(color_v)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(cx, y + 8, str(v))
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(cx, y + 1, l.upper())


def duo(c, x, y, w, v1, l1, v2, l2, color_v=BLANCO):
    col = w / 2
    for i, (v, l) in enumerate([(v1, l1), (v2, l2)]):
        cx = x + col * i + col / 2
        c.setFillColor(color_v)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(cx, y + 8, str(v))
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(cx, y + 1, l.upper())


def sublabel(c, x, y, texto):
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 5.5)
    c.drawString(x, y, texto.upper())


def fila_comp(c, x, y, label, vr, vv, ancho):
    """Fila comparativa River vs Rival con barra proporcional."""
    h = 13
    c.setFillColor(GRIS3)
    c.rect(x, y, ancho, h, fill=1, stroke=0)

    tot = (vr or 0) + (vv or 0)
    if tot > 0:
        bw = ancho * 0.32
        pr = (vr or 0) / tot
        c.setFillColor(ROJO)
        c.rect(x + 2, y + 3, bw * pr, 7, fill=1, stroke=0)
        c.setFillColor(GRIS4)
        c.rect(x + ancho - bw - 2 + bw * (1 - pr), y + 3, bw * (1 - pr), 7, fill=1, stroke=0)

    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 4, y + 3, str(vr or 0))
    c.setFillColor(GRISC)
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + ancho / 2, y + 3, label.upper())
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(x + ancho - 4, y + 3, str(vv or 0))
    return y - h - 1


# ─── PDF COLECTIVO ────────────────────────────────────────────────────────────

def generar_pdf_colectivo(data: dict, goles: list, minutos: list, cambios: list) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    c.setTitle(f"Colectivo — {data.get('partido','')}")

    fondo(c)
    encabezado(c, "Estadísticas Colectivas", "Informe de Partido", data.get("partido", ""))
    footer(c)

    gp = data["goles_propios"]
    gr = data["goles_rivales"]
    lp = data["llegadas_prop"]
    lr = data["llegadas_riv"]
    sp = data["salidas_prop"]
    sr = data["salidas_riv"]
    cp = data["centros_prop"]
    cr = data["centros_riv"]

    # ── Constantes de layout ───────────────────────────────────────────────
    TOP   = H - 58          # primera línea de contenido (bajo el header)
    PAD   = 10              # margen lateral global
    GAP   = 8               # separación entre columnas
    BH_G  = 38              # altura badge grande
    BH_M  = 30              # altura badge mini
    ROW_H = 16              # altura fila de valores (trio/duo)
    SEC_H = 16              # altura banda de sección

    # Anchos de cada columna (4 columnas)
    CW1 = 185   # Llegadas Propias
    CW2 = 198   # Comparativa
    CW3 = 198   # Salidas
    CW4 = W - PAD*2 - CW1 - CW2 - CW3 - GAP*3  # Goles + Cambios + Llegadas Rivales

    X1 = PAD
    X2 = X1 + CW1 + GAP
    X3 = X2 + CW2 + GAP
    X4 = X3 + CW3 + GAP

    # ── SCORE central (flotante sobre col 2) ─────────────────────────────
    sc_w = CW2
    sc_x = X2
    sc_y = TOP - 42
    c.setFillColor(GRIS2)
    c.roundRect(sc_x, sc_y, sc_w, 38, 5, fill=1, stroke=0)
    # River
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 32)
    c.drawRightString(sc_x + sc_w / 2 - 10, sc_y + 6, str(gp["total"]))
    c.setFillColor(GRIS4)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(sc_x + sc_w / 2, sc_y + 10, "–")
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 32)
    c.drawString(sc_x + sc_w / 2 + 12, sc_y + 6, str(gr["total"]))
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 6)
    c.drawCentredString(sc_x + sc_w / 2, sc_y + 2, "GOLES")
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(sc_x + 6, sc_y + 28, "RIVER")
    c.setFillColor(GRIS5)
    c.drawRightString(sc_x + sc_w - 6, sc_y + 28, "RIVAL")

    # ── COL 1: LLEGADAS PROPIAS ───────────────────────────────────────────
    y1 = TOP
    y1 = sec_titulo(c, X1, y1, CW1, "Llegadas Propias")

    # Badges principales (3 en una fila)
    bw = (CW1 - 4) / 3
    badge_grande(c, X1,        y1 - BH_G, bw - 2, BH_G, "Total",        lp["total"],      ROJO)
    badge_grande(c, X1+bw,     y1 - BH_G, bw - 2, BH_G, "Sit. de Gol",  data["sit_gol_prop"], AMBAR)
    badge_grande(c, X1+bw*2,   y1 - BH_G, bw - 2, BH_G, "Rem. al Arco", lp["tiros_arco"])
    y1 -= BH_G + 4

    sublabel(c, X1, y1, "tipo de llegada")
    y1 -= 3
    trio(c, X1, y1 - ROW_H, CW1, lp["asociado"], "Asociado", lp["directo"], "Directo", lp["detenidas"], "Detenidas")
    y1 -= ROW_H + 6

    sublabel(c, X1, y1, "finalización (carril)")
    y1 -= 3
    trio(c, X1, y1 - ROW_H, CW1, lp["izq"], "Izq", lp["eje"], "Eje", lp["der"], "Der")
    y1 -= ROW_H + 6

    sublabel(c, X1, y1, "remates")
    y1 -= 3
    trio(c, X1, y1 - ROW_H, CW1, lp["tiros_arco"], "Al Arco", lp["afuera"], "Afuera", lp["bloqueado"], "Bloqueado")
    y1 -= ROW_H + 6

    sublabel(c, X1, y1, "carriles utilizados")
    y1 -= 3
    trio(c, X1, y1 - ROW_H, CW1, lp["1carril"], "1 Carril", lp["2carriles"], "2 Carriles", lp["3carriles"], "3 Carriles")
    y1 -= ROW_H + 8

    y1 = sec_titulo(c, X1, y1, CW1, "Centros Propios")
    bw2 = (CW1 - 4) / 3
    badge_mini(c, X1,       y1 - BH_M, bw2 - 2, BH_M, "Total",       cp["total"])
    badge_mini(c, X1+bw2,   y1 - BH_M, bw2 - 2, BH_M, "Completos",   cp["completos"], VERDE)
    badge_mini(c, X1+bw2*2, y1 - BH_M, bw2 - 2, BH_M, "Incompletos", cp["incompletos"])
    y1 -= BH_M + 8

    y1 = sec_titulo(c, X1, y1, CW1, "Pelota Parada")
    bw3 = (CW1 - 2) / 2
    badge_mini(c, X1,      y1 - BH_M, bw3 - 2, BH_M, "Detenidas Prop", data["detenidas_prop"])
    badge_mini(c, X1+bw3,  y1 - BH_M, bw3 - 2, BH_M, "Corners Prop",  data["corners_prop"])

    # ── COL 2: COMPARATIVA ────────────────────────────────────────────────
    y2 = TOP - 48   # empieza debajo del score
    y2 = sec_titulo(c, X2, y2, CW2, "River vs Rival")

    stats_comp = [
        ("Llegadas",           lp["total"],          lr["total"]),
        ("Situaciones de Gol", data["sit_gol_prop"],  data["sit_gol_riv"]),
        ("Remates al Arco",    lp["tiros_arco"],      lr["tiros_arco"]),
        ("Centros",            cp["total"],           cr["total"]),
        ("Detenidas",          data["detenidas_prop"],data["detenidas_riv"]),
        ("Transic. Ofensiva",  data["trans_of"],      0),
        ("Transic. Defensiva", data["trans_def"],     0),
        ("Circulaciones",      data["circulaciones"], 0),
        ("Bloques",            data["bloques"],       0),
        ("Pérdidas",           data["perdidas"],      0),
        ("Recuperadas",        data["recuperadas"],   0),
    ]
    for label, vr, vv in stats_comp:
        y2 = fila_comp(c, X2, y2, label, vr, vv, CW2)

    # ── COL 3: SALIDAS ────────────────────────────────────────────────────
    y3 = TOP
    y3 = sec_titulo(c, X3, y3, CW3, "Salidas Propias")

    bw_s = (CW3 - 4) / 3
    badge_grande(c, X3,         y3 - BH_G, bw_s-2, BH_G, "Total",    sp["total"])
    badge_grande(c, X3+bw_s,    y3 - BH_G, bw_s-2, BH_G, "En Corto", sp["cortas"])
    badge_grande(c, X3+bw_s*2,  y3 - BH_G, bw_s-2, BH_G, "En Largo", sp["largas"])
    y3 -= BH_G + 4

    sublabel(c, X3, y3, "progresión")
    y3 -= 3
    duo(c, X3, y3 - ROW_H, CW3, sp["progresa"], "Progresa", sp["no_progresa"], "No Progresa")
    y3 -= ROW_H + 6

    sublabel(c, X3, y3, "orientación")
    y3 -= 3
    trio(c, X3, y3 - ROW_H, CW3, sp["izq"], "Izq", sp["eje"], "Eje", sp["der"], "Der")
    y3 -= ROW_H + 8

    y3 = sec_titulo(c, X3, y3, CW3, "Salidas Rivales")

    bw_sr = (CW3 - 4) / 3
    badge_grande(c, X3,          y3 - BH_G, bw_sr-2, BH_G, "Total",    sr["total"])
    badge_grande(c, X3+bw_sr,    y3 - BH_G, bw_sr-2, BH_G, "En Corto", sr["cortas"])
    badge_grande(c, X3+bw_sr*2,  y3 - BH_G, bw_sr-2, BH_G, "En Largo", sr["largas"])
    y3 -= BH_G + 4

    sublabel(c, X3, y3, "progresión")
    y3 -= 3
    duo(c, X3, y3 - ROW_H, CW3, sr["progresa"], "Progresa", sr["no_progresa"], "No Progresa")
    y3 -= ROW_H + 6

    sublabel(c, X3, y3, "orientación")
    y3 -= 3
    trio(c, X3, y3 - ROW_H, CW3, sr["izq"], "Izq", sr["eje"], "Eje", sr["der"], "Der")
    y3 -= ROW_H + 8

    y3 = sec_titulo(c, X3, y3, CW3, "Centros Rivales")
    bw_cr = (CW3 - 4) / 3
    badge_mini(c, X3,        y3 - BH_M, bw_cr-2, BH_M, "Total",       cr["total"])
    badge_mini(c, X3+bw_cr,  y3 - BH_M, bw_cr-2, BH_M, "Completos",   cr["completos"])
    badge_mini(c, X3+bw_cr*2,y3 - BH_M, bw_cr-2, BH_M, "Incompletos", cr["incompletos"])

    # ── COL 4: LLEGADAS RIVALES + GOLES + CAMBIOS ─────────────────────────
    y4 = TOP
    y4 = sec_titulo(c, X4, y4, CW4, "Llegadas Rivales")

    bw4 = (CW4 - 4) / 3
    badge_grande(c, X4,       y4-BH_G, bw4-2, BH_G, "Total",        lr["total"])
    badge_grande(c, X4+bw4,   y4-BH_G, bw4-2, BH_G, "Sit. de Gol",  data["sit_gol_riv"])
    badge_grande(c, X4+bw4*2, y4-BH_G, bw4-2, BH_G, "Rem. al Arco", lr["tiros_arco"])
    y4 -= BH_G + 4

    sublabel(c, X4, y4, "tipo de llegada")
    y4 -= 3
    trio(c, X4, y4-ROW_H, CW4, lr["asociado"], "Asociado", lr["directo"], "Directo", lr["detenidas"], "Detenidas")
    y4 -= ROW_H + 6

    sublabel(c, X4, y4, "finalización")
    y4 -= 3
    trio(c, X4, y4-ROW_H, CW4, lr["izq"], "Izq", lr["eje"], "Eje", lr["der"], "Der")
    y4 -= ROW_H + 8

    # GOLES
    y4 = sec_titulo(c, X4, y4, CW4, "Goles del Partido")
    for g in goles[:6]:
        esR = g["equipo"] == "Propio"
        eq_color = ROJO if esR else GRISC
        c.setFillColor(GRIS3)
        c.roundRect(X4, y4 - 12, CW4, 12, 2, fill=1, stroke=0)
        c.setFillColor(eq_color)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(X4 + 3, y4 - 9, "RIVER" if esR else "RIVAL")
        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(X4 + 34, y4 - 9, g["minuto"])
        c.setFillColor(GRISC)
        c.setFont("Helvetica", 6)
        c.drawString(X4 + 62, y4 - 9, g["tipo"][:20])
        c.drawRightString(X4 + CW4 - 3, y4 - 9, g["carril"][:10])
        y4 -= 14

    # CAMBIOS
    y4 -= 2
    y4 = sec_titulo(c, X4, y4, CW4, "Cambios")
    for cam in cambios[:7]:
        c.setFillColor(GRIS3)
        c.roundRect(X4, y4 - 22, CW4, 22, 2, fill=1, stroke=0)
        c.setFillColor(ROJO)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(X4 + 3, y4 - 9, cam["minuto"])
        c.setFillColor(colors.HexColor("#ff7777"))
        c.setFont("Helvetica", 6)
        c.drawString(X4 + 38, y4 - 9, f"↑ {cam['sale'][:18]}")
        c.setFillColor(colors.HexColor("#77ee99"))
        c.drawString(X4 + 38, y4 - 18, f"↓ {cam['entra'][:18]}")
        c.setFillColor(GRIS5)
        c.setFont("Helvetica", 5.5)
        c.drawRightString(X4 + CW4 - 3, y4 - 9, cam.get("equipo", "Propio").upper())
        y4 -= 24

    c.save()
    buf.seek(0)
    return buf.read()


# ─── PDF INDIVIDUAL ───────────────────────────────────────────────────────────

def generar_pdf_individual(ind: dict, partido: str, minutos_jugados: list = None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    c.setTitle(f"Individual — {ind.get('jugador','')} — {partido}")

    fondo(c)
    encabezado(c, "Estadísticas Individuales",
               f"{ind.get('jugador','').upper()} · {ind.get('condicion','')} · {ind.get('minutos',0)} min",
               partido)
    footer(c)

    TOP  = H - 58
    PAD  = 10
    GAP  = 7
    BH_M = 30
    BH_S = 24
    ROW  = 14   # alto de fila de stat

    # 4 columnas
    CW = (W - PAD * 2 - GAP * 3) / 4
    X1, X2, X3, X4 = PAD, PAD+CW+GAP, PAD+(CW+GAP)*2, PAD+(CW+GAP)*3

    # ── Nombre grande ─────────────────────────────────────────────────────
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W / 2, TOP - 4, ind.get("jugador", "").upper())
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, TOP - 16,
        f"{ind.get('condicion','')} · {ind.get('minutos',0)} min · {ind.get('intervenciones',0)} intervenciones")

    # KPIs centrales
    kpi_y = TOP - 52
    kpi_w = 62
    kpi_x = W / 2 - kpi_w * 1.5 - 6
    for i, (label, val, color) in enumerate([
        ("Goles",        ind.get("goles", 0),       ROJO),
        ("Asistencias",  ind.get("asistencias", 0), AMBAR),
        ("Pases Clave",  ind.get("pases_clave", 0), colors.HexColor("#4a90d9")),
    ]):
        badge_grande(c, kpi_x + i*(kpi_w+6), kpi_y, kpi_w, 34, label, val, color)

    # Línea separadora
    c.setFillColor(GRIS3)
    c.rect(PAD, TOP - 92, W - PAD*2, 1, fill=1, stroke=0)

    # ── Función para stat row ─────────────────────────────────────────────
    def stat_row(c, x, y, w, label, val, color=BLANCO):
        c.setFillColor(GRIS2)
        c.rect(x, y, w, ROW, fill=1, stroke=0)
        c.setFillColor(GRISC)
        c.setFont("Helvetica", 6)
        c.drawString(x + 4, y + 4, label)
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x + w - 4, y + 4, str(val))
        return y - ROW - 1

    def bloque(c, x, y, w, titulo):
        y = sec_titulo(c, x, y, w, titulo)
        return y

    # ── COL 1: PASES ─────────────────────────────────────────────────────
    y1 = TOP - 96

    y1 = bloque(c, X1, y1, CW, "Pases")
    # Efectividad
    efect = ind.get("pases_efect", 0)
    color_ef = VERDE if efect >= 75 else AMBAR if efect >= 60 else ROJO
    c.setFillColor(GRIS2)
    c.roundRect(X1, y1 - 28, CW, 28, 3, fill=1, stroke=0)
    c.setFillColor(color_ef)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(X1 + 6, y1 - 20, f"{efect}%")
    # barra
    bw_ef = CW - 60
    c.setFillColor(GRIS3)
    c.rect(X1 + 48, y1 - 14, bw_ef, 6, fill=1, stroke=0)
    c.setFillColor(color_ef)
    c.rect(X1 + 48, y1 - 14, bw_ef * efect / 100, 6, fill=1, stroke=0)
    c.setFillColor(GRIS5)
    c.setFont("Helvetica", 5.5)
    c.drawString(X1 + 48, y1 - 22, f"Total: {ind.get('pases_total',0)}  C: {ind.get('pases_completos',0)}  I: {ind.get('pases_incompletos',0)}")
    y1 -= 32

    y1 = stat_row(c, X1, y1, CW, "Adelante", ind.get("pases_adelante",0))
    y1 = stat_row(c, X1, y1, CW, "Atrás", ind.get("pases_atras",0))
    y1 = stat_row(c, X1, y1, CW, "Lateral", ind.get("pases_lateral",0))
    y1 = stat_row(c, X1, y1, CW, "Largo completo", ind.get("pases_largo_c",0), VERDE)
    y1 = stat_row(c, X1, y1, CW, "Largo incompleto", ind.get("pases_largo_i",0), ROJO)
    y1 = stat_row(c, X1, y1, CW, "Filtrado", ind.get("pases_filtrado",0), AMBAR)
    y1 = stat_row(c, X1, y1, CW, "Apoyo", ind.get("apoyos",0))
    y1 -= 4

    y1 = bloque(c, X1, y1, CW, "Centros")
    y1 = stat_row(c, X1, y1, CW, "Completos", ind.get("centros_c",0), VERDE)
    y1 = stat_row(c, X1, y1, CW, "Incompletos", ind.get("centros_i",0))
    y1 -= 4

    y1 = bloque(c, X1, y1, CW, "Remates")
    y1 = stat_row(c, X1, y1, CW, "Al arco", ind.get("remates_arco",0), ROJO)
    y1 = stat_row(c, X1, y1, CW, "Gol", ind.get("remates_gol",0), AMBAR)
    y1 = stat_row(c, X1, y1, CW, "Afuera", ind.get("remates_afuera",0))
    y1 = stat_row(c, X1, y1, CW, "Bloqueado", ind.get("remates_bloq",0))

    # ── COL 2: DUELOS + RECUPERADAS + PÉRDIDAS ────────────────────────────
    y2 = TOP - 96

    y2 = bloque(c, X2, y2, CW, "Duelos 1 vs 1")
    y2 = stat_row(c, X2, y2, CW, "Of. ganados",   ind.get("dao_plus",0),  VERDE)
    y2 = stat_row(c, X2, y2, CW, "Of. perdidos",  ind.get("dao_minus",0), ROJO)
    y2 = stat_row(c, X2, y2, CW, "Def. ganados",  ind.get("dad_plus",0),  VERDE)
    y2 = stat_row(c, X2, y2, CW, "Def. perdidos", ind.get("dad_minus",0), ROJO)
    y2 = stat_row(c, X2, y2, CW, "Regate compl.", ind.get("regate_c",0),  VERDE)
    y2 = stat_row(c, X2, y2, CW, "Regate incompl.", ind.get("regate_i",0))
    y2 -= 4

    y2 = bloque(c, X2, y2, CW, "Duelos Aéreos")
    y2 = stat_row(c, X2, y2, CW, "Of. ganados",   ind.get("aereo_og",0), VERDE)
    y2 = stat_row(c, X2, y2, CW, "Of. perdidos",  ind.get("aereo_op",0), ROJO)
    y2 = stat_row(c, X2, y2, CW, "Def. ganados",  ind.get("aereo_dg",0), VERDE)
    y2 = stat_row(c, X2, y2, CW, "Def. perdidos", ind.get("aereo_dp",0), ROJO)
    y2 -= 4

    y2 = bloque(c, X2, y2, CW, "Recuperadas")
    y2 = stat_row(c, X2, y2, CW, "Posicional",    ind.get("recup_posic",0),  VERDE)
    y2 = stat_row(c, X2, y2, CW, "Intervención",  ind.get("recup_interv",0), VERDE)
    y2 = stat_row(c, X2, y2, CW, "Tras pérdida",  ind.get("recup_tras",0),   VERDE)
    y2 -= 4

    y2 = bloque(c, X2, y2, CW, "Pérdidas")
    y2 = stat_row(c, X2, y2, CW, "Por pase",    ind.get("perd_pase",0),    ROJO)
    y2 = stat_row(c, X2, y2, CW, "Por control", ind.get("perd_control",0), ROJO)
    y2 = stat_row(c, X2, y2, CW, "Por gambeta", ind.get("perd_gambeta",0), ROJO)

    # ── COL 3: INTERVENCIONES DEF + TÁCTICO ──────────────────────────────
    y3 = TOP - 96

    y3 = bloque(c, X3, y3, CW, "Intervenciones Defensivas")
    y3 = stat_row(c, X3, y3, CW, "Entradas gan.",  ind.get("interv_entrada_g",0),  VERDE)
    y3 = stat_row(c, X3, y3, CW, "Entradas perd.", ind.get("interv_entrada_p",0),  ROJO)
    y3 = stat_row(c, X3, y3, CW, "Anticipos gan.", ind.get("interv_anticipo_g",0), VERDE)
    y3 = stat_row(c, X3, y3, CW, "Anticipos perd.",ind.get("interv_anticipo_p",0), ROJO)
    y3 = stat_row(c, X3, y3, CW, "Intercepciones", ind.get("intercepciones",0))
    y3 = stat_row(c, X3, y3, CW, "Bloqueos",       ind.get("bloqueos",0))
    y3 -= 4

    y3 = bloque(c, X3, y3, CW, "Táctico")
    y3 = stat_row(c, X3, y3, CW, "Toques en área",     ind.get("toques_area",0),  AMBAR)
    y3 = stat_row(c, X3, y3, CW, "Ruptura conducción",  ind.get("ruptura",0))
    y3 = stat_row(c, X3, y3, CW, "Recep. entre líneas", ind.get("recep_lineas",0))
    y3 = stat_row(c, X3, y3, CW, "Recep. esp. volante", ind.get("recep_espal",0))
    y3 = stat_row(c, X3, y3, CW, "Recep. al espacio",   ind.get("recep_espacio",0))
    y3 -= 4

    y3 = bloque(c, X3, y3, CW, "Despejes")
    y3 = stat_row(c, X3, y3, CW, "Orientado",    ind.get("despeje_or",0), VERDE)
    y3 = stat_row(c, X3, y3, CW, "No orientado", ind.get("despeje_no",0))
    y3 -= 4

    y3 = bloque(c, X3, y3, CW, "Acciones")
    y3 = stat_row(c, X3, y3, CW, "Faltas recibidas", ind.get("faltas_rec",0))
    y3 = stat_row(c, X3, y3, CW, "Faltas hechas",    ind.get("faltas_hec",0))
    y3 = stat_row(c, X3, y3, CW, "+ Positivos",      ind.get("positivos",0),  VERDE)
    y3 = stat_row(c, X3, y3, CW, "- Negativos",      ind.get("negativos",0),  ROJO)

    # ── COL 4: MINUTOS JUGADOS ────────────────────────────────────────────
    y4 = TOP - 96
    y4 = bloque(c, X4, y4, CW, "Minutos Jugados — River Plate")

    for grupo_label, grupo_color in [("Titular", ROJO), ("Suplente", GRIS4)]:
        grupo = [p for p in (minutos_jugados or []) if p["condicion"] == grupo_label]
        if not grupo:
            continue
        c.setFillColor(GRIS3)
        c.rect(X4, y4 - 11, CW, 11, fill=1, stroke=0)
        c.setFillColor(GRISC)
        c.setFont("Helvetica-Bold", 5.5)
        c.drawString(X4 + 3, y4 - 8, grupo_label.upper() + "S")
        y4 -= 12

        for p in grupo:
            mins = p["minutos"]
            fill_w = min(CW - 4, (CW - 4) * mins / 90)
            c.setFillColor(GRIS2)
            c.rect(X4, y4 - 11, CW, 11, fill=1, stroke=0)
            c.setFillColor(grupo_color)
            c.rect(X4 + 2, y4 - 9, fill_w, 7, fill=1, stroke=0)
            c.setFillColor(BLANCO)
            c.setFont("Helvetica-Bold", 5.5)
            c.drawString(X4 + 4, y4 - 8, p["jugador"][:22])
            c.setFillColor(GRISC)
            c.drawRightString(X4 + CW - 3, y4 - 8, f"{mins}m")
            y4 -= 12

        y4 -= 4

    c.save()
    buf.seek(0)
    return buf.read()
