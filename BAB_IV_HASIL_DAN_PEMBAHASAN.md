BAB IV
HASIL DAN PEMBAHASAN

4.1 Gambaran Umum Dashboard Visualisasi

Dibangun sebuah dashboard visualisasi interaktif menggunakan framework *Streamlit* untuk mendukung proses eksplorasi data (*Exploratory Data Analysis* atau EDA) hasil analisis sentimen komentar YouTube terhadap kebijakan RUU TNI. Dashboard tersebut dikembangkan dengan memanfaatkan library *Plotly* untuk grafik interaktif dan *WordCloud* untuk visualisasi frekuensi kata. Data yang ditampilkan bersumber dari dua *collection* MongoDB, yaitu *comments_sentiment* yang berisi data berlabel manual dan *phase2_auto_labeled* yang berisi hasil pelabelan otomatis menggunakan IndoBERT.

Dashboard dibagi menjadi lima tab utama, yaitu Distribusi Sentimen, Tren Waktu, Frekuensi Kata, *N-Gram* dan *Word Cloud*, serta *Insight* per Video. Setiap tab menyajikan visualisasi yang berbeda untuk mendukung analisis dari berbagai sudut pandang. Selain itu, disediakan juga panel samping (*sidebar*) yang memuat kontrol filter seperti jumlah kata teratas dan tombol *refresh* data.

[Gambar 4.1 — Tampilan Utama Dashboard]
Cara mendapatkan: jalankan dashboard dengan perintah "streamlit run dashboard_eda.py", lalu ambil tangkapan layar (*screenshot*) tampilan awal dashboard yang memperlihatkan header KPI dan navigasi tab.
Penjelasan gambar: Gambar ini menampilkan halaman utama dashboard EDA sentimen yang memuat enam kartu metrik ringkasan di bagian atas, yaitu total data gabungan, jumlah data berlabel manual, jumlah data berlabel otomatis, serta jumlah masing-masing sentimen positif, netral, dan negatif beserta persentasenya. Di bawahnya terdapat navigasi lima tab yang dapat diakses pengguna.


4.2 Ringkasan Metrik Data

Ditampilkan ringkasan metrik utama pada bagian paling atas dashboard dalam bentuk enam kartu (*metric cards*) yang disusun secara horizontal. Kartu-kartu tersebut menampilkan total data gabungan dari kedua sumber, jumlah data berlabel manual, jumlah data berlabel otomatis, serta jumlah dan persentase komentar untuk masing-masing kategori sentimen positif, netral, dan negatif.

Berdasarkan data yang berhasil dimuat dari MongoDB, diperoleh total keseluruhan sebanyak 13.177 komentar setelah proses deduplikasi berdasarkan *comment_id*. Dari jumlah tersebut, sebanyak 1.471 komentar berasal dari pelabelan manual yang tersimpan pada *collection comments_sentiment*, sedangkan sisanya sebanyak 11.706 komentar berasal dari pelabelan otomatis yang tersimpan pada *collection phase2_auto_labeled*.

Ringkasan metrik ini memberikan gambaran awal mengenai komposisi dataset sebelum pengguna masuk ke analisis yang lebih mendalam pada masing-masing tab.

[Gambar 4.2 — Kartu Metrik Ringkasan Data]
Cara mendapatkan: ambil *screenshot* bagian atas dashboard yang memperlihatkan enam kartu metrik dengan nilai total data, data manual, data otomatis, dan tiga sentimen.
Penjelasan gambar: Gambar ini memperlihatkan enam kartu metrik yang menjadi ringkasan kuantitatif dataset. Setiap kartu menampilkan nama metrik, nilai angka, dan keterangan persentase untuk kartu sentimen.


4.3 Distribusi Sentimen

4.3.1 Gambaran Umum Tab Distribusi Sentimen

Disajikan analisis distribusi label sentimen pada tab pertama yang diberi judul "Distribusi Sentimen". Tab ini terbagi menjadi tiga sub-tab, yaitu *Manual Label*, *Auto Label*, dan *Gabungan*. Masing-masing sub-tab menyajikan visualisasi yang sama namun menggunakan subset data yang berbeda sehingga perbandingan antar sumber data dapat dilakukan secara langsung.

4.3.2 Grafik Batang Jumlah Komentar per Sentimen

Ditampilkan grafik batang vertikal (*bar chart*) pada bagian pertama setiap sub-tab yang menggambarkan jumlah komentar untuk masing-masing kategori sentimen. Setiap batang diberi warna yang berbeda, yaitu hijau untuk sentimen positif, biru untuk netral, dan merah untuk negatif. Di atas setiap batang dicantumkan nilai jumlah komentar beserta persentasenya terhadap total data pada sumber yang bersangkutan.

[Gambar 4.3 — Grafik Batang Distribusi Sentimen (Data Gabungan)]
Cara mendapatkan: buka tab "Distribusi Sentimen", pilih sub-tab "Gabungan", lalu ambil *screenshot* grafik batang di sisi kiri.
Penjelasan gambar: Gambar ini menampilkan grafik batang jumlah komentar berdasarkan tiga kategori sentimen pada data gabungan. Setiap batang menunjukkan jumlah dan persentase komentar yang termasuk dalam kategori positif, netral, dan negatif.

Berdasarkan hasil visualisasi pada data gabungan, sentimen negatif mendominasi distribusi keseluruhan. Kondisi ini mencerminkan bahwa respons masyarakat terhadap kebijakan RUU TNI cenderung bernada penolakan atau kekhawatiran dibandingkan dukungan.

4.3.3 Grafik Lingkaran Proporsi Sentimen

