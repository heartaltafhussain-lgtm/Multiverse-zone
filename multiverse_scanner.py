#!/usr/bin/env python3
"""
MULTIVERSE ZONE scanner — GTF "Trading in the Zone" PDF engine (v6).
NIFTY-500 universe ke har stock par 1D / 1W / 1M timeframes me PDF-faithful
demand-supply zones detect karta hai (gtf_pdf_engine.py) aur dashboard ke liye
`gtf_live_data.json` likhta hai (charts ke liye last-60 daily candles samet).

Usage:
  python3 multiverse_scanner.py                 # full universe (GitHub Actions)
  python3 multiverse_scanner.py --top 50        # pehle 50 symbols
  python3 multiverse_scanner.py --demo          # synthetic demo data (offline)
"""
import json
import sys
import datetime

import numpy as np
import pandas as pd

from gtf_pdf_engine import (detect_zones_pdf, trend_clock, curve_position,
                            confirmation_status)

CHART_BARS = 60
UNIVERSE_CSV = "nifty500_universe.csv"
OUT_JSON = "gtf_live_data.json"
VERSION = "Multiverse Zone v1.0 — GTF PDF engine (p3-37)"


# ---------------------------------------------------------------- data fetch
def load_universe(top=None):
    df = pd.read_csv(UNIVERSE_CSV)
    df = df[df.get("series", "EQ").astype(str) == "EQ"] if "series" in df.columns else df
    rows = list(df[["symbol", "company"]].itertuples(index=False, name=None))
    return rows[:top] if top else rows


