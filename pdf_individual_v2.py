"""
pdf_individual_v2.py — Informe Individual River360 (informe COMPLETO de 8 páginas)

Estética del dashboard web: fondo blanco, banda roja arriba, cards con borde gris,
tipografía zinc, semáforo verde/ámbar/rojo.

Estructura — 8 páginas:

  1. Portada · Identidad + KPIs hero + Análisis IA narrativo + Resumen ejecutivo
  2. Perfil táctico · Pizza chart por posición + Estilo + Top 5 fortalezas/debilidades
  3. Aporte ofensivo · Finalización + Remates por superficie + 1v1/regate + Penetración
  4. Construcción y juego con pelota · Pases + dirección + valor + centros + progresión
  5. Aporte defensivo · Recuperaciones + intercep + bloqueos + 1v1 def + aéreos + pérdidas
  6. Posicionamiento y movilidad · CG + dispersión + carriles + altura + zonas
  7. Comparación con el plantel · Rankings métrica a métrica con barras de percentil
  8. Conclusión + plan de mejora + calificación por área
"""

import io
import math
import os
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ─── Paleta — estética clara del dashboard ───────────────────────────────────
BLANCO   = colors.white
NEGRO    = colors.HexColor("#0a0a0a")
ROJO     = colors.HexColor("#dc2626")
ROJO_OSC = colors.HexColor("#5a0a10")
ROJO_LBL = colors.HexColor("#ff5a5a")
ZINC_50  = colors.HexColor("#fafafa")
ZINC_100 = colors.HexColor("#f4f4f5")
ZINC_200 = colors.HexColor("#e4e4e7")
ZINC_300 = colors.HexColor("#d4d4d8")
ZINC_400 = colors.HexColor("#a1a1aa")
ZINC_500 = colors.HexColor("#71717a")
ZINC_600 = colors.HexColor("#52525b")
ZINC_700 = colors.HexColor("#3f3f46")
ZINC_900 = colors.HexColor("#18181b")
VERDE    = colors.HexColor("#10b981")
VERDE_BG = colors.HexColor("#ecfdf5")
VERDE_BD = colors.HexColor("#a7f3d0")
AMBAR    = colors.HexColor("#f59e0b")
AMBAR_BG = colors.HexColor("#fffbeb")
AMBAR_BD = colors.HexColor("#fde68a")
ROJO_HOT = colors.HexColor("#ef4444")
RED_BG   = colors.HexColor("#fef2f2")
RED_BD   = colors.HexColor("#fecaca")
AZUL     = colors.HexColor("#3b82f6")
AZUL_BG  = colors.HexColor("#eff6ff")

W, H = landscape(A4)  # 841.89 × 595.28
MX = 32
HEADER_H = 38
FOOTER_H = 26
CONTENT_TOP = H - HEADER_H - 14
CONTENT_BOTTOM = FOOTER_H + 8

LOGO_PATH = os.path.join(os.path.dirname(__file__), "static", "logo.png")


def _logo_blanco():
    if not os.path.exists(LOGO_PATH):
        return None
    try:
        from PIL import Image
        im = Image.open(LOGO_PATH).convert("RGBA")
        pix = list(im.getdata())
        out = [(255, 255, 255, a) for _r, _g, _b, a in pix]
        im.putdata(out)
        return im
    except Exception:
        return None


_LOGO_BLANCO = _logo_blanco()


# ─── Primitivas ──────────────────────────────────────────────────────────────

def _fondo(c):
    c.setFillColor(BLANCO)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _header(c, titulo, partido):
    """Banda roja arriba con escudo + título + partido + fecha."""
    c.setFillColor(ROJO)
    c.rect(0, H - HEADER_H, W, HEADER_H, fill=1, stroke=0)
    if _LOGO_BLANCO is not None:
        try:
            c.drawImage(ImageReader(_LOGO_BLANCO), MX - 4, H - HEADER_H + 4,
                        width=26, height=30, mask="auto")
        except Exception:
            pass
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MX + 28, H - 22, titulo.upper())
    if partido:
        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(W - MX, H - 16, partido.upper())
    c.setFillColor(ZINC_200)
    c.setFont("Helvetica", 7)
    c.drawRightString(W - MX, H - 28, datetime.now().strftime("%d/%m/%Y · %H:%M"))


def _footer(c, num_pag, total=8):
    c.setStrokeColor(ZINC_200)
    c.setLineWidth(0.5)
    c.line(MX, FOOTER_H, W - MX, FOOTER_H)
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 7)
    c.drawString(MX, FOOTER_H - 12, "Departamento de Análisis de Datos · CARP · Fútbol Formativo")
    c.drawRightString(W - MX, FOOTER_H - 12, f"Página {num_pag} de {total}")


def _section_title(c, x, y, texto):
    """Título de sección con barra roja vertical a la izquierda."""
    c.setFillColor(ROJO)
    c.rect(x, y - 1, 3, 12, fill=1, stroke=0)
    c.setFillColor(ZINC_900)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 8, y, texto)
    return y - 18  # devuelve y para el siguiente elemento


def _card(c, x, y, w, h, fill=None, border=ZINC_200, radius=6):
    if fill is not None:
        c.setFillColor(fill)
        c.setStrokeColor(border)
        c.setLineWidth(0.5)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    else:
        c.setStrokeColor(border)
        c.setLineWidth(0.5)
        c.roundRect(x, y, w, h, radius, fill=0, stroke=1)


def _card_header(c, x, y, w, h, titulo, sub=None):
    """Card con título arriba (barra roja + texto), retorna y del contenido."""
    _card(c, x, y, w, h, fill=BLANCO)
    # Barra de título superior
    c.setFillColor(ZINC_50)
    c.rect(x + 0.5, y + h - 18, w - 1, 17, fill=1, stroke=0)
    c.setFillColor(ROJO)
    c.rect(x + 0.5, y + h - 18, 3, 17, fill=1, stroke=0)
    c.setFillColor(ZINC_900)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 10, y + h - 13, titulo)
    if sub:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 7.5)
        c.drawRightString(x + w - 8, y + h - 13, sub)
    return y + h - 24  # y de inicio del contenido


def _kpi_card(c, x, y, w, h, label, valor, sub="", tone=None):
    """Card vertical: label arriba, número grande centrado, sub abajo (sin solaparse)."""
    _card(c, x, y, w, h, fill=BLANCO)
    # Label
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 8, y + h - 12, label.upper())
    # Valor — bien arriba para que no choque con sub
    color = ZINC_900
    if tone == "green": color = VERDE
    elif tone == "amber": color = AMBAR
    elif tone == "red":   color = ROJO_HOT
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 19)
    c.drawString(x + 8, y + h - 32, str(valor))
    # Sub (opcional) — abajo del todo, con padding
    if sub:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 7)
        c.drawString(x + 8, y + 7, sub[:38])


def _draw_text_wrapped(c, x, y, w, texto, font="Helvetica", size=9, leading=12,
                       fill=ZINC_700):
    """Wrappea texto preservando <b>...</b> y <i>...</i> en línea. Retorna Y final."""
    c.setFillColor(fill)
    if not texto:
        return y

    parts = []
    i = 0
    while i < len(texto):
        if texto.startswith("<b>", i):
            end = texto.find("</b>", i)
            if end == -1:
                parts.append((texto[i:], False)); break
            parts.append((texto[i + 3:end], True))
            i = end + 4
        elif texto.startswith("<i>", i):
            end = texto.find("</i>", i)
            if end == -1:
                parts.append((texto[i:], False)); break
            parts.append((texto[i + 3:end], "italic"))
            i = end + 4
        else:
            indices = [p for p in [texto.find("<b>", i), texto.find("<i>", i)] if p != -1]
            next_tag = min(indices) if indices else len(texto)
            parts.append((texto[i:next_tag], False))
            i = next_tag

    tokens = []
    for txt, style in parts:
        for w_ in txt.split(" "):
            if w_:
                tokens.append((w_, style))

    def _font_for(style):
        if style is True: return "Helvetica-Bold"
        if style == "italic": return "Helvetica-Oblique"
        return font

    line = []
    cur_w = 0
    space_w = c.stringWidth(" ", font, size)

    for tok, style in tokens:
        f = _font_for(style)
        tw = c.stringWidth(tok, f, size)
        if line and cur_w + space_w + tw > w:
            cx = x
            for t2, st2 in line:
                f2 = _font_for(st2)
                c.setFont(f2, size)
                c.setFillColor(ZINC_900 if st2 is True else fill)
                c.drawString(cx, y, t2)
                cx += c.stringWidth(t2, f2, size) + space_w
            y -= leading
            line = []
            cur_w = 0
        if line: cur_w += space_w
        line.append((tok, style))
        cur_w += tw

    if line:
        cx = x
        for t2, st2 in line:
            f2 = _font_for(st2)
            c.setFont(f2, size)
            c.setFillColor(ZINC_900 if st2 is True else fill)
            c.drawString(cx, y, t2)
            cx += c.stringWidth(t2, f2, size) + space_w
        y -= leading

    return y


def _bar(c, x, y, w, pct, color=ROJO, h=4):
    """Barra horizontal de progreso 0-100%."""
    c.setFillColor(ZINC_100)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)
    if pct > 0:
        fw = max(h, w * min(100, pct) / 100)
        c.setFillColor(color)
        c.roundRect(x, y, fw, h, h / 2, fill=1, stroke=0)


def _metric_row(c, x, y, w, label, valor, tone=None, font_size=9):
    """Una fila de métrica: label izquierda, valor derecha."""
    c.setFillColor(ZINC_600)
    c.setFont("Helvetica", font_size)
    c.drawString(x, y, label)
    color = ZINC_900
    if tone == "green": color = VERDE
    elif tone == "amber": color = AMBAR
    elif tone == "red":   color = ROJO_HOT
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", font_size)
    c.drawRightString(x + w, y, str(valor))


def _metric_row_bar(c, x, y, w, label, valor, pct, tone=None):
    """Fila con label, valor y barra de progreso debajo."""
    c.setFillColor(ZINC_600)
    c.setFont("Helvetica", 9)
    c.drawString(x, y, label)
    color = ROJO
    if tone == "green": color = VERDE
    elif tone == "amber": color = AMBAR
    elif tone == "red":   color = ROJO_HOT
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(x + w, y, str(valor))
    _bar(c, x, y - 7, w, pct, color=color, h=3)


def _badge(c, x, y, w, h, texto, fill, fg=BLANCO):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(x + w / 2, y + h / 2 - 2.5, texto)


# ─── Stats helpers ───────────────────────────────────────────────────────────

def _percentil(valor, valores):
    if not valores: return 0
    orden = sorted(valores)
    pos = sum(1 for v in orden if v <= valor)
    return round(pos / len(orden) * 100)


def _rank_pos(valor, valores):
    ord_ = sorted(valores, reverse=True)
    for i, v in enumerate(ord_):
        if v == valor:
            return i + 1
    return 0


def _apellido_corto(nombre):
    partes = (nombre or "").split()
    if not partes: return "?"
    ult = partes[-1]
    import re
    if re.match(r"^[A-ZÁÉÍÓÚÑ]\.?$", ult) and len(partes) > 1:
        return partes[-2][:12]
    return ult[:12]


# ─── Detección posicional ───────────────────────────────────────────────────

