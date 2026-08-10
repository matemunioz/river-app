"""
biblioteca.py — Biblioteca de partidos leída desde una carpeta.

El objetivo es que el videoanalista NO tenga que subir los CSVs a mano: exporta
de Sportcode a la carpeta compartida del área y la app los ve solos.

La carpeta puede ser:
  · una carpeta local (hoy)
  · la carpeta de OneDrive sincronizada en la máquina
  · en el futuro, una copia que baje un poller desde Microsoft Graph
En los tres casos esto lee del filesystem, así que el resto de la app no cambia.

Config: variable de entorno RIVER_BIBLIOTECA_DIR. Si no está, se prueban rutas
conocidas (OneDrive sincronizado, ~/RiverData).

Un partido se identifica por un id estable derivado de su ruta relativa, así el
frontend puede pedirlo sin conocer el filesystem ni recibir el CSV crudo — que
es justamente lo que queremos evitar, porque tienen nombres de menores.
"""

import hashlib
import os
import re
import unicodedata
from glob import glob

import pandas as pd

import parser as sc

EXTS = (".csv", ".xlsx", ".xls")

# División tal como aparece en el nombre del archivo o la carpeta
_DIVISIONES = ["4ta", "5ta", "6ta", "7ma", "8va", "9na", "reserva", "primera"]


# Nombres de carpeta que reconocemos como biblioteca de partidos
_PATRONES_CARPETA = ["Datos_Estadisticos_*", "Datos_estadisticos_*", "datos_estadisticos_*"]

# Dónde buscar, en orden de preferencia. La sincronizada de OneDrive gana sobre
# la copia local, así que apenas el analista sincroniza la carpeta del área la
# app pasa a leer la de verdad sin tocar nada.
_BASES = [
    "Library/CloudStorage/OneDrive-*",           # OneDrive corporativo (macOS)
    "Library/CloudStorage/OneDrive-*/*",         # dentro de una subcarpeta
    "Library/CloudStorage/OneDrive-*/*/*",
    "Library/CloudStorage/SharePoint-*",         # bibliotecas de sitio sincronizadas
    "Library/CloudStorage/SharePoint-*/*",
    "OneDrive*",                                 # sync viejo, fuera de CloudStorage
    "OneDrive*/*",
    "Library/Mobile Documents/com~apple~CloudDocs",  # iCloud
    "RiverData",                                 # copia local
    "Documents",
    "Desktop",
]


def _candidatos_raiz() -> list:
    """Rutas donde puede estar la carpeta de datos, en orden de preferencia."""
    env = os.environ.get("RIVER_BIBLIOTECA_DIR")
    if env:
        return [os.path.expanduser(env)]
    home = os.path.expanduser("~")
    cands = []
    for base in _BASES:
        for pat in _PATRONES_CARPETA:
            cands += sorted(glob(os.path.join(home, base, pat)))
    # sin duplicados, conservando el orden de preferencia
    vistos, unicos = set(), []
    for c in cands:
        real = os.path.realpath(c)
        if real not in vistos:
            vistos.add(real)
            unicos.append(c)
    return unicos


def _tiene_partidos(d: str) -> bool:
    """La carpeta sirve si tiene al menos un CSV/XLSX en ella o en sus subcarpetas."""
    for dirpath, _dirs, files in os.walk(d):
        if any(f.lower().endswith(EXTS) and not f.startswith(".") for f in files):
            return True
    return False


def raiz() -> str | None:
    """Carpeta activa de la biblioteca, o None si no hay ninguna disponible."""
    primero_existente = None
    for c in _candidatos_raiz():
        if c and os.path.isdir(c):
            if _tiene_partidos(c):
                return c
            primero_existente = primero_existente or c
    # Existe pero está vacía (p. ej. OneDrive recién sincronizado): la devolvemos
    # igual para que la UI muestre la ruta y no un "no encuentro nada".
    return primero_existente


def diagnostico() -> dict:
    """Qué carpetas se probaron — para explicar en la UI por qué no encuentra."""
    return {
        "env": os.environ.get("RIVER_BIBLIOTECA_DIR"),
        "candidatos": [{"ruta": c, "existe": os.path.isdir(c)} for c in _candidatos_raiz()],
        "elegida": raiz(),
    }


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _parsear_nombre(rel: str) -> dict:
    """Saca división, fecha y rival del nombre/ruta del archivo.

    Formatos reales vistos en la carpeta del área:
        4TA_F10_Colon.csv · 5ta_F13_Estudiantes LP.csv · CSV_9na_F9_Boca.csv
    """
    carpeta = os.path.dirname(rel)
    base = os.path.splitext(os.path.basename(rel))[0]
    nb = _norm(base)

    division = None
    for d in _DIVISIONES:
        if re.search(rf"\b{d}\b", nb) or re.search(rf"\b{d}\b", _norm(carpeta)):
            division = d
            break

    # "F10" en 4TA_F10_Colon. Ojo: \b no sirve porque '_' es caracter de palabra,
    # así que el separador se pide explícito (o inicio de nombre).
    m = re.search(r"(?:^|[_\-\s])f\s*(\d{1,2})(?=$|[_\-\s.])", nb)
    fecha = int(m.group(1)) if m else None

    # Rival: lo que queda después del último separador tras división/fecha
    rival = base
    partes = re.split(r"[_\-]", base)
    if len(partes) >= 2:
        # descartar tokens que sean 'CSV', la división o la fecha
        utiles = [p for p in partes
                  if not re.fullmatch(r"(?i)csv", p.strip())
                  and _norm(p.strip()) not in _DIVISIONES
                  and not re.fullmatch(r"(?i)f\s*\d{1,2}", p.strip())]
        if utiles:
            rival = " ".join(utiles).strip()

    return {"division": division, "fecha": fecha, "rival": rival or base}


