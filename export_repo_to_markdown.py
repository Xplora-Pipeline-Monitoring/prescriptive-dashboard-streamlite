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
