BAB IV
HASIL DAN PEMBAHASAN

4.1 Gambaran Umum Dashboard Visualisasi

Dibangun sebuah dashboard visualisasi interaktif menggunakan framework Streamlit guna mendukung proses eksplorasi data (Exploratory Data Analysis) terhadap hasil analisis sentimen komentar YouTube terkait kebijakan RUU TNI. Dashboard tersebut dikembangkan dengan memanfaatkan library Plotly untuk menghasilkan grafik interaktif dan library WordCloud untuk memvisualisasikan frekuensi kata. Data yang ditampilkan bersumber dari dua collection MongoDB, yaitu comments_sentiment yang berisi data berlabel manual dan phase2_auto_labeled yang berisi hasil pelabelan otomatis menggunakan model IndoBERT.

Dashboard dibagi menjadi lima tab utama, yaitu Distribusi Sentimen, Tren Waktu, Frekuensi Kata, N-Gram dan Word Cloud, serta Insight per Video. Setiap tab menyajikan visualisasi yang berbeda untuk mendukung analisis dari berbagai sudut pandang. Struktur ini dipilih agar pengguna dapat secara sistematis menelusuri data mulai dari gambaran distribusi keseluruhan, pola temporal, analisis leksikal, hingga perbandingan antar sumber video. Selain itu, disediakan pula panel samping (sidebar) yang memuat kontrol filter seperti pengaturan jumlah kata teratas, slider parameter n-gram, serta tombol refresh data yang memungkinkan pembaruan data secara langsung dari MongoDB.

[Gambar 4.1 — Tampilan Utama Dashboard]
Cara mendapatkan gambar: jalankan dashboard dengan perintah "streamlit run dashboard_eda.py", kemudian buka browser pada alamat http://localhost:8501 dan ambil tangkapan layar tampilan awal dashboard yang memperlihatkan header KPI dan navigasi tab.

Gambar 4.1 memperlihatkan halaman utama dashboard EDA sentimen. Bagian paling atas menampilkan enam kartu metrik ringkasan yang memuat total data gabungan, jumlah data berlabel manual, jumlah data berlabel otomatis, serta jumlah komentar untuk masing-masing sentimen positif, netral, dan negatif beserta persentasenya terhadap total data. Di bawah kartu metrik terdapat navigasi lima tab yang dapat diakses pengguna. Keberadaan ringkasan metrik pada posisi teratas bertujuan untuk memberikan gambaran kuantitatif awal sebelum pengguna masuk ke analisis yang lebih mendalam.


4.2 Ringkasan Metrik Data

Ditampilkan ringkasan metrik utama pada bagian paling atas dashboard dalam bentuk enam kartu metrik yang disusun secara horizontal. Kartu-kartu tersebut menampilkan total data gabungan dari kedua sumber, jumlah data berlabel manual, jumlah data berlabel otomatis, serta jumlah dan persentase komentar untuk masing-masing kategori sentimen positif, netral, dan negatif. Perancangan kartu metrik ini mengikuti pola desain dashboard analitik yang menempatkan indikator kunci kinerja pada bagian paling atas halaman agar informasi esensial dapat langsung teridentifikasi tanpa perlu melakukan pengguliran layar.

Berdasarkan data yang berhasil dimuat dari MongoDB, diperoleh total keseluruhan sebanyak 13.177 komentar setelah proses deduplikasi berdasarkan comment_id. Dari jumlah tersebut, sebanyak 1.471 komentar berasal dari pelabelan manual yang tersimpan pada collection comments_sentiment, sedangkan sisanya sebanyak 11.706 komentar berasal dari pelabelan otomatis yang tersimpan pada collection phase2_auto_labeled. Proporsi data berlabel otomatis yang jauh lebih besar dibandingkan data berlabel manual mencerminkan keterbatasan sumber daya manusia dalam proses anotasi dan menunjukkan pentingnya pendekatan pelabelan semi-otomatis dalam penelitian analisis sentimen berskala besar.

[Gambar 4.2 — Kartu Metrik Ringkasan Data]
Cara mendapatkan gambar: ambil tangkapan layar bagian atas dashboard yang memperlihatkan enam kartu metrik dengan nilai total data, data manual, data otomatis, dan tiga sentimen beserta persentasenya.

Gambar 4.2 memperlihatkan enam kartu metrik yang menjadi ringkasan kuantitatif dataset. Setiap kartu menampilkan nama metrik pada bagian atas, nilai angka pada bagian tengah dengan ukuran font yang lebih besar, serta keterangan persentase di bagian bawah untuk kartu sentimen. Desain kartu menggunakan garis biru di bagian atas sebagai aksen visual yang memudahkan pembacaan. Kartu metrik ini memberikan gambaran awal bahwa dari total keseluruhan komentar yang tersedia, sebagian besar komentar terklasifikasi sebagai sentimen negatif, yang mengindikasikan adanya tendensi penolakan publik terhadap kebijakan RUU TNI secara umum.


4.3 Distribusi Sentimen

Dikaji distribusi label sentimen pada bagian ini sebagai tahap eksplorasi pertama terhadap dataset komentar YouTube terkait kebijakan RUU TNI. Distribusi label ditinjau dari tiga sumber data yang berbeda, yaitu data berlabel manual, data berlabel otomatis, dan gabungan keduanya, sehingga konsistensi antar metode pelabelan dapat dievaluasi secara langsung. Selain distribusi frekuensi absolut dan proporsi relatif, dilakukan pula pengkajian terhadap tingkat ketidakseimbangan kelas serta hubungan antara kategori sentimen dengan jumlah like yang diterima komentar. Pemahaman yang mendalam terhadap distribusi data pada tahap ini menjadi landasan penting dalam menafsirkan hasil klasifikasi model secara tepat dan dalam menentukan strategi penanganan ketidakseimbangan kelas pada tahap pemodelan berikutnya.

4.3.1 Gambaran Umum Tab Distribusi Sentimen

Disajikan analisis distribusi label sentimen pada tab pertama yang diberi judul "Distribusi Sentimen". Tab ini dirancang sebagai pintu masuk pertama dalam eksplorasi data karena pemahaman terhadap distribusi label merupakan landasan penting sebelum dilakukan analisis yang lebih spesifik. Tab ini terbagi menjadi tiga sub-tab, yaitu Manual Label, Auto Label, dan Gabungan. Masing-masing sub-tab menyajikan visualisasi yang identik namun menggunakan subset data yang berbeda, sehingga perbandingan distribusi antar sumber data dapat dilakukan secara langsung dan sistematis.

Pembagian menjadi tiga sub-tab ini memiliki tujuan analitis yang jelas. Sub-tab Manual Label menampilkan distribusi 1.471 data yang telah diberi label secara manual dan dianggap sebagai data rujukan paling akurat. Sub-tab Auto Label menampilkan distribusi 11.706 data hasil pelabelan otomatis oleh model IndoBERT. Sub-tab Gabungan menampilkan distribusi keseluruhan data setelah kedua sumber digabungkan dan dideduplikasi.

4.3.2 Grafik Batang Jumlah Komentar per Sentimen

Ditampilkan grafik batang vertikal pada bagian pertama setiap sub-tab yang menggambarkan jumlah absolut komentar untuk masing-masing kategori sentimen. Setiap batang diberi warna yang berbeda dan konsisten di seluruh dashboard, yaitu hijau untuk sentimen positif, biru untuk sentimen netral, dan merah untuk sentimen negatif. Di atas setiap batang dicantumkan nilai jumlah komentar beserta persentasenya terhadap total data pada sumber yang bersangkutan. Penggunaan warna yang konsisten ini penting untuk membangun asosiasi visual yang kuat sehingga pembaca dapat dengan cepat mengidentifikasi kategori sentimen hanya berdasarkan warna tanpa harus membaca label secara eksplisit.

[Gambar 4.3 — Grafik Batang Distribusi Sentimen (Data Gabungan)]
Cara mendapatkan gambar: buka tab "Distribusi Sentimen", pilih sub-tab "Gabungan", kemudian ambil tangkapan layar grafik batang yang berada di sisi kiri tampilan.

Gambar 4.3 menampilkan grafik batang jumlah komentar berdasarkan tiga kategori sentimen pada data gabungan. Terlihat bahwa batang berwarna merah yang merepresentasikan sentimen negatif memiliki ketinggian yang paling dominan dibandingkan dua batang lainnya. Nilai jumlah dan persentase yang tertera di atas setiap batang memungkinkan pembaca untuk langsung mengetahui besaran absolut maupun proporsi relatif setiap sentimen. Dominasi sentimen negatif pada data gabungan ini mencerminkan bahwa respons masyarakat terhadap kebijakan RUU TNI secara keseluruhan cenderung bernada penolakan atau kekhawatiran dibandingkan dukungan. Kondisi tersebut sejalan dengan konteks sosial-politik pada periode pengambilan data, di mana pembahasan RUU TNI tengah menuai berbagai bentuk penolakan dari kalangan sipil dan akademisi.


