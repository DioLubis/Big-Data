# Spark Indonesian Comment Preprocessing

Pipeline utama tersedia sebagai notebook mandiri
`analisis_sentimen_spark_mongodb.ipynb` dan script `src/preprocess_spark.py`.
Keduanya membaca komentar
**hanya dari MongoDB** menggunakan MongoDB Spark Connector, memprosesnya dengan
PySpark, lalu menyimpan hasil dan report **hanya ke MongoDB**.

Sumber teks selalu `text_original`. Output teks final hanya `text_final`.
Kolom turunan lama seperti `text_clean` dan `text_preprocessed` tidak digunakan
sebagai sumber dan tidak disimpan ke collection output.

## Proses

- Validasi collection dan `text_original`
- Audit missing value, duplikasi, label, panjang komentar, emoji, URL, mention, dan hashtag
- HTML unescape, perbaikan encoding `ftfy`, Unicode NFKC, zero-width removal
- Ekstraksi fitur sebelum cleaning
- Emoji menjadi token sentimen
- URL dan mention dibersihkan dari teks final
- Ekspansi hashtag seperti `#TolakRUUTNI` menjadi `tolak ruu tni`
- Normalisasi slang berbasis token menggunakan Spark broadcast variable
- Stopword removal yang mempertahankan negasi, intensifier, domain term, dan kata sentimen
- Stemming Sastrawi opsional melalui `PREPROCESSING_USE_STEMMING`; default nonaktif
  agar run Spark lokal tetap cepat dan stabil
- Penandaan duplikasi berdasarkan `text_final`
- Penyimpanan hasil dan report ke MongoDB

## Output

Collection output `comments_preprocessed` dipotong ke field penting untuk
training saja: `comment_id`, `video_id`, `label` jika tersedia, `text_original`,
dan `text_final`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Isi `.env`:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=analisis_sentimen
MONGO_INPUT_COLLECTION=comments_labeled
MONGO_OUTPUT_COLLECTION=comments_preprocessed
MONGO_REPORT_COLLECTION=comments_preprocessing_report

SPARK_APP_NAME=IndonesianCommentStemmingPreprocessing
SPARK_MASTER=local[*]
MONGO_SPARK_CONNECTOR_PACKAGE=org.mongodb.spark:mongo-spark-connector_2.13:11.0.1

OVERWRITE_EXISTING=true
PREPROCESSING_VERSION=spark_text_final_v2
PREPROCESSING_MAX_CHARS=1000
PREPROCESSING_MAX_TOKENS=120
PREPROCESSING_USE_STEMMING=false
```

MongoDB harus dapat diakses. Pipeline berhenti dengan error jika koneksi gagal,
collection input kosong, atau `text_original` tidak tersedia.

## Menjalankan dengan Python

```powershell
python src\preprocess_spark.py
```

Script mengatur MongoDB Spark Connector melalui `spark.jars.packages`.

## Menjalankan Notebook

```powershell
jupyter notebook analisis_sentimen_spark_mongodb.ipynb
```

Pilih kernel `.venv`, lalu jalankan seluruh sel dari atas. Notebook berisi
implementasi lengkap dan tidak mengimpor script dari folder `src`.

## Menjalankan dengan spark-submit

```powershell
spark-submit `
  --packages org.mongodb.spark:mongo-spark-connector_2.13:11.0.1 `
  src\preprocess_spark.py
```

Untuk Spark standalone, ubah `SPARK_MASTER` di `.env`, misalnya:

```env
SPARK_MASTER=spark://192.168.0.10:7077
```

## Aturan Penulisan Output

- Output data training selalu ditulis ke `comments_preprocessed` dengan mode
  overwrite agar tidak membuat collection baru bersuffix timestamp.
- Collection input tidak pernah ditimpa.
- Report selalu di-append ke `comments_preprocessing_report`.

## Contoh Hasil

Script menampilkan 10 baris contoh dari MongoDB setelah proses:

```text
+------------------------------+--------------------------+--------+
|text_original                 |text_final                |label   |
+------------------------------+--------------------------+--------+
|Gak setuju RUU TNI ini!       |tidak setuju ruu tni     |negative|
|Mantap pak, lanjutkan 👍       |mantap bapak lanjut emo_pos|positive|
+------------------------------+--------------------------+--------+
```

Contoh tersebut hanya ilustrasi. Nilai aktual berasal dari collection MongoDB.

## Contoh Report

Report disimpan sebagai satu dokumen per run:

```json
{
  "run_id": "uuid",
  "input_collection": "comments_labeled",
  "output_collection": "comments_preprocessed",
  "preprocessing_version": "spark_text_final_v2",
  "total_rows_input": 15516,
  "total_rows_output": 15516,
  "total_unique_videos": 5,
  "total_unique_authors": 12000,
  "missing_text_count": 0,
  "duplicate_comment_id_count": 0,
  "duplicate_text_original_count": 120,
  "duplicate_text_count": 120,
  "comments_with_emoji_count": 2930,
  "comments_with_url_count": 10,
  "total_profanity": 340,
  "total_domain_terms": 22100,
  "empty_text_final_count": 3,
  "warnings": ["3 text_final kosong."]
}
```

Distribusi label, metrik validasi, serta top token sebelum dan sesudah preprocessing
disimpan pada field JSON di dokumen report.

## Catatan Connector

Pipeline menggunakan format `mongodb` dari MongoDB Spark Connector 11.0.1.
Versi ini ditujukan untuk Spark 4.x dan Scala 2.13. Connector harus tersedia
pada driver dan seluruh executor.

Pada Windows, Spark yang memakai `--packages` dapat membutuhkan `HADOOP_HOME`
dan `winutils.exe`. Jika muncul error `HADOOP_HOME and hadoop.home.dir are
unset`, lengkapi instalasi Hadoop Windows terlebih dahulu atau jalankan melalui
Spark cluster/Linux yang sudah dikonfigurasi.
