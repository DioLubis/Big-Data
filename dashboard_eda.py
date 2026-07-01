"""
Dashboard EDA — Analisis Sentimen Komentar YouTube
====================================================
Fokus: visualisasi DATA (bukan hasil model)
  - Distribusi label & class imbalance
  - Statistik & distribusi panjang teks
  - Kata-kata yang sering muncul (frekuensi & persentase)
  - Word cloud per sentimen
  - N-gram analysis (unigram, bigram)
  - Distribusi per video
  - Korelasi fitur teks
  - Heatmap co-occurrence kata
  - Timeline / urutan data
"""
from __future__ import annotations

import io
import os
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from wordcloud import WordCloud

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EDA Sentimen YouTube",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
section[data-testid="stSidebar"] { background-color: #1e2130; }
section[data-testid="stSidebar"] * { color: #e8e8e8 !important; }
[data-testid="metric-container"] {
    background: #f0f4f8;
    border-left: 4px solid #3498db;
    border-radius: 6px;
    padding: 10px 14px;
}
</style>
""", unsafe_allow_html=True)

# ── Konstanta ────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)
MONGO_URI    = os.getenv("MONGO_URI", "")
MONGO_DB     = os.getenv("MONGO_DB", "analisis_sentimen")
SOURCE_COL   = "comments_sentiment"
VALID_LABELS = ["positif", "netral", "negatif"]
LABEL_COLORS = {"positif": "#2ECC71", "netral": "#3498DB", "negatif": "#E74C3C"}
LABEL_WC_BG  = {"positif": "#f0fff4", "netral": "#f0f8ff", "negatif": "#fff0f0"}
SEED         = 42

# Mapping video_id -> judul (dari data proyek)
VIDEO_TITLES = {
    "KjXe214MfwQ": "RUU TNI itu apa? Mirip Orde Baru? (@geraldvincentt)",
    "7CLZkPwhEG4": "Revisi UU TNI: Apa dampaknya untuk masyarakat sipil? (BBC News)",
    "F6fgLwUeeqI": "BATALKAN REVISI UU TNI (Pandji Pragiwaksono)",
    "sg8Mzx0fZbU": "Revisi UU TNI (Sepulang Sekolah)",
    "MxCqHoldj2Y": "RUU TNI Resmi Jadi UU! Ada yang Perlu Dikhawatirkan? (METRO TV)",
}

# Stopword ringan — kata terlalu umum yang tidak informatif untuk analisis
STOPWORDS_EXTRA = {
    "yang", "dan", "di", "ini", "itu", "dengan", "tidak",
    "saya", "kamu", "kami", "kita", "ada", "kalau", "juga",
    "untuk", "dari", "pada", "ke", "ya", "bisa", "sudah",
    "akan", "lebih", "jadi", "atau", "tapi", "karena", "aja",
    "saja", "bro", "dong", "lah", "pun", "nya", "nih", "si",
}


# ══════════════════════════════════════════════════════════════════════════
# DATA LOADING & CACHING
# ══════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_client():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)


@st.cache_data(ttl=300, show_spinner=False)
def load_data() -> pd.DataFrame:
    docs = list(
        get_client()[MONGO_DB][SOURCE_COL].find(
            {"text_final": {"$exists": True, "$ne": ""},
             "sentiment":  {"$exists": True, "$nin": [None, ""]}},
            {"_id": 0, "text_final": 1, "sentiment": 1,
             "text_original": 1, "video_id": 1, "comment_id": 1},
        )
    )
    df = pd.DataFrame(docs)
    if df.empty:
        return df
    df["text_len"]    = df["text_final"].str.len()
    df["token_count"] = df["text_final"].str.split().str.len()
    df["unique_tokens"] = df["text_final"].apply(lambda t: len(set(str(t).split())))
    df["lexical_diversity"] = (
        df["unique_tokens"] / df["token_count"].replace(0, np.nan)
    ).round(4)
    df["avg_word_len"] = df["text_final"].apply(
        lambda t: np.mean([len(w) for w in str(t).split()]) if str(t).split() else 0
    ).round(2)
    # Tambahkan judul video (short label untuk chart)
    df["video_title"] = df["video_id"].map(VIDEO_TITLES).fillna(df["video_id"])
    df["video_short"] = df["video_title"].apply(
        lambda t: t[:45] + "…" if len(str(t)) > 45 else t
    )
    return df


@st.cache_data(show_spinner=False)
def get_token_freq(df: pd.DataFrame, label: str | None, remove_stop: bool,
                   top_n: int) -> pd.DataFrame:
    """Frekuensi token untuk label tertentu (atau semua)."""
    subset = df if label is None else df[df["sentiment"] == label]
    all_tokens: list[str] = []
    for txt in subset["text_final"]:
        tokens = str(txt).split()
        if remove_stop:
            tokens = [t for t in tokens if t not in STOPWORDS_EXTRA and len(t) > 1]
        all_tokens.extend(tokens)
    total_tokens = len(all_tokens)
    counter = Counter(all_tokens).most_common(top_n)
    result = pd.DataFrame(counter, columns=["kata", "frekuensi"])
    result["persentase"] = (result["frekuensi"] / total_tokens * 100).round(3)
    result["rank"] = range(1, len(result) + 1)
    return result, total_tokens


@st.cache_data(show_spinner=False)
def get_ngram_freq(df: pd.DataFrame, label: str | None, n: int,
                   remove_stop: bool, top_n: int) -> pd.DataFrame:
    """Frekuensi n-gram."""
    subset = df if label is None else df[df["sentiment"] == label]
    ngrams: list[str] = []
    for txt in subset["text_final"]:
        tokens = str(txt).split()
        if remove_stop:
            tokens = [t for t in tokens if t not in STOPWORDS_EXTRA and len(t) > 1]
        ngrams.extend([" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)])
    total = len(ngrams)
    counter = Counter(ngrams).most_common(top_n)
    result = pd.DataFrame(counter, columns=["ngram", "frekuensi"])
    result["persentase"] = (result["frekuensi"] / total * 100).round(3)
    return result, total


@st.cache_data(show_spinner=False)
def get_wordcloud_img(df: pd.DataFrame, label: str | None,
                      remove_stop: bool, bg_color: str) -> bytes:
    """Generate word cloud sebagai bytes PNG."""
    subset = df if label is None else df[df["sentiment"] == label]
    all_text = " ".join(
        t for txt in subset["text_final"]
        for t in str(txt).split()
        if (not remove_stop or (t not in STOPWORDS_EXTRA and len(t) > 1))
    )
    wc = WordCloud(
        width=800, height=400,
        background_color=bg_color,
        colormap="RdYlGn" if label == "positif" else
                 "Blues"   if label == "netral"  else
                 "Reds"    if label == "negatif" else "viridis",
        max_words=150,
        collocations=False,
        random_state=SEED,
    ).generate(all_text or "tidak ada data")
    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def get_cross_label_freq(df: pd.DataFrame, remove_stop: bool, top_n: int) -> pd.DataFrame:
    """Frekuensi kata per label — untuk heatmap perbandingan."""
    records = []
    for lbl in VALID_LABELS:
        subset = df[df["sentiment"] == lbl]
        all_tokens = []
        for txt in subset["text_final"]:
            tokens = str(txt).split()
            if remove_stop:
                tokens = [t for t in tokens if t not in STOPWORDS_EXTRA and len(t) > 1]
            all_tokens.extend(tokens)
        total = len(all_tokens)
        for word, cnt in Counter(all_tokens).most_common(top_n):
            records.append({
                "kata": word, "sentimen": lbl,
                "frekuensi": cnt,
                "persen": round(cnt / total * 100, 3) if total else 0,
            })
    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("📊 EDA Sentimen")
    st.caption("Eksplorasi Data Komentar YouTube")
    st.divider()

    # Koneksi
    try:
        get_client().admin.command("ping")
        st.success("MongoDB terhubung ✅")
    except Exception:
        st.error("MongoDB tidak terhubung ❌")

    st.divider()
    st.subheader("⚙️ Pengaturan Analisis")

    remove_stop = st.toggle(
        "Hapus stopword umum", value=True,
        help="Hapus kata-kata sangat umum (yang, dan, di, dll.) dari analisis frekuensi"
    )
    top_n_words = st.slider("Top N kata ditampilkan", 5, 50, 20)
    top_n_ngram = st.slider("Top N n-gram ditampilkan", 5, 30, 15)

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(f"DB: `{MONGO_DB}`")
    st.caption(f"Collection: `{SOURCE_COL}`")

# ══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════
with st.spinner("Memuat data dari MongoDB..."):
    df = load_data()

if df.empty:
    st.error("Data tidak ditemukan di collection `comments_sentiment`.")
    st.stop()

total = len(df)
n_pos = int((df["sentiment"] == "positif").sum())
n_net = int((df["sentiment"] == "netral").sum())
n_neg = int((df["sentiment"] == "negatif").sum())
total_tokens_all = df["token_count"].sum()
vocab_size = len(set(
    t for txt in df["text_final"]
    for t in str(txt).split()
    if (not remove_stop or t not in STOPWORDS_EXTRA)
))

# ══════════════════════════════════════════════════════════════════════════
# HEADER + KPI
# ══════════════════════════════════════════════════════════════════════════
st.title("📊 EDA — Analisis Sentimen Komentar YouTube")
st.caption(
    "Eksplorasi mendalam data teks: distribusi sentimen, frekuensi kata, "
    "n-gram, word cloud, dan karakteristik linguistik."
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("📝 Total Komentar",   f"{total:,}")
c2.metric("😊 Positif",          f"{n_pos:,}",  f"{n_pos/total*100:.1f}%")
c3.metric("😐 Netral",           f"{n_net:,}",  f"{n_net/total*100:.1f}%")
c4.metric("😠 Negatif",          f"{n_neg:,}",  f"{n_neg/total*100:.1f}%")
c5.metric("🔤 Total Token",      f"{int(total_tokens_all):,}")
c6.metric("📚 Ukuran Vocab",     f"{vocab_size:,}")

st.divider()


# ══════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏷️ Distribusi Data",
    "📏 Karakteristik Teks",
    "🔤 Frekuensi Kata",
    "☁️ Word Cloud",
    "🔗 N-Gram",
    "📊 Perbandingan Lintas Label",
])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — DISTRIBUSI DATA
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("🏷️ Distribusi Label Sentimen")

    # Pie + Bar side by side
    col_a, col_b = st.columns(2)
    with col_a:
        cnt = df["sentiment"].value_counts()
        colors = [LABEL_COLORS[l] for l in cnt.index]
        fig = go.Figure(go.Pie(
            labels=cnt.index, values=cnt.values,
            marker_colors=colors, hole=0.42,
            textinfo="label+percent+value",
            hovertemplate="<b>%{label}</b><br>%{value} komentar (%{percent})<extra></extra>",
        ))
        fig.update_layout(title="Proporsi Label Sentimen", height=400,
                          margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        cnt_df = cnt.reset_index()
        cnt_df.columns = ["sentimen", "jumlah"]
        cnt_df["persentase"] = (cnt_df["jumlah"] / total * 100).round(2)
        fig = go.Figure(go.Bar(
            x=cnt_df["sentimen"], y=cnt_df["jumlah"],
            marker_color=[LABEL_COLORS[l] for l in cnt_df["sentimen"]],
            text=[f"{r.jumlah:,}<br>({r.persentase:.1f}%)" for r in cnt_df.itertuples()],
            textposition="outside",
        ))
        fig.update_layout(
            title="Jumlah Komentar per Label",
            yaxis=dict(range=[0, cnt_df["jumlah"].max() * 1.25]),
            height=400, margin=dict(t=50, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Class imbalance lollipop
    st.markdown("#### ⚖️ Class Imbalance")
    ideal = 100 / len(VALID_LABELS)
    fig_lo = go.Figure()
    for lbl in VALID_LABELS:
        pct = df[df["sentiment"] == lbl].shape[0] / total * 100
        color = LABEL_COLORS[lbl]
        fig_lo.add_trace(go.Scatter(
            x=[0, pct], y=[lbl, lbl], mode="lines",
            line=dict(color=color, width=4), showlegend=False,
        ))
        fig_lo.add_trace(go.Scatter(
            x=[pct], y=[lbl], mode="markers+text",
            marker=dict(size=20, color=color, line=dict(width=2, color="white")),
            text=f"  {pct:.1f}%  ({df[df['sentiment']==lbl].shape[0]:,} komentar)",
            textposition="middle right", showlegend=False,
        ))
    fig_lo.add_vline(x=ideal, line_dash="dash", line_color="#888",
                     annotation_text=f"Ideal (seimbang) = {ideal:.1f}%",
                     annotation_position="top right")
    fig_lo.update_layout(
        title="Class Imbalance — Persentase Aktual vs Ideal Seimbang",
        xaxis=dict(title="Persentase (%)", range=[0, 70]),
        height=280, margin=dict(t=50, b=20, l=80),
    )
    st.plotly_chart(fig_lo, use_container_width=True)
    st.caption(
        f"💡 Data **tidak seimbang**: negatif ({n_neg/total*100:.1f}%) mendominasi, "
        f"positif ({n_pos/total*100:.1f}%) paling sedikit — "
        f"rasio negatif:positif = {n_neg//max(n_pos,1)}:1"
    )

    st.divider()

    # Distribusi per video
    if "video_id" in df.columns and df["video_id"].nunique() > 1:
        st.markdown("#### 🎬 Distribusi per Video")
        cv1, cv2 = st.columns(2)
        gdf = df.groupby(["video_short","sentiment"]).size().reset_index(name="n")
        with cv1:
            fig = px.bar(
                gdf, x="video_short", y="n", color="sentiment",
                color_discrete_map=LABEL_COLORS, barmode="stack",
                title="Jumlah Komentar per Video (stacked)",
                labels={"video_short": "Judul Video", "n": "Jumlah"},
                text="n",
            )
            fig.update_layout(
                height=480, margin=dict(t=50, b=160),
                xaxis_tickangle=-30,
                legend=dict(orientation="h", y=1.06),
            )
            fig.update_xaxes(tickfont=dict(size=11))
            st.plotly_chart(fig, use_container_width=True)
        with cv2:
            tot_vid = gdf.groupby("video_short")["n"].transform("sum")
            gdf["pct"] = (gdf["n"] / tot_vid * 100).round(1)
            fig = px.bar(
                gdf, x="video_short", y="pct", color="sentiment",
                color_discrete_map=LABEL_COLORS, barmode="stack",
                title="Persentase Sentimen per Video (%)",
                labels={"video_short": "Judul Video", "pct": "Persentase (%)"},
                text=gdf["pct"].apply(lambda v: f"{v:.0f}%"),
            )
            fig.update_yaxes(range=[0, 105])
            fig.update_layout(
                height=480, margin=dict(t=50, b=160),
                xaxis_tickangle=-30,
                legend=dict(orientation="h", y=1.06),
            )
            fig.update_xaxes(tickfont=dict(size=11))
            st.plotly_chart(fig, use_container_width=True)

        # Tabel mapping video
        st.markdown("##### 🗂️ Daftar Video")
        vid_tbl = (
            df.groupby(["video_id", "video_title"])
            .agg(Total_Komentar=("comment_id", "count"))
            .reset_index()
        )
        vid_tbl_sent = df.groupby(["video_id", "sentiment"]).size().unstack(fill_value=0).reset_index()
        vid_tbl = vid_tbl.merge(vid_tbl_sent, on="video_id", how="left")
        vid_tbl = vid_tbl.rename(columns={
            "video_id": "Video ID", "video_title": "Judul Video",
            "Total_Komentar": "Total",
        })
        st.dataframe(vid_tbl, use_container_width=True, hide_index=True)

    st.divider()

    # Tabel ringkasan
    st.markdown("#### 📋 Ringkasan Statistik Label")
    tbl = []
    for lbl in VALID_LABELS:
        sub = df[df["sentiment"] == lbl]
        tbl.append({
            "Sentimen":       lbl,
            "Jumlah":         len(sub),
            "% dari Total":   f"{len(sub)/total*100:.2f}%",
            "Rata-rata Token":f"{sub['token_count'].mean():.1f}",
            "Median Token":   f"{sub['token_count'].median():.0f}",
            "Rata-rata Karakter": f"{sub['text_len'].mean():.0f}",
        })
    st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — KARAKTERISTIK TEKS
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("📏 Karakteristik Linguistik Teks")

    # Histogram panjang karakter
    st.markdown("#### 📐 Distribusi Panjang Teks")
    ch1, ch2 = st.columns(2)
    with ch1:
        fig = px.histogram(
            df, x="text_len", color="sentiment",
            color_discrete_map=LABEL_COLORS, nbins=60,
            barmode="overlay", opacity=0.70, marginal="box",
            title="Distribusi Panjang Karakter per Sentimen",
            labels={"text_len": "Panjang (karakter)"},
        )
        fig.update_layout(height=420, margin=dict(t=50,b=10),
                          legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, use_container_width=True)
    with ch2:
        fig = px.histogram(
            df, x="token_count", color="sentiment",
            color_discrete_map=LABEL_COLORS, nbins=60,
            barmode="overlay", opacity=0.70, marginal="box",
            title="Distribusi Jumlah Token per Sentimen",
            labels={"token_count": "Jumlah Token"},
        )
        fig.update_layout(height=420, margin=dict(t=50,b=10),
                          legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Violin plot
    cv1, cv2 = st.columns(2)
    with cv1:
        fig = px.violin(df, x="sentiment", y="text_len",
                        color="sentiment", color_discrete_map=LABEL_COLORS,
                        box=True, points=False,
                        title="Violin — Panjang Karakter per Sentimen")
        fig.update_layout(height=400, margin=dict(t=50,b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cv2:
        fig = px.violin(df, x="sentiment", y="token_count",
                        color="sentiment", color_discrete_map=LABEL_COLORS,
                        box=True, points=False,
                        title="Violin — Jumlah Token per Sentimen")
        fig.update_layout(height=400, margin=dict(t=50,b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Lexical diversity & avg word len
    st.markdown("#### 🧠 Diversitas Leksikal & Panjang Rata-rata Kata")
    cl1, cl2 = st.columns(2)
    with cl1:
        fig = px.box(df, x="sentiment", y="lexical_diversity",
                     color="sentiment", color_discrete_map=LABEL_COLORS,
                     points="outliers", notched=True,
                     title="Lexical Diversity (unique tokens / total tokens)",
                     labels={"lexical_diversity":"Diversity Index"})
        fig.update_layout(height=380, margin=dict(t=50,b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cl2:
        fig = px.box(df, x="sentiment", y="avg_word_len",
                     color="sentiment", color_discrete_map=LABEL_COLORS,
                     points="outliers", notched=True,
                     title="Rata-rata Panjang Kata per Komentar",
                     labels={"avg_word_len":"Avg Word Length (karakter)"})
        fig.update_layout(height=380, margin=dict(t=50,b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Scatter token_count vs text_len
    st.markdown("#### 🔵 Korelasi: Jumlah Token vs Panjang Karakter")
    sample_df = df.sample(min(800, len(df)), random_state=SEED)
    fig = px.scatter(
        sample_df,
        x="token_count", y="text_len",
        color="sentiment", color_discrete_map=LABEL_COLORS,
        opacity=0.65,
        title="Scatter: Jumlah Token vs Panjang Karakter (sample 800)",
        labels={"token_count":"Jumlah Token", "text_len":"Panjang Karakter"},
    )
    # Trendline manual dengan numpy (tanpa statsmodels)
    x_all = sample_df["token_count"].values
    y_all = sample_df["text_len"].values
    mask  = ~(np.isnan(x_all) | np.isnan(y_all))
    if mask.sum() > 2:
        coef  = np.polyfit(x_all[mask], y_all[mask], 1)
        x_line = np.array([x_all[mask].min(), x_all[mask].max()])
        y_line = np.polyval(coef, x_line)
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode="lines",
            line=dict(color="black", width=2, dash="dash"),
            name=f"Trendline (semua)  y={coef[0]:.1f}x+{coef[1]:.0f}",
        ))
    fig.update_layout(height=420, margin=dict(t=50,b=10),
                      legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Statistik deskriptif tabel
    st.markdown("#### 📋 Statistik Deskriptif Lengkap per Label")
    stats = (
        df.groupby("sentiment").agg(
            Jumlah=("text_final","count"),
            Rata_Karakter=("text_len","mean"),
            Median_Karakter=("text_len","median"),
            Std_Karakter=("text_len","std"),
            Min_Karakter=("text_len","min"),
            Max_Karakter=("text_len","max"),
            Rata_Token=("token_count","mean"),
            Median_Token=("token_count","median"),
            Std_Token=("token_count","std"),
            Rata_Diversity=("lexical_diversity","mean"),
            Rata_AvgWordLen=("avg_word_len","mean"),
        ).round(2).reset_index()
    )
    stats.columns = [
        "Sentimen","Jumlah","Rata Karakter","Median Karakter","Std Karakter",
        "Min Karakter","Max Karakter","Rata Token","Median Token","Std Token",
        "Rata Diversity","Rata AvgWordLen",
    ]
    st.dataframe(stats, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — FREKUENSI KATA
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("🔤 Frekuensi & Persentase Kata")

    # Selector label
    col_sel, col_info = st.columns([2, 3])
    with col_sel:
        sel_label = st.selectbox(
            "Tampilkan kata untuk:",
            ["Semua Label"] + VALID_LABELS,
            key="t3_label",
        )
    label_key = None if sel_label == "Semua Label" else sel_label

    freq_df, total_tok = get_token_freq(df, label_key, remove_stop, top_n_words)
    with col_info:
        st.info(
            f"📊 **{sel_label}** — {total_tok:,} total token "
            f"| {len(freq_df)} kata ditampilkan"
            f"{'  |  Stopword dihapus ✓' if remove_stop else ''}",
        )

    if freq_df.empty:
        st.warning("Tidak ada data.")
    else:
        # Bar chart frekuensi
        bar_color = (LABEL_COLORS.get(label_key, "#3498DB")
                     if label_key else "#8E44AD")
        fig = go.Figure(go.Bar(
            x=freq_df["kata"],
            y=freq_df["frekuensi"],
            marker_color=bar_color,
            text=freq_df["frekuensi"],
            textposition="outside",
            customdata=freq_df[["persentase","rank"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Frekuensi: %{y:,}<br>"
                "Persentase: %{customdata[0]:.3f}%<br>"
                "Rank: #%{customdata[1]}<extra></extra>"
            ),
        ))
        fig.update_layout(
            title=f"Top {top_n_words} Kata Terbanyak — {sel_label}",
            xaxis_tickangle=-35,
            yaxis_title="Frekuensi",
            yaxis=dict(range=[0, freq_df["frekuensi"].max() * 1.2]),
            height=450, margin=dict(t=60, b=80),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Bar chart persentase
        fig2 = go.Figure(go.Bar(
            x=freq_df["kata"],
            y=freq_df["persentase"],
            marker_color=bar_color,
            text=freq_df["persentase"].apply(lambda v: f"{v:.2f}%"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:.3f}% dari total token<extra></extra>",
        ))
        fig2.update_layout(
            title=f"Persentase Kata dari Total Token — {sel_label}",
            xaxis_tickangle=-35,
            yaxis_title="Persentase (%)",
            yaxis=dict(range=[0, freq_df["persentase"].max() * 1.25]),
            height=450, margin=dict(t=60, b=80),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # Horizontal bar (lebih mudah dibaca untuk banyak kata)
        fig3 = go.Figure(go.Bar(
            y=freq_df["kata"][::-1],
            x=freq_df["frekuensi"][::-1],
            orientation="h",
            marker=dict(
                color=freq_df["frekuensi"][::-1],
                colorscale="Blues", showscale=True,
                colorbar=dict(title="Frekuensi"),
            ),
            text=freq_df.apply(
                lambda r: f"{r['frekuensi']:,}  ({r['persentase']:.2f}%)", axis=1
            )[::-1],
            textposition="outside",
        ))
        fig3.update_layout(
            title=f"Top {top_n_words} Kata — Horizontal (dengan %)",
            xaxis_title="Frekuensi",
            height=max(400, top_n_words * 22),
            margin=dict(t=60, b=20, l=120),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # Tabel lengkap
        st.markdown("#### 📋 Tabel Frekuensi Lengkap")
        display_df = freq_df.copy()
        display_df.columns = ["Kata","Frekuensi","Persentase (%)","Rank"]
        display_df["Kumulatif (%)"] = display_df["Persentase (%)"].cumsum().round(3)
        st.dataframe(
            display_df.style.background_gradient(subset=["Frekuensi"], cmap="Blues")
                            .format({"Persentase (%)": "{:.3f}%",
                                     "Kumulatif (%)": "{:.2f}%"}),
            use_container_width=True, hide_index=True, height=400,
        )
        st.caption(
            f"💡 Top {min(10,top_n_words)} kata menyumbang "
            f"**{display_df['Persentase (%)'].head(10).sum():.1f}%** dari total token."
        )


# ─────────────────────────────────────────────────────────────────────────
# TAB 4 — WORD CLOUD
# ─────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("☁️ Word Cloud per Sentimen")

    wc_tabs = st.tabs(["😊 Positif", "😐 Netral", "😠 Negatif", "🌐 Semua"])
    wc_configs = [
        ("positif", "Positif",  "#f0fff4"),
        ("netral",  "Netral",   "#f0f8ff"),
        ("negatif", "Negatif",  "#fff5f5"),
        (None,      "Semua Label", "#f5f5f5"),
    ]
    for wc_tab, (lbl, lbl_name, bg) in zip(wc_tabs, wc_configs):
        with wc_tab:
            subset_size = len(df) if lbl is None else int((df["sentiment"]==lbl).sum())
            st.caption(f"**{lbl_name}** — {subset_size:,} komentar")
            with st.spinner(f"Membuat word cloud {lbl_name}..."):
                img_bytes = get_wordcloud_img(df, lbl, remove_stop, bg)
            st.image(img_bytes, use_container_width=True)

            # Juga tampilkan top 20 kata di bawah word cloud
            freq_wc, total_wc = get_token_freq(df, lbl, remove_stop, 20)
            if not freq_wc.empty:
                color_wc = LABEL_COLORS.get(lbl, "#8E44AD") if lbl else "#8E44AD"
                fig_wc = go.Figure(go.Bar(
                    y=freq_wc["kata"][::-1],
                    x=freq_wc["frekuensi"][::-1],
                    orientation="h",
                    marker_color=color_wc,
                    text=freq_wc.apply(
                        lambda r: f"{r['frekuensi']:,} ({r['persentase']:.2f}%)", axis=1
                    )[::-1],
                    textposition="outside",
                ))
                fig_wc.update_layout(
                    title=f"Top 20 Kata — {lbl_name}",
                    xaxis_title="Frekuensi",
                    height=520, margin=dict(t=50,b=10,l=100),
                )
                st.plotly_chart(fig_wc, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 5 — N-GRAM
# ─────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("🔗 Analisis N-Gram")

    col_ng1, col_ng2, col_ng3 = st.columns(3)
    with col_ng1:
        sel_n = st.radio("Tipe N-Gram:", [("Bigram (2)", 2), ("Trigram (3)", 3)],
                         format_func=lambda x: x[0], key="t5_n")
        n_val = sel_n[1]
    with col_ng2:
        sel_lbl_ng = st.selectbox("Label:", ["Semua Label"]+VALID_LABELS, key="t5_lbl")
        label_ng = None if sel_lbl_ng == "Semua Label" else sel_lbl_ng
    with col_ng3:
        st.markdown("&nbsp;")
        st.info(f"N = **{n_val}** | Label: **{sel_lbl_ng}**")

    ngram_df, total_ng = get_ngram_freq(df, label_ng, n_val, remove_stop, top_n_ngram)

    if ngram_df.empty:
        st.warning("Tidak ada data n-gram.")
    else:
        ng_color = LABEL_COLORS.get(label_ng, "#8E44AD") if label_ng else "#8E44AD"

        cn1, cn2 = st.columns(2)
        with cn1:
            fig = go.Figure(go.Bar(
                x=ngram_df["ngram"],
                y=ngram_df["frekuensi"],
                marker_color=ng_color,
                text=ngram_df["frekuensi"],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Frek: %{y:,}<extra></extra>",
            ))
            fig.update_layout(
                title=f"Top {top_n_ngram} {sel_n[0]} — Frekuensi",
                xaxis_tickangle=-40,
                yaxis=dict(range=[0, ngram_df["frekuensi"].max()*1.2]),
                height=460, margin=dict(t=60,b=120),
            )
            st.plotly_chart(fig, use_container_width=True)

        with cn2:
            fig2 = go.Figure(go.Bar(
                y=ngram_df["ngram"][::-1],
                x=ngram_df["persentase"][::-1],
                orientation="h",
                marker=dict(color=ngram_df["persentase"][::-1],
                            colorscale="Purples", showscale=True),
                text=ngram_df["persentase"].apply(lambda v: f"{v:.3f}%")[::-1],
                textposition="outside",
            ))
            fig2.update_layout(
                title=f"Top {top_n_ngram} {sel_n[0]} — Persentase",
                xaxis_title="Persentase (%)",
                height=460, margin=dict(t=60,b=20,l=160),
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # N-gram per label side by side
        st.markdown(f"#### 🔍 Perbandingan {sel_n[0]} per Sentimen")
        cols_ng = st.columns(3)
        for i, lbl_ng in enumerate(VALID_LABELS):
            ng_sub, _ = get_ngram_freq(df, lbl_ng, n_val, remove_stop, 10)
            with cols_ng[i]:
                if not ng_sub.empty:
                    fig = go.Figure(go.Bar(
                        y=ng_sub["ngram"][::-1],
                        x=ng_sub["frekuensi"][::-1],
                        orientation="h",
                        marker_color=LABEL_COLORS[lbl_ng],
                        text=ng_sub["frekuensi"][::-1],
                        textposition="outside",
                    ))
                    fig.update_layout(
                        title=f"{lbl_ng.capitalize()} — Top 10",
                        height=380, margin=dict(t=50,b=10,l=130),
                    )
                    st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Tabel n-gram
        st.markdown(f"#### 📋 Tabel {sel_n[0]}")
        ng_display = ngram_df.copy()
        ng_display.columns = [f"{sel_n[0]}", "Frekuensi", "Persentase (%)"]
        ng_display["Kumulatif (%)"] = ng_display["Persentase (%)"].cumsum().round(3)
        st.dataframe(
            ng_display.style.background_gradient(subset=["Frekuensi"], cmap="Purples")
                            .format({"Persentase (%)": "{:.3f}%",
                                     "Kumulatif (%)": "{:.2f}%"}),
            use_container_width=True, hide_index=True,
        )


# ─────────────────────────────────────────────────────────────────────────
# TAB 6 — PERBANDINGAN LINTAS LABEL
# ─────────────────────────────────────────────────────────────────────────
with tab6:
    st.subheader("📊 Perbandingan Kata Lintas Sentimen")

    cross_df = get_cross_label_freq(df, remove_stop, top_n_words)

    # ── Heatmap frekuensi kata per label ──────────────────────────────────
    st.markdown("#### 🔥 Heatmap Frekuensi Kata per Sentimen")

    # Ambil kata yang muncul di minimal 2 label
    pivot = cross_df.pivot_table(
        index="kata", columns="sentimen", values="persen", fill_value=0
    )
    # Filter kata yang ada di semua label dan total persen tinggi
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False).head(30).drop(columns="total")
    pivot = pivot.sort_values(by=list(pivot.columns), ascending=False)

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="YlOrRd",
        text=[[f"{v:.3f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hovertemplate="Kata: <b>%{y}</b><br>Sentimen: <b>%{x}</b><br>%{z:.4f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="% Token"),
    ))
    fig_heat.update_layout(
        title="Heatmap % Kemunculan Kata per Sentimen (Top 30 kata)",
        xaxis_title="Sentimen",
        height=700, margin=dict(t=60, b=20, l=120),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # ── Kata eksklusif / unik per sentimen ────────────────────────────────
    st.markdown("#### 🎯 Kata yang Menonjol di Masing-masing Sentimen")
    st.caption("Kata yang persentasenya jauh lebih tinggi di satu sentimen dibanding lainnya.")

    cols_excl = st.columns(3)
    for i, lbl in enumerate(VALID_LABELS):
        other_lbls = [l for l in VALID_LABELS if l != lbl]
        lbl_freq, _ = get_token_freq(df, lbl, remove_stop, 200)
        oth_freq, _ = get_token_freq(df, None, remove_stop, 200)
        if lbl_freq.empty:
            continue
        # Dominance score: persen di label ini - persen di semua label
        merged = lbl_freq.set_index("kata")[["persentase"]].rename(
            columns={"persentase": "pct_label"}
        ).join(
            oth_freq.set_index("kata")[["persentase"]].rename(
                columns={"persentase": "pct_all"}
            ), how="left"
        ).fillna(0)
        merged["dominance"] = merged["pct_label"] - merged["pct_all"]
        top_excl = merged.sort_values("dominance", ascending=False).head(15)

        with cols_excl[i]:
            fig_excl = go.Figure(go.Bar(
                y=top_excl.index[::-1],
                x=top_excl["dominance"][::-1],
                orientation="h",
                marker_color=LABEL_COLORS[lbl],
                text=top_excl["dominance"][::-1].apply(lambda v: f"+{v:.3f}%"),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Dominance: +%{x:.4f}%<extra></extra>",
            ))
            fig_excl.update_layout(
                title=f"😊 {lbl.capitalize()}" if lbl == "positif"
                      else f"😐 {lbl.capitalize()}" if lbl == "netral"
                      else f"😠 {lbl.capitalize()}",
                xaxis_title="Dominance Score (%)",
                height=460, margin=dict(t=50,b=10,l=100),
            )
            st.plotly_chart(fig_excl, use_container_width=True)

    st.divider()

    # ── Stacked bar frekuensi absolut top kata per label ──────────────────
    st.markdown("#### 📊 Perbandingan Frekuensi Kata Antar Sentimen")
    top_words_global, _ = get_token_freq(df, None, remove_stop, 20)
    if not top_words_global.empty:
        top_words_list = top_words_global["kata"].tolist()
        records_comp = []
        for lbl in VALID_LABELS:
            lbl_freq_full, lbl_total = get_token_freq(df, lbl, remove_stop, 200)
            lbl_dict = lbl_freq_full.set_index("kata")["persentase"].to_dict()
            for w in top_words_list:
                records_comp.append({
                    "kata": w, "sentimen": lbl,
                    "persentase": lbl_dict.get(w, 0),
                })
        comp_df = pd.DataFrame(records_comp)
        fig_comp = px.bar(
            comp_df, x="kata", y="persentase", color="sentimen",
            color_discrete_map=LABEL_COLORS, barmode="group",
            text=comp_df["persentase"].apply(lambda v: f"{v:.2f}%"),
            title="Persentase Kemunculan Top 20 Kata per Sentimen",
            labels={"kata":"Kata","persentase":"Persentase (%)","sentimen":"Sentimen"},
        )
        fig_comp.update_traces(textposition="outside")
        fig_comp.update_layout(
            xaxis_tickangle=-35,
            yaxis_title="% dari Token Label",
            height=480, margin=dict(t=60,b=100),
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.divider()

    # ── Treemap komposisi kata ─────────────────────────────────────────────
    st.markdown("#### 🌳 Treemap Kata Dominan per Sentimen")
    treemap_records = []
    for lbl in VALID_LABELS:
        freq_tm, total_tm = get_token_freq(df, lbl, remove_stop, 20)
        for _, row in freq_tm.iterrows():
            treemap_records.append({
                "sentimen": lbl, "kata": row["kata"],
                "frekuensi": row["frekuensi"],
                "label_kata": f"{row['kata']} ({row['frekuensi']:,})",
            })
    if treemap_records:
        tm_df = pd.DataFrame(treemap_records)
        fig_tm = px.treemap(
            tm_df, path=["sentimen","kata"],
            values="frekuensi",
            color="sentimen", color_discrete_map=LABEL_COLORS,
            title=f"Treemap Top {top_n_words} Kata per Sentimen (luas = frekuensi)",
            hover_data={"frekuensi": True},
        )
        fig_tm.update_traces(textinfo="label+value")
        fig_tm.update_layout(height=550, margin=dict(t=60,b=10))
        st.plotly_chart(fig_tm, use_container_width=True)


# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"📊 EDA Dashboard — Analisis Sentimen Komentar YouTube  |  "
    f"DB: `{MONGO_DB}` · Collection: `{SOURCE_COL}`  |  "
    f"Total: {total:,} komentar · Vocab: {vocab_size:,} kata unik"
)