Ditampilkan grafik lingkaran (*donut chart*) di sebelah kanan grafik batang yang menggambarkan proporsi setiap sentimen dalam bentuk persentase. Grafik ini menggunakan format *donut* dengan lubang di tengah berukuran 45% dari total lingkaran. Setiap irisan diberi label sentimen dan persentase yang terlihat langsung pada grafik.

[Gambar 4.4 — Grafik Donut Proporsi Sentimen]
Cara mendapatkan: ambil *screenshot* grafik lingkaran di sisi kanan pada sub-tab "Gabungan" di tab "Distribusi Sentimen".
Penjelasan gambar: Gambar ini memperlihatkan proporsi ketiga kategori sentimen dalam bentuk diagram lingkaran berlubang. Setiap irisan menampilkan persentase langsung sehingga pembaca dapat dengan cepat memahami dominasi sentimen tertentu.


4.3.4 Grafik Ketidakseimbangan Kelas (Lollipop Chart)

Ditampilkan grafik *lollipop* di bawah kedua grafik sebelumnya untuk memvisualisasikan ketidakseimbangan distribusi kelas (*class imbalance*). Grafik ini menunjukkan persentase setiap sentimen dibandingkan dengan kondisi ideal, yaitu sebesar 33,3% untuk masing-masing kelas jika data terdistribusi secara merata. Garis putus-putus vertikal pada nilai 33,3% dijadikan acuan keseimbangan. Semakin jauh titik suatu sentimen dari garis tersebut, semakin besar ketidakseimbangannya.

[Gambar 4.5 — Grafik Lollipop Ketidakseimbangan Kelas]
Cara mendapatkan: ambil *screenshot* grafik *lollipop* yang berada di bawah pasangan grafik batang dan lingkaran pada salah satu sub-tab distribusi.
Penjelasan gambar: Gambar ini memperlihatkan posisi persentase masing-masing sentimen relatif terhadap kondisi ideal 33,3%. Titik berwarna merah yang berada jauh ke kanan menunjukkan dominasi sentimen negatif dalam dataset.

Ketidakseimbangan kelas yang teridentifikasi ini penting untuk diperhatikan pada tahap pelatihan model klasifikasi karena dapat memengaruhi performa model dalam mengenali kelas minoritas.

4.3.5 Perbandingan Distribusi Manual, Auto-Label, dan Gabungan

Ditampilkan grafik batang berkelompok (*grouped bar chart*) di bagian bawah tab distribusi untuk membandingkan proporsi sentimen dari ketiga sumber data secara berdampingan. Setiap kelompok batang mewakili satu kategori sentimen, sedangkan warna batang membedakan sumber data, yaitu biru untuk data manual, kuning untuk data *auto-label*, dan hijau untuk data gabungan.

[Gambar 4.6 — Grafik Batang Perbandingan Manual vs Auto-Label vs Gabungan]
Cara mendapatkan: *scroll* ke bawah pada tab "Distribusi Sentimen" setelah melewati tiga sub-tab, lalu ambil *screenshot* grafik batang berkelompok.
Penjelasan gambar: Gambar ini menampilkan perbandingan proporsi sentimen dari tiga sumber data secara berdampingan. Konsistensi antara data manual dan *auto-label* dapat dievaluasi dari kedekatan tinggi batang yang berwarna biru dan kuning pada setiap kategori sentimen.

Grafik perbandingan ini digunakan untuk menilai konsistensi antara pelabelan manual dan pelabelan otomatis. Apabila selisih antara keduanya kecil, maka dapat disimpulkan bahwa model IndoBERT yang digunakan untuk pelabelan otomatis menghasilkan distribusi yang mendekati distribusi label manual.


4.3.6 Rata-rata Jumlah Like per Sentimen

Ditampilkan grafik batang dan tabel ringkasan pada bagian terakhir tab distribusi yang menggambarkan rata-rata jumlah *like* yang diterima oleh komentar berdasarkan kategori sentimennya. Data *like_count* diperoleh melalui proses *join* antara data sentimen dan *collection comments* pada MongoDB yang menyimpan metadata komentar asli dari YouTube Data API.

[Gambar 4.7 — Grafik Rata-rata Like per Sentimen]
Cara mendapatkan: *scroll* ke bagian paling bawah tab "Distribusi Sentimen", lalu ambil *screenshot* grafik batang rata-rata *like* beserta tabel di sebelah kanannya.
Penjelasan gambar: Gambar ini memperlihatkan perbedaan rata-rata jumlah *like* yang diterima komentar berdasarkan sentimennya. Nilai rata-rata, median, dan total *like* untuk setiap kategori ditampilkan dalam tabel berwarna gradasi biru di sebelah kanan grafik.

Dari visualisasi ini dapat diketahui apakah komentar positif, negatif, atau netral cenderung lebih banyak mendapatkan respons berupa *like* dari pengguna lain. Pola ini dapat mencerminkan dukungan atau persetujuan komunitas terhadap komentar dengan sentimen tertentu.


4.4 Tren Waktu

4.4.1 Gambaran Umum Tab Tren Waktu

Disajikan analisis tren sentimen berdasarkan waktu publikasi komentar pada tab kedua yang diberi judul "Tren Waktu". Tab ini memuat berbagai visualisasi untuk mengidentifikasi pola temporal dari komentar YouTube terkait kebijakan RUU TNI, termasuk identifikasi periode lonjakan komentar negatif dan positif, analisis tren bulanan, serta eksplorasi kata kunci yang dominan pada periode puncak.

4.4.2 Filter Rentang Tanggal dan Granularitas

Disediakan kontrol filter pada bagian atas tab tren waktu yang memungkinkan pengguna memilih rentang tanggal dan granularitas waktu. Filter rentang tanggal memiliki nilai *default* yang diatur secara otomatis berdasarkan periode terpadat data, yaitu periode di mana volume komentar harian berada di atas kuartil 40%. Granularitas waktu dapat dipilih antara harian atau mingguan melalui tombol radio.

