# PipelineGuard AI - Prescriptive Dashboard Streamlit

Dashboard Streamlit untuk operasional risiko korosi berbasis graph, diturunkan dari pipeline notebook:

- Notebook lokal: `notebook/pipelineguard_ai_graph_based_corrosion_risk_prediction.ipynb`
- Referensi Colab: https://colab.research.google.com/drive/1b_jLBjgjYW2QdUDLmkAttACTa6TF3DwV#scrollTo=fc4c0c39

Fokus aplikasi ini adalah membantu tim integrity/corrosion engineer mengambil keputusan inspeksi yang cepat, terukur, dan mudah dijelaskan.

## Ringkasan Fitur

- Prediksi risiko per segmen pipa (`Safe`, `Warning`, `Critical`).
- Prioritas inspeksi operasional (`P1`, `P2`, `P3`) berbasis skor risiko.
- Peta jaringan interaktif dengan diagnosis fitur per node.
- Rekomendasi operasional yang bisa diekspor ke CSV.
- Evaluasi skenario (uji standar vs uji stress) dan ringkasan stabilitas multi-seed.
- Penjelasan SHAP untuk penggerak global dan audit per node.
- UI modern dan konsisten lintas halaman (tema global + kartu metrik responsif).

## Struktur Proyek

```text
prescriptive-dashboard-streamlite/
|-- app.py
|-- pages/
|   |-- 1_Dashboard_Risiko.py
|   |-- 2_Peta_Jaringan.py
|   |-- 3_Rekomendasi_Operasional.py
|   |-- 4_Validasi_dan_Metrik.py
|   `-- 5_Explainability_SHAP.py
|-- artifacts/
|   |-- model.pt
|   |-- model_config.json
|   |-- node_data.csv
|   `-- edge_data.csv
|-- notebook/
|   `-- pipelineguard_ai_graph_based_corrosion_risk_prediction.ipynb
|-- output/
|-- src/
|   |-- __init__.py
|   |-- app_state.py
|   |-- data_loader.py
|   |-- explainability.py
|   |-- graph_utils.py
|   |-- inference.py
|   |-- preprocess.py
|   |-- rules_engine.py
|   `-- ui_theme.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

## Kebutuhan Artefak

Minimal file berikut harus tersedia di folder `artifacts/`:

- `model.pt`
- `model_config.json`
- `node_data.csv`
- `edge_data.csv`

Jika model tidak dapat dimuat, aplikasi otomatis fallback ke mode inferensi heuristik supaya dashboard tetap bisa dipakai untuk eksplorasi.

## Aturan Prioritas Operasional

- `P1`: prediksi `Critical` atau `critical_prob >= 0.60`
  - Target SLA: `<= 24 jam`
- `P2`: prediksi `Warning` atau `critical_prob >= 0.35`
  - Target SLA: `<= 7 hari`
- `P3`: selain itu
  - Target SLA: `<= 30 hari`

## Setup Lokal (Windows)

1. Buat virtual environment:

```bash
python -m venv .venv
```

2. Aktivasi environment:

```bash
.venv\Scripts\activate
```

3. Pasang dependensi:

```bash
pip install -r requirements.txt
```

4. Jalankan aplikasi:

```bash
streamlit run app.py
```

5. (Opsional) Jalankan headless smoke test:

```bash
streamlit run app.py --server.headless true --server.port 8510
```

## Alur pakai cepat (operator)

1. Buka **Dashboard Risiko**: tinjau KPI, distribusi kelas, diagnostik fitur, tabel risiko, dan peta topologi interaktif (diagnosis per node di bawah tabel).
2. Gunakan **Evaluasi Metrik Model** untuk membandingkan uji standar vs uji stress, dampak propagasi, dan ringkasan multi-seed.
3. (Opsional) File `pages/` lain (`Peta Jaringan`, `Rekomendasi Operasional`, `Explainability SHAP`) tetap ada di repo tetapi tidak tampil di menu navigasi saat ini.

## Ringkasan halaman (menu aktif)

1. **Dashboard Risiko**
   - KPI utama, distribusi kelas, diagnostik fitur, tabel risiko per segmen, peta topologi, analisis AI (OpenRouter), dan daftar tiket.
2. **Evaluasi Metrik Model**
   - Perbandingan uji standar vs uji stress, dampak propagasi, ringkasan multi-seed, serta metrik skenario referensi notebook.

## Checklist Sebelum Go-Live

- [ ] Artefak di `artifacts/` lengkap dan terbaca.
- [ ] Semua halaman terbuka tanpa error runtime.
- [ ] Distribusi kelas dan prioritas konsisten dengan baseline notebook.
- [ ] Ekspor CSV rencana tindakan berhasil (jika memakai halaman rekomendasi).
- [ ] Hasil evaluasi uji standar vs uji stress masuk akal secara domain.
- [ ] (Opsional) Penjelasan SHAP dapat dipakai untuk justifikasi keputusan operasional.

## Catatan Teknis

- App state memakai cache Streamlit (`st.cache_data` dan `st.cache_resource`) untuk efisiensi.
- Preprocessing mendukung auto-generated missing indicators dan NLP anomaly score berbasis TF-IDF.
- Tema UI global terletak di `src/ui_theme.py` untuk menjaga konsistensi desain lintas halaman.