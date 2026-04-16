from __future__ import annotations

import importlib
import os
import uuid
from datetime import datetime

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.graph_utils import build_network_graph
from src.openrouter_analysis import run_node_analysis

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

TOPOLOGY_STYLES = """
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
.ticket-col-header {
    background: linear-gradient(180deg, #fdba74 0%, #fb923c 100%);
    color: #292524;
    font-weight: 700;
    font-size: 0.88rem;
    padding: 0.5rem 0.55rem;
    border-radius: 6px;
    border: 1px solid #ea580c;
    margin: 0 0 0.35rem 0;
    line-height: 1.25;
}
</style>
"""


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
            }
        )

    if not rows:
        return pd.DataFrame(columns=["feature", "nilai_saat_ini", "target_operasi", "severity"])

    return pd.DataFrame(rows).sort_values("severity", ascending=False).reset_index(drop=True)


def _status_pill(predicted_class: str) -> str:
    status_name = str(predicted_class)
    if status_name == "Critical":
        return '<span class="ops-pill pill-critical">Critical</span>'
    if status_name == "Warning":
        return '<span class="ops-pill pill-warning">Warning</span>'
    return '<span class="ops-pill pill-safe">Safe</span>'


JENIS_PERMINTAAN_OPTIONS = (
    "Perbaikan",
    "Pembelian alat dan Penggantian",
)


def _tickets_storage_key(selected_node_session_key: str) -> str:
    return f"{selected_node_session_key}_work_tickets"


