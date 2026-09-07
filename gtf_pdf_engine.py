#!/usr/bin/env python3
"""
GTF "TRADING IN THE ZONE" PDF — course-faithful zone engine.

Implements, page-by-page, the 12 concepts of the GetTogetherFinance PDF
(DOC-20260114-WA0004, 38 pages):

  1. Fundamentals of candle formation ......... p3   (open/close/body/wicks; green vs red)
  2. Types of candles .......................... p4   (EXCITING = body > 50% of range;
                                                       EXPLOSIVE = exciting with a big
                                                       open-close difference)
  3. Base candle formation ..................... p5   (BASE = body < 50% of range;
                                                       buyers ~ sellers)
  4. Exciting candle formation ................. p4/p25 (body>50%; ALSO p25 rule:
                                                       significant gap + base candle =
                                                       exciting candle)
  5. Strength of the demand zone ............... p7   (NORMAL / STRONG / VERY STRONG
                                                       BUYING, by leg-out size & follow-
                                                       through)
  6. Strength of the supply zone ............... p8   (NORMAL / STRONG / VERY STRONG
                                                       SELLING)
  7. Patterns of zone .......................... p9-10 (DBR reversal, RBR continuation,
                                                       RBD reversal, DBD continuation)
  8. Zone marking .............................. p11-12 (DEMAND: proximal = HIGHEST BODY
                                                       of all base, distal = LOWEST WICK
                                                       of all base; SUPPLY mirrored;
                                                       BODY-TO-WICK default, WICK-TO-WICK
                                                       alternative)
  9. Steps of making zone ...................... p13-15 (leg-in / base / leg-out; leg-out
                                                       must be explosive; leg-out colour
                                                       = green demand / red supply)
 10. Exceptional marking of the zone ........... p18-21 (REVERSAL: distal extended to
                                                       leg-in extreme wick; CONTINUATION:
                                                       distal extended to leg-out extreme
                                                       wick)
 11. Candle breakdown & market psychology ...... p22  (minimum base candles; multiple
                                                       base needs a very strong leg-out)
 12. Closing concept ........................... p23-26 (demand: leg-out must CLOSE ABOVE
                                                       leg-in; supply: close below leg-in;
                                                       origin of move / pressure logic)

PLUS the decision layer:
  - TRADE SCORE (p33): FRESHNESS /3 (fresh 3, 1 test 1.5, 2 tests 0)
                       + STRENGTH /3 (gap departure 3, 2 exciting 2, 1 exciting no gap 1)
                       + TIME AT BASE /2 (1-3 base = 2, 4-5 = 1, >5 = 0)  -> max 8
  - ENTRY TYPES (p34-35): score >=7 -> TYPE 1 SET & FORGET; 5-6 -> TYPE 2/3 CONFIRMATION;
                          <5 -> NO TRADE.
  - CREDIBILITY (p35-36): zone that is a reaction of a previous same-side zone =
                          NON-AUTHENTIC (non-tradeable) unless good closing (tradeable).
  - TRADE SETUP (p16-17): entry just above/below proximal, SL just beyond distal with
                          room, target = 2 x (entry - SL).
  - TREND CLOCK (p27-28): 50 SMA clock — 12-3 up, 3-6 down, near 3 sideways.
  - CURVE / LOCATION (p30-32): nearest fresh S.Z proximal to nearest fresh D.Z proximal
                          split in thirds: VERY HIGH / HIGH / EQUILIBRIUM / LOW / VERY LOW.
"""
import numpy as np

# ------------------------------------------------------------------ constants
BODY_PCT_EXCITING = 50.0      # p4: exciting candle = body part > 50% of range
BODY_PCT_BASE = 50.0          # p5: base candle     = body part < 50% of range
EXPLOSIVE_BODY_ATR = 1.2      # p4: "big difference between opening and closing"
GAP_PCT = 0.003               # significant gap = 0.3% of price (p16/p25/p33)
VERY_STRONG_ATR = 2.0         # p7/p8: very strong buying/selling leg-out
STRONG_ATR = 1.2              # p7/p8: strong buying/selling leg-out
MAX_ZONES = 8
LOOKBACK_BARS = 220
MIN_ZONE_ATR = 0.05
MAX_ZONE_ATR = 1.80
SL_ROOM_FRAC = 0.10           # p17: SL "with some room" beyond distal
SL_ROOM_MIN_PCT = 0.002       # floor room = 0.2% of distal


