Perkembangan UI-nya sudah terlihat sangat rapi dan profesional! Mengganti tombol kontrol dengan visualisasi data (*chart*) memang keputusan UX yang jauh lebih baik untuk *dashboard* analitik preskriptif, karena juri ingin melihat data pendukung dari metrik tersebut.

Berikut adalah *prompt* lengkap dan spesifik yang bisa langsung kamu salin dan *paste* ke Cursor untuk melakukan perubahan tersebut:

***

**Prompt untuk Cursor:**

> Tolong modifikasi kode antarmuka Streamlit saat ini dengan melakukan pembaruan di area bawah metrik operasional.
> 
> **1. Hapus Elemen UI:**
> Hapus baris kode yang merender tombol **"Sembunyikan Metrik"** dan tombol **"Reset Pilihan"** beserta *layout* kolom yang membungkusnya.
> 
> **2. Tambahkan Grafik Tren Degradasi (Sebagai Pengganti):**
> Tepat di bawah bagian "Metrik Operasional", tambahkan grafik garis interaktif untuk memvisualisasikan degradasi pipa. Gunakan `st.plotly_chart` (sangat direkomendasikan untuk tampilan profesional) atau `st.line_chart` bawaan Streamlit.
> 
> **Spesifikasi Grafik:**
> * **Judul:** "Tren Degradasi Ketebalan Dinding"
> * **Sumbu X:** Waktu (Bulan ke-0 hingga ke-12).
> * **Sumbu Y:** Ketebalan (mm).
> * **Data Garis (Buat *dummy data* / simulasi untuk node yang sedang dipilih):**
>     * **Garis 1 (Ketebalan Aktual):** Garis berwarna biru yang trennya menurun dari waktu ke waktu (misalnya dari 6.4 mm turun perlahan ke 4.7 mm).
>     * **Garis 2 (Batas Minimum/Threshold):** Garis lurus horizontal berwarna merah (misalnya di angka 5.0 mm). Ini merepresentasikan batas kritis di mana tindakan preskriptif harus diambil.
> 
> **3. Tata Letak:**
> Posisikan grafik ini di atas *expander* "Ringkasan Metrik Seluruh Aset". Pastikan grafik mengambil lebar penuh (*use_container_width=True*).

> **Instruksi Tambahan untuk Grafik:**
> Pastikan *dataframe* atau data simulasi untuk grafik ini di-generate secara dinamis di dalam masing-masing blok `if/elif` (Skenario B, C, dan D). 
> * **Jika Node Kritis (Alpha-1) dipilih:** Garis ketebalan harus menukik tajam ke bawah dan menembus garis batas merah dalam waktu dekat.
> * **Jika Node Aman (Alpha-2) dipilih:** Garis ketebalan harus sangat landai dan berada jauh di atas garis batas merah.
> * **Jika Node Peringatan (Beta) dipilih:** Garis ketebalan menurun moderat dan hampir menyentuh batas merah di bulan ke-12.


# Prompt Kedua

Ini adalah langkah ekspansi yang sangat bagus! Menambahkan lebih banyak aset (menjadi 10 *nodes*) akan membuat *dashboard* terlihat jauh lebih realistis dan kompleks di mata juri, benar-benar mencerminkan sebuah *Command Center* untuk *pipeline network* yang besar.

Karena kerangka kode (`if/elif/else`) yang sudah ada sangat dinamis, kita hanya perlu meminta Cursor untuk **menambahkan data *node*, *edge*, dan memperbarui daftar referensi (Set/Dictionary)**. Logika grafiknya akan otomatis menyesuaikan!

Berikut adalah *prompt* lengkap dan terstruktur yang bisa kamu salin ke Cursor:

***

**Prompt untuk Cursor:**

> Tolong modifikasi kode Streamlit ini untuk memperluas topologi jaringan pipa dari 5 aset menjadi 10 aset. Semua logika dinamis (grafik dan tab preskriptif) yang sudah ada biarkan tetap berjalan, cukup perbarui data jaringan dan daftar asetnya.
> 
> Lakukan perubahan pada bagian-bagian berikut:
> 
> **1. Perbarui Angka Statistik di Header (col_stats):**
> * Total Aset: Ubah dari 5 menjadi **10**
> * Status Kritis: Ubah dari 2 menjadi **3**
> * Status Peringatan: Ubah dari 1 menjadi **2**
> 
> **2. Tambahkan 5 Node Baru ke dalam list `nodes`:**
> Tambahkan konfigurasi `Node` berikut (sesuaikan *style*-nya dengan *node* yang sudah ada):
> * `id="jalur_gamma"`, `label="Jalur Gamma"`, *shape*="circle", warna hijau (`#22c55e`), status AMAN.
> * `id="beta_1"`, `label="Beta-1"`, *shape*="circle", warna hijau (`#22c55e`), status AMAN.
> * `id="beta_2"`, `label="Beta-2 ⚡"`, *shape*="ellipse", warna kuning (`#f59e0b`), status PERINGATAN.
> * `id="alpha_2a"`, `label="Alpha-2A"`, *shape*="circle", warna hijau (`#22c55e`), status AMAN.
> * `id="alpha_2b"`, `label="Alpha-2B ⚠"`, *shape*="ellipse", warna merah (`#ef4444`), status KRITIS.
> 
> **3. Tambahkan Edge (Koneksi) Baru ke dalam list `edges`:**
> Buat percabangan baru agar membentuk struktur pohon yang lebih dalam:
> * `main_export` -> `jalur_gamma`
> * `jalur_beta` -> `beta_1`
> * `jalur_beta` -> `beta_2`
> * `alpha_2` -> `alpha_2a`
> * `alpha_2` -> `alpha_2b`
> *(Gunakan warna `#6b7280` dan width=2 untuk edge turunan baru ini).*
> 
> **4. Perbarui Set dan Dictionary Status:**
> Perbarui variabel pengelompokan *node* agar logika dinamis di bawahnya bisa merespons *node* baru ini:
> * Tambahkan ke `SAFE_NODES`: `"jalur_gamma", "beta_1", "alpha_2a"`
> * Tambahkan ke `CRITICAL_NODES`: `"alpha_2b"`
> * Tambahkan ke `WARNING_NODES`: `"beta_2"`
> * Tambahkan label yang sesuai ke dalam dictionary `NODE_LABELS`.
> 
> **5. Perbarui Tabel "Ringkasan Metrik Seluruh Aset":**
> Di bagian paling bawah (dalam `st.expander`), tambahkan 5 baris data baru ini ke dalam definisi `st.dataframe`:
> * Jalur Gamma (Aman, Laju: 0.2 mm/thn, Tebal: 9.5, Sisa Umur: 9.0 Thn)
> * Beta-1 (Aman, Laju: 0.4 mm/thn, Tebal: 8.8, Sisa Umur: 7.5 Thn)
> * Beta-2 (Peringatan, Laju: 0.8 mm/thn, Tebal: 6.5, Sisa Umur: 2.5 Thn)
> * Alpha-2A (Aman, Laju: 0.2 mm/thn, Tebal: 9.0, Sisa Umur: 8.0 Thn)
> * Alpha-2B (Kritis, Laju: 1.8 mm/thn, Tebal: 3.5, Sisa Umur: 40 Hari)
> 
> Pastikan tidak merusak indentasi dan blok kode logika `if/elif` yang memuat grafik Plotly.

***