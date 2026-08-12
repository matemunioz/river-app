"""
fixture.py — Calendario oficial del Torneo Liga Profesional AFA 2026 (juveniles).

Fuente: las placas de "Fixture Juveniles" del área. El mismo rival por fecha
para las seis divisiones (cambia la sede, no el rival), así que alcanza con una
sola tabla.

Sirve para dos cosas que antes se hacían a ojo:
  · saber en qué fecha va el torneo según el día de hoy
  · saber exactamente qué partido falta cargar, por nombre de rival

OJO con la numeración: la fecha 1 (vs Racing) se suspendió y se reprograma al
final del torneo. Los videoanalistas numeraron sus archivos corrido SIN esa
fecha, así que el archivo "F19" es la fecha 20 del fixture. Por eso el cruce se
hace por RIVAL y no por número: es a prueba de reprogramaciones.
"""

from datetime import date

# (fecha_oficial, rival, día que se juega)
FIXTURE: list[tuple[int, str, date]] = [
    (1,  "Racing",                  date(2026, 3, 7)),   # suspendida → al final
    (2,  "Rosario Central",         date(2026, 3, 14)),
    (3,  "Godoy Cruz",              date(2026, 3, 21)),
    (4,  "Platense",                date(2026, 3, 28)),
    (5,  "Sarmiento",               date(2026, 4, 2)),
    (6,  "Belgrano",                date(2026, 4, 11)),
    (7,  "Atletico Rafaela",        date(2026, 4, 18)),
    (8,  "Riestra",                 date(2026, 4, 25)),
    (9,  "Aldosivi",                date(2026, 5, 2)),
    (10, "Boca",                    date(2026, 5, 9)),
    (11, "Colon",                   date(2026, 5, 16)),
    (12, "Huracan",                 date(2026, 5, 23)),
    (13, "Estudiantes LP",          date(2026, 5, 30)),
    (14, "Tigre",                   date(2026, 6, 6)),
    (15, "Atletico Tucuman",        date(2026, 6, 13)),
    (16, "Independiente Rivadavia", date(2026, 6, 20)),
    (17, "Ferro",                   date(2026, 6, 27)),
    (18, "Lanus",                   date(2026, 7, 4)),
    (19, "Independiente",           date(2026, 7, 11)),
    (20, "Newells",                 date(2026, 8, 1)),
    (21, "San Martin SJ",           date(2026, 8, 8)),
    (22, "Argentinos",              date(2026, 8, 15)),
    (23, "Instituto",               date(2026, 8, 22)),
    (24, "Talleres",                date(2026, 8, 29)),
    (25, "Estudiantes BA",          date(2026, 9, 5)),
    (26, "Barracas Central",        date(2026, 9, 12)),
    (27, "Quilmes",                 date(2026, 9, 19)),
    (28, "Defensa y Justicia",      date(2026, 9, 26)),
    (29, "Union",                   date(2026, 10, 3)),
    (30, "San Lorenzo",             date(2026, 10, 10)),
    (31, "Gimnasia LP",             date(2026, 10, 24)),
    (32, "Central Cordoba",         date(2026, 10, 31)),
    (33, "Gimnasia y Esgrima Mza",  date(2026, 11, 7)),
    (34, "Velez",                   date(2026, 11, 14)),
    (35, "Banfield",                date(2026, 11, 28)),
]

# La fecha 1 se suspendió: no se juega el 7/3 y se reprograma sin día definido.
FECHAS_SUSPENDIDAS = {1}


def _norm(s: str) -> str:
    """Para comparar rivales escritos de cualquier manera ('Atl. Tucuman')."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(ch for ch in s.lower() if ch.isalnum())


# Alias → forma canónica del fixture, para que el nombre del archivo matchee
_ALIAS = {
    "central": "rosariocentral",
    "rosariocentral": "rosariocentral",
    "atltucuman": "atleticotucuman",
    "atleticotucuman": "atleticotucuman",
    "tucuman": "atleticotucuman",
    "rafaela": "atleticorafaela",
    "atleticorafaela": "atleticorafaela",
    "deportivoriestra": "riestra",
    "riestra": "riestra",
    "irm": "independienterivadavia",
    "indrivadavia": "independienterivadavia",
    "independienteriv": "independienterivadavia",
    "independienterivadavia": "independienterivadavia",
    "edlp": "estudianteslp",
    "estudiantes": "estudianteslp",
    "estudianteslp": "estudianteslp",
    "sanmartin": "sanmartinsj",
    "sanmartinsj": "sanmartinsj",
    "gimnasia": "gimnasialp",
    "gimnasialp": "gimnasialp",
    "gye": "gimnasiayesgrimamza",
    "barracas": "barracascentral",
    "centralcordoba": "centralcordoba",
    "defensa": "defensayjusticia",
    "defensayjusticia": "defensayjusticia",
}


def clave_rival(nombre: str) -> str:
    n = _norm(nombre)
    return _ALIAS.get(n, n)


# rival normalizado → fecha oficial
_POR_RIVAL = {clave_rival(r): f for f, r, _ in FIXTURE}


def fecha_de_rival(rival: str) -> int | None:
    """Número de fecha del fixture para ese rival, o None si no lo reconoce."""
    return _POR_RIVAL.get(clave_rival(rival))


def jugadas_hasta(hoy: date | None = None) -> list[tuple[int, str, date]]:
    """Fechas que ya se jugaron (excluye las suspendidas)."""
    hoy = hoy or date.today()
    return [(f, r, d) for f, r, d in FIXTURE
            if d <= hoy and f not in FECHAS_SUSPENDIDAS]


def proxima(hoy: date | None = None) -> tuple[int, str, date] | None:
    """La próxima fecha a jugarse."""
    hoy = hoy or date.today()
    futuras = [(f, r, d) for f, r, d in FIXTURE
               if d > hoy and f not in FECHAS_SUSPENDIDAS]
    return futuras[0] if futuras else None


def faltantes(rivales_cargados: list[str], hoy: date | None = None) -> list[dict]:
    """Partidos ya jugados que todavía no están cargados, por rival.

    Se compara por rival —no por número— porque los archivos vienen numerados
    sin la fecha suspendida y cualquier reprogramación volvería a correrlos.
    """
    tengo = {clave_rival(r) for r in rivales_cargados if r}
    out = []
    for f, rival, dia in jugadas_hasta(hoy):
        if clave_rival(rival) not in tengo:
            out.append({"fecha": f, "rival": rival, "dia": dia.isoformat()})
    return out


def estado(hoy: date | None = None) -> dict:
    """Dónde está parado el torneo hoy."""
    hoy = hoy or date.today()
    jug = jugadas_hasta(hoy)
    prox = proxima(hoy)
    ultima = jug[-1] if jug else None
    return {
        "hoy": hoy.isoformat(),
        "ultima_jugada": ({"fecha": ultima[0], "rival": ultima[1], "dia": ultima[2].isoformat()}
                          if ultima else None),
        "proxima": ({"fecha": prox[0], "rival": prox[1], "dia": prox[2].isoformat()}
                    if prox else None),
        "jugadas": len(jug),
        "total": len([f for f, _, _ in FIXTURE if f not in FECHAS_SUSPENDIDAS]),
        "suspendidas": sorted(FECHAS_SUSPENDIDAS),
    }
