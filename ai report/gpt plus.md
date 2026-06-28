# Instruksi Perbaikan Dataset Komentar Sentimen untuk AI Agent

## 1. Konteks

File yang diaudit adalah dataset komentar YouTube hasil preprocessing awal untuk kebutuhan analisis sentimen.

**File sumber:** `analisis_sentimen.comments_preprocessed.json`

Dataset berisi komentar dengan struktur utama:

```json
{
  "_id": "...",
  "comment_id": "...",
  "video_id": "...",
  "text_original": "...",
  "text_final": "..."
}
```

Tujuan dokumen ini adalah memberikan instruksi lengkap kepada AI agent untuk membersihkan dataset agar lebih siap digunakan untuk:

1. analisis sentimen,
2. training model klasifikasi sentimen,
3. topic modeling,
4. analisis opini publik,
5. eksplorasi kata kunci politik/sosial.

---

## 2. Ringkasan Kondisi Dataset

Berdasarkan audit awal terhadap file JSON:

| Komponen | Temuan |
|---|---:|
| Total data/baris | 13.732 komentar |
| Jumlah `comment_id` unik | 13.732 |
| Duplikat `comment_id` | 0 |
| `text_original` kosong | 0 |
| `text_final` kosong | 0 |
| Jumlah `video_id` unik | 5 |
| Jumlah `text_final` unik | 13.477 |
| Duplikat berlebih berdasarkan `text_final` | 255 |
| Komentar original yang mengandung angka | 3.058 |
| Komentar final yang masih mengandung angka | 206 |
| Komentar emoji-only | 36 |
| Total token emoji placeholder | 3.821 |
| Komentar terindikasi kata kasar/profanity | sekitar 415 |
| Komentar terindikasi istilah kekerasan/ancaman/konflik | sekitar 1.133 |
| Token panjang minimal 15 karakter | 115 unique token |
| Kemunculan `undang undang dasar` di `text_final` | 151 |
| Kemunculan `undang undang dasar tni` di `text_final` | 56 |

---

## 3. Kesimpulan Utama

Dataset **belum bersih sepenuhnya** walaupun sudah melewati preprocessing awal. Masalah terbesar bukan hanya typo manual, tetapi terdapat beberapa kesalahan preprocessing yang sistematis.

Masalah prioritas tertinggi:

1. Bug tambahan huruf `i` di akhir kata.
2. Spam/judol/gambling masih tersisa.
3. Duplikasi `text_final`.
4. Angka penting hilang.
5. Kesalahan normalisasi istilah hukum seperti `UU`, `UUD`, dan `RUU`.
6. Typo, slang, dan kata tidak baku masih banyak.
7. Emoji placeholder perlu kebijakan final.
8. Kata kasar dan istilah kekerasan perlu diberi flag, bukan langsung dihapus.
9. Token panjang dan kata menyatu perlu diperbaiki.
10. Campuran bahasa perlu dideteksi.

---

## 4. Prinsip Perbaikan Utama

AI agent harus mengikuti prinsip berikut:

1. **Jangan menghapus `text_original`.**  
   Kolom ini harus tetap disimpan sebagai sumber kebenaran utama.

2. **Jangan hanya memperbaiki dari `text_final` lama.**  
   Sebaiknya buat hasil baru dari `text_original`, karena beberapa kesalahan di `text_final` berasal dari bug preprocessing.

3. **Jangan menghapus semua kata kasar.**  
   Dalam analisis sentimen, kata kasar sering menjadi sinyal sentimen negatif yang kuat. Kata kasar sebaiknya dinormalisasi dan diberi flag.

4. **Jangan menghapus semua angka.**  
   Angka tertentu membawa konteks penting, seperti `1998`, `1965`, `1945`, `58%`, atau `02`.

5. **Jangan menghapus semua emoji.**  
   Emoji adalah sinyal sentimen. Emoji perlu dipetakan dengan lebih rapi.

6. **Jangan melakukan stemming agresif tanpa validasi.**  
   Stemming yang terlalu agresif bisa merusak makna, terutama pada istilah politik, hukum, dan slang.

7. **Selalu simpan hasil pembersihan sebagai versi baru.**  
   Gunakan kolom seperti `text_clean_v2`, bukan mengganti permanen `text_original`.

---

## 5. Prioritas Perbaikan

