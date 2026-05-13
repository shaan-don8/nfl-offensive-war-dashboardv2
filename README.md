# NFL Offensive WAR Dashboard

Streamlit dashboard for 2022–2025 NFL Offensive WAR.

## App structure

1. Overview
2. All WAR Team
3. QB WAR
4. Skill WAR
5. OL WAR

The app supports two repository layouts:

- CSVs in the repository root beside `app.py`
- CSVs inside a `data/` folder beside `app.py`

## Streamlit Cloud entry point

```text
app.py
```

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Included data files

- `offense_war_master_2022_2025_te_adjusted.csv`
- `skill_war_master_2022_2025_te_adjusted.csv`
- `skill_war_detail_2022_2025_te_adjusted.csv`
- `te_run_block_adjustments_2022_2025.csv`
- `qb_war_master_2022_2025.csv`
- `qb_war_detail_2022_2025.csv`
- `ol_war_master_2022_2025.csv`
- `ol_war_detail_2022_2025.csv`

## TE run-blocking adjustment

Eligible tight ends require at least 50 run-blocking snaps. The adjustment scales a percentile-based bump by run-blocking volume as a fraction of the season maximum tight end run-blocking workload.
