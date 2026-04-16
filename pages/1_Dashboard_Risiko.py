from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.app_state import get_prediction_table
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(page_title="Dashboard Risiko", layout="wide")
apply_app_theme()
render_page_hero(
    "Dashboard Risiko Korosi",
    "Pantau distribusi risiko, probabilitas critical, dan indikator diagnostik utama per segmen pipa.",
)

prediction_df, meta = get_prediction_table()

df = prediction_df.copy()
if "node_id" not in df.columns:
    df["node_id"] = df.index

segment_filter = st.multiselect(
    "Filter kelas prediksi",
    options=sorted(df["predicted_class"].dropna().unique().tolist()),
    default=sorted(df["predicted_class"].dropna().unique().tolist()),
)
if segment_filter:
    df = df[df["predicted_class"].isin(segment_filter)]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Node", int(len(df)))
k2.metric("Jumlah Critical", int((df["predicted_class"] == "Critical").sum()))
k3.metric("Jumlah P1", int((df["priority_tier"] == "P1").sum()))
k4.metric("Rata-rata Risk Score", f"{df['priority_score'].mean():.3f}")

c1, c2 = st.columns(2)
with c1:
    dist = df["predicted_class"].value_counts().rename_axis("class").reset_index(name="count")
    fig_class = px.bar(
        dist,
        x="class",
        y="count",
        color="class",
        title="Distribusi Kelas Prediksi",
        category_orders={"class": ["Safe", "Warning", "Critical"]},
        color_discrete_map={"Safe": "#22c55e", "Warning": "#f59e0b", "Critical": "#ef4444"},
    )
    st.plotly_chart(fig_class, width="stretch")

with c2:
    fig_hist = px.histogram(
        df,
        x="critical_prob",
        nbins=20,
        color="predicted_class",
        title="Distribusi Probabilitas Critical",
        color_discrete_map={"Safe": "#22c55e", "Warning": "#f59e0b", "Critical": "#ef4444"},
    )
    st.plotly_chart(fig_hist, width="stretch")

st.subheader("Feature Diagnostics (Acuan Notebook)")
feature_opt = st.selectbox(
    "Pilih fitur untuk boxplot lintas kelas",
    options=[c for c in ["press_avg", "ph_level", "h2s_ppm", "pco2_psi", "corrosion_rate_mm_yr"] if c in df.columns],
)
if feature_opt:
    fig_box = px.box(
        df,
        x="predicted_class",
        y=feature_opt,
        color="predicted_class",
        category_orders={"predicted_class": ["Safe", "Warning", "Critical"]},
        title=f"Distribusi {feature_opt} per Kelas Prediksi",
        color_discrete_map={"Safe": "#22c55e", "Warning": "#f59e0b", "Critical": "#ef4444"},
    )
    st.plotly_chart(fig_box, width="stretch")

show_cols = [
    "node_id",
    "predicted_class",
    "safe_prob",
    "warning_prob",
    "critical_prob",
    "priority_tier",
    "priority_score",
]
available_cols = [c for c in show_cols if c in df.columns]

st.subheader("Tabel Risiko Per Segmen")
st.dataframe(
    df[available_cols].sort_values("priority_score", ascending=False),
    width="stretch",
    hide_index=True,
)

with st.expander("Ringkasan Konteks Model", expanded=False):
    model_cfg = meta.get("model_config", {})
    info1, info2, info3 = st.columns(3)
    info1.metric("Model", str(model_cfg.get("model_name", "N/A")))
    info2.metric("Versi", str(model_cfg.get("version", "N/A")))
    info3.metric("Mode Inferensi", str(meta.get("inference_mode", "N/A")))

    metrics = model_cfg.get("metrics", {})
    if metrics:
        st.markdown("**Metrik Model**")
        for metric_name, metric_value in metrics.items():
            st.markdown(f"- {metric_name}: {metric_value}")