METRICAS_POR_POSICION = {
    'def': [
        ('pases_efect',    '% Pase',         '%'),
        ('pct_progresivo', '% Progresivo',   '%'),
        ('recup_total',    'Recup.',         ''),
        ('intercepciones', 'Intercep.',      ''),
        ('aereo_dg',       'Aéreos Def +',   ''),
        ('dad_plus',       '1v1 Def +',      ''),
        ('despeje_or',     'Desp. or.',      ''),
        ('bloqueos',       'Bloqueos',       ''),
    ],
    'med': [
        ('pases_efect',      '% Pase',        '%'),
        ('pases_total',      'Pases tot.',    ''),
        ('pases_clave',      'P. clave',      ''),
        ('pases_filtrado',   'P. filtrado',   ''),
        ('pct_progresivo',   '% Progresivo',  '%'),
        ('recup_total',      'Recup.',        ''),
        ('dao_plus',         '1v1 Of +',      ''),
        ('progresion_media', 'Prog. media',   'm'),
    ],
    'atk': [
        ('remates_arco', 'Remates',     ''),
        ('goles',        'Goles',       ''),
        ('asistencias',  'Asistencias', ''),
        ('pct_area',     '% Área',      '%'),
        ('toques_area',  'Toques área', ''),
        ('regate_c',     'Regates +',   ''),
        ('dao_plus',     '1v1 Of +',    ''),
        ('pases_clave',  'P. clave',    ''),
    ],
}

POSICION_LABEL = {'def': 'DEFENSA', 'med': 'MEDIOCAMPO', 'atk': 'ATAQUE'}
POSICION_LBL_LARGO = {'def': 'línea defensiva', 'med': 'mediocampo', 'atk': 'ataque'}


def _calcular_lineas(jugadores, datos):
    """Clasifica por posición usando absoluto (no terciles):
    - El más cercano a nuestro arco = arquero (si gap suficiente con el 2do)
    - Los 4 siguientes más cercanos a nuestro arco = defensores
    - El resto se reparte mitad mediocampistas / mitad atacantes según CG x

    Robusto a equipos que juegan adelantado (todos los CG x altos).
    """
    elig = [(j, (datos[j].get('centro_grav_x') or 0)) for j in jugadores
            if datos.get(j) and (datos[j].get('minutos') or 0) >= 20
            and (datos[j].get('acciones_xy') or 0) > 0]
    if len(elig) < 6:
        return {j: 'med' for j, _ in elig}

    # Ordenar de menor a mayor CG x (de arco propio hacia arco rival)
    elig.sort(key=lambda e: e[1])
    linea = {}

    # Detectar arquero: si tiene CG x < 20 o gap >= 8 con el segundo
    inicio_def = 0
    if elig[0][1] < 20 or (len(elig) > 1 and elig[1][1] - elig[0][1] >= 8):
        linea[elig[0][0]] = 'def'  # arquero clasifica como defensa para análisis
        inicio_def = 1

    # Defensores: los 4 siguientes más cercanos al arco propio
    n_def = 4
    for j, _ in elig[inicio_def:inicio_def + n_def]:
        linea[j] = 'def'

    # Resto: mitad mediocampistas, mitad atacantes
    resto = elig[inicio_def + n_def:]
    if resto:
        n_med = (len(resto) + 1) // 2  # un poco más para medio si hay impar
        for j, _ in resto[:n_med]:
            linea[j] = 'med'
        for j, _ in resto[n_med:]:
            linea[j] = 'atk'
    return linea


def _posicion(nombre, datos):
    if not datos or nombre not in datos: return 'med'
    visibles = [j for j, d in datos.items()
                if (d.get('minutos') or 0) >= 20 and (d.get('acciones_xy') or 0) > 0]
    if len(visibles) < 6: return 'med'
    return _calcular_lineas(visibles, datos).get(nombre, 'med')


def _compañeros_linea(nombre, datos, posicion):
    visibles = [j for j, d in datos.items()
                if (d.get('minutos') or 0) >= 20 and (d.get('acciones_xy') or 0) > 0]
    if len(visibles) < 6:
        return [datos[j] for j in datos
                if j != nombre and (datos[j].get('intervenciones') or 0) >= 8]
    lineas = _calcular_lineas(visibles, datos)
    return [datos[j] for j in visibles
            if j != nombre and lineas.get(j) == posicion]


# ─── Estilo dominante ───────────────────────────────────────────────────────

ESTILOS = [
    ('area',         'Atacante de área',       ['pct_area', 'remates_arco', 'goles', 'toques_area'],
        'Especialista en jugadas dentro del área rival. Define oportunidades creadas por el equipo y lidera el ataque.'),
    ('creativo',     'Generador creativo',     ['pases_clave', 'pases_filtrado', 'recep_lineas', 'asistencias'],
        'Genera el juego con pases clave y filtrados. Se asocia entre líneas y desequilibra con visión.'),
    ('conductor',    'Encarador / Conductor',  ['dao_plus', 'ruptura', 'regate_c', 'pct_progresivo'],
        'Resuelve en 1v1 y rompe líneas con conducción. Atrae rivales y libera espacios.'),
    ('distribuidor', 'Distribuidor',           ['pases_efect', 'pases_largo_c', 'pases_total'],
        'Maneja el ritmo y la posesión. Altos volúmenes de pase con efectividad para girar el juego.'),
    ('recuperador',  'Recuperador alto',       ['recup_interv', 'recup_tras', 'pct_ultimo_tercio'],
        'Aprieta al rival y recupera por intervención en zonas adelantadas. Activa transiciones rápidas.'),
    ('cierre',       'Cierre defensivo',       ['intercepciones', 'bloqueos', 'dad_plus', 'recup_posic'],
        'Intercepta y bloquea. Gana duelos defensivos. Garantía atrás, lectura de juego para anticipar.'),
]


def _detectar_estilo(ind, plantel):
    candidatos = [j for j in plantel.values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) < 4:
        return 'Perfil mixto', 'Datos insuficientes para clasificar.', 0
    mejor = None
    mejor_pct = -1
    for _id, nombre, mets, desc in ESTILOS:
        scores = []
        for m in mets:
            valores = [j.get(m, 0) or 0 for j in candidatos]
            if max(valores) == 0: continue
            scores.append(_percentil(ind.get(m, 0) or 0, valores))
        if not scores: continue
        avg = sum(scores) / len(scores)
        if avg > mejor_pct:
            mejor_pct = avg
            mejor = (nombre, desc)
    if mejor is None:
        return 'Perfil mixto', 'Sin dominancia clara en ningún rol.', 0
    return mejor[0], mejor[1], round(mejor_pct)


# ─── Análisis IA narrativo ──────────────────────────────────────────────────

METRICAS_ANALISIS = [
    ('pases_efect',    '% Pase',         '%'),
    ('pct_progresivo', '% Progresivo',   '%'),
    ('pases_clave',    'pases clave',    ''),
    ('pases_filtrado', 'pases filtrados',''),
    ('pct_area',       '% en área',      '%'),
    ('remates_arco',   'remates',        ''),
    ('recup_posic',    'recup. posicional',''),
    ('recup_interv',   'recup. activas', ''),
    ('intercepciones', 'intercepciones', ''),
]


def _analisis_ia(ind, plantel):
    if not ind or not plantel: return ""
    candidatos = [j for j in plantel.values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) < 4: return ""
    lineas = []
    estilo, _, _ = _detectar_estilo(ind, plantel)
    cnt = f"{ind.get('intervenciones', 0)} intervenciones en {ind.get('minutos', 0)} min"

    if estilo and 'mixto' not in estilo.lower():
        lineas.append(f"{ind['jugador']} desplegó un perfil claro de <b>{estilo.lower()}</b>, sumando {cnt}.")
    else:
        lineas.append(f"{ind['jugador']} acumuló {cnt} sin un rol estadísticamente dominante.")

    if (ind.get('acciones_xy') or 0) >= 10:
        x = ind.get('centro_grav_x', 0) or 0
        dx = ind.get('dispersion_x', 0) or 0
        dy = ind.get('dispersion_y', 0) or 0
        if x >= 78:   s = f"Operó <b>muy cerca del arco rival</b> (CG x={x})"
        elif x >= 60: s = f"Operó <b>en zona alta-media</b> (CG x={x})"
        elif x >= 42: s = f"Operó <b>en zona media</b>, balanceando construcción y avance"
        else:          s = f"Operó <b>en zona baja</b> (CG x={x}), priorizando salida y cobertura"
        if dx >= 25 or dy >= 22: s += ", con <i>alta movilidad</i> por la cancha."
        elif dx <= 14 and dy <= 12: s += ", con un <i>posicionamiento muy estático</i>."
        else: s += "."
        lineas.append(s)

    fortalezas = []
    for k, label, unidad in METRICAS_ANALISIS:
        valores = [j.get(k, 0) or 0 for j in candidatos]
        if max(valores) == 0: continue
        v = ind.get(k, 0) or 0
        pct = _percentil(v, valores)
        if pct >= 75 and v > 0:
            fortalezas.append((label, v, unidad, pct, _rank_pos(v, valores)))
    fortalezas.sort(key=lambda f: f[3], reverse=True)
    if fortalezas:
        t = fortalezas[0]
        s = f"Destacó por <b>{t[1]}{t[2]} en {t[0]}</b> ({t[4]}º del plantel)"
        if len(fortalezas) >= 2:
            t2 = fortalezas[1]
            s += f" y <b>{t2[1]}{t2[2]} en {t2[0]}</b> ({t2[4]}º)"
        s += "."
        lineas.append(s)

    partes = []
    if ind.get('goles', 0): partes.append(f"<b>{ind['goles']} gol{'es' if ind['goles'] > 1 else ''}</b>")
    if ind.get('asistencias', 0): partes.append(f"<b>{ind['asistencias']} asistencia{'s' if ind['asistencias'] > 1 else ''}</b>")
    if not ind.get('asistencias', 0) and ind.get('pases_clave', 0) >= 2:
        partes.append(f"<b>{ind['pases_clave']} pases clave</b>")
    recup = (ind.get('recup_posic', 0) or 0) + (ind.get('recup_interv', 0) or 0) + (ind.get('recup_tras', 0) or 0)
    if recup >= 6:
        partes.append(f"<b>{recup} recuperaciones</b>")
    if partes:
        lineas.append(f"Aporte directo: {' + '.join(partes)}.")

    if ind.get('pct_area', 0) >= 5 and ind.get('toques_area', 0) >= 3:
        lineas.append(f"Frecuentó con peligrosidad el área rival (<b>{ind['toques_area']} toques</b>, {ind['pct_area']}% de sus acciones).")
    elif ind.get('pct_progresivo', 0) >= 35:
        lineas.append(f"Juego <b>marcadamente vertical</b>: {ind['pct_progresivo']}% de acciones progresivas.")
    elif ind.get('pases_efect', 0) >= 85 and ind.get('pases_total', 0) >= 30:
        lineas.append(f"Excelente efectividad de pase del <b>{ind['pases_efect']}%</b> sobre {ind['pases_total']} pases.")
    elif ind.get('pases_efect', 0) < 60 and ind.get('pases_total', 0) >= 20:
        lineas.append(f"Como aspecto a mejorar, su efectividad de pase ({ind['pases_efect']}%) quedó por debajo de lo deseado.")

    return " ".join(lineas)


# ─── Fortalezas / Debilidades extendidas ────────────────────────────────────