# ------------------------------------------------------------------ helpers
def wilder_atr(high, low, close, n=14):
    high = np.asarray(high, float)
    low = np.asarray(low, float)
    close = np.asarray(close, float)
    prev = np.roll(close, 1)
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev), np.abs(low - prev)))
    tr[0] = high[0] - low[0]
    atr = np.full(len(tr), np.nan)
    if len(tr) < n:
        return atr
    atr[n - 1] = tr[:n].mean()
    alpha = 1.0 / n
    for i in range(n, len(tr)):
        atr[i] = atr[i - 1] * (1 - alpha) + tr[i] * alpha
    return atr


def candle_kind(body, rng, atr_i, gap_up, gap_dn):
    """p4/p5/p25 classification -> (kind, body_pct)."""
    body_pct = body / max(rng, 1e-9) * 100.0
    if body_pct > BODY_PCT_EXCITING:
        kind = "EXPLOSIVE" if (np.isfinite(atr_i) and atr_i > 0 and
                               body >= atr_i * EXPLOSIVE_BODY_ATR) else "EXCITING"
    elif gap_up or gap_dn:
        kind = "EXCITING_GAP"          # p25: significant gap + base = exciting
    else:
        kind = "BASE"
    return kind, round(body_pct, 1)


def fresh_points(tests):
    """p33 FRESHNESS /3."""
    return 3.0 if tests == 0 else 1.5 if tests == 1 else 0.0


def strength_points(has_gap, n_legout):
    """p33 STRENGTH /3: gap=3 | 2 exciting=2 | 1 exciting no gap=1."""
    if has_gap:
        return 3.0
    return 2.0 if n_legout >= 2 else 1.0


def base_points(n_base):
    """p33 TIME AT BASE /2."""
    if 1 <= n_base <= 3:
        return 2.0
    return 1.0 if 4 <= n_base <= 5 else 0.0


def score_grade(score):
    """grade on the /8 PDF scale."""
    return "A+" if score >= 7 else "A" if score >= 6 else "B" if score >= 5 else "C"


def entry_type_for(score, auth):
    """p34-35 entry types + p35-36 credibility gate."""
    if auth == 0:
        return "NON-AUTHENTIC — NO TRADE", "SKIP"
    if score >= 7:
        return "TYPE 1 — SET & FORGET", "S&F"
    if score >= 5:
        return "TYPE 2/3 — CONFIRMATION", "CONF"
    return "NO TRADE (<5)", "SKIP"


def strength_label(side, legout_atr, n_legout):
    """p7/p8 strength of the zone."""
    tier = "VERY STRONG" if (legout_atr >= VERY_STRONG_ATR or n_legout >= 2) \
        else "STRONG" if legout_atr >= STRONG_ATR else "NORMAL"
    return f"{tier} {'BUYING' if side == 'DEMAND' else 'SELLING'}"


