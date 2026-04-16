# .gitignore

```
venv/
.env
__pycache__/
*.pyc
.streamlit/secrets.toml
```

# app.py

```python
"""Titik masuk Streamlit — jalankan dari root proyek: streamlit run app.py"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.main import main

main()
```

# export_repo_to_markdown.py

```python
#!/usr/bin/env python3
"""
Ekstrak semua file teks dari sebuah folder ke satu berkas Markdown.

Contoh pakai:
    python export_repo_to_markdown.py -r . -o daftar_code.md

Opsi:
  -r/--root        : folder akar yang ingin diekstrak (default: '.')
  -o/--output      : nama berkas Markdown keluaran (default: 'daftar_code.md')
  --max-bytes      : batas byte per file sebelum dipotong (default: 500_000)
  --include-hidden : sertakan file/dir tersembunyi (default: False)

Catatan:
- Menghindari direktori umum seperti .git, venv, node_modules, __pycache__, dll.
- Mencoba deteksi file biner; hanya file teks yang ditulis.
- File yang melebihi --max-bytes akan dipotong dengan penanda.
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".idea", ".vscode",
    "node_modules", "venv", ".venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".cache", ".next", ".turbo"
}

# Ekstensi -> nama bahasa untuk code fence Markdown
LANG_MAP = {
    # code
    ".py": "python", ".ipynb": "", ".js": "javascript", ".ts": "typescript",
    ".tsx": "tsx", ".jsx": "jsx", ".java": "java", ".kt": "kotlin",
    ".go": "go", ".rb": "ruby", ".rs": "rust", ".php": "php", ".c": "c",
    ".h": "c", ".hpp": "cpp", ".hh": "cpp", ".cpp": "cpp", ".cs": "csharp",
    ".swift": "swift", ".m": "objectivec", ".mm": "objectivec",
    ".scala": "scala", ".pl": "perl", ".lua": "lua", ".r": "r",
    ".sh": "bash", ".bash": "bash", ".zsh": "zsh", ".ps1": "powershell",
    ".bat": "bat", ".cmd": "bat", ".sql": "sql",
    # data / config / markup
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".ini": "ini", ".cfg": "", ".conf": "", ".env": "bash",
    ".md": "markdown", ".markdown": "markdown",
    ".csv": "", ".tsv": "", ".txt": "", ".log": "",
    ".html": "html", ".htm": "html", ".css": "css", ".scss": "scss",
    ".xml": "xml",
    # misc
    ".dockerfile": "dockerfile", ".docker": "dockerfile",
    ".make": "make", ".mk": "make",
    ".lock": "", ".license": "", ".lic": ""
}

SPECIAL_BASENAMES = {
    "Dockerfile": "dockerfile",
    "Makefile": "make",
    "LICENSE": "",
    ".gitignore": "",
    ".gitattributes": "",
    "Procfile": "",
    "README": "markdown",
    "README.md": "markdown",
}

# Beberapa ekstensi biner umum untuk skip cepat
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".class", ".o", ".a", ".lib",
    ".ttf", ".otf", ".woff", ".woff2",
    ".pyc", ".pyo", ".pyd"
}


def is_hidden(path: Path) -> bool:
    name = path.name
    return name.startswith(".") and name not in {".gitignore", ".gitattributes"}


def looks_binary(raw: bytes) -> bool:
    # Sederhana: ada NUL byte atau terlalu banyak byte non-text
    if b"\x00" in raw:
        return True
    # Jika >30% byte bernilai kontrol non-whitespace, anggap biner
    nontext = sum(1 for b in raw if (b < 9) or (13 < b < 32) or (b > 126))
    return (nontext / max(1.0, len(raw))) > 0.30


def detect_lang(path: Path) -> str:
    if path.name in SPECIAL_BASENAMES:
        return SPECIAL_BASENAMES[path.name]
    ext = path.suffix.lower()
    return LANG_MAP.get(ext, "")


def read_text_safely(path: Path, max_bytes: int) -> tuple[str, bool]:
    """
    Mengembalikan (teks, truncated_flag)
    """
    with path.open("rb") as f:
        raw = f.read(max_bytes + 1)
    if path.suffix.lower() in BINARY_EXTS or looks_binary(raw):
        raise ValueError("binary")
    truncated = len(raw) > max_bytes
    raw = raw[:max_bytes]
    # Coba decode; kalau gagal pakai latin-1 agar tidak error
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")
    return text, truncated


def should_skip_dir(dirname: str, include_hidden: bool) -> bool:
    if not include_hidden and dirname.startswith("."):
        return True
    return dirname in EXCLUDE_DIRS


def export_to_markdown(root: Path, out_md: Path, max_bytes: int, include_hidden: bool) -> int:
    files_written = 0
    rel_root = root.resolve()
    # Pastikan output tidak ikut diekstrak
    out_abs = out_md.resolve()
    with out_md.open("w", encoding="utf-8", newline="\n") as out:
        for dirpath, dirnames, filenames in os.walk(rel_root):
            # filter direktori
            dirnames[:] = [d for d in sorted(dirnames) if not should_skip_dir(d, include_hidden)]
            # urutkan file
            for fname in sorted(filenames):
                fpath = Path(dirpath) / fname
                if out_abs == fpath.resolve():
                    continue
                if not include_hidden and is_hidden(fpath):
                    continue
                # skip biner cepat via ekstensi
                if fpath.suffix.lower() in BINARY_EXTS:
                    continue
                try:
                    text, truncated = read_text_safely(fpath, max_bytes=max_bytes)
                except (UnicodeDecodeError, ValueError):
                    # biner atau tak bisa dibaca => lewati
                    continue

                rel = fpath.relative_to(rel_root).as_posix()
                lang = detect_lang(fpath)

                # Judul per file
                out.write(f"# {rel}\n\n")
                fence_lang = lang if lang else ""
                out.write(f"```{fence_lang}\n")
                out.write(text)
                if not text.endswith("\n"):
                    out.write("\n")
                if truncated:
                    out.write("\n# [TRUNCATED] File melebihi batas ukuran saat diekstrak.\n")
                out.write("```\n\n")
                files_written += 1
    return files_written


