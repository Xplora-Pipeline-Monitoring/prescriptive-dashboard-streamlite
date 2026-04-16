from __future__ import annotations

import os
from typing import Any

import pandas as pd

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    head = "| " + " | ".join(str(c) for c in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([head, sep, *rows])


SYSTEM_PROMPT = """Anda adalah ahli integritas pipa migas dan korosi operasional. Tugas Anda menjelaskan risiko satu segmen/node berdasarkan HANYA data pada blok KONTEKS yang diberikan pengguna.

Aturan wajib:
- Jangan mengarang nilai pengukuran, lokasi fisik, atau kejadian lapangan yang tidak ada di KONTEKS.
- Kolom `severity` adalah indeks simpangan relatif terhadap ambang `target_operasi` (bukan satuan fisik tersendiri). Jelaskan sebagai "seberapa jauh" melewati atau di bawah target menurut aturan tersebut.
- Jika tabel deviasi kosong, jelaskan bahwa pada daftar fitur yang dipantau tidak ada pelanggaran ambang — tanpa menyimpulkan aman secara mutlak di lapangan.

Struktur jawaban (gunakan Markdown):
- ## Ringkasan node — paragraf singkat: status prediksi, critical_prob, priority_tier.
- ## Deviasi operasional — untuk setiap baris tabel: nama fitur, nilai vs target, dan interpretasi `severity`.
- ## Pola dan prioritas — bullet: kemungkinan hubungan antar deviasi (hati-hati, tanpa klaim kausal kuat); prioritas inspeksi/monitoring secara umum.
- ## Batasan analisis — data adalah snapshot dashboard; keputusan operasional akhir mengikuti prosedur dan verifikasi lapangan perusahaan.

Bahasa Indonesia, nada teknis namun mudah dipahami operator."""


def _context_block(
    *,
    node_id: int,
    predicted_class: str,
    critical_prob: float,
    priority_tier: str,
    deviations_df: pd.DataFrame,
) -> str:
    if deviations_df.empty:
        table_part = "Tabel deviasi (fitur yang melanggar target operasi): tidak ada baris (tidak ada pelanggaran ambang pada fitur yang dipantau)."
    else:
        cols = [c for c in ["feature", "nilai_saat_ini", "target_operasi", "severity"] if c in deviations_df.columns]
        sub = deviations_df[cols].copy()
        table_part = "Tabel deviasi (fitur yang melanggar target operasi):\n" + _df_to_markdown_table(sub)

    return (
        f"KONTEKS — gunakan hanya informasi berikut.\n\n"
        f"node_id: {node_id}\n"
        f"predicted_class: {predicted_class}\n"
        f"critical_prob: {critical_prob}\n"
        f"priority_tier: {priority_tier}\n\n"
        f"{table_part}"
    )


def run_node_analysis(
    *,
    node_id: int,
    predicted_class: str,
    critical_prob: float,
    priority_tier: str,
    deviations_df: pd.DataFrame,
    model: str | None = None,
) -> tuple[str | None, str | None]:
    """Panggil OpenRouter; kembalikan (markdown_ulasan, None) atau (None, pesan_error)."""
    api_key = (os.getenv("OPENROUTER_API") or "").strip()
    if not api_key:
        return None, "Variabel lingkungan OPENROUTER_API belum diisi. Salin .env.example ke .env dan tambahkan kunci OpenRouter Anda."

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return None, "Paket `openai` belum terpasang. Jalankan: pip install -r requirements.txt"

    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    user_content = _context_block(
        node_id=node_id,
        predicted_class=str(predicted_class),
        critical_prob=float(critical_prob),
        priority_tier=str(priority_tier),
        deviations_df=deviations_df,
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Berikan analisis mendalam untuk operator berdasarkan KONTEKS berikut.\n\n" + user_content
            ),
        },
    ]

    try:
        response = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=messages,
        )
    except Exception as exc:  # noqa: BLE001 — tampilkan ke UI
        return None, f"Gagal memanggil OpenRouter: {exc}"

    choice = response.choices[0].message
    text = (choice.content or "").strip()
    if not text:
        return None, "Model mengembalikan respons kosong."

    return text, None