[Gambar 4.8 — Filter Rentang Tanggal dan Granularitas]
Cara mendapatkan: buka tab "Tren Waktu", lalu ambil *screenshot* bagian filter yang memuat pilihan granularitas dan dua *date picker* untuk tanggal awal dan akhir.
Penjelasan gambar: Gambar ini memperlihatkan tiga kontrol filter yang disusun horizontal, yaitu pilihan granularitas (Harian/Mingguan), input tanggal mulai, dan input tanggal akhir. Kontrol ini memungkinkan pengguna untuk mempersempit fokus analisis temporal sesuai kebutuhan.

4.4.3 Grafik Garis Tren Positif vs Negatif

Ditampilkan grafik garis ganda (*dual line chart*) yang membandingkan jumlah komentar positif dan negatif sepanjang periode waktu yang dipilih. Kedua garis diberi warna hijau untuk sentimen positif dan merah untuk sentimen negatif. Area di bawah garis juga diberi bayangan transparan untuk memperjelas perbedaan volume antar sentimen pada setiap periode.

[Gambar 4.9 — Grafik Tren Sentimen Positif vs Negatif]
Cara mendapatkan: setelah memilih rentang tanggal, *scroll* sedikit ke bawah dan ambil *screenshot* grafik garis dengan dua kurva berwarna hijau dan merah.
Penjelasan gambar: Gambar ini menampilkan tren temporal dua sentimen utama dalam bentuk grafik garis. Anotasi panah pada puncak kurva merah menunjukkan tanggal terjadinya lonjakan komentar negatif terbesar, sedangkan anotasi pada puncak kurva hijau menunjukkan puncak komentar positif.

Grafik ini efektif untuk mengidentifikasi kapan respons publik paling intens terhadap isu RUU TNI, terutama dalam bentuk penolakan atau kritik yang tercermin dari lonjakan komentar negatif.


4.4.4 Analisis Lonjakan dengan Word Cloud

Ditampilkan dua kartu berdampingan di bawah grafik tren yang masing-masing menganalisis puncak komentar negatif dan puncak komentar positif. Setiap kartu memuat informasi tanggal puncak, jumlah komentar, kata kunci utama, serta visualisasi *word cloud* dari komentar pada periode tersebut.

*Word cloud* dihasilkan menggunakan library *WordCloud* dengan parameter *max_words=80* dan *collocations=False*. Kata-kata umum yang tercantum dalam daftar *stopwords* tidak ditampilkan. Ukuran font kata pada *word cloud* mencerminkan frekuensi kemunculannya, sehingga kata yang paling sering disebutkan akan tampak lebih besar.

[Gambar 4.10 — Word Cloud Puncak Negatif dan Puncak Positif]
Cara mendapatkan: *scroll* ke bagian "Analisis Lonjakan — Kata Kunci & Word Cloud", lalu ambil *screenshot* dua kartu berwarna merah dan hijau beserta *word cloud* di dalamnya.
Penjelasan gambar: Gambar ini memperlihatkan dua *word cloud* yang dihasilkan dari komentar pada hari puncak sentimen negatif (kiri, latar belakang merah muda) dan hari puncak sentimen positif (kanan, latar belakang hijau muda). Kata-kata seperti "tolak", "bahaya", "sipil", dan "demokrasi" terlihat dominan pada *word cloud* negatif, sementara kata positif cenderung lebih beragam.

Analisis ini membantu memahami topik atau isu spesifik yang memicu lonjakan respons publik pada periode tertentu. Misalnya, jika kata "sipil" dan "bahaya" dominan pada puncak negatif, dapat disimpulkan bahwa kekhawatiran terhadap dampak RUU TNI pada masyarakat sipil menjadi isu sentral yang memicu kritik.


4.4.5 Tren Komentar Per Bulan

Disajikan dua grafik tren bulanan secara terpisah sebagai bagian khusus yang menggunakan seluruh rentang data tanpa mengikuti filter tanggal yang dipilih pengguna. Hal ini dilakukan agar gambaran tren bulanan tetap lengkap dan tidak terpengaruh oleh pembatasan rentang pada grafik harian atau mingguan.

Grafik pertama berupa grafik batang bertumpuk (*stacked bar chart*) yang menampilkan jumlah komentar tiap bulan dengan warna berbeda untuk setiap sentimen. Grafik kedua berupa grafik garis multi-sentimen yang memperlihatkan arah naik-turun ketiga sentimen dari bulan ke bulan, dilengkapi anotasi pada bulan dengan komentar negatif terbanyak.

[Gambar 4.11 — Grafik Batang Tren Komentar Per Bulan]
Cara mendapatkan: *scroll* ke bagian "Tren Komentar Per Bulan" pada tab "Tren Waktu", lalu ambil *screenshot* grafik batang bertumpuk.
Penjelasan gambar: Gambar ini menampilkan jumlah komentar yang dikelompokkan per bulan dalam bentuk batang bertumpuk tiga warna. Bulan-bulan dengan tinggi batang merah yang dominan menunjukkan periode di mana sentimen negatif sangat tinggi, yang kemungkinan besar berkaitan dengan perkembangan pembahasan RUU TNI di DPR.

[Gambar 4.12 — Grafik Garis Tren Sentimen Per Bulan]
Cara mendapatkan: ambil *screenshot* grafik garis multi-sentimen yang berada tepat di bawah grafik batang bulanan.
Penjelasan gambar: Gambar ini memperlihatkan tren perubahan ketiga sentimen dari bulan ke bulan dalam bentuk garis. Anotasi pada titik puncak garis merah memperlihatkan bulan dengan volume komentar negatif tertinggi sepanjang periode pengamatan.


4.4.6 Word Cloud Penyebab Lonjakan Per Bulan