def _new_ticket_id() -> str:
    return f"TKT-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def render_topology_risk_section(
    node_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    *,
    plotly_events_key: str,
    selected_node_session_key: str,
) -> None:
    st.markdown(TOPOLOGY_STYLES, unsafe_allow_html=True)

    graph = build_network_graph(node_df=node_df, edge_df=edge_df)

    if graph.number_of_nodes() == 0:
        st.warning("Graf tidak memiliki node untuk divisualisasikan.")
        return

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
    node_ids: list = []

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
            f"Kelas: {node_class}<br>"
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
            title="Peta risiko topologi — klik node untuk diagnosis",
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

    clicked: list = []
    graph_col, panel_col = st.columns([1.7, 1.0])

    with graph_col:
        if plotly_events is not None:
            clicked = plotly_events(
                fig,
                click_event=True,
                hover_event=False,
                select_event=False,
                override_height=670,
                key=plotly_events_key,
            )
        else:
            st.plotly_chart(fig, width="stretch")
            st.info("Plugin click-event tidak aktif. Gunakan dropdown node di panel kanan sebagai fallback.")

    selected_node = None
    if clicked:
        latest = clicked[-1]
        curve_no = int(latest.get("curveNumber", -1))
        point_idx = latest.get("pointIndex", latest.get("pointNumber", None))
        if curve_no == len(edge_traces) and point_idx is not None and 0 <= int(point_idx) < len(node_ids):
            selected_node = node_ids[int(point_idx)]

    if selected_node_session_key not in st.session_state:
        st.session_state[selected_node_session_key] = node_ids[0] if node_ids else None
    if selected_node is not None:
        st.session_state[selected_node_session_key] = selected_node

    if st.session_state[selected_node_session_key] is None and node_ids:
        st.session_state[selected_node_session_key] = node_ids[0]

    st.caption(
        "Warna node: hijau=Safe, oranye=Warning, merah=Critical. Ukuran node sebanding corrosion rate, "
        "dan edge merepresentasikan konektivitas aliran."
    )

    with panel_col:
        fallback_node = st.selectbox(
            "Node aktif",
            options=node_ids,
            index=node_ids.index(st.session_state[selected_node_session_key])
            if st.session_state[selected_node_session_key] in node_ids
            else 0,
        )
        st.session_state[selected_node_session_key] = fallback_node

        row_df = node_df[node_df["node_id"] == st.session_state[selected_node_session_key]].copy()
        if row_df.empty:
            st.warning("Data node tidak ditemukan untuk node terpilih.")
        else:
            selected_row = row_df.iloc[0]
            st.markdown('<div class="ops-card">', unsafe_allow_html=True)
            st.markdown(f"### Node {int(selected_row['node_id'])}")
            st.markdown(
                f"Status: {_status_pill(str(selected_row.get('predicted_class', 'Safe')))}",
                unsafe_allow_html=True,
            )

            k1, k2 = st.columns(2)
            k1.metric("Critical Prob", f"{float(selected_row.get('critical_prob', 0.0)):.3f}")
            k2.metric("Priority Tier", str(selected_row.get("priority_tier", "-")))

            actions_df = _build_operator_actions(selected_row)
            if actions_df.empty:
                st.success("Tidak ada deviasi besar. Pertahankan monitoring rutin dan inspeksi berkala.")
            else:
                st.markdown("**Tabel detail perbaikan fitur**")
                st.dataframe(actions_df, width="stretch", hide_index=True)

                tickets_key = _tickets_storage_key(selected_node_session_key)
                if tickets_key not in st.session_state:
                    st.session_state[tickets_key] = []

                form_open_key = f"{selected_node_session_key}_ticket_form_open"
                if st.button(
                    "Buat Ticket",
                    key=f"{selected_node_session_key}_btn_buat_ticket",
                ):
                    st.session_state[form_open_key] = True

                if st.session_state.get(form_open_key):
                    with st.form(f"{selected_node_session_key}_form_ticket"):
                        st.markdown("**Form tiket baru** (node saat ini)")
                        nama_pembuat = st.text_input(
                            "Nama pembuat tiket",
                            key=f"{selected_node_session_key}_ticket_nama",
                        )
                        tim_dept = st.text_input(
                            "Tim / departemen",
                            key=f"{selected_node_session_key}_ticket_dept",
                        )
                        jenis = st.selectbox(
                            "Jenis permintaan",
                            options=list(JENIS_PERMINTAAN_OPTIONS),
                            key=f"{selected_node_session_key}_ticket_jenis",
                        )
                        c_save, c_cancel = st.columns(2)
                        with c_save:
                            save_ticket = st.form_submit_button("Simpan tiket", type="primary")
                        with c_cancel:
                            cancel_ticket = st.form_submit_button("Batal")

                    if save_ticket:
                        if not str(nama_pembuat).strip():
                            st.error("Nama pembuat tiket wajib diisi.")
                        elif not str(tim_dept).strip():
                            st.error("Tim / departemen wajib diisi.")
                        else:
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            prioritas = str(selected_row.get("priority_tier", "-"))
                            entry = {
                                "ticket_id": _new_ticket_id(),
                                "dibuat_tanggal": now,
                                "node_id": int(selected_row["node_id"]),
                                "jenis_permintaan": jenis,
                                "prioritas": prioritas,
                                "status": "Terbuka",
                                "tim_department": str(tim_dept).strip(),
                                "update_terakhir": now,
                                "nama_pembuat": str(nama_pembuat).strip(),
                            }
                            st.session_state[tickets_key].append(entry)
                            st.session_state[form_open_key] = False
                            st.rerun()

                    if cancel_ticket:
                        st.session_state[form_open_key] = False
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    prev_llm_key = f"{selected_node_session_key}_llm_prev_node"
    ai_md_key = f"{selected_node_session_key}_llm_md"
    ai_for_key = f"{selected_node_session_key}_llm_for_node"

    active_node = st.session_state.get(selected_node_session_key)
    if active_node is not None:
        prev_node = st.session_state.get(prev_llm_key)
        if prev_node != active_node:
            st.session_state[ai_md_key] = None
            st.session_state[ai_for_key] = None
        st.session_state[prev_llm_key] = active_node

    _row_llm = (
        node_df[node_df["node_id"] == active_node].copy()
        if active_node is not None
        else pd.DataFrame()
    )

    with st.expander("Lihat data mentah node aktif", expanded=False):
        raw_df = node_df[node_df["node_id"] == st.session_state[selected_node_session_key]].copy()
        st.dataframe(raw_df, width="stretch", hide_index=True)

    api_key_ok = bool((os.getenv("OPENROUTER_API") or "").strip())
    if not api_key_ok:
        st.warning(
            "Analisis AI membutuhkan `OPENROUTER_API` di file `.env` (lihat `.env.example`). "
            "Tombol akan aktif setelah kunci diisi dan aplikasi dimuat ulang."
        )

    btn_disabled = not api_key_ok or _row_llm.empty
    if st.button(
        "Analisis dengan AI",
        disabled=btn_disabled,
        key=f"{selected_node_session_key}_analisis_ai",
    ):
        if not _row_llm.empty:
            sr = _row_llm.iloc[0]
            deviations = _build_operator_actions(sr)
            with st.spinner("Menghasilkan analisis dengan AI…"):
                md, err = run_node_analysis(
                    node_id=int(sr["node_id"]),
                    predicted_class=str(sr.get("predicted_class", "")),
                    critical_prob=float(sr.get("critical_prob", 0.0)),
                    priority_tier=str(sr.get("priority_tier", "-")),
                    deviations_df=deviations,
                )
            if err:
                st.error(err)
            else:
                st.session_state[ai_md_key] = md
                st.session_state[ai_for_key] = active_node

    if (
        active_node is not None
        and st.session_state.get(ai_for_key) == active_node
        and st.session_state.get(ai_md_key)
    ):
        st.markdown(st.session_state[ai_md_key])
    elif active_node is not None and not _row_llm.empty:
        st.caption("Klik **Analisis dengan AI** untuk menghasilkan penjelasan mendalam untuk node ini.")

    tickets_key = _tickets_storage_key(selected_node_session_key)
    if tickets_key not in st.session_state:
        st.session_state[tickets_key] = []

    st.subheader("Daftar tiket")
    tickets = st.session_state[tickets_key]
    if not tickets:
        st.caption("Belum ada tiket. Buat tiket dari panel kanan setelah ada **Tabel detail perbaikan fitur**.")
    else:
        hdr = st.columns([1.1, 1.25, 0.55, 1.35, 0.55, 0.65, 0.95, 0.9, 1.0, 0.45])
        labels = [
            "Dibuat tanggal",
            "Ticket ID",
            "Node ID",
            "Jenis permintaan",
            "Prioritas",
            "Status",
            "Tim/dept",
            "Pembuat Ticket",
            "Update terakhir",
            "Aksi",
        ]
        for col, label in zip(hdr, labels):
            col.markdown(
                f'<div class="ticket-col-header">{label}</div>',
                unsafe_allow_html=True,
            )

        for t in tickets:
            tid = str(t.get("ticket_id", ""))
            safe_id = tid.replace("-", "_").replace(" ", "_")
            r = st.columns([1.1, 1.25, 0.55, 1.35, 0.55, 0.65, 0.95, 0.9, 1.0, 0.45])
            r[0].write(t.get("dibuat_tanggal", ""))
            r[1].write(tid)
            r[2].write(str(t.get("node_id", "")))
            r[3].write(str(t.get("jenis_permintaan", "")))
            r[4].write(str(t.get("prioritas", "")))
            r[5].write(str(t.get("status", "")))
            r[6].write(str(t.get("tim_department", "")))
            r[7].write(str(t.get("nama_pembuat", "")))
            r[8].write(str(t.get("update_terakhir", "")))
            with r[9]:
                if st.button(
                    "Tutup",
                    key=f"{selected_node_session_key}_tutup_ticket_{safe_id}",
                    help="Hapus tiket dari daftar",
                ):
                    st.session_state[tickets_key] = [
                        x for x in st.session_state[tickets_key] if x.get("ticket_id") != tid
                    ]
                    st.rerun()