# Set completo de métricas — para página 7 (ranking exhaustivo)
METRICAS_RANKING = [
    ('pases_efect',     '% Efect. pase',        '%'),
    ('pases_clave',     'Pases clave',          ''),
    ('pases_filtrado',  'Pases filtrados',      ''),
    ('pases_largo_c',   'Pases largos compl.',  ''),
    ('pct_progresivo',  '% Acc. progresivas',   '%'),
    ('progresion_media','Progresión media',     'm'),
    ('pct_area',        '% Acc. en área',       '%'),
    ('toques_area',     'Toques en área',       ''),
    ('remates_arco',    'Remates al arco',      ''),
    ('goles',           'Goles',                ''),
    ('asistencias',     'Asistencias',          ''),
    ('dao_plus',        '1v1 Of. ganados',      ''),
    ('regate_c',        'Regates completados',  ''),
    ('ruptura',         'Rupturas en conducc.', ''),
    ('recep_lineas',    'Rec. entre líneas',    ''),
    ('recup_total',     'Recuperaciones',       ''),
    ('recup_interv',    'Recup. por interv.',   ''),
    ('intercepciones',  'Intercepciones',       ''),
    ('bloqueos',        'Bloqueos',             ''),
    ('despeje_or',      'Despejes orientados',  ''),
    ('dad_plus',        '1v1 Def. ganados',     ''),
    ('aereo_dg',        'Aéreos Def. ganados',  ''),
]

# Métricas RELEVANTES por posición — para fortalezas/debilidades (no rankear "1v1 of"
# como debilidad de un defensor: ese no es su rol)
METRICAS_RELEVANTES_DEF = [
    ('pases_efect',     '% Efect. pase',        '%'),
    ('pases_largo_c',   'Pases largos compl.',  ''),
    ('pct_progresivo',  '% Acc. progresivas',   '%'),
    ('progresion_media','Progresión media',     'm'),
    ('recup_total',     'Recuperaciones',       ''),
    ('recup_interv',    'Recup. por interv.',   ''),
    ('intercepciones',  'Intercepciones',       ''),
    ('bloqueos',        'Bloqueos',             ''),
    ('despeje_or',      'Despejes orientados',  ''),
    ('dad_plus',        '1v1 Def. ganados',     ''),
    ('aereo_dg',        'Aéreos Def. ganados',  ''),
]

METRICAS_RELEVANTES_MED = [
    ('pases_efect',     '% Efect. pase',        '%'),
    ('pases_clave',     'Pases clave',          ''),
    ('pases_filtrado',  'Pases filtrados',      ''),
    ('pases_largo_c',   'Pases largos compl.',  ''),
    ('pct_progresivo',  '% Acc. progresivas',   '%'),
    ('progresion_media','Progresión media',     'm'),
    ('recep_lineas',    'Rec. entre líneas',    ''),
    ('ruptura',         'Rupturas en conducc.', ''),
    ('dao_plus',        '1v1 Of. ganados',      ''),
    ('recup_total',     'Recuperaciones',       ''),
    ('recup_interv',    'Recup. por interv.',   ''),
    ('intercepciones',  'Intercepciones',       ''),
    ('dad_plus',        '1v1 Def. ganados',     ''),
]

METRICAS_RELEVANTES_ATK = [
    ('pases_clave',     'Pases clave',          ''),
    ('pases_filtrado',  'Pases filtrados',      ''),
    ('pct_area',        '% Acc. en área',       '%'),
    ('toques_area',     'Toques en área',       ''),
    ('remates_arco',    'Remates al arco',      ''),
    ('goles',           'Goles',                ''),
    ('asistencias',     'Asistencias',          ''),
    ('dao_plus',        '1v1 Of. ganados',      ''),
    ('regate_c',        'Regates completados',  ''),
    ('ruptura',         'Rupturas en conducc.', ''),
    ('recep_lineas',    'Rec. entre líneas',    ''),
    ('recep_espal',     'Rec. a la espalda',    ''),
    ('pct_progresivo',  '% Acc. progresivas',   '%'),
]

METRICAS_RELEVANTES_POR_POSICION = {
    'def': METRICAS_RELEVANTES_DEF,
    'med': METRICAS_RELEVANTES_MED,
    'atk': METRICAS_RELEVANTES_ATK,
}


def _ranking_para(ind, plantel, metricas_set):
    """Devuelve lista de (k, label, unidad, valor, pct, rank) para un set específico."""
    candidatos = [j for j in plantel.values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) < 4: return []
    out = []
    for k, label, unidad in metricas_set:
        valores = [j.get(k, 0) or 0 for j in candidatos]
        if max(valores) == 0: continue
        v = ind.get(k, 0) or 0
        if v == 0 and k != 'pases_efect': continue
        pct = _percentil(v, valores)
        rank = _rank_pos(v, valores)
        out.append((k, label, unidad, v, pct, rank))
    return out


def _ranking_completo(ind, plantel):
    """Ranking exhaustivo de todas las métricas — usado en página 7."""
    return _ranking_para(ind, plantel, METRICAS_RANKING)


def _ranking_por_posicion(ind, plantel):
    """Ranking filtrado por posición detectada — usado en fortalezas/debilidades."""
    posicion = _posicion(ind.get('jugador', ''), plantel)
    metricas = METRICAS_RELEVANTES_POR_POSICION.get(posicion, METRICAS_RELEVANTES_MED)
    return _ranking_para(ind, plantel, metricas)


# ─── PIZZA CHART POLAR (estética dashboard) ────────────────────────────────

def _pizza_polar(c, cx, cy, r_out, ind, plantel):
    nombre = ind.get('jugador', '')
    posicion = _posicion(nombre, plantel)
    comparables = _compañeros_linea(nombre, plantel, posicion)
    if len(comparables) < 2:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 9)
        c.drawCentredString(cx, cy, "Datos insuficientes")
        return posicion

    metricas = METRICAS_POR_POSICION[posicion]
    n = len(metricas)
    slice_ang = 2 * math.pi / n
    start_ang = -math.pi / 2
    r_min = r_out * 0.28
    GAP = 0.020

    # Fondo oscuro circular
    c.setFillColor(NEGRO)
    c.circle(cx, cy, r_out + 60, fill=1, stroke=0)

    # Anillos guía
    for s_ in [0.25, 0.5, 0.75, 1.0]:
        rr = r_min + s_ * (r_out - r_min)
        c.setStrokeColor(colors.HexColor("#2a1518"))
        c.setLineWidth(0.5)
        c.circle(cx, cy, rr, fill=0, stroke=1)

    # Separadores
    for i in range(n):
        ang = start_ang + (i + 0.5) * slice_ang
        c.setStrokeColor(NEGRO)
        c.setLineWidth(0.8)
        c.line(cx, cy, cx + math.cos(ang) * (r_out + 2), cy + math.sin(ang) * (r_out + 2))

    slices = []
    for i, (k, label, unidad) in enumerate(metricas):
        v = ind.get(k, 0) or 0
        comp_vals = [j.get(k, 0) or 0 for j in comparables]
        max_v = max([1, v] + comp_vals)
        pct = _percentil(v, comp_vals + [v])
        ang = start_ang + i * slice_ang
        r = r_min + (pct / 100.0) * (r_out - r_min)
        slices.append({'k': k, 'l': label, 'u': unidad, 'v': v, 'pct': pct,
                       'r': r, 'ang': ang, 'max': max_v, 'comp': comp_vals})

    for s in slices:
        a0 = s['ang'] - slice_ang / 2 + GAP
        a1 = s['ang'] + slice_ang / 2 - GAP
        path = c.beginPath()
        path.moveTo(cx, cy)
        for k in range(17):
            ang = a0 + (a1 - a0) * (k / 16)
            path.lineTo(cx + math.cos(ang) * s['r'], cy + math.sin(ang) * s['r'])
        path.close()
        c.saveState()
        try: c.setFillAlpha(0.82)
        except Exception: pass
        c.setFillColor(ROJO_OSC)
        c.setStrokeColor(ROJO_LBL)
        c.setLineWidth(0.7)
        c.drawPath(path, fill=1, stroke=1)
        c.restoreState()

    # Puntos grises de compañeros — con jittering perpendicular al eje radial
    # para que dos puntos con radios similares no se solapen
    for s in slices:
        if s['max'] == 0:
            continue
        # Calcular radio de cada compañero y ordenar
        radios = sorted([(cv / s['max']) * (r_out - r_min) + r_min for cv in s['comp']])
        # Detectar clusters: puntos con radios dentro de ~7 unidades = mismo grupo
        clusters = []
        for r in radios:
            if clusters and r - clusters[-1][-1] < 7:
                clusters[-1].append(r)
            else:
                clusters.append([r])
        # Calcular vector perpendicular al eje radial
        perp_x = -math.sin(s['ang'])
        perp_y =  math.cos(s['ang'])
        # Dibujar cada cluster con offsets perpendiculares simétricos
        for cluster in clusters:
            n = len(cluster)
            for idx, r in enumerate(cluster):
                # Offset: centrado en 0, distribuido +/- alternando
                if n == 1:
                    off = 0
                else:
                    pos_in_cluster = idx - (n - 1) / 2
                    off = pos_in_cluster * 5.5  # 5.5 unidades de separación lateral
                x = cx + math.cos(s['ang']) * r + perp_x * off
                y = cy + math.sin(s['ang']) * r + perp_y * off
                c.saveState()
                try: c.setFillAlpha(0.55)
                except Exception: pass
                c.setFillColor(ZINC_300)
                c.setStrokeColor(NEGRO)
                c.setLineWidth(0.35)
                c.circle(x, y, 2.7, fill=1, stroke=1)
                c.restoreState()

    for s in slices:
        x = cx + math.cos(s['ang']) * s['r']
        y = cy + math.sin(s['ang']) * s['r']
        c.setFillColor(ROJO_LBL)
        c.setStrokeColor(NEGRO)
        c.setLineWidth(0.7)
        c.circle(x, y, 4.2, fill=1, stroke=1)

    for s in slices:
        r = s['r'] + 11
        x = cx + math.cos(s['ang']) * r
        y = cy + math.sin(s['ang']) * r
        c.setFillColor(ROJO_LBL)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x, y - 2, f"{s['pct']}")

    for s in slices:
        r = r_out + 28
        x = cx + math.cos(s['ang']) * r
        y = cy + math.sin(s['ang']) * r
        lbl = s['l']
        w_lbl = max(50, len(lbl) * 4.7 + 14)
        c.setFillColor(colors.HexColor("#1a0a0c"))
        c.setStrokeColor(ROJO_LBL)
        c.setLineWidth(0.6)
        c.roundRect(x - w_lbl / 2, y - 8, w_lbl, 16, 8, fill=1, stroke=1)
        c.setFillColor(ROJO_LBL)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(x, y - 2, lbl)

    c.setFillColor(colors.HexColor("#1a0a0c"))
    c.setStrokeColor(ROJO_LBL)
    c.setLineWidth(1.2)
    c.circle(cx, cy, r_min - 6, fill=1, stroke=1)
    c.setFillColor(ROJO_LBL)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(cx, cy + 6, POSICION_LABEL[posicion])
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, cy - 7, _apellido_corto(nombre))
    c.setFillColor(ZINC_400)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(cx, cy - 18, f"vs {len(comparables)} comp.")
    return posicion


# ─── MINI CANCHA (para página de posicionamiento) ──────────────────────────