def _id_de(rel: str) -> str:
    """Id estable y corto a partir de la ruta relativa."""
    return hashlib.sha1(rel.encode("utf-8")).hexdigest()[:12]


def listar(base: str | None = None) -> dict:
    """Inventario de la carpeta: partidos disponibles, agrupables por división."""
    base = base or raiz()
    if not base:
        return {"disponible": False, "carpeta": None, "partidos": [],
                "diagnostico": diagnostico()}

    partidos = []
    for dirpath, _dirs, files in os.walk(base):
        # ignorar basura del sistema y carpetas ocultas
        if any(p.startswith(".") for p in os.path.relpath(dirpath, base).split(os.sep) if p not in (".", "")):
            continue
        for f in sorted(files):
            if f.startswith(".") or not f.lower().endswith(EXTS):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, base)
            try:
                st = os.stat(full)
            except OSError:
                continue
            meta = _parsear_nombre(rel)
            partidos.append({
                "id": _id_de(rel),
                "archivo": rel,
                "nombre": os.path.splitext(f)[0],
                "division": meta["division"],
                "fecha": meta["fecha"],
                "rival": meta["rival"],
                "bytes": st.st_size,
                "modificado": int(st.st_mtime),
            })

    # Orden natural: división y después número de fecha
    orden_div = {d: i for i, d in enumerate(_DIVISIONES)}
    partidos.sort(key=lambda p: (orden_div.get(p["division"] or "", 99),
                                 p["fecha"] if p["fecha"] is not None else 999,
                                 p["nombre"]))
    return {"disponible": True, "carpeta": base, "partidos": partidos}


# Índice id → ruta relativa. Sin esto, resolver N partidos hacía N recorridos
# completos de la carpeta (sobre OneDrive eso son cientos de ms cada uno).
_INDICE: dict = {}
_INDICE_BASE: str | None = None


def _indice(base: str) -> dict:
    global _INDICE, _INDICE_BASE
    if _INDICE_BASE != base or not _INDICE:
        _INDICE = {p["id"]: p["archivo"] for p in listar(base)["partidos"]}
        _INDICE_BASE = base
    return _INDICE


def _ruta_de_id(pid: str, base: str | None = None) -> str | None:
    base = base or raiz()
    if not base:
        return None
    rel = _indice(base).get(pid)
    if rel is None:
        # puede ser un partido agregado después de armar el índice
        _INDICE.clear()
        rel = _indice(base).get(pid)
        if rel is None:
            return None
    full = os.path.realpath(os.path.join(base, rel))
    # Defensa: nunca salir de la carpeta configurada
    if not full.startswith(os.path.realpath(base) + os.sep):
        return None
    return full


# ─── Caché de DataFrames ya enriquecidos ─────────────────────────────────────
# Leer + enriquecer el mismo CSV en cada pantalla es el grueso del costo actual.
# La clave incluye mtime y tamaño, así un archivo actualizado se re-lee solo.

_CACHE: dict = {}
_CACHE_MAX = 24  # ~24 partidos enriquecidos; suficiente para una división entera


def _clave(full: str) -> tuple:
    st = os.stat(full)
    return (full, int(st.st_mtime), st.st_size)


def leer_df(pid: str, base: str | None = None) -> pd.DataFrame:
    """DataFrame enriquecido de un partido de la biblioteca."""
    full = _ruta_de_id(pid, base)
    if not full or not os.path.isfile(full):
        raise FileNotFoundError(f"Partido '{pid}' no está en la biblioteca")

    k = _clave(full)
    if k in _CACHE:
        return _CACHE[k].copy()

    ext = os.path.splitext(full)[1].lower()
    with open(full, "rb") as fh:
        df = sc.leer_desde_bytes(fh.read(), ext)

    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[k] = df
    return df.copy()


def limpiar_cache() -> None:
    _CACHE.clear()
    _RESUMEN.clear()
    _INDICE.clear()


# ─── Resumen rápido por partido (para el panel principal) ────────────────────
# Sólo el resultado: no hace falta enriquecer el DataFrame ni calcular nada más.
# Se lee con el módulo csv (mucho más liviano que pandas para esto) y se cachea
# por (ruta, mtime, tamaño), así al abrir el panel la segunda vez es inmediato.

