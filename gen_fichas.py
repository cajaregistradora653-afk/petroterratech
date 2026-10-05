"""Genera 24 fichas PPL vs XPL en guias_optica/ desde optical_guide.json + manifest."""
import csv
import json
import os
from collections import defaultdict

CONFUSABLES = {
    "Olivino": "Clinopiroxeno (II orden + clivaje 90 + extincion inclinada vs Olivino III orden sin clivaje); Ortopiroxeno (I orden, extincion recta).",
    "Clinopiroxeno": "Ortopiroxeno (extincion recta, I orden rosado); Hornblenda (pleocroismo verde-marron, clivaje 120/60).",
    "Ortopiroxeno": "Clinopiroxeno (inclinada, II orden); Olivino (III orden, sin clivaje, fracturas).",
    "Piroxeno": "Ver Clinopiroxeno/Ortopiroxeno segun extincion.",
    "Plagioclasa": "Cuarzo (sin maclas, grises I orden, extincion ondulante); Ortoclasa (macla Carlsbad simple, pertitas).",
    "Cuarzo": "Plagioclasa (maclas polisinteticas de albita); Ortoclasa (Carlsbad). Cuarzo: anhedral, gris I orden, extincion ondulante.",
    "Ortoclasa": "Cuarzo (sin maclas); Plagioclasa (polisinteticas). Ortoclasa: Carlsbad simple, pertitas, sericitizacion.",
    "Hornblenda": "Flogopita (micacea, clivaje perfecto, II-III orden); Clinopiroxeno (sin pleocroismo fuerte, clivaje 90).",
    "Anfibol": "Ver Hornblenda.",
    "Flogopita": "Hornblenda (prismatica, 120/60); Flogopita: laminas, pleocroismo pardo, extincion moteada.",
    "Aegirina": "Arfvedsonita (pleocroismo azul-verde, anfibol); Aegirina: verde pasto en PPL.",
    "Arfvedsonita": "Aegirina (piroxeno verde pasto); Hornblenda (verde-marron).",
    "nefelina": "Cuarzo (uniaxico); Sodalita (isotropa). Nefelina: incolora, relieve moderado-bajo, grises I orden.",
    "Sodalita": "Nefelina (anisotropa debil); Sodalita: isotropa (negra en XPL), incolora-azulada en PPL.",
    "Cancrinita": "Nefelina/calcita por asociacion; verificar maclas y relieve. Guiarse por caption y roca huesped.",
    "Calcita": "Dolomita/plagioclasa: calcita con maclas polisinteticas finas + colores pastel de alto orden + clivaje romboedrico.",
    "Mineral opaco": "Ilmenita vs magnetita indistinguibles al optico sin luz reflejada: usar asociacion de roca. Opaco: negro en PPL y XPL.",
    "Ilmenita": "Ver Mineral opaco. Indicio: alteration a leucoxeno en gabros/dioritas.",
    "Antipertita": "Pertita inversa: lamelas de ortoclasa en huesped plagioclasa (XPL: contraste lamela/huesped + maclas del huesped).",
    "Eudialita": "Nefelina/feldespatoides: eudialita con pleocroismo rosa-morado debil y zonacion en sienitas alcalinas.",
    "Rusenbuschita": "Mineral raro de complejos alcalinos; usar caption + roca huesped (lujavritas, kakortokitas).",
    "Turmalina": "Hornblenda/biotita: turmalina con pleocroismo fuerte, habito prismatico alargado, sin clivaje, extincion recta.",
    "Olivino alterado con serpentina": "Olivino fresco (III orden, sin malla) vs alterado: islas de olivino + venas de serpentina (textura mesh) + magnetita.",
    "Venas de serpentina": "Vetas de baja interferencia (gris I orden) en malla + magnetita opaca asociada.",
}

PPL_KEYS = ("color", "colour", "pleochro", "relief", "relieve", "cleavage",
            "clivaje", "form", "forma", "habit", "alter", "twin")
XPL_KEYS = ("interference", "interferencia", "extinction", "extincion",
            "birefring", "twinn", "macla", "2v", "optic sign", "signo")

