# 📖 DEEP ANALYSIS — "TRADING IN THE ZONE" (GetTogetherFinance PDF)
### Source: `DOC-20260114-WA0004.pdf` (38 pages, GTF Institute) — analysed page-by-page
### Implementation: `gtf_pdf_engine.py` + `all_timeframe_scanner.py` (v6) + `index.html` ("Multiverse zone" dashboard)

---

## 1️⃣ Fundamentals of Candle Formation (p3)
A candle = **Open, Close, Body, Upper wick, Lower wick**.
- **Green candle**: closes *higher* than its opening price → buyers dominant.
- **Red candle**: closes *lower* than its opening price → sellers dominant.
- **Body** = open–close block (agreement + dominance); **wicks** = rejection / pressure on either side.

Every later concept (base, exciting, zone strength, closing concept) is built on *body vs range* and *wick extremes*.

**Code:** `candle_kind()` computes `body_pct = |close−open| / (high−low) × 100` — the single primitive behind topics 2–4.

## 2️⃣ Types of Candles (p4)
| Type | Rule (PDF exact) |
|---|---|
| Green/Red **EXCITING** | **Body part > 50% of range of the candle** |
| Green/Red **EXPLOSIVE** | Same structure as exciting but **big difference between opening and closing price** (much bigger body/range — coded as body ≥ 1.2 × ATR) |

Exciting/explosive candles are the only candles that can act as a zone's **leg-out** (the "explosive move" you look for in p13 step 2).

## 3️⃣ Base Candle Formation (p5)
**Base candle = Body part < 50% of range.** Four shapes shown (small-body green/red, doji-like) — all reflect *buyers ≈ sellers*:
1. 80,000 buyers / 60,000 sellers (marginally higher)
2. 80,000 / 72,000 (marginally higher)
3. 60,000 / 80,000 (marginally lower)
4. Open ≈ close (balance)

Base candles = **accumulation of pending orders** — the "B" in DBR/RBR/RBD/DBD.
**Psychology (p22):** minimum base candles = concentrated orders = strong zone; **>5 base candles = scattered/weak** (trade-score base component = 0).

## 4️⃣ Exciting Candle Formation (p4 + p25)
Two formations count as exciting:
1. **Body > 50% of range** (p4).
2. **Significant gap + base candle = exciting candle** (p25) — a small-body candle that *gaps* away from the base behaves like an exciting candle (orders skipped prices). Coded: gap ≥ 0.3% of price + base-shaped body → `EXCITING_GAP`, and it earns the **maximum departure score (3/3)** on p33.

## 5️⃣ Strength of the Demand Zone (p7)
Read the **green leg-out** after the base:
- **NORMAL BUYING** – modest green leg-out.
- **STRONG BUYING** – clearly larger body (coded: body ≥ 1.2 × ATR).
- **VERY STRONG BUYING** – huge body and/or follow-through exciting candles (coded: body ≥ 2 × ATR *or* 2+ leg-out candles).
Stronger leg-out = more unfilled buy orders parked in the zone.

## 6️⃣ Strength of the Supply Zone (p8)
Mirror image with the **red leg-out**: NORMAL / STRONG / VERY STRONG **SELLING** (same ATR tiers).

## 7️⃣ Patterns of Zone (p9–10)
| Pattern | Legs | Type |
|---|---|---|
| **DBR** Drop-Base-Rally | red leg-in → base → green leg-out | Demand **REVERSAL** |
| **RBR** Rally-Base-Rally | green leg-in → base → green leg-out | Demand **CONTINUOUS** |
| **RBD** Rally-Base-Drop | green leg-in → base → red leg-out | Supply **REVERSAL** |
| **DBD** Drop-Base-Drop | red leg-in → base → red leg-out | Supply **CONTINUOUS** |

Leg-in colour decides the pattern; leg-out colour decides the side (demand = green leg-out, supply = red leg-out — p15 booster point).

## 8️⃣ Zone Marking (p11–12)
**Demand Zone (body-to-wick, the default):**
- **Proximal line = HIGHEST BODY of all base candles** (max of open/close).
- **Distal line = LOWEST WICK of all base candles.**
**Supply Zone:** Proximal = **lowest body** of all base; Distal = **highest wick** of all base.
Alternative **wick-to-wick** marking also exists (proximal = highest wick of base) — p13 says *"initially we will focus on body-to-wick marking"*. The zone rectangle = **area of pending orders**.

## 9️⃣ Steps of Making Zone (p13–15)
1. Mark a horizontal line at **current market price**.
2. Look **left & down** for an explosive up-move (demand) / **left & up** for an explosive drop (supply).
3. Mark all three components: **leg-in, base, leg-out**.
4. **Important (p15):** leg-out *must* be explosive → maximum pending orders → powerful zone. Leg-out colour fixed by side; leg-in colour depends on pattern.

## 🔟 Exceptional Marking of the Zone (p18–21)
Normal marking uses only base wicks. **Exceptional** marking extends the **distal line** to the extreme wick that pierces the base:
- **Reversal patterns (DBR / RBD):** distal = **lowest wick of leg-in** (demand) / **highest wick of leg-in** (supply).
- **Continuous patterns (RBR / DBD):** distal = **lowest wick of leg-out** (demand) / **highest wick of leg-out** (supply).
Proximal line stays at the base body. The dashboard badges such zones **EXCEPTIONAL LEGIN / EXCEPTIONAL LEGOUT**.

