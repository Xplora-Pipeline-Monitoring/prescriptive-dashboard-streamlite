# PipelineGuard AI - Prescriptive Dashboard Streamlit

Aplikasi ini adalah implementasi operasional dari notebook analisis korosi berbasis graph (`notebook/pipelineguard_ai_graph_based_corrosion_risk_prediction.ipynb`) untuk kebutuhan tim integrity engineer dan corrosion engineer.

Aplikasi ini dikembangkan dari notebook jupyter : 
https://colab.research.google.com/drive/1b_jLBjgjYW2QdUDLmkAttACTa6TF3DwV#scrollTo=fc4c0c39

## Tujuan Aplikasi

- Menampilkan risiko korosi per segmen pipa secara interaktif.
- Memberikan prioritas inspeksi P1/P2/P3 beserta rekomendasi aksi.
- Menyediakan konteks validasi model (standard test vs stress test) untuk keputusan yang lebih defensible.

## Struktur Proyek

```text
prescriptive-dashboard-streamlite/
|-- app.py
|-- pages/
|   |-- 1_Dashboard_Risiko.py
|   |-- 2_Peta_Jaringan.py
|   |-- 3_Rekomendasi_Operasional.py
|   `-- 4_Validasi_dan_Metrik.py
|-- artifacts/
|   |-- model.pt
|   |-- node_data.csv
|   |-- edge_data.csv
|   `-- model_config.json
|-- output/
|   `-- (gambar hasil analisis)
|-- src/
|   |-- app_state.py
|   |-- data_loader.py
|   |-- inference.py
|   |-- preprocess.py
|   |-- graph_utils.py
|   `-- rules_engine.py
|-- requirements.txt
`-- README.md
```

## Artefak Minimal

Pastikan file berikut tersedia di `artifacts/` (atau fallback `output/` untuk data tertentu):

- `model.pt`
- `model_config.json`
- `node_data.csv`
- `edge_data.csv`

## Aturan Prioritas Operasional

- P1: prediksi `Critical` atau `critical_prob >= 0.60`
  - Aksi: UT segera, optimasi inhibitor, review tekanan
  - Target respons: `<=24 jam`
- P2: prediksi `Warning` atau `critical_prob >= 0.35`
  - Aksi: inspeksi targeted, penyesuaian kimia
  - Target respons: `<=7 hari`
- P3: selain itu
  - Aksi: monitoring rutin
  - Target respons: `<=30 hari`

## Instalasi dan Menjalankan Lokal

1. Buat virtual environment (opsional jika belum ada):

```bash
python -m venv .venv
```

2. Aktivasi environment:

```bash
# Windows
.venv\Scripts\activate
```

3. Install dependensi:

```bash
pip install -r requirements.txt
```

4. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Halaman Aplikasi

1. Dashboard Risiko
	- KPI critical, P1, dan distribusi kelas.
2. Peta Jaringan
	- Visual graph node-edge dengan tooltip teknis (pH, H2S, corrosion rate, critical probability).
3. Rekomendasi Operasional
	- Top-N prioritas inspeksi, filter area/tier, dan ekspor CSV action plan.
4. Validasi dan Metrik
	- Standard test vs stress test, multi-seed summary, dan batasan model.
5. Explainability SHAP
  - Global driver risiko critical (mean |SHAP|), audit per-node, dan rekomendasi per-driver.

## Checklist Go-Live

- [ ] Artefak model/data terbaca tanpa error.
- [ ] Semua halaman berjalan.
- [ ] Tabel prioritas sesuai aturan P1/P2/P3.
- [ ] Perbandingan standard vs stress tidak kontradiktif.
- [ ] Export CSV action plan berfungsi.
- [ ] Hasil Streamlit tervalidasi konsisten dengan notebook pada input yang sama.

## Catatan Teknis

- Aplikasi memakai cache Streamlit (`st.cache_data` dan `st.cache_resource`) untuk efisiensi.
- Jika `model.pt` tidak dapat dimuat, aplikasi fallback ke inferensi heuristik agar dashboard tetap operasional untuk eksplorasi data.