| Prioritas | Masalah | Dampak | Tindakan |
|---|---|---|---|
| P0 | Bug akhiran `i` | Vocabulary kotor dan makna rusak | Buat correction map khusus |
| P0 | Spam/judol/gambling | Mengganggu sentimen dan topik | Deteksi dan hapus/flag komentar spam |
| P1 | Duplikat `text_final` | Model bias ke pola berulang | Deduplicate exact dan near-duplicate |
| P1 | Angka penting hilang | Konteks politik hilang | Pertahankan angka bermakna |
| P1 | `UU`, `UUD`, `RUU` salah normalisasi | Makna hukum salah | Buat normalisasi kontekstual |
| P1 | Typo/slang | Vocabulary membesar | Gunakan kamus normalisasi |
| P2 | Emoji-only | Noise jika tidak diberi aturan | Pisahkan atau beri flag |
| P2 | Kata kasar/leetspeak | Sentimen kuat tapi noisy | Normalisasi dan beri flag |
| P2 | Token panjang/menyatu | OOV tinggi | Pecah atau hapus jika spam |
| P3 | Campuran bahasa | Potensi noise | Tambahkan language flag |

---

# 6. Detail Masalah dan Instruksi Perbaikan

---

## 6.1 Bug Akhiran `i`

### Masalah

Ditemukan banyak token yang mendapat tambahan huruf `i` di akhir kata. Ini tampaknya terjadi karena tanda baca seperti `?`, `!`, atau karakter tertentu tidak dibersihkan dengan benar dan berubah menjadi huruf `i`.

Contoh:

| Token salah | Koreksi |
|---|---|
| `suriahi` | `suriah` |
| `rakyati` | `rakyat` |
| `inii` | `ini` |
| `bangi` | `bang` |
| `sihi` | `sih` |
| `apai` | `apa` |
| `apaii` | `apa` |
| `kahi` | `kah` |
| `manai` | `mana` |
| `sipili` | `sipil` |
| `militeri` | `militer` |
| `dpri` | `dpr` |
| `disahkani` | `disahkan` |
| `negarai` | `negara` |
| `koruptori` | `koruptor` |
| `korupsii` | `korupsi` |
| `polrii` | `polri` |
| `indonesiai` | `indonesia` |
| `reformasii` | `reformasi` |
| `demokrasii` | `demokrasi` |
| `otaki` | `otak` |
| `politiki` | `politik` |
| `bisai` | `bisa` |
| `yai` | `ya` |
| `tohi` | `toh` |
| `toi` | `toh` |

### Instruksi untuk AI Agent

1. Buat dictionary koreksi khusus untuk token-token di atas.
2. Jangan menghapus akhiran `i` secara universal.
3. Validasi manual token berakhiran `i`, karena banyak kata valid:
   - `korupsi`
   - `demokrasi`
   - `reformasi`
   - `polisi`
   - `negeri`
   - `sendiri`
   - `fungsi`
   - `partai`
   - `ekonomi`

### Acceptance Criteria

- Token seperti `rakyati`, `inii`, `bangi`, dan `suriahi` tidak boleh muncul lagi di output final.
- Kata valid berakhiran `i` tidak boleh rusak.

---

## 6.2 Spam/Judol/Gambling

### Masalah

Masih ada komentar promosi judi online/spam yang tersisa. Beberapa menggunakan karakter Unicode stylized sehingga lolos dari preprocessing dasar.

Contoh token atau pola bermasalah:

| Token/Pola | Keterangan |
|---|---|
| `aero` / `aerbb` | Brand spam tersamarkan |
| `dora` / `dewadora` / `dwadra` | Brand spam |
| `agustoto` / `agustto` | Brand spam |
| `thor` / `thoreii` | Brand spam |
| `judol` | Judi online |
| `jakpot` / `jackpot` | Konteks judi |
| `gacor` / `gchor` | Slang judi online |
| `maxwin` / `mekwin` | Slang judi online |
| `saldo` | Sering muncul pada spam judi |
| `depo` | Deposit |
| `wd` | Withdraw |
| `cuan` | Konteks promosi |
| `slot` | Judi slot |

### Instruksi untuk AI Agent

1. Terapkan Unicode normalization:
   - gunakan `NFKC`,
   - bersihkan karakter stylized,
   - normalisasi huruf Cyrillic/Latin yang mirip jika memungkinkan.

2. Buat deteksi spam berbasis kata kunci:
   - `aero`
   - `dora`
   - `dewadora`
   - `agustoto`
   - `thor`
   - `judol`
   - `slot`
   - `gacor`
   - `maxwin`
   - `jackpot`
   - `jakpot`
   - `saldo`
   - `depo`
   - `wd`
   - `cuan`