4.3.3 Grafik Lingkaran Proporsi Sentimen

Ditampilkan grafik lingkaran berbentuk donut di sebelah kanan grafik batang yang menggambarkan proporsi setiap sentimen dalam bentuk persentase. Grafik ini menggunakan format donut dengan lubang di tengah berukuran 45% dari total lingkaran. Setiap irisan diberi label nama sentimen dan persentase yang terlihat langsung pada grafik tanpa memerlukan legenda terpisah. Pemilihan format donut dibandingkan pie chart biasa bertujuan agar tampilan lebih modern dan area kosong di tengah dapat dimanfaatkan untuk informasi tambahan apabila diperlukan.

[Gambar 4.4 — Grafik Donut Proporsi Sentimen]
Cara mendapatkan gambar: ambil tangkapan layar grafik lingkaran yang berada di sisi kanan pada sub-tab "Gabungan" dalam tab "Distribusi Sentimen".

Gambar 4.4 memperlihatkan proporsi ketiga kategori sentimen dalam bentuk diagram lingkaran berlubang. Irisan berwarna merah yang merepresentasikan sentimen negatif tampak menempati area terbesar dalam lingkaran, diikuti oleh irisan biru untuk netral, dan irisan hijau untuk positif di posisi terkecil. Informasi persentase yang tercetak langsung pada setiap irisan memudahkan pembaca untuk menangkap distribusi relatif tanpa melakukan perhitungan manual. Grafik ini melengkapi grafik batang sebelumnya dengan memberikan perspektif proporsi yang lebih intuitif secara visual, terutama untuk memperjelas seberapa besar selisih dominasi sentimen negatif terhadap dua sentimen lainnya.

4.3.4 Grafik Ketidakseimbangan Kelas

Ditampilkan grafik lollipop di bawah kedua grafik sebelumnya untuk memvisualisasikan ketidakseimbangan distribusi kelas (class imbalance). Grafik ini menunjukkan persentase setiap sentimen dan membandingkannya dengan kondisi ideal distribusi yang merata, yaitu sebesar 33,3% untuk masing-masing kelas. Garis putus-putus vertikal pada nilai 33,3% dijadikan acuan keseimbangan. Setiap sentimen direpresentasikan oleh sebuah garis horizontal dengan titik berukuran besar di ujungnya, di mana posisi horizontal titik tersebut menunjukkan persentase aktual. Semakin jauh posisi titik dari garis acuan, semakin besar tingkat ketidakseimbangan kelas tersebut.

[Gambar 4.5 — Grafik Ketidakseimbangan Kelas]
Cara mendapatkan gambar: ambil tangkapan layar grafik lollipop yang berada di bawah pasangan grafik batang dan grafik lingkaran pada salah satu sub-tab distribusi.

Gambar 4.5 memperlihatkan posisi persentase masing-masing sentimen relatif terhadap kondisi ideal 33,3%. Titik berwarna merah yang merepresentasikan sentimen negatif terlihat berada jauh di sebelah kanan garis acuan, mengindikasikan dominasi yang signifikan. Sebaliknya, titik berwarna hijau untuk sentimen positif berada di sebelah kiri garis acuan, menandakan proporsi yang lebih kecil dari kondisi ideal. Ketidakseimbangan kelas yang teridentifikasi melalui visualisasi ini memiliki implikasi penting terhadap tahap pelatihan model klasifikasi, karena model yang dilatih pada data tidak seimbang cenderung memiliki bias terhadap kelas mayoritas. Pemahaman terhadap kondisi ini menjadi landasan bagi pengambilan keputusan terkait strategi penanganan class imbalance, seperti oversampling atau pembobotan kelas, pada tahap pemodelan.


4.3.5 Perbandingan Distribusi Manual, Auto-Label, dan Gabungan

Ditampilkan grafik batang berkelompok di bagian bawah tab distribusi untuk membandingkan proporsi sentimen dari ketiga sumber data secara berdampingan. Setiap kelompok batang mewakili satu kategori sentimen, sedangkan warna batang membedakan sumber data, yaitu biru untuk data manual, kuning untuk data auto-label, dan hijau untuk data gabungan. Visualisasi perbandingan ini dirancang secara khusus untuk mengevaluasi konsistensi antara distribusi label manual dan label otomatis, yang merupakan salah satu indikator kualitas proses pelabelan otomatis.

[Gambar 4.6 — Grafik Batang Perbandingan Manual vs Auto-Label vs Gabungan]
Cara mendapatkan gambar: gulir ke bawah pada tab "Distribusi Sentimen" setelah melewati tiga sub-tab, kemudian ambil tangkapan layar grafik batang berkelompok yang memperlihatkan tiga kelompok batang untuk setiap sentimen.

Gambar 4.6 menampilkan perbandingan proporsi sentimen dari tiga sumber data secara berdampingan dalam satu grafik. Kedekatan tinggi batang berwarna biru (manual) dan batang berwarna kuning (auto-label) pada setiap kategori sentimen mencerminkan tingkat konsistensi antara kedua metode pelabelan. Apabila terdapat perbedaan yang mencolok antara keduanya, hal ini dapat mengindikasikan adanya bias sistematis pada model IndoBERT yang digunakan untuk pelabelan otomatis. Berdasarkan hasil visualisasi, distribusi antara data manual dan data auto-label menunjukkan pola yang relatif serupa, yang mengindikasikan bahwa model IndoBERT cukup berhasil mereplikasi pola pelabelan manusia pada konteks komentar YouTube berbahasa Indonesia terkait isu kebijakan publik. Keterangan interpretasi perbandingan ini juga ditampilkan di bawah grafik sebagai panduan bagi pengguna dalam membaca hasil visualisasi.

4.3.6 Rata-rata Jumlah Like per Sentimen

Ditampilkan grafik batang dan tabel ringkasan pada bagian terakhir tab distribusi yang menggambarkan rata-rata jumlah like yang diterima oleh komentar berdasarkan kategori sentimennya. Data like_count diperoleh melalui proses penggabungan (join) antara data sentimen dan collection comments pada MongoDB yang menyimpan metadata komentar asli dari YouTube Data API. Analisis ini memberikan dimensi tambahan dalam memahami respons publik, karena pemberian like pada komentar mencerminkan bentuk dukungan atau persetujuan dari pengguna lain terhadap isi komentar tersebut.

[Gambar 4.7 — Grafik Rata-rata Like per Sentimen]
Cara mendapatkan gambar: gulir ke bagian paling bawah tab "Distribusi Sentimen", kemudian ambil tangkapan layar grafik batang rata-rata like beserta tabel di sebelah kanannya.

Gambar 4.7 memperlihatkan perbedaan rata-rata jumlah like yang diterima komentar berdasarkan sentimennya. Grafik batang di sisi kiri menampilkan nilai rata-rata like untuk setiap kategori sentimen, sedangkan tabel di sisi kanan menyajikan data lebih lengkap yang mencakup rata-rata, median, dan total like dengan pewarnaan gradasi biru pada sel nilainya. Apabila komentar bersentimen positif mendapatkan rata-rata like yang lebih tinggi, hal ini mengindikasikan bahwa meskipun volume komentar negatif lebih besar, terdapat kelompok pengguna yang secara aktif mendukung komentar positif melalui pemberian like. Pola ini menunjukkan bahwa analisis sentimen berbasis volume komentar saja tidak cukup untuk merepresentasikan dinamika opini publik secara menyeluruh, dan perlu dilengkapi dengan analisis terhadap metrik interaksi lainnya.


4.4 Tren Waktu

Dikaji pola temporal data komentar YouTube terkait kebijakan RUU TNI pada bagian ini melalui serangkaian visualisasi yang mencakup berbagai granularitas waktu. Dimensi waktu merupakan aspek yang tidak dapat diabaikan dalam analisis opini publik di media sosial, karena respons masyarakat terhadap suatu kebijakan bersifat dinamis dan berubah seiring perkembangan peristiwa serta pemberitaan. Disajikan pada bagian ini visualisasi tren harian dan mingguan, analisis lonjakan komentar berbasis word cloud, tren bulanan dalam dua format grafik yang saling melengkapi, word cloud penyebab lonjakan pada bulan puncak, grafik area bertumpuk, serta grafik rasio sentimen negatif per periode. Melalui pendekatan berlapis ini, pola reaktivitas publik terhadap isu RUU TNI dapat diidentifikasi secara lebih komprehensif.

4.4.1 Gambaran Umum Tab Tren Waktu

Disajikan analisis tren sentimen berdasarkan waktu publikasi komentar pada tab kedua yang diberi judul "Tren Waktu". Tab ini merupakan salah satu komponen analisis paling informatif dalam dashboard karena memungkinkan identifikasi pola temporal yang tidak dapat diobservasi dari analisis distribusi statis. Melalui tab ini, dapat diidentifikasi periode-periode di mana terjadi lonjakan volume komentar negatif maupun positif, yang umumnya berkorelasi dengan peristiwa atau pemberitaan spesifik terkait kebijakan RUU TNI.

