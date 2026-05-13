from pathlib import Path
from html import escape

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# Page setup
# ============================================================

st.set_page_config(
    page_title="NFL Offensive WAR Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_ROOT = Path(__file__).parent
SEARCH_DIRS = [APP_ROOT / "data", APP_ROOT]

FILE_NAMES = {
    "offense": "offense_war_master_2022_2025_te_adjusted.csv",
    "skill_master": "skill_war_master_2022_2025_te_adjusted.csv",
    "skill_detail": "skill_war_detail_2022_2025_te_adjusted.csv",
    "qb_master": "qb_war_master_2022_2025.csv",
    "qb_detail": "qb_war_detail_2022_2025.csv",
    "ol_master": "ol_war_master_2022_2025.csv",
    "ol_detail": "ol_war_detail_2022_2025.csv",
    "te_adj": "te_run_block_adjustments_2022_2025.csv",
}

CUSTOM_CSS = """
<style>
    :root {
        --bg-card: rgba(255,255,255,0.065);
        --bg-card-strong: rgba(255,255,255,0.095);
        --border-soft: rgba(255,255,255,0.13);
        --text-muted: rgba(245,249,255,0.78);
        --accent: #6FA8FF;
        --accent-2: #80F2C4;
        --text-main: #F8FBFF;
        --text-soft: rgba(245,249,255,0.86);
    }

    .block-container {
        padding-top: 1.15rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(64, 120, 255, 0.18), transparent 26%),
            radial-gradient(circle at 85% 0%, rgba(0, 200, 170, 0.12), transparent 28%),
            linear-gradient(180deg, #0E1117 0%, #111827 45%, #0B0F16 100%);
        color: var(--text-main);
    }

    .hero {
        border: 1px solid rgba(255,255,255,0.14);
        background:
            linear-gradient(135deg, rgba(255,255,255,0.105), rgba(255,255,255,0.035)),
            radial-gradient(circle at top right, rgba(111,168,255,0.24), transparent 33%);
        box-shadow: 0 24px 80px rgba(0,0,0,0.35);
        border-radius: 28px;
        padding: 1.45rem 1.6rem 1.35rem 1.6rem;
        margin-bottom: 1.15rem;
    }

    .hero-eyebrow {
        font-size: 0.78rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--accent-2) !important;
        font-weight: 700;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }

    .hero-title {
        font-size: clamp(2.0rem, 4vw, 3.6rem);
        line-height: 0.97;
        margin: 0;
        font-weight: 850;
        color: var(--text-main) !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }

    .hero-copy {
        margin-top: 0.8rem;
        color: var(--text-soft) !important;
        font-size: 1.02rem;
        max-width: 980px;
        line-height: 1.45;
        text-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 1rem;
    }

    .pill {
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.06);
        color: rgba(245,249,255,0.9) !important;
        border-radius: 999px;
        padding: 0.33rem 0.62rem;
        font-size: 0.82rem;
        text-shadow: 0 1px 4px rgba(0,0,0,0.25);
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(255,255,255,0.105), rgba(255,255,255,0.035));
        border: 1px solid rgba(255,255,255,0.14);
        padding: 0.78rem 0.88rem;
        border-radius: 18px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.22);
    }

    div[data-testid="stMetricValue"] {
        color: var(--text-main) !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }

    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetric"] label {
        color: rgba(245,249,255,0.78) !important;
    }

    .section-title {
        font-size: 1.45rem;
        line-height: 1.1;
        margin: 0.7rem 0 0.25rem 0;
        font-weight: 800;
        color: var(--text-main) !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }

    .section-copy {
        color: var(--text-muted) !important;
        font-size: 0.96rem;
        line-height: 1.45;
        margin-bottom: 0.8rem;
        text-shadow: 0 1px 4px rgba(0,0,0,0.22);
    }

    .method-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 0.85rem;
    }

    @media (max-width: 1000px) {
        .method-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    }

    .method-card, .note-card {
        border: 1px solid rgba(255,255,255,0.13);
        background: linear-gradient(145deg, rgba(255,255,255,0.085), rgba(255,255,255,0.032));
        border-radius: 22px;
        padding: 1rem;
        box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        min-height: 142px;
        color: var(--text-soft) !important;
    }

    .method-kicker, .card-kicker {
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent-2) !important;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .method-head {
        font-size: 1.05rem;
        color: var(--text-main) !important;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }

    .method-text {
        color: rgba(245,249,255,0.82) !important;
        font-size: 0.91rem;
        line-height: 1.4;
    }

    .roster-card {
        position: relative;
        border: 1px solid rgba(255,255,255,0.15);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04)),
            radial-gradient(circle at top left, rgba(111,168,255,0.22), transparent 45%);
        border-radius: 24px;
        padding: 1rem 1.05rem 0.9rem 1.05rem;
        box-shadow: 0 18px 46px rgba(0,0,0,0.26);
        min-height: 164px;
        overflow: hidden;
    }

    .roster-card:after {
        content: "";
        position: absolute;
        right: -42px;
        top: -52px;
        width: 130px;
        height: 130px;
        border-radius: 999px;
        background: rgba(128,242,196,0.12);
        filter: blur(1px);
    }

    .slot-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(5,10,20,0.42);
        border-radius: 999px;
        padding: 0.22rem 0.55rem;
        color: var(--accent-2) !important;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .roster-player {
        margin-top: 0.7rem;
        color: #FFFFFF !important;
        font-size: 1.27rem;
        font-weight: 850;
        line-height: 1.05;
        padding-right: 1.5rem;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }

    .roster-meta {
        margin-top: 0.25rem;
        color: rgba(245,249,255,0.76) !important;
        font-size: 0.9rem;
    }

    .roster-stat {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin-top: 0.9rem;
        border-top: 1px solid rgba(255,255,255,0.11);
        padding-top: 0.7rem;
    }

    .roster-stat span {
        color: rgba(245,249,255,0.72) !important;
        font-size: 0.78rem;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        font-weight: 800;
    }

    .roster-stat strong {
        color: #FFFFFF !important;
        font-size: 1.55rem;
        line-height: 1;
        text-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }

    .driver {
        margin-top: 0.58rem;
        color: rgba(245,249,255,0.8) !important;
        font-size: 0.82rem;
        line-height: 1.28;
    }

    .mini-divider {
        height: 1px;
        background: rgba(255,255,255,0.11);
        margin: 0.8rem 0 1rem 0;
    }

    .read-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1.05rem;
        margin-top: 0.85rem;
        margin-bottom: 1.05rem;
    }

    @media (max-width: 1000px) {
        .read-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    }

    .read-card {
        border: 1px solid rgba(255,255,255,0.13);
        background:
            linear-gradient(145deg, rgba(18,27,43,0.96), rgba(16,24,38,0.9)),
            radial-gradient(circle at top right, rgba(111,168,255,0.16), transparent 35%);
        border-radius: 22px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        min-height: 250px;
        color: var(--text-soft) !important;
    }

    .read-card h3 {
        color: #FFFFFF !important;
        font-size: 1.35rem;
        letter-spacing: 0.06em;
        margin: 0 0 0.85rem 0;
        font-weight: 850;
    }

    .read-card p {
        color: rgba(245,249,255,0.86) !important;
        font-size: 0.93rem;
        line-height: 1.46;
        margin: 0.58rem 0;
    }

    .read-card strong {
        color: #FFFFFF !important;
        font-weight: 850;
    }

    .threshold-caption {
        color: rgba(245,249,255,0.76) !important;
        font-size: 0.9rem;
        line-height: 1.38;
        margin: 0.1rem 0 0.75rem 0;
    }

    .dataframe th {
        background: rgba(255,255,255,0.08) !important;
    }

    .stTabs [data-baseweb="tab"] p {
        color: #EAF2FF !important;
        font-weight: 750 !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.10) !important;
        border-radius: 12px !important;
    }

    h1, h2, h3, h4, p, label, span {
        color: inherit;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# Helpers
# ============================================================


def resolve_file(filename: str) -> Path:
    for directory in SEARCH_DIRS:
        path = directory / filename
        if path.exists():
            return path
    searched = ", ".join(str(d) for d in SEARCH_DIRS)
    raise FileNotFoundError(f"{filename} not found. Searched: {searched}")


def fmt_num(x, decimals=2):
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x):,.{decimals}f}"
    except Exception:
        return "—"


def fmt_pct(x, decimals=1):
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x) * 100:,.{decimals}f}%"
    except Exception:
        return "—"


def safe_float(value, default=np.nan):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def coalesce_columns(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype="object")
    for col in cols:
        if col in df.columns:
            out = out.fillna(df[col])
    return out


def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def render_html_card(slot, player, team, role, war, rank_label, driver):
    safe = {
        "slot": escape(str(slot)),
        "player": escape(str(player)),
        "team": escape(str(team)),
        "role": escape(str(role)),
        "war": escape(fmt_num(war, 2)),
        "rank": escape(str(rank_label)),
        "driver": escape(str(driver)),
    }
    return f"""
    <div class="roster-card">
        <div class="slot-tag">{safe['slot']} · {safe['rank']}</div>
        <div class="roster-player">{safe['player']}</div>
        <div class="roster-meta">{safe['team']} · {safe['role']}</div>
        <div class="roster-stat"><span>WAR</span><strong>{safe['war']}</strong></div>
        <div class="driver">{safe['driver']}</div>
    </div>
    """


def render_method_card(kicker, head, text):
    return f"""
    <div class="method-card">
        <div class="method-kicker">{escape(kicker)}</div>
        <div class="method-head">{escape(head)}</div>
        <div class="method-text">{escape(text)}</div>
    </div>
    """


def plot_bar(df, x, y, color=None, title="", x_title="WAR", height_per_row=28):
    if df.empty:
        st.info("No rows match the current filters.")
        return
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        color=color,
        title=title,
        hover_data=[c for c in df.columns if c in ["season", "team", "team_display", "final_epa", "total_epa", "success_rate", "epa_per_play", "epa_per_opportunity"]],
    )
    fig.update_layout(
        height=max(420, height_per_row * len(df)),
        yaxis_title="",
        xaxis_title=x_title,
        margin=dict(l=10, r=10, t=52, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.88)"),
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.03)")
    st.plotly_chart(fig, use_container_width=True)


def styled_dataframe(df, **kwargs):
    st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


# ============================================================
# Data loading
# ============================================================

@st.cache_data
def load_data():
    data = {key: pd.read_csv(resolve_file(filename)) for key, filename in FILE_NAMES.items()}

    for df in data.values():
        if "season" in df.columns:
            df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")

    offense = data["offense"]
    offense = ensure_numeric(
        offense,
        [
            "final_war", "final_epa", "raw_war", "raw_epa", "volume", "efficiency", "success_rate",
            "final_war_pre_te_block_adj", "final_epa_pre_te_block_adj", "te_run_block_war_adjustment",
            "te_run_block_epa_adjustment", "grades_run_block", "snap_counts_run_block",
            "te_run_block_grade_percentile", "te_run_block_volume_factor",
        ],
    )
    if "final_war_pre_te_block_adj" not in offense.columns:
        offense["final_war_pre_te_block_adj"] = offense["final_war"]
    if "final_epa_pre_te_block_adj" not in offense.columns:
        offense["final_epa_pre_te_block_adj"] = offense["final_epa"]
    if "te_run_block_war_adjustment" not in offense.columns:
        offense["te_run_block_war_adjustment"] = 0.0
    if "is_te_pff_match" not in offense.columns:
        offense["is_te_pff_match"] = False

    offense["display_position"] = np.where(
        offense["is_te_pff_match"].fillna(False).astype(bool),
        "TE",
        offense["position_group"].fillna(offense["unit"]),
    )
    offense["player_team"] = offense["player_name"].astype(str) + " — " + offense["team"].astype(str)
    offense["te_adjusted_label"] = np.where(
        offense["te_run_block_war_adjustment"].fillna(0).abs() > 0,
        "TE run-block adjusted",
        "Base WAR",
    )
    data["offense"] = offense

    qb_detail = data["qb_detail"]
    qb_detail = ensure_numeric(
        qb_detail,
        ["passing_epa", "pass_plays", "sacks", "interceptions", "scramble_epa", "scrambles", "total_epa", "total_plays", "war", "epa_per_play", "success_rate", "qualified_war_rank"],
    )
    qb_detail["team_display"] = coalesce_columns(qb_detail, ["team", "primary_team", "teams"])
    qb_detail["player_team"] = qb_detail["player_name"].astype(str) + " — " + qb_detail["team_display"].astype(str)
    qb_detail["position_rank"] = qb_detail.groupby("season")["war"].rank(method="first", ascending=False).astype("Int64")
    data["qb_detail"] = qb_detail

    skill_detail = data["skill_detail"]
    skill_detail = ensure_numeric(
        skill_detail,
        [
            "receiving_epa", "targets", "receptions", "receiving_yards", "air_epa", "yac_epa",
            "rushing_epa", "carries", "rushing_yards", "total_epa", "opportunities", "touches", "war",
            "epa_per_opportunity", "epa_per_touch", "success_rate", "role_adjusted_skill_war",
            "role_adjusted_skill_epa", "te_run_block_war_adjustment", "grades_run_block", "snap_counts_run_block",
            "te_run_block_grade_percentile", "te_run_block_volume_factor",
        ],
    )
    skill_detail["team_display"] = coalesce_columns(skill_detail, ["team", "primary_team", "teams"])
    skill_detail["player_team"] = skill_detail["player_name"].astype(str) + " — " + skill_detail["team_display"].astype(str)

    # TE is identified by the PFF TE run-blocking match. This gives TE its own filter
    # and All WAR Team slot while preserving the broader Pass Catcher framework.
    skill_detail["is_te_role"] = (
        skill_detail.get("is_te_pff_match", pd.Series(False, index=skill_detail.index))
        .fillna(False)
        .astype(bool)
    )
    skill_detail["skill_role_display"] = np.where(
        skill_detail["is_te_role"],
        "TE",
        skill_detail["position_group"],
    )
    skill_detail["position_rank"] = (
        skill_detail.groupby(["season", "skill_role_display"])["role_adjusted_skill_war"]
        .rank(method="first", ascending=False)
        .astype("Int64")
    )
    data["skill_detail"] = skill_detail

    ol_detail = data["ol_detail"]
    ol_detail = ensure_numeric(
        ol_detail,
        [
            "ol_war_v5", "ol_total_epa_v5", "final_ol_war", "final_ol_epa", "snap_counts_offense",
            "snap_counts_pass_block", "snap_counts_run_block", "grades_offense", "grades_pass_block",
            "grades_run_block", "pressures_allowed", "sacks_allowed", "penalties",
        ],
    )
    ol_detail["team_display"] = coalesce_columns(ol_detail, ["team", "team_name"])
    ol_detail["player_name"] = ol_detail["player"].astype(str)
    ol_detail["player_team"] = ol_detail["player_name"].astype(str) + " — " + ol_detail["team_display"].astype(str)
    ol_detail["display_ol_war"] = coalesce_columns(ol_detail, ["final_ol_war", "ol_war_v5"]).astype(float)
    ol_detail["display_ol_epa"] = coalesce_columns(ol_detail, ["final_ol_epa", "ol_total_epa_v5"]).astype(float)
    ol_detail["position_rank"] = (
        ol_detail.groupby(["season", "position"])["display_ol_war"]
        .rank(method="first", ascending=False)
        .astype("Int64")
    )
    data["ol_detail"] = ol_detail

    te_adj = data["te_adj"]
    te_adj = ensure_numeric(
        te_adj,
        ["grades_run_block", "snap_counts_run_block", "te_run_block_grade_percentile", "te_run_block_volume_factor", "te_run_block_war_adjustment", "te_run_block_epa_adjustment"],
    )
    data["te_adj"] = te_adj

    return data


try:
    data = load_data()
except FileNotFoundError as e:
    st.error(f"Missing data file: {e}")
    st.stop()


offense = data["offense"]
qb_detail = data["qb_detail"]
skill_detail = data["skill_detail"]
ol_detail = data["ol_detail"]
te_adj = data["te_adj"]

available_seasons = sorted([int(x) for x in offense["season"].dropna().unique()], reverse=True)
available_teams = sorted([x for x in offense["team"].dropna().unique()])

with st.sidebar:
    st.markdown("### Dashboard Controls")
    selected_seasons = st.multiselect("Season filter", available_seasons, default=[available_seasons[0]])
    selected_teams = st.multiselect("Team filter", available_teams, default=[])
    top_n = st.slider("Leaderboard size", min_value=5, max_value=50, value=15, step=5)
    st.divider()
    st.markdown(
        "<div class='section-copy'>All WAR Team uses its own single-season selector so the roster card always represents one season.</div>",
        unsafe_allow_html=True,
    )


def apply_common_filters(df, seasons=None, teams=None, team_col="team"):
    out = df.copy()
    if seasons:
        out = out[out["season"].isin(seasons)]
    if teams and team_col in out.columns:
        out = out[out[team_col].isin(teams)]
    return out


filtered_offense = apply_common_filters(offense, selected_seasons, selected_teams, "team")

INTERPRETATION_THRESHOLDS = pd.DataFrame(
    [
        {"Group": "QB", "WAR Range": "4.0+", "Interpretation": "MVP-caliber QB season"},
        {"Group": "QB", "WAR Range": "3.0–4.0", "Interpretation": "Elite QB season"},
        {"Group": "QB", "WAR Range": "2.0–3.0", "Interpretation": "Strong top-tier starter"},
        {"Group": "QB", "WAR Range": "1.0–2.0", "Interpretation": "Above-average starter"},
        {"Group": "Skill", "WAR Range": "2.0+", "Interpretation": "Elite skill production"},
        {"Group": "Skill", "WAR Range": "1.5–2.0", "Interpretation": "All-Pro caliber skill season"},
        {"Group": "Skill", "WAR Range": "1.0–1.5", "Interpretation": "High-end starter / primary weapon"},
        {"Group": "Skill", "WAR Range": "0.5–1.0", "Interpretation": "Strong contributor above role replacement"},
        {"Group": "OL", "WAR Range": "1.2+", "Interpretation": "Elite offensive line season"},
        {"Group": "OL", "WAR Range": "0.8–1.2", "Interpretation": "High-end starter"},
        {"Group": "OL", "WAR Range": "0.4–0.8", "Interpretation": "Good starter"},
        {"Group": "OL", "WAR Range": "0.0–0.4", "Interpretation": "Above replacement / solid contributor"},
    ]
)

# ============================================================
# Hero
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">Offensive Value Model · 2022–2025</div>
        <h1 class="hero-title">NFL Offensive WAR Dashboard</h1>
        <div class="hero-copy">
            Position-specific offensive value across quarterback play, skill production, and offensive line performance — now with a capped tight end run-blocking adjustment to better credit complete Y tight ends without overvaluing blocking-only profiles.
        </div>
        <div class="pill-row">
            <span class="pill">QB WAR</span>
            <span class="pill">Role-adjusted Skill WAR</span>
            <span class="pill">OL WAR</span>
            <span class="pill">TE run-block adjustment</span>
            <span class="pill">All WAR Team output</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick KPI ribbon
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Rows", f"{len(filtered_offense):,}")
with k2:
    st.metric("Total WAR", fmt_num(filtered_offense["final_war"].sum(), 2))
with k3:
    st.metric("QB WAR", fmt_num(filtered_offense.loc[filtered_offense["unit"].eq("QB"), "final_war"].sum(), 2))
with k4:
    st.metric("Skill WAR", fmt_num(filtered_offense.loc[filtered_offense["unit"].eq("Skill"), "final_war"].sum(), 2))
with k5:
    st.metric("OL WAR", fmt_num(filtered_offense.loc[filtered_offense["unit"].eq("OL"), "final_war"].sum(), 2))

# ============================================================
# All WAR Team builders
# ============================================================


def qb_driver(row):
    passing = safe_float(row.get("passing_epa", np.nan), 0)
    scramble = safe_float(row.get("scramble_epa", np.nan), 0)
    if scramble >= 0.20 * max(abs(passing), 1):
        return "Passing EPA + scramble value"
    return "Passing EPA"


def skill_driver(row):
    pos = str(row.get("skill_role_display", row.get("position_group", "")))
    rec = safe_float(row.get("receiving_epa", np.nan), 0)
    rush = safe_float(row.get("rushing_epa", np.nan), 0)

    if pos == "RB":
        if rec > rush:
            return "Receiving value + backfield usage"
        return "Role-adjusted rushing/receiving value"

    if abs(row.get("yac_epa", 0)) > abs(row.get("air_epa", 0)):
        return "Receiving EPA + YAC value"

    return "Receiving EPA"


def te_driver(row):
    te_adj_val = safe_float(row.get("te_run_block_war_adjustment", np.nan), 0)
    if te_adj_val > 0:
        return "Receiving EPA + TE run-block credit"
    return "Receiving EPA"


def ol_driver(row):
    pass_grade = safe_float(row.get("grades_pass_block", np.nan), np.nan)
    run_grade = safe_float(row.get("grades_run_block", np.nan), np.nan)
    if not pd.isna(run_grade) and not pd.isna(pass_grade) and run_grade > pass_grade + 5:
        return "PFF grade value + run blocking"
    return "PFF grade value + pass protection"


def add_roster_row(rows, slot, row, role, war_col, rank_prefix, rank_value, driver):
    if row is None or row.empty:
        rows.append(
            {
                "Slot": slot,
                "Player": "—",
                "Team": "—",
                "Position / Role": role,
                "WAR": np.nan,
                "Rank Within Position": "—",
                "Primary Value Driver": "No qualifying player",
            }
        )
        return

    series = row.iloc[0]
    rows.append(
        {
            "Slot": slot,
            "Player": series.get("player_name", series.get("player", "—")),
            "Team": series.get("team_display", series.get("team", "—")),
            "Position / Role": role,
            "WAR": safe_float(series.get(war_col, np.nan)),
            "Rank Within Position": f"{rank_prefix}{int(rank_value)}" if not pd.isna(rank_value) else rank_prefix,
            "Primary Value Driver": driver(series),
        }
    )


def build_all_war_team(season: int) -> pd.DataFrame:
    rows = []

    qbs = qb_detail[qb_detail["season"].eq(season)].sort_values("war", ascending=False)
    add_roster_row(rows, "QB", qbs.head(1), "QB", "war", "QB", 1, qb_driver)

    season_skill = skill_detail[skill_detail["season"].eq(season)].copy()
    te_mask = (
        season_skill.get("is_te_role", pd.Series(False, index=season_skill.index))
        .fillna(False)
        .astype(bool)
    )

    rbs = (
        season_skill[
            season_skill["skill_role_display"].eq("RB")
            & (~te_mask)
        ]
        .sort_values("role_adjusted_skill_war", ascending=False)
    )

    pcs = (
        season_skill[
            season_skill["skill_role_display"].eq("Pass Catcher")
            & (~te_mask)
        ]
        .sort_values("role_adjusted_skill_war", ascending=False)
    )

    tes = (
        season_skill[te_mask]
        .sort_values("role_adjusted_skill_war", ascending=False)
    )

    for i in range(2):
        add_roster_row(
            rows,
            f"RB{i+1}",
            rbs.iloc[[i]] if len(rbs) > i else pd.DataFrame(),
            "RB",
            "role_adjusted_skill_war",
            "RB",
            i + 1,
            skill_driver,
        )

    for i in range(3):
        add_roster_row(
            rows,
            f"PC{i+1}",
            pcs.iloc[[i]] if len(pcs) > i else pd.DataFrame(),
            "Pass Catcher",
            "role_adjusted_skill_war",
            "PC",
            i + 1,
            skill_driver,
        )

    add_roster_row(
        rows,
        "TE",
        tes.head(1),
        "TE",
        "role_adjusted_skill_war",
        "TE",
        1,
        te_driver,
    )

    season_ol = ol_detail[ol_detail["season"].eq(season)].copy()
    centers = season_ol[season_ol["position"].eq("C")].sort_values("display_ol_war", ascending=False)
    guards = season_ol[season_ol["position"].eq("G")].sort_values("display_ol_war", ascending=False)
    tackles = season_ol[season_ol["position"].eq("T")].sort_values("display_ol_war", ascending=False)

    add_roster_row(rows, "C", centers.head(1), "C", "display_ol_war", "C", 1, ol_driver)
    for i in range(2):
        add_roster_row(rows, f"G{i+1}", guards.iloc[[i]] if len(guards) > i else pd.DataFrame(), "G", "display_ol_war", "G", i + 1, ol_driver)
    for i in range(2):
        add_roster_row(rows, f"T{i+1}", tackles.iloc[[i]] if len(tackles) > i else pd.DataFrame(), "T", "display_ol_war", "T", i + 1, ol_driver)

    return pd.DataFrame(rows)


# ============================================================
# Tabs
# ============================================================

overview_tab, all_war_tab, qb_tab, skill_tab, ol_tab = st.tabs(
    ["Overview", "All WAR Team", "QB WAR", "Skill WAR", "OL WAR"]
)

with overview_tab:
    st.markdown("<div class='section-title'>Overview / Methodology</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-copy'>The app is built to make the framework legible quickly: explain the model, show the All WAR Team payoff, then let users drill into QB, skill, and OL leaderboards.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-title'>How to read this dashboard</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="read-grid">
            <div class="read-card">
                <h3>QB WAR</h3>
                <p><strong>What it captures:</strong> direct quarterback value on passing/dropback plays and scrambles.</p>
                <p><strong>Formula:</strong> passing/dropback EPA + scramble EPA, divided by 45 EPA per win.</p>
                <p><strong>Best use:</strong> comparing quarterback production across seasons and understanding how much value came from passing versus rushing creation.</p>
            </div>
            <div class="read-card">
                <h3>Skill WAR</h3>
                <p><strong>What it captures:</strong> receiving and non-QB rushing production above role-specific replacement.</p>
                <p><strong>Formula:</strong> raw EPA production adjusted against the 25th percentile replacement baseline within RB, Pass Catcher, and TE roles.</p>
                <p><strong>Best use:</strong> comparing RBs to RBs, pass catchers to pass catchers, and identifying role-adjusted skill value.</p>
            </div>
            <div class="read-card">
                <h3>OL WAR</h3>
                <p><strong>What it captures:</strong> a blend of team offensive context, individual PFF blocking grades, negative events, and position-specific replacement value.</p>
                <p><strong>Formula:</strong> allocated pass/rush EPA + grade value - negative events + position adjustment.</p>
                <p><strong>Best use:</strong> evaluating offensive line value without treating OL production as purely team passing output.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-title'>Production thresholds</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='threshold-caption'>These ranges are intended as practical interpretation bands, not hard scouting grades. QB, skill, and OL WAR should primarily be read within their own value buckets.</div>",
        unsafe_allow_html=True,
    )
    styled_dataframe(
        INTERPRETATION_THRESHOLDS,
        column_config={
            "Group": st.column_config.TextColumn("Group"),
            "WAR Range": st.column_config.TextColumn("WAR Range"),
            "Interpretation": st.column_config.TextColumn("Interpretation"),
        },
    )

    st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(render_method_card("Layer 1", "Separate value engines", "Quarterbacks, skill players, and offensive linemen are evaluated with unit-specific value models instead of forcing one generic offensive box-score formula."), unsafe_allow_html=True)
    with m2:
        st.markdown(render_method_card("Layer 2", "Role-adjusted skill value", "Running backs and pass catchers are valued against their own opportunity structures, with receiving/rushing EPA translated into role-adjusted WAR."), unsafe_allow_html=True)
    with m3:
        st.markdown(render_method_card("Layer 3", "TE blocking correction", "Tight ends receive a capped run-blocking adjustment using PFF run-block percentile and run-blocking volume share, with a 50-snap minimum."), unsafe_allow_html=True)

    st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85])
    with left:
        unit_summary = (
            filtered_offense.groupby("unit", as_index=False)
            .agg(players=("player_name", "nunique"), war=("final_war", "sum"), epa=("final_epa", "sum"))
            .sort_values("war", ascending=True)
        )
        plot_bar(unit_summary, "war", "unit", color="unit", title="Filtered WAR by offensive unit", x_title="WAR", height_per_row=90)

    with right:
        st.markdown("<div class='note-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-kicker'>TE Adjustment</div>", unsafe_allow_html=True)
        st.markdown(
            """
            The tight end correction is intentionally narrow:

            `eligible = run-block snaps >= 50`  
            `volume = TE run-block snaps / season max TE run-block snaps`  
            `adjustment = percentile bump × volume`

            The purpose is to credit complete tight ends while preserving receiving value as the primary separator.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Top offensive WAR leaders</div>", unsafe_allow_html=True)
    top_overview = filtered_offense.sort_values("final_war", ascending=False).head(top_n).copy()
    plot_bar(top_overview.sort_values("final_war"), "final_war", "player_team", color="unit", title="Top players in current filters", x_title="Adjusted Offensive WAR")
    styled_dataframe(
        top_overview[
            [
                "season",
                "overall_offense_war_rank",
                "player_name",
                "team",
                "unit",
                "display_position",
                "final_war",
                "final_epa",
                "volume",
                "success_rate",
            ]
        ],
        column_config={
            "final_war": st.column_config.NumberColumn("WAR", format="%.3f"),
            "final_epa": st.column_config.NumberColumn("EPA", format="%.1f"),
            "success_rate": st.column_config.NumberColumn("Success", format="%.1%"),
        },
    )

with all_war_tab:
    st.markdown("<div class='section-title'>All WAR Team</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-copy'>A single-season roster card: one QB, two RBs, three pass catchers, one tight end, one center, two guards, and two tackles. This gives the model a clean, memorable output while keeping the positional logic visible.</div>",
        unsafe_allow_html=True,
    )

    season_for_team = st.radio("Select season", available_seasons, horizontal=True, index=0)
    all_team = build_all_war_team(int(season_for_team))

    st.markdown(f"<div class='section-title'>{int(season_for_team)} All WAR Team</div>", unsafe_allow_html=True)

    # QB row
    qb_row = all_team[all_team["Slot"].eq("QB")]
    if not qb_row.empty:
        st.markdown(render_html_card(**{
            "slot": qb_row.iloc[0]["Slot"],
            "player": qb_row.iloc[0]["Player"],
            "team": qb_row.iloc[0]["Team"],
            "role": qb_row.iloc[0]["Position / Role"],
            "war": qb_row.iloc[0]["WAR"],
            "rank_label": qb_row.iloc[0]["Rank Within Position"],
            "driver": qb_row.iloc[0]["Primary Value Driver"],
        }), unsafe_allow_html=True)

    st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)

    # RBs
    rb_rows = all_team[all_team["Slot"].isin(["RB1", "RB2"])].reset_index(drop=True)
    rb_cols = st.columns(2)
    for idx, col in enumerate(rb_cols):
        if idx < len(rb_rows):
            row = rb_rows.iloc[idx]
            with col:
                st.markdown(render_html_card(row["Slot"], row["Player"], row["Team"], row["Position / Role"], row["WAR"], row["Rank Within Position"], row["Primary Value Driver"]), unsafe_allow_html=True)

    st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)

    # Pass catchers
    pc_rows = all_team[all_team["Slot"].isin(["PC1", "PC2", "PC3"])].reset_index(drop=True)
    pc_cols = st.columns(3)
    for idx, col in enumerate(pc_cols):
        if idx < len(pc_rows):
            row = pc_rows.iloc[idx]
            with col:
                st.markdown(render_html_card(row["Slot"], row["Player"], row["Team"], row["Position / Role"], row["WAR"], row["Rank Within Position"], row["Primary Value Driver"]), unsafe_allow_html=True)

    st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)

    # TE card, centered for cleaner presentation
    te_row = all_team[all_team["Slot"].eq("TE")].reset_index(drop=True)
    if not te_row.empty:
        te_cols = st.columns([1, 1.25, 1])
        with te_cols[1]:
            row = te_row.iloc[0]
            st.markdown(
                render_html_card(
                    row["Slot"],
                    row["Player"],
                    row["Team"],
                    row["Position / Role"],
                    row["WAR"],
                    row["Rank Within Position"],
                    row["Primary Value Driver"],
                ),
                unsafe_allow_html=True,
            )

    st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)

    # OL row: C + guards + tackles
    ol_rows = all_team[all_team["Slot"].isin(["C", "G1", "G2", "T1", "T2"])].reset_index(drop=True)
    ol_cols = st.columns(5)
    for idx, col in enumerate(ol_cols):
        if idx < len(ol_rows):
            row = ol_rows.iloc[idx]
            with col:
                st.markdown(render_html_card(row["Slot"], row["Player"], row["Team"], row["Position / Role"], row["WAR"], row["Rank Within Position"], row["Primary Value Driver"]), unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Full All WAR Team table</div>", unsafe_allow_html=True)
    styled_dataframe(
        all_team,
        column_config={"WAR": st.column_config.NumberColumn("WAR", format="%.3f")},
    )
    st.download_button(
        "Download All WAR Team CSV",
        data=all_team.to_csv(index=False).encode("utf-8"),
        file_name=f"all_war_team_{int(season_for_team)}.csv",
        mime="text/csv",
    )

with qb_tab:
    st.markdown("<div class='section-title'>QB WAR</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-copy'>Quarterback value combines passing EPA with scramble contribution, translated to WAR over the selected seasons.</div>", unsafe_allow_html=True)

    qd = apply_common_filters(qb_detail, selected_seasons, selected_teams, "team_display")
    qd = qd.sort_values("war", ascending=False).head(top_n)

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("QB rows", f"{len(qd):,}")
    with q2:
        st.metric("Total QB WAR", fmt_num(qd["war"].sum(), 2))
    with q3:
        st.metric("Best QB WAR", fmt_num(qd["war"].max(), 2))
    with q4:
        st.metric("Avg EPA/play", fmt_num(qd["epa_per_play"].mean(), 3))

    plot_bar(qd.sort_values("war"), "war", "player_team", color="season", title="QB WAR leaderboard", x_title="QB WAR")

    if not qd.empty:
        fig = px.scatter(
            qd,
            x="passing_epa",
            y="scramble_epa",
            size="war",
            color="season",
            hover_name="player_name",
            hover_data=["team_display", "war", "epa_per_play", "success_rate", "sacks", "interceptions"],
            title="Passing EPA vs scramble value",
        )
        fig.update_layout(
            height=480,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(255,255,255,0.88)"),
        )
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
        st.plotly_chart(fig, use_container_width=True)

    qb_cols = ["season", "position_rank", "player_name", "team_display", "war", "total_epa", "passing_epa", "scramble_epa", "total_plays", "epa_per_play", "success_rate", "sacks", "interceptions"]
    styled_dataframe(
        qd[[c for c in qb_cols if c in qd.columns]],
        column_config={
            "war": st.column_config.NumberColumn("QB WAR", format="%.3f"),
            "total_epa": st.column_config.NumberColumn("Total EPA", format="%.1f"),
            "passing_epa": st.column_config.NumberColumn("Passing EPA", format="%.1f"),
            "scramble_epa": st.column_config.NumberColumn("Scramble EPA", format="%.1f"),
            "epa_per_play": st.column_config.NumberColumn("EPA/Play", format="%.3f"),
            "success_rate": st.column_config.NumberColumn("Success", format="%.1%"),
        },
    )

with skill_tab:
    st.markdown("<div class='section-title'>Skill WAR</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-copy'>Running backs, pass catchers, and tight ends are shown through role-adjusted skill WAR. Tight ends retain receiving value while receiving a capped run-blocking correction when eligible.</div>", unsafe_allow_html=True)

    sd = apply_common_filters(skill_detail, selected_seasons, selected_teams, "team_display")
    skill_role_options = sorted(sd["skill_role_display"].dropna().unique())

    role_filter = st.multiselect(
        "Skill role",
        skill_role_options,
        default=skill_role_options,
    )

    if role_filter:
        sd = sd[sd["skill_role_display"].isin(role_filter)]

    sd = sd.sort_values("role_adjusted_skill_war", ascending=False).head(top_n)

    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.metric("Skill rows", f"{len(sd):,}")
    with s2:
        st.metric("Skill WAR", fmt_num(sd["role_adjusted_skill_war"].sum(), 2))
    with s3:
        st.metric("Receiving EPA", fmt_num(sd["receiving_epa"].sum(), 1))
    with s4:
        st.metric("Rushing EPA", fmt_num(sd["rushing_epa"].sum(), 1))
    with s5:
        st.metric("TE block WAR", fmt_num(sd["te_run_block_war_adjustment"].sum(), 3))

    plot_bar(sd.sort_values("role_adjusted_skill_war"), "role_adjusted_skill_war", "player_team", color="skill_role_display", title="Skill WAR leaderboard", x_title="Role-adjusted Skill WAR")

    if not sd.empty:
        fig = px.scatter(
            sd,
            x="receiving_epa",
            y="rushing_epa",
            size="role_adjusted_skill_war",
            color="skill_role_display",
            hover_name="player_name",
            hover_data=["season", "team_display", "targets", "carries", "success_rate", "te_run_block_war_adjustment"],
            title="Receiving vs rushing value",
        )
        fig.update_layout(height=480, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="rgba(255,255,255,0.88)"))
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
        st.plotly_chart(fig, use_container_width=True)

    skill_cols = [
        "season", "position_rank", "player_name", "skill_role_display", "team_display", "role_adjusted_skill_war",
        "role_adjusted_skill_epa", "receiving_epa", "rushing_epa", "opportunities", "targets", "carries",
        "epa_per_opportunity", "success_rate", "te_run_block_war_adjustment", "grades_run_block", "snap_counts_run_block",
    ]
    styled_dataframe(
        sd[[c for c in skill_cols if c in sd.columns]],
        column_config={
            "skill_role_display": st.column_config.TextColumn("Skill Role"),
            "role_adjusted_skill_war": st.column_config.NumberColumn("Skill WAR", format="%.3f"),
            "role_adjusted_skill_epa": st.column_config.NumberColumn("Skill EPA", format="%.1f"),
            "receiving_epa": st.column_config.NumberColumn("Receiving EPA", format="%.1f"),
            "rushing_epa": st.column_config.NumberColumn("Rushing EPA", format="%.1f"),
            "epa_per_opportunity": st.column_config.NumberColumn("EPA/Opp", format="%.3f"),
            "success_rate": st.column_config.NumberColumn("Success", format="%.1%"),
            "te_run_block_war_adjustment": st.column_config.NumberColumn("TE Block WAR", format="%.3f"),
            "grades_run_block": st.column_config.NumberColumn("PFF Run-Block Grade", format="%.1f"),
        },
    )

