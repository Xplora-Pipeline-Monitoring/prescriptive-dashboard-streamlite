from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import pandas as pd


def build_edge_index(node_df: pd.DataFrame, edge_df: pd.DataFrame) -> np.ndarray:
    """Build [2, E] edge index array from node_id/source/target columns."""
    if "node_id" not in node_df.columns:
        raise ValueError("node_data.csv wajib memiliki kolom 'node_id'.")
    if "source" not in edge_df.columns or "target" not in edge_df.columns:
        raise ValueError("edge_data.csv wajib memiliki kolom 'source' dan 'target'.")

    node_ids = node_df["node_id"].tolist()
    node_to_idx = {node_id: idx for idx, node_id in enumerate(node_ids)}

    valid_edges: list[tuple[int, int]] = []
    for _, row in edge_df.iterrows():
        src = row["source"]
        dst = row["target"]
        if src in node_to_idx and dst in node_to_idx:
            valid_edges.append((node_to_idx[src], node_to_idx[dst]))

    if not valid_edges:
        return np.zeros((2, 0), dtype=np.int64)

    edge_arr = np.array(valid_edges, dtype=np.int64)
    return edge_arr.T


def build_network_graph(node_df: pd.DataFrame, edge_df: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph()

    for _, row in node_df.iterrows():
        graph.add_node(row["node_id"], **row.to_dict())

    for _, row in edge_df.iterrows():
        graph.add_edge(row["source"], row["target"], **row.to_dict())

    return graph


def get_node_metric(node_attrs: dict[str, Any], col: str, default: float = 0.0) -> float:
    val = node_attrs.get(col, default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
