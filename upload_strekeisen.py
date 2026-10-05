"""Sube raw_strekeisen/manifest.csv a Roboflow petroterratech (instance-seg, sin anotar).
Tags: PPL/XPL + familia. Batch: roca. Split 70/20/10 deterministico por hash.
Uso:
  python upload_strekeisen.py --limit 20
  python upload_strekeisen.py --limit 0   (todo)
"""
import argparse
import csv
import hashlib
import os
import time

from roboflow import Roboflow
import config

PROJECT = "petroterratech"
UPLOG = "raw_strekeisen/uploaded.log"


def split_for(key: str) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16) % 100
    if h < 70:
        return "train"
    if h < 90:
        return "valid"
    return "test"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="raw_strekeisen/manifest.csv")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--delay", type=float, default=0.4)
    args = ap.parse_args()

    done = set()
    if os.path.exists(UPLOG):
        with open(UPLOG, encoding="utf-8") as f:
            done = {line.strip() for line in f if line.strip()}

    rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
    project = rf.workspace(config.ROBOFLOW_WORKSPACE).project(PROJECT)
    print(f"Proyecto destino: {PROJECT} ({project.type})")

    rows = list(csv.DictReader(open(args.manifest, encoding="utf-8")))
    pending = [r for r in rows if r["full_url"] not in done and os.path.exists(r["file"])]
    print(f"Manifest: {len(rows)} | ya subidas: {len(done)} | pendientes con archivo: {len(pending)}")
    if args.limit:
        pending = pending[:args.limit]

    ok = 0
    with open(UPLOG, "a", encoding="utf-8") as flog:
        for r in pending:
            try:
                project.upload(
                    image_path=r["file"],
                    batch_name=f"{r['family']}-{r['rock']}"[:63],
                    split=split_for(r["full_url"]),
                    tag_names=[r["ppl_xpl"], r["family"]],
                    metadata={"rock": r["rock"], "mag": r["mag"],
                              "source_url": r["full_url"]},
                    num_retry_uploads=2,
                )
                flog.write(r["full_url"] + "\n")
                flog.flush()
                ok += 1
                print(f"  [{ok}/{len(pending)}] OK {r['rock']} {r['ppl_xpl']} {os.path.basename(r['file'])}")
            except Exception as e:
                print(f"  ! fallo {r['file']}: {e}")
            time.sleep(args.delay)
    print(f"Subidas en esta corrida: {ok}")


if __name__ == "__main__":
    main()
