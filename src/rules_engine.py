from __future__ import annotations

import pandas as pd


ACTION_MAP = {
    "P1": "Immediate UT + inhibitor boost + pressure review",
    "P2": "Targeted inspection + chemistry adjustment",
    "P3": "Routine monitoring + normal PM cycle",
}

SLA_MAP = {
    "P1": "<=24 jam",
    "P2": "<=7 hari",
    "P3": "<=30 hari",
}


def assign_priority(predicted_class: str, critical_prob: float) -> str:
    if predicted_class == "Critical" or critical_prob >= 0.60:
        return "P1"
    if predicted_class == "Warning" or critical_prob >= 0.35:
        return "P2"
    return "P3"


def apply_operational_rules(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["priority_tier"] = out.apply(
        lambda row: assign_priority(
            str(row.get("predicted_class", "Safe")),
            float(row.get("critical_prob", 0.0)),
        ),
        axis=1,
    )
    out["recommended_action"] = out["priority_tier"].map(ACTION_MAP)
    out["target_sla"] = out["priority_tier"].map(SLA_MAP)

    thickness_loss = out.get("thickness_loss_pct", 0.0).astype(float)
    corr_rate = out.get("corrosion_rate_mm_yr", 0.0).astype(float)
    max_corr = max(float(corr_rate.max()), 1e-6)

    out["priority_score"] = (
        0.45 * out.get("critical_prob", 0.0).astype(float)
        + 0.25 * (thickness_loss / 45.0)
        + 0.20 * (corr_rate / max_corr)
        + 0.10 * out.get("propagation_uplift", 0.0).astype(float).clip(lower=0, upper=1)
    )
    out["priority_score"] = out["priority_score"].clip(lower=0.0, upper=1.0)
    return out