3. Jika komentar terindikasi spam penuh, lakukan salah satu:
   - hapus dari dataset training, atau
   - simpan tetapi beri flag `is_spam = true`.

4. Jangan hanya menghapus brand spam dari kalimat. Jika kalimatnya promosi, seluruh komentar harus dikeluarkan dari dataset utama.

### Output yang Disarankan

Tambahkan kolom:

```json
"is_spam": true,
"spam_reason": "gambling_keyword"
```

### Acceptance Criteria

- Komentar promosi judi tidak masuk ke dataset training utama.
- Komentar yang hanya menyebut `judol` sebagai kritik sosial jangan otomatis dihapus tanpa konteks.
- Gunakan kombinasi keyword + konteks kalimat.

---

## 6.3 Duplikasi `text_final`

### Masalah

Tidak ada duplikat `comment_id`, tetapi terdapat duplikasi berdasarkan `text_final`.

Contoh `text_final` yang berulang:

| Teks | Jumlah Kemunculan |
|---|---:|
| `baik gas baik gas` | 14 |
| `emo_other` | 11 |
| `tolak ruu tni` | 10 |
| `terima kasih member emo_pos` | 10 |
| `terima kasih member` | 9 |
| `emo_pos` | 9 |
| `wallahi re finished` | 6 |
| `tolak revisi uu tni` | 6 |
| `emo_laugh` | 5 |

### Instruksi untuk AI Agent

1. Simpan semua data mentah.
2. Untuk dataset training utama, buat deduplication:
   - exact duplicate berdasarkan `text_clean_v2`,
   - optional near-duplicate detection.

3. Jika komentar sama muncul dari video berbeda, beri opsi:
   - mode konservatif: tetap hapus duplikat teks,
   - mode analitik: simpan tetapi beri bobot lebih rendah.

### Output yang Disarankan

Tambahkan kolom:

```json
"is_duplicate_text": true,
"duplicate_group_id": "hash_text_clean_v2"
```

### Acceptance Criteria

- Dataset training tidak berisi banyak komentar final yang sama persis.
- Data audit tetap menyimpan informasi duplikasi.

---

## 6.4 Typo dan Slang Belum Ternormalisasi

### Masalah

Masih banyak typo, slang, dan bentuk tidak baku. Beberapa perlu dinormalisasi agar vocabulary lebih bersih.

Contoh correction map awal:

| Token | Koreksi |
|---|---|
| `terimakasih` | `terima kasih` |
| `masarakat` | `masyarakat` |
| `sprti` | `seperti` |
| `sperti` | `seperti` |
| `maen` | `main` |
| `koropsi` | `korupsi` |
| `koroptor` | `koruptor` |
| `dipake` | `dipakai` |
| `ketauan` | `ketahuan` |
| `smoga` | `semoga` |
| `prampasan` | `perampasan` |
| `dengerin` | `mendengarkan` |
| `skarang` | `sekarang` |
| `brani` | `berani` |
| `sistim` | `sistem` |
| `slalu` | `selalu` |
| `sndiri` | `sendiri` |
| `perduli` | `peduli` |
| `pnting` | `penting` |
| `bangett` | `banget` |
| `mensahkan` | `mengesahkan` |
| `disyahkan` | `disahkan` |
| `alusista` | `alutsista` |
| `kawatir` | `khawatir` |
| `munkin` | `mungkin` |

### Catatan Penting

Tidak semua slang harus diubah. Beberapa slang justru penting untuk sentimen, misalnya:

- `goblok`
- `tolol`
- `bacot`
- `anjir`
- `babi`
- `wkwk`
- `gemoy`
- `wowo`
- `konoha`
- `orba`
- `petrus`
- `buzzer`

Untuk token seperti ini, lebih baik distandarisasi daripada dihapus.

### Instruksi untuk AI Agent

1. Buat kamus normalisasi typo/slang.
2. Jalankan normalisasi berbasis token.
3. Setelah normalisasi, hitung ulang vocabulary.
4. Review token dengan frekuensi rendah dan panjang tidak wajar.

### Acceptance Criteria

- Typo umum seperti `masarakat`, `koropsi`, `sperti`, dan `prampasan` tidak muncul lagi.
- Slang yang penting untuk sentimen tetap dipertahankan atau dinormalisasi secara konsisten.

---

## 6.5 Angka Penting Hilang

### Masalah