def _mini_cancha(c, x, y, w, h, cgx=None, cgy=None, dx=None, dy=None):
    """Cancha mini con el CG y elipse de dispersión del jugador."""
    # Cancha de fondo
    c.setFillColor(ZINC_50)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setStrokeColor(ZINC_300)
    c.setLineWidth(0.5)
    c.rect(x, y, w, h, fill=0, stroke=1)
    # Línea media
    c.line(x + w / 2, y, x + w / 2, y + h)
    # Círculo central
    c.circle(x + w / 2, y + h / 2, w * 0.075, fill=0, stroke=1)
    # Áreas
    area_w = w * 0.15
    area_h = h * 0.55
    c.rect(x, y + (h - area_h) / 2, area_w, area_h, fill=0, stroke=1)
    c.rect(x + w - area_w, y + (h - area_h) / 2, area_w, area_h, fill=0, stroke=1)
    # CG + dispersión
    if cgx is not None and cgy is not None:
        # mapear (0-120, 0-80) a (x..x+w, y..y+h) — y invertido
        px = x + (cgx / 120) * w
        py = y + (1 - (cgy / 80)) * h
        if dx is not None and dy is not None:
            # Dispersión: divisor sobre el rango real del campo (120 en x, 80 en y)
            # Factor 0.75 para que la elipse no domine visualmente
            ex = max(3, min(w * 0.28, (dx / 120) * w * 0.75))
            ey = max(3, min(h * 0.28, (dy / 80) * h * 0.75))
            c.saveState()
            try: c.setFillAlpha(0.18); c.setStrokeAlpha(0.6)
            except Exception: pass
            c.setFillColor(ROJO)
            c.setStrokeColor(ROJO)
            c.setLineWidth(0.8)
            c.ellipse(px - ex, py - ey, px + ex, py + ey, fill=1, stroke=1)
            c.restoreState()
        c.setFillColor(ROJO)
        c.setStrokeColor(BLANCO)
        c.setLineWidth(1)
        c.circle(px, py, 4, fill=1, stroke=1)


# ─── DIAGNÓSTICOS NARRATIVOS POR ÁREA ──────────────────────────────────────

def _diag_ofensivo(ind):
    partes = []
    rem = ind.get('remates_total', 0) or 0
    if rem >= 5:
        partes.append(f"Alto volumen de remate ({rem}) con {ind.get('remates_efect', 0)}% de efectividad.")
    elif rem >= 3:
        partes.append(f"{rem} remates con {ind.get('remates_efect', 0)}% de efectividad.")
    elif rem > 0:
        partes.append(f"Volumen bajo de remate ({rem}).")
    else:
        partes.append("No ejecutó remates.")

    if (ind.get('toques_area', 0) or 0) >= 5:
        partes.append(f"Frecuentó el área rival con {ind.get('toques_area', 0)} toques.")

    dao = (ind.get('dao_plus', 0) or 0) + (ind.get('dao_minus', 0) or 0)
    if dao >= 3:
        ef = round((ind.get('dao_plus', 0) or 0) / dao * 100)
        partes.append(f"{ind.get('dao_plus', 0)}/{dao} 1v1 OF ({ef}% efectividad).")
    return " ".join(partes) or "Sin actividad ofensiva relevante en este partido."


def _diag_construccion(ind):
    ef = ind.get('pases_efect', 0) or 0
    total = ind.get('pases_total', 0) or 0
    clave = ind.get('pases_clave', 0) or 0
    filt = ind.get('pases_filtrado', 0) or 0
    if total < 20:
        return f"Bajo volumen de pase ({total}). Difícil construir desde su posición o pocos minutos."
    base = f"{ef}% efectividad en {total} pases."
    if ef >= 80: base = "Excelente circulación: " + base
    elif ef < 60: base = "Efectividad por debajo del estándar: " + base
    if clave + filt >= 8:
        base += f" Aporte creativo notable ({clave} clave + {filt} filtrados)."
    elif clave + filt >= 4:
        base += f" Aporte creativo moderado ({clave} clave, {filt} filtrados)."
    return base


def _diag_defensivo(ind):
    rec = ind.get('recup_total', 0) or 0
    if rec == 0:
        return "Sin recuperaciones registradas."
    partes = []
    if rec >= 15: partes.append(f"Volumen muy alto de recuperación ({rec}).")
    elif rec >= 8: partes.append(f"{rec} recuperaciones — aporte defensivo notable.")
    else: partes.append(f"{rec} recuperaciones totales.")
    cgx = ind.get('centro_grav_x', 0) or 0
    if rec >= 5:
        if cgx > 70: partes.append("Presiona alto.")
        elif cgx < 35: partes.append("Recupera en zona propia.")
        else: partes.append("Recupera en bloque medio.")
    dad = (ind.get('dad_plus', 0) or 0) + (ind.get('dad_minus', 0) or 0)
    if dad >= 3:
        ef = round((ind.get('dad_plus', 0) or 0) / dad * 100)
        partes.append(f"{ef}% en 1v1 def.")
    return " ".join(partes)


