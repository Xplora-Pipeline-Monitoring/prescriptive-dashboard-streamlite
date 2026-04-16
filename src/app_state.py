from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_loader import (
    has_model_weight,
    load_edge_data,
    load_model_config,
    load_node_data,
    locate_artifact_dir,
    validate_artifacts,
)
from src.explainability import compute_shap_artifacts
from src.inference import load_model, run_inference
from src.rules_engine import apply_operational_rules


@st.cache_data(show_spinner=False)
def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner=False)
def get_artifact_dir() -> Path:
    return locate_artifact_dir(get_project_root())


@st.cache_data(show_spinner=True)
def get_base_artifacts() -> tuple[pd.DataFrame, pd.DataFrame, dict, list[str]]:
    artifact_dir = get_artifact_dir()
    missing = validate_artifacts(artifact_dir)
    if missing:
        raise FileNotFoundError(f"Artefak wajib belum lengkap: {', '.join(missing)}")

    node_df = load_node_data(artifact_dir)
    edge_df = load_edge_data(artifact_dir)
    model_config = load_model_config(artifact_dir)
    return node_df, edge_df, model_config, []


@st.cache_resource(show_spinner=True)
def get_model_resource() -> tuple[object | None, str]:
    artifact_dir = get_artifact_dir()
    if not has_model_weight(artifact_dir):
        return None, "model.pt tidak ditemukan. Inference berjalan dengan mode heuristik."
    return load_model(artifact_dir / "model.pt")


@st.cache_data(show_spinner=True)
def get_prediction_table() -> tuple[pd.DataFrame, dict]:
    node_df, edge_df, model_config, _ = get_base_artifacts()
    model_obj, model_note = get_model_resource()

    infer_result = run_inference(node_df=node_df, edge_df=edge_df, model_config=model_config, model_obj=model_obj)
    final_df = apply_operational_rules(infer_result.predictions)

    meta = {
        "artifact_dir": str(get_artifact_dir()),
        "model_note": model_note,
        "inference_mode": infer_result.mode,
        "warnings": infer_result.warnings,
        "classes": model_config.get("classes", ["Safe", "Warning", "Critical"]),
        "model_config": model_config,
    }
    return final_df, meta


@st.cache_data(show_spinner=True)
def get_explainability_artifacts(n_explain_nodes: int = 18, nsamples: int = 80) -> dict:
    node_df, edge_df, model_config, _ = get_base_artifacts()
    pred_df, _ = get_prediction_table()
    return compute_shap_artifacts(
        node_df=node_df,
        edge_df=edge_df,
        model_config=model_config,
        pred_df=pred_df,
        n_explain_nodes=n_explain_nodes,
        nsamples=nsamples,
    )
