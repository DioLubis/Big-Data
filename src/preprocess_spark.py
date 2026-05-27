from __future__ import annotations

import os
from typing import Iterable, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lower, regexp_replace, trim, udf
from pyspark.sql.types import StringType

from mongo_comments_loader import create_spark_session, load_comments_spark_df
from preprocess import normalize_and_stem


TEXT_CANDIDATES: tuple[str, ...] = (
    "text_original",
    "text",
    "textDisplay",
    "comment_text",
)


def resolve_text_column(df: DataFrame, candidates: Iterable[str] = TEXT_CANDIDATES) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    raise ValueError(
        "Kolom teks tidak ditemukan. Coba set SPARK_TEXT_COLUMN atau sesuaikan nama field."
    )


@udf(returnType=StringType())
def normalize_and_stem_udf(text: Optional[str]) -> str:
    return normalize_and_stem(text or "")


def preprocess_comments_df(
    df: DataFrame,
    source_col: Optional[str] = None,
    output_col: str = "text_preprocessed",
) -> DataFrame:
    source_col = source_col or resolve_text_column(df)

    cleaned = (
        df.withColumn("_text_source", col(source_col).cast("string"))
        .withColumn("_text_source", lower(col("_text_source")))
        .withColumn("_text_source", regexp_replace(col("_text_source"), r"http\S+|www\S+", " "))
        .withColumn("_text_source", regexp_replace(col("_text_source"), r"@\w+", " "))
        .withColumn("_text_source", regexp_replace(col("_text_source"), r"#\w+", " "))
        .withColumn("_text_source", regexp_replace(col("_text_source"), r"\d+", " "))
        .withColumn(
            "_text_source",
            regexp_replace(col("_text_source"), r"[^\w\s]", " "),
        )
        .withColumn("_text_source", trim(regexp_replace(col("_text_source"), r"\s+", " ")))
    )

    processed = cleaned.withColumn(output_col, normalize_and_stem_udf(col("_text_source")))

    return processed.drop("_text_source")


def save_processed_comments_to_mongo(
    df: DataFrame,
    mongo_uri: str,
    mongo_db: str,
    mongo_collection: str,
    batch_size: int = 1000,
) -> int:
    if not mongo_uri or not mongo_db or not mongo_collection:
        raise ValueError("Konfigurasi MongoDB untuk output preprocessing belum lengkap")

    client = MongoClient(mongo_uri)
    collection = client[mongo_db][mongo_collection]

    collection.delete_many({})

    inserted_count = 0
    batch: list[dict] = []
    for row in df.toLocalIterator():
        document = row.asDict(recursive=True)
        document.pop("_id", None)
        batch.append(document)

        if len(batch) >= batch_size:
            collection.insert_many(batch)
            inserted_count += len(batch)
            batch.clear()

    if batch:
        collection.insert_many(batch)
        inserted_count += len(batch)

    client.close()
    return inserted_count


def main() -> None:
    load_dotenv()
    spark = create_spark_session(app_name="mongo-comments-preprocess")
    source_col = os.getenv("SPARK_TEXT_COLUMN")
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    mongo_db = os.getenv("MONGO_DB", "").strip()
    processed_collection = os.getenv(
        "MONGO_PROCESSED_COLLECTION",
        os.getenv("MONGO_COLLECTION_PROCESSED", "comments_processed"),
    ).strip()

    raw_df = load_comments_spark_df(spark)
    processed_df = preprocess_comments_df(raw_df, source_col=source_col)

    processed_df.show(5, truncate=False)
    inserted_count = save_processed_comments_to_mongo(
        processed_df,
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        mongo_collection=processed_collection,
    )
    print(
        "Data hasil preprocessing disimpan ke MongoDB: "
        f"{mongo_db}.{processed_collection} (dokumen: {inserted_count})"
    )


if __name__ == "__main__":
    main()