# ------------------------------------------------------------------ detection
def detect_zones_pdf(o, h, l, c, vol=None, max_zones=MAX_ZONES, lookback=LOOKBACK_BARS):
    """
    PDF-faithful zone detection (p3-p26).
    Returns (demands, supplies) — lists of zone dicts, tracked to the last bar
    (tests counted, zones invalidated on close beyond distal).
    """
    o = np.asarray(o, float)
    h = np.asarray(h, float)
    l = np.asarray(l, float)
    c = np.asarray(c, float)
    n = len(c)
    atr = wilder_atr(h, l, c)
    start = max(n - lookback, 16)

    kinds = []
    for i in range(n):
        a = atr[i]
        gap_up = i > 0 and np.isfinite(h[i - 1]) and (o[i] - h[i - 1]) >= c[i] * GAP_PCT
        gap_dn = i > 0 and np.isfinite(l[i - 1]) and (l[i - 1] - o[i]) >= c[i] * GAP_PCT
        kinds.append((candle_kind(abs(c[i] - o[i]), h[i] - l[i], a, gap_up, gap_dn)[0],
                      gap_up, gap_dn))

    demands, supplies = [], []

    def is_exciting(k):
        return k in ("EXCITING", "EXPLOSIVE", "EXCITING_GAP")

    for i in range(max(start, 1), n):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        kind_i, gap_up_i, gap_dn_i = kinds[i]
        green = c[i] > o[i]
        red = c[i] < o[i]

        for side in ("DEMAND", "SUPPLY"):
            want = (green and side == "DEMAND") or (red and side == "SUPPLY")
            if not want or not is_exciting(kind_i):
                continue
            zones = demands if side == "DEMAND" else supplies

            # ---- walk back over base candles (p5/p13 step 3)
            b_start = i - 1
            while b_start > start and kinds[b_start][0] == "BASE":
                b_start -= 1
            base_idx = list(range(b_start, i)) if kinds[b_start][0] == "BASE" else \
                list(range(b_start + 1, i))
            if not base_idx:
                continue
            legin_idx = base_idx[0] - 1

            # ---- pattern (p9/p10): leg-in colour decides reversal/continuation
            if legin_idx >= 0 and c[legin_idx] < o[legin_idx]:
                pattern, pkind = ("DBR", "REVERSAL") if side == "DEMAND" else \
                    ("DBD", "CONTINUATION")
            else:
                pattern, pkind = ("RBR", "CONTINUATION") if side == "DEMAND" else \
                    ("RBD", "REVERSAL")

            # ---- leg-out count (consecutive exciting same-colour candles)
            j = i
            while j + 1 < n and is_exciting(kinds[j + 1][0]) and \
                    ((side == "DEMAND") == (c[j + 1] > o[j + 1])):
                j += 1
            legout_idx = j
            n_legout = legout_idx - i + 1

            # ---- p11/p12 marking: BODY-TO-WICK
            prox = max(max(o[k], c[k]) for k in base_idx)          # highest body (demand)
            dist = min(l[k] for k in base_idx)                     # lowest wick (demand)
            prox_ww = max(h[k] for k in base_idx)                  # wick-to-wick alt
            if side == "SUPPLY":
                prox = min(min(o[k], c[k]) for k in base_idx)      # lowest body
                dist = max(h[k] for k in base_idx)                 # highest wick
                prox_ww = min(l[k] for k in base_idx)

            # ---- p18-21 exceptional marking: distal extended to extreme wick
            exceptional = None
            if side == "DEMAND":
                if pkind == "REVERSAL" and legin_idx >= 0 and l[legin_idx] < dist:
                    exceptional = "LEGIN"
                    dist = l[legin_idx]
                if l[legout_idx] < dist:
                    exceptional = "LEGOUT"
                    dist = l[legout_idx]
            else:
                if pkind == "REVERSAL" and legin_idx >= 0 and h[legin_idx] > dist:
                    exceptional = "LEGIN"
                    dist = h[legin_idx]
                if h[legout_idx] > dist:
                    exceptional = "LEGOUT"
                    dist = h[legout_idx]

            height = abs(prox - dist)
            if not (a * MIN_ZONE_ATR <= height <= a * MAX_ZONE_ATR):
                continue
            if _overlap(zones, prox, dist):
                continue

            has_gap = gap_up_i if side == "DEMAND" else gap_dn_i
            legout_atr = abs(c[i] - o[i]) / a
            n_base = len(base_idx)

            # ---- p23-26 closing concept: leg-out close vs leg-in extreme
            if legin_idx >= 0:
                closing_ok = (c[legout_idx] > h[legin_idx]) if side == "DEMAND" \
                    else (c[legout_idx] < l[legin_idx])
            else:
                closing_ok = True

            # ---- p35-36 credibility: reaction of a previous same-side zone?
            auth = 1
            for z2 in zones:
                lo2, hi2 = sorted((z2["prox"], z2["dist"]))
                lo_win = min(l[k] for k in base_idx + [i])
                hi_win = max(h[k] for k in base_idx + [i])
                if lo2 * 0.999 <= lo_win and hi_win <= hi2 * 1.001 and z2["born"] < i:
                    auth = 2 if closing_ok else 0     # reaction: tradeable only w/ good close
                    break

            dep = strength_points(has_gap, n_legout)
            bpts = base_points(n_base)
            fpts = fresh_points(0)
            score = dep + fpts + bpts
            et, ets = entry_type_for(score, auth)
            # p22 NOTE: >5 base candles zone tab hi le sakte ho jab legout VERY STRONG ho
            p22_weak = n_base > 5 and not (legout_atr >= VERY_STRONG_ATR or n_legout >= 2)
            if p22_weak:
                et, ets = "NO TRADE (>5 base + legout very strong nahi — p22)", "SKIP"

            # ---- p16-17 trade setup (2:1)
            room = max(SL_ROOM_FRAC * height, SL_ROOM_MIN_PCT * dist)
            if side == "DEMAND":
                entry, sl = prox, dist - room
                target = entry + 2 * (entry - sl)
            else:
                entry, sl = prox, dist + room
                target = entry - 2 * (sl - entry)

            zones.append({
                "side": side,
                "pat": "DR DEMAND" if side == "DEMAND" else "RD SUPPLY",
                "pdf_pattern": pattern,
                "pdf_kind": pkind,
                "prox": round(float(prox), 2),
                "dist": round(float(dist), 2),
                "prox_ww": round(float(prox_ww), 2),
                "marking": "BODY-TO-WICK",
                "exceptional": exceptional,
                "born": i,
                "legin_idx": int(legin_idx),
                "base_idx": [int(k) for k in base_idx],
                "legout_idx": int(legout_idx),
                "tests": 0,
                "n_base": n_base,
                "n_legout": n_legout,
                "legout": round(float(legout_atr), 2),
                "body_pct": round(abs(c[i] - o[i]) / max(h[i] - l[i], 1e-9) * 100.0, 1),
                "has_gap": bool(has_gap),
                "p22_weak": bool(p22_weak),
                "strength_label": strength_label(side, legout_atr, n_legout),
                "closing_ok": bool(closing_ok),
                "auth": auth,
                "dep": dep, "fresh": fpts, "base": bpts,
                "score": round(score, 1),
                "grade": score_grade(score),
                "birth_score": round(score, 1),
                "birth_grade": score_grade(score),
                "et": et, "ets": ets,
                "setup": {"entry": round(float(entry), 2),
                          "sl": round(float(sl), 2),
                          "target": round(float(target), 2),
                          "rr": 2.0},
                "vol_ratio": _vol_ratio(vol, i),
            })
            if len(zones) > max_zones:
                zones.pop(0)

        # ---- tests + invalidation (p33 freshness decay, p36 authenticity)
        for zones, is_dem in ((demands, True), (supplies, False)):
            keep = []
            for z in zones:
                if i <= z["legout_idx"]:
                    keep.append(z)
                    continue
                lo_z, hi_z = sorted((z["prox"], z["dist"]))
                px = l[i] if is_dem else h[i]
                in_zone = lo_z <= px <= hi_z
                px_prev = l[i - 1] if is_dem else h[i - 1]
                was_in = lo_z <= px_prev <= hi_z if i - 1 > z["legout_idx"] else False
                if in_zone and not was_in:
                    z["tests"] += 1
                    z["fresh"] = fresh_points(z["tests"])
                    z["score"] = round(z["dep"] + z["fresh"] + z["base"], 1)
                    z["grade"] = score_grade(z["score"])
                    z["et"], z["ets"] = entry_type_for(z["score"], z["auth"])
                broken = (c[i] < lo_z) if is_dem else (c[i] > hi_z)
                if broken:
                    continue
                keep.append(z)
            zones[:] = keep[-max_zones:]

    return demands, supplies