def _diag_posicional(ind):
    partes = []
    cgx = ind.get('centro_grav_x', 0) or 0
    cgy = ind.get('centro_grav_y', 40) or 40
    if cgx >= 78: partes.append("Centro de gravedad muy avanzado, cerca del arco rival.")
    elif cgx >= 60: partes.append("Centro de gravedad en zona alta.")
    elif cgx >= 42: partes.append("Centro de gravedad en zona media.")
    else: partes.append("Centro de gravedad en zona baja, prioriza salida y cobertura.")
    if cgy >= 53: partes.append("Operó preferentemente por el carril derecho.")
    elif cgy <= 27: partes.append("Operó preferentemente por el carril izquierdo.")
    else: partes.append("Distribución equilibrada por los carriles.")
    dx = ind.get('dispersion_x', 0) or 0
    dy = ind.get('dispersion_y', 0) or 0
    if dx >= 25 or dy >= 22: partes.append("Alta movilidad y desplazamiento por la cancha.")
    elif dx <= 14 and dy <= 12: partes.append("Posicionamiento muy estático, zona acotada.")
    return " ".join(partes)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Portada + Análisis IA
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_1(c, ind, plantel, partido):
    _fondo(c)
    _header(c, f"Informe Individual · {ind.get('jugador', '')}", partido)

    # ─── HERO del jugador (h=80) ───
    hero_y = CONTENT_TOP - 80
    _card(c, MX, hero_y, W - 2 * MX, 80, fill=ZINC_50)

    # Nombre + posición + sub
    c.setFillColor(ZINC_900)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(MX + 18, hero_y + 50, ind.get('jugador', '').upper())

    pos_label = ''
    if plantel and len(plantel) >= 6:
        pos = _posicion(ind.get('jugador', ''), plantel)
        pos_label = POSICION_LABEL.get(pos, 'MEDIOCAMPO')

    # Badge de posición
    if pos_label:
        c.setFillColor(ROJO)
        bw = c.stringWidth(pos_label, "Helvetica-Bold", 9) + 16
        c.roundRect(MX + 18, hero_y + 26, bw, 14, 7, fill=1, stroke=0)
        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MX + 26, hero_y + 30, pos_label)

    # Sub
    sub_x = MX + 18 + (c.stringWidth(pos_label, "Helvetica-Bold", 9) + 24 if pos_label else 0)
    sub = f"{ind.get('condicion', '')} · {ind.get('minutos', 0)} min · {ind.get('intervenciones', 0)} intervenciones"
    c.setFillColor(ZINC_600)
    c.setFont("Helvetica", 10)
    c.drawString(sub_x, hero_y + 30, sub)

    # 6 KPI cards en la parte baja del hero
    kpi_total_w = W - 2 * MX - 32
    kpi_gap = 6
    kpi_w = (kpi_total_w - 5 * kpi_gap) / 6
    kpi_y = hero_y - 70
    kpi_h = 62
    pases_ef = ind.get('pases_efect', 0) or 0
    kpis = [
        ("Goles",       ind.get('goles', 0), "", "red" if (ind.get('goles', 0) or 0) > 0 else None),
        ("Asistencias", ind.get('asistencias', 0),
            f"{ind.get('asist_pases', 0)}P · {ind.get('asist_centros', 0)}C" if (ind.get('asist_pases', 0) + ind.get('asist_centros', 0)) > 0 else "",
            "amber" if (ind.get('asistencias', 0) or 0) > 0 else None),
        ("Pases clave", ind.get('pases_clave', 0),
            f"{ind.get('pases_filtrado', 0)} filtrados" if (ind.get('pases_filtrado', 0) or 0) > 0 else "", None),
        ("% Pase",      f"{pases_ef}%",
            f"{ind.get('pases_completos', 0)}/{ind.get('pases_total', 0)}",
            "green" if pases_ef >= 75 else ("amber" if pases_ef >= 60 else "red")),
        ("Recup. tot.", ind.get('recup_total', 0),
            f"intercep {ind.get('intercepciones', 0)}" if (ind.get('intercepciones', 0) or 0) > 0 else "",
            "green" if (ind.get('recup_total', 0) or 0) >= 10 else None),
        ("Toques área", ind.get('toques_area', 0),
            f"{ind.get('pct_area', 0)}% acciones" if (ind.get('pct_area', 0) or 0) > 0 else "",
            "green" if (ind.get('toques_area', 0) or 0) >= 5 else None),
    ]
    for i, (lbl, val, sub_kpi, tone) in enumerate(kpis):
        x = MX + 16 + i * (kpi_w + kpi_gap)
        _kpi_card(c, x, kpi_y, kpi_w, kpi_h, lbl, val, sub_kpi, tone)

    # ─── ANÁLISIS IA ───
    y = kpi_y - 28
    y = _section_title(c, MX, y, "Análisis del jugador · River360 IA")

    analisis_h = 160
    analisis_y = y - analisis_h + 10
    _card(c, MX, analisis_y, W - 2 * MX, analisis_h, fill=BLANCO)
    c.setFillColor(ROJO)
    c.rect(MX, analisis_y, 3, analisis_h, fill=1, stroke=0)

    texto = _analisis_ia(ind, plantel) if plantel else ""
    if not texto:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 10)
        c.drawString(MX + 18, analisis_y + analisis_h - 24,
                     "Análisis no disponible — se necesitan al menos 4 jugadores del plantel.")
    else:
        _draw_text_wrapped(c, MX + 18, analisis_y + analisis_h - 24,
                           W - 2 * MX - 36, texto,
                           font="Helvetica", size=11, leading=16, fill=ZINC_700)

    _footer(c, 1)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — Perfil táctico (pizza + estilo + top fortalezas/debilidades)
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_2(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Perfil táctico por posición", partido)

    if not plantel or len(plantel) < 4:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 11)
        c.drawCentredString(W / 2, H / 2, "Datos del plantel insuficientes para perfil posicional.")
        _footer(c, 2)
        return

    # Lado izq — Pizza chart (40% del ancho)
    pizza_w = (W - 2 * MX) * 0.42
    pizza_cx = MX + pizza_w / 2
    pizza_cy = H / 2 - 18
    pizza_r = min(pizza_w / 2 - 60, 115)
    _pizza_polar(c, pizza_cx, pizza_cy, pizza_r, ind, plantel)

    # Leyenda
    leyenda_y = pizza_cy - pizza_r - 75
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 8)
    c.drawCentredString(pizza_cx, leyenda_y,
                        "Cuña roja: percentil del jugador vs compañeros de su línea")
    c.drawCentredString(pizza_cx, leyenda_y - 11,
                        "Puntos grises: distribución de los compañeros")

    # Lado der — Estilo + Top 5 fortalezas + Top 5 debilidades
    der_x = MX + pizza_w + 20
    der_w = W - der_x - MX

    # Estilo dominante
    y = CONTENT_TOP
    y = _section_title(c, der_x, y, "Estilo dominante")
    estilo_nombre, estilo_desc, estilo_pct = _detectar_estilo(ind, plantel)
    estilo_card_h = 60
    _card(c, der_x, y - estilo_card_h + 6, der_w, estilo_card_h, fill=colors.HexColor("#fef2f5"), border=RED_BD)
    c.setFillColor(ROJO)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(der_x + 14, y - 12, estilo_nombre)
    if estilo_pct:
        _badge(c, der_x + der_w - 50, y - 16, 36, 12, f"p{estilo_pct}", ROJO)
    c.setFillColor(ZINC_600)
    next_y = _draw_text_wrapped(c, der_x + 14, y - 28, der_w - 28, estilo_desc,
                                font="Helvetica", size=8.5, leading=11, fill=ZINC_600)

    # Top 5 fortalezas y debilidades — usando SOLO métricas relevantes a la posición
    # del jugador (un defensor no debe tener "1v1 ofensivos" como debilidad)
    ranking = _ranking_por_posicion(ind, plantel)
    fortalezas = [r for r in ranking if r[4] >= 60]
    fortalezas = sorted(fortalezas, key=lambda r: r[4], reverse=True)[:5]
    keys_fortalezas = {f[0] for f in fortalezas}
    debilidades = [r for r in ranking if r[4] <= 50 and r[0] not in keys_fortalezas]
    debilidades = sorted(debilidades, key=lambda r: r[4])[:5]

    y = y - estilo_card_h - 10
    y = _section_title(c, der_x, y, "Top 5 fortalezas (destaca en)")
    row_h = 17
    if not fortalezas:
        _card(c, der_x, y - 22, der_w, row_h, fill=ZINC_50, border=ZINC_200)
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(der_x + 10, y - 17, "Sin métricas con percentil destacado.")
    for i, (k, label, unidad, valor, pct, rank) in enumerate(fortalezas):
        ry = y - (i + 1) * (row_h + 3) + 4
        _card(c, der_x, ry, der_w, row_h, fill=VERDE_BG, border=VERDE_BD)
        c.setFillColor(ZINC_700)
        c.setFont("Helvetica", 9)
        c.drawString(der_x + 10, ry + 5, label)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 9)
        valor_str = f"{valor}{unidad}"
        rank_str = f"  ·  {rank}º del plantel"
        c.drawString(der_x + der_w - 90, ry + 5, valor_str)
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 8)
        c.drawString(der_x + der_w - 90 + c.stringWidth(valor_str, "Helvetica-Bold", 9), ry + 5, rank_str)
        _badge(c, der_x + der_w - 36, ry + 3, 28, 11, f"p{pct}", VERDE)

    y = y - 5 * (row_h + 3) - 18
    y = _section_title(c, der_x, y, "Top 5 a mejorar")
    if not debilidades:
        _card(c, der_x, y - 22, der_w, row_h, fill=ZINC_50, border=ZINC_200)
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(der_x + 10, y - 17, "Sin métricas con percentil bajo (jugador completo).")
    for i, (k, label, unidad, valor, pct, rank) in enumerate(debilidades):
        ry = y - (i + 1) * (row_h + 3) + 4
        _card(c, der_x, ry, der_w, row_h, fill=AMBAR_BG, border=AMBAR_BD)
        c.setFillColor(ZINC_700)
        c.setFont("Helvetica", 9)
        c.drawString(der_x + 10, ry + 5, label)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 9)
        valor_str = f"{valor}{unidad}"
        c.drawString(der_x + der_w - 90, ry + 5, valor_str)
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 8)
        c.drawString(der_x + der_w - 90 + c.stringWidth(valor_str, "Helvetica-Bold", 9), ry + 5, f"  ·  {rank}º")
        _badge(c, der_x + der_w - 36, ry + 3, 28, 11, f"p{pct}", AMBAR)

    _footer(c, 2)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Aporte ofensivo (penetración + finalización)
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_3(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Aporte ofensivo · penetración y finalización", partido)

    y = CONTENT_TOP

    # Layout: 4 cards en grid 2x2 (top: Finalización + Remates por superficie)
    #                            (bot: Penetración + Duelos ofensivos)
    grid_gap = 12
    col_w = (W - 2 * MX - grid_gap) / 2
    row_h = 175

    # ─── Card 1: Finalización ───
    cy1 = y - row_h
    content_y = _card_header(c, MX, cy1, col_w, row_h,
                              "Finalización", f"Total: {ind.get('remates_total', 0)} remates")
    cy = content_y
    rem_tot = ind.get('remates_total', 0) or 0
    rem_ef = ind.get('remates_efect', 0) or 0
    _metric_row(c, MX + 14, cy, col_w - 28, "Goles", ind.get('goles', 0),
                "red" if (ind.get('goles', 0) or 0) > 0 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Remates al arco",
                f"{ind.get('remates_arco', 0)} / {rem_tot}",
                "green" if rem_tot > 0 and (ind.get('remates_arco', 0) / max(rem_tot, 1)) >= 0.5 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "% Efectividad", f"{rem_ef}%",
                "green" if rem_ef >= 50 else ("amber" if rem_ef >= 30 else None))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Afuera", ind.get('remates_afuera', 0))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Bloqueado", ind.get('remates_bloq', 0))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Sin definir", ind.get('rem_sd_total', 0))
    cy -= 22
    # Diagnóstico
    _draw_text_wrapped(c, MX + 14, cy, col_w - 28,
                       "<i>💬 " + _diag_ofensivo(ind) + "</i>",
                       font="Helvetica-Oblique", size=8, leading=10, fill=ZINC_500)

    # ─── Card 2: Remates por superficie ───
    cx2 = MX + col_w + grid_gap
    content_y = _card_header(c, cx2, cy1, col_w, row_h,
                              "Remates por superficie", "Cabeza · Pie hábil · Pie inhábil")
    cy = content_y
    superficies = [
        ('Cabeza',      'rem_cab_total', 'rem_cab_gol', 'rem_cab_efect'),
        ('Pie hábil',   'rem_pieh_total','rem_pieh_gol','rem_pieh_efect'),
        ('Pie inhábil', 'rem_piei_total','rem_piei_gol','rem_piei_efect'),
    ]
    # Header de tabla
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(cx2 + 14, cy, "SUPERFICIE")
    c.drawRightString(cx2 + col_w * 0.55, cy, "TOTAL")
    c.drawRightString(cx2 + col_w * 0.75, cy, "GOLES")
    c.drawRightString(cx2 + col_w - 14, cy, "% EFECT.")
    cy -= 4
    c.setStrokeColor(ZINC_200)
    c.line(cx2 + 14, cy, cx2 + col_w - 14, cy)
    cy -= 10
    for lbl, k_tot, k_gol, k_ef in superficies:
        tot = ind.get(k_tot, 0) or 0
        gol = ind.get(k_gol, 0) or 0
        ef = ind.get(k_ef, 0) or 0
        c.setFillColor(ZINC_900 if tot > 0 else ZINC_400)
        c.setFont("Helvetica", 9.5)
        c.drawString(cx2 + 14, cy, lbl)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawRightString(cx2 + col_w * 0.55, cy, str(tot))
        c.setFillColor(VERDE if gol > 0 else (ZINC_900 if tot > 0 else ZINC_400))
        c.drawRightString(cx2 + col_w * 0.75, cy, str(gol))
        if tot > 0:
            c.setFillColor(VERDE if ef >= 50 else (AMBAR if ef >= 30 else ROJO_HOT))
            c.drawRightString(cx2 + col_w - 14, cy, f"{ef}%")
        else:
            c.setFillColor(ZINC_400)
            c.drawRightString(cx2 + col_w - 14, cy, "—")
        cy -= 18
    cy -= 8
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Total al arco", ind.get('remates_arco', 0))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Total goles", ind.get('remates_gol', 0),
                "red" if (ind.get('remates_gol', 0) or 0) > 0 else None)

    # ─── Card 3: Penetración (abajo izquierda) ───
    cy3 = cy1 - row_h - 14
    content_y = _card_header(c, MX, cy3, col_w, row_h,
                              "Penetración y zona de área", "Acciones en zonas de definición")
    cy = content_y
    _metric_row(c, MX + 14, cy, col_w - 28, "Toques en área",
                ind.get('toques_area', 0),
                "green" if (ind.get('toques_area', 0) or 0) >= 5 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "% Acciones en área", f"{ind.get('pct_area', 0)}%",
                "amber" if (ind.get('pct_area', 0) or 0) >= 5 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "% Acciones último tercio",
                f"{ind.get('pct_ultimo_tercio', 0)}%",
                "green" if (ind.get('pct_ultimo_tercio', 0) or 0) >= 30 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Recepciones entre líneas",
                ind.get('recep_lineas', 0))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Recepciones a la espalda",
                ind.get('recep_espal', 0))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Recepciones en espacio",
                ind.get('recep_espacio', 0))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Rupturas en conducción",
                ind.get('ruptura', 0))

    # ─── Card 4: Duelos ofensivos + regates ───
    content_y = _card_header(c, cx2, cy3, col_w, row_h,
                              "Duelos 1v1 ofensivos · Regates · Asistencias", "")
    cy = content_y
    dao_p = ind.get('dao_plus', 0) or 0
    dao_m = ind.get('dao_minus', 0) or 0
    dao_t = dao_p + dao_m
    dao_ef = round(dao_p / dao_t * 100) if dao_t else 0
    _metric_row(c, cx2 + 14, cy, col_w - 28, "1v1 OF ganados",
                f"{dao_p} / {dao_t}",
                "green" if dao_ef >= 60 else ("amber" if dao_ef >= 40 else None))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "% Efectividad 1v1 OF",
                f"{dao_ef}%" if dao_t else "—",
                "green" if dao_ef >= 60 else ("amber" if dao_ef >= 40 else None))
    cy -= 16
    reg_c = ind.get('regate_c', 0) or 0
    reg_i = ind.get('regate_i', 0) or 0
    reg_t = reg_c + reg_i
    reg_ef = round(reg_c / reg_t * 100) if reg_t else 0
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Regates completados",
                f"{reg_c} / {reg_t}",
                "green" if reg_ef >= 60 else None)
    cy -= 16
    aero_p = ind.get('aereo_og', 0) or 0
    aero_m = ind.get('aereo_op', 0) or 0
    aero_t = aero_p + aero_m
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Aéreos OF ganados",
                f"{aero_p} / {aero_t}")
    cy -= 22
    c.setStrokeColor(ZINC_200)
    c.line(cx2 + 14, cy + 4, cx2 + col_w - 14, cy + 4)
    cy -= 4
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Asistencias totales",
                ind.get('asistencias', 0),
                "amber" if (ind.get('asistencias', 0) or 0) > 0 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Asistencias de pase",
                ind.get('asist_pases', 0))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Asistencias de centro",
                ind.get('asist_centros', 0))

    _footer(c, 3)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — Construcción y juego con pelota (técnico)
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_4(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Construcción y juego con pelota · técnico", partido)

    y = CONTENT_TOP

    # 2x2 grid otra vez
    grid_gap = 12
    col_w = (W - 2 * MX - grid_gap) / 2
    row_h = 175

    # ─── Card 1: Volumen + Efectividad de pase ───
    cy1 = y - row_h
    content_y = _card_header(c, MX, cy1, col_w, row_h,
                              "Volumen y efectividad de pase", "")
    cy = content_y
    ef = ind.get('pases_efect', 0) or 0
    tone_ef = "green" if ef >= 75 else ("amber" if ef >= 60 else "red")

    # Número grande % Pase
    c.setFillColor(VERDE if ef >= 75 else (AMBAR if ef >= 60 else ROJO_HOT))
    c.setFont("Helvetica-Bold", 36)
    c.drawString(MX + 14, cy - 20, f"{ef}%")
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 8.5)
    c.drawString(MX + 14, cy - 32, f"{ind.get('pases_completos', 0)} de {ind.get('pases_total', 0)} pases")
    # Barra grande
    _bar(c, MX + 14, cy - 45, col_w - 100, ef,
         color=VERDE if ef >= 75 else (AMBAR if ef >= 60 else ROJO_HOT), h=6)
    cy -= 70
    c.setStrokeColor(ZINC_200)
    c.line(MX + 14, cy + 4, MX + col_w - 14, cy + 4)
    cy -= 6
    _metric_row(c, MX + 14, cy, col_w - 28, "Total pases", ind.get('pases_total', 0))
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Completos", ind.get('pases_completos', 0), "green")
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Incompletos", ind.get('pases_incompletos', 0), "red")

    # ─── Card 2: Dirección de pases (con barras) ───
    cx2 = MX + col_w + grid_gap
    content_y = _card_header(c, cx2, cy1, col_w, row_h,
                              "Distribución por dirección", "Adelante · Lateral · Atrás")
    cy = content_y
    pa = ind.get('pases_adelante', 0) or 0
    pl = ind.get('pases_lateral', 0) or 0
    pat = ind.get('pases_atras', 0) or 0
    tot = pa + pl + pat or 1
    for lbl, v, color in [
        ("↑ Adelante", pa, VERDE),
        ("↔ Lateral",  pl, ZINC_500),
        ("↓ Atrás",    pat, AMBAR),
    ]:
        pct = round(v / tot * 100)
        c.setFillColor(ZINC_600)
        c.setFont("Helvetica", 9.5)
        c.drawString(cx2 + 14, cy, lbl)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawRightString(cx2 + col_w - 14, cy, f"{v}  ({pct}%)")
        cy -= 8
        _bar(c, cx2 + 14, cy, col_w - 28, pct, color=color, h=5)
        cy -= 16
    cy -= 6
    c.setStrokeColor(ZINC_200)
    c.line(cx2 + 14, cy + 4, cx2 + col_w - 14, cy + 4)
    cy -= 8
    _metric_row(c, cx2 + 14, cy, col_w - 28, "% Progresión",
                f"{ind.get('pct_progresivo', 0)}%",
                "green" if (ind.get('pct_progresivo', 0) or 0) >= 30 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Progresión media",
                f"{ind.get('progresion_media', 0)} m")
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Distancia media",
                f"{ind.get('distancia_media', 0)} m")

    # ─── Card 3: Pases de valor ───
    cy3 = cy1 - row_h - 14
    content_y = _card_header(c, MX, cy3, col_w, row_h,
                              "Pases de valor agregado", "Clave · filtrado · largos")
    cy = content_y
    _metric_row(c, MX + 14, cy, col_w - 28, "Pases clave",
                ind.get('pases_clave', 0),
                "green" if (ind.get('pases_clave', 0) or 0) >= 3 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Pases filtrados",
                ind.get('pases_filtrado', 0),
                "green" if (ind.get('pases_filtrado', 0) or 0) >= 3 else None)
    cy -= 16
    plc = ind.get('pases_largo_c', 0) or 0
    pli = ind.get('pases_largo_i', 0) or 0
    plt = plc + pli
    pl_ef = round(plc / plt * 100) if plt else 0
    _metric_row(c, MX + 14, cy, col_w - 28, "Largos completos / total",
                f"{plc} / {plt}")
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "% Efect. en pase largo",
                f"{pl_ef}%" if plt else "—",
                "green" if pl_ef >= 70 else None)
    cy -= 16
    _metric_row(c, MX + 14, cy, col_w - 28, "Pases de apoyo",
                ind.get('pases_apoyo', 0))
    cy -= 22
    _draw_text_wrapped(c, MX + 14, cy, col_w - 28,
                       "<i>💬 " + _diag_construccion(ind) + "</i>",
                       font="Helvetica-Oblique", size=8, leading=10, fill=ZINC_500)

    # ─── Card 4: Centros ───
    content_y = _card_header(c, cx2, cy3, col_w, row_h,
                              "Centros y asistencias por centro", "")
    cy = content_y
    cc = ind.get('centros_c', 0) or 0
    ci = ind.get('centros_i', 0) or 0
    ct = cc + ci
    c_ef = round(cc / ct * 100) if ct else 0

    c.setFillColor(VERDE if c_ef >= 35 else (AMBAR if c_ef >= 20 else (ROJO_HOT if ct else ZINC_400)))
    c.setFont("Helvetica-Bold", 30)
    c.drawString(cx2 + 14, cy - 18, f"{c_ef}%" if ct else "—")
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 8.5)
    c.drawString(cx2 + 14, cy - 30, f"{cc} de {ct} centros completos")
    _bar(c, cx2 + 14, cy - 42, col_w - 100, c_ef if ct else 0,
         color=VERDE if c_ef >= 35 else (AMBAR if c_ef >= 20 else ROJO_HOT), h=6)
    cy -= 60
    c.setStrokeColor(ZINC_200)
    c.line(cx2 + 14, cy + 4, cx2 + col_w - 14, cy + 4)
    cy -= 6
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Centros completos", cc, "green" if cc > 0 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Centros incompletos", ci)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Asistencias de centro",
                ind.get('asist_centros', 0),
                "amber" if (ind.get('asist_centros', 0) or 0) > 0 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Asistencias de pase",
                ind.get('asist_pases', 0),
                "amber" if (ind.get('asist_pases', 0) or 0) > 0 else None)

    _footer(c, 4)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — Aporte defensivo
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_5(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Aporte defensivo · recuperación, anticipación, contención", partido)

    y = CONTENT_TOP
    grid_gap = 12
    col_w = (W - 2 * MX - grid_gap) / 2
    row_h = 175

    # ─── Card 1: Recuperaciones ───
    cy1 = y - row_h
    content_y = _card_header(c, MX, cy1, col_w, row_h,
                              "Recuperaciones por tipo",
                              f"Total: {ind.get('recup_total', 0)}")
    cy = content_y
    rec_total = ind.get('recup_total', 0) or 0
    rec_pos = ind.get('recup_posic', 0) or 0
    rec_int = ind.get('recup_interv', 0) or 0
    rec_tra = ind.get('recup_tras', 0) or 0

    # Número grande
    c.setFillColor(VERDE if rec_total >= 10 else ZINC_900)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(MX + 14, cy - 20, str(rec_total))
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 8.5)
    c.drawString(MX + 14, cy - 32, "recuperaciones totales")
    cy -= 50

    for lbl, v, color in [
        ("Posicional",      rec_pos, VERDE),
        ("Por intervención", rec_int, ROJO),
        ("Tras pérdida",    rec_tra, AMBAR),
    ]:
        pct = round(v / rec_total * 100) if rec_total else 0
        c.setFillColor(ZINC_600)
        c.setFont("Helvetica", 9.5)
        c.drawString(MX + 14, cy, lbl)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawRightString(MX + col_w - 14, cy, f"{v}  ({pct}%)")
        cy -= 8
        _bar(c, MX + 14, cy, col_w - 28, pct, color=color, h=5)
        cy -= 16
    cy -= 12
    _draw_text_wrapped(c, MX + 14, cy, col_w - 28,
                       "<i>💬 " + _diag_defensivo(ind) + "</i>",
                       font="Helvetica-Oblique", size=8, leading=10, fill=ZINC_500)

    # ─── Card 2: Anticipación y bloqueo ───
    cx2 = MX + col_w + grid_gap
    content_y = _card_header(c, cx2, cy1, col_w, row_h,
                              "Anticipación, intercepción, bloqueo", "")
    cy = content_y
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Intercepciones",
                ind.get('intercepciones', 0),
                "green" if (ind.get('intercepciones', 0) or 0) >= 2 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Bloqueos",
                ind.get('bloqueos', 0))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Despejes orientados",
                ind.get('despeje_or', 0))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Despejes no orientados",
                ind.get('despeje_no', 0))
    cy -= 16
    # Total acciones defensivas
    total_def = (ind.get('intercepciones', 0) or 0) + (ind.get('bloqueos', 0) or 0) + \
                (ind.get('despeje_or', 0) or 0) + (ind.get('despeje_no', 0) or 0)
    c.setStrokeColor(ZINC_200)
    c.line(cx2 + 14, cy + 4, cx2 + col_w - 14, cy + 4)
    cy -= 6
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Total acc. defensivas",
                total_def,
                "green" if total_def >= 8 else None)
    cy -= 22
    # Duelos defensivos
    dad_p = ind.get('dad_plus', 0) or 0
    dad_m = ind.get('dad_minus', 0) or 0
    dad_t = dad_p + dad_m
    dad_ef = round(dad_p / dad_t * 100) if dad_t else 0
    _metric_row(c, cx2 + 14, cy, col_w - 28, "1v1 DEF ganados",
                f"{dad_p} / {dad_t}",
                "green" if dad_ef >= 60 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "% Efect. 1v1 DEF",
                f"{dad_ef}%" if dad_t else "—",
                "green" if dad_ef >= 60 else None)
    cy -= 16
    aer_p = ind.get('aereo_dg', 0) or 0
    aer_m = ind.get('aereo_dp', 0) or 0
    aer_t = aer_p + aer_m
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Aéreos DEF ganados",
                f"{aer_p} / {aer_t}")

    # ─── Card 3: Pérdidas (abajo izq) ───
    cy3 = cy1 - row_h - 14
    content_y = _card_header(c, MX, cy3, col_w, row_h,
                              "Pérdidas — control del balón",
                              f"Total: {ind.get('perd_total', 0)}")
    cy = content_y
    p_tot = ind.get('perd_total', 0) or 0
    p_pase = ind.get('perd_pase', 0) or 0
    p_ctrl = ind.get('perd_control', 0) or 0
    p_gamb = ind.get('perd_gambeta', 0) or 0

    c.setFillColor(AMBAR if p_tot >= 10 else (ZINC_900 if p_tot else ZINC_400))
    c.setFont("Helvetica-Bold", 36)
    c.drawString(MX + 14, cy - 20, str(p_tot))
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 8.5)
    c.drawString(MX + 14, cy - 32, "pérdidas totales")
    cy -= 50

    for lbl, v, color in [
        ("De pase",    p_pase, ROJO),
        ("De control", p_ctrl, AMBAR),
        ("De gambeta", p_gamb, ZINC_500),
    ]:
        pct = round(v / p_tot * 100) if p_tot else 0
        c.setFillColor(ZINC_600)
        c.setFont("Helvetica", 9.5)
        c.drawString(MX + 14, cy, lbl)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawRightString(MX + col_w - 14, cy, f"{v}  ({pct}%)")
        cy -= 8
        _bar(c, MX + 14, cy, col_w - 28, pct, color=color, h=5)
        cy -= 16

    # ─── Card 4: Faltas + disciplina ───
    content_y = _card_header(c, cx2, cy3, col_w, row_h,
                              "Disciplina y faltas", "")
    cy = content_y
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Faltas recibidas",
                ind.get('faltas_rec', 0))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Faltas cometidas",
                ind.get('faltas_hec', 0),
                "amber" if (ind.get('faltas_hec', 0) or 0) >= 3 else None)
    cy -= 16
    # Balance
    balance = (ind.get('faltas_rec', 0) or 0) - (ind.get('faltas_hec', 0) or 0)
    c.setStrokeColor(ZINC_200)
    c.line(cx2 + 14, cy + 4, cx2 + col_w - 14, cy + 4)
    cy -= 6
    _metric_row(c, cx2 + 14, cy, col_w - 28, "Balance (rec - com)",
                f"{'+' if balance > 0 else ''}{balance}",
                "green" if balance > 0 else ("amber" if balance < -2 else None))

    _footer(c, 5)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 6 — Posicionamiento y movilidad
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_6(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Posicionamiento, movilidad y ocupación del campo", partido)

    y = CONTENT_TOP
    # Layout: izquierda cancha grande + datos / derecha distribución por zonas
    izq_w = (W - 2 * MX - 16) * 0.50
    der_w = W - 2 * MX - izq_w - 16
    cy1 = y - 350

    # ─── Card 1: Mapa con CG + dispersión ───
    content_y = _card_header(c, MX, cy1, izq_w, 350,
                              "Centro de gravedad y dispersión",
                              f"CG ({ind.get('centro_grav_x', 0)}, {ind.get('centro_grav_y', 0)})")
    # Cancha mini
    cancha_w = izq_w - 28
    cancha_h = cancha_w * 0.667
    cancha_x = MX + 14
    cancha_y = content_y - cancha_h - 8
    _mini_cancha(c, cancha_x, cancha_y, cancha_w, cancha_h,
                 cgx=ind.get('centro_grav_x'), cgy=ind.get('centro_grav_y'),
                 dx=ind.get('dispersion_x'), dy=ind.get('dispersion_y'))

    # Leyenda
    cy = cancha_y - 14
    c.setFillColor(ZINC_500)
    c.setFont("Helvetica", 7.5)
    c.drawString(MX + 14, cy, "Punto rojo: CG.  Elipse: dispersión típica.  Cancha izq→der = avance del jugador")

    # Stats bajo el mapa
    cy -= 18
    stats_left = [
        ("Centro grav. x", ind.get('centro_grav_x', 0)),
        ("Centro grav. y", ind.get('centro_grav_y', 0)),
        ("Dispersión x",   ind.get('dispersion_x', 0)),
        ("Dispersión y",   ind.get('dispersion_y', 0)),
        ("Acciones con coord.", ind.get('acciones_xy', 0)),
    ]
    for lbl, v in stats_left:
        _metric_row(c, MX + 14, cy, izq_w - 28, lbl, v)
        cy -= 15

    # ─── Card 2: Distribución por zona ───
    cx2 = MX + izq_w + 16
    content_y = _card_header(c, cx2, cy1, der_w, 350,
                              "Distribución de acciones por zona", "")
    cy = content_y

    # % último tercio
    c.setFillColor(ZINC_700)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(cx2 + 14, cy, "Acciones por altura del campo")
    cy -= 18
    pct_ult3 = ind.get('pct_ultimo_tercio', 0) or 0
    pct_med = max(0, 100 - pct_ult3 - 30)  # aproximado si no tenemos breakdown exacto
    # Mejor: usar acciones_ult3 si está
    acc_xy = ind.get('acciones_xy', 0) or 1
    acc_ult3 = ind.get('acciones_ult3', 0) or 0
    acc_resto = acc_xy - acc_ult3
    pct_resto = round(acc_resto / acc_xy * 100) if acc_xy else 0

    for lbl, v, pct, color in [
        ("↑ Último tercio (x > 80)",  acc_ult3, pct_ult3, VERDE),
        ("Resto del campo",            acc_resto, pct_resto, ZINC_500),
    ]:
        c.setFillColor(ZINC_600)
        c.setFont("Helvetica", 9)
        c.drawString(cx2 + 14, cy, lbl)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(cx2 + der_w - 14, cy, f"{v}  ({pct}%)")
        cy -= 8
        _bar(c, cx2 + 14, cy, der_w - 28, pct, color=color, h=4)
        cy -= 16

    cy -= 6
    c.setFillColor(ZINC_700)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(cx2 + 14, cy, "Zonas de peligro (acciones de definición)")
    cy -= 18
    _metric_row(c, cx2 + 14, cy, der_w - 28, "% en último tercio",
                f"{pct_ult3}%",
                "green" if pct_ult3 >= 30 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, der_w - 28, "% en área rival",
                f"{ind.get('pct_area', 0)}%",
                "amber" if (ind.get('pct_area', 0) or 0) >= 5 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, der_w - 28, "Toques en área rival",
                ind.get('toques_area', 0),
                "green" if (ind.get('toques_area', 0) or 0) >= 5 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, der_w - 28, "Acciones progresivas (≥10m)",
                ind.get('acciones_progresivas', 0))
    cy -= 16
    _metric_row(c, cx2 + 14, cy, der_w - 28, "% Acciones progresivas",
                f"{ind.get('pct_progresivo', 0)}%",
                "green" if (ind.get('pct_progresivo', 0) or 0) >= 30 else None)
    cy -= 16
    _metric_row(c, cx2 + 14, cy, der_w - 28, "Progresión media por acción",
                f"{ind.get('progresion_media', 0)} m")
    cy -= 22
    _draw_text_wrapped(c, cx2 + 14, cy, der_w - 28,
                       "<i>💬 " + _diag_posicional(ind) + "</i>",
                       font="Helvetica-Oblique", size=8.5, leading=11, fill=ZINC_500)

    _footer(c, 6)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 7 — Rankings vs plantel
# ═══════════════════════════════════════════════════════════════════════════

def _pagina_7(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Comparación con el plantel · ranking métrica por métrica", partido)

    if not plantel or len(plantel) < 4:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 11)
        c.drawCentredString(W / 2, H / 2, "Plantel insuficiente para rankings.")
        _footer(c, 7)
        return

    ranking = _ranking_completo(ind, plantel)
    if not ranking:
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 11)
        c.drawCentredString(W / 2, H / 2, "Sin datos suficientes para rankings.")
        _footer(c, 7)
        return

    # Header: 4 cards de resumen arriba
    n_total = len(ranking)
    n_top10 = sum(1 for r in ranking if r[4] >= 90)
    n_top25 = sum(1 for r in ranking if r[4] >= 75)
    n_bot25 = sum(1 for r in ranking if r[4] <= 25)
    n_mid   = n_total - n_top25 - n_bot25

    cards_y = CONTENT_TOP - 60
    cards_w = (W - 2 * MX - 3 * 8) / 4
    for i, (lbl, val, tone) in enumerate([
        ("Métricas evaluadas", n_total, None),
        ("Top 10% (p ≥ 90)",   n_top10, "green"),
        ("Top 25% (p ≥ 75)",   n_top25, "green"),
        ("Bottom 25%",          n_bot25, "amber"),
    ]):
        x = MX + i * (cards_w + 8)
        _kpi_card(c, x, cards_y, cards_w, 60, lbl, val, "", tone)

    # Lista de rankings en 2 columnas
    cy_top = cards_y - 18
    cy_top = _section_title(c, MX, cy_top, "Ranking detallado (ordenado por percentil descendente)")

    ordenado = sorted(ranking, key=lambda r: r[4], reverse=True)
    col_w = (W - 2 * MX - 20) / 2
    row_h = 15
    rows_per_col = max(11, (len(ordenado) + 1) // 2)
    rows_per_col = min(rows_per_col, 20)

    for i, (k, label, unidad, valor, pct, rank) in enumerate(ordenado[:2 * rows_per_col]):
        col = i // rows_per_col
        row_in_col = i % rows_per_col
        x = MX + col * (col_w + 20)
        y = cy_top - 4 - (row_in_col + 1) * row_h

        # Background del row con color suave según percentil
        if pct >= 75:   bg = VERDE_BG
        elif pct >= 50: bg = colors.HexColor("#f4f4f5")
        elif pct >= 25: bg = AMBAR_BG
        else:            bg = RED_BG
        c.setFillColor(bg)
        c.rect(x, y - 1, col_w, row_h - 1, fill=1, stroke=0)

        c.setFillColor(ZINC_700)
        c.setFont("Helvetica", 8.5)
        c.drawString(x + 6, y + 3, label)
        c.setFillColor(ZINC_900)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawRightString(x + col_w - 56, y + 3, f"{valor}{unidad}")
        # Mini barra de percentil
        _bar(c, x + col_w - 50, y + 3, 28, pct,
             color=VERDE if pct >= 75 else (AMBAR if pct >= 25 else ROJO_HOT), h=4)
        # Percentil texto
        c.setFillColor(VERDE if pct >= 75 else (AMBAR if pct >= 25 else ROJO_HOT))
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x + col_w - 6, y + 3, f"p{pct}")

    _footer(c, 7)


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA 8 — Conclusión, plan de mejora, calificación
# ═══════════════════════════════════════════════════════════════════════════