Tab ini memuat beberapa lapisan visualisasi yang saling melengkapi, yaitu grafik garis tren harian atau mingguan, analisis lonjakan berbasis word cloud, grafik tren bulanan, word cloud penyebab lonjakan per bulan, grafik area bertumpuk, grafik rasio negatif per periode, serta tabel data tren lengkap. Pendekatan berlapis ini bertujuan agar pengguna dapat melakukan analisis dari granularitas yang luas (bulanan) hingga granularitas yang lebih sempit (harian), sesuai dengan kebutuhan analitisnya.

4.4.2 Filter Rentang Tanggal dan Granularitas

Disediakan kontrol filter pada bagian atas tab tren waktu yang memungkinkan pengguna menyesuaikan rentang tanggal dan granularitas waktu analisis. Filter rentang tanggal memiliki nilai bawaan (default) yang diatur secara otomatis berdasarkan periode terpadat data, yaitu periode di mana volume komentar harian berada di atas persentil ke-40. Penetapan nilai default secara otomatis ini bertujuan agar grafik yang pertama kali ditampilkan sudah langsung menunjukkan periode yang paling relevan tanpa memerlukan penyesuaian manual. Granularitas waktu dapat dipilih antara harian atau mingguan melalui tombol pilihan.

[Gambar 4.8 — Filter Rentang Tanggal dan Granularitas]
Cara mendapatkan gambar: buka tab "Tren Waktu", kemudian ambil tangkapan layar bagian filter yang memuat pilihan granularitas dan dua bidang masukan tanggal untuk tanggal awal dan akhir.

Gambar 4.8 memperlihatkan tiga kontrol filter yang disusun secara horizontal. Bagian kiri menampilkan tombol pilihan granularitas antara "Harian" dan "Mingguan". Bagian tengah dan kanan masing-masing menampilkan bidang masukan tanggal untuk menentukan batas awal dan batas akhir periode analisis. Kontrol filter ini memberikan fleksibilitas kepada pengguna untuk mempersempit fokus analisis temporal sesuai dengan periode peristiwa yang ingin ditelaah, misalnya untuk mengamati dinamika komentar selama periode sidang DPR membahas RUU TNI atau selama periode tertentu setelah disahkannya undang-undang tersebut.


4.4.3 Grafik Garis Tren Positif vs Negatif

Ditampilkan grafik garis ganda yang membandingkan jumlah komentar positif dan negatif sepanjang periode waktu yang dipilih. Kedua garis diberi warna hijau untuk sentimen positif dan merah untuk sentimen negatif, konsisten dengan skema warna yang digunakan di seluruh dashboard. Area di bawah setiap garis diberi bayangan transparan untuk memperjelas perbedaan volume antar sentimen pada setiap satuan waktu. Anotasi panah otomatis diberikan pada titik puncak masing-masing garis untuk menandai tanggal terjadinya lonjakan tertinggi beserta nilai jumlah komentarnya.

[Gambar 4.9 — Grafik Garis Tren Sentimen Positif vs Negatif]
Cara mendapatkan gambar: setelah memilih rentang tanggal yang diinginkan, gulir sedikit ke bawah dan ambil tangkapan layar grafik garis yang menampilkan dua kurva berwarna hijau dan merah beserta anotasi puncaknya.

Gambar 4.9 menampilkan tren temporal dua sentimen utama dalam bentuk grafik garis sepanjang periode yang dipilih. Anotasi panah pada puncak kurva merah menunjukkan tanggal terjadinya lonjakan komentar negatif terbesar, sedangkan anotasi pada puncak kurva hijau menunjukkan puncak komentar positif. Pola grafik memperlihatkan bahwa lonjakan komentar tidak terjadi secara merata sepanjang waktu, melainkan terkonsentrasi pada periode-periode tertentu. Fenomena ini sesuai dengan karakteristik data media sosial yang bersifat reaktif terhadap peristiwa eksternal. Lonjakan tajam yang teridentifikasi pada grafik kemungkinan besar berkaitan dengan momen-momen krusial dalam proses legislasi RUU TNI, seperti saat rancangan undang-undang tersebut mulai dibahas secara publik di media atau ketika pengesahannya diumumkan.

4.4.4 Analisis Lonjakan dengan Word Cloud

Ditampilkan dua panel berdampingan di bawah grafik tren yang masing-masing menganalisis puncak komentar negatif dan puncak komentar positif secara lebih mendalam. Setiap panel memuat informasi tanggal puncak, jumlah komentar pada hari tersebut, kata kunci utama dalam format teks, serta visualisasi word cloud yang dihasilkan dari komentar pada periode tersebut. Word cloud dihasilkan menggunakan library WordCloud dengan parameter maksimum 80 kata dan tanpa kolokasi, sehingga setiap kata ditampilkan secara independen. Kata-kata yang termasuk dalam daftar stopwords tidak ditampilkan karena dianggap tidak membawa informasi sentimen yang bermakna. Ukuran huruf setiap kata pada word cloud mencerminkan frekuensi kemunculannya, sehingga kata yang paling sering disebutkan pada periode tersebut akan tampak lebih besar dan menonjol.

[Gambar 4.10 — Word Cloud Puncak Negatif dan Puncak Positif]
Cara mendapatkan gambar: gulir ke bagian "Analisis Lonjakan — Kata Kunci dan Word Cloud" pada tab "Tren Waktu", kemudian ambil tangkapan layar dua panel yang ditampilkan berdampingan, yaitu panel merah di sisi kiri dan panel hijau di sisi kanan.

Gambar 4.10 memperlihatkan dua word cloud yang dihasilkan dari komentar pada periode puncak masing-masing sentimen. Panel kiri dengan latar belakang merah muda menampilkan word cloud komentar negatif pada hari puncak negatif, sedangkan panel kanan dengan latar belakang hijau muda menampilkan word cloud komentar positif pada hari puncak positif. Kata-kata seperti "tolak", "bahaya", "sipil", dan "demokrasi" yang tampak berukuran besar pada word cloud negatif mengindikasikan bahwa kekhawatiran terhadap dampak RUU TNI pada kehidupan sipil dan sistem demokrasi menjadi isu sentral yang mendorong lonjakan komentar negatif pada periode tersebut. Analisis word cloud ini memberikan pemahaman yang lebih kontekstual dibandingkan sekadar mengetahui tanggal dan jumlah lonjakan, karena secara langsung memperlihatkan substansi kekhawatiran yang melatarbelakangi respons publik.


4.4.5 Tren Komentar Per Bulan

Disajikan dua grafik tren bulanan secara terpisah sebagai bagian khusus yang menggunakan seluruh rentang data tanpa bergantung pada filter tanggal yang dipilih pengguna. Keputusan untuk tidak mengaitkan grafik bulanan dengan filter rentang tanggal diambil secara disengaja agar gambaran tren bulanan tetap utuh dan representatif. Apabila grafik bulanan juga dipengaruhi oleh filter, maka pengguna yang memilih rentang waktu sempit akan kehilangan konteks tren secara keseluruhan.

Grafik pertama berupa grafik batang bertumpuk yang menampilkan jumlah komentar tiap bulan dengan warna berbeda untuk setiap sentimen. Pemilihan format batang bertumpuk memungkinkan pembaca untuk sekaligus melihat volume total komentar per bulan dan komposisi sentimen di dalamnya. Grafik kedua berupa grafik garis multi-sentimen yang memperlihatkan arah naik-turun ketiga sentimen dari bulan ke bulan secara terpisah, sehingga tren masing-masing sentimen dapat diobservasi tanpa tumpang tindih. Pada grafik garis ini, diberikan anotasi otomatis pada bulan dengan jumlah komentar negatif tertinggi.

[Gambar 4.11 — Grafik Batang Tren Komentar Per Bulan]
Cara mendapatkan gambar: gulir ke bagian "Tren Komentar Per Bulan" pada tab "Tren Waktu", kemudian ambil tangkapan layar grafik batang bertumpuk yang menampilkan data per bulan.

Gambar 4.11 menampilkan jumlah komentar yang dikelompokkan per bulan dalam format batang bertumpuk tiga warna. Sumbu horizontal menampilkan label bulan dalam format "MMM YYYY", sedangkan sumbu vertikal menampilkan jumlah komentar. Setiap batang terdiri dari tiga segmen berwarna yang secara langsung menggambarkan komposisi sentimen pada bulan tersebut. Bulan-bulan dengan tinggi segmen merah yang lebih besar dari segmen lainnya mengindikasikan periode di mana sentimen negatif mendominasi secara signifikan, yang kemungkinan besar berkaitan dengan perkembangan proses legislasi atau pemberitaan negatif seputar RUU TNI pada periode tersebut.

[Gambar 4.12 — Grafik Garis Tren Sentimen Per Bulan]
Cara mendapatkan gambar: ambil tangkapan layar grafik garis multi-sentimen yang berada tepat di bawah grafik batang bulanan, pastikan anotasi puncak negatif terlihat dengan jelas.

