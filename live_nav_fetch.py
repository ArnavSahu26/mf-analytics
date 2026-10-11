"""Fetch live NAV history from mfapi.in and save as raw CSVs."""
import time
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")
BASE = "https://api.mfapi.in/mf/{}"

SCHEMES = {
    119018: "HDFC Large Cap Direct",
    119598: "SBI Large Cap Direct",
    120586: "ICICI Pru Large Cap Direct",
    118632: "Nippon Large Cap Direct",
    120465: "Axis Large Cap Direct",
    120152: "Kotak Large Cap Direct",
}


def fetch_nav(code: int, retries: int = 3) -> pd.DataFrame:
    for attempt in range(retries):
        try:
            r = requests.get(BASE.format(code), timeout=30)
            r.raise_for_status()
            payload = r.json()
            break
        except requests.RequestException as e:
            print(f"  [{code}] attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"Failed to fetch scheme {code}")

    meta = payload.get("meta", {})
    df = pd.DataFrame(payload.get("data", []))
    if df.empty:
        raise ValueError(f"No NAV data for {code}")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    df.insert(0, "scheme_code", code)
    df.insert(1, "scheme_name", meta.get("scheme_name", SCHEMES.get(code)))
    df.insert(2, "fund_house", meta.get("fund_house"))
    return df


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    frames = []
    for code, label in SCHEMES.items():
        print(f"Fetching {code} ({label})...")
        df = fetch_nav(code)
        out = RAW / f"live_nav_{code}.csv"
        df.to_csv(out, index=False)
        print(f"  saved {out} | rows={len(df)} | {df['date'].min().date()} -> {df['date'].max().date()}")
        frames.append(df)
        time.sleep(0.5)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(RAW / "live_nav_all.csv", index=False)
    print(f"\nCombined: {combined.shape} -> {RAW / 'live_nav_all.csv'}")


if __name__ == "__main__":
    main()