with ol_tab:
    st.markdown("<div class='section-title'>OL WAR</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-copy'>Offensive line value combines PFF grade value, pass protection, run blocking, penalties, and negative events into OL WAR.</div>", unsafe_allow_html=True)

    od = apply_common_filters(ol_detail, selected_seasons, selected_teams, "team_display")
    ol_pos_filter = st.multiselect("OL position", sorted(od["position"].dropna().unique()), default=sorted(od["position"].dropna().unique()))
    if ol_pos_filter:
        od = od[od["position"].isin(ol_pos_filter)]
    od = od.sort_values("display_ol_war", ascending=False).head(top_n)

    o1, o2, o3, o4, o5 = st.columns(5)
    with o1:
        st.metric("OL rows", f"{len(od):,}")
    with o2:
        st.metric("OL WAR", fmt_num(od["display_ol_war"].sum(), 2))
    with o3:
        st.metric("Best OL WAR", fmt_num(od["display_ol_war"].max(), 2))
    with o4:
        st.metric("Avg pass grade", fmt_num(od["grades_pass_block"].mean(), 1))
    with o5:
        st.metric("Avg run grade", fmt_num(od["grades_run_block"].mean(), 1))

    plot_bar(od.sort_values("display_ol_war"), "display_ol_war", "player_team", color="position", title="OL WAR leaderboard", x_title="OL WAR")

    if not od.empty:
        fig = px.scatter(
            od,
            x="grades_pass_block",
            y="grades_run_block",
            size="display_ol_war",
            color="position",
            hover_name="player_name",
            hover_data=["season", "team_display", "display_ol_war", "snap_counts_offense", "pressures_allowed", "sacks_allowed", "penalties"],
            title="Pass-block grade vs run-block grade",
        )
        fig.update_layout(height=480, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="rgba(255,255,255,0.88)"))
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
        st.plotly_chart(fig, use_container_width=True)

    ol_cols = [
        "season", "position_rank", "player_name", "team_display", "position", "display_ol_war", "display_ol_epa",
        "snap_counts_offense", "snap_counts_pass_block", "snap_counts_run_block", "grades_offense", "grades_pass_block",
        "grades_run_block", "pressures_allowed", "sacks_allowed", "penalties",
    ]
    styled_dataframe(
        od[[c for c in ol_cols if c in od.columns]],
        column_config={
            "display_ol_war": st.column_config.NumberColumn("OL WAR", format="%.3f"),
            "display_ol_epa": st.column_config.NumberColumn("OL EPA", format="%.1f"),
            "grades_offense": st.column_config.NumberColumn("Offense Grade", format="%.1f"),
            "grades_pass_block": st.column_config.NumberColumn("Pass Grade", format="%.1f"),
            "grades_run_block": st.column_config.NumberColumn("Run Grade", format="%.1f"),
        },
    )