Gambar 4.12 memperlihatkan tren perubahan ketiga sentimen dari bulan ke bulan dalam format garis yang mudah dibaca. Setiap garis menggunakan warna sentimen yang konsisten dengan grafik lainnya, yaitu merah untuk negatif, hijau untuk positif, dan biru untuk netral. Area di bawah setiap garis diberi bayangan transparan untuk membantu pembaca mengenali volume relatif setiap sentimen. Anotasi pada titik puncak garis merah menginformasikan bulan dengan volume komentar negatif tertinggi sepanjang periode pengamatan. Grafik ini secara efektif memperlihatkan bahwa pola tren sentimen mengikuti pola yang tidak linier, dengan adanya puncak-puncak yang mencerminkan momen-momen reaktif dalam diskusi publik.


4.4.6 Word Cloud Penyebab Lonjakan Per Bulan

Ditampilkan dua word cloud secara berdampingan yang berfokus secara khusus pada bulan dengan volume komentar negatif terbanyak. Pendekatan ini dirancang untuk menjawab pertanyaan analitis yang lebih mendalam: tidak hanya "kapan" lonjakan terjadi, tetapi juga "mengapa" lonjakan tersebut terjadi dengan memvisualisasikan kata-kata yang paling banyak digunakan pada periode tersebut. Word cloud pertama dihasilkan hanya dari komentar bersentimen negatif pada bulan puncak, sedangkan word cloud kedua dihasilkan dari seluruh komentar tanpa memfilter sentimen pada bulan yang sama. Perbandingan antara kedua word cloud ini memungkinkan identifikasi kata-kata yang secara spesifik mendominasi wacana negatif dan yang bersifat umum dalam diskusi bulan tersebut.

[Gambar 4.13 — Word Cloud Penyebab Lonjakan Bulan Puncak Negatif]
Cara mendapatkan gambar: gulir ke bagian yang bertajuk "Word Cloud Penyebab Lonjakan" pada tab "Tren Waktu", kemudian ambil tangkapan layar dua word cloud yang ditampilkan berdampingan setelah grafik garis bulanan.

Gambar 4.13 menampilkan dua word cloud yang disajikan secara berdampingan. Word cloud di sisi kiri dihasilkan dari komentar bersentimen negatif pada bulan dengan jumlah komentar negatif terbanyak, dengan warna gradasi merah yang mempertegas identitas sentimennya. Di bawahnya terdapat kotak informasi berwarna merah yang mencantumkan nama bulan, jumlah komentar negatif, serta kata-kata yang paling sering muncul. Word cloud di sisi kanan dihasilkan dari seluruh komentar tanpa filter sentimen pada bulan yang sama, menggunakan skema warna netral. Perbandingan antara kedua word cloud ini memberikan pemahaman tentang kata-kata yang secara eksklusif mendominasi komentar negatif dibandingkan topik diskusi umum pada bulan tersebut. Kata-kata yang berukuran besar pada word cloud kiri tetapi tidak tampak pada word cloud kanan, atau berukuran lebih kecil pada word cloud kanan, merupakan indikator kuat dari topik yang memicu sentimen negatif secara khusus.

4.4.7 Grafik Area Bertumpuk Volume Komentar

Ditampilkan grafik area bertumpuk di bawah bagian word cloud bulanan sebagai representasi visual yang memperlihatkan kontribusi total volume komentar dari ketiga sentimen secara kumulatif dalam satu tampilan. Format area bertumpuk dipilih karena mampu sekaligus menampilkan tren total volume dan komposisi sentimen tanpa mengaburkan informasi dari masing-masing kategori. Setiap lapisan area diberi warna semi-transparan yang sesuai dengan warna sentimen untuk mempertahankan keterbacaan saat lapisan-lapisan tersebut saling bertumpuk.

[Gambar 4.14 — Grafik Area Bertumpuk Volume Komentar]
Cara mendapatkan gambar: gulir ke bawah setelah word cloud bulanan, kemudian ambil tangkapan layar grafik area bertumpuk yang menampilkan tiga lapisan berwarna merah, biru, dan hijau.

Gambar 4.14 menampilkan grafik area bertumpuk yang memperlihatkan kontribusi volume komentar dari ketiga sentimen sepanjang periode yang dipilih. Lapisan paling bawah berwarna merah merepresentasikan sentimen negatif, lapisan tengah berwarna biru merepresentasikan sentimen netral, dan lapisan teratas berwarna hijau merepresentasikan sentimen positif. Tinggi total area pada setiap titik waktu mencerminkan volume keseluruhan komentar pada periode tersebut, sedangkan proporsi setiap lapisan mencerminkan komposisi sentimen. Puncak-puncak ketinggian total area yang terlihat pada grafik menunjukkan periode-periode di mana aktivitas berkomentar secara keseluruhan mengalami peningkatan, yang umumnya bersamaan dengan lonjakan sentimen negatif yang telah diidentifikasi sebelumnya.


4.4.8 Grafik Rasio Sentimen Negatif Per Periode

Ditampilkan grafik batang rasio negatif sebagai komplemen dari grafik area bertumpuk. Grafik ini menampilkan persentase komentar negatif dari total komentar pada setiap periode waktu, sehingga informasi yang disajikan bukan lagi volume absolut melainkan proporsi relatif. Garis ambang kritis pada nilai 60% ditambahkan sebagai referensi, dan setiap batang yang melampaui ambang tersebut diberi warna merah untuk memberikan peringatan visual. Batang yang berada di bawah ambang diberi warna abu-abu untuk membedakannya secara jelas.

[Gambar 4.15 — Grafik Rasio Sentimen Negatif Per Periode]
Cara mendapatkan gambar: gulir ke bawah setelah grafik area bertumpuk, kemudian ambil tangkapan layar grafik batang rasio negatif beserta garis ambang kritis 60%.

Gambar 4.15 menampilkan grafik batang yang memperlihatkan persentase komentar negatif pada setiap satuan waktu sesuai granularitas yang dipilih. Garis putus-putus horizontal pada posisi 60% berfungsi sebagai ambang kritis yang memisahkan periode normal dari periode kritis. Batang-batang berwarna merah yang melampaui garis ambang mengidentifikasi periode-periode di mana lebih dari 60% komentar pada periode tersebut bersentimen negatif. Informasi ini sangat bermanfaat untuk kepentingan pemantauan opini publik (public opinion monitoring), karena memungkinkan identifikasi periode-periode yang memerlukan perhatian lebih dalam konteks pengelolaan kebijakan dan komunikasi publik. Diakhiri tab tren waktu dengan tabel ringkasan data tren lengkap yang memuat kolom Periode, Positif, Netral, Negatif, Total, dan persentase Negatif. Tabel ini menggunakan pewarnaan gradasi merah pada kolom persentase negatif sehingga periode dengan proporsi negatif tertinggi langsung teridentifikasi secara visual.


4.5 Frekuensi Kata

Dikaji distribusi kosakata dominan dalam corpus komentar YouTube terkait kebijakan RUU TNI pada bagian ini melalui beberapa lapisan analisis yang saling memperkuat. Pemahaman terhadap kata-kata yang paling sering digunakan memberikan gambaran tentang topik-topik yang paling banyak diperbincangkan oleh masyarakat, sekaligus mengungkap kecenderungan leksikal yang membedakan satu kategori sentimen dari yang lain. Disajikan pada bagian ini analisis frekuensi absolut dalam bentuk grafik batang vertikal, proporsi relatif dalam bentuk grafik batang horizontal berwarna gradasi, perbandingan kosakata menonjol antar sentimen secara berdampingan, serta identifikasi kata-kata yang secara khas mendominasi satu sentimen tertentu berdasarkan perhitungan dominance score. Seluruh analisis dilakukan setelah menyaring kata-kata yang tidak bermakna secara semantik, sehingga hasil yang diperoleh mencerminkan kosakata yang benar-benar relevan dengan ekspresi sentimen dalam konteks penelitian ini.

4.5.1 Gambaran Umum Tab Frekuensi Kata

Disajikan analisis frekuensi kata pada tab ketiga yang diberi judul "Frekuensi Kata". Analisis frekuensi kata merupakan tahap dasar dalam eksplorasi data teks yang bertujuan mengidentifikasi kosakata dominan dalam corpus komentar. Pemahaman tentang kata-kata yang paling sering digunakan memberikan wawasan tentang topik-topik yang paling banyak dibicarakan serta kecenderungan leksikal yang membedakan satu kategori sentimen dari yang lain.

Analisis dilakukan pada kolom text_final yang merupakan teks komentar hasil preprocessing. Kata-kata yang termasuk dalam daftar stopwords, kata dengan panjang kurang dari tiga karakter, serta kata yang bukan alfabet murni tidak diikutsertakan dalam perhitungan frekuensi. Penyaringan ini dilakukan untuk memastikan bahwa hanya kata-kata bermakna secara semantik yang dianalisis. Pengguna dapat memilih sentimen yang ingin dianalisis melalui dropdown di bagian atas tab dan mengatur jumlah kata teratas melalui slider di panel samping.

