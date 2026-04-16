from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.app_state import get_prediction_table
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(
    page_title="PipelineGuard AI Dashboard",
    page_icon="assets",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_app_theme()
render_page_hero(
    "PipelineGuard AI - Prescriptive Corrosion Dashboard",
    "Dashboard operasional untuk memprioritaskan inspeksi dan tindakan mitigasi korosi secara cepat.",
)

with st.container(border=True):
    st.markdown(
        "Aplikasi ini menampilkan prediksi risiko korosi, prioritas inspeksi P1/P2/P3, "
        "peta jaringan pipa, serta ringkasan validasi standard test vs stress test."
    )

try:
    prediction_df, meta = get_prediction_table()
except (FileNotFoundError, ValueError, RuntimeError) as exc:
    st.error(f"Gagal memuat artefak atau menjalankan inference: {exc}")
    st.stop()

c1, c2, c3 = st.columns(3)
total_segments = int(len(prediction_df))
critical_segments = int((prediction_df["predicted_class"] == "Critical").sum())
p1_segments = int((prediction_df["priority_tier"] == "P1").sum())

critical_rate = (critical_segments / total_segments) if total_segments else 0.0
p1_rate = (p1_segments / total_segments) if total_segments else 0.0

c1.metric("Total Segmen", total_segments)
c2.metric("Segmen Critical", critical_segments, delta=f"{critical_rate:.1%} dari total")
c3.metric("Segmen P1", p1_segments, delta=f"{p1_rate:.1%} dari total")

class_dist = prediction_df["predicted_class"].value_counts().reindex(["Safe", "Warning", "Critical"]).fillna(0).astype(int)

st.markdown("### Ringkasan Distribusi Risiko")
viz_col, summary_col = st.columns([1.2, 1.0])

with viz_col:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=class_dist.index.tolist(),
                values=class_dist.values.tolist(),
                hole=0.58,
                marker=dict(colors=["#22c55e", "#f59e0b", "#ef4444"]),
                textinfo="label+percent",
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

with summary_col:
    st.markdown(
        f"""
<div class="pg-stat-card">
    <div class="pg-stat-label">Safe</div>
    <div class="pg-stat-value">{int(class_dist.get('Safe', 0))} segmen</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="pg-stat-card">
    <div class="pg-stat-label">Warning</div>
    <div class="pg-stat-value">{int(class_dist.get('Warning', 0))} segmen</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="pg-stat-card">
    <div class="pg-stat-label">Critical</div>
    <div class="pg-stat-value">{int(class_dist.get('Critical', 0))} segmen</div>
</div>
""",
        unsafe_allow_html=True,
    )

with st.container(border=True):
    st.markdown("### Alur Pakai Cepat (Operator)")
    st.markdown("1. Buka halaman **Peta Jaringan** lalu klik node berwarna Warning/Critical.")
    st.markdown("2. Lihat panel diagnosis fitur untuk tahu parameter mana yang paling mendesak diperbaiki.")
    st.markdown("3. Buka **Rekomendasi Operasional** untuk ekspor action plan inspeksi.")

with st.expander("Status Sistem", expanded=False):
    left_status, right_status = st.columns(2)
    left_status.markdown("**Direktori Artifact**")
    left_status.caption(str(meta.get("artifact_dir", "N/A")))
    left_status.markdown("**Mode Inference**")
    left_status.caption(str(meta.get("inference_mode", "N/A")))

    right_status.markdown("**Catatan Model**")
    right_status.caption(str(meta.get("model_note", "N/A")))

    warnings = meta.get("warnings", [])
    if warnings:
        st.warning(f"Terdapat {len(warnings)} warning yang perlu ditinjau.")
        for idx, warning_text in enumerate(warnings[:5], start=1):
            st.markdown(f"{idx}. {warning_text}")
    else:
        st.success("Tidak ada warning pada proses preprocessing dan inference.")

st.info("Gunakan menu di sidebar untuk membuka halaman Dashboard Risiko, Peta Jaringan, Rekomendasi Operasional, dan Validasi & Metrik.")
