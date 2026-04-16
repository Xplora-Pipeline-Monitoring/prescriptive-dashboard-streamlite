from __future__ import annotations

import streamlit as st


def apply_app_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
    --pg-surface: #ffffff;
    --pg-surface-soft: #f8fbff;
    --pg-text-main: #102a43;
    --pg-text-soft: #486581;
    --pg-border: #d9e2ec;
    --pg-safe: #22c55e;
    --pg-warning: #f59e0b;
    --pg-critical: #ef4444;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: var(--pg-text-main);
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top right, #f0f6ff, #f8fbff 30%, #ffffff 65%);
}

.main .block-container {
    padding-top: 1.1rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    letter-spacing: -0.01em;
}

[data-testid="stMetric"] {
    border: 1px solid var(--pg-border);
    border-radius: 12px;
    background: linear-gradient(180deg, #ffffff, #f8fbff);
    padding: 10px 12px;
}

[data-testid="stMetricLabel"] p {
    color: var(--pg-text-soft);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-size: 11px;
}

[data-testid="stMetricValue"] {
    font-weight: 700;
}

.pg-hero {
    border: 1px solid var(--pg-border);
    border-radius: 16px;
    padding: 16px 18px;
    background: radial-gradient(circle at top right, #eaf4ff, #f8fbff 55%, #ffffff);
    margin-bottom: 12px;
}

.pg-hero-title {
    font-size: 24px;
    font-weight: 800;
    color: var(--pg-text-main);
    margin-bottom: 6px;
}

.pg-hero-sub {
    color: var(--pg-text-soft);
    font-size: 14px;
}

.pg-stat-card {
    border: 1px solid var(--pg-border);
    border-radius: 12px;
    padding: 12px 14px;
    background: linear-gradient(180deg, #ffffff, #f8fbff);
    margin-bottom: 8px;
}

.pg-stat-label {
    color: var(--pg-text-soft);
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 4px;
}

.pg-stat-value {
    color: var(--pg-text-main);
    font-size: 22px;
    font-weight: 800;
    line-height: 1.2;
}

.pg-stat-note {
    color: #627d98;
    font-size: 12px;
    margin-top: 6px;
}

@media (max-width: 900px) {
    .main .block-container {
        padding-top: 0.8rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .pg-hero {
        border-radius: 14px;
        padding: 14px;
    }

    .pg-hero-title {
        font-size: 20px;
    }

    .pg-stat-value {
        font-size: 18px;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_page_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
<div class="pg-hero">
  <div class="pg-hero-title">{title}</div>
  <div class="pg-hero-sub">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )