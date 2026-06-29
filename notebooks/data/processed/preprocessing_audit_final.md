# Final Audit Preprocessing

## Konsolidasi Laporan 3 AI

### Temuan Sama
- Typo/slang perlu dinormalisasi ulang dari `text_original`.
- Stopword harus selektif; negasi, intensifier, istilah domain, profanity, dan istilah konflik dipertahankan.
- Spam/judol perlu dikeluarkan dari dataset training.
- Duplikat exact `text_final` perlu dikurangi.
- Angka penting dan istilah hukum perlu aturan khusus.

### Temuan Unik
- Gemini: repair JSON truncation dan kasus `koruptot`, `bernyas`, `suriahi`, `keseringen`, `dipake`.
- GPT Plus: bug akhiran `i`, spam/judol, angka penting, hukum `UU/UUD/RUU`, profanity, violence term, token panjang, campuran bahasa.
- Claude: slang frekuensi tinggi, stopword agresif, emoji placeholder, dokumen terlalu pendek.

### Konflik dan Keputusan Aman
- Rekomendasi field baru tidak diterapkan karena aturan user melarang field baru. Audit/flag disimpan di report, bukan output dataset.
- Mapping single token `u -> yang` tidak diterapkan universal karena raw CSV mengandung campuran bahasa dan huruf tunggal bisa ambigu.
- Emoji `emo_*` dipertahankan sebagai sinyal sentimen; noise tawa teks seperti `wkw...` dibuang.

## Validasi Data dan Output

```json
{
  "input_rows": 13748,
  "output_rows": 11915,
  "duplicate_text_after_extra": 0,
  "text_final_empty_after": 0,
  "long_token_unique_after": 76,
  "error_tokens_remaining_after": {},
  "undang_undang_dasar_tni_after": 0,
  "field_names": [
    "comment_id",
    "video_id",
    "text_original",
    "text_final"
  ]
}
```

## Perubahan Notebook

- `uud` tidak lagi diekspansi otomatis menjadi `undang undang dasar`.
- Normalisasi hukum kontekstual: `ruu_tni`, `uu_tni`, `ruu_polri`, `uu_polri`, `ruu_perampasan_aset`, `uu_perampasan_aset`, `uud_1945`, `uud_nri_1945`.
- Preservasi angka penting: `1945`, `1965`, `1998`, `2024`, `2025`, `2029`, `2030`, `angka_58_persen`, `paslon_02`.
- Spam/judol detection diperluas dan komentar spam penuh menjadi kosong sehingga tidak lolos output training.
- Correction map diperluas untuk bug akhiran `i`, typo laporan AI, profanity/leetspeak, dan token menyatu penting.
- Exact duplicate `text_final` disisakan satu baris di output training.
- Output tetap hanya field `comment_id`, `video_id`, `text_original`, `text_final`.

## File Output Baru

- `notebooks/data/processed/comments_preprocessed_clean_v2.json`
- `notebooks/data/processed/comments_preprocessed_clean_v2.csv`
