from __future__ import annotations

import os
from typing import Iterable, Optional

from dotenv import load_dotenv
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


def save_processed_comments(
    df: DataFrame,
    output_path: str,
    output_format: str = "parquet",
) -> None:
    writer = df.coalesce(1).write.mode("overwrite")
    if output_format.lower() == "csv":
        writer.option("header", True).csv(output_path)
        return
    writer.parquet(output_path)


def main() -> None:
    load_dotenv()
    spark = create_spark_session(app_name="mongo-comments-preprocess")
    source_col = os.getenv("SPARK_TEXT_COLUMN")
    output_path = os.getenv(
        "SPARK_PROCESSED_OUTPUT_PATH",
        "notebooks/data/processed/comments_processed_spark",
    )
    output_format = os.getenv("SPARK_PROCESSED_OUTPUT_FORMAT", "parquet")

    raw_df = load_comments_spark_df(spark)
    processed_df = preprocess_comments_df(raw_df, source_col=source_col)

    processed_df.show(5, truncate=False)
    save_processed_comments(processed_df, output_path=output_path, output_format=output_format)
    print(f"Data hasil preprocessing disimpan ke: {output_path} ({output_format})")


if __name__ == "__main__":
    main()