st.markdown("<div class='mini-divider'></div>", unsafe_allow_html=True)
with st.expander("Downloads"):
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.download_button("Offense master", data["offense"].to_csv(index=False).encode("utf-8"), FILE_NAMES["offense"], "text/csv")
        st.download_button("QB detail", data["qb_detail"].to_csv(index=False).encode("utf-8"), FILE_NAMES["qb_detail"], "text/csv")
    with d2:
        st.download_button("Skill master", data["skill_master"].to_csv(index=False).encode("utf-8"), FILE_NAMES["skill_master"], "text/csv")
        st.download_button("Skill detail", data["skill_detail"].to_csv(index=False).encode("utf-8"), FILE_NAMES["skill_detail"], "text/csv")
    with d3:
        st.download_button("OL master", data["ol_master"].to_csv(index=False).encode("utf-8"), FILE_NAMES["ol_master"], "text/csv")
        st.download_button("OL detail", data["ol_detail"].to_csv(index=False).encode("utf-8"), FILE_NAMES["ol_detail"], "text/csv")
    with d4:
        st.download_button("QB master", data["qb_master"].to_csv(index=False).encode("utf-8"), FILE_NAMES["qb_master"], "text/csv")
        st.download_button("TE adjustments", data["te_adj"].to_csv(index=False).encode("utf-8"), FILE_NAMES["te_adj"], "text/csv")