Ditampilkan dua *word cloud* secara berdampingan yang berfokus pada bulan dengan komentar negatif terbanyak. *Word cloud* pertama dihasilkan hanya dari komentar bersentimen negatif pada bulan tersebut, sedangkan *word cloud* kedua dihasilkan dari seluruh komentar tanpa memfilter sentimen pada bulan yang sama.

[Gambar 4.13 — Word Cloud Penyebab Lonjakan Bulan Puncak Negatif]
Cara mendapatkan: *scroll* ke bagian "Word Cloud Penyebab Lonjakan" pada tab "Tren Waktu", lalu ambil *screenshot* dua *word cloud* yang muncul setelah grafik garis bulanan.
Penjelasan gambar: Gambar kiri menampilkan *word cloud* berwarna merah dari komentar negatif pada bulan puncak, sedangkan gambar kanan menampilkan *word cloud* dari semua komentar bulan yang sama tanpa filter sentimen. Perbandingan keduanya memungkinkan identifikasi kata yang spesifik hanya muncul pada komentar negatif.

4.4.7 Grafik Area Stacked dan Rasio Negatif

Ditampilkan grafik area bertumpuk (*stacked area chart*) dan grafik batang rasio negatif sebagai pelengkap analisis tren. Grafik area bertumpuk memperlihatkan kontribusi total volume dari ketiga sentimen secara proporsional dalam satu tampilan. Adapun grafik rasio negatif menampilkan persentase komentar negatif dari total komentar pada setiap periode, dengan garis ambang kritis pada nilai 60%.

[Gambar 4.14 — Grafik Area Stacked dan Rasio Negatif]
Cara mendapatkan: *scroll* ke bawah setelah *word cloud* bulanan, ambil *screenshot* grafik area bertumpuk dan di bawahnya grafik batang rasio negatif.
Penjelasan gambar: Grafik area menunjukkan komposisi total komentar per periode dengan warna bertumpuk. Grafik batang rasio negatif menampilkan batang berwarna merah untuk periode yang melampaui ambang 60%, menandakan kondisi kritis di mana lebih dari separuh komentar pada periode tersebut bernada negatif.

Diakhiri tab tren waktu dengan tabel ringkasan data tren yang memuat kolom Periode, Positif, Netral, Negatif, Total, dan % Negatif. Tabel ini menggunakan *background gradient* merah pada kolom % Negatif sehingga periode dengan proporsi negatif tertinggi langsung terlihat secara visual.


4.5 Frekuensi Kata

4.5.1 Gambaran Umum Tab Frekuensi Kata

Disajikan analisis frekuensi kata pada tab ketiga yang diberi judul "Frekuensi Kata". Analisis ini dilakukan pada kolom *text_final* yang merupakan teks komentar hasil preprocessing. Kata-kata yang termasuk dalam daftar *stopwords*, kata dengan panjang kurang dari tiga karakter, serta kata yang bukan alfabet murni tidak diikutsertakan dalam perhitungan frekuensi. Pengguna dapat memilih sentimen yang ingin dianalisis melalui *dropdown* di bagian atas tab dan mengatur jumlah kata teratas melalui *slider* di *sidebar*.

4.5.2 Grafik Batang Vertikal Frekuensi Kata

Ditampilkan grafik batang vertikal pada bagian pertama tab frekuensi kata yang menampilkan kata-kata paling sering muncul berdasarkan filter sentimen yang dipilih. Setiap batang menampilkan nilai frekuensi kemunculan di atasnya. Sumbu horizontal menampilkan kata dan sumbu vertikal menampilkan jumlah kemunculan.

[Gambar 4.15 — Grafik Batang Vertikal Top N Kata]
Cara mendapatkan: buka tab "Frekuensi Kata", pilih sentimen "Semua" atau salah satu sentimen tertentu, lalu ambil *screenshot* grafik batang vertikal yang muncul pertama.
Penjelasan gambar: Gambar ini memperlihatkan daftar kata paling sering muncul dalam komentar berdasarkan filter sentimen yang dipilih. Tinggi setiap batang merepresentasikan frekuensi kemunculan kata tersebut di seluruh komentar yang sesuai dengan filter.

4.5.3 Grafik Batang Horizontal Persentase Kata

Ditampilkan grafik batang horizontal di bawah grafik vertikal yang menampilkan kontribusi persentase setiap kata terhadap total token pada subset data yang dipilih. Warna batang menggunakan gradasi dari biru muda ke biru tua, di mana warna semakin gelap menunjukkan persentase yang semakin tinggi. *Color bar* pada sisi kanan grafik menjelaskan skala warna persentase.

[Gambar 4.16 — Grafik Batang Horizontal Persentase Kata]
Cara mendapatkan: *scroll* ke bawah pada tab "Frekuensi Kata" setelah grafik vertikal, lalu ambil *screenshot* grafik batang horizontal dengan gradasi warna biru.
Penjelasan gambar: Gambar ini menampilkan urutan kata dari persentase tertinggi hingga terendah dalam orientasi horizontal. Kata dengan persentase tertinggi berada di atas dan ditampilkan dengan warna biru paling gelap.


4.5.4 Perbandingan Kata Menonjol per Sentimen

Ditampilkan tiga grafik batang horizontal secara berdampingan yang masing-masing menampilkan kata paling sering muncul untuk sentimen positif, netral, dan negatif secara terpisah. Setiap grafik menggunakan warna yang sesuai dengan sentimen yang diwakilinya, yaitu hijau untuk positif, biru untuk netral, dan merah untuk negatif.

