from __future__ import annotations

import math
import os
from datetime import date, datetime
from pathlib import Path
import html
import re
import unicodedata
from typing import Iterable, Optional

from pymongo import MongoClient
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lower, regexp_replace, trim, udf
from pyspark.sql.types import StringType

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from mongo_comments_loader import (
    create_spark_session,
    load_comments_spark_df,
    load_project_env,
)


STOPWORDS_ID = {
    "ada",
    "adalah",
    "agar",
    "akan",
    "akhir",
    "antara",
    "apa",
    "apabila",
    "atau",
    "bagai",
    "bagaimana",
    "bagi",
    "bahwa",
    "dalam",
    "dan",
    "dari",
    "dengan",
    "demi",
    "di",
    "dia",
    "hal",
    "ini",
    "itu",
    "jadi",
    "juga",
    "kami",
    "kamu",
    "kan",
    "karena",
    "ke",
    "kemudian",
    "kita",
    "lagi",
    "maka",
    "mereka",
    "nya",
    "oleh",
    "pada",
    "para",
    "saat",
    "saja",
    "saling",
    "sama",
    "saya",
    "sebagai",
    "sebab",
    "secara",
    "sedang",
    "sehingga",
    "seperti",
    "serta",
    "setelah",
    "sudah",
    "tanpa",
    "telah",
    "tentang",
    "tersebut",
    "tetapi",
    "untuk",
    "yang",
}

NEGATIONS = {"tidak", "bukan", "jangan", "belum", "tak", "kurang"}

SLANG_MAP = {
    "aja": "saja",
    "ama": "sama",
    "banget": "sangat",
    "bgt": "sangat",
    "bkn": "bukan",
    "blm": "belum",
    "br": "baru",
    "buat": "untuk",
    "cm": "cuma",
    "cuma": "hanya",
    "dah": "sudah",
    "dg": "dengan",
    "dgn": "dengan",
    "dl": "dulu",
    "dlm": "dalam",
    "dr": "dari",
    "emg": "memang",
    "ga": "tidak",
    "gak": "tidak",
    "gk": "tidak",
    "gw": "saya",
    "gue": "saya",
    "jd": "jadi",
    "jg": "juga",
    "kalo": "kalau",
    "karna": "karena",
    "kek": "seperti",
    "kpd": "kepada",
    "krn": "karena",
    "lo": "kamu",
    "lu": "kamu",
    "ma": "sama",
    "msh": "masih",
    "ngga": "tidak",
    "nggak": "tidak",
    "org": "orang",
    "pd": "pada",
    "pemerentah": "pemerintah",
    "pemerentahan": "pemerintahan",
    "pengen": "ingin",
    "sm": "sama",
    "sma": "sama",
    "tdk": "tidak",
    "tp": "tapi",
    "trs": "terus",
    "udh": "sudah",
    "utk": "untuk",
    "yg": "yang",
}

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
HTML_ENTITY_RE = re.compile(r"&[a-z]+;|&#\d+;", re.IGNORECASE)
NON_TEXT_RE = re.compile(r"[^0-9a-zA-Z_\'\-\s]")
REPEATED_CHAR_RE = re.compile(r"([a-zA-Z])\1{2,}")
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\'-]*")
EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]")

factory = StemmerFactory()
stemmer = factory.create_stemmer()


TEXT_CANDIDATES: tuple[str, ...] = (
    "text_original",
    "text",
    "textDisplay",
    "comment_text",
)

ESSENTIAL_METADATA_COLUMNS: tuple[str, ...] = (
    "comment_id",
    "video_id",
    "author_channel_id",
    "author",
    "published_at",
    "updated_at",
    "like_count",
    "total_reply_count",
)


def _prompt_positive_int(prompt: str, default: int) -> int:
    while True:
        try:
            raw_value = input(f"{prompt} [{default}]: ").strip()
        except EOFError:
            return default

        if not raw_value:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            print("Input harus berupa angka bulat positif.", flush=True)
            continue

        if value > 0:
            return value

        print("Input harus lebih besar dari 0.", flush=True)


def _prompt_memory(prompt: str, default: str) -> str:
    pattern = re.compile(r"^\d+[kmgKMG]$")

    while True:
        try:
            raw_value = input(f"{prompt} [{default}]: ").strip()
        except EOFError:
            return default

        if not raw_value:
            return default

        if pattern.fullmatch(raw_value):
            return raw_value.lower()

        print("Input memory harus format Spark, contoh: 2g, 4096m.", flush=True)