def main():
    p = argparse.ArgumentParser(description="Ekspor repository/direktori ke satu berkas Markdown bergaya daftar_code.md")
    p.add_argument("-r", "--root", default=".", help="Folder akar yang diekstrak (default: .)")
    p.add_argument("-o", "--output", default="daftar_code.md", help="Nama berkas Markdown keluaran")
    p.add_argument("--max-bytes", type=int, default=500_000, help="Batas byte per file sebelum dipotong")
    p.add_argument("--include-hidden", action="store_true", help="Sertakan file/direktori tersembunyi")
    args = p.parse_args()

    root = Path(args.root).resolve()
    out_md = Path(args.output)

    if not root.exists() or not root.is_dir():
        print(f"Folder '{root}' tidak ditemukan atau bukan direktori.", file=sys.stderr)
        sys.exit(1)

    count = export_to_markdown(root, out_md, max_bytes=args.max_bytes, include_hidden=args.include_hidden)
    print(f"Selesai. {count} file diekspor ke: {out_md}")


if __name__ == "__main__":
    main()
```

# gemini_prompt.md

```markdown
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
```

# requirements.txt

```
streamlit>=1.32.0
streamlit-agraph>=0.0.45
plotly>=5.18.0
python-dotenv>=1.0.0
```

# src/__init__.py

```python
"""Paket aplikasi dashboard pemantauan integritas pipa."""
```

# src/main.py

```python
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
```

# src/config/__init__.py

```python
from src.config.settings import MONTHS, PROJECT_ROOT, THRESHOLD_MM

__all__ = ["MONTHS", "PROJECT_ROOT", "THRESHOLD_MM"]
```

# src/config/settings.py

```python
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

MONTHS = list(range(13))
THRESHOLD_MM = float(os.getenv("PIPE_WALL_THRESHOLD_MM", "5.0"))
```

# src/domain/__init__.py

```python
from src.domain.nodes import CRITICAL_NODES, NODE_LABELS, SAFE_NODES, WARNING_NODES

__all__ = [
    "CRITICAL_NODES",
    "NODE_LABELS",
    "SAFE_NODES",
    "WARNING_NODES",
]
```

# src/domain/nodes.py

```python
SAFE_NODES = {
    "main_export",
    "alpha_2",
    "jalur_gamma",
    "beta_1",
    "alpha_2a",
}
CRITICAL_NODES = {"jalur_alpha", "alpha_1", "alpha_2b"}
WARNING_NODES = {"jalur_beta", "beta_2"}

NODE_LABELS = {
    "main_export": "Main Export",
    "jalur_alpha": "Jalur Alpha",
    "jalur_beta": "Jalur Beta",
    "jalur_gamma": "Jalur Gamma",
    "alpha_1": "Alpha-1",
    "alpha_2": "Alpha-2",
    "beta_1": "Beta-1",
    "beta_2": "Beta-2",
    "alpha_2a": "Alpha-2A",
    "alpha_2b": "Alpha-2B",
}
```

# src/ui/__init__.py

```python
from src.ui.analytics import render_prescriptive_panel
from src.ui.header import render_header
from src.ui.styles import inject_app_styles

