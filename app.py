from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="NFL Offensive WAR Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

OFFENSE_PATH = DATA_DIR / "offense_war_master_2022_2025_te_adjusted.csv"
SKILL_MASTER_PATH = DATA_DIR / "skill_war_master_2022_2025_te_adjusted.csv"
SKILL_DETAIL_PATH = DATA_DIR / "skill_war_detail_2022_2025_te_adjusted.csv"
QB_MASTER_PATH = DATA_DIR / "qb_war_master_2022_2025.csv"
QB_DETAIL_PATH = DATA_DIR / "qb_war_detail_2022_2025.csv"
OL_MASTER_PATH = DATA_DIR / "ol_war_master_2022_2025.csv"
OL_DETAIL_PATH = DATA_DIR / "ol_war_detail_2022_2025.csv"
TE_ADJ_PATH = DATA_DIR / "te_run_block_adjustments_2022_2025.csv"

CUSTOM_CSS = """
<style>
    .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: rgba(250, 250, 250, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.22);
        padding: 0.75rem 0.9rem;
        border-radius: 1rem;
    }
    .small-note {
        color: #7A7A7A;
        font-size: 0.92rem;
        line-height: 1.35;
    }
    .method-box {
        border: 1px solid rgba(128, 128, 128, 0.24);
        border-radius: 1rem;
        padding: 1rem 1.1rem;
        background: rgba(250, 250, 250, 0.03);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def fmt_num(x, decimals=2):
    if pd.isna(x):
        return "—"
    return f"{x:,.{decimals}f}"


def coalesce_columns(df, cols):
    out = pd.Series(np.nan, index=df.index, dtype="object")
    for col in cols:
        if col in df.columns:
            out = out.fillna(df[col])
    return out


@st.cache_data
def load_data():
    offense = pd.read_csv(OFFENSE_PATH)
    skill_master = pd.read_csv(SKILL_MASTER_PATH)
    skill_detail = pd.read_csv(SKILL_DETAIL_PATH)
    qb_master = pd.read_csv(QB_MASTER_PATH)
    qb_detail = pd.read_csv(QB_DETAIL_PATH)
    ol_master = pd.read_csv(OL_MASTER_PATH)
    ol_detail = pd.read_csv(OL_DETAIL_PATH)
    te_adj = pd.read_csv(TE_ADJ_PATH)

    frames = [offense, skill_master, skill_detail, qb_master, qb_detail, ol_master, ol_detail, te_adj]
    for df in frames:
        if "season" in df.columns:
            df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")

    # Master offense file is the primary leaderboard surface.
    offense["display_position"] = np.where(
        offense.get("is_te_pff_match", pd.Series(False, index=offense.index)).fillna(False),
        "TE",
        offense["position_group"].fillna(offense["unit"]),
    )
    offense["te_adjusted_label"] = np.where(
        offense.get("te_run_block_war_adjustment", pd.Series(0, index=offense.index)).fillna(0).abs() > 0,
        "TE adjusted",
        "No TE block adjustment",
    )
    offense["player_team"] = offense["player_name"].astype(str) + " — " + offense["team"].astype(str)
    offense["war_delta_pct"] = np.where(
        offense["final_war_pre_te_block_adj"].abs() > 0,
        offense["te_run_block_war_adjustment"] / offense["final_war_pre_te_block_adj"].abs(),
        np.nan,
    )

    # Detail file display helpers.
    qb_detail["team_display"] = coalesce_columns(qb_detail, ["team", "primary_team", "teams"])
    qb_detail["player_team"] = qb_detail["player_name"].astype(str) + " — " + qb_detail["team_display"].astype(str)

    ol_detail["team_display"] = coalesce_columns(ol_detail, ["team", "team_name"])
    ol_detail["player_name"] = ol_detail["player"].astype(str)
    ol_detail["player_team"] = ol_detail["player_name"].astype(str) + " — " + ol_detail["team_display"].astype(str)
    ol_detail["display_ol_war"] = coalesce_columns(ol_detail, ["final_ol_war", "ol_war_v5"]).astype(float)
    ol_detail["display_ol_epa"] = coalesce_columns(ol_detail, ["final_ol_epa", "ol_total_epa_v5"]).astype(float)

    skill_detail["team_display"] = coalesce_columns(skill_detail, ["team", "primary_team", "teams"])
    skill_detail["player_team"] = skill_detail["player_name"].astype(str) + " — " + skill_detail["team_display"].astype(str)

    te_adj["te_run_block_grade_percentile_display"] = te_adj["te_run_block_grade_percentile"] * 100
    te_adj["te_run_block_volume_factor_display"] = te_adj["te_run_block_volume_factor"] * 100

    return {
        "offense": offense,
        "skill_master": skill_master,
        "skill_detail": skill_detail,
        "qb_master": qb_master,
        "qb_detail": qb_detail,
        "ol_master": ol_master,
        "ol_detail": ol_detail,
        "te_adj": te_adj,
    }


def filter_offense(df, seasons, units, teams, positions, min_volume):
    out = df.copy()
    if seasons:
        out = out[out["season"].isin(seasons)]
    if units:
        out = out[out["unit"].isin(units)]
    if teams:
        out = out[out["team"].isin(teams)]
    if positions:
        out = out[out["display_position"].isin(positions)]
    if min_volume > 0 and "volume" in out.columns:
        out = out[out["volume"].fillna(0) >= min_volume]
    return out


def leaderboard_table(df):
    cols = [
        "season",
        "overall_offense_war_rank",
        "unit_war_rank",
        "player_name",
        "team",
        "unit",
        "display_position",
        "final_war",
        "final_war_pre_te_block_adj",
        "te_run_block_war_adjustment",
        "final_epa",
        "volume",
        "efficiency",
        "success_rate",
        "pff_player_name",
        "grades_run_block",
        "snap_counts_run_block",
        "te_run_block_grade_percentile",
        "te_run_block_volume_factor",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def standard_master_table(df):
    cols = [
        "season",
        "rank",
        "player_name",
        "team",
        "unit",
        "position_group",
        "final_war",
        "final_epa",
        "raw_war",
        "raw_epa",
        "volume",
        "efficiency",
        "success_rate",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def render_download_button(label, df, filename):
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


try:
    data = load_data()
except FileNotFoundError as e:
    st.error(f"Missing data file: {e}")
    st.stop()

offense = data["offense"]
skill_detail = data["skill_detail"]
qb_detail = data["qb_detail"]
ol_detail = data["ol_detail"]
te_adj = data["te_adj"]

st.title("NFL Offensive WAR Dashboard")
st.caption("2022–2025 offensive WAR with TE run-blocking adjustment, plus QB/Skill/OL detail tables")

with st.sidebar:
    st.header("Filters")
    available_seasons = sorted(offense["season"].dropna().unique(), reverse=True)
    seasons = st.multiselect("Season", available_seasons, default=[available_seasons[0]])

    available_units = sorted(offense["unit"].dropna().unique())
    units = st.multiselect("Unit", available_units, default=available_units)

    available_positions = sorted(offense["display_position"].dropna().unique())
    positions = st.multiselect("Position group", available_positions, default=available_positions)

    available_teams = sorted(offense["team"].dropna().unique())
    teams = st.multiselect("Team", available_teams, default=[])

    st.divider()
    top_n = st.slider("Top N", min_value=5, max_value=75, value=20, step=5)
    min_volume = st.number_input("Minimum volume", min_value=0, value=0, step=10)

filtered = filter_offense(offense, seasons, units, teams, positions, min_volume)

# KPI row
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("Players", f"{len(filtered):,}")
with c2:
    st.metric("Total WAR", fmt_num(filtered["final_war"].sum(), 2))
with c3:
    st.metric("Top WAR", fmt_num(filtered["final_war"].max(), 2))
with c4:
    st.metric("QB WAR", fmt_num(filtered.loc[filtered["unit"].eq("QB"), "final_war"].sum(), 2))
with c5:
    st.metric("Skill WAR", fmt_num(filtered.loc[filtered["unit"].eq("Skill"), "final_war"].sum(), 2))
with c6:
    st.metric("OL WAR", fmt_num(filtered.loc[filtered["unit"].eq("OL"), "final_war"].sum(), 2))

leaderboard_tab, unit_tab, te_tab, player_tab, team_tab, methodology_tab = st.tabs(
    [
        "Overall Leaderboard",
        "Unit Detail",
        "TE Run Blocking",
        "Player Lookup",
        "Team Summary",
        "Methodology + Downloads",
    ]
)

with leaderboard_tab:
    st.subheader("Offensive WAR leaderboard")
    search = st.text_input("Search player", placeholder="Example: Mahomes, Kittle, Jefferson, Kelce")
    board = filtered.copy()
    if search:
        board = board[board["player_name"].str.contains(search, case=False, na=False)]

    board = board.sort_values("final_war", ascending=False).head(top_n)

    chart_df = board.sort_values("final_war", ascending=True)
    if not chart_df.empty:
        fig = px.bar(
            chart_df,
            x="final_war",
            y="player_team",
            orientation="h",
            color="unit",
            hover_data=[
                c
                for c in [
                    "season",
                    "team",
                    "final_epa",
                    "efficiency",
                    "success_rate",
                    "te_run_block_war_adjustment",
                ]
                if c in chart_df.columns
            ],
            title=f"Top {len(chart_df)} by adjusted offensive WAR",
        )
        fig.update_layout(height=max(420, 26 * len(chart_df)), yaxis_title="", xaxis_title="Adjusted WAR")
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        leaderboard_table(board),
        use_container_width=True,
        hide_index=True,
        column_config={
            "final_war": st.column_config.NumberColumn("Adjusted WAR", format="%.3f"),
            "final_war_pre_te_block_adj": st.column_config.NumberColumn("Pre-TE Block WAR", format="%.3f"),
            "te_run_block_war_adjustment": st.column_config.NumberColumn("TE Block WAR Adj.", format="%.3f"),
            "final_epa": st.column_config.NumberColumn("Adjusted EPA", format="%.1f"),
            "efficiency": st.column_config.NumberColumn("EPA / Volume", format="%.3f"),
            "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1%"),
            "te_run_block_grade_percentile": st.column_config.NumberColumn("TE Block Grade %ile", format="%.1%"),
            "te_run_block_volume_factor": st.column_config.NumberColumn("TE Block Volume Factor", format="%.1%"),
        },
    )

with unit_tab:
    st.subheader("QB, skill, and offensive line detail")
    selected_unit_detail = st.radio("Detail view", ["QB", "Skill", "OL"], horizontal=True)

    if selected_unit_detail == "QB":
        qd = qb_detail.copy()
        if seasons:
            qd = qd[qd["season"].isin(seasons)]
        if teams:
            qd = qd[qd["team_display"].isin(teams)]
        qd = qd.sort_values("war", ascending=False).head(top_n)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("QB rows", f"{len(qd):,}")
        with d2:
            st.metric("Total QB WAR", fmt_num(qd["war"].sum(), 2))
        with d3:
            st.metric("Best QB WAR", fmt_num(qd["war"].max(), 2))
        with d4:
            st.metric("Avg EPA/play", fmt_num(qd["epa_per_play"].mean(), 3))

        if not qd.empty:
            fig = px.bar(
                qd.sort_values("war"),
                x="war",
                y="player_team",
                orientation="h",
                hover_data=["season", "passing_epa", "scramble_epa", "pass_plays", "scrambles", "success_rate"],
                title="QB WAR detail",
            )
            fig.update_layout(height=max(420, 26 * len(qd)), yaxis_title="", xaxis_title="WAR")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            qd[
                [
                    "season",
                    "qualified_war_rank",
                    "player_name",
                    "team_display",
                    "war",
                    "total_epa",
                    "passing_epa",
                    "scramble_epa",
                    "total_plays",
                    "epa_per_play",
                    "success_rate",
                    "sacks",
                    "interceptions",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "war": st.column_config.NumberColumn("WAR", format="%.3f"),
                "total_epa": st.column_config.NumberColumn("Total EPA", format="%.1f"),
                "passing_epa": st.column_config.NumberColumn("Passing EPA", format="%.1f"),
                "scramble_epa": st.column_config.NumberColumn("Scramble EPA", format="%.1f"),
                "epa_per_play": st.column_config.NumberColumn("EPA/Play", format="%.3f"),
                "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1%"),
            },
        )

    elif selected_unit_detail == "Skill":
        sd = skill_detail.copy()
        if seasons:
            sd = sd[sd["season"].isin(seasons)]
        if teams:
            sd = sd[sd["team_display"].isin(teams)]
        sd = sd.sort_values("role_adjusted_skill_war", ascending=False).head(top_n)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Skill rows", f"{len(sd):,}")
        with d2:
            st.metric("Total Skill WAR", fmt_num(sd["role_adjusted_skill_war"].sum(), 2))
        with d3:
            st.metric("Receiving EPA", fmt_num(sd["receiving_epa"].sum(), 1))
        with d4:
            st.metric("Rushing EPA", fmt_num(sd["rushing_epa"].sum(), 1))

        if not sd.empty:
            fig = px.bar(
                sd.sort_values("role_adjusted_skill_war"),
                x="role_adjusted_skill_war",
                y="player_team",
                orientation="h",
                color="position_group",
                hover_data=["season", "receiving_epa", "rushing_epa", "targets", "carries", "success_rate", "te_run_block_war_adjustment"],
                title="Skill WAR detail",
            )
            fig.update_layout(height=max(420, 26 * len(sd)), yaxis_title="", xaxis_title="Role-adjusted Skill WAR")
            st.plotly_chart(fig, use_container_width=True)

        cols = [
            "season",
            "role_adjusted_skill_war_rank",
            "player_name",
            "position_group",
            "team_display",
            "role_adjusted_skill_war",
            "role_adjusted_skill_war_pre_te_block_adj",
            "te_run_block_war_adjustment",
            "role_adjusted_skill_epa",
            "receiving_epa",
            "rushing_epa",
            "opportunities",
            "epa_per_opportunity",
            "success_rate",
        ]
        st.dataframe(
            sd[[c for c in cols if c in sd.columns]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "role_adjusted_skill_war": st.column_config.NumberColumn("Adjusted Skill WAR", format="%.3f"),
                "role_adjusted_skill_war_pre_te_block_adj": st.column_config.NumberColumn("Pre-TE Block Skill WAR", format="%.3f"),
                "te_run_block_war_adjustment": st.column_config.NumberColumn("TE Block WAR Adj.", format="%.3f"),
                "role_adjusted_skill_epa": st.column_config.NumberColumn("Adjusted Skill EPA", format="%.1f"),
                "epa_per_opportunity": st.column_config.NumberColumn("EPA/Opp", format="%.3f"),
                "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1%"),
            },
        )

    else:
        od = ol_detail.copy()
        if seasons:
            od = od[od["season"].isin(seasons)]
        if teams:
            od = od[od["team_display"].isin(teams)]
        war_col = "display_ol_war"
        epa_col = "display_ol_epa"
        od = od.sort_values(war_col, ascending=False).head(top_n)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("OL rows", f"{len(od):,}")
        with d2:
            st.metric("Total OL WAR", fmt_num(od[war_col].sum(), 2))
        with d3:
            st.metric("Best OL WAR", fmt_num(od[war_col].max(), 2))
        with d4:
            st.metric("Avg offense grade", fmt_num(od["grades_offense"].mean(), 1))

        if not od.empty:
            fig = px.bar(
                od.sort_values(war_col),
                x=war_col,
                y="player_team",
                orientation="h",
                color="position",
                hover_data=[
                    "season",
                    "snap_counts_offense",
                    "grades_offense",
                    "grades_pass_block",
                    "grades_run_block",
                    "pressures_allowed",
                    "sacks_allowed",
                    "penalties",
                ],
                title="Offensive line WAR detail",
            )
            fig.update_layout(height=max(420, 26 * len(od)), yaxis_title="", xaxis_title="OL WAR")
            st.plotly_chart(fig, use_container_width=True)

        cols = [
            "season",
            "ol_war_v5_rank",
            "player_name",
            "team_display",
            "position",
            war_col,
            epa_col,
            "snap_counts_offense",
            "snap_counts_pass_block",
            "snap_counts_run_block",
            "grades_offense",
            "grades_pass_block",
            "grades_run_block",
            "pressures_allowed",
            "sacks_allowed",
            "penalties",
        ]
        st.dataframe(
            od[[c for c in cols if c in od.columns]],
            use_container_width=True,
            hide_index=True,
            column_config={
                war_col: st.column_config.NumberColumn("OL WAR", format="%.3f"),
                epa_col: st.column_config.NumberColumn("OL EPA", format="%.1f"),
                "grades_offense": st.column_config.NumberColumn("Offense Grade", format="%.1f"),
                "grades_pass_block": st.column_config.NumberColumn("Pass Block Grade", format="%.1f"),
                "grades_run_block": st.column_config.NumberColumn("Run Block Grade", format="%.1f"),
            },
        )

with te_tab:
    st.subheader("Tight end run-blocking adjustment")
    st.markdown(
        "<div class='small-note'>The TE adjustment requires at least 50 run-blocking snaps. "
        "Quality comes from PFF run-block grade percentile among eligible TEs by season, and volume is scaled as a fraction of the season maximum TE run-blocking snaps.</div>",
        unsafe_allow_html=True,
    )

    te_rows = offense[offense.get("is_te_pff_match", pd.Series(False, index=offense.index)).fillna(False)].copy()
    if seasons:
        te_rows = te_rows[te_rows["season"].isin(seasons)]
    if teams:
        te_rows = te_rows[te_rows["team"].isin(teams)]
    te_rows = te_rows.sort_values("te_run_block_war_adjustment", ascending=False)

    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        st.metric("TE rows", f"{len(te_rows):,}")
    with t2:
        st.metric("Positive block adj.", f"{(te_rows['te_run_block_war_adjustment'] > 0).sum():,}")
    with t3:
        st.metric("Negative block adj.", f"{(te_rows['te_run_block_war_adjustment'] < 0).sum():,}")
    with t4:
        st.metric("Total block adj.", fmt_num(te_rows["te_run_block_war_adjustment"].sum(), 3))
    with t5:
        st.metric("Max block adj.", fmt_num(te_rows["te_run_block_war_adjustment"].max(), 3))

    plot_te = te_rows.dropna(subset=["grades_run_block", "snap_counts_run_block"]).copy()
    plot_te["abs_te_block_war_adjustment"] = plot_te["te_run_block_war_adjustment"].abs().clip(lower=0.005)
    if not plot_te.empty:
        fig = px.scatter(
            plot_te,
            x="snap_counts_run_block",
            y="grades_run_block",
            size="abs_te_block_war_adjustment",
            color="te_run_block_war_adjustment",
            hover_name="pff_player_name",
            hover_data=[
                "season",
                "team",
                "final_war",
                "final_war_pre_te_block_adj",
                "te_run_block_grade_percentile",
                "te_run_block_volume_factor",
            ],
            title="TE run-blocking quality and volume",
        )
        fig.update_layout(height=520, xaxis_title="Run-blocking snaps", yaxis_title="PFF run-block grade")
        st.plotly_chart(fig, use_container_width=True)

    display = te_rows.head(top_n)
    st.dataframe(
        leaderboard_table(display),
        use_container_width=True,
        hide_index=True,
        column_config={
            "final_war": st.column_config.NumberColumn("Adjusted WAR", format="%.3f"),
            "final_war_pre_te_block_adj": st.column_config.NumberColumn("Pre-TE Block WAR", format="%.3f"),
            "te_run_block_war_adjustment": st.column_config.NumberColumn("TE Block WAR Adj.", format="%.3f"),
            "grades_run_block": st.column_config.NumberColumn("PFF Run-Block Grade", format="%.1f"),
            "snap_counts_run_block": st.column_config.NumberColumn("Run-Block Snaps", format="%d"),
            "te_run_block_grade_percentile": st.column_config.NumberColumn("Grade Percentile", format="%.1%"),
            "te_run_block_volume_factor": st.column_config.NumberColumn("Volume Factor", format="%.1%"),
        },
    )

    with st.expander("Raw TE adjustment table"):
        raw = te_adj[te_adj["season"].isin(seasons)] if seasons else te_adj.copy()
        st.dataframe(
            raw.sort_values(["season", "te_run_block_war_adjustment"], ascending=[False, False]),
            use_container_width=True,
            hide_index=True,
        )

with player_tab:
    st.subheader("Player lookup")
    player_options = sorted(offense["player_name"].dropna().unique())
    selected_player = st.selectbox("Select player", player_options, index=0)
    player_df = offense[offense["player_name"].eq(selected_player)].sort_values("season")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("Seasons", f"{player_df['season'].nunique():,}")
    with p2:
        st.metric("Best WAR", fmt_num(player_df["final_war"].max(), 3))
    with p3:
        st.metric("Total WAR", fmt_num(player_df["final_war"].sum(), 3))
    with p4:
        st.metric("TE block adj.", fmt_num(player_df["te_run_block_war_adjustment"].sum(), 3))

    long_player = player_df.melt(
        id_vars=["season", "player_name", "team"],
        value_vars=["final_war_pre_te_block_adj", "final_war"],
        var_name="WAR version",
        value_name="WAR",
    )
    label_map = {
        "final_war_pre_te_block_adj": "Pre-TE block adjustment",
        "final_war": "Adjusted WAR",
    }
    long_player["WAR version"] = long_player["WAR version"].map(label_map)
    if not long_player.empty:
        fig = px.line(
            long_player,
            x="season",
            y="WAR",
            color="WAR version",
            markers=True,
            title=f"{selected_player}: WAR by season",
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        leaderboard_table(player_df),
        use_container_width=True,
        hide_index=True,
        column_config={
            "final_war": st.column_config.NumberColumn("Adjusted WAR", format="%.3f"),
            "final_war_pre_te_block_adj": st.column_config.NumberColumn("Pre-TE Block WAR", format="%.3f"),
            "te_run_block_war_adjustment": st.column_config.NumberColumn("TE Block WAR Adj.", format="%.3f"),
            "final_epa": st.column_config.NumberColumn("Adjusted EPA", format="%.1f"),
            "success_rate": st.column_config.NumberColumn("Success Rate", format="%.1%"),
        },
    )

with team_tab:
    st.subheader("Team and unit summary")
    summary = filtered.groupby(["season", "team", "unit"], as_index=False).agg(
        players=("player_name", "nunique"),
        adjusted_war=("final_war", "sum"),
        raw_war=("raw_war", "sum"),
        pre_te_block_war=("final_war_pre_te_block_adj", "sum"),
        te_block_war_adjustment=("te_run_block_war_adjustment", "sum"),
        adjusted_epa=("final_epa", "sum"),
        volume=("volume", "sum"),
    )
    summary = summary.sort_values("adjusted_war", ascending=False)

    if not summary.empty:
        top_team = (
            summary.groupby("team", as_index=False)["adjusted_war"]
            .sum()
            .sort_values("adjusted_war", ascending=False)
            .head(top_n)
        )
        fig = px.bar(
            top_team.sort_values("adjusted_war"),
            x="adjusted_war",
            y="team",
            orientation="h",
            title="Team offensive WAR in current filters",
        )
        fig.update_layout(height=max(420, 26 * len(top_team)), xaxis_title="Adjusted WAR", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "adjusted_war": st.column_config.NumberColumn("Adjusted WAR", format="%.3f"),
            "raw_war": st.column_config.NumberColumn("Raw WAR", format="%.3f"),
            "pre_te_block_war": st.column_config.NumberColumn("Pre-TE Block WAR", format="%.3f"),
            "te_block_war_adjustment": st.column_config.NumberColumn("TE Block WAR Adj.", format="%.3f"),
            "adjusted_epa": st.column_config.NumberColumn("Adjusted EPA", format="%.1f"),
        },
    )

with methodology_tab:
    st.subheader("Methodology")
    st.markdown(
        """