def _overlap(zones, prox, dist):
    lo2, hi2 = sorted((prox, dist))
    for z in zones:
        lo1, hi1 = sorted((z["prox"], z["dist"]))
        ov = min(hi1, hi2) - max(lo1, lo2)
        if ov > 0 and ov / max(hi2 - lo2, 1e-9) > 0.50:
            return True
    return False


def _vol_ratio(vol, i):
    if vol is None:
        return None
    try:
        v = np.asarray(vol, float)
        if i >= len(v) or not np.isfinite(v[i]) or v[i] <= 0:
            return None
        win = v[max(0, i - 20):i]
        avg = np.nanmean(win) if len(win) else np.nan
        if not np.isfinite(avg) or avg <= 0:
            return None
        return round(float(v[i] / avg), 2)
    except Exception:
        return None


# ------------------------------------------------------------------ decision layer
def trend_clock(close, ltp=None):
    """p27-28 50-SMA clock: 12-3 = UP, 3-6 = DOWN, near 3 = SIDEWAYS."""
    close = np.asarray(close, float)
    if len(close) < 58:
        return "UNKNOWN", "need 58+ bars for 50 SMA"
    sma = np.convolve(close, np.ones(50) / 50, mode="valid")
    last, prev = sma[-1], sma[-8]
    if ltp is None:
        ltp = close[-1]
    slope_up = last >= prev
    slope_dn = last <= prev
    near = abs(ltp - last) / last < 0.004
    if near or (slope_up and slope_dn):
        return "SIDEWAYS", "price near 3 o'clock on the 50-SMA clock"
    if ltp >= last and slope_up:
        return "UP", "50 SMA between 12-3 (green quadrant)"
    if ltp <= last and slope_dn:
        return "DOWN", "50 SMA between 3-6 (red quadrant)"
    return "UP" if ltp >= last else "DOWN", "mixed clock — price side decides"