[Gambar 4.17 — Perbandingan Kata Menonjol per Sentimen]
Cara mendapatkan: *scroll* ke bagian "Perbandingan Kata Menonjol per Sentimen", lalu ambil *screenshot* tiga grafik yang tersusun berdampingan.
Penjelasan gambar: Gambar ini menampilkan tiga grafik batang horizontal berdampingan untuk tiga sentimen. Perbandingan ini memungkinkan identifikasi kata yang muncul secara eksklusif atau dominan pada satu sentimen tertentu dibandingkan sentimen lainnya.

Dari visualisasi ini dapat diidentifikasi bahwa beberapa kata seperti "tolak", "bahaya", dan "demokrasi" cenderung lebih sering muncul pada komentar negatif, sementara kata seperti "dukung" dan "setuju" lebih dominan pada komentar positif.

4.5.5 Kata Khas per Sentimen (Dominance Score)

Ditampilkan tiga grafik *dominance score* yang menunjukkan kata-kata paling "khas" untuk setiap sentimen. Kata khas didefinisikan sebagai kata yang proporsi kemunculannya pada satu sentimen jauh lebih tinggi dibandingkan rata-rata proporsinya pada keseluruhan data. Nilai *dominance* dihitung sebagai selisih antara persentase kata pada sentimen tertentu dengan persentase kata pada seluruh data.

[Gambar 4.18 — Grafik Dominance Score Kata Khas per Sentimen]
Cara mendapatkan: *scroll* ke bagian "Kata Khas per Sentimen" pada tab "Frekuensi Kata", lalu ambil *screenshot* tiga grafik batang horizontal yang disusun berdampingan.
Penjelasan gambar: Gambar ini memperlihatkan kata-kata yang paling unik untuk masing-masing sentimen berdasarkan selisih persentase. Kata dengan batang terpanjang berarti kata tersebut jauh lebih sering muncul pada sentimen tersebut dibandingkan rata-rata keseluruhan, sehingga dapat dianggap sebagai ciri khas sentimen itu.

Diakhiri tab frekuensi kata dengan tabel lengkap yang memuat kolom Kata, Frekuensi, Persentase, dan Kumulatif. Tabel ini dilengkapi dengan keterangan ringkasan di bagian bawah yang menunjukkan berapa persen total token yang disumbangkan oleh 10 kata teratas.


4.6 N-Gram dan Word Cloud

4.6.1 Gambaran Umum Tab N-Gram dan Word Cloud

Disajikan analisis *n-gram* dan *word cloud* pada tab keempat. Analisis *n-gram* digunakan untuk mengidentifikasi pasangan kata (*bigram*) atau tiga kata berurutan (*trigram*) yang sering muncul bersama dalam komentar. Visualisasi ini penting karena memberikan konteks yang lebih kaya dibandingkan analisis kata tunggal. Misalnya, kata "tidak" dan "setuju" yang masing-masing muncul secara terpisah akan memberikan makna yang berbeda dibandingkan ketika keduanya dianalisis sebagai pasangan "tidak setuju".

4.6.2 Grafik N-Gram Utama

Ditampilkan grafik batang horizontal yang menampilkan *n-gram* paling sering muncul berdasarkan pilihan tipe (*bigram* atau *trigram*) dan filter sentimen yang dipilih pengguna melalui panel kontrol di sebelah kiri. Grafik menggunakan gradasi warna ungu dari muda ke tua.

[Gambar 4.19 — Grafik N-Gram Utama]
Cara mendapatkan: buka tab "N-Gram & *Word Cloud*", pilih tipe *bigram* atau *trigram* dan sentimen tertentu, lalu ambil *screenshot* grafik batang horizontal yang muncul di sisi kanan panel kontrol.
Penjelasan gambar: Gambar ini menampilkan kombinasi dua atau tiga kata yang paling sering muncul bersama dalam komentar sesuai filter sentimen yang dipilih. Frasa seperti "revisi uu tni" atau "tolak ruu tni" yang muncul sebagai *n-gram* paling sering mencerminkan tema utama diskusi.

4.6.3 Perbandingan N-Gram per Sentimen

Ditampilkan tiga grafik *n-gram* secara berdampingan di bawah grafik utama untuk membandingkan frasa-frasa yang dominan pada setiap sentimen. Setiap grafik menggunakan warna sentimen yang sesuai.

[Gambar 4.20 — Perbandingan N-Gram per Sentimen]
Cara mendapatkan: *scroll* ke bagian "Perbandingan *N-Gram* per Sentimen", lalu ambil *screenshot* tiga grafik yang tersusun horizontal.
Penjelasan gambar: Gambar ini memperlihatkan perbedaan frasa dominan antara komentar positif, netral, dan negatif. Frasa pada komentar negatif cenderung berisi ekspresi penolakan, sementara frasa pada komentar positif cenderung berisi ekspresi dukungan atau pujian.


4.6.4 Word Cloud per Sentimen

Ditampilkan *word cloud* pada bagian bawah tab yang disusun dalam empat sub-tab, yaitu Positif, Netral, Negatif, dan Semua Label. Setiap *word cloud* dihasilkan dari komentar yang sesuai dengan kategori sentimennya menggunakan *colormap* yang berbeda, yaitu "Greens" untuk positif, "Blues" untuk netral, "Reds" untuk negatif, dan "viridis" untuk gabungan semua sentimen. Latar belakang *word cloud* disesuaikan dengan warna dominan sentimen untuk memberikan kesan visual yang konsisten.

[Gambar 4.21 — Word Cloud Sentimen Negatif]
Cara mendapatkan: buka sub-tab "Negatif" pada bagian *Word Cloud* di tab "N-Gram & *Word Cloud*", tunggu hingga *word cloud* selesai di-*render*, lalu ambil *screenshot*.
Penjelasan gambar: Gambar ini menampilkan *word cloud* dari seluruh komentar bersentimen negatif. Kata-kata berukuran besar mencerminkan frekuensi kemunculan tinggi dalam komentar negatif, dan warna merah digunakan untuk mempertegas identitas sentimen yang diwakili.

