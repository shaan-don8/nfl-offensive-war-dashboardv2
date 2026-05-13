# NFL Offensive WAR Dashboard

Streamlit dashboard for 2022-2025 offensive WAR with an added tight end run-blocking adjustment and dedicated QB, Skill, and OL detail views.

## Files

- `app.py`: Streamlit dashboard with overall leaderboard, unit detail tabs, TE run-blocking view, player lookup, team summary, and downloads
- `data/offense_war_master_2022_2025_te_adjusted.csv`: adjusted full offensive WAR file
- `data/skill_war_master_2022_2025_te_adjusted.csv`: adjusted skill WAR master file
- `data/skill_war_detail_2022_2025_te_adjusted.csv`: adjusted skill WAR detail file
- `data/qb_war_master_2022_2025.csv`: QB WAR master file
- `data/qb_war_detail_2022_2025.csv`: QB WAR detail file
- `data/ol_war_master_2022_2025.csv`: OL WAR master file
- `data/ol_war_detail_2022_2025.csv`: OL WAR detail file
- `data/te_run_block_adjustments_2022_2025.csv`: TE run-blocking adjustment table
- `update_te_war.py`: reproducible TE adjustment script

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Push this folder to GitHub, then point Streamlit Cloud at `app.py`.

## TE adjustment logic

A TE receives a run-blocking adjustment only if he has at least 50 run-blocking snaps. The adjustment uses PFF run-block grade percentile among eligible TEs within season and scales by volume:

```text
volume_factor = player TE run-block snaps / season max TE run-block snaps
TE block WAR adjustment = eligible_flag × percentile bump × volume_factor
```

Percentile bump table:

| TE run-block percentile | Base WAR bump |
|---:|---:|
| 90th+ | +0.30 |
| 80th-89th | +0.20 |
| 70th-79th | +0.12 |
| 60th-69th | +0.06 |
| 40th-59th | 0.00 |
| 25th-39th | -0.05 |
| below 25th | -0.10 |
