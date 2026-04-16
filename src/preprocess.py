from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


RISK_TERMS = ["acidic", "sour", "chloride", "underdose", "pitting", "critical", "corrosion"]
SAFE_TERMS = ["stable", "protective", "no anomaly", "normal", "good condition"]


def _ensure_nlp_anomaly_score(working: pd.DataFrame) -> None:
    """Compute lightweight TF-IDF risk score when nlp_anomaly_score is unavailable."""
    if "nlp_anomaly_score" in working.columns and not working["nlp_anomaly_score"].isna().all():
        return

    if "inspection_note" not in working.columns:
        working["nlp_anomaly_score"] = 0.5
        return

    notes = working["inspection_note"].fillna("").astype(str)
    if (notes.str.len() == 0).all():
        working["nlp_anomaly_score"] = 0.5
        return

    tfidf = TfidfVectorizer(max_features=64, ngram_range=(1, 2), stop_words="english")
    try:
        sparse_mat = tfidf.fit_transform(notes)
        x_text = np.asarray(sparse_mat.todense())
    except ValueError:
        working["nlp_anomaly_score"] = 0.5
        return

    vocab = tfidf.get_feature_names_out()
    vocab_to_idx = {word: i for i, word in enumerate(vocab)}

    risk_idx = [vocab_to_idx[t] for t in RISK_TERMS if t in vocab_to_idx]
    safe_idx = [vocab_to_idx[t] for t in SAFE_TERMS if t in vocab_to_idx]

    risk_score = x_text[:, risk_idx].mean(axis=1) if risk_idx else np.zeros(len(working))
    safe_score = x_text[:, safe_idx].mean(axis=1) if safe_idx else np.zeros(len(working))
    working["nlp_anomaly_score"] = np.clip(risk_score - safe_score + 0.5, 0, 1)


def _ensure_missing_indicators(working: pd.DataFrame, feature_columns: list[str]) -> None:
    """Generate *_missing features from base columns to avoid noisy warnings."""
    for col in feature_columns:
        if not col.endswith("_missing") or col in working.columns:
            continue
        base_col = col[: -len("_missing")]
        if base_col in working.columns:
            working[col] = pd.to_numeric(working[base_col], errors="coerce").isna().astype(float)
        else:
            working[col] = 0.0


def validate_and_prepare_features(
    df: pd.DataFrame, feature_columns: list[str]
) -> tuple[pd.DataFrame, list[str]]:
    """Ensure feature columns exist and are numeric-ready for inference."""
    working = df.copy()
    warnings: list[str] = []

    _ensure_nlp_anomaly_score(working)
    _ensure_missing_indicators(working, feature_columns)

    for col in feature_columns:
        if col not in working.columns:
            working[col] = 0.0
            if not col.endswith("_missing"):
                warnings.append(f"Kolom fitur '{col}' tidak ditemukan. Diisi default 0.")

    feature_df = working[feature_columns].copy()

    for col in feature_columns:
        feature_df[col] = pd.to_numeric(feature_df[col], errors="coerce")
        if feature_df[col].isna().all():
            feature_df[col] = 0.0
            warnings.append(f"Kolom '{col}' seluruhnya null/non-numeric. Diisi 0.")
        else:
            feature_df[col] = feature_df[col].fillna(feature_df[col].median())

    return feature_df, warnings


def standardize_features(feature_df: pd.DataFrame) -> np.ndarray:
    """Use a stable z-score transform for model-ready numeric matrix."""
    x = feature_df.to_numpy(dtype=np.float32)
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    std[std == 0] = 1.0
    return (x - mean) / std