<div class="method-box">

This version keeps the combined offensive WAR master table as the main leaderboard and adds dedicated QB, skill, and offensive line detail views from their source detail files.

**TE run-blocking adjustment**

```
eligible_flag = 1 if TE run-blocking snaps >= 50 else 0
volume_factor = TE run-blocking snaps / season max TE run-blocking snaps
TE block WAR adjustment = eligible_flag × percentile bump × volume_factor
```

The grade percentile is calculated among eligible tight ends within the same season using PFF run-block grade.

**Percentile bump table**

| TE run-block percentile | Base WAR bump |
|---:|---:|
| 90th+ | +0.30 |
| 80th–89th | +0.20 |
| 70th–79th | +0.12 |
| 60th–69th | +0.06 |
| 40th–59th | 0.00 |
| 25th–39th | -0.05 |
| below 25th | -0.10 |

The adjustment is intentionally capped. It credits complete tight ends without turning blocking-only profiles into high-WAR offensive players.

</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Downloads")
    d1, d2, d3 = st.columns(3)
    with d1:
        render_download_button("Download adjusted offense master", data["offense"], "offense_war_master_2022_2025_te_adjusted.csv")
        render_download_button("Download QB master", data["qb_master"], "qb_war_master_2022_2025.csv")
        render_download_button("Download QB detail", data["qb_detail"], "qb_war_detail_2022_2025.csv")
    with d2:
        render_download_button("Download skill master", data["skill_master"], "skill_war_master_2022_2025_te_adjusted.csv")
        render_download_button("Download skill detail", data["skill_detail"], "skill_war_detail_2022_2025_te_adjusted.csv")
        render_download_button("Download TE adjustments", data["te_adj"], "te_run_block_adjustments_2022_2025.csv")
    with d3:
        render_download_button("Download OL master", data["ol_master"], "ol_war_master_2022_2025.csv")
        render_download_button("Download OL detail", data["ol_detail"], "ol_war_detail_2022_2025.csv")