Banyak angka hilang setelah preprocessing.

| Jenis | Jumlah Komentar |
|---|---:|
| Komentar original yang mengandung angka | 3.058 |
| Komentar final yang masih mengandung angka | 206 |

Ini menunjukkan preprocessing terlalu agresif menghapus angka.

### Angka yang Sebaiknya Dipertahankan

| Angka | Makna Potensial |
|---|---|
| `1998` / `98` | Reformasi, Mei 1998, Orde Baru |
| `1965` | Peristiwa politik/sejarah |
| `1945` | UUD 1945 / NRI 1945 |
| `2025` | Tahun konteks komentar |
| `2029`, `2030` | Prediksi atau konteks masa depan |
| `58%` | Konteks politik/pemilih |
| `02` | Konteks paslon/kelompok politik |

### Angka yang Boleh Dihapus

| Pola | Alasan |
|---|---|
| `02:15` | Timestamp video |
| `44:40` | Timestamp video |
| `13:18` | Timestamp video |
| angka random tanpa konteks | Bisa menjadi noise |

### Instruksi untuk AI Agent

1. Hapus timestamp dengan pola:
   - `mm:ss`
   - `hh:mm:ss`

2. Pertahankan tahun penting:
   - `1998`
   - `1965`
   - `1945`
   - `2025`
   - `2029`
   - `2030`

3. Normalisasi angka politik:
   - `58%` → `angka_58_persen`
   - `58 persen` → `angka_58_persen`
   - `02` → `paslon_02` jika konteks politik jelas

4. Normalisasi `98` menjadi `1998` jika konteksnya:
   - `mei`
   - `orba`
   - `reformasi`
   - `soeharto`
   - `kerusuhan`
   - `mahasiswa`

### Acceptance Criteria

- Angka bermakna tidak hilang.
- Timestamp video tetap terhapus.
- `58%` dan `02` tidak hilang jika membawa konteks politik.

---

## 6.6 Normalisasi `UU`, `UUD`, dan `RUU`

### Masalah

Ditemukan banyak hasil normalisasi yang salah. Contohnya, `UUD TNI` sering berubah menjadi `undang undang dasar tni`, padahal dalam konteks komentar kemungkinan besar maksudnya adalah `UU TNI`, bukan `UUD`.

### Aturan Normalisasi

| Pola Original | Output yang Disarankan |
|---|---|
| `RUU TNI` | `ruu_tni` |
| `UU TNI` | `uu_tni` |
| `UUD TNI` | `uu_tni` jika konteksnya revisi TNI |
| `UU Polri` | `uu_polri` |
| `UUD Polri` | `uu_polri` jika konteksnya revisi Polri |
| `RUU Perampasan Aset` | `ruu_perampasan_aset` |
| `UU Perampasan Aset` | `uu_perampasan_aset` |
| `UUD Perampasan Aset` | `uu_perampasan_aset` jika konteksnya rancangan/undang-undang biasa |
| `UUD 1945` | `uud_1945` |
| `UUD NRI 1945` | `uud_nri_1945` |

### Instruksi untuk AI Agent

1. Jangan ubah semua `UUD` menjadi `undang undang dasar`.
2. Gunakan aturan berbasis konteks.
3. Jika `UUD` diikuti `1945` atau `NRI`, simpan sebagai `uud_1945` atau `uud_nri_1945`.
4. Jika `UUD` diikuti `TNI`, `Polri`, atau `perampasan aset`, kemungkinan itu typo dari `UU`.

### Acceptance Criteria

- Tidak ada output seperti `undang undang dasar tni`.
- Istilah hukum menjadi konsisten:
  - `ruu_tni`
  - `uu_tni`
  - `uud_1945`
  - `uu_perampasan_aset`
  - `ruu_perampasan_aset`

---

## 6.7 Emoji Placeholder

### Masalah

Emoji sudah dipetakan menjadi placeholder, tetapi masih terlalu umum.

Distribusi token emoji:

| Token | Jumlah |
|---|---:|
| `emo_other` | 1.424 |
| `emo_laugh` | 1.417 |
| `emo_sad` | 483 |
| `emo_pos` | 384 |
| `emo_neg` | 44 |
| `emo_think` | 38 |
| `emo_angry` | 31 |

Ada 36 komentar yang hanya berisi emoji placeholder.

### Instruksi untuk AI Agent

1. Pertahankan emoji yang membawa sentimen:
   - `emo_laugh`
   - `emo_sad`
   - `emo_angry`
   - `emo_neg`
   - `emo_pos`
   - `emo_think`