[Gambar 4.22 — Word Cloud Sentimen Positif]
Cara mendapatkan: buka sub-tab "Positif" pada bagian *Word Cloud*, tunggu *render* selesai, lalu ambil *screenshot*.
Penjelasan gambar: Gambar ini menampilkan *word cloud* dari komentar bersentimen positif dengan gradasi warna hijau. Kata-kata besar pada *word cloud* positif mencerminkan ekspresi dukungan atau apresiasi yang paling sering disebutkan oleh pengguna.

[Gambar 4.23 — Word Cloud Semua Label]
Cara mendapatkan: buka sub-tab "Semua Label" pada bagian *Word Cloud*, lalu ambil *screenshot*.
Penjelasan gambar: Gambar ini menampilkan *word cloud* dari keseluruhan 13.177 komentar tanpa filter sentimen menggunakan *colormap* "viridis". Gambaran ini mencerminkan topik-topik yang paling banyak dibicarakan secara keseluruhan dalam dataset.


4.7 Insight per Video

4.7.1 Gambaran Umum Tab Insight per Video

Disajikan analisis sentimen pada tingkat video individual pada tab kelima yang diberi judul "*Insight* per Video". Tab ini memungkinkan perbandingan respons publik antar video sehingga dapat diidentifikasi video mana yang paling banyak menuai komentar negatif dan video mana yang mendapatkan respons lebih positif.

4.7.2 Grafik Batang Bertumpuk Komentar per Video

Ditampilkan grafik batang bertumpuk (*stacked bar chart*) yang menampilkan jumlah komentar dari setiap video berdasarkan kategori sentimennya. Setiap batang mewakili satu video, dan setiap bagian batang menampilkan jumlah komentar untuk satu sentimen. Sumbu horizontal menampilkan judul video yang diperpendek, sedangkan sumbu vertikal menampilkan jumlah komentar.

[Gambar 4.24 — Grafik Batang Bertumpuk Komentar per Video]
Cara mendapatkan: buka tab "*Insight* per Video", lalu ambil *screenshot* grafik batang bertumpuk yang muncul di sisi kiri.
Penjelasan gambar: Gambar ini menampilkan perbandingan jumlah komentar dari lima video yang dianalisis. Setiap batang terdiri dari tiga bagian berwarna yang merepresentasikan sentimen positif (hijau), netral (biru), dan negatif (merah). Video dengan bagian merah paling tinggi berarti paling banyak mendapatkan komentar bernada negatif.

4.7.3 Grafik Donut Proporsi Sentimen per Video

Ditampilkan kumpulan grafik lingkaran berlubang (*donut chart*) yang disusun dalam *subplot* untuk setiap video di sebelah kanan grafik batang. Setiap *donut* menampilkan proporsi ketiga sentimen dalam bentuk persentase. Judul setiap grafik menggunakan judul video yang diperpendek untuk efisiensi ruang.

[Gambar 4.25 — Grafik Donut Proporsi Sentimen per Video]
Cara mendapatkan: ambil *screenshot* kumpulan grafik *donut* di sisi kanan pada tab "*Insight* per Video".
Penjelasan gambar: Gambar ini memperlihatkan proporsi sentimen dari masing-masing video dalam bentuk diagram lingkaran. Perbedaan ukuran irisan merah antar video menggambarkan perbedaan tingkat sentimen negatif yang diterima setiap video dari para komentator.


4.7.4 Tabel Metrik Lengkap per Video

Ditampilkan tabel ringkasan metrik yang memuat informasi kuantitatif lengkap untuk setiap video, yaitu judul video, total komentar, jumlah komentar positif, netral, negatif, persentase negatif, persentase positif, total *like*, dan rata-rata *like*. Tabel diurutkan berdasarkan persentase negatif dari yang tertinggi. Kolom "% Negatif" diberi *background gradient* merah dan kolom "% Positif" diberi *background gradient* hijau untuk memudahkan identifikasi visual.

[Gambar 4.26 — Tabel Metrik per Video]
Cara mendapatkan: *scroll* ke bawah pada tab "*Insight* per Video" setelah grafik, lalu ambil *screenshot* tabel yang memuat semua kolom metrik.
Penjelasan gambar: Gambar ini menampilkan tabel dengan gradasi warna pada kolom % Negatif dan % Positif. Video yang berada di baris paling atas memiliki persentase negatif tertinggi, ditandai dengan sel berwarna merah paling gelap.

Dari tabel ini dapat diketahui bahwa video dari kanal tertentu mendapatkan proporsi komentar negatif yang lebih tinggi, yang dapat mengindikasikan perbedaan sudut pandang penyajian konten dan komunitas penonton yang terlibat pada masing-masing kanal.

4.7.5 Kata Paling Sering per Video

Ditampilkan grafik batang horizontal untuk setiap video yang menunjukkan 10 kata yang paling sering muncul dalam komentar video tersebut. Grafik-grafik ini disusun dalam tata letak tiga kolom, dengan warna batang menggunakan gradasi biru muda ke biru tua berdasarkan frekuensi.

[Gambar 4.27 — Kata Paling Sering per Video]
Cara mendapatkan: *scroll* ke bagian "Kata Paling Sering per Video" pada tab "*Insight* per Video", lalu ambil *screenshot* kumpulan grafik batang horizontal yang disusun dalam tiga kolom.
Penjelasan gambar: Gambar ini memperlihatkan kata-kata yang paling dominan untuk setiap video secara individual. Perbedaan kata yang menonjol antar video mencerminkan perbedaan topik atau sudut pandang yang dibahas dalam masing-masing video, sekaligus memperlihatkan fokus diskusi yang berbeda pada komunitas komentator setiap kanal.