def _calificar_areas(ind, plantel):
    """Devuelve dict con notas 0-100 por área basadas en percentiles del jugador."""
    if not plantel or len(plantel) < 4:
        return None
    candidatos = [j for j in plantel.values() if (j.get('intervenciones') or 0) >= 8]
    if len(candidatos) < 4: return None

    def avg_pct(keys):
        scores = []
        for k in keys:
            valores = [j.get(k, 0) or 0 for j in candidatos]
            if max(valores) == 0: continue
            v = ind.get(k, 0) or 0
            scores.append(_percentil(v, valores))
        return round(sum(scores) / len(scores)) if scores else 50

    return {
        'Ofensivo': avg_pct(['goles', 'asistencias', 'remates_arco', 'toques_area', 'pct_area', 'dao_plus']),
        'Técnico':  avg_pct(['pases_efect', 'pases_clave', 'pases_filtrado', 'regate_c', 'pases_largo_c']),
        'Táctico':  avg_pct(['pct_progresivo', 'progresion_media', 'pct_ultimo_tercio', 'recep_lineas']),
        'Defensivo': avg_pct(['recup_total', 'intercepciones', 'bloqueos', 'dad_plus', 'aereo_dg']),
    }


def _pagina_8(c, ind, plantel, partido):
    _fondo(c)
    _header(c, "Conclusión y plan de mejora", partido)

    y = CONTENT_TOP

    # ─── Calificación por área (4 medallones grandes) ───
    notas = _calificar_areas(ind, plantel)
    if notas:
        y = _section_title(c, MX, y, "Calificación por área")
        notas_y = y - 90
        medallon_w = (W - 2 * MX - 3 * 12) / 4
        for i, (area, nota) in enumerate(notas.items()):
            x = MX + i * (medallon_w + 12)
            color = VERDE if nota >= 75 else (AMBAR if nota >= 50 else ROJO_HOT)
            bg = VERDE_BG if nota >= 75 else (AMBAR_BG if nota >= 50 else RED_BG)
            bd = VERDE_BD if nota >= 75 else (AMBAR_BD if nota >= 50 else RED_BD)
            _card(c, x, notas_y, medallon_w, 80, fill=bg, border=bd)
            c.setFillColor(ZINC_700)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x + medallon_w / 2, notas_y + 64, area.upper())
            c.setFillColor(color)
            c.setFont("Helvetica-Bold", 34)
            c.drawCentredString(x + medallon_w / 2, notas_y + 26, str(nota))
            c.setFillColor(ZINC_500)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x + medallon_w / 2, notas_y + 14, "PERCENTIL PROMEDIO")
        # Nota global — todo alineado a misma baseline
        global_nota = round(sum(notas.values()) / len(notas))
        baseline = notas_y - 18
        c.setFillColor(ZINC_700)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MX, baseline, "Calificación global del jugador:")
        gcolor = VERDE if global_nota >= 75 else (AMBAR if global_nota >= 50 else ROJO_HOT)
        c.setFillColor(gcolor)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(MX + 180, baseline, str(global_nota))
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica", 8.5)
        c.drawString(MX + 215, baseline, "(promedio de las 4 áreas)")

    # ─── Plan: Fortalezas a mantener (3) + Aspectos a mejorar (3) ───
    plan_y = (notas_y - 38) if notas else (y - 30)

    # Fortalezas y debilidades por posición — un defensor no debe tener
    # debilidades ofensivas en su plan de mejora
    ranking = _ranking_por_posicion(ind, plantel) if plantel else []
    fortalezas = [r for r in ranking if r[4] >= 60]
    fortalezas = sorted(fortalezas, key=lambda r: r[4], reverse=True)[:3]
    keys_fortalezas = {f[0] for f in fortalezas}
    debilidades = [r for r in ranking if r[4] <= 50 and r[0] not in keys_fortalezas]
    debilidades = sorted(debilidades, key=lambda r: r[4])[:3]

    col_w = (W - 2 * MX - 16) / 2

    # Columna izq: Fortalezas
    y_izq = _section_title(c, MX, plan_y, "Fortalezas a mantener")
    if not fortalezas:
        _card(c, MX, y_izq - 38, col_w, 32, fill=ZINC_50, border=ZINC_200)
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(MX + 12, y_izq - 22, "Sin métricas con percentil destacado vs el plantel.")
    for i, (k, label, unidad, valor, pct, rank) in enumerate(fortalezas):
        ry = y_izq - 10 - i * 36
        _card(c, MX, ry - 28, col_w, 32, fill=VERDE_BG, border=VERDE_BD)
        c.setFillColor(VERDE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MX + 12, ry - 8, f"✓ {label}")
        c.setFillColor(ZINC_700)
        c.setFont("Helvetica", 8.5)
        suger = _sugerencia_fortaleza(k, valor, unidad, rank)
        _draw_text_wrapped(c, MX + 12, ry - 20, col_w - 24, suger,
                           font="Helvetica", size=8, leading=10, fill=ZINC_600)

    # Columna der: A mejorar
    x_der = MX + col_w + 16
    y_der = _section_title(c, x_der, plan_y, "Aspectos a mejorar")
    if not debilidades:
        _card(c, x_der, y_der - 38, col_w, 32, fill=ZINC_50, border=ZINC_200)
        c.setFillColor(ZINC_500)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(x_der + 12, y_der - 22, "Sin debilidades destacadas — jugador completo.")
    for i, (k, label, unidad, valor, pct, rank) in enumerate(debilidades):
        ry = y_der - 10 - i * 36
        _card(c, x_der, ry - 28, col_w, 32, fill=AMBAR_BG, border=AMBAR_BD)
        c.setFillColor(AMBAR)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_der + 12, ry - 8, f"▲ {label}")
        c.setFillColor(ZINC_700)
        c.setFont("Helvetica", 8.5)
        suger = _sugerencia_debilidad(k, valor, unidad, rank)
        _draw_text_wrapped(c, x_der + 12, ry - 20, col_w - 24, suger,
                           font="Helvetica", size=8, leading=10, fill=ZINC_600)

    # ─── Conclusión ejecutiva final ───
    concl_y_inicio = plan_y - 200
    concl_h = 110
    concl_y = concl_y_inicio - concl_h + 14
    _section_title(c, MX, concl_y_inicio, "Conclusión ejecutiva")
    _card(c, MX, concl_y, W - 2 * MX, concl_h, fill=BLANCO)
    c.setFillColor(ROJO)
    c.rect(MX, concl_y, 3, concl_h, fill=1, stroke=0)
    texto_concl = _conclusion_ejecutiva(ind, plantel, notas)
    if texto_concl:
        _draw_text_wrapped(c, MX + 18, concl_y + concl_h - 22, W - 2 * MX - 36, texto_concl,
                           font="Helvetica", size=10.5, leading=15, fill=ZINC_700)

    _footer(c, 8)


