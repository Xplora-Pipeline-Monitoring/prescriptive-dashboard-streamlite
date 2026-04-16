from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from src.app_state import get_explainability_artifacts
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(page_title="Explainability SHAP", layout="wide")
apply_app_theme()
render_page_hero(
    "Explainability SHAP untuk Risiko Critical",
    "Halaman ini membantu operator memahami fitur utama pendorong risiko dan rekomendasi per node.",
)

with st.sidebar:
    n_explain = st.slider("Jumlah node untuk explain", min_value=9, max_value=30, value=18, step=3)
    nsamples = st.slider("Kernel SHAP nsamples", min_value=40, max_value=120, value=80, step=10)

artifacts = get_explainability_artifacts(n_explain_nodes=n_explain, nsamples=nsamples)
shap_importance_df = artifacts["shap_importance_df"]
per_node_shap_df = artifacts["per_node_shap_df"]

st.caption(f"Mode explainability: {artifacts['shap_mode']}")

mx1, mx2, mx3 = st.columns(3)
mx1.metric("Node Dianalisis", int(len(per_node_shap_df)))
mx2.metric("Avg Critical Prob", f"{float(per_node_shap_df['critical_prob'].mean()):.3f}" if len(per_node_shap_df) else "0.000")
mx3.metric("Top Driver #1", str(shap_importance_df.iloc[0]["feature"]) if len(shap_importance_df) else "N/A")

st.subheader("Top 10 Global Drivers (Mean |SHAP|)")
top10 = shap_importance_df.head(10).copy()
fig1 = plt.figure(figsize=(9, 4.8))
sns.barplot(data=top10, x="mean_abs_shap", y="feature", hue="feature", palette="rocket", dodge=False, legend=False)
plt.title("Top Feature Importance untuk Critical Probability")
plt.xlabel("Mean |SHAP value|")
plt.ylabel("Feature")
plt.tight_layout()
st.pyplot(fig1)
plt.close(fig1)

st.subheader("Ringkasan Arah Dampak")
direction_df = top10[["feature", "mean_abs_shap", "mean_shap"]].copy()
direction_df["impact_direction"] = direction_df["mean_shap"].apply(lambda v: "positive" if float(v) >= 0 else "negative")
st.dataframe(direction_df, width="stretch", hide_index=True)

st.subheader("Per-Node SHAP Audit Table")
cols_priority = [
    "node_id",
    "risk_class",
    "pred_risk_class",
    "critical_prob",
    "audit_flag",
    "top3_shap_drivers",
    "rekomendasi_per_node",
]
available_cols = [c for c in cols_priority if c in per_node_shap_df.columns]
st.dataframe(
    per_node_shap_df[available_cols].sort_values(["critical_prob", "node_id"], ascending=[False, True]),
    width="stretch",
    hide_index=True,
)

st.subheader("Node Explorer")
node_options = per_node_shap_df["node_id"].astype(int).tolist()
selected_node = st.selectbox("Pilih node", options=node_options)
selected_row = per_node_shap_df[per_node_shap_df["node_id"] == selected_node].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Node", int(selected_row["node_id"]))
c2.metric("Pred Class", str(selected_row.get("pred_risk_class", "N/A")))
c3.metric("Critical Prob", f"{float(selected_row.get('critical_prob', 0.0)):.4f}")
c4.metric("Audit", str(selected_row.get("audit_flag", "N/A")))

st.markdown("**Top 3 SHAP Drivers**")
st.info(str(selected_row.get("top3_shap_drivers", "-")))
st.markdown("**Rekomendasi Per Node**")
st.success(str(selected_row.get("rekomendasi_per_node", "-")))
