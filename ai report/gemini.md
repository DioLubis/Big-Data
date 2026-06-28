Panduan Pembersihan, Reparasi Struktural, dan Preprocessing Korpus Sentimen JSON (Instruksi AI Agent)Dokumen ini ditujukan kepada AI Agent untuk mengeksekusi pipeline pemulihan data dan penyelarasan leksikal pada berkas analisis_sentimen.comments_preprocessed.json. Lakukan pengerjaan secara bertahap sesuai spesifikasi teknis di bawah ini.Tahap 1: Reparasi Struktural Berkas JSON (Syntax Repair)1.1 Identifikasi Masalah StrukturalBerkas input memiliki kerusakan struktural fatal akibat kegagalan transmisi data (data truncation). Berkas terputus secara tidak normal pada baris terakhir objek ke-26.  ID Objek Terpotong: 6a41815713664b4e1f28966b   Teks Asli Terpotong: "text_original": "akibat di iming im...   Sintaksis Rusak: Kehilangan karakter penutup string ("), penutup objek (}), dan penutup array (]). Parser standar seperti json.load() akan memunculkan kesalahan fatal JSONDecodeError.  1.2 Algoritma Pemulihan StrukturalAI Agent harus menggunakan pendekatan pemrograman defensif berbasis pencarian indeks byte (byte-index search) untuk memotong bagian yang rusak:Baca berkas secara mentah (raw string/bytes).Temukan kemunculan penutup objek terakhir yang valid }, (yaitu akhir dari objek ke-25 dengan ID 6a41815713664b4e1f28966a).  Potong string mentah tepat setelah tanda koma pada },.Tambahkan karakter penutup larik ] secara manual untuk menutup struktur array JSON secara sah.  Abaikan objek ke-26 karena informasi semantiknya tidak utuh.  Tahap 2: Audit Kualitas Data & Koreksi Anomali LeksikalSetelah memulihkan sintaksis berkas, AI Agent wajib menyisir data dan menerapkan perbaikan leksikal tingkat tinggi pada bidang text_original sebelum menyimpannya ke text_final.  Berikut adalah tabel audit kesalahan penulisan (typo), anomali leksikal, dan degradasi preprocessing sebelumnya yang wajib diperbaiki :  ID ObjekTeks Asli (Input)Masalah pada Preprocessing LamaKoreksi Baku yang Benar (Output)6a41815713664b4e1f289652...ja dh ngeri bgt...Kata "ngeri" diubah menjadi "takut". Ini mendegradasi bobot intensitas sentimen.  Kembalikan ke kata dasar aslinya: "ngeri".  6a41815713664b4e1f289657...ladang koruptot baru.Kata "koruptot" dibiarkan begitu saja tanpa koreksi.  Koreksi typo menjadi kata baku: "koruptor".  6a41815713664b4e1f289657...minta bernyas preman...Kata "bernyas" dibiarkan tanpa koreksi.  Koreksi typo menjadi kata baku: "berantas".  6a41815713664b4e1f28965dAE𝙍О𝟴𝟴menarik semakin banyak...Komentar spam promosi judi online yang lolos.  Hapus seluruh objek dari korpus.  6a41815713664b4e1f28965fI aint readin allat broKomentar bahasa Inggris informal yang tidak memiliki konteks sentimen lokal.  Hapus seluruh objek dari korpus.  6a41815713664b4e1f289662Akankah kita menjadi Suriah?Kata "Suriah" dikorup menjadi "suriahi" karena kesalahan penanganan afiksasi.  Koreksi kembali menjadi bentuk aslinya: "suriah".  6a41815713664b4e1f289663...klo keseringen dipake...Kata "keseringen" dibiarkan tanpa koreksi.  Koreksi kata menjadi baku: "keseringan".  6a41815713664b4e1f289663...klo keseringen dipake...Kata "dipake" dibiarkan informal.  Standardisasi menjadi kata formal: "dipakai".  Tahap 3: Kamus Normalisasi Kata Gaul dan Singkatan (Colloquial Mappings)Untuk mencegah variasi penulisan memicu masalah out-of-vocabulary (OOV) pada model, terapkan kamus pemetaan formal berikut :  JSON{
  "gk": "tidak",
  "gak": "tidak",
  "nggak": "tidak",
  "bgt": "banget",
  "tp": "tetapi",
  "trs": "terus",
  "klw": "kalau",
  "klo": "kalau",
  "dr": "dari",
  "ak": "aku",
  "bkn": "bukan",
  "tr": "terus",
  "ja": "saja",
  "dh": "sudah",
  "uu": "undang-undang",
  "ruu": "rancangan undang-undang",
  "omon": "omong"
}
Tahap 4: Spesifikasi Pipeline Pembersihan Teks (Text Preprocessing Steps)AI Agent wajib mengeksekusi pipeline teks dengan urutan logis berikut demi menjamin kualitas fitur :  Case Folding: Ubah semua teks menjadi huruf kecil (lowercase).  Noise Removal: Bersihkan URL, penyebutan pengguna (@username), tagar (#), angka (kecuali angka kontekstual penting seperti 1998 atau 98 yang wajib dipertahankan untuk konteks sejarah), serta simbol non-alfabet.  Emoji & Emoticon Standardization: Jangan menghapus emoji marah atau sedih, melainkan konversikan ke padanan kata ekspresif (misal: 😡 menjadi marah, 🙂 menjadi senyum) menggunakan pustaka representasi emoji.  Slang & Typo Correction: Lakukan pencocokan token menggunakan kamus pada Tahap 2 dan Tahap 3. Jika ditemukan token tidak dikenal, gunakan algoritma Jarak Damerau-Levenshtein dengan ambang batas jarak maksimum $d \le 1$ untuk mencocokkan kata dengan leksikon KBBI baku.  Formulasi matematis Damerau-Levenshtein:$$d_{a,b}(i,j)=\min\begin{cases}d_{a,b}(i-1,j)+1&(\text{Penghapusan})\\d_{a,b}(i,j-1)+1&(\text{Penyisipan})\\d_{a,b}(i-1,j-1)+\text{cost}&(\text{Substitusi})\\d_{a,b}(i-2,j-2)+1&(\text{Transposisi jika }i,j>1\text{ dan }a_i=b_{j-1}\text{ dan }a_{i-1}=b_j)\end{cases}$$Negation Handling: Jangan menghapus kata negasi seperti "tidak" atau "bukan". Gabungkan kata negasi dengan kata sifat setelahnya menggunakan karakter garis bawah (misal: tidak bagus $\rightarrow$ tidak_bagus).  No Stemming: Untuk model representasi vektor (word embedding), nonaktifkan proses stemming agar struktur semantik dan afiksasi kata kerja tetap terjaga demi akurasi sentimen maksimal.  Tahap 5: Skrip Eksekusi Otomatis (Python Implementation Script)AI Agent dapat langsung mengeksekusi skrip Python berikut untuk memproses berkas secara aman tanpa memicu AttributError tipe data.  Pythonimport json
import re

def repair_json_syntax(file_path):
    """Memperbaiki kerusakan struktural JSON akibat data terpotong."""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = f.read().strip()
    
    # Mencari index penutup objek ke-25 yang valid
    last_valid_idx = raw_data.rfind("},")
    if last_valid_idx == -1:
        raise ValueError("Format berkas terlalu rusak untuk dipulihkan.")
    
    # Memotong dan merekonstruksi struktur JSON yang valid
    fixed_json_str = raw_data[:last_valid_idx + 2] + "]"
    return json.loads(fixed_json_str)

def clean_text_pipeline(text):
    """Pipeline preprocessing teks tanpa merusak kualitas semantik."""
    if not isinstance(text, str):
        return ""
    
    # 1. Lowercasing
    text = text.lower()
    
    # 2. Amankan angka sejarah penting
    text = re.sub(r'\b98\b', '1998', text)
    
    # 3. Noise Removal (Regex)
    text = re.sub(r'https?://\S+|www\.\S+', '', text) # Hapus URL
    text = re.sub(r'[-+]?[0-9]+', '', text) # Hapus angka selain yang diamankan di atas
    text = re.sub(r'[^\w\s]', ' ', text) # Hapus tanda baca
    text = re.sub(r'\s+', ' ', text).strip() # Normalisasi spasi
    
    # 4. Kamus Pemetaan Kustom (Typo + Slang)
    normalization_dict = {
        "gk": "tidak", "gak": "tidak", "nggak": "tidak",
        "bgt": "banget", "tp": "tetapi", "trs": "terus",
        "klw": "kalau", "klo": "kalau", "dr": "dari",
        "ak": "aku", "bkn": "bukan", "tr": "terus",
        "ja": "saja", "dh": "sudah", "uu": "undang-undang",
        "ruu": "rancangan undang-undang", "omon": "omong",
        "koruptot": "koruptor", "bernyas": "berantas",
        "keseringen": "keseringan", "dipake": "dipakai",
        "suriahi": "suriah", "dengernya": "mendengarnya"
    }
    
    words = text.split()
    cleaned_words = [normalization_dict.get(word, word) for word in words]
    
    # 5. Penanganan Negasi (Negation Handling)
    negations = {"tidak", "bukan", "kurang", "belum"}
    final_tokens =
    skip = False
    for i in range(len(cleaned_words)):
        if skip:
            skip = False
            continue
        if cleaned_words[i] in negations and i + 1 < len(cleaned_words):
            final_tokens.append(f"{cleaned_words[i]}_{cleaned_words[i+1]}")
            skip = True
        else:
            final_tokens.append(cleaned_words[i])
            
    return " ".join(final_tokens)

def main():
    input_file = "analisis_sentimen.comments_preprocessed.json"
    output_file = "analisis_sentimen.comments_cleaned.json"
    
    try:
        # Eksekusi reparasi struktural
        data = repair_json_syntax(input_file)
        cleaned_dataset =
        
        # Filter spesifik ID spam/bot
        blacklisted_ids = {
            "6a41815713664b4e1f28965d", # Spam bot judi AERO88
            "6a41815713664b4e1f28965f"  # English spam comment
        }
        
        for item in data:
            obj_id = item["_id"]["$oid"]
            if obj_id in blacklisted_ids:
                continue # Hapus komentar spam
                
            # Pastikan penanganan kesalahan logika tipe data
            original_text = str(item.get("text_original", ""))
            
            # Jalankan pipeline pembersihan maksimal
            item["text_final"] = clean_text_pipeline(original_text)
            cleaned_dataset.append(item)
            
        # Simpan kembali berkas dengan sintaksis valid
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_dataset, f, indent=2, ensure_ascii=False)
            
        print(f"Sukses! Data bersih disimpan di '{output_file}'. Total record aktif: {len(cleaned_dataset)}.")
        
    except Exception as e:
        print(f"Gagal menjalankan pipeline: {str(e)}")

if __name__ == "__main__":
    main()
Tahap 6: Kriteria Penerimaan Data Bersih (Acceptance Criteria)AI Agent harus memverifikasi keluaran data bersih berdasarkan daftar periksa di bawah ini:[ ] Validitas Sintaksis: Berkas baru dapat di-parsing menggunakan metode standar json.loads() tanpa menimbulkan galat JSONDecodeError.  [ ] Pengurangan Derau Ekstrim: Tidak ada lagi elemen spam promosi seperti "aerbbmenarik" atau kalimat murni bahasa Inggris non-konteks.  [ ] Konsistensi Semantik: Kata negasi tidak terbuang, melainkan terikat dengan kata sifat setelahnya melalui format kata_sifat.  [ ] Integritas Morfologi: Tidak ada kata-kata bentukan baru yang rusak seperti "suriahi", dan kata sifat emosional kuat seperti "ngeri" dipertahankan pada tempatnya.  [ ] Standarisasi Bahasa Gaul: Seluruh singkatan media sosial dasar (gk, bgt, tp, trs, klo) sepenuhnya bertransformasi menjadi kata baku bahasa Indonesia.