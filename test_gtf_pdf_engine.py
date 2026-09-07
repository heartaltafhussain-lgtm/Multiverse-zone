#!/usr/bin/env python3
"""Verification suite for gtf_pdf_engine — every scenario mirrors a PDF diagram."""
import numpy as np
from gtf_pdf_engine import (detect_zones_pdf, trend_clock, curve_position,
                            risk_plan, candle_kind, fresh_points,
                            strength_points, base_points, entry_type_for,
                            confirmation_status)

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def warmup(n=30, px=100.0):
    O, H, L, C = [], [], [], []
    for k in range(n):
        o = px + (0.1 if k % 2 else -0.1)
        c = o + (0.2 if k % 2 else -0.2)
        O.append(o); C.append(c); H.append(max(o, c) + 0.3); L.append(min(o, c) - 0.3)
    return O, H, L, C


def add(arrs, o, c, h, l):
    arrs[0].append(o); arrs[1].append(h); arrs[2].append(l); arrs[3].append(c)


print("== 1) candle classification (p4/p5/p25) ==")
k, bp = candle_kind(0.8, 1.0, 1.0, False, False)
check("exciting body>50%", k == "EXCITING" and bp == 80.0, f"{k} {bp}")
k, _ = candle_kind(3.0, 4.0, 1.0, False, False)
check("explosive big body", k == "EXPLOSIVE", k)
k, _ = candle_kind(2.0, 4.0, 1.0, False, False)
check("exactly 50% = BASE (p5)", k == "BASE", k)
k, _ = candle_kind(0.3, 1.0, 1.0, False, False)
check("base body<50%", k == "BASE", k)
k, _ = candle_kind(0.3, 1.0, 1.0, True, False)
check("gap+base = exciting (p25)", k == "EXCITING_GAP", k)

print("== 2) p33 score tables ==")
check("fresh 3/1.5/0", (fresh_points(0), fresh_points(1), fresh_points(2)) == (3.0, 1.5, 0.0))
check("strength gap3/2exc2/1exc1", (strength_points(True, 1), strength_points(False, 2),
                                    strength_points(False, 1)) == (3.0, 2.0, 1.0))
check("base 2/1/0", (base_points(2), base_points(5), base_points(6)) == (2.0, 1.0, 0.0))
check("entry 7->T1", entry_type_for(7, 1)[1] == "S&F")
check("entry 5-6->T2/3", entry_type_for(6, 1)[1] == "CONF" and entry_type_for(5, 1)[1] == "CONF")
check("entry <5 skip", entry_type_for(4.5, 1)[1] == "SKIP")
check("non-authentic skip", entry_type_for(8, 0)[1] == "SKIP")

print("== 3) DBR demand + exceptional LEGIN (p9/p11/p18) ==")
arrs = warmup()
add(arrs, 100.2, 98.8, 100.4, 98.2)    # 30 leg-in red exciting
add(arrs, 98.9, 99.1, 99.3, 98.6)      # 31 base
add(arrs, 99.1, 98.9, 99.2, 98.5)      # 32 base
add(arrs, 99.1, 102.3, 102.6, 99.0)    # 33 leg-out green explosive
add(arrs, 102.3, 102.5, 102.8, 102.1)  # 34 consolidation
add(arrs, 102.5, 102.4, 102.7, 102.2)  # 35
add(arrs, 102.4, 100.5, 102.5, 98.9)   # 36 retest into zone
add(arrs, 100.5, 97.5, 100.7, 97.2)    # 37 breakdown
O, H, L, C = arrs
d0, _ = detect_zones_pdf(O[:36], H[:36], L[:36], C[:36])   # before retest
dz = [z for z in d0 if z["born"] == 33]
check("demand zone born at legout", len(dz) == 1, f"{len(dz)}")
if dz:
    z = dz[0]
    check("pattern DBR reversal", z["pdf_pattern"] == "DBR" and z["pdf_kind"] == "REVERSAL",
          z["pdf_pattern"])
    check("proximal = highest body of base (99.1)", abs(z["prox"] - 99.1) < 1e-6, z["prox"])
    check("exceptional LEGIN distal = 98.2", z["exceptional"] == "LEGIN" and
          abs(z["dist"] - 98.2) < 1e-6, f'{z["exceptional"]} {z["dist"]}')
    check("marking BODY-TO-WICK", z["marking"] == "BODY-TO-WICK")
    check("strength VERY STRONG BUYING (p7)", z["strength_label"].startswith("VERY STRONG"),
          z["strength_label"])
    check("closing concept ok (p24)", z["closing_ok"] is True)
    check("birth score 6 (dep1+fresh3+base2)", z["birth_score"] == 6.0, z["birth_score"])
    check("entry type CONF at birth", z["ets"] == "CONF", z["et"])
    check("setup 2:1 (p16-17)", z["setup"]["target"] > z["setup"]["entry"] > z["setup"]["sl"])
