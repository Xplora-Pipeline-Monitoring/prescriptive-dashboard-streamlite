"""Titik masuk multipage — jalankan dari folder ini: streamlit run app.py"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="PipelineGuard AI Dashboard",
    page_icon="assets",
    layout="wide",
    initial_sidebar_state="expanded",
)

dashboard = st.Page(
    "pages/1_Dashboard_Risiko.py",
    title="Dashboard Risiko",
    default=True,
)
validasi = st.Page(
    "pages/4_Validasi_dan_Metrik.py",
    title="Evaluasi Metrik Model",
)

pg = st.navigation([dashboard, validasi])
pg.run()
