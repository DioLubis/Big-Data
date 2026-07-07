"""Dashboard EDA — Analisis Sentimen Komentar YouTube"""
from __future__ import annotations
import io, os
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from wordcloud import WordCloud

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="EDA Sentimen YouTube", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""<style>
.stApp{background:#FFFFFF;color:#1E293B}
section[data-testid="stSidebar"]{background:#1E3A5F;border-right:1px solid #CBD5E1}
section[data-testid="stSidebar"] *{color:#F1F5F9!important}
section[data-testid="stSidebar"] .stButton>button{background:#2563EB;color:#FFF!important;border:none;border-radius:6px;font-weight:600}
[data-testid="metric-container"]{background:#F8FAFC;border:1px solid #E2E8F0;border-top:3px solid #2563EB;border-radius:8px;padding:12px 16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
[data-testid="metric-container"] label{color:#64748B!important;font-size:.8rem}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#1E293B!important;font-weight:700}
button[data-baseweb="tab"]{font-weight:600;color:#64748B!important}
button[data-baseweb="tab"][aria-selected="true"]{color:#2563EB!important;border-bottom:2px solid #2563EB}
h1{color:#1E293B!important;font-weight:800}h2,h3{color:#1E3A5F!important}
hr{border-color:#E2E8F0}
</style>""", unsafe_allow_html=True)

# ── Konstanta ─────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)
MONGO_URI    = os.getenv("MONGO_URI", "")
MONGO_DB     = os.getenv("MONGO_DB", "analisis_sentimen")
SOURCE_COL   = "comments_sentiment"       # data manual
AUTO_COL     = "phase2_auto_labeled"      # data auto-labeled
COMMENTS_COL = "comments"
VALID_LABELS = ["positif", "netral", "negatif"]
LABEL_COLORS = {"positif": "#16A34A", "netral": "#2563EB", "negatif": "#DC2626"}
SEED         = 42

VIDEO_TITLES = {
    "KjXe214MfwQ": "RUU TNI itu apa? Mirip Orde Baru?",
    "7CLZkPwhEG4": "Revisi UU TNI: Dampak bagi Masyarakat Sipil (BBC)",
    "F6fgLwUeeqI": "BATALKAN REVISI UU TNI (Pandji)",
    "sg8Mzx0fZbU": "Revisi UU TNI (Sepulang Sekolah)",
    "MxCqHoldj2Y": "RUU TNI Resmi Jadi UU (METRO TV)",
}

# Stopword: kata sambung / kata hubung yang tidak informatif
STOPWORDS = {
    "yang","dan","di","ini","itu","dengan","tidak","saya","kamu","kami","kita",
    "ada","kalau","juga","untuk","dari","pada","ke","ya","bisa","sudah","akan",
    "lebih","jadi","atau","tapi","karena","aja","saja","bro","dong","lah","pun",
    "nya","nih","si","iya","juga","buat","saat","bila","jika","maka","agar",
    "supaya","namun","tetapi","sedang","telah","pun","lagi","pula","hanya","bahwa",
    "oleh","atas","bagi","antara","setelah","sebelum","seperti","karena","sebab",
    "meski","walaupun","ialah","adalah","merupakan","dalam","demi","per","serta",
}

# Plotly template putih
pio.templates["eda_white"] = go.layout.Template(layout=go.Layout(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#F8FAFC",
    font=dict(family="Inter,Segoe UI,Arial,sans-serif", color="#1E293B", size=13),
    title=dict(font=dict(size=15, color="#1E293B"), x=0.02),
    colorway=["#2563EB","#16A34A","#DC2626","#D97706","#7C3AED","#0891B2"],
    xaxis=dict(gridcolor="#E2E8F0", linecolor="#CBD5E1",
               tickfont=dict(color="#475569", size=12), zerolinecolor="#E2E8F0"),
    yaxis=dict(gridcolor="#E2E8F0", linecolor="#CBD5E1",
               tickfont=dict(color="#475569", size=12), zerolinecolor="#E2E8F0"),
    legend=dict(bgcolor="rgba(255,255,255,.95)", bordercolor="#E2E8F0",
                borderwidth=1, font=dict(size=12, color="#1E293B")),
    hoverlabel=dict(bgcolor="#1E293B", font_color="#F8FAFC",
                    bordercolor="#1E293B", font_size=13),
))
pio.templates.default = "eda_white"

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_client():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)


@st.cache_data(ttl=300, show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return (df_manual, df_full):
      - df_manual : 2000 data berlabel manual dari comments_sentiment
      - df_full   : 13446 data gabungan dari full_comments_sentiment
                    (sudah include kolom tanggal, video_id, like_count dari join)
    """
    # ── Helper: join tanggal + video info dari collection comments ────────────
    def _enrich(df: pd.DataFrame) -> pd.DataFrame:
        dates = list(get_client()[MONGO_DB][COMMENTS_COL].find(
            {"comment_id": {"$exists": True}, "published_at": {"$exists": True}},
            {"_id": 0, "comment_id": 1, "published_at": 1,
             "video_id": 1, "like_count": 1},
        ))
        dates_df = pd.DataFrame(dates)
        if not dates_df.empty:
            df = df.merge(dates_df, on="comment_id", how="left")
            df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
            df["date"] = df["published_at"].dt.date
        else:
            df["date"] = None
            df["video_id"] = df.get("video_id", None)
            df["like_count"] = 0

        df["like_count"] = pd.to_numeric(df.get("like_count", 0), errors="coerce").fillna(0).astype(int)
        df["video_id"]   = df.get("video_id", "")
        df["video_title"] = df["video_id"].map(VIDEO_TITLES).fillna(df["video_id"])
        df["video_short"] = df["video_title"].apply(
            lambda t: t[:40] + "…" if len(str(t)) > 40 else t)

        # Fitur teks
        df["text_len"]    = df["text_final"].str.len()
        df["token_count"] = df["text_final"].str.split().str.len()
        df["unique_tokens"] = df["text_final"].apply(lambda t: len(set(str(t).split())))
        df["lexical_diversity"] = (
            df["unique_tokens"] / df["token_count"].replace(0, np.nan)
        ).round(4)
        df["avg_word_len"] = df["text_final"].apply(
            lambda t: round(np.mean([len(w) for w in str(t).split()]), 2)
            if str(t).split() else 0)
        return df

    # ── Load data manual dari comments_sentiment ─────────────────────────────
    docs_manual = list(get_client()[MONGO_DB][SOURCE_COL].find(
        {"text_final": {"$exists": True, "$ne": ""},
         "sentiment":  {"$exists": True, "$nin": [None, ""]}},
        {"_id": 0, "comment_id": 1, "video_id": 1,
         "text_final": 1, "sentiment": 1, "text_original": 1},
    ))
    df_manual = pd.DataFrame(docs_manual)
    if not df_manual.empty:
        df_manual = _enrich(df_manual)
        df_manual["data_source"] = "Manual"

    # ── Load data auto-label dari phase2_auto_labeled ─────────────────────────
    docs_auto = list(get_client()[MONGO_DB][AUTO_COL].find(
        {"text_final": {"$exists": True, "$ne": ""},
         "sentiment":  {"$exists": True, "$nin": [None, ""]}},
        {"_id": 0, "comment_id": 1, "video_id": 1,
         "text_final": 1, "sentiment": 1, "text_original": 1},
    ))
    df_auto = pd.DataFrame(docs_auto)
    if not df_auto.empty:
        df_auto = _enrich(df_auto)
        df_auto["data_source"] = "Auto-label"

    # ── Gabungkan keduanya ────────────────────────────────────────────────────
    frames = [f for f in [df_manual, df_auto] if not f.empty]
    if frames:
        df_full = pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["comment_id"], keep="first")
        df_full["data_source"] = df_full["data_source"].fillna("Auto-label")
    else:
        df_full = pd.DataFrame()

    return df_manual, df_full


@st.cache_data(show_spinner=False)
def get_token_freq(df, label, top_n):
    subset = df if label is None else df[df["sentiment"] == label]
    tokens = []
    for txt in subset["text_final"]:
        for t in str(txt).split():
            if t not in STOPWORDS and len(t) > 2 and t.isalpha():
                tokens.append(t)
    total = len(tokens)
    rows = pd.DataFrame(Counter(tokens).most_common(top_n), columns=["kata","frekuensi"])
    rows["persen"] = (rows["frekuensi"] / total * 100).round(2)
    return rows, total


@st.cache_data(show_spinner=False)
def get_ngram_freq(df, label, n, top_n):
    subset = df if label is None else df[df["sentiment"] == label]
    ngrams = []
    for txt in subset["text_final"]:
        words = [w for w in str(txt).split()
                 if w not in STOPWORDS and len(w) > 2 and w.isalpha()]
        ngrams.extend([" ".join(words[i:i+n]) for i in range(len(words)-n+1)])
    total = len(ngrams)
    rows = pd.DataFrame(Counter(ngrams).most_common(top_n), columns=["ngram","frekuensi"])
    rows["persen"] = (rows["frekuensi"] / total * 100).round(2)
    return rows, total


@st.cache_data(show_spinner=False)
def get_wordcloud_img(df, label, bg):
    subset = df if label is None else df[df["sentiment"] == label]
    text = " ".join(
        w for txt in subset["text_final"]
        for w in str(txt).split()
        if w not in STOPWORDS and len(w) > 2 and w.isalpha()
    )
    cmap = ("Greens" if label=="positif" else "Blues" if label=="netral"
            else "Reds" if label=="negatif" else "viridis")
    wc = WordCloud(width=900, height=400, background_color=bg,
                   colormap=cmap, max_words=120, collocations=False,
                   random_state=SEED).generate(text or "kosong")
    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    return buf.getvalue()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("EDA Sentimen")
    st.caption("Analisis Komentar YouTube")
    st.divider()
    try:
        get_client().admin.command("ping")
        st.success("MongoDB terhubung")
    except Exception:
        st.error("MongoDB tidak terhubung")
    st.divider()
    st.subheader("Pengaturan")
    top_n_words = st.slider("Top N kata", 5, 40, 20)
    top_n_ngram = st.slider("Top N n-gram", 5, 25, 15)
    st.divider()
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner("Memuat data..."):
    df_manual, df = load_data()   # df = 13446 gabungan, df_manual = 2000 manual

if df.empty:
    st.error("Data tidak ditemukan.")
    st.stop()

# df digunakan untuk semua tab kecuali distribusi (yang pakai keduanya)
total     = len(df)
total_m   = len(df_manual)
total_a   = int((df["data_source"] == "Auto-label").sum())
n_pos     = int((df["sentiment"]=="positif").sum())
n_net     = int((df["sentiment"]=="netral").sum())
n_neg     = int((df["sentiment"]=="negatif").sum())
has_date  = df["date"].notna().sum() > 10

# ── Header KPI ────────────────────────────────────────────────────────────────
st.title("Analisis Sentimen Komentar YouTube")
st.caption("Eksplorasi distribusi sentimen, tren waktu, frekuensi kata, dan insight penting.")

k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Total Data Gabungan", f"{total:,}")
k2.metric("Manual Labeled",      f"{total_m:,}")
k3.metric("Auto Labeled",        f"{total_a:,}")
k4.metric("Positif",  f"{n_pos:,}",  f"{n_pos/total*100:.1f}%")
k5.metric("Netral",   f"{n_net:,}",  f"{n_net/total*100:.1f}%")
k6.metric("Negatif",  f"{n_neg:,}",  f"{n_neg/total*100:.1f}%")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Distribusi Sentimen",
    "Tren Waktu",
    "Frekuensi Kata",
    "N-Gram & Word Cloud",
    "Insight per Video",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DISTRIBUSI SENTIMEN
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Distribusi Label Sentimen")

    # ── Sub-tab: Perbandingan Manual vs Auto vs Gabungan ──────────────────────
    dist_tab1, dist_tab2, dist_tab3 = st.tabs([
        f"Manual Label ({total_m:,} data)",
        f"Auto Label ({total_a:,} data)",
        f"Gabungan ({total:,} data)",
    ])

    def _dist_charts(ddf: pd.DataFrame, label: str):
        """Render bar + pie + lollipop untuk satu dataset."""
        tot   = len(ddf)
        n_p   = int((ddf["sentiment"]=="positif").sum())
        n_n_  = int((ddf["sentiment"]=="netral").sum())
        n_ng  = int((ddf["sentiment"]=="negatif").sum())

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Bar(
                x=["Positif","Netral","Negatif"], y=[n_p, n_n_, n_ng],
                marker_color=[LABEL_COLORS["positif"],LABEL_COLORS["netral"],LABEL_COLORS["negatif"]],
                text=[f"{n_p:,}<br>{n_p/tot*100:.1f}%",
                      f"{n_n_:,}<br>{n_n_/tot*100:.1f}%",
                      f"{n_ng:,}<br>{n_ng/tot*100:.1f}%"],
                textposition="outside",
            ))
            fig.update_layout(
                title=f"Jumlah Komentar — {label}",
                yaxis_title="Jumlah",
                yaxis=dict(range=[0, max(n_p,n_n_,n_ng)*1.28]),
                height=420, margin=dict(t=55,b=15),
            )
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = go.Figure(go.Pie(
                labels=["Positif","Netral","Negatif"],
                values=[n_p, n_n_, n_ng],
                marker_colors=[LABEL_COLORS["positif"],LABEL_COLORS["netral"],LABEL_COLORS["negatif"]],
                hole=0.45, textinfo="label+percent", textfont_size=14,
                hovertemplate="<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(title=f"Proporsi Sentimen — {label}",
                              height=420, margin=dict(t=55,b=15))
            st.plotly_chart(fig, use_container_width=True)

        # Lollipop imbalance
        ideal = 100/3
        fig_lo = go.Figure()
        for lbl, n in [("positif",n_p),("netral",n_n_),("negatif",n_ng)]:
            pct = n/tot*100
            fig_lo.add_trace(go.Scatter(
                x=[0,pct], y=[lbl,lbl], mode="lines",
                line=dict(color=LABEL_COLORS[lbl], width=5), showlegend=False))
            fig_lo.add_trace(go.Scatter(
                x=[pct], y=[lbl], mode="markers+text",
                marker=dict(size=22, color=LABEL_COLORS[lbl],
                            line=dict(width=2, color="white")),
                text=f"  {pct:.1f}%  ({n:,})",
                textposition="middle right", showlegend=False))
        fig_lo.add_vline(x=ideal, line_dash="dash", line_color="#94A3B8",
                         annotation_text=f"Ideal = {ideal:.1f}%",
                         annotation_position="top right")
        fig_lo.update_layout(
            title=f"Ketidakseimbangan Kelas — {label}",
            xaxis=dict(title="Persentase (%)", range=[0,80]),
            height=260, margin=dict(t=50,b=20,l=80))
        st.plotly_chart(fig_lo, use_container_width=True)
        st.caption(
            "Grafik lollipop menunjukkan seberapa jauh distribusi dari kondisi seimbang (33% per kelas). "
            "Titik yang jauh ke kanan berarti sentimen itu mendominasi data."
        )

        # Info
        ci1, ci2 = st.columns(2)
        with ci1:
            st.info(f"Rasio negatif : positif = **{n_ng//max(n_p,1)} : 1**")
        with ci2:
            dom = max(VALID_LABELS, key=lambda l: (ddf["sentiment"]==l).sum())
            st.warning(f"Sentimen dominan: **{dom.upper()}** "
                       f"({(ddf['sentiment']==dom).sum()/tot*100:.1f}%)")

    with dist_tab1:
        _dist_charts(df_manual, "Manual Label")
    with dist_tab2:
        df_auto_tab = df[df["data_source"] == "Auto-label"]
        _dist_charts(df_auto_tab, "Auto Label")
    with dist_tab3:
        _dist_charts(df, "Gabungan")

    st.divider()

    # ── Perbandingan manual vs auto (grouped bar) ─────────────────────────────
    st.markdown("#### Perbandingan Distribusi: Manual vs Auto vs Gabungan")
    comp_records = []
    for src_label, ddf in [
        ("Manual", df_manual),
        ("Auto-label",  df[df["data_source"]=="Auto-label"]),
        ("Gabungan", df),
    ]:
        tot = len(ddf)
        for lbl in VALID_LABELS:
            n = int((ddf["sentiment"]==lbl).sum())
            comp_records.append({"Sumber": src_label, "Sentimen": lbl.capitalize(),
                                  "Persentase": round(n/tot*100, 2)})
    comp_df = pd.DataFrame(comp_records)
    fig_cmp = px.bar(
        comp_df, x="Sentimen", y="Persentase", color="Sumber",
        barmode="group",
        color_discrete_sequence=["#2563EB","#D97706","#16A34A"],
        text=comp_df["Persentase"].apply(lambda v: f"{v:.1f}%"),
        title="Perbandingan Proporsi Sentimen: Manual vs Auto vs Gabungan",
        labels={"Persentase":"Persentase (%)"},
    )
    fig_cmp.update_traces(textposition="outside")
    fig_cmp.update_layout(yaxis=dict(range=[0,85]),
                          height=420, margin=dict(t=55,b=15),
                          legend=dict(orientation="h", y=1.06))
    st.plotly_chart(fig_cmp, use_container_width=True)
    st.caption(
        "Perbandingan ini menunjukkan konsistensi distribusi antara data manual "
        "dan data auto-label — perbedaan besar mengindikasikan bias pada model labeling."
    )

    st.divider()

    # ── Like per sentimen (data gabungan) ─────────────────────────────────────
    st.markdown("#### Rata-rata Jumlah Like per Sentimen (Data Gabungan)")
    like_df = df.groupby("sentiment")["like_count"].agg(["mean","median","sum"]).round(1).reset_index()
    like_df.columns = ["Sentimen","Rata-rata Like","Median Like","Total Like"]
    lc1, lc2 = st.columns(2)
    with lc1:
        fig = go.Figure(go.Bar(
            x=like_df["Sentimen"], y=like_df["Rata-rata Like"],
            marker_color=[LABEL_COLORS[l] for l in like_df["Sentimen"]],
            text=like_df["Rata-rata Like"], textposition="outside",
        ))
        fig.update_layout(title="Rata-rata Like per Sentimen",
                          yaxis_title="Rata-rata Like",
                          yaxis=dict(range=[0, like_df["Rata-rata Like"].max()*1.3]),
                          height=380, margin=dict(t=55,b=15))
        st.plotly_chart(fig, use_container_width=True)
    with lc2:
        st.dataframe(like_df.style.background_gradient(
            subset=["Rata-rata Like","Total Like"], cmap="Blues"),
            use_container_width=True, hide_index=True)
        st.caption("Komentar bersentimen positif cenderung mendapat lebih banyak like.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TREN WAKTU
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def get_spike_wordcloud_img(df_spike, label, bg, title_text):
    """Buat word cloud dari komentar di periode lonjakan."""
    subset = df_spike if label is None else df_spike[df_spike["sentiment"] == label]
    text = " ".join(
        w for txt in subset["text_final"]
        for w in str(txt).split()
        if w not in STOPWORDS and len(w) > 2 and w.isalpha()
    )
    if not text.strip():
        text = "tidak ada data"
    cmap = ("Reds" if label == "negatif" else "Greens" if label == "positif"
            else "Blues" if label == "netral" else "plasma")
    wc = WordCloud(width=700, height=320, background_color=bg,
                   colormap=cmap, max_words=80, collocations=False,
                   random_state=SEED).generate(text)
    buf = io.BytesIO()
    wc.to_image().save(buf, format="PNG")
    return buf.getvalue()


with tab2:
    st.subheader("Tren Sentimen Berdasarkan Waktu")

    if not has_date:
        st.warning("Data tanggal tidak tersedia.")
    else:
        df_dated = df[df["date"].notna()].copy()
        df_dated["date"] = pd.to_datetime(df_dated["date"])

        # Hitung batas default: periode padat (median ke atas volumenya)
        daily_all = df_dated.groupby(df_dated["date"].dt.date).size()
        dense_dates = daily_all[daily_all >= daily_all.quantile(0.4)].index
        default_start = pd.to_datetime(min(dense_dates)).date()
        default_end   = pd.to_datetime(max(dense_dates)).date()
        date_min = df_dated["date"].min().date()
        date_max = df_dated["date"].max().date()

        st.caption(
            f"Rentang data: **{date_min.strftime('%d %b %Y')}** — "
            f"**{date_max.strftime('%d %b %Y')}**  |  "
            f"Data terpadat: Maret 2025. Gunakan filter di bawah untuk zoom."
        )

        # ── Filter & granularitas ─────────────────────────────────────────────
        col_f1, col_f2, col_f3 = st.columns([2,2,2])
        with col_f1:
            gran = st.radio("Granularitas:", ["Harian","Mingguan"],
                            horizontal=True, key="gran")
        with col_f2:
            filter_start = st.date_input("Dari tanggal:", value=default_start,
                                          min_value=date_min, max_value=date_max, key="d_from")
        with col_f3:
            filter_end = st.date_input("Sampai tanggal:", value=default_end,
                                        min_value=date_min, max_value=date_max, key="d_to")

        df_f = df_dated[
            (df_dated["date"].dt.date >= filter_start) &
            (df_dated["date"].dt.date <= filter_end)
        ].copy()

        if df_f.empty:
            st.warning("Tidak ada data pada rentang tanggal ini.")
        else:
            if gran == "Harian":
                df_f["period"] = df_f["date"].dt.date
            else:
                df_f["period"] = df_f["date"].dt.to_period("W").apply(
                    lambda p: p.start_time.date() if hasattr(p, "start_time") else None)

            trend = (df_f.groupby(["period","sentiment"])
                         .size().reset_index(name="count"))
            trend["period"] = pd.to_datetime(trend["period"])
            trend_wide = trend.pivot_table(
                index="period", columns="sentiment", values="count", fill_value=0
            ).reset_index().sort_values("period")
            for lbl in VALID_LABELS:
                if lbl not in trend_wide.columns:
                    trend_wide[lbl] = 0

            # KPI
            tk1,tk2,tk3,tk4 = st.columns(4)
            tk1.metric("Komentar",    f"{len(df_f):,}")
            tk2.metric("Negatif",     f"{int(trend_wide['negatif'].sum()):,}")
            tk3.metric("Positif",     f"{int(trend_wide['positif'].sum()):,}")
            pct_neg = int(trend_wide['negatif'].sum()) / max(len(df_f),1) * 100
            tk4.metric("% Negatif",   f"{pct_neg:.1f}%")
            st.divider()

            # ── Grafik garis Positif vs Negatif ──────────────────────────────
            st.markdown("#### Tren Komentar Positif vs Negatif")
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=trend_wide["period"], y=trend_wide["negatif"],
                mode="lines+markers", name="Negatif",
                line=dict(color=LABEL_COLORS["negatif"], width=2.5),
                marker=dict(size=5), fill="tozeroy",
                fillcolor="rgba(220,38,38,0.10)",
            ))
            fig_line.add_trace(go.Scatter(
                x=trend_wide["period"], y=trend_wide["positif"],
                mode="lines+markers", name="Positif",
                line=dict(color=LABEL_COLORS["positif"], width=2.5),
                marker=dict(size=5), fill="tozeroy",
                fillcolor="rgba(22,163,74,0.10)",
            ))

            y_max = max(trend_wide["negatif"].max(), trend_wide["positif"].max(), 1)
            peak_neg = trend_wide.loc[trend_wide["negatif"].idxmax()]
            peak_pos = trend_wide.loc[trend_wide["positif"].idxmax()]
            fig_line.add_annotation(
                x=peak_neg["period"], y=peak_neg["negatif"],
                text=f"Puncak Negatif<br>{int(peak_neg['negatif']):,}",
                showarrow=True, arrowhead=2,
                arrowcolor=LABEL_COLORS["negatif"],
                font=dict(color=LABEL_COLORS["negatif"], size=11),
                bgcolor="white", bordercolor=LABEL_COLORS["negatif"], ax=0, ay=-50,
            )
            if peak_pos["positif"] > 0:
                fig_line.add_annotation(
                    x=peak_pos["period"], y=peak_pos["positif"],
                    text=f"Puncak Positif<br>{int(peak_pos['positif']):,}",
                    showarrow=True, arrowhead=2,
                    arrowcolor=LABEL_COLORS["positif"],
                    font=dict(color=LABEL_COLORS["positif"], size=11),
                    bgcolor="white", bordercolor=LABEL_COLORS["positif"], ax=0, ay=-50,
                )

            fig_line.update_layout(
                title=f"Tren Sentimen Positif vs Negatif ({gran})",
                xaxis_title="Tanggal", yaxis_title="Jumlah Komentar",
                yaxis=dict(range=[0, y_max * 1.28],
                           dtick=max(1, int(y_max / 8))),
                height=480, margin=dict(t=55,b=15),
                legend=dict(orientation="h", y=1.06),
            )
            st.plotly_chart(fig_line, use_container_width=True)
            st.caption(
                "Grafik ini memperlihatkan bagaimana jumlah komentar negatif dan positif berubah dari waktu ke waktu. "
                "Lonjakan tajam biasanya muncul ketika ada berita atau peristiwa besar yang ramai dibahas."
            )

            # ── Analisis lonjakan dengan word cloud ───────────────────────────
            st.markdown("##### Analisis Lonjakan — Kata Kunci & Word Cloud")
            df_peak_neg = df_f[(df_f["sentiment"]=="negatif") &
                                (df_f["period"]==peak_neg["period"].date())]
            df_peak_pos = df_f[(df_f["sentiment"]=="positif") &
                                (df_f["period"]==peak_pos["period"].date())]
            top_n_w, _ = get_token_freq(df_peak_neg, None, 6) \
                if not df_peak_neg.empty else (pd.DataFrame(), 0)
            top_p_w, _ = get_token_freq(df_peak_pos, None, 6) \
                if not df_peak_pos.empty else (pd.DataFrame(), 0)
            an1, an2 = st.columns(2)
            with an1:
                kw = ", ".join(top_n_w["kata"].head(5).tolist()) if not top_n_w.empty else "-"
                st.error(
                    f"**Puncak Negatif** — {peak_neg['period'].strftime('%d %b %Y')}\n\n"
                    f"Jumlah: **{int(peak_neg['negatif']):,}** komentar\n\n"
                    f"Kata kunci: `{kw}`\n\n"
                    f"Kemungkinan penyebab: lonjakan reaksi publik terhadap isu pada tanggal tersebut."
                )
                if not df_peak_neg.empty:
                    with st.spinner("Membuat word cloud puncak negatif..."):
                        wc_neg_spike = get_spike_wordcloud_img(
                            df_peak_neg, "negatif", "#FFF1F2", "Puncak Negatif")
                    st.image(wc_neg_spike, use_container_width=True)
                    st.caption(
                        "Kata-kata yang paling banyak muncul di komentar negatif pada hari puncak. "
                        "Semakin besar hurufnya, semakin sering kata itu dipakai."
                    )
            with an2:
                kw2 = ", ".join(top_p_w["kata"].head(5).tolist()) if not top_p_w.empty else "-"
                st.success(
                    f"**Puncak Positif** — {peak_pos['period'].strftime('%d %b %Y')}\n\n"
                    f"Jumlah: **{int(peak_pos['positif']):,}** komentar\n\n"
                    f"Kata kunci: `{kw2}`"
                )
                if not df_peak_pos.empty:
                    with st.spinner("Membuat word cloud puncak positif..."):
                        wc_pos_spike = get_spike_wordcloud_img(
                            df_peak_pos, "positif", "#F0FDF4", "Puncak Positif")
                    st.image(wc_pos_spike, use_container_width=True)
                    st.caption(
                        "Kata-kata yang paling banyak muncul di komentar positif pada hari puncak."
                    )
            st.divider()

            # ── Tren Per Bulan (dedicated) ────────────────────────────────────
            st.markdown("#### Tren Komentar Per Bulan")
            df_full_dated = df_dated.copy()
            df_full_dated["bulan"] = df_full_dated["date"].dt.to_period("M").apply(
                lambda p: p.start_time.date() if hasattr(p, "start_time") else None)
            trend_monthly = (df_full_dated.groupby(["bulan","sentiment"])
                             .size().reset_index(name="count"))
            trend_monthly["bulan"] = pd.to_datetime(trend_monthly["bulan"])
            trend_monthly_wide = trend_monthly.pivot_table(
                index="bulan", columns="sentiment", values="count", fill_value=0
            ).reset_index().sort_values("bulan")
            for lbl in VALID_LABELS:
                if lbl not in trend_monthly_wide.columns:
                    trend_monthly_wide[lbl] = 0
            trend_monthly_wide["total"] = trend_monthly_wide[VALID_LABELS].sum(axis=1)
            trend_monthly_wide["label_bulan"] = trend_monthly_wide["bulan"].dt.strftime("%b %Y")

            # Grafik batang per bulan — jumlah absolut
            fig_monthly_bar = go.Figure()
            for lbl in ["positif","netral","negatif"]:
                fig_monthly_bar.add_trace(go.Bar(
                    x=trend_monthly_wide["label_bulan"],
                    y=trend_monthly_wide[lbl],
                    name=lbl.capitalize(),
                    marker_color=LABEL_COLORS[lbl],
                    text=trend_monthly_wide[lbl],
                    textposition="inside",
                    textfont=dict(size=10),
                ))
            fig_monthly_bar.update_layout(
                title="Jumlah Komentar per Bulan (Semua Sentimen)",
                barmode="stack",
                xaxis_title="Bulan",
                yaxis_title="Jumlah Komentar",
                height=420,
                margin=dict(t=55, b=15),
                legend=dict(orientation="h", y=1.06),
            )
            st.plotly_chart(fig_monthly_bar, use_container_width=True)
            st.caption(
                "Grafik batang ini menampilkan total komentar tiap bulan, dipisah berdasarkan sentimen. "
                "Bulan dengan bagian merah tinggi menandakan banyak komentar bernada negatif pada periode itu."
            )

            # Grafik garis per bulan — semua sentimen
            fig_monthly_line = go.Figure()
            for lbl, fc in [
                ("negatif","rgba(220,38,38,0.15)"),
                ("netral","rgba(37,99,235,0.12)"),
                ("positif","rgba(22,163,74,0.12)"),
            ]:
                fig_monthly_line.add_trace(go.Scatter(
                    x=trend_monthly_wide["label_bulan"],
                    y=trend_monthly_wide[lbl],
                    mode="lines+markers",
                    name=lbl.capitalize(),
                    line=dict(color=LABEL_COLORS[lbl], width=2.5),
                    marker=dict(size=8),
                    fill="tozeroy",
                    fillcolor=fc,
                ))
            if not trend_monthly_wide.empty:
                peak_m_neg_idx = trend_monthly_wide["negatif"].idxmax()
                peak_m_neg = trend_monthly_wide.loc[peak_m_neg_idx]
                fig_monthly_line.add_annotation(
                    x=peak_m_neg["label_bulan"],
                    y=peak_m_neg["negatif"],
                    text=f"Puncak Negatif<br>{int(peak_m_neg['negatif']):,}",
                    showarrow=True, arrowhead=2,
                    arrowcolor=LABEL_COLORS["negatif"],
                    font=dict(color=LABEL_COLORS["negatif"], size=11),
                    bgcolor="white", bordercolor=LABEL_COLORS["negatif"], ax=0, ay=-55,
                )
            fig_monthly_line.update_layout(
                title="Tren Sentimen per Bulan (Garis)",
                xaxis_title="Bulan",
                yaxis_title="Jumlah Komentar",
                height=420,
                margin=dict(t=55, b=15),
                legend=dict(orientation="h", y=1.06),
            )
            st.plotly_chart(fig_monthly_line, use_container_width=True)
            st.caption(
                "Grafik garis memudahkan melihat arah naik-turun sentimen dari bulan ke bulan. "
                "Titik merah yang melonjak tajam menandakan bulan dengan puncak komentar negatif terbanyak."
            )

            # Word cloud bulan puncak negatif
            if not trend_monthly_wide.empty:
                peak_month_label = peak_m_neg["label_bulan"]
                peak_month_date  = peak_m_neg["bulan"].date()
                df_peak_month = df_full_dated[
                    df_full_dated["date"].dt.to_period("M").apply(
                        lambda p: p.start_time.date() if hasattr(p, "start_time") else None
                    ) == peak_month_date
                ]
                df_peak_month_neg = df_peak_month[df_peak_month["sentiment"]=="negatif"]

                st.markdown(f"##### Word Cloud Penyebab Lonjakan — {peak_month_label}")
                wc_col1, wc_col2 = st.columns(2)
                with wc_col1:
                    if not df_peak_month_neg.empty:
                        with st.spinner(f"Membuat word cloud {peak_month_label}..."):
                            wc_month_neg = get_spike_wordcloud_img(
                                df_peak_month_neg, "negatif", "#FFF1F2", peak_month_label)
                        st.image(wc_month_neg, use_container_width=True)
                        top_m_neg, _ = get_token_freq(df_peak_month_neg, None, 5)
                        kw_m = ", ".join(top_m_neg["kata"].head(5).tolist()) if not top_m_neg.empty else "-"
                        st.error(
                            f"**{peak_month_label}** — Bulan komentar negatif terbanyak\n\n"
                            f"Jumlah negatif: **{int(peak_m_neg['negatif']):,}** komentar\n\n"
                            f"Kata yang mendominasi: `{kw_m}`"
                        )
                        st.caption(
                            "Word cloud ini menampilkan kata-kata yang paling sering muncul di komentar negatif "
                            "pada bulan puncak. Kata-kata inilah yang paling mencerminkan apa yang dikeluhkan netizen."
                        )
                with wc_col2:
                    if not df_peak_month.empty:
                        with st.spinner(f"Membuat word cloud semua sentimen {peak_month_label}..."):
                            wc_month_all = get_spike_wordcloud_img(
                                df_peak_month, None, "#F8FAFC", peak_month_label)
                        st.image(wc_month_all, use_container_width=True)
                        st.info(
                            f"**Semua Sentimen — {peak_month_label}**\n\n"
                            f"Total komentar bulan ini: **{int(peak_m_neg['total']):,}**"
                        )
                        st.caption(
                            "Word cloud semua komentar (tanpa filter sentimen) di bulan yang sama. "
                            "Berguna untuk melihat topik apa yang paling ramai dibicarakan secara keseluruhan."
                        )

            st.divider()

            # ── Area stacked ──────────────────────────────────────────────────
            st.markdown("#### Volume Komentar Semua Sentimen (Stacked)")
            fig_area = go.Figure()
            for lbl, fc in [("negatif","rgba(220,38,38,0.55)"),
                             ("netral", "rgba(37,99,235,0.45)"),
                             ("positif","rgba(22,163,74,0.50)")]:
                fig_area.add_trace(go.Scatter(
                    x=trend_wide["period"], y=trend_wide[lbl],
                    mode="lines", name=lbl.capitalize(),
                    line=dict(color=LABEL_COLORS[lbl], width=1.5),
                    stackgroup="one", fillcolor=fc,
                ))
            fig_area.update_layout(title=f"Volume Komentar Stacked ({gran})",
                                    xaxis_title="Tanggal", yaxis_title="Jumlah Komentar",
                                    height=420, margin=dict(t=55,b=15),
                                    legend=dict(orientation="h", y=1.06))
            st.plotly_chart(fig_area, use_container_width=True)
            st.caption(
                "Area stacked menunjukkan proporsi setiap sentimen dalam total komentar. "
                "Ketika area merah mendominasi, artinya komentar negatif lebih banyak dari yang lain pada periode itu."
            )
            st.divider()

            # ── Rasio negatif ─────────────────────────────────────────────────
            st.markdown("#### Rasio Sentimen Negatif per Periode")
            trend_wide["total"]     = trend_wide[VALID_LABELS].sum(axis=1)
            trend_wide["rasio_neg"] = (
                trend_wide["negatif"] / trend_wide["total"].replace(0,np.nan) * 100
            ).round(1).fillna(0)
            threshold = 60.0
            fig_ratio = go.Figure(go.Bar(
                x=trend_wide["period"], y=trend_wide["rasio_neg"],
                marker_color=[LABEL_COLORS["negatif"] if v >= threshold else "#94A3B8"
                              for v in trend_wide["rasio_neg"]],
            ))
            fig_ratio.add_hline(y=threshold, line_dash="dash", line_color="#D97706",
                                annotation_text=f"Ambang kritis {threshold:.0f}%",
                                annotation_position="top right")
            fig_ratio.update_layout(
                title=f"Rasio Sentimen Negatif ({gran}) — merah di atas {threshold:.0f}%",
                xaxis_title="Tanggal", yaxis_title="% Negatif",
                yaxis=dict(range=[0,105]),
                height=380, margin=dict(t=55,b=15))
            st.plotly_chart(fig_ratio, use_container_width=True)
            st.caption(
                "Grafik ini menunjukkan berapa persen komentar yang bernada negatif di tiap periode. "
                "Bar berwarna merah berarti lebih dari 60% komentar pada periode itu bernada negatif — perlu perhatian lebih."
            )
            st.divider()

            # ── Tabel ─────────────────────────────────────────────────────────
            st.markdown("#### Tabel Data Tren")
            disp_t = trend_wide.copy()
            disp_t["period"] = disp_t["period"].dt.strftime("%d %b %Y")
            disp_t = disp_t.rename(columns={
                "period":"Periode","positif":"Positif","netral":"Netral",
                "negatif":"Negatif","total":"Total","rasio_neg":"% Negatif"})
            st.dataframe(
                disp_t[["Periode","Positif","Netral","Negatif","Total","% Negatif"]]
                    .sort_values("Periode", ascending=False)
                    .style.background_gradient(subset=["% Negatif"], cmap="Reds"),
                use_container_width=True, hide_index=True, height=350,
            )
            st.caption(
                "Tabel lengkap data tren. Klik header kolom untuk mengurutkan. "
                "Warna merah pada kolom % Negatif semakin gelap berarti semakin tinggi proporsi komentar negatif."
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FREKUENSI KATA
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Frekuensi Kata Bermakna")
    st.caption("Kata sambung, kata hubung, dan kata tidak bermakna telah dihapus.")

    c_sel, c_info = st.columns([2,3])
    with c_sel:
        sel_lbl = st.selectbox("Sentimen:", ["Semua"]+VALID_LABELS, key="t3_lbl")
    lbl_key = None if sel_lbl == "Semua" else sel_lbl
    freq_df, total_tok = get_token_freq(df, lbl_key, top_n_words)

    if not freq_df.empty:
        bar_c = LABEL_COLORS.get(lbl_key, "#2563EB") if lbl_key else "#2563EB"

        # Bar vertikal frekuensi
        fig = go.Figure(go.Bar(
            x=freq_df["kata"], y=freq_df["frekuensi"],
            marker_color=bar_c,
            text=freq_df["frekuensi"], textposition="outside",
            customdata=freq_df["persen"].values,
            hovertemplate="<b>%{x}</b><br>Frekuensi: %{y:,}<br>%{customdata:.2f}%<extra></extra>",
        ))
        fig.update_layout(title=f"Top {top_n_words} Kata — {sel_lbl}",
                          xaxis_tickangle=-35, yaxis_title="Frekuensi",
                          yaxis=dict(range=[0, freq_df["frekuensi"].max()*1.22]),
                          height=450, margin=dict(t=55,b=85))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Grafik batang menampilkan kata-kata yang paling sering muncul. "
            "Angka di atas batang adalah jumlah kemunculan kata tersebut di komentar."
        )
        st.divider()

        # Horizontal bar dengan persentase
        fig2 = go.Figure(go.Bar(
            y=freq_df["kata"][::-1], x=freq_df["persen"][::-1],
            orientation="h",
            marker=dict(color=freq_df["persen"][::-1],
                        colorscale=[[0,"#DBEAFE"],[1,"#1D4ED8"]], showscale=True,
                        colorbar=dict(title="%")),
            text=freq_df["persen"].apply(lambda v: f"{v:.2f}%")[::-1],
            textposition="outside",
        ))
        fig2.update_layout(title=f"Persentase Kata dari Total Token — {sel_lbl}",
                           xaxis_title="Persentase (%)",
                           height=max(380, top_n_words*22),
                           margin=dict(t=55,b=15,l=110))
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "Grafik horizontal ini menunjukkan seberapa besar kontribusi setiap kata dari total kata yang ada. "
            "Warna semakin gelap berarti kata itu semakin dominan."
        )
        st.divider()

        # Perbandingan kata per sentimen
        st.markdown("#### Perbandingan Kata Menonjol per Sentimen")
        cols3 = st.columns(3)
        for i, lbl in enumerate(VALID_LABELS):
            f, _ = get_token_freq(df, lbl, 12)
            with cols3[i]:
                if not f.empty:
                    fig_s = go.Figure(go.Bar(
                        y=f["kata"][::-1], x=f["frekuensi"][::-1],
                        orientation="h",
                        marker_color=LABEL_COLORS[lbl],
                        text=f["persen"].apply(lambda v: f"{v:.1f}%")[::-1],
                        textposition="outside",
                    ))
                    fig_s.update_layout(title=f"{lbl.capitalize()}",
                                        height=420, margin=dict(t=50,b=10,l=100))
                    st.plotly_chart(fig_s, use_container_width=True)
        st.caption(
            "Perbandingan ini membantu kita lihat kata apa yang sering muncul di setiap kategori sentimen. "
            "Misal: kata 'semoga', 'dukungan' lebih banyak di positif, sedangkan 'bahaya', 'tolak' di negatif."
        )
        st.divider()

        # Kata eksklusif per sentimen (dominance score)
        st.markdown("#### Kata Khas per Sentimen")
        st.caption("Kata yang proporsinya jauh lebih tinggi di satu sentimen dibanding rata-rata keseluruhan.")
        all_freq, _ = get_token_freq(df, None, 300)
        all_dict = all_freq.set_index("kata")["persen"].to_dict()
        dom_cols = st.columns(3)
        for i, lbl in enumerate(VALID_LABELS):
            lbl_freq, _ = get_token_freq(df, lbl, 200)
            if lbl_freq.empty:
                continue
            lbl_dict = lbl_freq.set_index("kata")["persen"].to_dict()
            dominance = [(w, lbl_dict[w] - all_dict.get(w,0)) for w in lbl_dict]
            dominance = sorted(dominance, key=lambda x: x[1], reverse=True)[:12]
            dom_df = pd.DataFrame(dominance, columns=["kata","dominance"])
            with dom_cols[i]:
                fig_d = go.Figure(go.Bar(
                    y=dom_df["kata"][::-1], x=dom_df["dominance"][::-1],
                    orientation="h", marker_color=LABEL_COLORS[lbl],
                    text=dom_df["dominance"].apply(lambda v: f"+{v:.2f}%")[::-1],
                    textposition="outside",
                ))
                fig_d.update_layout(title=f"Khas: {lbl.capitalize()}",
                                    xaxis_title="Dominance (%)",
                                    height=420, margin=dict(t=50,b=10,l=100))
                st.plotly_chart(fig_d, use_container_width=True)
        st.caption(
            "Grafik ini menampilkan kata yang paling 'khas' per sentimen — "
            "yaitu kata yang proporsinya jauh lebih tinggi dibanding rata-rata. "
            "Semakin panjang batangnya, semakin unik kata itu untuk sentimen tersebut."
        )
        st.divider()

        # Tabel
        st.markdown("#### Tabel Frekuensi Lengkap")
        disp = freq_df.copy()
        disp.columns = ["Kata","Frekuensi","Persentase (%)"]
        disp["Kumulatif (%)"] = disp["Persentase (%)"].cumsum().round(2)
        st.dataframe(
            disp.style.background_gradient(subset=["Frekuensi"], cmap="Blues")
                      .format({"Persentase (%)":"{:.2f}%","Kumulatif (%)":"{:.2f}%"}),
            use_container_width=True, hide_index=True, height=380,
        )
        st.caption(f"Top 10 kata menyumbang {disp['Persentase (%)'].head(10).sum():.1f}% dari total token.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — N-GRAM & WORD CLOUD
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Analisis N-Gram dan Word Cloud")

    # N-gram
    ng1, ng2 = st.columns([1,2])
    with ng1:
        sel_n_type = st.radio("Tipe:", [("Bigram",2),("Trigram",3)],
                              format_func=lambda x: x[0], key="ng_type")
        n_val = sel_n_type[1]
        sel_ng_lbl = st.selectbox("Sentimen:", ["Semua"]+VALID_LABELS, key="ng_lbl")
        ng_lbl = None if sel_ng_lbl == "Semua" else sel_ng_lbl
    with ng2:
        ng_df, ng_total = get_ngram_freq(df, ng_lbl, n_val, top_n_ngram)
        if not ng_df.empty:
            fig_ng = go.Figure(go.Bar(
                y=ng_df["ngram"][::-1], x=ng_df["frekuensi"][::-1],
                orientation="h",
                marker=dict(color=ng_df["persen"][::-1],
                            colorscale=[[0,"#F3E8FF"],[1,"#7C3AED"]], showscale=True),
                text=ng_df["persen"].apply(lambda v: f"{v:.2f}%")[::-1],
                textposition="outside",
            ))
            fig_ng.update_layout(
                title=f"Top {top_n_ngram} {sel_n_type[0]} — {sel_ng_lbl}",
                xaxis_title="Frekuensi",
                height=max(400, top_n_ngram*28),
                margin=dict(t=55,b=15,l=160),
            )
            st.plotly_chart(fig_ng, use_container_width=True)
            st.caption(
                "N-gram adalah kombinasi dua atau tiga kata yang sering muncul bersamaan. "
                "Ini membantu memahami konteks kalimat, bukan hanya kata tunggal."
            )

    st.divider()

    # N-gram per sentimen side by side
    st.markdown(f"#### Perbandingan {sel_n_type[0]} per Sentimen")
    ng_cols = st.columns(3)
    for i, lbl in enumerate(VALID_LABELS):
        ng_s, _ = get_ngram_freq(df, lbl, n_val, 10)
        with ng_cols[i]:
            if not ng_s.empty:
                fig_ns = go.Figure(go.Bar(
                    y=ng_s["ngram"][::-1], x=ng_s["frekuensi"][::-1],
                    orientation="h", marker_color=LABEL_COLORS[lbl],
                    text=ng_s["frekuensi"][::-1], textposition="outside",
                ))
                fig_ns.update_layout(title=f"{lbl.capitalize()}",
                                     height=380, margin=dict(t=50,b=10,l=140))
                st.plotly_chart(fig_ns, use_container_width=True)
    st.caption(
        "Perbandingan frasa yang sering muncul di setiap sentimen. "
        "Frasa seperti 'tentara masuk sipil' lebih sering di negatif, sedangkan frasa lain bisa lebih banyak di positif."
    )
    st.divider()

    # Word cloud
    st.markdown("#### Word Cloud per Sentimen")
    wc_subtabs = st.tabs(["Positif","Netral","Negatif","Semua Label"])
    wc_cfg = [("positif","Positif","#F0FDF4"),("netral","Netral","#EFF6FF"),
              ("negatif","Negatif","#FFF1F2"),(None,"Semua Label","#F8FAFC")]
    for wc_tab, (lbl,name,bg) in zip(wc_subtabs, wc_cfg):
        with wc_tab:
            n_docs = len(df) if lbl is None else int((df["sentiment"]==lbl).sum())
            st.caption(f"{name} — {n_docs:,} komentar")
            with st.spinner(f"Membuat word cloud {name}..."):
                img = get_wordcloud_img(df, lbl, bg)
            st.image(img, use_container_width=True)
            st.caption(
                "Kata yang lebih besar dan tebal berarti lebih sering muncul di komentar. "
                "Word cloud memudahkan pembacaan topik utama secara visual sekaligus."
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — INSIGHT PER VIDEO
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Insight per Video")

    # Distribusi sentimen per video
    gdf = df.groupby(["video_short","sentiment"]).size().reset_index(name="n")
    tot_vid = gdf.groupby("video_short")["n"].transform("sum")
    gdf["pct"] = (gdf["n"] / tot_vid * 100).round(1)

    v1, v2 = st.columns(2)
    with v1:
        fig = px.bar(gdf, x="video_short", y="n", color="sentiment",
                     color_discrete_map=LABEL_COLORS, barmode="stack",
                     title="Jumlah Komentar per Video",
                     labels={"video_short":"Video","n":"Jumlah"},
                     text="n")
        fig.update_layout(height=450, margin=dict(t=55,b=150), xaxis_tickangle=-25,
                          legend=dict(orientation="h", y=1.06))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Setiap batang mewakili satu video. Bagian warna menunjukkan proporsi setiap sentimen. "
            "Video dengan bagian merah besar artinya banyak komentar negatif di sana."
        )
    with v2:
        # Pie chart per video — satu pie per video menggunakan subplot
        from plotly.subplots import make_subplots

        video_list = gdf["video_short"].unique().tolist()
        n_vids = len(video_list)
        cols_per_row = min(n_vids, 3)
        n_rows = -(-n_vids // cols_per_row)  # ceiling division

        fig_pie = make_subplots(
            rows=n_rows, cols=cols_per_row,
            specs=[[{"type": "pie"}] * cols_per_row for _ in range(n_rows)],
            subplot_titles=video_list,
        )

        for idx, vid in enumerate(video_list):
            row = idx // cols_per_row + 1
            col = idx % cols_per_row + 1
            sub = gdf[gdf["video_short"] == vid].sort_values("sentiment")
            fig_pie.add_trace(
                go.Pie(
                    labels=sub["sentiment"],
                    values=sub["pct"],
                    marker_colors=[LABEL_COLORS.get(l, "#aaa") for l in sub["sentiment"]],
                    hole=0.38,
                    textinfo="percent",
                    textfont_size=12,
                    hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
                    showlegend=(idx == 0),
                ),
                row=row, col=col,
            )

        fig_pie.update_layout(
            title="Proporsi Sentimen per Video (%)",
            height=320 * n_rows,
            margin=dict(t=60, b=20, l=20, r=20),
            legend=dict(orientation="h", y=-0.08,
                        font=dict(size=12, color="#1E293B")),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption(
            "Setiap lingkaran mewakili satu video. Warna merah = negatif, hijau = positif, biru = netral. "
            "Video dengan porsi merah besar berarti lebih banyak menuai komentar negatif."
        )

    st.divider()

    # Tabel metrik per video
    st.markdown("#### Metrik Lengkap per Video")
    vid_stats = []
    for vid_id, vid_title in VIDEO_TITLES.items():
        sub = df[df["video_id"] == vid_id]
        if sub.empty:
            continue
        n_tot = len(sub)
        vid_stats.append({
            "Judul Video":   vid_title,
            "Total":         n_tot,
            "Positif":       int((sub["sentiment"]=="positif").sum()),
            "Netral":        int((sub["sentiment"]=="netral").sum()),
            "Negatif":       int((sub["sentiment"]=="negatif").sum()),
            "% Negatif":     round((sub["sentiment"]=="negatif").sum()/n_tot*100, 1),
            "% Positif":     round((sub["sentiment"]=="positif").sum()/n_tot*100, 1),
            "Total Like":    int(sub["like_count"].sum()),
            "Rata Like":     round(sub["like_count"].mean(), 1),
        })
    if vid_stats:
        vs_df = pd.DataFrame(vid_stats).sort_values("% Negatif", ascending=False)
        st.dataframe(
            vs_df.style.background_gradient(subset=["% Negatif"], cmap="Reds")
                       .background_gradient(subset=["% Positif"], cmap="Greens"),
            use_container_width=True, hide_index=True,
        )
        st.caption(
            "Tabel ini merangkum metrik utama tiap video. "
            "Video dengan % Negatif tinggi (merah gelap) paling banyak memicu reaksi negatif dari penonton."
        )

    st.divider()

    # Kata khas per video (top 10 kata bermakna)
    st.markdown("#### Kata Paling Sering per Video")
    vid_ids = df["video_id"].unique().tolist()
    n_vids = len(vid_ids)
    vid_cols = st.columns(min(n_vids, 3))
    for i, vid_id in enumerate(vid_ids[:6]):
        sub_vid = df[df["video_id"]==vid_id]
        vf, _ = get_token_freq(sub_vid, None, 10)
        title_short = VIDEO_TITLES.get(vid_id, vid_id)[:35]
        with vid_cols[i % 3]:
            if not vf.empty:
                fig_v = go.Figure(go.Bar(
                    y=vf["kata"][::-1], x=vf["frekuensi"][::-1],
                    orientation="h",
                    marker=dict(color=vf["frekuensi"][::-1],
                                colorscale=[[0,"#E0F2FE"],[1,"#0284C7"]], showscale=False),
                    text=vf["persen"].apply(lambda v: f"{v:.1f}%")[::-1],
                    textposition="outside",
                ))
                fig_v.update_layout(title=title_short,
                                    height=360, margin=dict(t=50,b=10,l=100))
                st.plotly_chart(fig_v, use_container_width=True)
    st.caption(
        "Masing-masing video punya topik kata yang dominan di komentarnya. "
        "Ini membantu menangkap fokus utama diskusi per video — misalnya kata 'tni', 'sipil', 'bahaya', dll."
    )
