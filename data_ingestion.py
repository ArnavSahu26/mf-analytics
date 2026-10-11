"""Day 1: load all CSVs, profile them, explore fund_master, validate AMFI codes."""
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
REPORTS = Path("reports")

CONFIG = {
    "fund_master_file": "fund_master.csv",
    "nav_history_file": "nav_history.csv",
    "code_col": "scheme_code",
    "fund_house_col": "fund_house",
    "category_col": "category",
    "subcategory_col": "sub_category",
    "risk_col": "risk_grade",
}


def load_all():
    dfs = {}
    for f in sorted(RAW.glob("*.csv")):
        if f.name.startswith("live_nav"):
            continue
        dfs[f.stem] = pd.read_csv(f)
    return dfs


def profile(dfs):
    anomalies = []
    for name, df in dfs.items():
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        print("shape:", df.shape)
        print("\ndtypes:\n", df.dtypes)
        print("\nhead:\n", df.head())

        nulls = df.isna().sum()
        nulls = nulls[nulls > 0]
        if not nulls.empty:
            anomalies.append(f"{name}: nulls -> {nulls.to_dict()}")
        dups = int(df.duplicated().sum())
        if dups:
            anomalies.append(f"{name}: {dups} fully duplicated rows")
        for col in df.select_dtypes("object"):
            sample = df[col].dropna().head(50)
            if sample.empty:
                continue
            if pd.to_numeric(sample, errors="coerce").notna().all():
                anomalies.append(f"{name}.{col}: numeric stored as object")
            elif "date" in col.lower():
                anomalies.append(f"{name}.{col}: date stored as object")
    return anomalies


def explore_fund_master(fm):
    print(f"\n{'=' * 70}\nFUND MASTER EXPLORATION\n{'=' * 70}")
    print("columns:", list(fm.columns))
    for key in ("fund_house_col", "category_col", "subcategory_col", "risk_col"):
        col = CONFIG[key]
        if col in fm.columns:
            vals = sorted(fm[col].dropna().unique())
            print(f"\n{col} ({len(vals)} unique):")
            for v in vals:
                print("  -", v)
        else:
            print(f"\n[!] column '{col}' not found; update CONFIG")
    code = CONFIG["code_col"]
    if code in fm.columns:
        s = fm[code].astype(str)
        print(f"\nAMFI code: {s.nunique()} unique, length distribution:\n{s.str.len().value_counts().to_dict()}")
        print("range:", fm[code].min(), "->", fm[code].max())


def validate_codes(fm, nav):
    code = CONFIG["code_col"]
    fm_codes = set(fm[code].astype(str).str.strip())
    nav_codes = set(nav[code].astype(str).str.strip())
    missing = sorted(fm_codes - nav_codes)
    orphan = sorted(nav_codes - fm_codes)
    lines = [
        "# Day 1 Data Quality Summary",
        f"- fund_master codes: {len(fm_codes)} | nav_history codes: {len(nav_codes)}",
        f"- In fund_master but NOT in nav_history: {len(missing)} {missing[:20]}",
        f"- In nav_history but NOT in fund_master: {len(orphan)} {orphan[:20]}",
        f"- Duplicate codes in fund_master: {int(fm[code].duplicated().sum())}",
        "- Result: " + ("PASS" if not missing else "FAIL, see missing codes above"),
    ]
    return "\n".join(lines)


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    dfs = load_all()
    print(f"Loaded {len(dfs)} datasets: {list(dfs)}")
    anomalies = profile(dfs)

    fm = dfs.get(Path(CONFIG["fund_master_file"]).stem)
    nav = dfs.get(Path(CONFIG["nav_history_file"]).stem)
    if fm is None or nav is None:
        raise SystemExit("fund_master / nav_history not found; check CONFIG filenames")

    explore_fund_master(fm)
    summary = validate_codes(fm, nav)
    summary += "\n\n## Anomalies\n" + ("\n".join(f"- {a}" for a in anomalies) or "- none detected")
    print(f"\n{'=' * 70}\n{summary}")
    (REPORTS / "day1_data_quality.md").write_text(summary)
    print(f"\nSaved {REPORTS / 'day1_data_quality.md'}")


if __name__ == "__main__":
    main()