2. Evaluasi ulang `emo_other`, karena terlalu umum.

3. Komentar emoji-only perlu diberi flag:
   - `is_emoji_only = true`

4. Untuk training model:
   - jika task hanya text sentiment, emoji-only boleh dipisahkan,
   - jika task sentiment umum, emoji-only bisa tetap dipakai dengan label berbasis emoji.

### Acceptance Criteria

- Emoji tidak dihapus total.
- Komentar emoji-only bisa difilter dengan mudah.
- `emo_other` tidak mendominasi tanpa makna.

---

## 6.8 Kata Kasar, Umpatan, dan Leetspeak

### Masalah

Ditemukan ratusan komentar dengan kata kasar. Dalam konteks analisis sentimen, ini bukan hanya noise, tetapi sinyal emosi negatif yang penting.

Contoh token:

| Token | Keterangan |
|---|---|
| `bodoh` | hinaan/sentimen negatif |
| `tolol` | hinaan/sentimen negatif |
| `goblok` | hinaan/sentimen negatif |
| `bacot` | hinaan/sentimen negatif |
| `babi` | umpatan |
| `anjing` | umpatan |
| `anjir` | slang/umpatan ringan |
| `bangsat` | umpatan |
| `asu` | umpatan |
| `anjj` | variasi sensor |
| `banhsat` | typo dari `bangsat` |
| `t3mb4k` | leetspeak dari `tembak` |
| `m4ti` | leetspeak dari `mati` |
| `fuvk` | obfuscation dari kata kasar Inggris |

### Instruksi untuk AI Agent

1. Jangan hapus otomatis semua kata kasar.
2. Buat normalisasi variasi:
   - `goblokkk`, `g0blok` → `goblok`
   - `tololl`, `t0lol` → `tolol`
   - `banhsat` → `bangsat`
   - `t3mb4k` → `tembak`
   - `m4ti` → `mati`
   - `fuvk` → `fuck` atau `profanity_en`

3. Tambahkan flag:
   - `has_profanity = true`

4. Jika kata kasar terlalu ofensif untuk output publik, simpan versi:
   - `text_clean_v2`
   - `text_clean_safe`

### Acceptance Criteria

- Kata kasar tetap terdeteksi sebagai sinyal sentimen.
- Variasi sensor/leetspeak dinormalisasi.
- Dataset dapat difilter berdasarkan `has_profanity`.

---

## 6.9 Istilah Kekerasan, Ancaman, dan Konflik

### Masalah

Ada banyak komentar dengan istilah seperti:

- `perang`
- `senjata`
- `tembak`
- `mati`
- `bunuh`
- `bakar`
- `kudeta`
- `revolusi`
- `petrus`
- `hilang`
- `diculik`
- `eksekusi`
- `pemberontakan`

Kata-kata ini tidak selalu berarti ajakan kekerasan. Sebagian adalah konteks sejarah, kritik politik, kekhawatiran, atau pembahasan berita. Karena itu, jangan langsung dihapus.

### Instruksi untuk AI Agent

1. Tambahkan flag:
   - `has_violence_term = true`

2. Klasifikasikan konteks jika memungkinkan:
   - `historical_context`
   - `fear_or_warning`
   - `supportive_violence`
   - `news_discussion`
   - `metaphor_or_sarcasm`

3. Jangan otomatis menghapus komentar hanya karena mengandung kata `perang`, `senjata`, atau `mati`.

4. Jika dataset akan digunakan untuk moderasi konten, buat label terpisah dari label sentimen.

### Acceptance Criteria

- Komentar kekhawatiran tidak disamakan dengan ajakan kekerasan.
- Istilah kekerasan dapat difilter atau dianalisis terpisah.

---

## 6.10 Token Panjang dan Kata Menyatu

### Masalah

Ditemukan token yang terlalu panjang, sebagian merupakan kata valid, tetapi sebagian lain adalah hasil gabungan kata, username, spam, atau hasil preprocessing rusak.

Contoh token bermasalah:

| Token | Masalah |
|---|---|
| `haruusnyauutniituutidaperluu` | Banyak kata menyatu |
| `yangpalingperluusijokowidan` | Banyak kata menyatu |
| `berhentibayarpajak` | Gabungan frasa |
| `merdekaindonesiaantikorupsi` | Gabungan slogan |
| `pertanyaannyaiapakah` | Gabungan + bug akhiran `i` |
| `dipertanyakanibagi` | Gabungan + bug akhiran `i` |
| `persibfootballnews` | Kemungkinan channel/username |
| `lapanganpekerjaan` | Gabungan dua kata |
| `aerbbmenawarkan` | Spam |
| `ahahahahahahahahahah...` | Tawa berulang/noise |