def _conclusion_ejecutiva(ind, plantel, notas):
    """Genera un texto de cierre que ata todo: estilo + rendimiento + recomendación final."""
    if not ind or not plantel: return ""
    estilo, _, _ = _detectar_estilo(ind, plantel)
    partes = []

    # Apertura — quién es el jugador
    nombre = ind.get('jugador', 'El jugador')
    if estilo and 'mixto' not in estilo.lower():
        partes.append(f"{nombre} responde al perfil de <b>{estilo.lower()}</b>.")
    else:
        partes.append(f"{nombre} presenta un perfil <b>mixto</b>, sin una vocación estadística clara.")

    # Diagnóstico por notas
    if notas:
        nota_max = max(notas, key=notas.get)
        nota_min = min(notas, key=notas.get)
        n_max = notas[nota_max]
        n_min = notas[nota_min]
        if n_max - n_min < 15:
            partes.append(f"Muestra un perfil <b>parejo</b> entre las cuatro áreas (todas en torno a p{round(sum(notas.values())/len(notas))}).")
        else:
            partes.append(f"Su mayor diferencial está en lo <b>{nota_max.lower()}</b> (p{n_max}), mientras que lo <b>{nota_min.lower()}</b> aparece como su área a fortalecer (p{n_min}).")

    # Recomendación según rol detectado
    rec_dict = {
        'Atacante de área':       "Trabajar movimientos previos al remate y carrera de tercer hombre para potenciar definición.",
        'Generador creativo':     "Pulir timing del pase clave y selección del último pase en zona de definición.",
        'Encarador / Conductor':  "Sostener encaramientos clave, mejorar selección entre regate y pase posterior.",
        'Distribuidor':           "Mantener volumen y efectividad; sumar verticalidad sin bajar el % de pase.",
        'Recuperador alto':       "Conservar intensidad sin balón; mejorar la primera salida tras recuperación.",
        'Cierre defensivo':       "Sostener lectura de juego; trabajar despeje orientado y salida con pelota.",
    }
    rec = rec_dict.get(estilo)
    if rec:
        partes.append(f"Recomendación: {rec}")

    # Aporte directo
    aporte = []
    if ind.get('goles', 0): aporte.append(f"{ind['goles']} gol(es)")
    if ind.get('asistencias', 0): aporte.append(f"{ind['asistencias']} asistencia(s)")
    if ind.get('recup_total', 0) >= 8: aporte.append(f"{ind['recup_total']} recuperaciones")
    if ind.get('pases_clave', 0) >= 4: aporte.append(f"{ind['pases_clave']} pases clave")
    if aporte:
        partes.append(f"Aporte directo del partido: <b>{', '.join(aporte)}</b>.")

    return " ".join(partes)