_RESUMEN: dict = {}


def resumen_partido(pid: str, base: str | None = None) -> dict | None:
    """{gf, gc, resultado} de un partido, leyendo sólo la columna Row."""
    full = _ruta_de_id(pid, base)
    if not full or not os.path.isfile(full):
        return None
    k = _clave(full)
    if k in _RESUMEN:
        return _RESUMEN[k]

    gf = gc = 0
    ext = os.path.splitext(full)[1].lower()
    try:
        if ext == ".csv":
            import csv
            with open(full, newline="", encoding="utf-8", errors="replace") as fh:
                r = csv.reader(fh)
                hdr = next(r, None)
                if hdr is None:
                    return None
                try:
                    i_row = hdr.index("Row")
                except ValueError:
                    return None
                for fila in r:
                    if len(fila) > i_row:
                        v = fila[i_row]
                        if v == "Goles Propios":
                            gf += 1
                        elif v == "Goles Rivales":
                            gc += 1
        else:
            df = pd.read_excel(full, usecols=["Row"])
            gf = int((df["Row"] == "Goles Propios").sum())
            gc = int((df["Row"] == "Goles Rivales").sum())
    except Exception:
        return None

    out = {"gf": gf, "gc": gc,
           "resultado": "G" if gf > gc else "P" if gf < gc else "E"}
    _RESUMEN[k] = out
    return out


def panel() -> dict:
    """Resumen de toda la biblioteca para la pantalla principal: por división,
    registro (G-E-P), goles, forma reciente y última fecha con datos."""
    inv = listar()
    if not inv["disponible"]:
        return {**inv, "divisiones": [], "ultimos": []}

    base = inv["carpeta"]
    partidos = []
    for p in inv["partidos"]:
        r = resumen_partido(p["id"], base)
        partidos.append({**p, **(r or {"gf": None, "gc": None, "resultado": None})})

    divisiones = {}
    for p in partidos:
        d = p["division"] or "otros"
        acc = divisiones.setdefault(d, {
            "division": d, "partidos": 0, "g": 0, "e": 0, "p": 0,
            "gf": 0, "gc": 0, "ultima_fecha": None, "forma": [], "ids": [],
            "fechas": [],
        })
        acc["partidos"] += 1
        acc["ids"].append(p["id"])
        if p["resultado"]:
            acc["g" if p["resultado"] == "G" else "e" if p["resultado"] == "E" else "p"] += 1
            acc["gf"] += p["gf"] or 0
            acc["gc"] += p["gc"] or 0
        if p["fecha"] is not None:
            acc["ultima_fecha"] = max(acc["ultima_fecha"] or 0, p["fecha"])
            acc["fechas"].append(p["fecha"])

    # ¿En qué fecha va el torneo? La más alta cargada en cualquier categoría.
    fecha_torneo = max((f for a in divisiones.values() for f in a["fechas"]), default=0)

    for d, acc in divisiones.items():
        delDiv = sorted([q for q in partidos if (q["division"] or "otros") == d],
                        key=lambda q: q["fecha"] if q["fecha"] is not None else -1)
        # Forma: los últimos 5 por número de fecha
        acc["forma"] = [q["resultado"] for q in delDiv[-5:] if q["resultado"]]
        # Último partido JUGADO (fecha más alta), que no es lo mismo que el
        # último archivo cargado.
        ult = delDiv[-1] if delDiv else None
        acc["ultimo_partido"] = ult
        # Qué falta. Se distinguen dos casos, porque no significan lo mismo:
        #   huecos     → fechas salteadas antes de la última cargada = se
        #                olvidaron de subir ese partido
        #   pendientes → fechas posteriores a la última cargada = todavía no
        #                las subieron (probablemente recién jugadas)
        tiene = set(acc["fechas"])
        acc["fechas"] = sorted(tiene)
        ultima = acc["ultima_fecha"] or 0
        acc["huecos"] = [f for f in range(1, ultima) if f not in tiene]
        acc["pendientes"] = [f for f in range(ultima + 1, fecha_torneo + 1)]
        acc["faltan"] = len(acc["huecos"]) + len(acc["pendientes"])

    orden = {d: i for i, d in enumerate(_DIVISIONES)}
    divs = sorted(divisiones.values(), key=lambda a: orden.get(a["division"], 99))

    # Lo que entró último a la carpeta. OneDrive conserva la fecha de
    # modificación original de cada archivo, así que el mtime refleja de verdad
    # cuándo el videoanalista subió ese partido.
    # Se devuelven bastantes porque el frontend filtra por grupo de videoanálisis
    # (4ta-5ta-6ta / 7ma-8va-9na): si mandáramos sólo los últimos 8 globales,
    # un grupo podría quedarse sin ninguno.
    ultimos = sorted(partidos, key=lambda q: q["modificado"], reverse=True)[:40]

    return {"disponible": True, "carpeta": base, "total": len(partidos),
            "fecha_torneo": fecha_torneo, "divisiones": divs, "ultimos": ultimos}