# nombre EN en captions -> para buscar ejemplos en manifest
EN_EXAMPLES = {
    "Sodalita": ["sodalite"], "nefelina": ["nepheline"],
    "Cancrinita": ["cancrinite"], "Plagioclasa": ["plagioclase"],
    "Calcita": ["calcite"], "Ortopiroxeno": ["orthopyroxene", "enstatite", "hypersthene"],
    "Mineral opaco": ["opaque", "magnetite"], "Cuarzo": ["quartz"],
    "Flogopita": ["biotite", "phlogopite"], "Piroxeno": ["pyroxene"],
    "Ortoclasa": ["orthoclase", "sanidine", "alkali feldspar"],
    "Antipertita": ["antiperthite", "perthite"], "Hornblenda": ["hornblende"],
    "Aegirina": ["aegirine"], "Olivino alterado con serpentina": ["serpentine", "iddingsite", "mesh"],
    "Clinopiroxeno": ["clinopyroxene", "augite"], "Olivino": ["olivine"],
    "Anfibol": ["amphibole"], "Arfvedsonita": ["arfvedsonite"],
    "Eudialita": ["eudialyte", "eudialite"], "Rusenbuschita": ["rosenbuschite"],
    "Ilmenita": ["ilmenite", "leucoxene"], "Turmalina": ["tourmaline"],
    "Venas de serpentina": ["serpentine", "vein"],
}


def split_ppl_xpl(props):
    ppl, xpl, resto = [], [], []
    for b in props:
        bl = b.lower()
        is_p = any(k in bl for k in PPL_KEYS)
        is_x = any(k in bl for k in XPL_KEYS)
        if is_p and not is_x:
            ppl.append(b)
        elif is_x and not is_p:
            xpl.append(b)
        elif is_p and is_x:
            ppl.append(b)
            xpl.append(b)
        else:
            resto.append(b)
    return ppl, xpl, resto


def main():
    guide = json.load(open("optical_guide.json", encoding="utf-8"))
    ex = defaultdict(list)
    try:
        for r in csv.DictReader(open("raw_strekeisen/manifest.csv", encoding="utf-8")):
            ex[r["rock"]].append(r)
    except FileNotFoundError:
        pass
    os.makedirs("guias_optica", exist_ok=True)
    for mineral, info in guide.items():
        props = info.get("propiedades_opticas", [])
        ppl, xpl, resto = split_ppl_xpl(props)
        # ejemplos: captions EN que mencionan el mineral (mezcla PPL/XPL, hasta 6)
        terms = EN_EXAMPLES.get(mineral, [mineral.lower()])
        got_ppl, got_xpl = [], []
        for r in csv.DictReader(open("raw_strekeisen/manifest.csv", encoding="utf-8")) \
                if os.path.exists("raw_strekeisen/manifest.csv") else []:
            cap = r.get("caption", "").lower()
            if any(t in cap for t in terms):
                if r.get("ppl_xpl") == "PPL" and len(got_ppl) < 3:
                    got_ppl.append(r)
                elif r.get("ppl_xpl") == "XPL" and len(got_xpl) < 3:
                    got_xpl.append(r)
            if len(got_ppl) >= 3 and len(got_xpl) >= 3:
                break
        rock_hits = got_ppl + got_xpl
        lines = [f"# {mineral} -> `{mineral}_PPL` / `{mineral}_XPL`", "",
                 f"Fuente: {info.get('page', '')}", ""]
        if info.get("descripcion"):
            lines += ["## Descripcion fuente", info["descripcion"], ""]
        lines.append("## PPL (luz polarizada plana)")
        lines += [f"- {b}" for b in ppl] or ["- (la fuente no detalla criterios PPL; usar color/relieve/clivaje estandar)"]
        lines += ["", "## XPL (nicoles cruzados)"]
        lines += [f"- {b}" for b in xpl] or ["- (la fuente no detalla criterios XPL; usar interferencia/extincion/maclas estandar)"]
        if resto:
            lines += ["", "## Otros criterios fuente"] + [f"- {b}" for b in resto]
        if info.get("alteracion"):
            lines += ["", "## Alteracion", info["alteracion"][:700]]
        lines += ["", "## Confusables (revisar antes de anotar)",
                  CONFUSABLES.get(mineral, "Usar asociacion mineralogica de la roca huesped."), "",
                  "## Ejemplos en el dataset"]
        if rock_hits:
            lines += [f"- `{h['file']}` [{h['ppl_xpl']}] {h['caption'][:130]}" for h in rock_hits]
        else:
            lines.append("- (sin ejemplos con caption; buscar por roca huesped en annotation_queue.csv)")
        if not props:
            lines += ["", "> NOTA: la pagina fuente no trae seccion optica; criterios = estandar de mineralogia optica. Verificar con pares PPL/XPL del mismo campo."]
        with open(f"guias_optica/{mineral}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print(f"Fichas: {len(guide)} en guias_optica/")


if __name__ == "__main__":
    main()
