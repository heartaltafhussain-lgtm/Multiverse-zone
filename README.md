# 🌌 MULTIVERSE ZONE — Demand/Supply Dashboard (GTF "Trading in the Zone" PDF)

100% PDF-faithful dashboard: zones = **leg-in + base + exciting/explosive leg-out**,
patterns **DBR/RBR/RBD/DBD**, **body-to-wick + exceptional marking**, strength labels,
closing concept, credibility, **trade score /8 (p33)**, **entry types (p34-35)**,
**2:1 setup (p16-17)**, **50-SMA trend clock (p27-28)**, **curve location (p30-32)**,
**risk management (p37)**. Deep analysis: `GTF_PDF_Deep_Analysis.md`.

## 📁 Files (GitHub pe upload karne ke liye)
| File | Kaam |
|---|---|
| `index.html` | 🌌 Dashboard (zones table + candlestick chart + zone overlays + course + calculators) |
| `gtf_pdf_engine.py` | PDF rule engine (p3-37) — 51/51 tests |
| `test_gtf_pdf_engine.py` | Verification suite (`python3 test_gtf_pdf_engine.py`) |
| `multiverse_scanner.py` | NIFTY-500 scanner (1D/1W/1M) → `gtf_live_data.json` (charts ke liye candles samet) |
| `nifty500_universe.csv` | 500 symbols universe |
| `GTF_PDF_Deep_Analysis.md` | PDF ki 12-topic deep analysis |
| `.github/workflows/daily_scan.yml` | Mon–Fri auto-scan + JSON commit |
| `requirements.txt` | pandas, numpy, yfinance |
| `gtf_live_data.json` | Demo data pehle se hai (real scan Actions me banega) |

## 🚀 GitHub setup — step by step
1. **GitHub.com → + → New repository** → naam **`Multiverse-zone`** rakho → **Public** → Create.
   (Public zaroori = free GitHub Pages.)
2. Repo page pe **"uploading an existing file"** link kholo → **saari upar wali files drag-drop** karo
   (`.github` folder samet — hidden folder bhi upload hota hai drag-drop se) → **Commit changes**.
3. **Settings → Pages** → Source: **Deploy from a branch** → Branch: **`main`** → folder **`/ (root)`** → Save.
4. **Settings → Actions → General** → Workflow permissions → **Read and write permissions** ✅ → Save.
   (Isse daily bot `gtf_live_data.json` repo me commit kar sakta hai.)
5. **Actions tab** → "Multiverse Zone — Daily NSE 500 Scan" → **Run workflow** ▶️
   → ~5-10 min me 500 stocks ka real scan hokar JSON commit hoga.
6. Live dashboard: **`https://<USERNAME>.github.io/Multiverse-zone/`** 🎉
   (Mon–Fri 16:07 IST auto-scan chalta rahega.)

## 💻 Local chalana
```bash
pip install -r requirements.txt
python3 multiverse_scanner.py --demo     # offline demo data
# ya real:  python3 multiverse_scanner.py --top 50
python3 -m http.server 8000              # http://localhost:8000
python3 test_gtf_pdf_engine.py           # 51/51 PDF-rule checks
```

## 🧠 Dashboard kya dikhata hai
- **Zone table**: symbol, LTP, signal (curve/clock rules p28-32), 1D zone (pattern, score /8, entry type, strength), 1W/1M trend clock, curve band.
- **🔍 popup**: SVG candlestick chart pe zone boxes (proximal solid / distal dashed), ENTRY/SL/TGT 2:1 lines, 🟡leg-in 🔵base 🟣leg-out markers; EXCEPTIONAL LEGIN/LEGOUT badges; score breakdown; live Type-2/3 confirmation (p34-35); credibility; risk qty.
- **📖 Course tab**: 12 topics + score/entry tables. **🧮 Calculators**: risk (1/1.5/2%) + trade score.

⚠️ Educational tool — investment advice nahi. Past performance ≠ future guarantee.