__all__ = ["inject_app_styles", "render_header", "render_prescriptive_panel"]
```

# src/ui/analytics.py

```python
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
```

# src/ui/header.py

```python
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
```

# src/ui/styles.py

```python
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
```

# src/visualization/__init__.py

```python
from src.visualization.charts import degradation_chart_figure
from src.visualization.topology import build_graph_elements, render_pipeline_graph

__all__ = [
    "build_graph_elements",
    "degradation_chart_figure",
    "render_pipeline_graph",
]
```

# src/visualization/charts.py

```python
import plotly.graph_objects as go

from src.config.settings import MONTHS, THRESHOLD_MM


def degradation_chart_figure(
    actual_series: list[float],
    title: str = "Tren Degradasi Ketebalan Dinding",
) -> go.Figure:
    n = len(actual_series)
    x_axis = MONTHS[:n] if n <= len(MONTHS) else list(range(n))
    threshold_line = [THRESHOLD_MM] * n
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=actual_series,
            mode="lines",
            name="Ketebalan Aktual",
            line={"color": "#3b82f6", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=threshold_line,
            mode="lines",
            name="Batas Minimum / Threshold",
            line={"color": "#ef4444", "width": 2},
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Waktu (Bulan ke-0 hingga ke-12)",
        yaxis_title="Ketebalan (mm)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
    return fig
```

# src/visualization/topology.py

```python
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph


def build_graph_elements():
    nodes = [
        Node(
            id="main_export",
            label="Main Export",
            size=35,
            color="#22c55e",
            font={"color": "#ffffff", "size": 14, "bold": True},
            shape="circle",
            title="Main Export | Status: AMAN",
        ),
        Node(
            id="jalur_alpha",
            label="Jalur Alpha ⚠",
            size=32,
            color="#ef4444",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Jalur Alpha | Status: KRITIS",
        ),
        Node(
            id="jalur_beta",
            label="Jalur Beta ⚡",
            size=32,
            color="#f59e0b",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Jalur Beta | Status: PERINGATAN",
        ),
        Node(
            id="alpha_1",
            label="Alpha-1 ⚠",
            size=28,
            color="#ef4444",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Alpha-1 | Status: KRITIS",
        ),
        Node(
            id="alpha_2",
            label="Alpha-2",
            size=28,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Alpha-2 | Status: AMAN",
        ),
        Node(
            id="jalur_gamma",
            label="Jalur Gamma",
            size=32,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Jalur Gamma | Status: AMAN",
        ),
        Node(
            id="beta_1",
            label="Beta-1",
            size=28,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Beta-1 | Status: AMAN",
        ),
        Node(
            id="beta_2",
            label="Beta-2 ⚡",
            size=28,
            color="#f59e0b",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Beta-2 | Status: PERINGATAN",
        ),
        Node(
            id="alpha_2a",
            label="Alpha-2A",
            size=28,
            color="#22c55e",
            font={"color": "#ffffff", "size": 13},
            shape="circle",
            title="Alpha-2A | Status: AMAN",
        ),
        Node(
            id="alpha_2b",
            label="Alpha-2B ⚠",
            size=28,
            color="#ef4444",
            font={"color": "#ffffff", "size": 13},
            shape="ellipse",
            title="Alpha-2B | Status: KRITIS",
        ),
    ]

    edges = [
        Edge(source="main_export", target="jalur_alpha", label="", color="#6b7280", width=3),
        Edge(source="main_export", target="jalur_beta", label="", color="#6b7280", width=3),
        Edge(source="main_export", target="jalur_gamma", label="", color="#6b7280", width=2),
        Edge(source="jalur_alpha", target="alpha_1", label="", color="#6b7280", width=2),
        Edge(source="jalur_alpha", target="alpha_2", label="", color="#6b7280", width=2),
        Edge(source="jalur_beta", target="beta_1", label="", color="#6b7280", width=2),
        Edge(source="jalur_beta", target="beta_2", label="", color="#6b7280", width=2),
        Edge(source="alpha_2", target="alpha_2a", label="", color="#6b7280", width=2),
        Edge(source="alpha_2", target="alpha_2b", label="", color="#6b7280", width=2),
    ]

    config = Config(
        width="100%",
        height=420,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#60a5fa",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label", "renderLabel": False},
        d3={"gravity": -400, "linkLength": 180},
    )

    return nodes, edges, config


def render_pipeline_graph() -> None:
    nodes, edges, config = build_graph_elements()
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    if return_value:
        st.session_state.selected_node = return_value
```

