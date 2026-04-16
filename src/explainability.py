from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.feature_actions import get_feature_action
from src.graph_utils import build_edge_index
from src.preprocess import standardize_features, validate_and_prepare_features


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def _audit_flag(actual_cls: str, pred_cls: str) -> str:
    if actual_cls == pred_cls:
        return "cocok"
    if actual_cls == "Critical" and pred_cls != "Critical":
        return "critical_terlewat"
    if actual_cls != "Critical" and pred_cls == "Critical":
        return "peringatan_berlebih"
    return "kelas_tidak_cocok"


def _recommend_from_driver(feature: str, direction: str) -> str:
    base = get_feature_action(feature)
    if direction == "positive":
        return f"{feature}: mendorong risiko naik. {base}"
    return f"{feature}: menahan risiko. Pertahankan kontrol operasional saat ini."


def _select_explain_nodes(pred_df: pd.DataFrame, n_total: int = 18) -> list[int]:
    if "node_id" not in pred_df.columns:
        pred_df = pred_df.copy()
        pred_df["node_id"] = pred_df.index

    selected: list[int] = []
    cls_order = ["Critical", "Warning", "Safe"]
    quota = max(2, n_total // 6)

    for cls in cls_order:
        cls_df = pred_df[pred_df["predicted_class"] == cls].sort_values("critical_prob", ascending=False)
        selected.extend(cls_df["node_id"].astype(int).head(quota).tolist())

    overall = pred_df.sort_values("critical_prob", ascending=False)["node_id"].astype(int).tolist()
    for nid in overall:
        if nid not in selected:
            selected.append(nid)
        if len(selected) >= n_total:
            break

    return selected[:n_total]


def _select_background(X_scaled: np.ndarray, pred_df: pd.DataFrame, n_bg: int = 12) -> np.ndarray:
    if "node_id" not in pred_df.columns:
        pred_df = pred_df.copy()
        pred_df["node_id"] = pred_df.index

    picks: list[int] = []
    for cls in ["Safe", "Warning", "Critical"]:
        cls_df = pred_df[pred_df["predicted_class"] == cls].sort_values("critical_prob")
        if cls_df.empty:
            continue
        mid = len(cls_df) // 2
        for idx in [0, mid, len(cls_df) - 1]:
            picks.append(int(cls_df.iloc[idx]["node_id"]))

    picks = list(dict.fromkeys(picks))[:n_bg]
    if not picks:
        picks = list(range(min(n_bg, X_scaled.shape[0])))

    return X_scaled[np.array(picks, dtype=int)]


def _make_proxy_predict_fn(base_x: np.ndarray, node_id: int, feature_columns: list[str]):
    idx = {name: i for i, name in enumerate(feature_columns)}

    def _col(name: str, default: float = 0.0) -> np.ndarray:
        return base_x[:, idx[name]] if name in idx else np.full(base_x.shape[0], default, dtype=np.float32)

    def predict_critical_proba(x_batch: np.ndarray) -> np.ndarray:
        x_batch = np.asarray(x_batch, dtype=np.float32)
        outputs: list[float] = []
        for row in x_batch:
            x_temp = base_x.copy()
            x_temp[node_id, :] = row

            press = x_temp[node_id, idx.get("press_avg", 0)] if "press_avg" in idx else 0.0
            ph = x_temp[node_id, idx.get("ph_level", 0)] if "ph_level" in idx else 0.0
            pco2 = x_temp[node_id, idx.get("pco2_psi", 0)] if "pco2_psi" in idx else 0.0
            h2s = x_temp[node_id, idx.get("h2s_ppm", 0)] if "h2s_ppm" in idx else 0.0
            chloride = x_temp[node_id, idx.get("chloride_ppm", 0)] if "chloride_ppm" in idx else 0.0
            inhibitor = x_temp[node_id, idx.get("inhibitor_ppm", 0)] if "inhibitor_ppm" in idx else 0.0
            corr = x_temp[node_id, idx.get("corrosion_rate_mm_yr", 0)] if "corrosion_rate_mm_yr" in idx else 0.0
            flow = x_temp[node_id, idx.get("in_flow_mean", 0)] if "in_flow_mean" in idx else 0.0

            score = 0.45 * press - 0.40 * ph + 0.40 * pco2 + 0.45 * h2s + 0.25 * chloride - 0.35 * inhibitor + 0.55 * corr + 0.18 * flow
            outputs.append(float(_sigmoid(np.array([score]))[0]))
        return np.array(outputs, dtype=np.float32)

    return predict_critical_proba


def compute_shap_artifacts(
    node_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    model_config: dict[str, Any],
    pred_df: pd.DataFrame,
    n_explain_nodes: int = 18,
    nsamples: int = 80,
) -> dict[str, Any]:
    feature_columns = model_config.get("feature_columns", [])
    if not feature_columns:
        raise ValueError("feature_columns tidak ditemukan di model_config.json")

    feature_df, _ = validate_and_prepare_features(node_df, feature_columns)
    X_scaled = standardize_features(feature_df)
    _ = build_edge_index(node_df, edge_df)  # kept for parity with graph pipeline

    explain_nodes = _select_explain_nodes(pred_df, n_total=n_explain_nodes)
    explain_nodes_np = np.array(explain_nodes, dtype=int)
    X_explain = X_scaled[explain_nodes_np]
    background = _select_background(X_scaled, pred_df, n_bg=12)

    shap_mode = "kernel_proxy"
    try:
        import shap

        shap_rows: list[np.ndarray] = []
        base_x_np = X_scaled.copy()
        for node_id in explain_nodes:
            predict_fn = _make_proxy_predict_fn(base_x_np, int(node_id), feature_columns)
            explainer = shap.KernelExplainer(predict_fn, background)
            sv = explainer.shap_values(X_scaled[node_id: node_id + 1], nsamples=nsamples)
            sv_arr = np.array(sv).reshape(1, -1)
            shap_rows.append(sv_arr[0])

        shap_values_matrix = np.vstack(shap_rows)
    except ModuleNotFoundError:
        shap_mode = "fallback_no_shap_pkg"
        centered = X_explain - X_explain.mean(axis=0, keepdims=True)
        crit = pred_df.set_index("node_id").loc[explain_nodes, "critical_prob"].to_numpy(dtype=np.float32)
        crit_center = crit - crit.mean()
        numer = centered * crit_center[:, None]
        shap_values_matrix = numer / max(len(crit), 1)

    mean_abs_shap = np.abs(shap_values_matrix).mean(axis=0)
    shap_importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "mean_abs_shap": mean_abs_shap,
            "mean_shap": shap_values_matrix.mean(axis=0),
        }
    ).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

    node_lookup = pred_df.copy()
    if "node_id" not in node_lookup.columns:
        node_lookup["node_id"] = node_lookup.index
    node_lookup = node_lookup.set_index("node_id")

    display_feature_cols = [
        "temp_avg",
        "press_avg",
        "ph_level",
        "pco2_psi",
        "h2s_ppm",
        "chloride_ppm",
        "inhibitor_ppm",
        "segment_age",
        "wall_thick_nom",
        "corrosion_rate_mm_yr",
    ]

    rows: list[dict[str, Any]] = []
    base_node = node_df.set_index("node_id")

    for local_i, node_id in enumerate(explain_nodes):
        shap_vec = shap_values_matrix[local_i]
        abs_order = np.argsort(np.abs(shap_vec))[::-1][:3]

        top_drivers: list[str] = []
        recs: list[str] = []
        for idx_f in abs_order:
            feat = feature_columns[idx_f]
            shap_val = float(shap_vec[idx_f])
            direction = "positive" if shap_val >= 0 else "negative"
            top_drivers.append(f"{feat} ({shap_val:+.4f})")
            recs.append(_recommend_from_driver(feat, direction))

        base_row: dict[str, Any] = {"node_id": int(node_id)}
        if int(node_id) in base_node.index:
            raw = base_node.loc[int(node_id)]
            if isinstance(raw, pd.DataFrame):
                raw = raw.iloc[0]
            for col in ["risk_class"] + display_feature_cols:
                base_row[col] = raw[col] if col in raw.index else np.nan

        pred_row = node_lookup.loc[int(node_id)]
        if isinstance(pred_row, pd.DataFrame):
            pred_row = pred_row.iloc[0]
        pred_cls = str(pred_row.get("predicted_class", "Safe"))
        actual_cls = str(base_row.get("risk_class", pred_cls))

        base_row.update(
            {
                "pred_risk_class": pred_cls,
                "critical_prob": float(pred_row.get("critical_prob", 0.0)),
                "top3_shap_drivers": " | ".join(top_drivers),
                "rekomendasi_per_node": " | ".join(recs),
                "audit_flag": _audit_flag(actual_cls, pred_cls),
            }
        )
        rows.append(base_row)

    per_node_shap_df = pd.DataFrame(rows).sort_values("critical_prob", ascending=False).reset_index(drop=True)

    return {
        "shap_mode": shap_mode,
        "feature_columns": feature_columns,
        "explain_nodes": explain_nodes,
        "X_explain": X_explain,
        "shap_values_matrix": shap_values_matrix,
        "shap_importance_df": shap_importance_df,
        "per_node_shap_df": per_node_shap_df,
    }