## 1️⃣1️ Candle Breakdown & Market Psychology (p22)
- **Strong zone = less base candles** (orders concentrated, one decision point).
- **Multiple base candles = not strong** (orders scattered, base was a fight, not accumulation).
- If you *must* take a multi-base zone, demand a **very strong leg-out** as compensation.
- Score table (p33) quantifies this: 1–3 base = 2 pts, 4–5 = 1 pt, >5 = 0 pts.

## 1️⃣2️⃣ Closing Concept (+ Price Origin, p23–26)
- **Demand:** the leg-out candle should **close ABOVE the leg-in** (buyers fully absorbed the sellers who created the drop).
- **Supply:** leg-out should **close BELOW the leg-in**.
- **Origin of move / pressure logic (p23, 25-26):** price returning with *normal* selling pressure should bounce at the origin of demand; only *heavy* pressure should even enter the zone — and a strong zone still holds. A base candle with a **significant gap** works like an exciting candle against that pressure (p25).
- **Credibility (p35–36):** a zone that is merely a **reaction of a previous zone = NON-AUTHENTIC (non-tradeable)** — *unless* it shows **good closing** (leg-out closes beyond leg-in), which makes it tradeable again. Fresh zones = authentic.

---

# 🧠 DECISION LAYER (how the PDF turns zones into trades)

## Trade Score — max 8 (p33)
| Component | a | b | c |
|---|---|---|---|
| **FRESHNESS /3** | fresh = **3** | 1 test = **1.5** | 2 tests = **0** |
| **STRENGTH /3** | leaves level **with gap = 3** | **2 exciting** candles = **2** | **1 exciting, no gap = 1** |
| **TIME AT BASE /2** | 1–3 base = **2** | 4–5 base = **1** | >5 base = **0** |

## Entry Types (p34–35)
- **Score ≥ 7 → Entry Type 1 (SET & FORGET):** entry just above proximal (demand) / just below (supply).
- **Score 5–6 → Entry Type 2/3 (CONFIRMATION):** Type 2 = candle closes in zone, next opens in zone; Type 3 = 1st candle closes in zone, 2nd leaves the zone on the trade side.
- **Score < 5 → NO TRADE.**

## Trade Setup (p16–17)
- Entry just outside proximal; **SL just beyond distal "with some room"**; **Target = 2 × (Entry − SL)** (2:1). PDF example: Entry ₹125, SL ₹120 → Target ₹135.

## Trend Clock (p27–28)
50 SMA drawn as a clock: **12–3 = UP** (green MA), **3–6 = DOWN** (red MA), **close to 3 = SIDEWAYS**. Buy demand only in uptrend; sell supply only in downtrend — counter-trend is "extremely dangerous".

## Timeframes (p29)
HTF = **location** (Weekly/Monthly) • ITF = **trend** (Daily/75-min) • LTF = **execution** (15/5-min).

## Curve / Location (p30–32)
Mark nearest fresh supply proximal & demand proximal; split into thirds: **VERY HIGH / HIGH → SELL at LTF**, **LOW / VERY LOW → BUY at LTF**, **EQUILIBRIUM → follow ITF trend**. Buying at daily demand while near weekly supply = stop-loss likely.

## Risk Management (p37)
Risk/trade: **1% beginner, 1.5% intermediate, 2% pro**; ~10 trades/month; **Qty = Risk₹ ÷ (Entry − SL)**; 2:1 (or 3:1) reward — 5W/5L at 2:1 still nets +5K per 10K risked.

---

# 🛠 WHERE EACH TOPIC LIVES IN THE DASHBOARD ("Multiverse zone")

| PDF topic | Engine (`gtf_pdf_engine.py`) | Dashboard (`index.html`) |
|---|---|---|
| 1–4 candles | `candle_kind()` | Course card 1–4 |
| 5–6 strength | `strength_label()` | popup: "💪 VERY STRONG BUYING/SELLING" |
| 7 patterns | `detect_zones_pdf()` → `pdf_pattern` (DBR/RBR/RBD/DBD) | popup badge 📐 |
| 8 marking | prox/dist body-to-wick (+ `prox_ww`) | popup "Marking: BODY-TO-WICK" |
| 9 steps | leg-in/base/leg-out walk | zone cards |
| 10 exceptional | `exceptional` = LEGIN/LEGOUT | popup badge EXCEPTIONAL |
| 11 psychology | `base_points()` (p33) | score line "Base x/2" |
| 12 closing/credibility | `closing_ok`, `auth` (0/1/2) | popup "Closing ✓ / NON-AUTHENTIC" |
| Score/entries | `fresh_points/strength_points/base_points`, `entry_type_for` | 📘 x/8 badge + entry type |
| Setup p16-17 | `setup{entry,sl,target}` | popup 🎯 line |
| Trend clock | `trend_clock()` | 50DN warning + w_trend |
| Curve | `curve_position()` | "📍 loc" column |
| Risk p37 | `risk_plan()` | Course card calculator |

**Verification:** `test_gtf_pdf_engine.py` — 48/48 checks pass, every scenario mirrors a PDF diagram (DBR+exceptional-LEGIN, RBR+exceptional-LEGOUT, RBD, DBD, gap-exciting→score 8→Type 1, >5-base weak zone, retest decay 6→4.5→NO TRADE, breakdown invalidation, clock, curve bands, p17 ₹125/₹120→qty 200/tgt ₹135).