def curve_position(ltp, demand_prox, supply_prox):
    """p30-32 location on the curve (thirds between fresh DZ/SZ proximals)."""
    if demand_prox is None or supply_prox is None:
        return None
    span = supply_prox - demand_prox
    if span <= 0:
        return {"band": "EQUILIBRIUM", "pos": 0.5, "action": "follow ITF trend"}
    pos = (ltp - demand_prox) / span
    if pos >= 5 / 6:
        band, action = "VERY HIGH", "SELL (LTF)"
    elif pos >= 2 / 3:
        band, action = "HIGH", "SELL (LTF)"
    elif pos > 1 / 3:
        band, action = "EQUILIBRIUM", "follow ITF trend (UP=buy, DOWN=sell)"
    elif pos > 1 / 6:
        band, action = "LOW", "BUY (LTF)"
    else:
        band, action = "VERY LOW", "BUY (LTF)"
    return {"band": band, "pos": round(float(pos), 3), "action": action}


def risk_plan(capital, risk_pct, entry, sl, side="DEMAND", rr=2.0):
    """p37 risk management: qty = risk/(entry-SL), target rr:1."""
    per_share = abs(entry - sl)
    if per_share <= 0 or capital <= 0:
        return None
    risk_amt = capital * risk_pct / 100.0
    qty = int(risk_amt // per_share)
    target = entry + rr * (entry - sl) if side == "DEMAND" else entry - rr * (sl - entry)
    return {"risk_amt": round(risk_amt, 2), "qty": qty,
            "target": round(float(target), 2), "rr": rr}


def confirmation_status(o, h, l, c, z):
    """p34-35 live entry-confirmation on the last two candles:
       TYPE 2: 1st candle closes within zone AND next candle opens within zone.
       TYPE 3: 1st candle closes within zone AND 2nd leaves the zone on trade side."""
    lo, hi = sorted((float(z["prox"]), float(z["dist"])))
    dem = str(z.get("side")) == "DEMAND"
    c = np.asarray(c, float)
    o = np.asarray(o, float)
    if len(c) < 2:
        return None
    c1, o0, c0 = c[-2], o[-1], c[-1]
    in1 = lo <= c1 <= hi
    if not in1:
        return None
    if (dem and c0 > hi) or ((not dem) and c0 < lo):
        return "TYPE 3 LIVE — 1st candle zone me close, 2nd zone ke bahar close (p35)"
    if lo <= o0 <= hi:
        return "TYPE 2 LIVE — candle zone me close hui, current candle zone me open (p34)"
    return "WAIT — 1st candle zone me close; 2nd candle ka open/close confirm karo (p34-35)"


def detect_active_zones_df(df, max_zones=MAX_ZONES, lookback=LOOKBACK_BARS):
    """pandas convenience wrapper used by all_timeframe_scanner.py."""
    vol = df["Volume"].to_numpy(float) if "Volume" in df.columns else None
    ds, ss = detect_zones_pdf(
        df["Open"].to_numpy(float), df["High"].to_numpy(float),
        df["Low"].to_numpy(float), df["Close"].to_numpy(float),
        vol=vol, max_zones=max_zones, lookback=lookback)
    for z in ds + ss:
        try:
            z["born_date"] = str(df.index[z["born"]].date())
        except Exception:
            z["born_date"] = None
    return ds, ss
