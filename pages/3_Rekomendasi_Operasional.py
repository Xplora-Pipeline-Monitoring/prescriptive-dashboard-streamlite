from __future__ import annotations

import streamlit as st

from src.app_state import get_prediction_table
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(page_title="Rekomendasi Operasional", layout="wide")
apply_app_theme()
render_page_hero(
    "Rekomendasi Operasional Berbasis Risiko",
    "Gunakan filter area dan tier untuk menghasilkan rencana tindakan inspeksi yang paling berdampak.",
)

pred_df, _ = get_prediction_table()
df = pred_df.copy()

if "node_id" not in df.columns:
    df["node_id"] = df.index


def infer_area(node_id) -> str:
    text = str(node_id)
    if "_" in text:
        return text.split("_")[0].upper()
    return "MAIN"


df["area"] = df["node_id"].apply(infer_area)

tier_options = ["P1", "P2", "P3"]
col1, col2, col3 = st.columns(3)
with col1:
    area_filter = st.multiselect("Filter Area", options=sorted(df["area"].unique()), default=sorted(df["area"].unique()))
with col2:
    tier_filter = st.multiselect("Filter Priority Tier", options=tier_options, default=tier_options)
with col3:
    top_n = st.slider("Top-N prioritas", min_value=5, max_value=min(100, len(df)), value=min(20, len(df)), step=1)

filtered = df[df["area"].isin(area_filter) & df["priority_tier"].isin(tier_filter)].copy()
filtered = filtered.sort_values("priority_score", ascending=False).head(top_n)

s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Hasil Filter", int(len(filtered)))
s2.metric("P1", int((filtered["priority_tier"] == "P1").sum()))
s3.metric("Critical", int((filtered["predicted_class"] == "Critical").sum()))
s4.metric("Rata-rata priority_score", f"{float(filtered['priority_score'].mean()):.3f}" if len(filtered) else "0.000")

show_cols = [
    "node_id",
    "area",
    "predicted_class",
    "critical_prob",
    "propagation_uplift",
    "priority_tier",
    "priority_score",
    "recommended_action",
    "target_sla",
]
show_cols = [c for c in show_cols if c in filtered.columns]

st.subheader("Prioritas inspeksi teratas")
st.dataframe(filtered[show_cols], width="stretch", hide_index=True)

csv_bytes = filtered[show_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    label="Unduh CSV rencana tindakan",
    data=csv_bytes,
    file_name="pipelineguard_action_plan.csv",
    mime="text/csv",
)

with st.container(border=True):
    st.markdown("### Aturan Prioritas (P1/P2/P3)")
    st.markdown("- P1: prediksi Critical atau critical_prob >= 0.60 -> SLA <=24 jam")
    st.markdown("- P2: prediksi Warning atau critical_prob >= 0.35 -> SLA <=7 hari")
    st.markdown("- P3: selain itu -> SLA <=30 hari")
