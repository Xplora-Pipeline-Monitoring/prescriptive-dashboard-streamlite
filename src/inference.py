from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.graph_utils import build_edge_index
from src.preprocess import standardize_features, validate_and_prepare_features


@dataclass
class InferenceResult:
    predictions: pd.DataFrame
    mode: str
    warnings: list[str]


CLASS_TO_IDX = {"Safe": 0, "Warning": 1, "Critical": 2}
IDX_TO_CLASS = {0: "Safe", 1: "Warning", 2: "Critical"}


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x, axis=1, keepdims=True)
    ex = np.exp(x)
    return ex / np.sum(ex, axis=1, keepdims=True)


def _safe_sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def load_model(model_path: Path):
    try:
        import torch
    except ModuleNotFoundError:
        return None, "Torch tidak tersedia, fallback ke skor heuristik."

    if not model_path.exists():
        return None, "model.pt tidak ditemukan, fallback ke skor heuristik."

    try:
        model_obj = torch.load(model_path, map_location="cpu", weights_only=False)
        return model_obj, "Model torch berhasil dimuat."
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return None, f"Gagal memuat model.pt ({exc}); fallback ke skor heuristik."


def _heuristic_probabilities(base_df: pd.DataFrame) -> np.ndarray:
    ph = base_df.get("ph_level", 7.0).astype(float).to_numpy()
    h2s = base_df.get("h2s_ppm", 0.0).astype(float).to_numpy()
    chloride = base_df.get("chloride_ppm", 0.0).astype(float).to_numpy()
    inhibitor = base_df.get("inhibitor_ppm", 0.0).astype(float).to_numpy()
    corr = base_df.get("corrosion_rate_mm_yr", 0.0).astype(float).to_numpy()
    anom = base_df.get("nlp_anomaly_score", 0.0).astype(float).to_numpy()

    risk_raw = (
        1.8 * corr
        + 0.012 * h2s
        + 0.0012 * chloride
        + 1.2 * np.maximum(0.0, 7.0 - ph)
        + 1.1 * anom
        - 0.01 * inhibitor
    )
    critical = _safe_sigmoid(risk_raw - 1.4)
    warning = np.clip(_safe_sigmoid(risk_raw - 0.8) - critical * 0.55, 0.01, 0.90)
    safe = np.clip(1.0 - (critical + warning), 0.01, 0.98)

    probs = np.column_stack([safe, warning, critical])
    probs = probs / probs.sum(axis=1, keepdims=True)
    return probs


def _probs_from_exported_labels(base_df: pd.DataFrame) -> np.ndarray:
    """Construct calibrated class probabilities from exported notebook labels."""
    if "predicted_risk_class" in base_df.columns:
        cls_series = base_df["predicted_risk_class"].astype(str)
    elif "predicted_label" in base_df.columns:
        cls_series = base_df["predicted_label"].map(IDX_TO_CLASS).fillna("Safe")
    else:
        raise ValueError("Kolom prediksi ekspor tidak tersedia.")

    corr = pd.to_numeric(base_df.get("corrosion_rate_mm_yr", 0.0), errors="coerce").fillna(0.0)
    corr_norm = (corr - corr.min()) / max(corr.max() - corr.min(), 1e-6)

    ph = pd.to_numeric(base_df.get("ph_level", 7.0), errors="coerce").fillna(7.0)
    acidic = (7.0 - ph).clip(lower=0) / 2.0

    base_signal = (0.65 * corr_norm + 0.35 * acidic).clip(0, 1)

    probs = np.zeros((len(base_df), 3), dtype=np.float32)
    for i, cls in enumerate(cls_series):
        s = float(base_signal.iloc[i])
        if cls == "Critical":
            critical = 0.62 + 0.35 * s
            warning = 0.03 + 0.08 * (1.0 - s)
            safe = max(0.01, 1.0 - critical - warning)
        elif cls == "Warning":
            critical = 0.35 + 0.20 * s
            warning = 0.38 + 0.30 * (1.0 - abs(0.5 - s))
            safe = max(0.01, 1.0 - critical - warning)
        else:
            critical = 0.03 + 0.22 * s
            warning = 0.10 + 0.25 * s
            safe = max(0.01, 1.0 - critical - warning)
        probs[i] = [safe, warning, critical]

    probs = probs / probs.sum(axis=1, keepdims=True)
    return probs


