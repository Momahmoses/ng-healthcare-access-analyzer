"""
Nigeria Healthcare Access Gap Analyzer — Streamlit Dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from data.generate_data import generate_facilities, generate_health_gaps
from gis.spatial_analysis import build_facility_gdf, build_state_gdf, build_access_map

st.set_page_config(page_title="NG Healthcare Access", page_icon="🏥", layout="wide")

st.markdown("""
<style>
.kpi{background:#0d47a1;color:white;padding:14px;border-radius:8px;text-align:center;}
.kpi-val{font-size:1.9rem;font-weight:700;}
.kpi-lbl{font-size:.8rem;opacity:.85;}
.critical{background:#b71c1c;color:white;padding:4px 10px;border-radius:4px;}
.high{background:#e65100;color:white;padding:4px 10px;border-radius:4px;}
.moderate{background:#f9a825;color:black;padding:4px 10px;border-radius:4px;}
.adequate{background:#1b5e20;color:white;padding:4px 10px;border-radius:4px;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    return generate_facilities(800), generate_health_gaps()


def priority_badge(tier: str) -> str:
    return f'<span class="{tier.lower()}">{tier}</span>'


def main():
    fac_df, gap_df = load_data()
    fac_gdf = build_facility_gdf(fac_df)
    state_gdf = build_state_gdf(gap_df)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🏥 Healthcare Access")
        st.caption("Nigeria Gap Analyzer")
        st.divider()
        zone_filter = st.multiselect("Geopolitical Zone", gap_df["zone"].unique().tolist(),
                                     default=gap_df["zone"].unique().tolist())
        min_gap = st.slider("Min Gap Score", 0.0, 1.0, 0.0, 0.05)
        facility_type = st.multiselect("Facility Type", fac_df["type"].unique().tolist(),
                                       default=fac_df["type"].unique().tolist())
        st.divider()
        st.markdown("**WHO Benchmarks**")
        st.info("1 doctor per 1,000 people")
        st.info("2.5 beds per 1,000 people")
        st.info("≤1hr travel to facility")

    gap_filtered = gap_df[gap_df["zone"].isin(zone_filter) & (gap_df["gap_score"] >= min_gap)]
    fac_filtered = fac_df[fac_df["type"].isin(facility_type)]

    # ── Title ─────────────────────────────────────────────────────────────────
    st.title("🏥 Nigeria Healthcare Access Gap Analyzer")
    st.caption("Facility coverage · Underserved LGA mapping · Powered by GIS + PySpark + Azure")
    st.divider()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    total_fac = len(fac_df[fac_df["operational"] == True])
    underserved = len(gap_df[gap_df["gap_score"] > 0.5])
    avg_travel = gap_df["avg_travel_time_min"].mean()
    avg_docs = gap_df["doctors_per_10k"].mean()
    total_beds = fac_df[fac_df["operational"] == True]["beds"].sum()
    for col, val, lbl in zip(
        [c1, c2, c3, c4, c5],
        [total_fac, underserved, f"{avg_travel:.0f} min", f"{avg_docs:.1f}", f"{total_beds:,}"],
        ["Active Facilities", "Underserved States", "Avg Travel Time", "Doctors/10k", "Total Beds"]
    ):
        col.markdown(f'<div class="kpi"><div class="kpi-val">{val}</div>'
                     f'<div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.divider()

    # ── Map + Treemap ─────────────────────────────────────────────────────────
    col_map, col_chart = st.columns([3, 2])
    with col_map:
        st.subheader("🗺 Facility Coverage Map")
        m = build_access_map(state_gdf[state_gdf["zone"].isin(zone_filter)], fac_gdf)
        st_folium(m, width=700, height=460)

    with col_chart:
        st.subheader("📊 Gap Score by State")
        fig = px.bar(
            gap_filtered.sort_values("gap_score", ascending=True).tail(20),
            x="gap_score", y="state", orientation="h",
            color="gap_score", color_continuous_scale="RdYlGn_r",
            labels={"gap_score": "Gap Score", "state": ""},
            height=460,
        )
        fig.update_layout(coloraxis_showscale=False,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=0, r=10, t=5, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Facility Type Distribution ────────────────────────────────────────────
    col_pie, col_scatter = st.columns(2)
    with col_pie:
        st.subheader("🏗 Facility Type Distribution")
        type_counts = fac_filtered[fac_filtered["operational"] == True]["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig_pie = px.pie(type_counts, names="type", values="count", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_pie.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_scatter:
        st.subheader("👥 Coverage % vs Population")
        fig_sc = px.scatter(
            gap_filtered, x="population", y="coverage_pct",
            color="zone", size="population",
            hover_name="state", size_max=40,
            labels={"population": "State Population", "coverage_pct": "Healthcare Coverage (%)"},
        )
        fig_sc.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sc, use_container_width=True)

    st.divider()

    # ── Priority Tier Table ───────────────────────────────────────────────────
    st.subheader("📋 State Priority Rankings")
    gap_df_display = gap_filtered.copy()
    gap_df_display["Priority"] = gap_df_display["gap_score"].apply(
        lambda x: "Critical" if x > 0.7 else "High" if x > 0.5 else "Moderate" if x > 0.3 else "Adequate"
    )
    display_cols = ["state", "zone", "population", "doctors_per_10k", "beds_per_1k",
                    "coverage_pct", "avg_travel_time_min", "Priority"]
    st.dataframe(
        gap_df_display[display_cols].sort_values("gap_score", ascending=False)
        .style.background_gradient(subset=["coverage_pct"], cmap="RdYlGn")
               .background_gradient(subset=["avg_travel_time_min"], cmap="RdYlGn_r"),
        use_container_width=True, height=320,
    )

    st.caption("Data: Synthetic — replace with FMOH, NBS, WHO SARA surveys. "
               "Pipeline: Azure Databricks PySpark. Storage: Azure Blob Storage.")


if __name__ == "__main__":
    main()
