import streamlit as st

from src.ui.analytics import render_prescriptive_panel
from src.ui.header import render_header
from src.ui.styles import inject_app_styles
from src.visualization.topology import render_pipeline_graph


def main() -> None:
    st.set_page_config(
        page_title="Sistem Pemantauan Integritas Pipa Migas",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_app_styles()

    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None

    render_header()

    st.markdown("#### Topologi Jaringan Pipa (Klik Node untuk Analisis)")
    render_pipeline_graph()

    st.markdown(
        '<div class="instruction-text">'
        "&#128270; <strong>Pilih node pipa</strong> pada diagram hierarki di atas untuk melihat analisis preskriptif."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    render_prescriptive_panel()
