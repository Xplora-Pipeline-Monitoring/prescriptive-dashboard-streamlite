from __future__ import annotations

import importlib

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app_state import get_base_artifacts, get_prediction_table
from src.feature_actions import get_feature_action
from src.graph_utils import build_network_graph
from src.ui_theme import apply_app_theme, render_page_hero


st.set_page_config(page_title="Peta Jaringan", layout="wide")
apply_app_theme()

st.markdown(
    """
<style>
.ops-card {
    border: 1px solid #dbe2ea;
    border-radius: 12px;
    padding: 12px 14px;
    background: linear-gradient(180deg, #ffffff, #f8fbff);
    margin-bottom: 10px;
}
.ops-pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 12px;
}
.pill-critical { background: #fee2e2; color: #b91c1c; }
.pill-warning  { background: #fef3c7; color: #92400e; }
.pill-safe     { background: #dcfce7; color: #166534; }
</style>
""",
    unsafe_allow_html=True,
)

render_page_hero(
    "Peta Jaringan Pipeline",
    "Klik node pada topology untuk melihat diagnosis fitur prioritas dan tindakan korektif yang paling relevan.",
)


FEATURE_RULES = [
    ("corrosion_rate_mm_yr", "max", 1.00),
    ("ph_level", "min", 6.50),
    ("h2s_ppm", "max", 18.0),
    ("chloride_ppm", "max", 800.0),
    ("inhibitor_ppm", "min", 20.0),
    ("press_avg", "max", 60.0),
    ("pco2_psi", "max", 1.50),
    ("nlp_anomaly_score", "max", 0.60),
]


def _severity_score(value: float, rule_type: str, threshold: float) -> float:
    if rule_type == "max":
        return max(0.0, (value - threshold) / max(abs(threshold), 1e-6))
    return max(0.0, (threshold - value) / max(abs(threshold), 1e-6))


def _build_operator_actions(node_data: pd.Series) -> pd.DataFrame:
    rows: list[dict] = []
    for feature, rule_type, threshold in FEATURE_RULES:
        if feature not in node_data.index:
            continue
        raw_val = node_data.get(feature)
        if raw_val is None:
            continue
        value = pd.to_numeric(pd.Series([raw_val]), errors="coerce").iloc[0]
        if pd.isna(float(value)):
            continue

        sev = _severity_score(float(value), rule_type, float(threshold))
        if sev <= 0:
            continue

        rows.append(
            {
                "feature": feature,
                "nilai_saat_ini": float(value),
                "target_operasi": float(threshold),
                "severity": float(sev),
                "aksi_disarankan": get_feature_action(feature),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["feature", "nilai_saat_ini", "target_operasi", "severity", "aksi_disarankan"])

    return pd.DataFrame(rows).sort_values("severity", ascending=False).reset_index(drop=True)


def _status_pill(predicted_class: str) -> str:
    status_name = str(predicted_class)
    if status_name == "Critical":
        return '<span class="ops-pill pill-critical">Critical</span>'
    if status_name == "Warning":
        return '<span class="ops-pill pill-warning">Warning</span>'
    return '<span class="ops-pill pill-safe">Safe</span>'

pred_df, _ = get_prediction_table()
_, edge_df, _, _ = get_base_artifacts()

node_df = pred_df.copy()
graph = build_network_graph(node_df=node_df, edge_df=edge_df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Node", int(len(node_df)))
k2.metric("Node Critical", int((node_df["predicted_class"] == "Critical").sum()))
k3.metric("Node Warning", int((node_df["predicted_class"] == "Warning").sum()))
k4.metric("Rata-rata Critical Prob", f"{float(node_df['critical_prob'].mean()):.3f}")

if graph.number_of_nodes() == 0:
    st.warning("Graf tidak memiliki node untuk divisualisasikan.")
    st.stop()

pos = nx.spring_layout(graph, seed=42)

edge_traces = []
for src, dst in graph.edges():
    x0, y0 = pos[src]
    x1, y1 = pos[dst]
    attrs = graph.get_edge_data(src, dst, default={})
    flow = float(attrs.get("flow_vol", 0.0) or 0.0)
    width = 1.0 + min(5.0, flow / 50.0)
    edge_traces.append(
        go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            line=dict(width=width, color="#9ca3af"),
            hoverinfo="none",
            mode="lines",
            showlegend=False,
        )
    )

node_x = []
node_y = []
node_color = []
node_text = []
node_size = []
node_ids = []

color_map = {"Safe": "#22c55e", "Warning": "#f59e0b", "Critical": "#ef4444"}

for node_id, attrs in graph.nodes(data=True):
    x, y = pos[node_id]
    node_ids.append(node_id)
    node_x.append(x)
    node_y.append(y)
    node_class = str(attrs.get("predicted_class", "Safe"))
    node_color.append(color_map.get(node_class, "#60a5fa"))
    corr_rate = float(attrs.get("corrosion_rate_mm_yr", 0.0) or 0.0)
    node_size.append(10 + min(28, corr_rate * 2.4))

    tooltip = (
        f"Node: {node_id}<br>"
        f"Class: {node_class}<br>"
        f"critical_prob: {float(attrs.get('critical_prob', 0.0)):.3f}<br>"
        f"pH: {attrs.get('ph_level', 'N/A')}<br>"
        f"H2S: {attrs.get('h2s_ppm', 'N/A')}<br>"
        f"corr_rate: {attrs.get('corrosion_rate_mm_yr', 'N/A')}"
    )
    node_text.append(tooltip)

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
    hoverinfo="text",
    text=node_text,
    customdata=node_ids,
    marker=dict(size=node_size, color=node_color, line=dict(width=1, color="#111827")),
)