4.8 Pembahasan Hasil Analisis Sentimen

4.8.1 Dominasi Sentimen Negatif

Diidentifikasi bahwa sentimen negatif mendominasi keseluruhan dataset komentar YouTube terkait kebijakan RUU TNI. Kondisi ini konsisten antara data berlabel manual maupun data berlabel otomatis, yang mengindikasikan bahwa dominasi negatif bukan merupakan artefak dari metode pelabelan tertentu, melainkan mencerminkan respons publik yang sesungguhnya.

Dominasi sentimen negatif yang tinggi sejalan dengan konteks isu RUU TNI yang pada periode pengambilan data tengah menuai banyak penolakan dari berbagai kalangan masyarakat. Komentar-komentar yang mengandung kata seperti "tolak", "bahaya", "sipil", dan "demokrasi" mencerminkan kekhawatiran publik terhadap dampak kebijakan tersebut terhadap kehidupan sipil dan sistem demokrasi.

4.8.2 Pola Temporal dan Lonjakan Komentar

Ditemukan dari analisis tren waktu bahwa lonjakan komentar negatif terjadi pada periode-periode tertentu yang berkaitan langsung dengan perkembangan pembahasan RUU TNI. Lonjakan ini mengikuti pola reaktif, yaitu volume komentar meningkat tajam setelah ada pemberitaan atau peristiwa signifikan, kemudian menurun seiring berjalannya waktu.

Analisis *word cloud* pada periode puncak memberikan informasi tambahan mengenai isu-isu spesifik yang memicu reaksi publik pada tanggal atau bulan tertentu. Pola ini dapat dimanfaatkan untuk memahami dinamika pembentukan opini publik di media sosial.

4.8.3 Perbedaan Topik Antar Video

Diidentifikasi melalui analisis per video bahwa setiap video memiliki distribusi sentimen yang berbeda. Perbedaan ini dapat dikaitkan dengan sudut pandang konten yang disajikan oleh masing-masing kanal. Video yang menyajikan konten yang lebih kritis terhadap kebijakan cenderung mendapatkan komentar dengan proporsi negatif yang lebih tinggi, sedangkan video yang lebih bersifat informatif atau netral cenderung mendapatkan distribusi yang lebih seimbang.

Kata-kata yang dominan juga berbeda antar video, mencerminkan perbedaan fokus diskusi pada komunitas penonton yang berbeda. Analisis ini memberikan gambaran bahwa persepsi publik terhadap RUU TNI bervariasi tergantung pada sumber informasi yang dikonsumsi.

4.8.4 Konsistensi Pelabelan Manual dan Otomatis

Dibuktikan melalui grafik perbandingan distribusi bahwa pelabelan manual dan pelabelan otomatis menggunakan IndoBERT menghasilkan distribusi sentimen yang relatif konsisten. Perbedaan yang ada dalam rentang yang wajar mengindikasikan bahwa model IndoBERT mampu menangkap pola sentimen bahasa Indonesia dengan cukup baik pada konteks teks komentar YouTube terkait isu kebijakan publik.

Konsistensi ini penting karena memberikan kepercayaan bahwa data berlabel otomatis yang digunakan untuk melatih dan menguji model Logistic Regression dan Naive Bayes memiliki kualitas yang memadai untuk menghasilkan hasil klasifikasi yang dapat dipercaya.


4.9 Implikasi Ketidakseimbangan Kelas terhadap Model

Diidentifikasi melalui grafik *lollipop* bahwa terdapat ketidakseimbangan kelas (*class imbalance*) yang signifikan pada dataset yang digunakan untuk pelatihan model klasifikasi sentimen. Sentimen negatif mendominasi dengan proporsi yang jauh melebihi kondisi ideal 33,3%, sementara sentimen positif memiliki proporsi paling kecil.

Ketidakseimbangan ini memiliki implikasi terhadap performa model klasifikasi. Model yang dilatih pada data tidak seimbang cenderung memiliki performa lebih baik pada kelas mayoritas (negatif) dan performa lebih rendah pada kelas minoritas (positif). Hal ini perlu dipertimbangkan ketika menginterpretasikan hasil evaluasi model, terutama pada metrik *precision* dan *recall* untuk setiap kelas.

Beberapa strategi yang dapat diterapkan untuk mengatasi masalah ini antara lain menggunakan teknik *oversampling* pada kelas minoritas, *undersampling* pada kelas mayoritas, atau menggunakan pendekatan *class weighting* pada algoritma klasifikasi. Pada penelitian ini, penanganan ketidakseimbangan kelas dilakukan melalui pemilihan metrik evaluasi yang tepat dan analisis performa per kelas secara terpisah.

4.10 Pemanfaatan Dashboard dalam Analisis Sentimen

Dashboard visualisasi yang dikembangkan menggunakan *Streamlit* memberikan beberapa keunggulan dalam proses analisis sentimen komentar YouTube. Pertama, dashboard bersifat interaktif sehingga pengguna dapat melakukan eksplorasi data secara dinamis melalui filter dan kontrol yang tersedia. Kedua, visualisasi yang beragam memungkinkan analisis dari berbagai sudut pandang, mulai dari distribusi, tren waktu, hingga frekuensi kata dan frasa.

Ketiga, penggunaan warna yang konsisten antar visualisasi memudahkan interpretasi dan mengurangi beban kognitif pengguna. Keempat, dashboard dapat di-*refresh* untuk memuat data terbaru dari MongoDB sehingga mendukung analisis berkelanjutan ketika data baru ditambahkan.

Dashboard ini juga dapat dimanfaatkan sebagai alat bantu dalam proses *data storytelling* untuk menyampaikan temuan analisis sentimen kepada pemangku kepentingan yang tidak memiliki latar belakang teknis mendalam dalam bidang *data science* atau *text mining*.


