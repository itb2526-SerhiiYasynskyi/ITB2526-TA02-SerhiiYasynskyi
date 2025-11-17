import xml.etree.ElementTree as ET
from datetime import datetime
import re

# Archivo XML
XML_IN = "ta04-PieroYcaza-SerhiiYasynskyi-SfiliAyoub-MoralesMiquel-grup6.xml"

# Rango de fechas
START_DATE = datetime.strptime("01/11/2025", "%d/%m/%Y")
END_DATE = datetime.strptime("17/11/2025", "%d/%m/%Y")

# Colores por COLUMNA
COL_DATA = "\033[92m"      # Verde
COL_HORA = "\033[96m"      # Cian
COL_PRIOICON = "\033[95m"  # Magenta
COL_PRIORITAT = "\033[93m" # Amarillo
COL_NOM = "\033[94m"       # Azul
COL_AREA = "\033[37m"      # Gris claro
COL_TIPUS = "\033[97m"     # Blanco
COL_MOMENT = "\033[91m"    # Rojo suave
COL_EQUIP = "\033[92m"     # Verde claro

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"

# Columnas (field, title, width, color)
COLUMNS = [
    ("data", "Data", 10, COL_DATA),
    ("hora", "Hora", 8, COL_HORA),
    ("prioritat_icon", "Prio", 4, COL_PRIOICON),   # A / M / B
    ("prioritat", "Prioritat", 40, COL_PRIORITAT),
    ("nom", "Nom", 20, COL_NOM),
    ("area", "Àrea/Despatx", 18, COL_AREA),
    ("tipus", "Tipus", 20, COL_TIPUS),
    ("moment", "Moment problema", 25, COL_MOMENT),
    ("equip", "Equip", 15, COL_EQUIP),
]


def priority_icon(priority: str) -> str:
    """Devuelve un código corto de prioridad para la columna Prio."""
    p = priority.lower()
    if p.startswith("alta"):
        return "A"   # Alta
    if p.startswith("mitjana"):
        return "M"   # Mitjana
    if p.startswith("baixa"):
        return "B"   # Baixa
    return "?"


def priority_num(priority: str) -> int:
    p = priority.lower()
    if p.startswith("alta"):
        return 1
    if p.startswith("mitjana"):
        return 2
    if p.startswith("baixa"):
        return 3
    return 99


def parse_date(text: str):
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
    ]
    for f in formats:
        try:
            return datetime.strptime(text.strip(), f)
        except Exception:
            pass
    return None


def detectar_campos(root):
    """Detecta etiquetas de fecha y prioridad automáticamente."""
    first = root.find("row")
    if first is None:
        return None, None
    date_tag, prio_tag = None, None
    for child in first:
        txt = (child.text or "").strip()
        if re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", txt):
            date_tag = child.tag
        if ("Alta" in txt) or ("Mitjana" in txt) or ("Baixa" in txt):
            prio_tag = child.tag
    return date_tag, prio_tag


# Ajusta estos nombres si ves alguna columna vacía
TAG_HORA = "hora_de_la_incidencia"
TAG_NOM = "nom_de_persona_que_reporta_la_incidencia"
TAG_AREA = "areadespatx"
TAG_TIPUS = "tipus_dincidencia"
TAG_MOMENT = "en_quin_moment_passa_el_problema"
TAG_DESC = "descripcio_detallada_del_problema"
TAG_EQUIP = "equip_afectat_codi_equip_xxxxx-000"
TAG_ACC = "accions_realitzades_abans_de_reportar_reinici_canvi_de_cable_reinstal_lacio_etc"


def fit(text, width):
    """Ajusta texto a un ancho fijo con … si es demasiado largo."""
    if text is None:
        text = ""
    text = str(text)
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def main():
    # Cargar XML
    try:
        tree = ET.parse(XML_IN)
        root = tree.getroot()
    except Exception as e:
        print("❌ Error carregant el XML:", e)
        return

    date_tag, prio_tag = detectar_campos(root)
    print(f"Detectat camp DATA: {date_tag}")
    print(f"Detectat camp PRIORITAT: {prio_tag}")
    print("-" * 140)

    incidencies = []

    for row in root.findall("row"):
        date_txt = (row.findtext(date_tag) or "").strip()
        prio_txt = (row.findtext(prio_tag) or "").strip()

        date_obj = parse_date(date_txt)
        if date_obj is None:
            continue

        if not (START_DATE <= date_obj <= END_DATE):
            continue

        incidencies.append({
            "data_obj": date_obj,
            "data": date_obj.strftime("%d/%m/%Y"),
            "hora": (row.findtext(TAG_HORA) or "").strip(),
            "prioritat": prio_txt,
            "prioritat_icon": priority_icon(prio_txt),
            "nom": (row.findtext(TAG_NOM) or "").strip(),
            "area": (row.findtext(TAG_AREA) or "").strip(),
            "tipus": (row.findtext(TAG_TIPUS) or "").strip(),
            "moment": (row.findtext(TAG_MOMENT) or "").strip(),
            "equip": (row.findtext(TAG_EQUIP) or "").strip(),
            "descripcio": (row.findtext(TAG_DESC) or "").strip(),
            "accions": (row.findtext(TAG_ACC) or "").strip(),
        })

    # Ordenar: fecha → prioridad → hora
    def sort_key(it):
        try:
            h = datetime.strptime(it["hora"], "%H:%M").time()
        except Exception:
            h = datetime.min.time()
        return (it["data_obj"], priority_num(it["prioritat"]), h)

    incidencies.sort(key=sort_key)

    if not incidencies:
        print("No hi ha incidències en aquest rang.")
        return

    # Calcular ancho total para la tabla
    widths = [c[2] for c in COLUMNS]
    total_width = sum(widths) + 3 * (len(COLUMNS) - 1)
    top = "═" * total_width
    sep = "─" * total_width

    # CABECERA
    print(BOLD + CYAN + top + RESET)

    header_cells = []
    for field, title, width, col_color in COLUMNS:
        header_cells.append(col_color + BOLD + fit(title, width).ljust(width) + RESET)
    print(" | ".join(header_cells))
    print(CYAN + sep + RESET)

    # FILAS
    for it in incidencies:
        row_cells = []
        for field, title, width, col_color in COLUMNS:
            value = fit(it[field], width).ljust(width)
            row_cells.append(col_color + value + RESET)

        print(" | ".join(row_cells))

        if it["descripcio"]:
            print(f"    Descripció: {it['descripcio']}")
        if it["accions"]:
            print(f"    Accions   : {it['accions']}")
        print(sep)

    print(BOLD + CYAN + top + RESET)


if __name__ == "__main__":
    main()