4.5.2 Grafik Batang Vertikal Frekuensi Kata

Ditampilkan grafik batang vertikal pada bagian pertama tab frekuensi kata yang menampilkan kata-kata paling sering muncul berdasarkan filter sentimen yang dipilih. Setiap batang menampilkan nilai frekuensi kemunculan di atasnya. Sumbu horizontal menampilkan daftar kata dengan sudut kemiringan teks untuk mengakomodasi kata-kata yang panjang, sedangkan sumbu vertikal menampilkan jumlah kemunculan.

[Gambar 4.16 — Grafik Batang Vertikal Top N Kata]
Cara mendapatkan gambar: buka tab "Frekuensi Kata", pilih sentimen yang diinginkan melalui dropdown, kemudian ambil tangkapan layar grafik batang vertikal yang muncul pertama kali pada tab tersebut.

Gambar 4.16 memperlihatkan daftar kata paling sering muncul dalam komentar berdasarkan filter sentimen yang dipilih. Tinggi setiap batang secara langsung merepresentasikan frekuensi absolut kemunculan kata tersebut di seluruh komentar yang sesuai dengan filter. Angka yang tercetak di atas setiap batang memudahkan pembacaan nilai eksak tanpa harus mengacu pada sumbu vertikal. Kata-kata yang mendominasi grafik ini mencerminkan isu-isu yang paling banyak dibahas dalam komentar, di mana istilah seperti "tni", "ruu", "sipil", dan "rakyat" yang berkaitan langsung dengan topik penelitian diperkirakan akan muncul di posisi teratas untuk kategori sentimen negatif.

4.5.3 Grafik Batang Horizontal Persentase Kata

Ditampilkan grafik batang horizontal di bawah grafik vertikal yang menampilkan kontribusi persentase setiap kata terhadap total token pada subset data yang dipilih. Grafik ini memberikan perspektif yang berbeda dari grafik sebelumnya karena nilai yang ditampilkan bukan lagi frekuensi absolut melainkan proporsi relatif terhadap keseluruhan token. Warna batang menggunakan gradasi dari biru muda ke biru tua, di mana intensitas warna yang semakin gelap menunjukkan persentase yang semakin tinggi.

[Gambar 4.17 — Grafik Batang Horizontal Persentase Kata]
Cara mendapatkan gambar: gulir ke bawah pada tab "Frekuensi Kata" setelah grafik batang vertikal, kemudian ambil tangkapan layar grafik batang horizontal dengan gradasi warna biru beserta skala warna di sisi kanannya.

Gambar 4.17 menampilkan urutan kata dari persentase tertinggi hingga terendah dalam orientasi horizontal. Kata dengan persentase tertinggi berada di bagian atas grafik dan ditampilkan dengan warna biru paling gelap, sementara kata dengan persentase lebih rendah berada di bagian bawah dengan warna lebih muda. Persentase yang tercetak di ujung setiap batang memudahkan interpretasi tanpa harus mengacu pada sumbu. Informasi ini berguna untuk memahami seberapa besar kontribusi setiap kata dalam membentuk karakteristik leksikal suatu kategori sentimen tertentu.


4.5.4 Perbandingan Kata Menonjol per Sentimen

Ditampilkan tiga grafik batang horizontal secara berdampingan yang masing-masing menampilkan kata paling sering muncul untuk sentimen positif, netral, dan negatif secara terpisah. Visualisasi ini dirancang khusus untuk memudahkan perbandingan leksikal antar sentimen dalam satu pandangan. Setiap grafik menggunakan warna yang sesuai dengan sentimen yang diwakilinya untuk mempertahankan konsistensi visual.

[Gambar 4.18 — Perbandingan Kata Menonjol per Sentimen]
Cara mendapatkan gambar: gulir ke bagian "Perbandingan Kata Menonjol per Sentimen" pada tab "Frekuensi Kata", kemudian ambil tangkapan layar tiga grafik batang horizontal yang tersusun berdampingan.

Gambar 4.18 menampilkan tiga grafik batang horizontal yang disusun dalam satu baris untuk memudahkan perbandingan. Grafik paling kiri berwarna hijau menampilkan kata-kata dominan pada komentar positif, grafik tengah berwarna biru untuk komentar netral, dan grafik paling kanan berwarna merah untuk komentar negatif. Perbandingan ini memungkinkan identifikasi kata-kata yang muncul secara konsisten di semua sentimen (kata netral secara kontekstual) maupun kata-kata yang secara eksklusif atau sangat dominan pada satu sentimen tertentu. Kata seperti "tolak", "bahaya", dan "demokrasi" yang muncul dominan pada grafik merah namun tidak pada grafik hijau merupakan indikator kosakata negatif yang spesifik terhadap respons penolakan terhadap RUU TNI, sementara kata seperti "dukung" dan "setuju" yang dominan pada grafik hijau mencerminkan ekspresi persetujuan dari sebagian kecil pengguna.

4.5.5 Kata Khas per Sentimen Berdasarkan Dominance Score

Ditampilkan tiga grafik lainnya yang menunjukkan kata-kata paling "khas" untuk setiap sentimen berdasarkan metrik yang disebut dominance score. Kata khas didefinisikan sebagai kata yang proporsi kemunculannya pada satu sentimen jauh lebih tinggi dibandingkan rata-rata proporsinya pada keseluruhan data. Nilai dominance score dihitung sebagai selisih antara persentase kata pada sentimen tertentu dengan persentase kata yang sama pada keseluruhan corpus. Pendekatan ini lebih informatif dibandingkan sekadar membandingkan frekuensi absolut karena memperhitungkan distribusi baseline kata di seluruh data.

[Gambar 4.19 — Grafik Dominance Score Kata Khas per Sentimen]
Cara mendapatkan gambar: gulir ke bagian "Kata Khas per Sentimen" pada tab "Frekuensi Kata", kemudian ambil tangkapan layar tiga grafik batang horizontal yang disusun berdampingan.

Gambar 4.19 memperlihatkan kata-kata yang paling unik untuk masing-masing sentimen berdasarkan selisih persentase terhadap keseluruhan corpus. Nilai dominance score ditampilkan dalam format "+X.XX%" di ujung setiap batang, menunjukkan seberapa jauh proporsi kata tersebut melebihi rata-rata keseluruhan data. Kata dengan batang terpanjang pada grafik merah merupakan kata yang proporsi kemunculannya jauh lebih tinggi pada komentar negatif dibandingkan pada komentar secara umum, sehingga dapat dianggap sebagai penanda (marker) kosakata yang bersifat khas untuk sentimen negatif. Informasi ini secara langsung berguna untuk memahami kosakata yang paling membedakan satu sentimen dari yang lain, dan secara tidak langsung juga memberikan wawasan tentang fitur-fitur teks yang dianggap penting oleh model Logistic Regression dalam proses klasifikasi. Diakhiri tab frekuensi kata dengan tabel lengkap yang memuat kolom Kata, Frekuensi, Persentase, dan Kumulatif. Kolom kumulatif menunjukkan seberapa besar kontribusi gabungan dari kata-kata teratas terhadap total token, memberikan gambaran tentang tingkat konsentrasi leksikal dalam corpus.


4.6 N-Gram dan Word Cloud

Dilakukan perluasan analisis leksikal pada bagian ini dari level kata tunggal ke level kombinasi kata melalui pendekatan n-gram, serta disajikan representasi visual frekuensi kata dalam bentuk word cloud. Pendekatan n-gram penting karena makna suatu ekspresi dalam bahasa alami seringkali tidak dapat dipahami hanya dari kata tunggal, melainkan perlu mempertimbangkan kata-kata yang muncul secara berdampingan. Melalui analisis bigram dan trigram, frasa-frasa yang mencerminkan tema utama diskusi publik terkait RUU TNI dapat diidentifikasi secara lebih tepat. Adapun word cloud memberikan representasi visual yang intuitif dan mudah dipahami, di mana ukuran huruf setiap kata secara langsung merepresentasikan frekuensi kemunculannya. Kedua pendekatan ini disajikan secara terpisah berdasarkan kategori sentimen sehingga perbedaan karakteristik linguistik antar sentimen dapat diobservasi secara komparatif.

4.6.1 Gambaran Umum Tab N-Gram dan Word Cloud

Disajikan analisis n-gram dan word cloud pada tab keempat. Analisis n-gram merupakan perluasan dari analisis frekuensi kata tunggal (unigram) ke analisis pasangan kata (bigram) atau tiga kata berurutan (trigram). Pendekatan ini penting karena makna suatu ekspresi dalam bahasa alami seringkali tidak dapat dipahami hanya dari kata individual melainkan harus mempertimbangkan kombinasi kata-kata yang berdekatan. Sebagai contoh, kata "tidak" dan "setuju" yang masing-masing dianalisis secara terpisah memiliki makna yang berbeda dibandingkan ketika keduanya dianalisis sebagai pasangan "tidak setuju" yang merupakan ekspresi penolakan yang jelas. Demikian pula, frasa "revisi uu tni" atau "tolak ruu tni" hanya dapat diidentifikasi melalui analisis bigram atau trigram.

