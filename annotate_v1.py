"""Inferencia v2 sobre dataset_v1.csv -> preannot/{rock}/{base}.json (reanuda)."""
import argparse
import csv
import json
import os
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--confidence", type=int, default=15)
    ap.add_argument("--delay", type=float, default=0.4)
    args = ap.parse_args()

    from roboflow import Roboflow
    import config

    rows = list(csv.DictReader(open("dataset_v1.csv", encoding="utf-8")))
    todo = []
    for r in rows:
        base = os.path.splitext(os.path.basename(r["file"]))[0]
        out = os.path.join("preannot", r["rock"], base + ".json")
        if not os.path.exists(out):
            todo.append((r, out))
    print(f"v1: {len(rows)} | pendientes: {len(todo)}", flush=True)
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
            if ok % 100 == 0:
                print(f"  {ok}/{len(todo)}...", flush=True)
        except Exception as e:
            print(f"  ! fallo {r['file']}: {e}", flush=True)
        time.sleep(args.delay)
    fres.close()
    print(f"Listo: {ok}")


if __name__ == "__main__":
    main()
