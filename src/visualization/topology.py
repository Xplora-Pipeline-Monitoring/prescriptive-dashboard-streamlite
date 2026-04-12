import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph


def build_graph_elements():
    nodes = [
        Node(
            id="main_export",
            label="Main Export",
            size=35,
            color="#22c55e",
            font={"color": "#ffffff", "size": 14, "bold": True},
            shape="circle",
            title="Main Export | Status: AMAN",
        ),
        Node(
            id="jalur_alpha",
            label="Jalur Alpha ⚠",
            size=32,
            color="#ef4444",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Jalur Alpha | Status: KRITIS",
        ),
        Node(
            id="jalur_beta",
            label="Jalur Beta ⚡",
            size=32,
            color="#f59e0b",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Jalur Beta | Status: PERINGATAN",
        ),
        Node(
            id="alpha_1",
            label="Alpha-1 ⚠",
            size=28,
            color="#ef4444",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Alpha-1 | Status: KRITIS",
        ),
        Node(
            id="alpha_2",
            label="Alpha-2",
            size=28,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Alpha-2 | Status: AMAN",
        ),
        Node(
            id="jalur_gamma",
            label="Jalur Gamma",
            size=32,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Jalur Gamma | Status: AMAN",
        ),
        Node(
            id="beta_1",
            label="Beta-1",
            size=28,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Beta-1 | Status: AMAN",
        ),
        Node(
            id="beta_2",
            label="Beta-2 ⚡",
            size=28,
            color="#f59e0b",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Beta-2 | Status: PERINGATAN",
        ),
        Node(
            id="alpha_2a",
            label="Alpha-2A",
            size=28,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Alpha-2A | Status: AMAN",
        ),
        Node(
            id="alpha_2b",
            label="Alpha-2B ⚠",
            size=28,
            color="#ef4444",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Alpha-2B | Status: KRITIS",
        ),
    ]

    edges = [
        Edge(source="main_export", target="jalur_alpha", label="", color="#6b7280", width=3),
        Edge(source="main_export", target="jalur_beta", label="", color="#6b7280", width=3),
        Edge(source="main_export", target="jalur_gamma", label="", color="#6b7280", width=2),
        Edge(source="jalur_alpha", target="alpha_1", label="", color="#6b7280", width=2),
        Edge(source="jalur_alpha", target="alpha_2", label="", color="#6b7280", width=2),
        Edge(source="jalur_beta", target="beta_1", label="", color="#6b7280", width=2),
        Edge(source="jalur_beta", target="beta_2", label="", color="#6b7280", width=2),
        Edge(source="alpha_2", target="alpha_2a", label="", color="#6b7280", width=2),
        Edge(source="alpha_2", target="alpha_2b", label="", color="#6b7280", width=2),
    ]

    config = Config(
        width="100%",
        height=420,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#60a5fa",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label", "renderLabel": False},
        d3={"gravity": -400, "linkLength": 180},
    )

    return nodes, edges, config


def render_pipeline_graph() -> None:
    nodes, edges, config = build_graph_elements()
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    if return_value:
        st.session_state.selected_node = return_value
