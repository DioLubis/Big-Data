from __future__ import annotations

import math
import os
import re
from datetime import date, datetime
from typing import Iterable, Optional

from pymongo import MongoClient
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, regexp_replace, trim, udf
from pyspark.sql.types import StringType

from mongo_comments_loader import (
    create_spark_session,
    load_comments_spark_df,
    load_project_env,
)
from preprocess import normalize_without_stem


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


def preprocess_text(text: str) -> str:
    return normalize_without_stem(text or "")


preprocess_text_udf = udf(preprocess_text, StringType())


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
        .withColumn(
            "text_original",
            regexp_replace(col("text_original"), r"\s+", " "),
        )
        .withColumn("text_preprocessed", preprocess_text_udf(col("text_original")))
    )

    processed = cleaned.filter(col("text_original").isNotNull() & (col("text_original") != ""))
    processed = processed.filter(
        col("text_preprocessed").isNotNull() & (col("text_preprocessed") != "")
    )

    if "comment_id" in processed.columns:
        processed = processed.dropDuplicates(["comment_id"])

    return processed.select(
        *[name for name in ESSENTIAL_METADATA_COLUMNS if name in processed.columns],
        "text_preprocessed",
    )


def save_processed_comments_to_mongo(
    df: DataFrame,
    mongo_uri: str,
    mongo_db: str,
    mongo_collection: str,
    batch_size: int = 200,
) -> tuple[int, int]:
    if not mongo_uri or not mongo_db or not mongo_collection:
        raise ValueError("Konfigurasi MongoDB untuk output preprocessing belum lengkap")

    cached_df = df.cache()
    processed_rows = cached_df.count()
    if processed_rows == 0:
        cached_df.unpersist()
        raise ValueError("Tidak ada data yang lolos preprocessing untuk disimpan ke MongoDB")

    inserted_count = 0
    batch: list[dict[str, object]] = []

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        client[mongo_db][mongo_collection].delete_many({})
        collection = client[mongo_db][mongo_collection]

        for row in cached_df.toLocalIterator():
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

    cached_df.unpersist()
    return processed_rows, inserted_count


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

    processed_df = preprocess_comments_df(raw_df, source_col=resolved_source_col).repartition(effective_partitions)

    preview_rows = [row.asDict(recursive=True) for row in processed_df.limit(5).collect()]
    if preview_rows:
        print("Preview hasil preprocessing:")
        for preview_row in preview_rows:
            print(
                f"- {preview_row.get('comment_id', '')} | {preview_row.get('video_id', '')} | {preview_row.get('text_preprocessed', '')[:160]}"
            )

    insert_batch_size = int(os.getenv("MONGO_INSERT_BATCH_SIZE", "200"))

    processed_count, inserted_count = save_processed_comments_to_mongo(
        processed_df,
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        mongo_collection=processed_collection,
        batch_size=insert_batch_size,
    )
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
