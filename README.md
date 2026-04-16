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
- Validasi skenario (standard vs stress) dan ringkasan stabilitas multi-seed.
- Explainability SHAP untuk global driver dan audit per node.
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

3. Install dependency:

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

## Alur Pakai Cepat (Operator)

1. Buka halaman `Peta Jaringan` dan pilih node `Warning/Critical`.
2. Cek panel diagnosis fitur untuk tahu parameter paling mendesak diperbaiki.
3. Buka `Rekomendasi Operasional` untuk menyusun dan ekspor action plan.
4. Validasi konteks keputusan di `Validasi dan Metrik`.
5. Gunakan `Explainability SHAP` saat perlu justifikasi berbasis driver fitur.

## Ringkasan Halaman

1. **Dashboard Risiko**
   - KPI utama, distribusi kelas, histogram probabilitas critical, dan diagnostik fitur.
2. **Peta Jaringan**
   - Topology node-edge interaktif, diagnosis fitur per node, dan detail edge sekitar node aktif.
3. **Rekomendasi Operasional**
   - Top-N prioritas inspeksi, filter area/tier, tabel prioritas, dan ekspor CSV.
4. **Validasi dan Metrik**
   - Perbandingan standard vs stress, dampak propagasi, dan ringkasan multi-seed.
5. **Explainability SHAP**
   - Top global SHAP drivers, audit per-node, serta rekomendasi per node.

## Checklist Sebelum Go-Live

- [ ] Artefak di `artifacts/` lengkap dan terbaca.
- [ ] Semua halaman terbuka tanpa error runtime.
- [ ] Distribusi kelas dan prioritas konsisten dengan baseline notebook.
- [ ] Export CSV action plan berhasil.
- [ ] Hasil validasi standard vs stress masuk akal secara domain.
- [ ] Penjelasan SHAP dapat dipakai untuk justifikasi keputusan operasional.

## Catatan Teknis

- App state memakai cache Streamlit (`st.cache_data` dan `st.cache_resource`) untuk efisiensi.
- Preprocessing mendukung auto-generated missing indicators dan NLP anomaly score berbasis TF-IDF.
- Tema UI global terletak di `src/ui_theme.py` untuk menjaga konsistensi desain lintas halaman.