d1, _ = detect_zones_pdf(O[:37], H[:37], L[:37], C[:37])   # retest, still holding
dz = [z for z in d1 if z["born"] == 33]
check("retest counted -> score decays", dz and dz[0]["tests"] == 1 and dz[0]["score"] == 4.5,
      f'{dz[0]["tests"] if dz else "-"} {dz[0]["score"] if dz else "-"}')
check("decayed zone = NO TRADE", dz and dz[0]["ets"] == "SKIP")
d2, _ = detect_zones_pdf(O, H, L, C)                       # full: breakdown at 37
check("broken zone removed after close<distal",
      not any(zz["born"] == 33 for zz in d2))

print("== 4) RBR continuation + exceptional LEGOUT (p9/p19) ==")
arrs = warmup()
add(arrs, 99.8, 101.2, 101.4, 99.6)    # leg-in green
add(arrs, 101.1, 100.9, 101.3, 100.7)  # base
add(arrs, 100.9, 101.0, 101.2, 100.6)  # base
add(arrs, 100.8, 104.0, 104.3, 100.4)  # leg-out wick below base -> exceptional LEGOUT
O, H, L, C = arrs
d, s = detect_zones_pdf(O, H, L, C)
dz = [z for z in d if z["pdf_pattern"] == "RBR" and z["born"] == 33]
check("RBR detected", len(dz) == 1, f"{[(z['pdf_pattern'], z['born']) for z in d]}")
if dz:
    check("exceptional LEGOUT distal=100.4", dz[0]["exceptional"] == "LEGOUT" and
          abs(dz[0]["dist"] - 100.4) < 1e-6, f'{dz[0]["exceptional"]} {dz[0]["dist"]}')

print("== 5) RBD supply reversal (p10/p12/p20) ==")
arrs = warmup()
add(arrs, 99.8, 101.2, 101.2, 99.6)    # leg-in green (no upper wick beyond base)
add(arrs, 101.1, 100.9, 101.3, 100.7)
add(arrs, 100.9, 101.0, 101.2, 100.6)
add(arrs, 101.0, 97.8, 101.2, 97.6)    # leg-out red explosive
O, H, L, C = arrs
d, s = detect_zones_pdf(O, H, L, C)
sz = [z for z in s if z["pdf_pattern"] == "RBD"]
check("RBD detected", len(sz) == 1, f"{[z['pdf_pattern'] for z in s]}")
if sz:
    z = sz[0]
    check("supply proximal = lowest body (100.9)", abs(z["prox"] - 100.9) < 1e-6, z["prox"])
    check("supply distal = highest wick (101.3)", abs(z["dist"] - 101.3) < 1e-6, z["dist"])
    check("closing below legin (p24)", z["closing_ok"] is True)
    check("strength VERY STRONG SELLING (p8)", "SELLING" in z["strength_label"])

print("== 6) DBD continuation (p10/p21) ==")
arrs = warmup()
add(arrs, 100.2, 98.8, 100.4, 98.2)    # leg-in red
add(arrs, 98.9, 99.1, 99.3, 98.6)
add(arrs, 99.1, 98.9, 99.2, 98.5)
add(arrs, 98.9, 95.8, 99.1, 95.6)      # leg-out red
O, H, L, C = arrs
d, s = detect_zones_pdf(O, H, L, C)
sz = [z for z in s if z["pdf_pattern"] == "DBD"]
check("DBD detected", len(sz) >= 1, f"{[z['pdf_pattern'] for z in s]}")