4.11 Analisis Frekuensi Kata dan Konteks Sentimen

Ditemukan dari analisis frekuensi kata bahwa kata-kata yang paling sering muncul dalam dataset tidak hanya mencakup kata-kata netral seperti "tni", "uu", dan "ruu", tetapi juga kata-kata yang bermuatan emosional seperti "tolak", "bahaya", dan "demokrasi". Distribusi kata-kata ini berbeda antar sentimen, di mana kata "tolak" dan "bahaya" jauh lebih dominan pada komentar negatif dibandingkan komentar positif atau netral.

Analisis *n-gram* memberikan konteks yang lebih kaya dengan menunjukkan pasangan atau rangkaian kata yang sering muncul bersama. Frasa seperti "tolak ruu tni", "bahaya sipil", dan "demokrasi terancam" mendominasi *bigram* dan *trigram* pada komentar negatif, sementara frasa seperti "dukung kebijakan" atau "setuju pemerintah" lebih dominan pada komentar positif.

Temuan ini mengonfirmasi bahwa klasifikasi sentimen tidak hanya bergantung pada keberadaan kata tunggal, tetapi juga pada konteks dan kombinasi kata. Hal ini menjadi salah satu alasan mengapa metode TF-IDF yang digunakan pada penelitian ini tidak hanya mempertimbangkan frekuensi kata tunggal (*unigram*), tetapi juga *bigram* untuk menangkap konteks lokal dalam teks komentar.

4.12 Analisis Interaksi Publik melalui Jumlah Like

Ditemukan bahwa komentar dengan sentimen positif cenderung menerima rata-rata jumlah *like* yang lebih tinggi dibandingkan komentar negatif atau netral. Pola ini mengindikasikan bahwa meskipun komentar negatif mendominasi dari segi kuantitas, komentar positif mendapatkan dukungan yang lebih kuat dari komunitas pengguna yang ditunjukkan melalui pemberian *like*.

Temuan ini memberikan dimensi tambahan dalam memahami opini publik di media sosial. Volume komentar negatif yang tinggi tidak serta-merta berarti dominasi opini secara keseluruhan, karena intensitas dukungan terhadap komentar positif dapat mencerminkan adanya kelompok pengguna yang tidak vokal dalam berkomentar tetapi aktif dalam memberikan *like* sebagai bentuk dukungan.

Analisis ini menunjukkan pentingnya mempertimbangkan berbagai metrik interaksi sosial, bukan hanya jumlah komentar, untuk memahami dinamika opini publik secara lebih komprehensif.



---

CATATAN PENGAMBILAN GAMBAR

Seluruh gambar yang tercantum dalam Bab 4 ini perlu diambil langsung dari tampilan dashboard yang berjalan. Berikut panduan lengkapnya:

1. Pastikan Streamlit berjalan dengan perintah: streamlit run dashboard_eda.py
2. Buka browser di http://localhost:8501
3. Pastikan koneksi ke MongoDB aktif (indikator "MongoDB terhubung" di sidebar)
4. Klik "Refresh Data" di sidebar sebelum mengambil gambar untuk memastikan data terbaru
5. Untuk setiap gambar, navigasikan ke tab dan bagian yang sesuai, lalu gunakan tombol Print Screen
   atau alat tangkapan layar seperti Snipping Tool (Windows) untuk mengambil screenshot
6. Simpan gambar dengan nama sesuai nomor gambar (misal: Gambar_4_1_Dashboard_Utama.png)
7. Tempelkan gambar pada posisi yang ditandai "[Gambar X.X — ...]" dalam dokumen laporan

Urutan gambar yang perlu diambil:
- Gambar 4.1  : Tampilan halaman utama dashboard (header + tab navigasi)
- Gambar 4.2  : Enam kartu metrik di bagian atas
- Gambar 4.3  : Grafik batang distribusi sentimen (sub-tab Gabungan)
- Gambar 4.4  : Grafik donut proporsi sentimen
- Gambar 4.5  : Grafik lollipop ketidakseimbangan kelas
- Gambar 4.6  : Grafik batang grouped perbandingan manual vs auto vs gabungan
- Gambar 4.7  : Grafik batang rata-rata like per sentimen + tabel
- Gambar 4.8  : Filter rentang tanggal dan granularitas (tab Tren Waktu)
- Gambar 4.9  : Grafik garis tren positif vs negatif dengan anotasi puncak
- Gambar 4.10 : Dua word cloud lonjakan (puncak negatif + puncak positif)
- Gambar 4.11 : Grafik batang bertumpuk tren bulanan
- Gambar 4.12 : Grafik garis tren sentimen per bulan
- Gambar 4.13 : Dua word cloud penyebab lonjakan bulan puncak
- Gambar 4.14 : Grafik area stacked + grafik batang rasio negatif
- Gambar 4.15 : Grafik batang vertikal top N kata (tab Frekuensi Kata)
- Gambar 4.16 : Grafik batang horizontal persentase kata
- Gambar 4.17 : Tiga grafik perbandingan kata per sentimen
- Gambar 4.18 : Tiga grafik dominance score kata khas
- Gambar 4.19 : Grafik n-gram utama (tab N-Gram & Word Cloud)
- Gambar 4.20 : Tiga grafik n-gram per sentimen
- Gambar 4.21 : Word cloud sentimen negatif
- Gambar 4.22 : Word cloud sentimen positif
- Gambar 4.23 : Word cloud semua label
- Gambar 4.24 : Grafik batang bertumpuk komentar per video (tab Insight per Video)
- Gambar 4.25 : Kumpulan grafik donut per video
- Gambar 4.26 : Tabel metrik per video dengan gradient warna
- Gambar 4.27 : Kumpulan grafik kata paling sering per video
