from __future__ import annotations


FEATURE_ACTION_MAP = {
    "temp_avg": "Tinjau temperatur operasi (cooling/flow regime) untuk menurunkan akselerasi reaksi korosi.",
    "press_avg": "Kurangi pressure spike dan evaluasi choke/control valve.",
    "ph_level": "Stabilkan pH melalui treatment kimia/buffering.",
    "pco2_psi": "Optimalkan kontrol CO2 dan chemical dosing anti-corrosion.",
    "h2s_ppm": "Tingkatkan sweetening/scavenger untuk menekan sour corrosion.",
    "chloride_ppm": "Kendalikan kadar klorida dan tingkatkan inspeksi pitting.",
    "inhibitor_ppm": "Optimalkan dosis inhibitor dan verifikasi residual inhibitor.",
    "corrosion_rate_mm_yr": "Prioritaskan UT/ILI untuk segmen dengan laju korosi tinggi.",
    "segment_age": "Evaluasi strategi inspeksi berbasis umur segmen.",
    "wall_thick_nom": "Verifikasi margin ketebalan desain terhadap kondisi operasi aktual.",
    "in_flow_mean": "Cek kondisi upstream karena transport fluida dapat memicu propagasi risiko.",
    "in_distance_mean": "Evaluasi segmen dengan jarak alir panjang terhadap akumulasi dampak.",
    "in_elev_abs_mean": "Periksa titik perubahan elevasi untuk potensi stratifikasi cairan/gas.",
    "nlp_anomaly_score": "Tindaklanjuti catatan inspeksi/anomali operator di segmen terkait.",
}


def get_feature_action(feature_name: str) -> str:
    return FEATURE_ACTION_MAP.get(feature_name, "Lakukan verifikasi lapangan untuk fitur ini.")
