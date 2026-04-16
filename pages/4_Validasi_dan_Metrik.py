from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.app_state import get_prediction_table
from src.inference import run_stress_test
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(page_title="Evaluasi Metrik Model", layout="wide")
apply_app_theme()
render_page_hero(
    "Evaluasi Metrik Model",
    "Bandingkan performa standard vs stress test serta cek stabilitas metrik untuk pengambilan keputusan operasional.",
)

base_df, meta = get_prediction_table()
stress_df = run_stress_test(base_df)


def summarize(df: pd.DataFrame) -> dict:
    return {
        "critical_rate": float((df["predicted_class"] == "Critical").mean()),
        "avg_critical_prob": float(df["critical_prob"].mean()),
        "avg_priority_score": float(df["priority_score"].mean()) if "priority_score" in df.columns else float(df["critical_prob"].mean()),
    }


std_metrics = summarize(base_df)
stress_metrics = summarize(stress_df)

c1, c2, c3 = st.columns(3)
c1.metric("Laju critical (standar)", f"{std_metrics['critical_rate']:.2%}")
c2.metric("Laju critical (stress)", f"{stress_metrics['critical_rate']:.2%}", delta=f"{stress_metrics['critical_rate'] - std_metrics['critical_rate']:.2%}")
c3.metric("Rata-rata critical_prob (stress)", f"{stress_metrics['avg_critical_prob']:.3f}", delta=f"{stress_metrics['avg_critical_prob'] - std_metrics['avg_critical_prob']:.3f}")

compare_df = pd.DataFrame(
    {
        "skenario": ["Uji standar", "Uji stress"],
        "critical_rate": [std_metrics["critical_rate"], stress_metrics["critical_rate"]],
        "avg_critical_prob": [std_metrics["avg_critical_prob"], stress_metrics["avg_critical_prob"]],
        "avg_priority_score": [std_metrics["avg_priority_score"], stress_metrics["avg_priority_score"]],
    }
)

_metrik_label = {
    "critical_rate": "Laju critical",
    "avg_critical_prob": "Rata-rata critical_prob",
    "avg_priority_score": "Rata-rata priority_score",
}
_compare_melt = compare_df.melt(id_vars="skenario", var_name="metrik", value_name="nilai")
_compare_melt["metrik"] = _compare_melt["metrik"].map(lambda m: _metrik_label.get(m, m))

scenario_df = pd.DataFrame(
    [
        {
            "Skenario": "Uji standar (checkpoint terbaik)",
            "Akurasi": 1.0000,
            "Macro F1": 1.0000,
            "Critical F1": 1.0000,
            "Tujuan": "Performa pada kondisi nominal",
        },
        {
            "Skenario": "Uji standar (epoch terakhir)",
            "Akurasi": 1.0000,
            "Macro F1": 1.0000,
            "Critical F1": 1.0000,
            "Tujuan": "Snapshot akhir pelatihan",
        },
        {
            "Skenario": "Uji stress (GraphSAGE tanpa konteks edge)",
            "Akurasi": 0.6957,
            "Macro F1": 0.7165,
            "Critical F1": 0.8889,
            "Tujuan": "Robustness saat degradasi sensor",
        },
    ]
)

fig_compare = px.bar(
    _compare_melt,
    x="metrik",
    y="nilai",
    color="skenario",
    barmode="group",
    title="Perbandingan uji standar vs uji stress",
)
st.plotly_chart(fig_compare, width="stretch")

if "propagation_uplift" in base_df.columns:
    before_critical = int((base_df["predicted_class"] == "Critical").sum())
    after_critical = int((base_df["critical_prob"] + base_df["propagation_uplift"] >= 0.60).sum())
    prop_df = pd.DataFrame(
        {"tahap": ["Sebelum", "Sesudah"], "jumlah_node_critical": [before_critical, after_critical]}
    )
    fig_prop = px.bar(
        prop_df,
        x="tahap",
        y="jumlah_node_critical",
        title="Jumlah node Critical: sebelum vs sesudah propagasi",
        color="tahap",
        color_discrete_map={"Sebelum": "#60a5fa", "Sesudah": "#ef4444"},
    )
    st.plotly_chart(fig_prop, width="stretch")

# Simulasi multi-seed sederhana untuk estimasi stabilitas skenario standar.
seed_rows = []
rng = np.random.default_rng(42)
base_probs = base_df["critical_prob"].to_numpy()
for seed in range(1, 11):
    noise = rng.normal(0.0, 0.015, size=len(base_probs))
    sampled = np.clip(base_probs + noise, 0, 1)
    seed_rows.append({
        "seed": seed,
        "critical_prob_mean": float(sampled.mean()),
        "critical_rate_est": float((sampled >= 0.60).mean()),
    })

seed_df = pd.DataFrame(seed_rows)
critical_prob_mean_mean = float(seed_df["critical_prob_mean"].mean())
critical_prob_mean_std = float(seed_df["critical_prob_mean"].std(ddof=1))
critical_rate_mean = float(seed_df["critical_rate_est"].mean())
critical_rate_std = float(seed_df["critical_rate_est"].std(ddof=1))

st.subheader("Ringkasan multi-seed (mean ± std)")
summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.markdown(
        f"""
<div class="pg-stat-card">
    <div class="pg-stat-label">Rata-rata critical_prob</div>
    <div class="pg-stat-value">{critical_prob_mean_mean:.3f} ± {critical_prob_mean_std:.3f}</div>
    <div class="pg-stat-note">Rata-rata probabilitas critical dari simulasi 10 seed.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with summary_col2:
    st.markdown(
        f"""
<div class="pg-stat-card">
    <div class="pg-stat-label">Estimasi laju critical</div>
    <div class="pg-stat-value">{critical_rate_mean:.2%} ± {critical_rate_std:.2%}</div>
    <div class="pg-stat-note">Persentase estimasi node critical saat threshold probabilitas 0.60.</div>
</div>
""",
        unsafe_allow_html=True,
    )

seed_tampil = seed_df.rename(
    columns={
        "seed": "seed",
        "critical_prob_mean": "Rata-rata critical_prob",
        "critical_rate_est": "Estimasi laju critical",
    }
)
st.dataframe(seed_tampil, hide_index=True, width="stretch")

st.subheader("Metrik skenario (referensi notebook)")
st.dataframe(scenario_df, hide_index=True, width="stretch")

_inference_mode_label = {
    "heuristic": "Heuristik",
    "artifact_export": "Ekspor artefak (label)",
    "torch_model": "Model Torch",
}
_mode_tampil = _inference_mode_label.get(str(meta.get("inference_mode", "")), meta.get("inference_mode", "N/A"))

with st.expander("Batasan model", expanded=False):
    st.markdown(
        "- Jika model Torch tidak dapat dimuat, aplikasi memakai **fallback** ke skor heuristik."
    )
    st.markdown(
        "- Uji stress di halaman ini adalah simulasi operasional untuk **robustness check**, bukan pelatihan ulang."
    )
    st.markdown(
        "- Validasi akhir sebelum **go-live** wajib membandingkan hasil notebook dan Streamlit pada input yang sama."
    )
    st.write(f"Mode inferensi saat ini: {_mode_tampil}")
