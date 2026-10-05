"""Sube annot_v1/*.txt a petroterratech. Deduplica por contenido (no duplica imagen).
NOTA: crea clases numericas '0'..'23' -> renombrar en UI segun classes24.txt (1 vez).
Reanuda por uploaded_ann.log. Solo filas ok con n_kept>0.
Uso: python upload_v1.py --limit 0
"""
import argparse
import csv
import os
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.3)
    args = ap.parse_args()

    from roboflow import Roboflow
    import config

    done = set()
    if os.path.exists("uploaded_ann.log"):
        with open("uploaded_ann.log", encoding="utf-8") as f:
            done = {l.strip() for l in f if l.strip()}

    rows = [r for r in csv.DictReader(open("filter_report.csv", encoding="utf-8"))
            if r["motivo"] == "ok" and int(r["n_kept"]) > 0 and r["file"] not in done]
    print(f"Anotadas a subir: {len(rows)}")
    if args.limit:
        rows = rows[:args.limit]

    rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
    project = rf.workspace(config.ROBOFLOW_WORKSPACE).project("petroterratech")
    ok = 0
    with open("uploaded_ann.log", "a", encoding="utf-8") as flog:
        for r in rows:
            base = os.path.splitext(os.path.basename(r["file"]))[0]
            txt = os.path.join("annot_v1", r["rock"], base + ".txt")
            if not os.path.exists(txt):
                continue
            try:
                project.upload(image_path=r["file"], annotation_path=txt,
                               batch_name="v1", num_retry_uploads=2)
                flog.write(r["file"] + "\n")
                flog.flush()
                ok += 1
                if ok % 50 == 0:
                    print(f"  {ok}/{len(rows)}...", flush=True)
            except Exception as e:
                print(f"  ! fallo {r['file']}: {e}", flush=True)
            time.sleep(args.delay)
    print(f"Subidas: {ok}")


if __name__ == "__main__":
    main()
