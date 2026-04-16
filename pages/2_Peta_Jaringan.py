from __future__ import annotations

import streamlit as st

from src.app_state import get_base_artifacts, get_prediction_table
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(page_title="Peta Jaringan", layout="wide")
apply_app_theme()

render_page_hero(
    "Peta Jaringan Pipeline",
    "Ringkasan metrik jaringan. Peta topology interaktif dan diagnosis per node ada di halaman Dashboard Risiko (bagian bawah, setelah tabel risiko).",
)

pred_df, _ = get_prediction_table()
_, edge_df, _, _ = get_base_artifacts()

node_df = pred_df.copy()
if "node_id" not in node_df.columns:
    node_df["node_id"] = node_df.index

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Node", int(len(node_df)))
k2.metric("Node Critical", int((node_df["predicted_class"] == "Critical").sum()))
k3.metric("Node Warning", int((node_df["predicted_class"] == "Warning").sum()))
k4.metric("Rata-rata Critical Prob", f"{float(node_df['critical_prob'].mean()):.3f}")

st.info(
    "**Peta interaktif (Topology Risk Map)** beserta panel diagnosis node telah dipindahkan ke "
    "**Dashboard Risiko**, tepatnya di bawah bagian **Tabel Risiko Per Segmen**."
)

st.caption(f"Total edge pada data: {len(edge_df)}")