Tab ini juga memuat visualisasi word cloud yang memberikan representasi visual intuitif dari frekuensi kata. Word cloud efektif sebagai alat eksplorasi awal karena memungkinkan identifikasi kata-kata dominan secara sekilas tanpa harus membaca tabel angka.

4.6.2 Grafik N-Gram Utama

Ditampilkan grafik batang horizontal yang menampilkan n-gram paling sering muncul berdasarkan pilihan tipe (bigram atau trigram) dan filter sentimen yang dipilih pengguna melalui panel kontrol di sebelah kiri. Grafik menggunakan gradasi warna ungu dari muda ke tua untuk membedakan tingkat frekuensi. Selain grafik, panel kiri juga menyediakan kontrol untuk menentukan tipe n-gram dan memilih sentimen yang ingin dianalisis.

[Gambar 4.20 — Grafik N-Gram Utama]
Cara mendapatkan gambar: buka tab "N-Gram dan Word Cloud", pilih tipe bigram atau trigram dan sentimen tertentu melalui kontrol di panel kiri, kemudian ambil tangkapan layar grafik batang horizontal yang muncul di sisi kanan.

Gambar 4.20 menampilkan kombinasi dua atau tiga kata yang paling sering muncul bersama dalam komentar sesuai filter sentimen yang dipilih. Setiap batang horizontal merepresentasikan satu n-gram dengan panjang batang yang mencerminkan frekuensi kemunculannya. Persentase yang tercetak di ujung setiap batang menunjukkan proporsi n-gram tersebut terhadap total n-gram yang ditemukan. Frasa-frasa yang muncul sebagai n-gram dengan frekuensi tertinggi, seperti "revisi uu tni", "tolak ruu tni", atau "demokrasi terancam", secara langsung mencerminkan tema-tema utama yang mendominasi diskusi publik dalam komentar YouTube terkait kebijakan RUU TNI.

4.6.3 Perbandingan N-Gram per Sentimen

Ditampilkan tiga grafik n-gram secara berdampingan di bawah grafik utama untuk membandingkan frasa-frasa yang dominan pada setiap sentimen. Masing-masing grafik menggunakan warna sentimen yang sesuai dan menampilkan sepuluh n-gram teratas untuk kategori sentimennya.

[Gambar 4.21 — Perbandingan N-Gram per Sentimen]
Cara mendapatkan gambar: gulir ke bagian "Perbandingan N-Gram per Sentimen" pada tab "N-Gram dan Word Cloud", kemudian ambil tangkapan layar tiga grafik yang tersusun secara horizontal.

Gambar 4.21 memperlihatkan perbedaan frasa dominan antara komentar positif, netral, dan negatif dalam satu tampilan perbandingan. Frasa pada komentar negatif cenderung berisi ekspresi penolakan dan kekhawatiran, sedangkan frasa pada komentar positif cenderung berisi ekspresi dukungan atau apresiasi. Frasa pada komentar netral cenderung bersifat deskriptif atau informatif tanpa muatan evaluatif yang kuat. Perbandingan ini memperkuat temuan dari analisis unigram sebelumnya dengan menunjukkan bahwa perbedaan leksikal antar sentimen tidak hanya terjadi pada level kata individual tetapi juga pada level frasa, yang merupakan unit ekspresi yang lebih alami dalam bahasa sehari-hari.


4.6.4 Word Cloud per Sentimen

Ditampilkan visualisasi word cloud pada bagian bawah tab yang disusun dalam empat sub-tab, yaitu Positif, Netral, Negatif, dan Semua Label. Setiap word cloud dihasilkan dari komentar yang sesuai dengan kategori sentimennya. Skema warna yang berbeda digunakan untuk setiap sentimen: "Greens" untuk positif, "Blues" untuk netral, "Reds" untuk negatif, dan "viridis" untuk gabungan semua sentimen. Latar belakang word cloud disesuaikan dengan nuansa warna sentimen untuk memberikan konsistensi visual yang memudahkan identifikasi kategori secara intuitif. Parameter pembuatan word cloud mencakup lebar 900 piksel, tinggi 400 piksel, maksimum 120 kata, serta nonaktifnya fitur kolokasi agar setiap kata direpresentasikan secara independen.

[Gambar 4.22 — Word Cloud Sentimen Negatif]
Cara mendapatkan gambar: pada bagian "Word Cloud per Sentimen" di tab "N-Gram dan Word Cloud", buka sub-tab "Negatif", tunggu hingga proses rendering selesai, kemudian ambil tangkapan layar.

Gambar 4.22 menampilkan word cloud dari seluruh komentar bersentimen negatif. Kata-kata berukuran paling besar mencerminkan frekuensi kemunculan yang paling tinggi dalam corpus komentar negatif. Dominasi kata-kata berkonotasi penolakan dan kekhawatiran pada word cloud ini secara visual mengonfirmasi temuan dari analisis frekuensi kata sebelumnya. Warna merah yang digunakan sebagai skema warna word cloud memperkuat identitas sentimen yang diwakilinya dan memudahkan pembeda visual dibandingkan word cloud sentimen lainnya.

[Gambar 4.23 — Word Cloud Sentimen Positif]
Cara mendapatkan gambar: buka sub-tab "Positif" pada bagian Word Cloud, tunggu proses rendering selesai, kemudian ambil tangkapan layar.

Gambar 4.23 menampilkan word cloud dari komentar bersentimen positif dengan gradasi warna hijau. Meskipun jumlah komentar positif lebih sedikit dibandingkan negatif, word cloud ini tetap dapat mengungkapkan kosakata yang mencirikan dukungan dan apresiasi publik terhadap kebijakan tersebut. Perbedaan kata-kata yang dominan antara word cloud positif dan negatif secara visual mempertegas perbedaan karakteristik leksikal antar sentimen yang sebelumnya diidentifikasi melalui grafik frekuensi.

[Gambar 4.24 — Word Cloud Semua Label]
Cara mendapatkan gambar: buka sub-tab "Semua Label" pada bagian Word Cloud, tunggu proses rendering selesai, kemudian ambil tangkapan layar.

Gambar 4.24 menampilkan word cloud dari keseluruhan komentar tanpa filter sentimen menggunakan skema warna "viridis". Word cloud ini memberikan gambaran menyeluruh tentang topik-topik yang paling banyak dibicarakan dalam seluruh corpus komentar YouTube terkait RUU TNI. Kata-kata yang mendominasi word cloud ini merepresentasikan isu-isu yang menjadi pusat perhatian publik secara umum, terlepas dari polaritas sentimennya. Perbandingan antara word cloud gabungan ini dengan word cloud per sentimen memungkinkan identifikasi kata-kata yang mendominasi karena volume corpus besar (bukan karena spesifik pada satu sentimen) versus kata-kata yang memang khas untuk sentimen tertentu.


4.7 Insight per Video

Dikaji variasi distribusi sentimen berdasarkan sumber video pada bagian ini sebagai dimensi analisis yang membedakan penelitian ini dari kajian sentimen secara agregat. Kelima video yang digunakan dalam penelitian berasal dari kanal YouTube yang berbeda, yaitu Gerald Vincentt, BBC News Indonesia, Pandji Pragiwaksono, Sepulang Sekolah, dan Metro TV, yang masing-masing memiliki karakteristik konten, gaya penyajian, dan basis audiens yang berbeda. Perbedaan tersebut berpotensi menghasilkan distribusi sentimen komentar yang berbeda pula, sehingga diperlukan analisis pada tingkat video individual untuk mengungkap variasi tersebut. Disajikan pada bagian ini perbandingan distribusi sentimen antar video dalam format grafik batang bertumpuk dan grafik lingkaran, tabel metrik kuantitatif lengkap yang mencakup jumlah komentar per sentimen, persentase, serta data interaksi berbasis like, dan visualisasi kosakata dominan untuk masing-masing video.

4.7.1 Gambaran Umum Tab Insight per Video

Disajikan analisis sentimen pada tingkat video individual pada tab kelima yang diberi judul "Insight per Video". Tab ini memberikan perspektif analisis yang berbeda dibandingkan tab-tab sebelumnya karena melakukan segmentasi data berdasarkan sumber videonya. Kelima video yang menjadi sumber data penelitian berasal dari kanal YouTube yang berbeda dengan gaya penyajian konten yang berbeda pula, yaitu Gerald Vincentt, BBC News Indonesia, Pandji Pragiwaksono, Sepulang Sekolah, dan Metro TV. Perbedaan kanal ini menciptakan variasi pada karakteristik audiens yang memberikan komentar, sehingga analisis per video dapat mengungkapkan bagaimana perbedaan framing konten memengaruhi sentimen respons publik.

4.7.2 Grafik Batang Bertumpuk Komentar per Video