print("== 7) gap departure = exciting + score 8 -> SET & FORGET (p25/p33/p34) ==")
arrs = warmup()
add(arrs, 100.2, 98.8, 100.4, 98.2)
add(arrs, 98.9, 99.1, 99.3, 98.6)
add(arrs, 99.1, 98.9, 99.2, 98.5)
add(arrs, 101.0, 101.4, 101.9, 100.8)  # gap-up base-shaped candle = exciting (p25)
O, H, L, C = arrs
d, s = detect_zones_pdf(O, H, L, C)
dz = [z for z in d if z["born"] == 33]
check("gap-exciting zone born", len(dz) == 1, f"{len(d)}")
if dz:
    check("dep=3 via gap", dz[0]["dep"] == 3.0, dz[0]["dep"])
    check("score 8 -> TYPE 1 S&F", dz[0]["score"] == 8.0 and dz[0]["ets"] == "S&F",
          f'{dz[0]["score"]} {dz[0]["et"]}')

print("== 8) multiple base candles = weak (p22/p33) ==")
arrs = warmup()          # 30 base candles then exciting -> n_base > 5
add(arrs, 99.1, 100.5, 100.8, 98.9)   # exciting but NOT very-strong legout
O, H, L, C = arrs
d, s = detect_zones_pdf(O, H, L, C)
if d:
    z = d[-1]
    check(">5 base -> base pts 0", z["base"] == 0.0, z["base"])
    check("p22 gate: >5 base + non-very-strong legout = NO TRADE",
          z["p22_weak"] is True and z["ets"] == "SKIP" and "p22" in z["et"],
          f'{z["p22_weak"]} {z["et"]}')
else:
    check(">5 base zone exists but weak", False, "no zone")

print("== 12) entry confirmation live status (p34-35) ==")
arrs = warmup()
add(arrs, 100.2, 98.8, 100.4, 98.2)
add(arrs, 98.9, 99.1, 99.3, 98.6)
add(arrs, 99.1, 98.9, 99.2, 98.5)
add(arrs, 99.1, 102.3, 102.6, 99.0)   # 33 legout -> zone 98.2-99.1
add(arrs, 100.0, 98.95, 100.2, 98.6)  # 34 close IN zone
add(arrs, 98.9, 98.95, 99.0, 98.7)    # 35 open IN zone, still inside -> TYPE 2
O, H, L, C = arrs
d, _ = detect_zones_pdf(O, H, L, C)
z = [x for x in d if x["born"] == 33]
check("zone present", len(z) == 1)
if z:
    st = confirmation_status(O, H, L, C, z[0])
    check("TYPE 2 LIVE detected", st and st.startswith("TYPE 2"), st)
    C2 = list(C); C2[-1] = 99.6        # 2nd candle leaves zone upside -> TYPE 3
    st = confirmation_status(O, H, L, C2, z[0])
    check("TYPE 3 LIVE detected", st and st.startswith("TYPE 3"), st)

print("== 9) trend clock (p27-28) ==")
up = [100 + i * 0.3 for i in range(70)]
dn = [130 - i * 0.3 for i in range(70)]
fl = [100 + (0.05 if i % 2 else -0.05) for i in range(70)]
check("clock UP", trend_clock(up)[0] == "UP", trend_clock(up))
check("clock DOWN", trend_clock(dn)[0] == "DOWN", trend_clock(dn))
check("clock SIDEWAYS", trend_clock(fl)[0] == "SIDEWAYS", trend_clock(fl))

print("== 10) curve position (p30-32) ==")
cp = curve_position(109.5, 100, 110)
check("VERY HIGH -> SELL", cp["band"] == "VERY HIGH" and "SELL" in cp["action"], cp)
cp = curve_position(107.0, 100, 110)
check("HIGH -> SELL", cp["band"] == "HIGH", cp)
cp = curve_position(102.5, 100, 110)
check("LOW -> BUY", cp["band"] == "LOW", cp)
cp = curve_position(101.0, 100, 110)
check("VERY LOW -> BUY", cp["band"] == "VERY LOW", cp)
cp = curve_position(104.5, 100, 110)
check("EQUILIBRIUM -> trend follow", cp["band"] == "EQUILIBRIUM", cp)

print("== 11) risk management (p37, p17 example) ==")
rp = risk_plan(100000, 1.0, 125, 120, "DEMAND")
check("PDF p17 example: qty 200 tgt 135", rp["qty"] == 200 and rp["target"] == 135.0, rp)
rp = risk_plan(100000, 2.0, 125, 120, "DEMAND")
check("2% pro risk qty 400", rp["qty"] == 400, rp)

print(f"\nTOTAL: {PASS} passed, {FAIL} failed")
raise SystemExit(1 if FAIL else 0)
