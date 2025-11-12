
import csv
import re
import unicodedata
import xml.etree.ElementTree as ET

CSV_IN = "ta04-PieroYcaza-SerhiiYasynskyi-SfiliAyoub-MoralesMiquel-grup6.csv"
XML_OUT = "ta04-PieroYcaza-SerhiiYasynskyi-SfiliAyoub-MoralesMiquel-grup6.xml"

def sanitize_tag(s: str, idx: int = None) -> str:
    """Convierte el nombre de columna en una etiqueta XML válida."""
    if not s or s.strip() == "":
        s = f"col_{idx if idx is not None else 'x'}"
    s = s.strip()

    # quita acentos
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

    # minúsculas, espacios->_, quita signos raros (incluye ':')
    s = s.lower().replace(" ", "_")
    s = re.sub(r"[^a-z0-9._-]", "", s)

    # la 1ª letra no puede ser dígito ni punto/guion
    if not s or not re.match(r"[a-z_]", s[0]):
        s = f"col_{s}"

    return s

with open(CSV_IN, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

if not rows:
    raise ValueError("El CSV está vacío.")

raw_headers = rows[0]
headers = []
seen = {}

# normaliza y evita duplicados
for i, h in enumerate(raw_headers):
    tag = sanitize_tag(h, i)
    if tag in seen:
        seen[tag] += 1
        tag = f"{tag}_{seen[tag]}"
    else:
        seen[tag] = 1
    headers.append(tag)

root = ET.Element("rows")
for r in rows[1:]:
    item = ET.SubElement(root, "row")
    for k, v in zip(headers, r):
        child = ET.SubElement(item, k)
        child.text = v if v is not None else ""

tree = ET.ElementTree(root)
tree.write(XML_OUT, encoding="utf-8", xml_declaration=True)
print(f"✅ XML creado: {XML_OUT}")