def _sugerencia_fortaleza(k, valor, unidad, rank):
    base = {
        'pases_efect':    f"Sostener {valor}{unidad} con riesgo controlado al avanzar la pelota.",
        'pases_clave':    f"Mantener volumen de creación. Buscar finalización tras los {valor} pases clave.",
        'pases_filtrado': f"{valor} filtrados — clave para romper líneas. Repetir en próximos partidos.",
        'pct_progresivo': f"Verticalidad ({valor}%) le da diferencial. Combinar con efectividad.",
        'pct_area':       f"{valor}% en área — sostener esa presencia agresiva en zonas de definición.",
        'toques_area':    f"{valor} toques en área = potencial goleador. Trabajar última definición.",
        'remates_arco':   f"{valor} remates al arco — volumen alto, foco en mejorar selección.",
        'goles':          f"{valor} goles — rol definitorio. Reforzar movimientos previos.",
        'asistencias':    f"{valor} asistencias — visión privilegiada. Combinar con propio gol.",
        'dao_plus':       f"{valor} 1v1 ofensivos ganados — encaramiento neto. Mantener decisión.",
        'regate_c':       f"{valor} regates completos — recurso constante. Combinar con pase posterior.",
        'recup_total':    f"{valor} recuperaciones — pilar del balance. Sostener intensidad.",
        'recup_interv':   f"{valor} recup. activas — agresividad clave. Mantener anticipación.",
        'intercepciones': f"{valor} intercepciones — lectura de juego destacada. Confiar en el anticipo.",
        'bloqueos':       f"{valor} bloqueos — cuerpo presente. Mantener compromiso defensivo.",
        'dad_plus':       f"{valor} 1v1 def ganados — confiabilidad en marca. Mantener postura.",
        'aereo_dg':       f"{valor} aéreos def — referencia por arriba. Sostener despeje primer palo.",
        'despeje_or':     f"{valor} despejes orientados — buen criterio bajo presión.",
    }
    return base.get(k, f"Mantener nivel de {valor}{unidad} ({rank}º del plantel).")


def _sugerencia_debilidad(k, valor, unidad, rank):
    base = {
        'pases_efect':    f"Trabajar selección de pase. Reducir riesgo en su zona, mejorar perfil para recibir.",
        'pases_clave':    f"Buscar más pases en zonas de definición. Pedir balón entre líneas.",
        'pases_filtrado': f"Sumar pases que rompan líneas. Trabajar timing del pase entre 2 marcadores.",
        'pct_progresivo': f"Verticalizar más cuando recibe. Reducir el pase de seguridad.",
        'pct_area':       f"Aumentar incursiones al área. Trabajar carrera de tercer hombre.",
        'toques_area':    f"Llegar más al área cuando hay generación por banda. Movilidad sin balón.",
        'remates_arco':   f"Buscar terminación en zonas de definición. Practicar primer toque al arco.",
        'goles':          f"Trabajar definición — anticipación al portero y aprovechamiento de centros.",
        'asistencias':    f"Mejorar elección del último pase. Identificar mejor al compañero libre.",
        'dao_plus':       f"Trabajar 1v1 frontal. Cambio de ritmo, perfil de cuerpo, fintas.",
        'regate_c':       f"Reducir la cantidad de regates fallidos. Identificar cuándo soltar la pelota.",
        'recup_total':    f"Mayor intensidad sin balón. Anticipar trayectorias del rival.",
        'recup_interv':   f"Más agresividad en presión y duelos. Ganar metros adelantados.",
        'intercepciones': f"Mejorar lectura del pase rival. Estudiar tendencias del adversario.",
        'bloqueos':       f"Cuerpo presente entre rival y arco. Carrera de cobertura.",
        'dad_plus':       f"Trabajar duelos defensivos: timing del barrido, postura corporal.",
        'aereo_dg':       f"Mejorar timing en el salto. Despejar al primer palo en córner defensivo.",
        'despeje_or':     f"Cuando despeja, hacerlo a sectores seguros. Buscar al lateral o el out.",
    }
    return base.get(k, f"Aspecto a trabajar: {valor}{unidad} ({rank}º del plantel).")


# ─── ENTRY POINT ────────────────────────────────────────────────────────────

def generar_pdf_individual_v2(ind, partido, minutos=None, todos_jug=None, coords=None):
    """Genera informe individual de 8 páginas — completo y narrativo."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    plantel = todos_jug or {}

    _pagina_1(c, ind, plantel, partido); c.showPage()
    _pagina_2(c, ind, plantel, partido); c.showPage()
    _pagina_3(c, ind, plantel, partido); c.showPage()
    _pagina_4(c, ind, plantel, partido); c.showPage()
    _pagina_5(c, ind, plantel, partido); c.showPage()
    _pagina_6(c, ind, plantel, partido); c.showPage()
    _pagina_7(c, ind, plantel, partido); c.showPage()
    _pagina_8(c, ind, plantel, partido); c.showPage()

    c.save()
    return buf.getvalue()