def fetch_ohlc(yf_sym):
    import yfinance as yf
    tk = yf.Ticker(yf_sym)
    h = tk.history(period="2y", interval="1d", auto_adjust=False)
    if h is None or len(h) < 60:
        return None
    h = h[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return h


def resample(df, rule):
    return df.resample(rule).agg({
        "Open": "first", "High": "max", "Low": "min",
        "Close": "last", "Volume": "sum"}).dropna()


def zone_public(z, o, h, l, c):
    """JSON-safe zone with live confirmation status (p34-35)."""
    out = {k: z.get(k) for k in (
        "side", "pdf_pattern", "pdf_kind", "prox", "dist", "prox_ww", "marking",
        "exceptional", "born_date", "tests", "n_base", "n_legout", "legout",
        "has_gap", "p22_weak", "strength_label", "closing_ok", "auth",
        "dep", "fresh", "base", "score", "grade", "et", "ets", "setup", "vol_ratio")}
    out["legin_idx"] = z.get("legin_idx")
    out["base_idx"] = z.get("base_idx")
    out["legout_idx"] = z.get("legout_idx")
    out["confirm"] = confirmation_status(o, h, l, c, z)
    return out


def scan_symbol(sym, company, df1d):
    o = df1d["Open"].to_numpy(float)
    h = df1d["High"].to_numpy(float)
    l = df1d["Low"].to_numpy(float)
    c = df1d["Close"].to_numpy(float)
    ltp = float(c[-1])

    tfs = {}
    frames = {"1D": df1d, "1W": resample(df1d, "W"), "1M": resample(df1d, "ME")}
    for tf, fr in frames.items():
        if fr is None or len(fr) < 60:
            continue
        oz = fr["Open"].to_numpy(float)
        hz = fr["High"].to_numpy(float)
        lz = fr["Low"].to_numpy(float)
        cz = fr["Close"].to_numpy(float)
        dz, sz = detect_zones_pdf(oz, hz, lz, cz,
                                  vol=fr["Volume"].to_numpy(float) if "Volume" in fr else None)
        clock, _ = trend_clock(cz, cz[-1])
        tfs[tf] = {
            "clock": clock,
            "zones": [zone_public(z, oz, hz, lz, cz) for z in (dz + sz)
                      if z["born"] >= len(cz) - 120],
        }

    # curve location (p30-32) — 1D fresh demand prox vs fresh supply prox
    fd = fs = None
    for z in tfs.get("1D", {}).get("zones", []):
        if z["tests"] == 0:
            hi_e, lo_e = max(z["prox"], z["dist"]), min(z["prox"], z["dist"])
            if z["side"] == "DEMAND" and hi_e <= ltp * 1.002:
                fd = hi_e if fd is None else max(fd, hi_e)
            if z["side"] == "SUPPLY" and lo_e >= ltp * 0.998:
                fs = lo_e if fs is None else min(fs, lo_e)
    curve = curve_position(ltp, fd, fs)

    # signal (p28 + p32): curve band + trend clock
    sig = "WAIT"
    clk = tfs.get("1D", {}).get("clock")
    if curve:
        if curve["band"] in ("LOW", "VERY LOW"):
            sig = "BUY SIDE (LTF)"
        elif curve["band"] in ("HIGH", "VERY HIGH"):
            sig = "SELL SIDE (LTF)"
        else:
            sig = "BUY (trend UP)" if clk == "UP" else "SELL (trend DOWN)" if clk == "DOWN" else "EQUILIBRIUM — wait"
    elif clk == "UP":
        sig = "BUY (trend UP)"
    elif clk == "DOWN":
        sig = "SELL (trend DOWN)"
    best = None
    for z in sorted(tfs.get("1D", {}).get("zones", []), key=lambda x: -x["score"]):
        lo, hi = min(z["prox"], z["dist"]), max(z["prox"], z["dist"])
        if lo * 0.95 <= ltp <= hi * 1.05 and z["ets"] != "SKIP":
            # p28 caution: demand buy sirf UP clock me, supply sell sirf DOWN clock me
            if z["side"] == "DEMAND" and clk == "DOWN":
                continue
            if z["side"] == "SUPPLY" and clk == "UP":
                continue
            best = z
            break

    n = len(df1d)
    return {
        "sym": sym, "comp": company, "ltp": round(ltp, 2),
        "tfs": tfs, "curve": curve, "signal": sig,
        "best": best,
        "candles": {
            "o": [round(float(x), 2) for x in o[-CHART_BARS:]],
            "h": [round(float(x), 2) for x in h[-CHART_BARS:]],
            "l": [round(float(x), 2) for x in l[-CHART_BARS:]],
            "c": [round(float(x), 2) for x in c[-CHART_BARS:]],
            "dates": [str(d.date()) for d in df1d.index[-CHART_BARS:]],
            "offset": max(0, n - CHART_BARS),
        },
    }


# ---------------------------------------------------------------- demo data
def demo_symbol(name, seed):
    """PDF diagrams jaisi synthetic candles — dashboard demo ke liye."""
    rng = np.random.default_rng(seed)
    O, H, L, C = [], [], [], []
    px = 100.0
    for k in range(70):
        o = px + float(rng.normal(0, 0.1))
        c = o + float(rng.normal(0, 0.2))
        O.append(o); C.append(c); H.append(max(o, c) + 0.3); L.append(min(o, c) - 0.3)
        px = c
    def add(o, c, h, l):
        O.append(o); C.append(c); H.append(h); L.append(l)
    if name == "DBRFRESH":      # DBR reversal, fresh, gap departure -> score 8 Type-1
        add(100.2, 98.8, 100.4, 98.2); add(98.9, 99.1, 99.3, 98.6)
        add(99.1, 98.9, 99.2, 98.5); add(101.0, 101.4, 101.9, 100.8)
        add(101.4, 101.8, 102.1, 101.2); add(101.8, 102.2, 102.5, 101.6)
    elif name == "RBREXC":      # RBR continuation + exceptional LEGOUT
        add(99.8, 101.2, 101.4, 99.6); add(101.1, 100.9, 101.3, 100.7)
        add(100.9, 101.0, 101.2, 100.6); add(100.8, 104.0, 104.3, 100.4)
        add(104.0, 104.4, 104.8, 103.8); add(104.4, 104.1, 104.7, 103.9)
    elif name == "RBDSUP":      # RBD supply reversal
        add(99.8, 101.2, 101.2, 99.6); add(101.1, 100.9, 101.3, 100.7)
        add(100.9, 101.0, 101.2, 100.6); add(101.0, 97.8, 101.2, 97.6)
        add(97.8, 97.4, 98.1, 97.1); add(97.4, 97.0, 97.7, 96.8)
    elif name == "TESTED":      # demand zone, 1 test -> score decay
        add(100.2, 98.8, 100.4, 98.2); add(98.9, 99.1, 99.3, 98.6)
        add(99.1, 98.9, 99.2, 98.5); add(99.1, 102.3, 102.6, 99.0)
        add(102.3, 102.6, 102.9, 102.1); add(102.6, 102.4, 102.8, 102.2)
        add(102.4, 100.5, 102.5, 98.9); add(100.5, 98.9, 100.7, 98.6)
        add(98.9, 99.4, 99.6, 98.7)   # 1st close IN zone, 2nd leaves upside -> TYPE 3 live
    else:                       # MULTIBASE weak (p22)
        for k in range(8):
            add(99.9 + 0.05 * (k % 2), 100.0 + 0.05 * ((k + 1) % 2), 100.3, 99.6)
        add(99.1, 100.5, 100.8, 98.9)
        add(100.5, 100.7, 101.0, 100.3); add(100.7, 100.6, 100.9, 100.4)
    idx = pd.date_range(end="2026-09-07", periods=len(O), freq="B")
    return pd.DataFrame({"Open": O, "High": H, "Low": L, "Close": C,
                         "Volume": [100000] * len(O)}, index=idx)


def build_demo():
    stocks = []
    for i, nm in enumerate(["DBRFRESH", "RBREXC", "RBDSUP", "TESTED", "MULTIBASE"]):
        df = demo_symbol(nm, 7 + i)
        stocks.append(scan_symbol(nm, f"Demo {nm} case (PDF diagram)", df))
    return stocks


# ---------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    demo = "--demo" in args
    top = None
    if "--top" in args:
        top = int(args[args.index("--top") + 1])

    if demo:
        stocks = build_demo()
    else:
        universe = load_universe(top)
        stocks, failed = [], 0
        for i, (sym, comp) in enumerate(universe):
            try:
                df = fetch_ohlc(sym + ".NS")
                if df is None:
                    failed += 1
                    continue
                stocks.append(scan_symbol(sym, comp, df))
                print(f"[{i + 1}/{len(universe)}] {sym} ok", flush=True)
            except Exception as exc:
                failed += 1
                print(f"[{i + 1}/{len(universe)}] {sym} FAIL {exc}", flush=True)

    buy7 = sum(1 for s in stocks for z in (s["best"] and [s["best"]] or [])
               if z["side"] == "DEMAND" and z["score"] >= 7)
    sell7 = sum(1 for s in stocks for z in (s["best"] and [s["best"]] or [])
                if z["side"] == "SUPPLY" and z["score"] >= 7)
    conf = sum(1 for s in stocks for tf in s["tfs"].values()
               for z in tf["zones"] if z.get("confirm"))
    payload = {
        "version": VERSION + (" (DEMO DATA)" if demo else ""),
        "date": str(datetime.date.today()),
        "demo": bool(demo),
        "summary": {"stocks": len(stocks), "buy7": buy7, "sell7": sell7,
                    "confirmations": conf},
        "stocks": stocks,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    print(f"[done] {OUT_JSON} — stocks={len(stocks)} buy7={buy7} sell7={sell7} conf={conf}")


if __name__ == "__main__":
    main()
