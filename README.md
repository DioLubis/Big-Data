# Analisis Sentimen Komentar YouTube (Indonesia)

Project ini adalah template awal untuk:
- Mengambil komentar YouTube via YouTube Data API v3
- Membersihkan dan normalisasi teks bahasa Indonesia
- Melatih model sentimen sederhana (TF-IDF + Logistic Regression)
- Menyimpan model untuk inferensi berikutnya

## Struktur Folder

- `data/raw/`: hasil komentar mentah
- `data/processed/`: data setelah preprocessing/labeling
- `models/`: model dan vectorizer tersimpan
- `notebooks/`: notebook untuk workflow block-by-block
- `src/`: fungsi reusable (fetch, preprocessing, training)

## 1) Setup Environment

### Opsi A (disarankan): Virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Jika PowerShell menolak activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2) Siapkan API Key YouTube

1. Enable **YouTube Data API v3** di Google Cloud Console
2. Buat API key
3. Duplikat `.env.example` menjadi `.env`
4. Isi value:

```env
YOUTUBE_API_KEY=...
YOUTUBE_VIDEO_IDS=id_video_1,id_video_2,id_video_3
MAX_COMMENTS=
```

Keterangan:
- `YOUTUBE_VIDEO_IDS` bisa diisi banyak ID video, dipisahkan koma.
- `MAX_COMMENTS` dikosongkan agar mengambil semua komentar yang tersedia.

### Cara Mendapatkan YouTube Video ID

Contoh URL:

`https://www.youtube.com/watch?v=dQw4w9WgXcQ`

Maka `video_id` adalah nilai setelah `v=` yaitu:

`dQw4w9WgXcQ`

Jika URL pendek seperti:

`https://youtu.be/dQw4w9WgXcQ`

Maka `video_id` adalah segmen terakhir URL: `dQw4w9WgXcQ`.

## 3) Jalankan Notebook (Block by Block seperti Google Colab)

Ya, **bisa dijalankan satu blok satu blok** di VS Code, sama seperti Google Colab.

Langkah:
1. Install extension VS Code: **Python** dan **Jupyter**
2. Buka file notebook di folder `notebooks/`
3. Pilih kernel Python (`.venv`)
4. Klik tombol **Run Cell** pada tiap blok atau `Shift+Enter`

Shortcut penting:
- `Shift+Enter`: jalankan cell aktif, pindah ke cell berikutnya
- `Ctrl+Enter`: jalankan cell aktif, tetap di cell itu
- `Run All`: jalankan semua cell dari atas ke bawah

## 4) Alur Kerja yang Disarankan

1. Fetch komentar
2. Simpan CSV mentah ke `data/raw/`
3. Preprocess teks
4. Labeling data (manual/semi otomatis)
5. Training model
6. Evaluasi dan simpan model ke `models/`

## Catatan Penting Labeling

Model supervised **butuh label** (`positif`, `negatif`, `netral`).
Jika belum punya label:
- Mulai dengan labeling manual 300-1000 komentar
- Atau gunakan weak labeling, lalu review manual

## Next Development (Opsional)

- Coba model IndoBERT untuk akurasi lebih tinggi
- Tambahkan visualisasi wordcloud per kelas sentimen
- Bungkus pipeline jadi API Flask/FastAPI