### Instruksi untuk AI Agent

1. Deteksi token dengan panjang minimal 15 karakter.
2. Klasifikasikan token panjang:
   - kata Indonesia valid,
   - gabungan kata,
   - spam,
   - username/channel,
   - tawa berulang,
   - noise.

3. Pecah token jika jelas:
   - `lapanganpekerjaan` → `lapangan pekerjaan`
   - `berhentibayarpajak` → `berhenti bayar pajak`

4. Hapus atau flag token spam/username jika tidak relevan.

### Acceptance Criteria

- Token panjang yang tidak valid berkurang.
- Gabungan kata penting dipisahkan.
- Spam token tidak masuk vocabulary utama.

---

## 6.11 Campuran Bahasa

### Masalah

Dataset berisi campuran bahasa:

- Bahasa Indonesia,
- Bahasa Inggris,
- istilah Arab/Islam,
- istilah Jepang/pop culture,
- istilah slang internet.

Contoh:

| Teks/Token | Jenis |
|---|---|
| `absolute power corrupts absolutely` | Inggris |
| `aint readin allat` | Inggris slang |
| `welcome neo orba` | Inggris + Indonesia |
| `wallahi re finished` | Inggris/Arab slang |
| `dear god` | Inggris |
| `kami-sama` | Jepang |
| `insya allah`, `aamiin`, `astaghfirullah` | Arab/Islam |
| `hokage`, `konoha` | Pop culture/slang politik |

### Instruksi untuk AI Agent

1. Tambahkan language detection sederhana:
   - `id`
   - `en`
   - `mixed`
   - `unknown`

2. Jangan langsung hapus komentar mixed-language.
3. Untuk model Bahasa Indonesia, komentar full-English dapat:
   - dihapus,
   - diterjemahkan,
   - atau diberi flag `language = "en"`.

4. Istilah domain seperti `konoha`, `hokage`, `wowo`, `gemoy`, dan `orba` harus dipertahankan karena penting untuk konteks politik/sentimen.

### Acceptance Criteria

- Setiap komentar memiliki flag bahasa.
- Komentar non-Indonesia tidak mencampuri training utama tanpa keputusan eksplisit.

---

# 7. Pipeline Preprocessing yang Disarankan

Gunakan pipeline berikut untuk membuat versi data bersih.

## 7.1 Input

Gunakan `text_original` sebagai sumber utama.

Jangan hanya melanjutkan dari `text_final`, karena `text_final` sudah mengandung beberapa error hasil preprocessing.

## 7.2 Urutan Pipeline

1. **Preserve raw data**
   - simpan `_id`, `comment_id`, `video_id`, `text_original`.

2. **Unicode normalization**
   - gunakan NFKC,
   - ubah karakter stylized menjadi bentuk normal,
   - bersihkan zero-width character.

3. **Remove technical noise**
   - hapus URL,
   - hapus mention `@username`,
   - hapus hashtag jika tidak bermakna,
   - hapus timestamp video seperti `02:15`.

4. **Spam detection**
   - deteksi judol/gambling,
   - beri flag `is_spam`,
   - keluarkan dari dataset training utama.

5. **Emoji handling**
   - ubah emoji menjadi placeholder yang lebih informatif,
   - beri flag `is_emoji_only`.

6. **Case folding**
   - ubah menjadi lowercase,
   - tetapi simpan acronym penting dalam bentuk token konsisten.

7. **Normalize legal/political terms**
   - `RUU TNI` → `ruu_tni`,
   - `UU TNI` → `uu_tni`,
   - `UUD 1945` → `uud_1945`,
   - `UU Perampasan Aset` → `uu_perampasan_aset`,
   - `DPR`, `TNI`, `POLRI`, `KPK`, `HAM`, `ASN`, `CPNS`, `PPPK`.

8. **Preserve meaningful numbers**
   - `1998`,
   - `1965`,
   - `1945`,
   - `58%`,
   - `02` jika konteks politik.

9. **Slang and typo normalization**
   - gunakan correction map,
   - perbaiki bug akhiran `i`,
   - normalisasi leetspeak.