def _compute_propagation_uplift(n_nodes: int, edge_index_np: np.ndarray, critical_prob: np.ndarray) -> np.ndarray:
    if edge_index_np.size == 0:
        return np.zeros(n_nodes, dtype=np.float32)

    adjacency = np.zeros((n_nodes, n_nodes), dtype=np.float32)
    src, dst = edge_index_np
    adjacency[src, dst] = 1.0
    adjacency[dst, src] = 1.0

    degree = adjacency.sum(axis=1)
    degree[degree == 0] = 1.0
    neighbor_critical = adjacency @ critical_prob / degree
    uplift = neighbor_critical - critical_prob
    return uplift.astype(np.float32)


def _try_torch_inference(model_obj, x_scaled: np.ndarray, edge_index_np: np.ndarray):
    try:
        import torch

        x_tensor = torch.tensor(x_scaled, dtype=torch.float32)
        edge_tensor = torch.tensor(edge_index_np, dtype=torch.long)

        with torch.no_grad():
            if hasattr(model_obj, "eval"):
                model_obj.eval()

            if callable(model_obj):
                logits = model_obj(x_tensor, edge_tensor)
            elif isinstance(model_obj, dict) and "model" in model_obj and callable(model_obj["model"]):
                logits = model_obj["model"](x_tensor, edge_tensor)
            else:
                return None

            if hasattr(logits, "detach"):
                logits = logits.detach().cpu().numpy()
            if logits.ndim == 1:
                logits = np.expand_dims(logits, axis=0)

            return _softmax(logits)
    except (RuntimeError, TypeError, ValueError, AttributeError):
        return None


def run_inference(node_df: pd.DataFrame, edge_df: pd.DataFrame, model_config: dict, model_obj=None) -> InferenceResult:
    feature_columns = model_config.get("feature_columns", [])
    classes = model_config.get("classes", ["Safe", "Warning", "Critical"])

    feature_df, prep_warnings = validate_and_prepare_features(node_df, feature_columns)
    x_scaled = standardize_features(feature_df)
    edge_index = build_edge_index(node_df, edge_df)

    probs = None
    mode = "heuristic"

    if "predicted_risk_class" in node_df.columns or "predicted_label" in node_df.columns:
        probs = _probs_from_exported_labels(node_df)
        mode = "artifact_export"

    if probs is None and model_obj is not None:
        probs = _try_torch_inference(model_obj, x_scaled, edge_index)
        if probs is not None and probs.shape[1] >= 3:
            mode = "torch_model"

    if probs is None:
        probs = _heuristic_probabilities(node_df)

    # Keep first 3 classes as dashboard target.
    classes = classes[:3] if len(classes) >= 3 else ["Safe", "Warning", "Critical"]
    if probs.shape[1] != 3:
        probs = probs[:, :3]

    result = node_df.copy()
    result["safe_prob"] = probs[:, 0]
    result["warning_prob"] = probs[:, 1]
    result["critical_prob"] = probs[:, 2]

    if "predicted_risk_class" in result.columns:
        result["predicted_class"] = result["predicted_risk_class"].astype(str)
    elif "predicted_label" in result.columns:
        result["predicted_class"] = result["predicted_label"].map(IDX_TO_CLASS).fillna("Safe")
    else:
        pred_idx = np.argmax(probs, axis=1)
        result["predicted_class"] = [classes[i] for i in pred_idx]

    result["predicted_label"] = result["predicted_class"].map(CLASS_TO_IDX).fillna(0).astype(int)
    result["propagation_uplift"] = _compute_propagation_uplift(
        n_nodes=len(result),
        edge_index_np=edge_index,
        critical_prob=result["critical_prob"].to_numpy(dtype=np.float32),
    )

    return InferenceResult(predictions=result, mode=mode, warnings=prep_warnings)


def run_stress_test(df_pred: pd.DataFrame) -> pd.DataFrame:
    """Generate stress-case probabilities by perturbing key corrosion drivers."""
    stressed = df_pred.copy()
    if "h2s_ppm" in stressed.columns:
        stressed["h2s_ppm"] = stressed["h2s_ppm"].astype(float) * 1.2
    if "chloride_ppm" in stressed.columns:
        stressed["chloride_ppm"] = stressed["chloride_ppm"].astype(float) * 1.15
    if "inhibitor_ppm" in stressed.columns:
        stressed["inhibitor_ppm"] = stressed["inhibitor_ppm"].astype(float) * 0.85
    if "ph_level" in stressed.columns:
        stressed["ph_level"] = stressed["ph_level"].astype(float) - 0.25

    probs = _heuristic_probabilities(stressed)
    stressed["safe_prob"] = probs[:, 0]
    stressed["warning_prob"] = probs[:, 1]
    stressed["critical_prob"] = probs[:, 2]
    pred_idx = np.argmax(probs, axis=1)
    classes = ["Safe", "Warning", "Critical"]
    stressed["predicted_class"] = [classes[i] for i in pred_idx]
    return stressed