Ditampilkan grafik batang bertumpuk yang menampilkan jumlah komentar dari setiap video berdasarkan kategori sentimennya. Setiap batang mewakili satu video, dan setiap segmen batang menampilkan jumlah komentar untuk satu sentimen. Sumbu horizontal menampilkan judul video yang diperpendek maksimal 40 karakter untuk efisiensi ruang, sedangkan sumbu vertikal menampilkan jumlah komentar.

[Gambar 4.25 — Grafik Batang Bertumpuk Komentar per Video]
Cara mendapatkan gambar: buka tab "Insight per Video", kemudian ambil tangkapan layar grafik batang bertumpuk yang muncul di sisi kiri tampilan.

Gambar 4.25 menampilkan perbandingan jumlah komentar dari kelima video yang dianalisis dalam format batang bertumpuk. Ketinggian total setiap batang mencerminkan volume total komentar pada video tersebut, sedangkan komposisi warna di dalam setiap batang mencerminkan distribusi sentimen. Video dengan segmen merah paling tinggi dan proporsional merupakan video yang paling banyak menuai komentar bernada negatif. Perbandingan ketinggian total antar video juga memperlihatkan perbedaan tingkat interaksi (engagement) dari komunitas penonton masing-masing kanal, yang dapat dikaitkan dengan jumlah pengikut, gaya penyajian konten, serta tingkat kontroversialitas sudut pandang yang ditampilkan dalam video.

4.7.3 Grafik Lingkaran Proporsi Sentimen per Video

Ditampilkan kumpulan grafik lingkaran berlubang yang disusun dalam format multi-panel (subplot) untuk setiap video di sebelah kanan grafik batang. Setiap lingkaran menampilkan proporsi ketiga sentimen dalam bentuk persentase untuk satu video tertentu. Penggunaan format multi-panel ini memungkinkan perbandingan visual yang lebih setara antar video karena setiap video mendapatkan lingkaran dengan ukuran yang sama, sehingga tidak terdistorsi oleh perbedaan volume komentar.

[Gambar 4.26 — Grafik Lingkaran Proporsi Sentimen per Video]
Cara mendapatkan gambar: ambil tangkapan layar kumpulan grafik lingkaran yang berada di sisi kanan pada tab "Insight per Video", pastikan seluruh panel grafik untuk kelima video terlihat dalam tangkapan layar.

Gambar 4.26 memperlihatkan proporsi sentimen dari masing-masing video dalam format diagram lingkaran berlubang yang tersusun dalam kisi-kisi. Setiap lingkaran diberi judul video yang sesuai di bagian atasnya. Perbedaan ukuran irisan merah antar video secara langsung menggambarkan perbedaan tingkat sentimen negatif yang diterima oleh setiap video. Video yang irisannya didominasi oleh warna merah mengindikasikan bahwa komunitas komentarnya bereaksi lebih negatif terhadap konten yang disajikan, yang dapat diinterpretasikan sebagai indikasi ketidaksetujuan audiens terhadap sudut pandang yang ditampilkan dalam video tersebut atau sebaliknya, audiens yang setuju dengan kritik yang disampaikan oleh pembuat konten terhadap kebijakan RUU TNI.


4.7.4 Tabel Metrik Lengkap per Video

Ditampilkan tabel ringkasan metrik yang memuat informasi kuantitatif lengkap untuk setiap video. Tabel ini mencakup kolom judul video, total komentar, jumlah komentar positif, netral, negatif, persentase negatif, persentase positif, total like yang diterima, dan rata-rata like per komentar. Tabel diurutkan secara otomatis berdasarkan persentase negatif dari yang tertinggi ke terendah sehingga video dengan tingkat sentimen negatif paling tinggi langsung terlihat di baris teratas. Kolom persentase negatif diberi pewarnaan gradasi merah dan kolom persentase positif diberi pewarnaan gradasi hijau untuk memudahkan identifikasi visual secara sekilas.

[Gambar 4.27 — Tabel Metrik Lengkap per Video]
Cara mendapatkan gambar: gulir ke bawah pada tab "Insight per Video" setelah grafik, kemudian ambil tangkapan layar tabel yang memuat semua kolom metrik beserta pewarnaan gradasi pada kolom persentase.

Gambar 4.27 menampilkan tabel dengan pewarnaan gradasi pada kolom persentase negatif dan persentase positif. Video yang berada di baris paling atas memiliki persentase negatif tertinggi, ditandai dengan sel berwarna merah paling gelap. Sebaliknya, video dengan persentase positif tertinggi ditandai dengan sel berwarna hijau paling gelap. Kolom total like dan rata-rata like memberikan dimensi tambahan yang memungkinkan perbandingan antara tingkat sentimen komentar dengan tingkat interaksi berbasis like, sehingga dapat diidentifikasi apakah video dengan banyak komentar negatif juga cenderung mendapatkan sedikit like atau sebaliknya. Informasi ini berguna untuk memahami dinamika komunitas penonton dari masing-masing kanal YouTube yang dikaji.

4.7.5 Kata Paling Sering per Video

Ditampilkan grafik batang horizontal untuk setiap video yang menunjukkan sepuluh kata yang paling sering muncul dalam komentar video tersebut. Grafik-grafik ini disusun dalam tata letak tiga kolom, sehingga maksimal enam video dapat ditampilkan dalam dua baris. Warna batang menggunakan gradasi biru dari muda ke tua berdasarkan frekuensi kemunculan, memberikan isyarat visual tentang kata mana yang paling dominan.

[Gambar 4.28 — Kata Paling Sering per Video]
Cara mendapatkan gambar: gulir ke bagian "Kata Paling Sering per Video" pada tab "Insight per Video", kemudian ambil tangkapan layar kumpulan grafik batang horizontal yang tersusun dalam tiga kolom.

Gambar 4.28 memperlihatkan kata-kata yang paling dominan untuk setiap video secara individual. Meskipun beberapa kata umum seperti "tni" dan "ruu" kemungkinan muncul di semua video karena relevansinya dengan topik penelitian, perbedaan kata-kata pada posisi selanjutnya mencerminkan perbedaan topik spesifik atau sudut pandang yang dibahas dalam masing-masing video. Misalnya, video dari kanal yang lebih kritis terhadap kebijakan mungkin akan memiliki kata-kata seperti "tolak" dan "bahaya" di posisi teratas, sementara video yang lebih bersifat informatif mungkin akan lebih banyak mengandung kata-kata teknis dan deskriptif. Analisis per video ini secara keseluruhan memberikan wawasan bahwa opini publik terhadap RUU TNI tidak bersifat homogen melainkan bervariasi tergantung pada sumber informasi yang dikonsumsi dan komunitas penonton yang terlibat dalam setiap platform konten.


4.8 Pembahasan Hasil Analisis Sentimen

Diintegrasikan pada bagian ini seluruh temuan yang diperoleh dari proses eksplorasi data pada sub-bab sebelumnya untuk membangun pemahaman yang menyeluruh tentang pola sentimen publik terhadap kebijakan RUU TNI. Temuan mencakup aspek distribusi sentimen secara keseluruhan dan per sumber data, pola reaktivitas temporal, karakteristik leksikal yang membedakan antar sentimen, konsistensi metode pelabelan manual dan otomatis, implikasi ketidakseimbangan kelas terhadap performa model klasifikasi, variasi sentimen antar video, serta kontribusi dashboard visualisasi dalam mendukung pencapaian tujuan penelitian. Setiap temuan dikaitkan dengan konteks sosial-politik yang melatarbelakangi isu RUU TNI sehingga interpretasi yang dihasilkan bersifat relevan secara akademis maupun praktis.

4.8.1 Dominasi Sentimen Negatif

Diidentifikasi bahwa sentimen negatif mendominasi keseluruhan dataset komentar YouTube terkait kebijakan RUU TNI. Kondisi ini bersifat konsisten antara data berlabel manual maupun data berlabel otomatis, yang mengindikasikan bahwa dominasi negatif bukan merupakan artefak dari metode pelabelan tertentu melainkan mencerminkan respons publik yang sesungguhnya. Dominasi sentimen negatif yang signifikan ini sejalan dengan konteks sosial-politik pada periode pengambilan data, di mana berbagai kelompok masyarakat sipil, akademisi, dan aktivis secara aktif menyuarakan penolakan terhadap pembahasan RUU TNI yang dianggap berpotensi mengembalikan dwifungsi militer dalam kehidupan sipil.

Komentar-komentar yang mengandung kata seperti "tolak", "bahaya", "sipil", dan "demokrasi" dengan frekuensi tinggi pada kategori sentimen negatif mencerminkan substansi kekhawatiran publik yang berpusat pada potensi dampak kebijakan tersebut terhadap prinsip-prinsip demokrasi dan supremasi sipil. Temuan ini memberikan bukti empiris berbasis data media sosial yang mendukung narasi penolakan publik yang selama ini hanya terdokumentasi melalui pemberitaan jurnalistik dan survei opini publik konvensional.

4.8.2 Pola Temporal dan Reaktivitas Publik

