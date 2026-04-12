import streamlit as st

from src.config.settings import MONTHS
from src.domain.nodes import CRITICAL_NODES, NODE_LABELS, SAFE_NODES, WARNING_NODES
from src.visualization.charts import degradation_chart_figure


def render_prescriptive_panel() -> None:
    selected = st.session_state.selected_node

    if selected is None:
        st.markdown(
            "#### Panel Analitik Preskriptif\n"
            "> Belum ada node yang dipilih. Klik salah satu node pada diagram di atas untuk memulai analisis."
        )
        return

    if selected in SAFE_NODES:
        _render_safe_scenario(selected)
    elif selected in CRITICAL_NODES:
        _render_critical_scenario(selected)
    elif selected in WARNING_NODES:
        _render_warning_scenario(selected)
    else:
        st.info(f"Node `{selected}` tidak dikenali. Silakan pilih ulang dari diagram.")

    if selected in SAFE_NODES | CRITICAL_NODES | WARNING_NODES:
        _render_summary_expander()


def _render_safe_scenario(selected: str) -> None:
    label = NODE_LABELS[selected]
    st.markdown(
        f'<div class="banner-green">✅ &nbsp; Aset <strong>{label}</strong> dalam kondisi <strong>AMAN</strong>. '
        "Tidak ada tindakan preskriptif yang diperlukan saat ini.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"#### Metrik Operasional — {label}")
    m1, m2, m3 = st.columns(3)
    if selected == "jalur_gamma":
        m1.metric("Laju Korosi", "0.2 mm/thn", delta="-0.05 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "9.0 Tahun", delta="+1 bln", delta_color="normal")
        m3.metric("Ketebalan Pipa", "9.5 mm", delta="Min: 4.5 mm", delta_color="off")
    elif selected == "beta_1":
        m1.metric("Laju Korosi", "0.4 mm/thn", delta="-0.08 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "7.5 Tahun", delta="+1 bln", delta_color="normal")
        m3.metric("Ketebalan Pipa", "8.8 mm", delta="Min: 4.5 mm", delta_color="off")
    elif selected == "alpha_2a":
        m1.metric("Laju Korosi", "0.2 mm/thn", delta="-0.05 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "8.0 Tahun", delta="+2 bln", delta_color="normal")
        m3.metric("Ketebalan Pipa", "9.0 mm", delta="Min: 4.5 mm", delta_color="off")
    elif selected == "alpha_2":
        m1.metric("Laju Korosi", "0.3 mm/thn", delta="-0.1 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "8.5 Tahun", delta="+2 bln", delta_color="normal")
        m3.metric("Ketebalan Pipa", "9.2 mm", delta="Min: 4.5 mm", delta_color="off")
    else:
        m1.metric("Laju Korosi", "0.3 mm/thn", delta="-0.1 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "8.5 Tahun", delta="+2 bln", delta_color="normal")
        m3.metric("Ketebalan Pipa", "9.2 mm", delta="Min: 4.5 mm", delta_color="off")

    if selected == "alpha_2":
        actual_degradation = [9.05 - 0.015 * i for i in MONTHS]
    elif selected == "jalur_gamma":
        actual_degradation = [9.55 - 0.012 * i for i in MONTHS]
    elif selected == "beta_1":
        actual_degradation = [8.9 - 0.018 * i for i in MONTHS]
    elif selected == "alpha_2a":
        actual_degradation = [9.0 - 0.015 * i for i in MONTHS]
    else:
        actual_degradation = [9.25 - 0.02 * i for i in MONTHS]
    st.plotly_chart(
        degradation_chart_figure(actual_degradation),
        use_container_width=True,
        key=f"chart_safe_{selected}",
    )


def _render_critical_scenario(selected: str) -> None:
    label = NODE_LABELS[selected]
    st.markdown(
        '<div class="banner-red">🚨 &nbsp; TINDAKAN SEGERA DIPERLUKAN — '
        f"Node <strong>{label}</strong> dalam kondisi <strong>KRITIS</strong>!</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"#### Metrik Kritis — {label}")
    m1, m2, m3 = st.columns(3)
    if selected == "alpha_2b":
        m1.metric("Sisa Umur Pipa", "40 Hari", delta="-5 hari", delta_color="inverse")
        m2.metric("Laju Korosi", "1.8 mm/thn", delta="+0.3 mm/thn", delta_color="inverse")
        m3.metric("Ketebalan Pipa", "3.5 mm", delta="Min: 4.5 mm", delta_color="off")
    else:
        m1.metric("Sisa Umur Pipa", "25 Hari", delta="-10 hari", delta_color="inverse")
        m2.metric("Laju Korosi", "2.0 mm/thn", delta="+0.5 mm/thn", delta_color="inverse")
        m3.metric("Ketebalan Pipa", "3.0 mm", delta="Min: 4.5 mm", delta_color="off")

    if selected == "alpha_1":
        actual_degradation = [
            7.2,
            6.75,
            6.1,
            5.45,
            4.85,
            4.35,
            3.95,
            3.6,
            3.35,
            3.15,
            3.0,
            2.9,
            2.8,
        ]
    elif selected == "alpha_2b":
        actual_degradation = [
            6.9,
            6.4,
            5.8,
            5.1,
            4.5,
            4.0,
            3.6,
            3.3,
            3.05,
            2.85,
            2.7,
            2.6,
            2.5,
        ]
    else:
        actual_degradation = [6.55 - 0.12 * i - 0.018 * i * i for i in MONTHS]
    st.plotly_chart(
        degradation_chart_figure(actual_degradation),
        use_container_width=True,
        key=f"chart_critical_{selected}",
    )

    st.markdown("---")
    tab_mitigasi, tab_erp = st.tabs(["🔧 Mitigasi Operasional", "📦 Supply Chain & ERP"])

    with tab_mitigasi:
        st.warning(
            "**Rekomendasi Tindakan Segera:**\n\n"
            "- Tingkatkan dosis inhibitor korosi **+15%** segera **ATAU** turunkan tekanan operasi **-10%** "
            f"pada segmen {label}.\n"
            "- Perkiraan penambahan umur pipa: **+4 bulan**.\n"
            "- Lakukan inspeksi inline (ILI) dalam **7 hari ke depan**."
        )
        if st.button("✅ Terapkan Perubahan Parameter", key=f"btn_mitigasi_{selected}", type="primary"):
            st.success("Parameter operasional telah dikirim ke sistem kontrol. Tim lapangan dihubungi.")

    with tab_erp:
        st.info(
            f"**Simulasi Otomatisasi ERP — {label} Kritis**\n\n"
            '- Stok material pipa **12"** di Gudang Utama: ✅ **Tersedia (20 joint)**\n'
            "- Lead time pengiriman: **3 hari kerja**\n"
            "- Estimasi jadwal penggantian: **minggu depan**\n\n"
            "Pesan material segera untuk memastikan ketersediaan tepat waktu?"
        )
        if st.button('📦 Pesan Material Pipa (Carbon Steel 12")', key=f"btn_erp_{selected}", type="primary"):
            st.success("Purchase Order telah dibuat di sistem ERP. Notifikasi dikirim ke tim pengadaan.")


def _render_warning_scenario(selected: str) -> None:
    label = NODE_LABELS[selected]
    st.markdown(
        f'<div class="banner-yellow">⚠️ &nbsp; Node <strong>{label}</strong> dalam kondisi <strong>PERINGATAN</strong>. '
        "Pemantauan lebih ketat diperlukan.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"#### Metrik Operasional — {label}")
    m1, m2, m3 = st.columns(3)
    if selected == "beta_2":
        m1.metric("Laju Korosi", "0.8 mm/thn", delta="+0.15 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "2.5 Tahun", delta="-2 bln", delta_color="inverse")
        m3.metric("Ketebalan Pipa", "6.5 mm", delta="Min: 4.5 mm", delta_color="off")
    else:
        m1.metric("Laju Korosi", "0.9 mm/thn", delta="+0.2 mm/thn", delta_color="inverse")
        m2.metric("Sisa Umur Pipa", "2.1 Tahun", delta="-3 bln", delta_color="inverse")
        m3.metric("Ketebalan Pipa", "6.1 mm", delta="Min: 4.5 mm", delta_color="off")

    if selected == "beta_2":
        actual_degradation = [6.5 - i * (6.5 - 5.08) / 12 for i in MONTHS]
    else:
        actual_degradation = [6.4 - i * (6.4 - 5.05) / 12 for i in MONTHS]
    st.plotly_chart(
        degradation_chart_figure(actual_degradation),
        use_container_width=True,
        key=f"chart_warning_{selected}",
    )

    st.markdown("---")
    st.warning(
        f"**Rekomendasi Preskriptif:**\n\n"
        f"Sifat korosi pada segmen **{label}** meningkat melampaui ambang batas normal. "
        "Jadwal pemeriksaan berbasis risiko (RBI) harus **ditingkatkan frekuensinya** "
        "menjadi **setiap minggu** mulai bulan depan.\n\n"
        "Pertimbangkan pengujian ultrasonik pada titik TP-07 dan TP-12."
    )
    if st.button("📅 Jadwalkan RBI Inspeksi Mingguan", key=f"btn_rbi_{selected}", type="primary"):
        st.success("Jadwal RBI mingguan telah diperbarui. Notifikasi dikirim ke tim inspeksi.")


def _render_summary_expander() -> None:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    with st.expander("Ringkasan Metrik Seluruh Aset", expanded=False):
        st.dataframe(
            {
                "Node": [
                    "Main Export",
                    "Jalur Alpha",
                    "Jalur Beta",
                    "Jalur Gamma",
                    "Alpha-1",
                    "Alpha-2",
                    "Beta-1",
                    "Beta-2",
                    "Alpha-2A",
                    "Alpha-2B",
                ],
                "Status": [
                    "Aman",
                    "Kritis",
                    "Peringatan",
                    "Aman",
                    "Kritis",
                    "Aman",
                    "Aman",
                    "Peringatan",
                    "Aman",
                    "Kritis",
                ],
                "Laju Korosi": [
                    "0.3 mm/thn",
                    "2.0 mm/thn",
                    "0.9 mm/thn",
                    "0.2 mm/thn",
                    "2.0 mm/thn",
                    "0.3 mm/thn",
                    "0.4 mm/thn",
                    "0.8 mm/thn",
                    "0.2 mm/thn",
                    "1.8 mm/thn",
                ],
                "Ketebalan (mm)": [9.2, 3.0, 6.1, 9.5, 3.0, 9.2, 8.8, 6.5, 9.0, 3.5],
                "Sisa Umur": [
                    "8.5 Thn",
                    "25 Hari",
                    "2.1 Thn",
                    "9.0 Thn",
                    "25 Hari",
                    "8.5 Thn",
                    "7.5 Thn",
                    "2.5 Thn",
                    "8.0 Thn",
                    "40 Hari",
                ],
            },
            use_container_width=True,
            hide_index=True,
        )
