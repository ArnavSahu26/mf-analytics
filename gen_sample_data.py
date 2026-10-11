"""Generate 10 sample CSVs into data/raw/ so data_ingestion.py can be tested.

Run from the project root:  python gen_sample_data.py
Uses real NAVs for the 6 live-fetched schemes (if live_nav_<code>.csv exist),
synthetic NAVs for the rest. Includes a few deliberate anomalies.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

REAL = {
    119018: ("HDFC Large Cap Fund - Direct Plan - Growth", "HDFC Mutual Fund"),
    119598: ("SBI Large Cap Fund - Direct Plan - Growth", "SBI Mutual Fund"),
    120586: ("ICICI Prudential Large Cap Fund - Direct Plan - Growth", "ICICI Prudential Mutual Fund"),
    118632: ("Nippon India Large Cap Fund - Direct Plan - Growth", "Nippon India Mutual Fund"),
    120465: ("Axis Large Cap Fund - Direct Plan - Growth", "Axis Mutual Fund"),
    120152: ("Kotak Large Cap Fund - Direct Plan - Growth", "Kotak Mahindra Mutual Fund"),
}
HOUSES = ["HDFC Mutual Fund", "SBI Mutual Fund", "ICICI Prudential Mutual Fund", "Nippon India Mutual Fund",
          "Axis Mutual Fund", "Kotak Mahindra Mutual Fund", "Mirae Asset Mutual Fund", "UTI Mutual Fund"]
CATS = {
    "Equity": [("Large Cap", "Very High"), ("Mid Cap", "Very High"), ("Small Cap", "Very High"), ("Flexi Cap", "Very High")],
    "Debt": [("Liquid", "Low"), ("Corporate Bond", "Moderate"), ("Gilt", "Moderate")],
    "Hybrid": [("Aggressive Hybrid", "Very High"), ("Balanced Advantage", "High")],
}

# ---- 1. fund_master ----
rows = []
for code, (name, house) in REAL.items():
    rows.append(dict(scheme_code=code, scheme_name=name, fund_house=house, category="Equity",
                     sub_category="Large Cap", risk_grade="Very High", plan="Direct", option="Growth",
                     launch_date="2013-01-01"))
code = 100001
while len(rows) < 30:
    cat = rng.choice(list(CATS))
    sub, risk = CATS[cat][rng.integers(len(CATS[cat]))]
    house = HOUSES[rng.integers(len(HOUSES))]
    rows.append(dict(scheme_code=code, scheme_name=f"{house.replace(' Mutual Fund', '')} {sub} Fund - Direct Plan - Growth",
                     fund_house=house, category=cat, sub_category=sub, risk_grade=risk, plan="Direct",
                     option="Growth", launch_date=str(pd.Timestamp("2014-01-01") + pd.Timedelta(days=int(rng.integers(0, 2500))))[:10]))
    code += 1
# anomalies: a code with no NAV history, and missing risk grades
rows.append(dict(scheme_code=999001, scheme_name="Sample Delisted Fund - Direct Plan - Growth", fund_house="UTI Mutual Fund",
                 category="Equity", sub_category="Mid Cap", risk_grade="Very High", plan="Direct", option="Growth",
                 launch_date="2015-06-01"))
fm = pd.DataFrame(rows)
fm.loc[[3, 17], "risk_grade"] = np.nan
fm.to_csv(RAW / "fund_master.csv", index=False)

# ---- 2. nav_history ----
dates = pd.bdate_range("2020-01-01", "2026-10-09")
frames = []
for c in fm["scheme_code"]:
    if c == 999001:
        continue
    f = RAW / f"live_nav_{c}.csv"
    if c in REAL and f.exists():
        d = pd.read_csv(f, parse_dates=["date"])
        d = d[d["date"] >= "2020-01-01"][["scheme_code", "date", "nav"]]
    else:
        r = rng.normal(0.0004, 0.01, len(dates))
        d = pd.DataFrame({"scheme_code": c, "date": dates, "nav": 20 * np.exp(np.cumsum(r)).round(4)})
    frames.append(d)
nav = pd.concat(frames, ignore_index=True)
nav["date"] = nav["date"].dt.strftime("%Y-%m-%d")
nav.loc[nav.sample(15, random_state=1).index, "nav"] = np.nan  # anomaly: missing NAVs
nav.to_csv(RAW / "nav_history.csv", index=False)

codes = [c for c in fm["scheme_code"] if c != 999001]
months = pd.date_range("2022-01-31", "2026-09-30", freq="ME")

# ---- 3. aum_monthly ----
pd.DataFrame([dict(scheme_code=c, month=m.strftime("%Y-%m-%d"), aum_cr=round(float(rng.uniform(500, 40000)), 2))
              for c in codes for m in months]).to_csv(RAW / "aum_monthly.csv", index=False)

# ---- 4. expense_ratio (with a duplicate row) ----
er = pd.DataFrame({"scheme_code": codes, "expense_ratio_pct": rng.uniform(0.2, 1.2, len(codes)).round(2),
                   "exit_load_pct": rng.choice([0, 0.25, 0.5, 1.0], len(codes))})
pd.concat([er, er.iloc[[0]]]).to_csv(RAW / "expense_ratio.csv", index=False)

# ---- 5. fund_manager ----
mgrs = ["A. Sharma", "R. Iyer", "S. Mehta", "K. Nair", "P. Gupta", "V. Rao"]
pd.DataFrame({"scheme_code": codes, "manager_name": rng.choice(mgrs, len(codes)),
              "tenure_years": rng.uniform(1, 12, len(codes)).round(1)}).to_csv(RAW / "fund_manager.csv", index=False)

# ---- 6. benchmark_index ----
idx = pd.bdate_range("2020-01-01", "2026-10-09")
pd.DataFrame({"date": idx.strftime("%Y-%m-%d"), "index_name": "NIFTY 100 TRI",
              "value": (10000 * np.exp(np.cumsum(rng.normal(0.0004, 0.009, len(idx))))).round(2)}
             ).to_csv(RAW / "benchmark_index.csv", index=False)

# ---- 7. sip_flows ----
pd.DataFrame({"month": months.strftime("%Y-%m-%d"), "sip_inflow_cr": np.linspace(11000, 29000, len(months)).round(0),
              "sip_accounts_mn": np.linspace(50, 95, len(months)).round(1)}).to_csv(RAW / "sip_flows.csv", index=False)

# ---- 8. category_returns ----
pd.DataFrame([dict(category=cat, sub_category=s, period=p, avg_return_pct=round(float(rng.uniform(4, 22)), 2))
              for cat, subs in CATS.items() for s, _ in subs for p in ["1Y", "3Y", "5Y"]]
             ).to_csv(RAW / "category_returns.csv", index=False)

# ---- 9. portfolio_holdings ----
stocks = ["HDFC Bank", "ICICI Bank", "Reliance", "Infosys", "TCS", "L&T", "ITC", "Bharti Airtel", "SBI", "Axis Bank"]
pd.DataFrame([dict(scheme_code=c, stock=s, weight_pct=round(float(w), 2))
              for c in codes[:12] for s, w in zip(stocks, rng.dirichlet(np.ones(10)) * 90)]
             ).to_csv(RAW / "portfolio_holdings.csv", index=False)

# ---- 10. investor_folio_stats ----
pd.DataFrame({"scheme_code": codes, "folios_lakh": rng.uniform(1, 90, len(codes)).round(2),
              "avg_ticket_size": rng.integers(5000, 150000, len(codes))}).to_csv(RAW / "investor_folio_stats.csv", index=False)

print("Generated:")
for f in sorted(RAW.glob("*.csv")):
    if not f.name.startswith("live_nav"):
        print(" ", f.name)
