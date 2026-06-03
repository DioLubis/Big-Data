# Analisis Sentimen Komentar YouTube

Project ini dipakai untuk:
- Mengambil komentar YouTube via YouTube Data API v3
- Menyimpan data komentar ke MongoDB
- Melakukan preprocessing teks bahasa Indonesia dengan Spark
- Melatih model sentimen sederhana berbasis TF-IDF + Logistic Regression

## Struktur Folder

- `data/raw/`: data mentah hasil fetch
- `data/processed/`: data setelah preprocessing atau labeling
- `models/`: model dan vectorizer tersimpan
- `notebooks/`: notebook untuk workflow bertahap
- `src/`: kode reusable untuk fetch, preprocessing, dan training

## Setup

### 1. Buat virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Kalau PowerShell menolak activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Siapkan file `.env`

Salin `.env.example` menjadi `.env`, lalu isi variabel yang dibutuhkan.

Contoh variabel utama:

```env
YOUTUBE_API_KEY=...
YOUTUBE_VIDEO_IDS=id_video_1,id_video_2,id_video_3
MAX_COMMENTS=

MONGO_URI=...
MONGO_DB=analisis_sentimen
MONGO_COMMENTS_COLLECTION=comments
MONGO_PROCESSED_COLLECTION=comments_processed

SPARK_MASTER=local[*]
SPARK_NUM_PARTITIONS=4
SPARK_TEXT_COLUMN=text_original
SPARK_HOME=C:\spark
```

Catatan:
- `SPARK_MASTER` adalah alamat master Spark, misalnya `spark://192.168.0.10:7077`
- `SPARK_HOME` harus berisi path folder instalasi Spark, bukan URL
- `MONGO_PROCESSED_COLLECTION` adalah collection tujuan hasil preprocessing
- Kalau nama kolom teks di MongoDB bukan `text_original`, ubah `SPARK_TEXT_COLUMN`

## Alur Data

1. Ambil komentar YouTube
2. Simpan komentar mentah ke MongoDB
3. Baca komentar dari MongoDB
4. Lakukan preprocessing teks
5. Simpan hasil preprocessing ke MongoDB
6. Pakai data hasil preprocessing untuk training model

## MongoDB

File utama untuk membaca data komentar:
- `src/mongo_comments_loader.py`

File utama untuk preprocessing dan menyimpan hasil ke MongoDB:
- `src/preprocess_spark.py`

Jalankan loader untuk cek data mentah:

```powershell
python src\mongo_comments_loader.py
```

Jalankan preprocessing:

```powershell
python src\preprocess_spark.py
```

## Preprocessing Raw JSON Notebook

Kalau memakai file raw dari notebook:

```text
notebooks\data\raw\comments_raw_all_videos.json
```

jalankan:

```powershell
python src\preprocess_raw_youtube.py
```

Output akan dibuat ke:

```text
notebooks\data\processed\comments_preprocessed_all_videos.csv
notebooks\data\processed\comments_preprocessed_all_videos.jsonl
```

Preprocessing ini khusus untuk komentar YouTube bahasa Indonesia:
- flatten struktur `raw_comment_threads`
- ambil metadata penting komentar dan video
- buang komentar kosong dan duplikat `comment_id`
- normalisasi URL, mention, hashtag, emoji, huruf berulang, dan slang seperti `yg`, `gak`, `tdk`, `dgn`
- tetap mempertahankan negasi seperti `tidak`, `bukan`, `jangan`, dan `belum`
- tambah fitur ringan seperti jumlah emoji, tanda tanya, tanda seru, URL, dan rasio huruf kapital

Kalau ingin menambahkan stemming Sastrawi, jalankan:

```powershell
python src\preprocess_raw_youtube.py --with-stem
```

Catatan: `--with-stem` jauh lebih lambat. Untuk TF-IDF + Logistic Regression, output default `text_preprocessed` biasanya lebih praktis karena sudah bersih dan tetap mempertahankan kata negasi.

## Spark

### Mode lokal

Kalau semua dijalankan di satu mesin, cukup pakai:

```env
SPARK_MASTER=local[*]
```

### Mode cluster

Kalau device ini hanya sebagai worker dan master ada di laptop lain, set:

```env
SPARK_MASTER=spark://192.168.0.10:7077
SPARK_HOME=C:\spark
```

Lalu jalankan worker di PowerShell:

```powershell
$env:SPARK_HOME="C:\spark"
$env:SPARK_MASTER="spark://192.168.0.10:7077"
& "$env:SPARK_HOME\bin\spark-class.cmd" org.apache.spark.deploy.worker.Worker "$env:SPARK_MASTER"
```

Kalau ingin membatasi resource worker:

```powershell
$env:SPARK_HOME="C:\spark"
$env:SPARK_MASTER="spark://192.168.0.10:7077"
& "$env:SPARK_HOME\bin\spark-class.cmd" org.apache.spark.deploy.worker.Worker --cores 4 --memory 4g "$env:SPARK_MASTER"
```

Catatan penting:
- Paket Spark yang ada di `C:\spark` pada instalasi ini tidak memakai `sbin\start-worker.cmd`
- Untuk instalasi ini, `spark-class.cmd` adalah command yang dipakai di Windows
- Pastikan port `7077` bisa diakses dari worker ke master

## Cara Mendapatkan Video ID YouTube

Contoh URL:

```text
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Video ID-nya:

```text
dQw4w9WgXcQ
```

Kalau URL pendek:

```text
https://youtu.be/dQw4w9WgXcQ
```

Video ID tetap bagian terakhir URL:

```text
dQw4w9WgXcQ
```

## Notebook

Kalau ingin menjalankan workflow seperti di Google Colab:

1. Install extension VS Code: **Python** dan **Jupyter**
2. Buka notebook di folder `notebooks/`
3. Pilih kernel Python dari `.venv`
4. Jalankan cell satu per satu dengan `Shift+Enter`

## Model Training

Setelah preprocessing selesai, data bisa dipakai untuk training model di pipeline training yang ada di repo ini.

## Troubleshooting Cepat

- Kalau preprocessing tidak masuk MongoDB, cek `MONGO_URI`, `MONGO_DB`, dan `MONGO_PROCESSED_COLLECTION`
- Kalau Spark worker tidak muncul di master, cek koneksi ke `spark://<IP_MASTER>:7077`
- Kalau script tidak menemukan teks komentar, cek `SPARK_TEXT_COLUMN`
- Kalau `SPARK_HOME` berisi URL `spark://...`, ubah menjadi path folder seperti `C:\spark`

