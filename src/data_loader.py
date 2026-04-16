from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REQUIRED_FILES = ["node_data.csv", "edge_data.csv", "model_config.json"]
OPTIONAL_FILES = ["model.pt"]


def locate_artifact_dir(project_root: Path) -> Path:
    """Find artifact directory by priority: artifacts/, then output/."""
    candidates = [project_root / "artifacts", project_root / "output"]
    for directory in candidates:
        if directory.exists() and directory.is_dir():
            return directory
    raise FileNotFoundError("Folder artifacts/ atau output/ tidak ditemukan.")


def validate_artifacts(artifact_dir: Path) -> list[str]:
    missing = []
    for filename in REQUIRED_FILES:
        if not (artifact_dir / filename).exists():
            missing.append(filename)
    return missing


def load_node_data(artifact_dir: Path) -> pd.DataFrame:
    return pd.read_csv(artifact_dir / "node_data.csv")


def load_edge_data(artifact_dir: Path) -> pd.DataFrame:
    return pd.read_csv(artifact_dir / "edge_data.csv")


def load_model_config(artifact_dir: Path) -> dict:
    with (artifact_dir / "model_config.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def has_model_weight(artifact_dir: Path) -> bool:
    return (artifact_dir / "model.pt").exists()
