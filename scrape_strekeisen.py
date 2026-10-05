"""Scraper Strekeisen thin sections: 4 familias -> raw_strekeisen/ + manifest.csv
Uso:
  python scrape_strekeisen.py --families pluto vulc meta sedi --limit-pages 0 --delay 0.8
  --limit-pages 0 = todo. Para prueba usa --limit-pages 3
"""
import argparse
import csv
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.alexstrekeisen.it"
INDEX = {
    "pluto": f"{BASE}/english/pluto/index.php",
    "vulc": f"{BASE}/english/vulc/index.php",
    "meta": f"{BASE}/english/meta/index.php",
    "sedi": f"{BASE}/english/sedi/index.php",
}
HEADERS = {"User-Agent": "petroterratech-research/1.0 (educational, with-permission)"}

RE_PPL_XPL = re.compile(r"\b(PPL|XPL)\b", re.I)
RE_MAG = re.compile(r"(\d+(?:\.\d+)?x)", re.I)


def get(url, timeout=30):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.encoding = "iso-8859-1"
    r.raise_for_status()
    return r.text


def rock_links(family, index_url):
    html = get(index_url)
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.endswith(".php") and not href.startswith(("http", "javascript", "#")):
            full = urljoin(index_url, href)
            # solo mismas carpetas english/pluto|vulc|meta|sedi
            if f"/english/{family}/" in full:
                links.append(full)
    # dedup preservando orden
    seen, out = set(), []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def parse_rock_page(family, page_url):
    """Devuelve lista de dicts con full_url, caption, ppl_xpl."""
    html = get(page_url)
    soup = BeautifulSoup(html, "lxml")
    items = []
    for td in soup.select("table.foto td.foto"):
        # full image esta en onclick window.open('/immagini/...')
        full = None
        a = td.find("a", onclick=True)
        if a and "window.open(" in a["onclick"]:
            m = re.search(r"window\.open\('([^']+)'", a["onclick"])
            if m:
                full = urljoin(BASE, m.group(1))
        if not full:
            # fallback: img src grande sin /piccole/
            img = td.find("img", src=True)
            if img:
                src = img["src"]
                full = urljoin(BASE, src.replace("/piccole/", "/"))
            else:
                continue
        caption = td.get_text(" ", strip=True)
        m2 = RE_PPL_XPL.search(caption or "")
        ppl_xpl = m2.group(1).upper() if m2 else "UNKNOWN"
        m3 = RE_MAG.search(caption or "")
        mag = m3.group(1) if m3 else ""
        items.append({"full_url": full, "caption": caption, "ppl_xpl": ppl_xpl, "mag": mag})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="+", default=["pluto", "vulc", "meta", "sedi"])
    ap.add_argument("--limit-pages", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.8)
    ap.add_argument("--out", default="raw_strekeisen")
    ap.add_argument("--manifest", default="raw_strekeisen/manifest.csv")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    # cargar manifest existente para reanudar
    done_urls = set()
    if os.path.exists(args.manifest):
        with open(args.manifest, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done_urls.add(row["full_url"])

    write_header = not os.path.exists(args.manifest)
    fman = open(args.manifest, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fman, fieldnames=[
        "family", "rock_page", "rock", "file", "full_url",
        "ppl_xpl", "mag", "caption"])
    if write_header:
        w.writeheader()

    total_new = 0
    for fam in args.families:
        links = rock_links(fam, INDEX[fam])
        print(f"[{fam}] paginas encontradas: {len(links)}")
        if args.limit_pages:
            links = links[:args.limit_pages]
        for page_url in links:
            rock = page_url.rsplit("/", 1)[-1].replace(".php", "")
            try:
                items = parse_rock_page(fam, page_url)
            except Exception as e:
                print(f"  ! fallo pagina {rock}: {e}")
                time.sleep(args.delay)
                continue
            print(f"  {rock}: {len(items)} fotos")
            for it in items:
                if it["full_url"] in done_urls:
                    continue
                ext = os.path.splitext(it["full_url"])[1].split("?")[0] or ".jpg"
                safe_cap = re.sub(r"[^\w\-]+", "_", it["caption"][:40])
                fname = f"{rock}_{it['ppl_xpl']}_{abs(hash(it['full_url'])) % 10**8}{ext}"
                dest_dir = os.path.join(args.out, fam, rock)
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, fname)
                try:
                    r = requests.get(it["full_url"], headers=HEADERS, timeout=30)
                    r.raise_for_status()
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    w.writerow({"family": fam, "rock_page": page_url, "rock": rock,
                                "file": dest, "full_url": it["full_url"],
                                "ppl_xpl": it["ppl_xpl"], "mag": it["mag"],
                                "caption": it["caption"]})
                    fman.flush()
                    done_urls.add(it["full_url"])
                    total_new += 1
                except Exception as e:
                    print(f"    ! descarga fallo {it['full_url']}: {e}")
                time.sleep(0.2)
            time.sleep(args.delay)
    fman.close()
    print(f"Listo. Nuevas: {total_new}. Manifest: {args.manifest}")


if __name__ == "__main__":
    main()