10. **Token cleanup**
    - hapus token kosong,
    - hapus token terlalu pendek jika tidak bermakna,
    - tangani token panjang/menyatu.

11. **Profanity and violence flagging**
    - jangan hapus otomatis,
    - beri flag.

12. **Deduplication**
    - exact duplicate,
    - near duplicate jika diperlukan.

13. **Final validation**
    - cek vocabulary,
    - cek OOV,
    - cek top token,
    - cek jumlah data sebelum/sesudah.

---

# 8. Format Output yang Disarankan

AI agent sebaiknya menghasilkan file JSON/CSV baru dengan struktur berikut:

```json
{
  "_id": "...",
  "comment_id": "...",
  "video_id": "...",
  "text_original": "...",
  "text_final_v1": "...",
  "text_clean_v2": "...",
  "is_spam": false,
  "spam_reason": null,
  "is_duplicate_text": false,
  "duplicate_group_id": null,
  "is_emoji_only": false,
  "has_emoji": true,
  "has_profanity": false,
  "has_violence_term": false,
  "language": "id",
  "preprocessing_notes": []
}
```

---

# 9. Correction Dictionary Awal

Berikut correction dictionary awal yang bisa digunakan sebagai baseline.

```json
{
  "suriahi": "suriah",
  "rakyati": "rakyat",
  "inii": "ini",
  "bangi": "bang",
  "sihi": "sih",
  "apai": "apa",
  "apaii": "apa",
  "kahi": "kah",
  "manai": "mana",
  "sipili": "sipil",
  "militeri": "militer",
  "dpri": "dpr",
  "disahkani": "disahkan",
  "negarai": "negara",
  "koruptori": "koruptor",
  "korupsii": "korupsi",
  "polrii": "polri",
  "indonesiai": "indonesia",
  "reformasii": "reformasi",
  "demokrasii": "demokrasi",
  "otaki": "otak",
  "politiki": "politik",
  "bisai": "bisa",
  "yai": "ya",
  "tohi": "toh",
  "toi": "toh",
  "terimakasih": "terima kasih",
  "masarakat": "masyarakat",
  "sprti": "seperti",
  "sperti": "seperti",
  "maen": "main",
  "koropsi": "korupsi",
  "koroptor": "koruptor",
  "dipake": "dipakai",
  "ketauan": "ketahuan",
  "smoga": "semoga",
  "prampasan": "perampasan",
  "dengerin": "mendengarkan",
  "skarang": "sekarang",
  "brani": "berani",
  "sistim": "sistem",
  "slalu": "selalu",
  "sndiri": "sendiri",
  "perduli": "peduli",
  "pnting": "penting",
  "bangett": "banget",
  "mensahkan": "mengesahkan",
  "disyahkan": "disahkan",
  "alusista": "alutsista",
  "kawatir": "khawatir",
  "munkin": "mungkin",
  "banhsat": "bangsat",
  "t3mb4k": "tembak",
  "m4ti": "mati",
  "jakpot": "jackpot"
}
```

---

# 10. Keyword List untuk Spam/Judol

Gunakan daftar awal berikut:

```json
[
  "aero",
  "aerbb",
  "dora",
  "dewadora",
  "dwadra",
  "agustoto",
  "agustto",
  "thor",
  "thoreii",
  "judol",
  "slot",
  "gacor",
  "gchor",
  "maxwin",
  "mekwin",
  "jackpot",
  "jakpot",
  "saldo",
  "depo",
  "withdraw",
  "wd",
  "cuan",
  "bonus"
]
```

Catatan: kata seperti `cuan` atau `saldo` jangan digunakan sendirian sebagai indikator spam. Gunakan bersama konteks lain seperti `slot`, `jackpot`, `depo`, `gacor`, atau brand spam.

---

# 11. Keyword List untuk Flag Profanity

```json
[
  "bodoh",
  "tolol",
  "tololl",
  "goblok",
  "bacot",
  "babi",
  "anjing",
  "anjir",
  "anjay",
  "anjj",
  "anj",
  "anying",
  "bangsat",
  "banhsat",
  "asu",
  "geblek",
  "dongo",
  "bodok"
]
```

---

# 12. Keyword List untuk Flag Istilah Kekerasan/Konflik

```json
[
  "perang",
  "senjata",
  "senpi",
  "tembak",
  "nembak",
  "t3mb4k",
  "mati",
  "m4ti",
  "bunuh",
  "membunuh",
  "dibunuh",
  "bakar",
  "membakar",
  "kudeta",
  "revolusi",
  "pemberontakan",
  "hancurkan",
  "bantai",
  "dibantai",
  "hilang",
  "culik",
  "diculik",
  "eksekusi",
  "petrus"
]
```

