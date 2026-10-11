# Day 1 Data Quality Summary
- fund_master codes: 31 | nav_history codes: 30
- In fund_master but NOT in nav_history: 1 ['999001']
- In nav_history but NOT in fund_master: 0 []
- Duplicate codes in fund_master: 0
- Result: FAIL, see missing codes above

## Anomalies
- benchmark_index.date: date stored as object
- expense_ratio: 1 fully duplicated rows
- fund_master: nulls -> {'risk_grade': 2}
- fund_master.launch_date: date stored as object
- nav_history: nulls -> {'nav': 15}
- nav_history.date: date stored as object