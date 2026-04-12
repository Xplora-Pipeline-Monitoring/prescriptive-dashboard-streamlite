import streamlit as st


def inject_app_styles() -> None:
    st.markdown(
        """
    <style>
    .main { background-color: #0e1117; }
    .title-block {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px 18px;
        border: 1px solid #e5e7eb;
    }
    .title-text {
        font-size: 2rem;
        font-weight: 800;
        color: #000000;
        line-height: 1.2;
    }
    .subtitle-text {
        font-size: 0.9rem;
        color: #000000;
        opacity: 0.75;
        margin-top: 2px;
    }
    .stat-card {
        background: #1a2035;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        border: 1px solid #2a3550;
    }
    .stat-label {
        font-size: 0.75rem;
        color: #8b9ab5;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .stat-value { font-size: 2rem; font-weight: 700; }
    .stat-value.white  { color: #f0f2f6; }
    .stat-value.red    { color: #ef4444; }
    .stat-value.yellow { color: #f59e0b; }
    .banner-red {
        background: linear-gradient(90deg, #7f1d1d, #991b1b);
        border: 1px solid #ef4444;
        border-radius: 10px;
        padding: 16px 24px;
        color: #fecaca;
        font-size: 1.1rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 16px;
    }
    .banner-yellow {
        background: linear-gradient(90deg, #78350f, #92400e);
        border: 1px solid #f59e0b;
        border-radius: 10px;
        padding: 14px 24px;
        color: #fde68a;
        font-size: 1rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 16px;
    }
    .banner-green {
        background: linear-gradient(90deg, #064e3b, #065f46);
        border: 1px solid #10b981;
        border-radius: 10px;
        padding: 14px 24px;
        color: #a7f3d0;
        font-size: 1rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 16px;
    }
    .instruction-text {
        background: #1a2035;
        border-left: 4px solid #3b82f6;
        border-radius: 6px;
        padding: 12px 18px;
        color: #93c5fd;
        font-size: 0.95rem;
        margin: 12px 0;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #2a3550;
        margin: 20px 0;
    }
    div[data-testid="stButton"] > button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
