"""
Rebuilds adjusted offensive WAR files with the TE run-blocking adjustment.

Expected folder structure:

nfl_war_te_streamlit_app/
  update_te_war.py
  data/
    raw/
      offense_run_blockng.csv
      offense_run_blockng (1).csv
      offense_run_blockng (2).csv
      offense_run_blockng (3).csv
      skill_war_master_2022_2025.csv
      skill_war_detail_2022_2025.csv
      offense_war_master_2022_2025.csv
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

RUN_BLOCK_FILES = {
    2022: RAW_DIR / "offense_run_blockng (3).csv",
    2023: RAW_DIR / "offense_run_blockng (2).csv",
    2024: RAW_DIR / "offense_run_blockng (1).csv",
    2025: RAW_DIR / "offense_run_blockng.csv",
}

SKILL_MASTER_PATH = RAW_DIR / "skill_war_master_2022_2025.csv"
SKILL_DETAIL_PATH = RAW_DIR / "skill_war_detail_2022_2025.csv"
OFFENSE_MASTER_PATH = RAW_DIR / "offense_war_master_2022_2025.csv"

MIN_TE_RUN_BLOCK_SNAPS = 50
EPA_PER_WIN = 45.0

TEAM_MAP = {
    "ARZ": "ARI",
    "BLT": "BAL",
    "CLV": "CLE",
    "HST": "HOU",
    "JAX": "JAC",
    "LA": "LA",
    "LAR": "LA",
    "OAK": "LV",
    "SD": "LAC",
    "SL": "LA",
    "WSH": "WAS",
}

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def clean_token(x):
    return re.sub(r"[^a-z0-9]", "", str(x).lower())


def split_full_name(full_name):
    parts = str(full_name).replace(".", "").replace("'", "").split()
    parts = [p for p in parts if clean_token(p) not in SUFFIXES]
    if not parts:
        return "", ""
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else parts[0]
    return first, last


def pff_name_key(player):
    first, last = split_full_name(player)
    return clean_token(first)[:1] + "_" + clean_token(last)


def war_name_key(player_name):
    s = str(player_name)
    if "." in s:
        prefix, last = s.split(".", 1)
        return clean_token(prefix)[:1] + "_" + clean_token(last)
    return clean_token(s)


def normalize_team(team):
    if pd.isna(team):
        return team
    return TEAM_MAP.get(str(team), str(team))


def base_te_run_block_bump(percentile):
    if pd.isna(percentile):
        return 0.0
    if percentile >= 0.90:
        return 0.30
    if percentile >= 0.80:
        return 0.20
    if percentile >= 0.70:
        return 0.12
    if percentile >= 0.60:
        return 0.06
    if percentile >= 0.40:
        return 0.00
    if percentile >= 0.25:
        return -0.05
    return -0.10


def main():
    DATA_DIR.mkdir(exist_ok=True)

    missing = [p for p in list(RUN_BLOCK_FILES.values()) + [SKILL_MASTER_PATH, SKILL_DETAIL_PATH, OFFENSE_MASTER_PATH] if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required raw files:\n" + "\n".join(str(p) for p in missing))

    pff_parts = []
    for season, path in RUN_BLOCK_FILES.items():
        temp = pd.read_csv(path)
        temp["season"] = season
        temp["source_run_block_file"] = path.name
        pff_parts.append(temp)

    pff = pd.concat(pff_parts, ignore_index=True)
    pff["team_norm"] = pff["team_name"].apply(normalize_team)
    pff["name_key"] = pff["player"].apply(pff_name_key)

    te = pff[pff["position"].eq("TE")].copy()
    te["eligible_te_run_block"] = te["snap_counts_run_block"] >= MIN_TE_RUN_BLOCK_SNAPS
    te["te_run_block_grade_percentile"] = np.nan

    eligible = te["eligible_te_run_block"]
    te.loc[eligible, "te_run_block_grade_percentile"] = (
        te.loc[eligible]
        .groupby("season")["grades_run_block"]
        .rank(pct=True, method="average")
    )

    te["season_max_te_run_block_snaps"] = te.groupby("season")["snap_counts_run_block"].transform("max")
    te["te_run_block_volume_factor"] = (te["snap_counts_run_block"] / te["season_max_te_run_block_snaps"]).clip(0, 1)
    te.loc[~te["eligible_te_run_block"], "te_run_block_volume_factor"] = 0.0

    te["te_run_block_base_war_bump"] = te["te_run_block_grade_percentile"].apply(base_te_run_block_bump)
    te.loc[~te["eligible_te_run_block"], "te_run_block_base_war_bump"] = 0.0

    te["te_run_block_war_adjustment"] = te["te_run_block_base_war_bump"] * te["te_run_block_volume_factor"]
    te["te_run_block_epa_adjustment"] = te["te_run_block_war_adjustment"] * EPA_PER_WIN

    te_adjustments = te[
        [
            "season",
            "player",
            "player_id",
            "name_key",
            "team_norm",
            "team_name",
            "grades_run_block",
            "snap_counts_run_block",
            "season_max_te_run_block_snaps",
            "eligible_te_run_block",
            "te_run_block_grade_percentile",
            "te_run_block_volume_factor",
            "te_run_block_base_war_bump",
            "te_run_block_war_adjustment",
            "te_run_block_epa_adjustment",
            "source_run_block_file",
        ]
    ].copy()

    te_adjustments = (
        te_adjustments
        .sort_values(["season", "team_norm", "name_key", "snap_counts_run_block"], ascending=[True, True, True, False])
        .drop_duplicates(["season", "team_norm", "name_key"], keep="first")
    )

    merge_cols = [
        "season",
        "team_norm",
        "name_key",
        "player",
        "grades_run_block",
        "snap_counts_run_block",
        "season_max_te_run_block_snaps",
        "eligible_te_run_block",
        "te_run_block_grade_percentile",
        "te_run_block_volume_factor",
        "te_run_block_base_war_bump",
        "te_run_block_war_adjustment",
        "te_run_block_epa_adjustment",
    ]

    skill = pd.read_csv(SKILL_MASTER_PATH)
    skill["team_norm"] = skill["team"].apply(normalize_team)
    skill["name_key"] = skill["player_name"].apply(war_name_key)
    skill_adj = skill.merge(te_adjustments[merge_cols], on=["season", "team_norm", "name_key"], how="left")
    skill_adj = skill_adj.rename(columns={"player": "pff_player_name"})

    for col in ["te_run_block_war_adjustment", "te_run_block_epa_adjustment", "te_run_block_volume_factor", "te_run_block_base_war_bump"]:
        skill_adj[col] = skill_adj[col].fillna(0.0)

    skill_adj["is_te_pff_match"] = skill_adj["pff_player_name"].notna()
    skill_adj["final_war_pre_te_block_adj"] = skill_adj["final_war"]
    skill_adj["final_epa_pre_te_block_adj"] = skill_adj["final_epa"]
    skill_adj["final_war"] = skill_adj["final_war_pre_te_block_adj"] + skill_adj["te_run_block_war_adjustment"]
    skill_adj["final_epa"] = skill_adj["final_epa_pre_te_block_adj"] + skill_adj["te_run_block_epa_adjustment"]
    skill_adj["rank"] = skill_adj.groupby("season")["final_war"].rank(method="min", ascending=False).astype(int)
    skill_adj = skill_adj.drop(columns=["team_norm", "name_key"])

    skill_detail = pd.read_csv(SKILL_DETAIL_PATH)
    team_source = skill_detail["team"].where(skill_detail["team"].notna(), skill_detail["primary_team"])
    skill_detail["team_norm"] = team_source.apply(normalize_team)
    skill_detail["name_key"] = skill_detail["player_name"].apply(war_name_key)
    skill_detail_adj = skill_detail.merge(te_adjustments[merge_cols], on=["season", "team_norm", "name_key"], how="left")
    skill_detail_adj = skill_detail_adj.rename(columns={"player": "pff_player_name"})

    for col in ["te_run_block_war_adjustment", "te_run_block_epa_adjustment", "te_run_block_volume_factor", "te_run_block_base_war_bump"]:
        skill_detail_adj[col] = skill_detail_adj[col].fillna(0.0)

    skill_detail_adj["is_te_pff_match"] = skill_detail_adj["pff_player_name"].notna()
    skill_detail_adj["role_adjusted_skill_war_pre_te_block_adj"] = skill_detail_adj["role_adjusted_skill_war"]
    skill_detail_adj["role_adjusted_skill_epa_pre_te_block_adj"] = skill_detail_adj["role_adjusted_skill_epa"]
    skill_detail_adj["role_adjusted_skill_war"] = skill_detail_adj["role_adjusted_skill_war_pre_te_block_adj"] + skill_detail_adj["te_run_block_war_adjustment"]
    skill_detail_adj["role_adjusted_skill_epa"] = skill_detail_adj["role_adjusted_skill_epa_pre_te_block_adj"] + skill_detail_adj["te_run_block_epa_adjustment"]
    skill_detail_adj["war_pre_te_block_adj"] = skill_detail_adj["war"]
    skill_detail_adj["total_epa_pre_te_block_adj"] = skill_detail_adj["total_epa"]
    skill_detail_adj["war"] = skill_detail_adj["war_pre_te_block_adj"] + skill_detail_adj["te_run_block_war_adjustment"]
    skill_detail_adj["total_epa"] = skill_detail_adj["total_epa_pre_te_block_adj"] + skill_detail_adj["te_run_block_epa_adjustment"]
    skill_detail_adj["role_adjusted_skill_war_rank"] = skill_detail_adj.groupby("season")["role_adjusted_skill_war"].rank(method="min", ascending=False).astype(int)
    skill_detail_adj = skill_detail_adj.drop(columns=["team_norm", "name_key"])

    offense = pd.read_csv(OFFENSE_MASTER_PATH)
    offense["team_norm"] = offense["team"].apply(normalize_team)
    offense["name_key"] = offense["player_name"].apply(war_name_key)
    offense_adj = offense.merge(te_adjustments[merge_cols], on=["season", "team_norm", "name_key"], how="left")
    offense_adj = offense_adj.rename(columns={"player": "pff_player_name"})

    for col in ["te_run_block_war_adjustment", "te_run_block_epa_adjustment", "te_run_block_volume_factor", "te_run_block_base_war_bump"]:
        offense_adj[col] = offense_adj[col].fillna(0.0)

    offense_adj["is_te_pff_match"] = offense_adj["pff_player_name"].notna()
    apply_te_adj = offense_adj["unit"].eq("Skill") & offense_adj["is_te_pff_match"]
    offense_adj["final_war_pre_te_block_adj"] = offense_adj["final_war"]
    offense_adj["final_epa_pre_te_block_adj"] = offense_adj["final_epa"]
    offense_adj.loc[apply_te_adj, "final_war"] = offense_adj.loc[apply_te_adj, "final_war_pre_te_block_adj"] + offense_adj.loc[apply_te_adj, "te_run_block_war_adjustment"]
    offense_adj.loc[apply_te_adj, "final_epa"] = offense_adj.loc[apply_te_adj, "final_epa_pre_te_block_adj"] + offense_adj.loc[apply_te_adj, "te_run_block_epa_adjustment"]
    offense_adj.loc[~apply_te_adj, ["te_run_block_war_adjustment", "te_run_block_epa_adjustment"]] = 0.0
    offense_adj["overall_offense_war_rank"] = offense_adj.groupby("season")["final_war"].rank(method="min", ascending=False).astype(int)
    offense_adj["unit_war_rank"] = offense_adj.groupby(["season", "unit"])["final_war"].rank(method="min", ascending=False).astype(int)
    offense_adj["rank"] = offense_adj["unit_war_rank"]
    offense_adj = offense_adj.drop(columns=["team_norm", "name_key"])

    te_adjustments.to_csv(DATA_DIR / "te_run_block_adjustments_2022_2025.csv", index=False)
    skill_adj.to_csv(DATA_DIR / "skill_war_master_2022_2025_te_adjusted.csv", index=False)
    skill_detail_adj.to_csv(DATA_DIR / "skill_war_detail_2022_2025_te_adjusted.csv", index=False)
    offense_adj.to_csv(DATA_DIR / "offense_war_master_2022_2025_te_adjusted.csv", index=False)

    print("Saved adjusted files to:", DATA_DIR)
    print("Offense rows:", len(offense_adj))
    print("Skill rows:", len(skill_adj))
    print("TE adjustment rows:", len(te_adjustments))
    print("Matched TE rows in offense file:", int((offense_adj["unit"].eq("Skill") & offense_adj["is_te_pff_match"]).sum()))
    print("Total TE block WAR adjustment:", round(float(offense_adj["te_run_block_war_adjustment"].sum()), 3))


if __name__ == "__main__":
    main()