fig = go.Figure(
    data=[*edge_traces, node_trace],
    layout=go.Layout(
        title="Topology Risk Map - Klik Node untuk Diagnosis",
        title_x=0.01,
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=10, r=10, t=50),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#f8fafc",
    ),
)

plotly_events = None
try:
    plotly_events = importlib.import_module("streamlit_plotly_events").plotly_events
except ModuleNotFoundError:
    plotly_events = None

clicked = []
graph_col, panel_col = st.columns([1.7, 1.0])

with graph_col:
    if plotly_events is not None:
        clicked = plotly_events(
            fig,
            click_event=True,
            hover_event=False,
            select_event=False,
            override_height=670,
            key="pipeline_topology_click",
        )
    else:
        st.plotly_chart(fig, width="stretch")
        st.info("Plugin click-event tidak aktif. Gunakan dropdown node di panel kanan sebagai fallback.")

selected_node = None
if clicked:
    latest = clicked[-1]
    curve_no = int(latest.get("curveNumber", -1))
    point_idx = latest.get("pointIndex", latest.get("pointNumber", None))
    # Node trace is added as the last trace after all edge traces.
    if curve_no == len(edge_traces) and point_idx is not None and 0 <= int(point_idx) < len(node_ids):
        selected_node = node_ids[int(point_idx)]

if "selected_node_id" not in st.session_state:
    st.session_state["selected_node_id"] = node_ids[0] if node_ids else None
if selected_node is not None:
    st.session_state["selected_node_id"] = selected_node

if st.session_state["selected_node_id"] is None and node_ids:
    st.session_state["selected_node_id"] = node_ids[0]

st.caption("Warna node: hijau=Safe, oranye=Warning, merah=Critical. Ukuran node sebanding corrosion rate, dan edge merepresentasikan konektivitas aliran.")

with panel_col:
    fallback_node = st.selectbox("Node aktif", options=node_ids, index=node_ids.index(st.session_state["selected_node_id"]) if st.session_state["selected_node_id"] in node_ids else 0)
    st.session_state["selected_node_id"] = fallback_node

    row_df = node_df[node_df["node_id"] == st.session_state["selected_node_id"]].copy()
    if row_df.empty:
        st.warning("Data node tidak ditemukan untuk node terpilih.")
    else:
        selected_row = row_df.iloc[0]
        st.markdown('<div class="ops-card">', unsafe_allow_html=True)
        st.markdown(f"### Node {int(selected_row['node_id'])}")
        st.markdown(f"Status: {_status_pill(str(selected_row.get('predicted_class', 'Safe')))}", unsafe_allow_html=True)

        k1, k2 = st.columns(2)
        k1.metric("Critical Prob", f"{float(selected_row.get('critical_prob', 0.0)):.3f}")
        k2.metric("Priority Tier", str(selected_row.get("priority_tier", "-")))

        st.markdown("**Instruksi cepat operator**")
        actions_df = _build_operator_actions(selected_row)
        if actions_df.empty:
            st.success("Tidak ada deviasi besar. Pertahankan monitoring rutin dan inspeksi berkala.")
        else:
            top_actions = actions_df.head(3).copy()
            for rank, (_, rec) in enumerate(top_actions.iterrows(), start=1):
                st.markdown(
                    f"{rank}. **{rec['feature']}**: {rec['nilai_saat_ini']:.3f} (target {rec['target_operasi']:.3f})"
                )
                st.caption(str(rec["aksi_disarankan"]))

            st.markdown("**Tabel detail perbaikan fitur**")
            st.dataframe(actions_df, width="stretch", hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

        neighbor_edges = edge_df[
            (edge_df["source"] == st.session_state["selected_node_id"])
            | (edge_df["target"] == st.session_state["selected_node_id"])
        ].copy()
        st.markdown("**Koneksi Edge Node Aktif**")
        if neighbor_edges.empty:
            st.info("Node ini tidak memiliki edge pada data saat ini.")
        else:
            st.dataframe(neighbor_edges, width="stretch", hide_index=True)

with st.expander("Lihat data mentah node aktif", expanded=False):
    raw_df = node_df[node_df["node_id"] == st.session_state["selected_node_id"]].copy()
    st.dataframe(raw_df, width="stretch", hide_index=True)