def prompt_spark_resources() -> tuple[int, str]:
    default_total_cores = int(os.getenv("SPARK_CORES", os.getenv("SPARK_NUM_PARTITIONS", "4")))
    default_memory = os.getenv(
        "SPARK_MEMORY",
        os.getenv("SPARK_EXECUTOR_MEMORY", "2g"),
    ).strip()
    spark_master = os.getenv("SPARK_MASTER", "local[*]").strip()

    print("Masukkan resource Spark untuk preprocessing.", flush=True)
    print(f"Target Spark master: {spark_master}", flush=True)
    total_cores = _prompt_positive_int("Total core aplikasi", default=default_total_cores)
    memory = _prompt_memory("Memory per executor/driver", default=default_memory)
    return total_cores, memory


def resolve_text_column(df: DataFrame, candidates: Iterable[str] = TEXT_CANDIDATES) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    raise ValueError(
        "Kolom teks tidak ditemukan. Coba set SPARK_TEXT_COLUMN atau sesuaikan nama field."
    )


def _essential_columns(df: DataFrame) -> list[str]:
    return [name for name in ESSENTIAL_METADATA_COLUMNS if name in df.columns]


def normalize_unicode(text: str) -> str:
    text = html.unescape(text or "")
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\u200b", " ").replace("\ufeff", " ")


def reduce_repeated_chars(token: str, max_repeat: int = 2) -> str:
    return REPEATED_CHAR_RE.sub(lambda match: match.group(1) * max_repeat, token)


def normalize_token(token: str) -> str:
    token = reduce_repeated_chars(token.casefold())
    return SLANG_MAP.get(token, token)


def looks_like_tail_noise(token: str) -> bool:
    if len(token) < 5 or len(token) > 10:
        return False
    if any(char.isdigit() for char in token):
        return True
    letters = [char for char in token if char.isalpha()]
    if len(letters) != len(token):
        return False
    return not any(char in "aiueo" for char in token)


def tokenize_comment(text: str) -> list[str]:
    text = normalize_unicode(text)
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HASHTAG_RE.sub(r" \1 ", text)
    text = HTML_ENTITY_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = NON_TEXT_RE.sub(" ", text)

    tokens = [normalize_token(match.group(0)) for match in TOKEN_RE.finditer(text)]
    while tokens and looks_like_tail_noise(tokens[-1]):
        tokens.pop()
    return tokens
def remove_stopwords(tokens: Iterable[str]) -> list[str]:
    return [
        token
        for token in tokens
        if len(token) > 1 and (token not in STOPWORDS_ID or token in NEGATIONS)
    ]


def clean_text(text: str) -> str:
    return " ".join(tokenize_comment(text))


def normalize_without_stem(text: str) -> str:
    return " ".join(remove_stopwords(tokenize_comment(text)))


def normalize_and_stem(text: str) -> str:
    tokens = remove_stopwords(tokenize_comment(text))
    stemmed = [stemmer.stem(token) for token in tokens]
    return " ".join(token for token in stemmed if token)


@udf(returnType=StringType())
def clean_text_udf(text: Optional[str]) -> str:
    return clean_text(text or "")


@udf(returnType=StringType())
def normalize_without_stem_udf(text: Optional[str]) -> str:
    return normalize_without_stem(text or "")


@udf(returnType=StringType())
def normalize_and_stem_udf(text: Optional[str]) -> str:
    return normalize_and_stem(text or "")


