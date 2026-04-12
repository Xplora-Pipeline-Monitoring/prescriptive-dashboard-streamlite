import streamlit as st


def render_header() -> None:
    col_title, col_stats = st.columns([2, 3], gap="large")

    with col_title:
        st.markdown(
            """
        <div class="title-block">
        <div class="title-text">Sistem Pemantauan<br>Integritas Pipa Migas</div>
        <div class="subtitle-text">Pipeline Integrity Monitoring System &nbsp;|&nbsp; Real-time Analytics</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_stats:
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(
                '<div class="stat-card"><div class="stat-label">Total Aset</div>'
                '<div class="stat-value white">10</div></div>',
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                '<div class="stat-card"><div class="stat-label">Status Kritis</div>'
                '<div class="stat-value red">3</div></div>',
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                '<div class="stat-card"><div class="stat-label">Status Peringatan</div>'
                '<div class="stat-value yellow">2</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