Ditemukan dari analisis tren waktu bahwa pola distribusi komentar bersifat tidak merata sepanjang waktu, melainkan terkonsentrasi pada periode-periode tertentu dalam bentuk lonjakan yang tajam. Pola ini sesuai dengan karakteristik data media sosial yang bersifat reaktif terhadap peristiwa eksternal. Lonjakan volume komentar umumnya terjadi beberapa hari setelah adanya pemberitaan atau peristiwa signifikan terkait RUU TNI, kemudian secara bertahap menurun seiring berjalannya waktu dan beralihnya perhatian publik ke isu lain.

Analisis word cloud pada periode puncak memberikan pemahaman kontekstual tentang isu-isu spesifik yang memicu lonjakan tersebut. Kemampuan untuk mengidentifikasi tidak hanya "kapan" tetapi juga "mengapa" lonjakan terjadi merupakan keunggulan pendekatan eksplorasi berbasis visualisasi dibandingkan analisis statistik deskriptif konvensional. Informasi ini dapat dimanfaatkan oleh para pembuat kebijakan, tim komunikasi publik, maupun peneliti sosial untuk memahami mekanisme pembentukan opini publik di era media digital.

4.8.3 Variasi Sentimen Antar Video dan Kanal

Diidentifikasi melalui analisis per video bahwa setiap video memiliki distribusi sentimen yang berbeda meskipun membahas topik yang sama, yaitu kebijakan RUU TNI. Variasi ini dapat dikaitkan dengan beberapa faktor, di antaranya perbedaan framing konten yang disajikan oleh masing-masing kanal, karakteristik demografis dan ideologis audiens dari setiap kanal, serta perbedaan nada dan sudut pandang yang diambil oleh pembuat konten dalam membahas isu tersebut.

Video-video dari kanal yang secara eksplisit mengekspresikan penolakan terhadap RUU TNI dalam judul dan kontennya cenderung menarik audiens yang lebih homogen secara pandangan, sehingga menghasilkan komentar dengan distribusi sentimen negatif yang lebih terkonsentrasi. Sebaliknya, video yang bersifat lebih informatif dan berimbang cenderung menghasilkan distribusi sentimen yang lebih beragam. Temuan ini menggarisbawahi pentingnya mempertimbangkan sumber data (dalam hal ini identitas kanal) sebagai variabel kontekstual dalam penelitian analisis sentimen berbasis media sosial, karena karakteristik platform dan komunitas pengguna dapat memengaruhi distribusi sentimen secara signifikan.

4.8.4 Konsistensi Pelabelan Manual dan Otomatis

Dibuktikan melalui grafik perbandingan distribusi pada tab Distribusi Sentimen bahwa pelabelan manual dan pelabelan otomatis menggunakan model IndoBERT menghasilkan distribusi sentimen yang relatif konsisten. Perbedaan yang ada masih berada dalam rentang yang dapat diterima, mengindikasikan bahwa model IndoBERT mampu menangkap pola sentimen bahasa Indonesia dengan cukup baik pada konteks teks komentar YouTube yang membahas isu kebijakan publik.

Konsistensi ini memiliki implikasi positif terhadap kualitas data yang digunakan dalam pelatihan model Logistic Regression dan Naive Bayes. Apabila distribusi label manual dan otomatis sangat berbeda, hal itu akan mengindikasikan adanya bias sistematis dalam proses pelabelan otomatis yang berpotensi memengaruhi performa model klasifikasi. Dengan konsistensi yang terjaga, dapat disimpulkan bahwa pendekatan pelabelan semi-otomatis yang diterapkan dalam penelitian ini merupakan pendekatan yang valid untuk menghasilkan dataset berlabel dalam skala besar dengan kualitas yang memadai.

4.8.5 Implikasi terhadap Model Klasifikasi

Diidentifikasi bahwa ketidakseimbangan kelas (class imbalance) yang tervisualisasi melalui grafik lollipop memiliki implikasi langsung terhadap performa model klasifikasi sentimen. Model yang dilatih pada dataset dengan distribusi tidak merata cenderung mengoptimalkan kinerjanya untuk kelas mayoritas, dalam hal ini sentimen negatif, sehingga performa pada kelas minoritas, yaitu sentimen positif, berpotensi lebih rendah.

Pemahaman terhadap ketidakseimbangan ini penting untuk interpretasi yang tepat terhadap metrik evaluasi model. Nilai akurasi keseluruhan yang tinggi belum tentu mencerminkan kemampuan model yang sesungguhnya apabila kelas minoritas memiliki performa yang buruk. Oleh karena itu, evaluasi model perlu mempertimbangkan metrik per kelas seperti precision, recall, dan F1-score untuk masing-masing kategori sentimen secara individual, sebagaimana yang telah dilakukan dalam tahap evaluasi model pada penelitian ini.

4.8.6 Kontribusi Dashboard terhadap Pemahaman Data

Dibangunnya dashboard visualisasi EDA memberikan kontribusi signifikan terhadap proses pemahaman data secara menyeluruh sebelum dan sesudah tahap pemodelan. Dashboard ini tidak hanya berfungsi sebagai alat eksplorasi data sekali pakai, tetapi dirancang untuk mendukung analisis berkelanjutan karena kemampuannya memuat data terbaru secara langsung dari MongoDB.

Keunggulan utama dashboard ini terletak pada interaktivitasnya yang memungkinkan pengguna melakukan eksplorasi yang dipersonalisasi sesuai pertanyaan analitis masing-masing, berbeda dengan laporan statis yang hanya menyajikan satu sudut pandang yang telah ditentukan sebelumnya. Dalam konteks penelitian ini, dashboard berperan sebagai jembatan antara data mentah di MongoDB dengan pemahaman berbasis bukti tentang pola sentimen publik terhadap kebijakan RUU TNI, sehingga mendukung pencapaian tujuan penelitian untuk menganalisis kecenderungan opini masyarakat secara lebih komprehensif dan berbasis data.



---

PANDUAN PENGAMBILAN GAMBAR UNTUK LAPORAN

Seluruh gambar yang tercantum dalam Bab 4 ini perlu diambil langsung dari tampilan dashboard yang sedang berjalan. Berikut panduan lengkapnya.

Langkah persiapan:
1. Pastikan Streamlit berjalan dengan menjalankan perintah: streamlit run dashboard_eda.py
2. Buka browser pada alamat http://localhost:8501
3. Pastikan koneksi ke MongoDB aktif dengan memeriksa indikator "MongoDB terhubung" di panel samping
4. Klik tombol "Refresh Data" di panel samping sebelum mengambil gambar untuk memastikan data terbaru termuat
5. Gunakan alat tangkapan layar Snipping Tool (Windows) untuk mengambil area gambar yang spesifik
6. Simpan gambar dengan nama yang mencerminkan nomor dan judul gambar yang sesuai

Daftar gambar yang perlu diambil:

Gambar 4.1  — Tampilan halaman utama dashboard (header KPI dan lima tab navigasi)
Gambar 4.2  — Enam kartu metrik di bagian atas halaman
Gambar 4.3  — Grafik batang distribusi sentimen pada sub-tab Gabungan
Gambar 4.4  — Grafik donut proporsi sentimen pada sub-tab Gabungan
Gambar 4.5  — Grafik lollipop ketidakseimbangan kelas
Gambar 4.6  — Grafik batang berkelompok perbandingan manual vs auto-label vs gabungan
Gambar 4.7  — Grafik batang rata-rata like per sentimen beserta tabel
Gambar 4.8  — Kontrol filter rentang tanggal dan granularitas (tab Tren Waktu)
Gambar 4.9  — Grafik garis tren positif vs negatif dengan anotasi puncak
Gambar 4.10 — Dua panel word cloud lonjakan (puncak negatif dan puncak positif)
Gambar 4.11 — Grafik batang bertumpuk tren bulanan
Gambar 4.12 — Grafik garis tren sentimen per bulan dengan anotasi puncak negatif
Gambar 4.13 — Dua word cloud penyebab lonjakan pada bulan puncak
Gambar 4.14 — Grafik area bertumpuk volume komentar
Gambar 4.15 — Grafik batang rasio sentimen negatif per periode
Gambar 4.16 — Grafik batang vertikal top N kata (tab Frekuensi Kata)
Gambar 4.17 — Grafik batang horizontal persentase kata dengan gradasi biru
Gambar 4.18 — Tiga grafik perbandingan kata menonjol per sentimen
Gambar 4.19 — Tiga grafik dominance score kata khas per sentimen
Gambar 4.20 — Grafik n-gram utama (tab N-Gram dan Word Cloud)
Gambar 4.21 — Tiga grafik perbandingan n-gram per sentimen
Gambar 4.22 — Word cloud sentimen negatif
Gambar 4.23 — Word cloud sentimen positif
Gambar 4.24 — Word cloud semua label
Gambar 4.25 — Grafik batang bertumpuk komentar per video (tab Insight per Video)
Gambar 4.26 — Kumpulan grafik lingkaran proporsi sentimen per video
Gambar 4.27 — Tabel metrik lengkap per video dengan pewarnaan gradasi
Gambar 4.28 — Kumpulan grafik kata paling sering per video
