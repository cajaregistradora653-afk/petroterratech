"""Pre-anotacion SELECTIVA con identificacion-de-minerales/v2.
Solo rocas maficas/ultramaficas de pluto/vulc (dominio del modelo).
Todo poligono resultante es PROPUESTA a revisar + sufijo _PPL/_XPL manual.
Guarda preannot/{rock}/{base}.json y preannot_resumen.csv
Uso: python preannotate.py --limit 0 --confidence 15
"""
import argparse
import csv
import json
import os
import time

MAFICAS = {"gabbro", "eufodite", "gabbroaugite", "gabbronorite", "olivinegabbro",
           "gabbrohornblende", "mattonigabbro", "mattoni", "norite", "troctolite",
           "dun", "dunite", "basalt", "ankaramite", "wherlite", "harzburgite",
           "finero", "peridotites", "pyroxenite", "orthopyroxenite", "olivine",
           "clinopyroxene", "cumberlandite", "hornblendite", "hornblendite1",
           "ijolite", "ijolite1", "melteigite", "jacupirangite", "kentallenite",
           "diorite", "monzodiorite", "rhum", "orthocumulates", "adcumulates",
           "olivinegabbro", "quartzgabbro", "lherzoliteserpentinized",
           "garnetlherzolite", "spinelehorzolite", "carbonatites"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="raw_strekeisen/manifest.csv")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--confidence", type=int, default=15)
    ap.add_argument("--delay", type=float, default=0.5)
    args = ap.parse_args()

    from roboflow import Roboflow
    import config

    rows = [r for r in csv.DictReader(open(args.manifest, encoding="utf-8"))
            if r.get("family") in ("pluto", "vulc") and r.get("rock") in MAFICAS
            and r.get("ppl_xpl") in ("PPL", "XPL") and os.path.exists(r["file"])]
    todo = []
    for r in rows:
        base = os.path.splitext(os.path.basename(r["file"]))[0]
        out = os.path.join("preannot", r["rock"], base + ".json")
        if not os.path.exists(out):
            todo.append((r, out))
    print(f"Subset mafico: {len(rows)} | pendientes: {len(todo)}")
    if args.limit:
        todo = todo[:args.limit]

    rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
    model = rf.workspace(config.ROBOFLOW_WORKSPACE).project(
        "identificacion-de-minerales").version(2).model

    res_path = "preannot_resumen.csv"
    new_file = not os.path.exists(res_path)
    fres = open(res_path, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fres, fieldnames=["file", "rock", "ppl_xpl", "n_pred", "clases"])
    if new_file:
        w.writeheader()
    ok = 0
    for r, out in todo:
        try:
            pred = model.predict(r["file"], confidence=args.confidence).json()
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(pred, f)
            preds = pred.get("predictions", [])
            cls = sorted({p.get("class", "?") for p in preds})
            w.writerow({"file": r["file"], "rock": r["rock"], "ppl_xpl": r["ppl_xpl"],
                        "n_pred": len(preds), "clases": ";".join(cls)})
            fres.flush()
            ok += 1
            if ok % 25 == 0:
                print(f"  {ok}/{len(todo)}...")
        except Exception as e:
            print(f"  ! fallo {r['file']}: {e}")
        time.sleep(args.delay)
    fres.close()
    print(f"Pre-anotadas en esta corrida: {ok}")


if __name__ == "__main__":
    main()
