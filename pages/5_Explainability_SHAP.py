from __future__ import annotations

import pandas as pd
import plotly.express as px
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
    display_mode = st.radio("Mode tampilan fitur SHAP", options=["Semua Fitur", "Top-N"], index=0)
    top_n_features = st.slider("Jumlah fitur (Top-N)", min_value=5, max_value=20, value=10, step=1, disabled=display_mode == "Semua Fitur")

artifacts = get_explainability_artifacts(n_explain_nodes=n_explain, nsamples=nsamples)
shap_importance_df = artifacts["shap_importance_df"]
per_node_shap_df = artifacts["per_node_shap_df"]
feature_columns = artifacts.get("feature_columns", [])
shap_values_matrix = artifacts.get("shap_values_matrix")
explain_nodes = artifacts.get("explain_nodes", [])

st.caption(f"Mode explainability: {artifacts['shap_mode']}")

if len(shap_importance_df) == 0:
    st.warning("Data SHAP belum tersedia untuk ditampilkan.")
    st.stop()

all_features_df = shap_importance_df.copy().reset_index(drop=True)
all_features_df["rank"] = all_features_df.index + 1
all_features_df = all_features_df[["rank", "feature", "mean_abs_shap", "mean_shap"]]

if display_mode == "Top-N":
    display_features_df = all_features_df.head(top_n_features).copy()
else:
    display_features_df = all_features_df.copy()

temp_row = all_features_df[all_features_df["feature"] == "temp_avg"]
temp_rank_label = str(int(temp_row.iloc[0]["rank"])) if not temp_row.empty else "N/A"
temp_mean_abs_label = f"{float(temp_row.iloc[0]['mean_abs_shap']):.4f}" if not temp_row.empty else "0.0000"

mx1, mx2, mx3 = st.columns(3)
mx1.metric("Node Dianalisis", int(len(per_node_shap_df)))
mx2.metric("Avg Critical Prob", f"{float(per_node_shap_df['critical_prob'].mean()):.3f}" if len(per_node_shap_df) else "0.000")
mx3.metric("Top Driver #1", str(all_features_df.iloc[0]["feature"]))

t1, t2 = st.columns(2)
t1.metric("Rank temp_avg (Global SHAP)", temp_rank_label)
t2.metric("Mean |SHAP| temp_avg", temp_mean_abs_label)

if display_mode == "Top-N":
    st.subheader(f"Global SHAP Top-{top_n_features} Fitur (Mean |SHAP|)")
else:
    st.subheader("Global SHAP Semua Fitur (Mean |SHAP|)")

fig_all = px.bar(
    display_features_df,
    x="mean_abs_shap",
    y="feature",
    color="mean_abs_shap",
    color_continuous_scale="YlOrRd",
    orientation="h",
    title="Global Feature Importance untuk Critical Probability",
    height=max(420, 26 * len(display_features_df)),
)
fig_all.update_layout(yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
st.plotly_chart(fig_all, width="stretch")

st.subheader("Ringkasan Arah Dampak")
direction_df = display_features_df[["feature", "mean_abs_shap", "mean_shap"]].copy()
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

if shap_values_matrix is not None and feature_columns and explain_nodes:
    shap_matrix_df = pd.DataFrame(shap_values_matrix, columns=feature_columns)
    shap_matrix_df.insert(0, "node_id", explain_nodes)

    st.subheader("Semua SHAP Value Per Node")
    selected_node_shap = shap_matrix_df[shap_matrix_df["node_id"] == int(selected_node)].copy()
    if not selected_node_shap.empty:
        long_df = selected_node_shap.melt(id_vars=["node_id"], var_name="feature", value_name="shap_value")
        long_df["abs_shap"] = long_df["shap_value"].abs()
        long_df = long_df.sort_values("abs_shap", ascending=False)

        if display_mode == "Top-N":
            long_df_display = long_df.head(top_n_features).copy()
            st.caption(f"Mode presentasi aktif: menampilkan Top-{top_n_features} fitur per node.")
        else:
            long_df_display = long_df.copy()

        fig_node = px.bar(
            long_df_display,
            x="shap_value",
            y="feature",
            color="shap_value",
            color_continuous_scale="RdBu",
            orientation="h",
            title=f"Semua SHAP Value untuk Node {int(selected_node)}",
            height=max(420, 24 * len(long_df_display)),
        )
        fig_node.update_layout(yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
        st.plotly_chart(fig_node, width="stretch")

        st.dataframe(long_df_display[["feature", "shap_value", "abs_shap"]], width="stretch", hide_index=True)
