"""Extrae propiedades opticas de paginas de minerales Strekeisen -> optical_guide.json
Uso: python scrape_optics.py (respeta delay, reanuda por cache html/)
"""
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://www.alexstrekeisen.it"
HEADERS = {"User-Agent": "petroterratech-research/1.0 (educational, with-permission)"}
CACHE = "raw_strekeisen/html_cache"
os.makedirs(CACHE, exist_ok=True)

# clase ES -> (familia, pagina)
MINERAL_PAGES = {
    "Sodalita": ("pluto", "sodalite.php"),
    "nefelina": ("pluto", "nepheline.php"),
    "Cancrinita": ("pluto", "cancrinite.php"),
    "Plagioclasa": ("pluto", "plagioclase.php"),
    "Calcita": ("pluto", "calcite.php"),
    "Ortopiroxeno": ("vulc", "orthopyroxene.php"),
    "Mineral opaco": ("pluto", "magnetite.php"),
    "Cuarzo": ("pluto", "quartz.php"),
    "Flogopita": ("pluto", "biotite.php"),
    "Piroxeno": ("pluto", "clinopyroxene.php"),
    "Ortoclasa": ("pluto", "alkalifeldspar.php"),
    "Antipertita": ("pluto", "antiperthite.php"),
    "Hornblenda": ("pluto", "amphiboles.php"),
    "Aegirina": ("pluto", "clinopyroxene.php"),
    "Olivino alterado con serpentina": ("meta", "serpentine.php"),
    "Clinopiroxeno": ("pluto", "clinopyroxene.php"),
    "Olivino": ("pluto", "olivine.php"),
    "Anfibol": ("pluto", "amphiboles.php"),
    "Arfvedsonita": ("pluto", "amphiboles.php"),
    "Eudialita": ("pluto", "eudialyte.php"),
    "Rusenbuschita": ("pluto", "rosenbuschite.php"),
    "Ilmenita": ("pluto", "ilmenite.php"),
    "Turmalina": ("pluto", "tourmaline.php"),
    "Venas de serpentina": ("meta", "serpentine.php"),
}


def fetch(fam, page):
    cpath = os.path.join(CACHE, f"{fam}_{page.replace('.php', '')}.html")
    if os.path.exists(cpath):
        with open(cpath, encoding="utf-8", errors="replace") as f:
            return f.read()
    url = f"{BASE}/english/{fam}/{page}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.encoding = "iso-8859-1"
        r.raise_for_status()
        with open(cpath, "w", encoding="utf-8", errors="replace") as f:
            f.write(r.text)
        time.sleep(0.6)
        return r.text
    except Exception as e:
        print(f"  ! fallo {url}: {e}")
        return ""


def section_after(text, marker, maxlen=1800):
    i = text.find(marker)
    if i < 0:
        # probar sin mayusculas
        m = re.search(re.escape(marker), text, re.I)
        if not m:
            return ""
        i = m.start()
    chunk = text[i + len(marker):i + len(marker) + maxlen]
    # cortar en siguiente encabezado típico o inicio del menu lateral
    stop = re.search(
        r"\n(Bibliography|Photo|Alteration|Occurrence|Distinguishing|Structure|"
        r"Fundamental Minerals|Plutonic Rocks|Volcanic Rocks|Metamorphic Rocks|"
        r"Sedimentary Rocks|Microstructures|Accessory Minerals|Rare Accessory)\b",
        chunk)
    if stop:
        chunk = chunk[:stop.start()]
    return chunk.strip()


def main():
    guide = {}
    for mineral, (fam, page) in MINERAL_PAGES.items():
        url = f"{BASE}/english/{fam}/{page}"
        print(f"{mineral} <- {url}")
        html = fetch(fam, page)
        if not html:
            guide[mineral] = {"page": url, "error": "fetch-failed"}
            continue
        soup = BeautifulSoup(html, "lxml")
        content = soup.find("div", id="content")
        # solo el contenido central: el menu lateral contamina "Alteration Products", etc.
        text = content.get_text("\n", strip=True) if content else soup.get_text("\n", strip=True)
        optics_raw = ""
        for marker in ("Optical Properties", "Optical properties",
                       "In thin section", "Thin section",
                       "Distinguishing Features", "Distinguishing features"):
            optics_raw = section_after(text, marker)
            if len(optics_raw) > 60:
                break
        # partir solo por viñeta • para no romper "Etiqueta: valor"
        optics = [b.strip(" \t") for b in optics_raw.split("•")
                  if len(b.strip()) > 8][:14]
        alteration = section_after(text, "Alteration", 900)
        # primer parrafo descriptivo real (evita pies de figura Fig./Figure)
        desc = ""
        if content:
            for p in content.find_all(["p", "dfn"])[:8]:
                t = p.get_text(" ", strip=True)
                if len(t) > 120 and not re.match(r"(Fig\.|Figure|Plate)", t):
                    desc = t[:900]
                    break
        # captions que mencionan el mineral (ingles)
        caps = []
        for td in soup.select("table.foto td.foto")[:40]:
            c = td.get_text(" ", strip=True)
            if c and len(caps) < 6:
                caps.append(c[:220])
        guide[mineral] = {
            "page": url,
            "descripcion": desc,
            "propiedades_opticas": optics,
            "alteracion": alteration[:900],
            "captions_ejemplo": caps,
        }
    with open("optical_guide.json", "w", encoding="utf-8") as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)
    n = sum(1 for v in guide.values() if v.get("propiedades_opticas"))
    print(f"Listo: {len(guide)} minerales, {n} con propiedades opticas -> optical_guide.json")


if __name__ == "__main__":
    main()
