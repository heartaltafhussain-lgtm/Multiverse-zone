#!/usr/bin/env python3
"""gtf_history.json backfill — gtf_live_data.json ke 60-bar candles se
pichhle N sessions ke 'best buy' flags (DEMAND, score>=7) dobara compute karta hai.
Wahi GTF engine (gtf_pdf_engine.py) use hota hai jo scanner me hai.

Usage:  python3 build_history.py [src_json] [out_json] [days_back]
Default: gtf_live_data.json gtf_history.json 11
"""
import json
import sys

import numpy as np

from gtf_pdf_engine import detect_zones_pdf, trend_clock


def best_buy_at(o, h, l, c, min_score=7):
    """Us din ka best buy flag: DEMAND zone score>=min_score, ltp zone ke ±5% me,
    1D clock DOWN nahi (scanner wali hi logic)."""
    if len(c) < 30:
        return None
    dz, _sz = detect_zones_pdf(o, h, l, c, vol=None)
    clk, _ = trend_clock(c, c[-1])
    ltp = float(c[-1])
    for z in sorted(dz, key=lambda x: -x["score"]):
        lo, hi = min(z["prox"], z["dist"]), max(z["prox"], z["dist"])
        if lo * 0.95 <= ltp <= hi * 1.05 and z["ets"] != "SKIP" and z["score"] >= min_score:
            if clk == "DOWN":
                continue
            return {"score": z["score"], "pattern": z.get("pdf_pattern", ""),
                    "grade": z.get("grade", "")}
    return None


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "gtf_live_data.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "gtf_history.json"
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 11

    with open(src, encoding="utf-8") as fh:
        data = json.load(fh)

    flags_by_date = {}
    checked = 0
    for s in data["stocks"]:
        cd = s.get("candles")
        if not cd or "dates" not in cd or len(cd.get("c", [])) < 32:
            continue
        o = np.array(cd["o"], float)
        h = np.array(cd["h"], float)
        l = np.array(cd["l"], float)
        c = np.array(cd["c"], float)
        dates = cd["dates"]
        start = max(30, len(c) - days)
        for d in range(start, len(c)):
            checked += 1
            f = best_buy_at(o[:d + 1], h[:d + 1], l[:d + 1], c[:d + 1])
            if f:
                flags_by_date.setdefault(dates[d], []).append(
                    {"sym": s["sym"], "ltp": round(float(c[d]), 2), **f})

    hist = {"demo": bool(data.get("demo")),
            "note": "Backfilled from 60-bar candles (same GTF engine) — aage scanner roz append karega",
            "flags": {d: flags_by_date[d] for d in sorted(flags_by_date)}}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(hist, fh, ensure_ascii=False)
    print(f"[history] {out} — dates: {sorted(flags_by_date)} | "
          f"checks={checked} flags={sum(len(v) for v in flags_by_date.values())}")


if __name__ == "__main__":
    main()