def _sanitize_for_mongo(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (str, bool, int, datetime, date)):
        return value
    if hasattr(value, "item") and callable(value.item):
        try:
            return _sanitize_for_mongo(value.item())
        except Exception:
            pass
    if isinstance(value, dict):
        return {key: _sanitize_for_mongo(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_mongo(item) for item in value]
    return str(value)


def _resolve_source_text(document: dict, source_col: str) -> str:
    candidate = document.get(source_col)
    if candidate is None:
        candidate = document.get("text_original") or document.get("text") or ""
    return str(candidate).strip()


def preprocess_comment_document(
    document: dict,
    source_col: str,
    seen_comment_ids: Optional[set[str]] = None,
) -> Optional[dict]:
    comment_id = str(document.get("comment_id") or "")
    if seen_comment_ids is not None and comment_id:
        if comment_id in seen_comment_ids:
            return None
        seen_comment_ids.add(comment_id)

    text_original = _resolve_source_text(document, source_col)
    if not text_original:
        return None

    text_clean = clean_text(text_original)
    text_preprocessed = normalize_without_stem(text_original)
    text_stemmed = normalize_and_stem(text_original)

    if not text_preprocessed:
        return None

    processed_document: dict[str, object] = {}
    for column_name in ESSENTIAL_METADATA_COLUMNS:
        if column_name in document:
            processed_document[column_name] = _sanitize_for_mongo(document.get(column_name))

    processed_document["text_original"] = text_original
    processed_document["text_clean"] = text_clean
    processed_document["text_preprocessed"] = text_preprocessed
    processed_document["text_stemmed"] = text_stemmed
    return processed_document


def iter_preprocessed_documents(df: DataFrame, source_col: str) -> Iterable[dict]:
    seen_comment_ids: set[str] = set()
    for row in df.toLocalIterator():
        document = _sanitize_for_mongo(row.asDict(recursive=True))
        processed_document = preprocess_comment_document(
            document,
            source_col=source_col,
            seen_comment_ids=seen_comment_ids,
        )
        if processed_document is not None:
            yield processed_document


def preprocess_comments_df(
    df: DataFrame,
    source_col: Optional[str] = None,
) -> DataFrame:
    source_col = source_col or resolve_text_column(df)

    selected = df.select(
        *_essential_columns(df),
        col(source_col).cast("string").alias("text_original"),
    )

    cleaned = (
        selected.withColumn("text_original", trim(col("text_original")))
        .withColumn("text_clean", clean_text_udf(col("text_original")))
        .withColumn("text_preprocessed", normalize_without_stem_udf(col("text_original")))
        .withColumn("text_stemmed", normalize_and_stem_udf(col("text_original")))
        .withColumn(
            "text_original",
            regexp_replace(col("text_original"), r"\s+", " "),
        )
    )

    processed = cleaned.filter(col("text_original").isNotNull() & (col("text_original") != ""))
    processed = processed.filter(
        col("text_preprocessed").isNotNull() & (col("text_preprocessed") != "")
    )

    if "comment_id" in processed.columns:
        processed = processed.dropDuplicates(["comment_id"])

    return processed.select(
        *[name for name in ESSENTIAL_METADATA_COLUMNS if name in processed.columns],
        "text_original",
        "text_clean",
        "text_preprocessed",
        "text_stemmed",
    )


def save_processed_comments_to_mongo(
    df: DataFrame,
    mongo_uri: str,
    mongo_db: str,
    mongo_collection: str,
    batch_size: int = 1000,
) -> int:
    if not mongo_uri or not mongo_db or not mongo_collection:
        raise ValueError("Konfigurasi MongoDB untuk output preprocessing belum lengkap")

    cached_df = df.cache()
    processed_rows = cached_df.count()
    if processed_rows == 0:
        cached_df.unpersist()
        raise ValueError("Tidak ada data yang lolos preprocessing untuk disimpan ke MongoDB")

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        client[mongo_db][mongo_collection].delete_many({})

    inserted_count = 0

    def insert_partition(rows) -> None:
        batch: list[dict] = []
        with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
            collection = client[mongo_db][mongo_collection]
            for row in rows:
                document = _sanitize_for_mongo(row.asDict(recursive=True))
                document.pop("_id", None)
                batch.append(document)

                if len(batch) >= batch_size:
                    collection.insert_many(batch, ordered=False)
                    batch.clear()

            if batch:
                collection.insert_many(batch, ordered=False)

    cached_df.foreachPartition(insert_partition)
    inserted_count = processed_rows

    cached_df.unpersist()
    return inserted_count


def save_processed_comments_to_mongo_serial(
    df: DataFrame,
    mongo_uri: str,
    mongo_db: str,
    mongo_collection: str,
    batch_size: int = 1000,
) -> int:
    if not mongo_uri or not mongo_db or not mongo_collection:
        raise ValueError("Konfigurasi MongoDB untuk output preprocessing belum lengkap")

    inserted_count = 0
    batch: list[dict] = []

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        collection = client[mongo_db][mongo_collection]
        for row in df.toLocalIterator():
            document = _sanitize_for_mongo(row.asDict(recursive=True))
            document.pop("_id", None)
            batch.append(document)

            if len(batch) >= batch_size:
                result = collection.insert_many(batch, ordered=False)
                inserted_count += len(result.inserted_ids)
                batch.clear()

        if batch:
            result = collection.insert_many(batch, ordered=False)
            inserted_count += len(result.inserted_ids)

    return inserted_count


def preprocess_and_save_comments_to_mongo(
    df: DataFrame,
    source_col: str,
    mongo_uri: str,
    mongo_db: str,
    mongo_collection: str,
    batch_size: int = 200,
) -> tuple[int, int]:
    if not mongo_uri or not mongo_db or not mongo_collection:
        raise ValueError("Konfigurasi MongoDB untuk output preprocessing belum lengkap")

    inserted_count = 0
    processed_count = 0
    batch: list[dict] = []

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        client[mongo_db][mongo_collection].delete_many({})
        collection = client[mongo_db][mongo_collection]

        for document in iter_preprocessed_documents(df, source_col=source_col):
            processed_count += 1
            batch.append(document)

            if len(batch) >= batch_size:
                result = collection.insert_many(batch, ordered=False)
                inserted_count += len(result.inserted_ids)
                batch.clear()

        if batch:
            result = collection.insert_many(batch, ordered=False)
            inserted_count += len(result.inserted_ids)

    return processed_count, inserted_count


def main() -> None:
    load_project_env()
    spark_cores, spark_memory = prompt_spark_resources()
    spark = create_spark_session(
        app_name="mongo-comments-preprocess",
        cores=spark_cores,
        memory=spark_memory,
    )
    source_col = os.getenv("SPARK_TEXT_COLUMN")
    num_partitions = int(os.getenv("SPARK_NUM_PARTITIONS", "4"))
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    mongo_db = os.getenv("MONGO_DB", "").strip()
    processed_collection = os.getenv(
        "MONGO_PROCESSED_COLLECTION",
        os.getenv("MONGO_COLLECTION_PROCESSED", "comments_processed"),
    ).strip()

    print(
        "Spark session aktif: "
        f"app_id={spark.sparkContext.applicationId}, "
        f"master={spark.sparkContext.master}, "
        f"total_cores={spark_cores}, "
        f"executor_memory={spark_memory}, "
        f"ui={spark.sparkContext.uiWebUrl or 'tidak tersedia'}",
        flush=True,
    )
    print(
        "Konfigurasi Mongo output: "
        f"{mongo_db}.{processed_collection}",
        flush=True,
    )

    effective_partitions = max(num_partitions, spark_cores * 2)
    raw_df = load_comments_spark_df(spark).repartition(effective_partitions)
    resolved_source_col = source_col or resolve_text_column(raw_df)

    total_rows = raw_df.count()
    if total_rows == 0:
        raise ValueError(
            "Hasil preprocessing kosong. Cek SPARK_TEXT_COLUMN dan isi collection komentar sumber."
        )

    print(
        f"Data sumber terbaca: {total_rows} baris, kolom teks={resolved_source_col}",
        flush=True,
    )

    processed_df = preprocess_comments_df(raw_df, source_col=resolved_source_col).repartition(
        effective_partitions
    )

    preview_rows = [row.asDict(recursive=True) for row in processed_df.limit(5).collect()]
    if preview_rows:
        print("Preview hasil preprocessing:")
        for preview_row in preview_rows:
            print(
                f"- {preview_row.get('comment_id', '')} | {preview_row.get('video_id', '')} | {preview_row.get('text_preprocessed', '')[:160]}"
            )

    insert_batch_size = int(os.getenv("MONGO_INSERT_BATCH_SIZE", "200"))

    inserted_count = save_processed_comments_to_mongo(
        processed_df,
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        mongo_collection=processed_collection,
        batch_size=insert_batch_size,
    )
    processed_count = inserted_count
    print(
        "Data hasil preprocessing disimpan ke MongoDB: "
        f"{mongo_db}.{processed_collection} "
        f"(total: {total_rows}, lolos preprocessing: {processed_count}, dokumen tersimpan: {inserted_count})"
    )

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        final_count = client[mongo_db][processed_collection].count_documents({})
    print(f"Dokumen di koleksi target setelah insert: {final_count}")


if __name__ == "__main__":
    main()
