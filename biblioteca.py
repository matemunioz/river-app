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


def _candidatos_raiz() -> list:
    """Rutas donde puede estar la carpeta de datos, en orden de preferencia."""
    env = os.environ.get("RIVER_BIBLIOTECA_DIR")
    if env:
        return [env]
    home = os.path.expanduser("~")
    cands = []
    # OneDrive / SharePoint sincronizado por el cliente de escritorio
    cands += sorted(glob(os.path.join(home, "Library/CloudStorage/OneDrive-*/Datos_Estadisticos_*")))
    cands += sorted(glob(os.path.join(home, "Library/CloudStorage/OneDrive-*/*/Datos_Estadisticos_*")))
    cands += sorted(glob(os.path.join(home, "OneDrive*/Datos_Estadisticos_*")))
    # Copia local
    cands += sorted(glob(os.path.join(home, "RiverData/Datos_Estadisticos_*")))
    return cands


def raiz() -> str | None:
    """Carpeta activa de la biblioteca, o None si no hay ninguna disponible."""
    for c in _candidatos_raiz():
        if c and os.path.isdir(c):
            return c
    return None


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
        return {"disponible": False, "carpeta": None, "partidos": []}

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


def _ruta_de_id(pid: str, base: str | None = None) -> str | None:
    base = base or raiz()
    if not base:
        return None
    for p in listar(base)["partidos"]:
        if p["id"] == pid:
            full = os.path.realpath(os.path.join(base, p["archivo"]))
            # Defensa: nunca salir de la carpeta configurada
            if full.startswith(os.path.realpath(base) + os.sep):
                return full
    return None


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