Catatan: daftar ini hanya untuk flag, bukan untuk penghapusan otomatis.

---

# 13. Validasi Akhir yang Wajib Dilakukan

Setelah preprocessing v2, AI agent wajib membuat laporan validasi berisi:

## 13.1 Statistik Dataset

- jumlah data awal,
- jumlah data setelah hapus spam,
- jumlah data setelah deduplikasi,
- jumlah komentar kosong,
- jumlah komentar emoji-only,
- jumlah komentar dengan profanity,
- jumlah komentar dengan istilah kekerasan,
- jumlah komentar per bahasa,
- jumlah komentar per video.

## 13.2 Statistik Vocabulary

- total token,
- unique token,
- top 100 token,
- token dengan frekuensi 1,
- token panjang minimal 15 karakter,
- token yang masih mengandung angka,
- token yang masih mengandung karakter aneh.

## 13.3 Validasi Error Lama

Pastikan token berikut tidak muncul lagi:

```text
suriahi
rakyati
inii
bangi
sihi
apai
apaii
kahi
manai
sipili
militeri
dpri
disahkani
negarai
koruptori
korupsii
indonesiai
reformasii
demokrasii
```

Pastikan frasa berikut juga tidak muncul lagi:

```text
undang undang dasar tni
undang undang dasar perampasan aset
```

Kecuali jika konteksnya benar-benar membahas UUD sebagai konstitusi.

---

# 14. Acceptance Criteria Final

Dataset dianggap lebih bersih jika memenuhi kriteria berikut:

1. Tidak ada `comment_id` duplikat.
2. Tidak ada `text_clean_v2` kosong.
3. Spam/judol sudah difilter atau diberi flag.
4. Duplikat `text_clean_v2` sudah ditangani.
5. Bug akhiran `i` sudah hilang.
6. Typo umum sudah berkurang signifikan.
7. Angka penting tetap dipertahankan.
8. Timestamp video sudah dihapus.
9. `UU`, `UUD`, dan `RUU` sudah konsisten.
10. Emoji sentiment tetap dipertahankan.
11. Emoji-only dapat difilter.
12. Kata kasar tidak hilang tanpa kontrol, tetapi diberi flag.
13. Istilah kekerasan tidak otomatis dihapus, tetapi diberi flag.
14. Token panjang/noise sudah ditangani.
15. Output menyimpan `text_original`, `text_final_v1`, dan `text_clean_v2`.
16. Ada laporan audit sebelum dan sesudah preprocessing.

---

# 15. Instruksi Eksekusi untuk AI Agent

Gunakan instruksi berikut sebagai task utama:

> Bersihkan file `analisis_sentimen.comments_preprocessed.json` dengan membuat kolom baru `text_clean_v2`. Gunakan `text_original` sebagai sumber utama, bukan hanya `text_final`. Terapkan Unicode normalization, spam detection, normalisasi typo/slang, perbaikan bug akhiran `i`, normalisasi istilah hukum/politik, preservasi angka penting, emoji handling, profanity flagging, violence-term flagging, language detection, dan deduplication. Jangan menghapus `text_original`. Hasilkan file bersih baru dan laporan audit sebelum-sesudah preprocessing.

---

# 16. Deliverables yang Harus Dihasilkan AI Agent

AI agent harus menghasilkan minimal:

1. `comments_clean_v2.json`
2. `comments_clean_v2.csv`
3. `preprocessing_audit_report.md`
4. `correction_dictionary.json`
5. `spam_removed_or_flagged.csv`
6. `duplicate_text_report.csv`
7. `vocabulary_report.csv`

---

# 17. Catatan Akhir

Dataset ini sudah cukup baik sebagai hasil preprocessing awal, tetapi belum aman digunakan langsung untuk training model tanpa cleaning tahap kedua. Fokus utama perbaikan adalah membersihkan error sistematis, bukan hanya menghapus kata-kata kasar atau slang.

Untuk analisis sentimen, beberapa elemen yang terlihat noisy seperti emoji, kata kasar, slang politik, dan istilah konflik justru bisa menjadi sinyal penting. Karena itu, pendekatan terbaik adalah:

1. normalisasi,
2. flagging,
3. deduplikasi,
4. validasi,
5. baru kemudian filtering sesuai kebutuhan model.
