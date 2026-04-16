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
c1.metric("Critical Rate (Standard)", f"{std_metrics['critical_rate']:.2%}")
c2.metric("Critical Rate (Stress)", f"{stress_metrics['critical_rate']:.2%}", delta=f"{stress_metrics['critical_rate'] - std_metrics['critical_rate']:.2%}")
c3.metric("Avg Critical Prob (Stress)", f"{stress_metrics['avg_critical_prob']:.3f}", delta=f"{stress_metrics['avg_critical_prob'] - std_metrics['avg_critical_prob']:.3f}")

compare_df = pd.DataFrame(
    {
        "scenario": ["Standard Test", "Stress Test"],
        "critical_rate": [std_metrics["critical_rate"], stress_metrics["critical_rate"]],
        "avg_critical_prob": [std_metrics["avg_critical_prob"], stress_metrics["avg_critical_prob"]],
        "avg_priority_score": [std_metrics["avg_priority_score"], stress_metrics["avg_priority_score"]],
    }
)

scenario_df = pd.DataFrame(
    [
        {
            "Scenario": "Standard Test (Best Checkpoint)",
            "Accuracy": 1.0000,
            "Macro F1": 1.0000,
            "Critical F1": 1.0000,
            "Purpose": "Nominal condition performance",
        },
        {
            "Scenario": "Standard Test (Last Epoch)",
            "Accuracy": 1.0000,
            "Macro F1": 1.0000,
            "Critical F1": 1.0000,
            "Purpose": "Training-end snapshot",
        },
        {
            "Scenario": "Stress Test (GraphSAGE w/o Edge Context)",
            "Accuracy": 0.6957,
            "Macro F1": 0.7165,
            "Critical F1": 0.8889,
            "Purpose": "Robustness under sensor degradation",
        },
    ]
)

fig_compare = px.bar(
    compare_df.melt(id_vars="scenario", var_name="metric", value_name="value"),
    x="metric",
    y="value",
    color="scenario",
    barmode="group",
    title="Perbandingan Standard Test vs Stress Test",
)
st.plotly_chart(fig_compare, width="stretch")

if "propagation_uplift" in base_df.columns:
    before_critical = int((base_df["predicted_class"] == "Critical").sum())
    after_critical = int((base_df["critical_prob"] + base_df["propagation_uplift"] >= 0.60).sum())
    prop_df = pd.DataFrame(
        {"stage": ["Before", "After"], "critical_nodes": [before_critical, after_critical]}
    )
    fig_prop = px.bar(
        prop_df,
        x="stage",
        y="critical_nodes",
        title="Critical Node Count: Before vs After Propagation",
        color="stage",
        color_discrete_map={"Before": "#60a5fa", "After": "#ef4444"},
    )
    st.plotly_chart(fig_prop, width="stretch")

# Simulasi multi-seed sederhana untuk estimasi stabilitas skenario standard.
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

st.subheader("Multi-Seed Summary (Mean ± Std)")
summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.markdown(
        f"""
<div class="pg-stat-card">
    <div class="pg-stat-label">Critical Prob Mean</div>
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
    <div class="pg-stat-label">Critical Rate Estimate</div>
    <div class="pg-stat-value">{critical_rate_mean:.2%} ± {critical_rate_std:.2%}</div>
    <div class="pg-stat-note">Persentase estimasi node critical saat threshold probabilitas 0.60.</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.dataframe(seed_df, hide_index=True, width="stretch")

st.subheader("Scenario Metrics (Notebook Reference)")
st.dataframe(scenario_df, hide_index=True, width="stretch")

with st.expander("Batasan Model", expanded=False):
    st.markdown("- Jika model torch tidak bisa dimuat, aplikasi fallback ke mode heuristik.")
    st.markdown("- Stress test pada halaman ini adalah simulasi operasional untuk robust-check, bukan retraining.")
    st.markdown("- Validasi final sebelum go-live wajib membandingkan hasil notebook dan Streamlit pada input yang sama.")
    st.write(f"Mode inference saat ini: {meta.get('inference_mode', 'N/A')}")
