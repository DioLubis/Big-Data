from __future__ import annotations

import html
import json
import os
import re
import sys
import unicodedata
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import emoji
import ftfy
import regex
from dotenv import load_dotenv
from pyspark import StorageLevel
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory


MONGO_CONNECTOR_PACKAGE = "org.mongodb.spark:mongo-spark-connector_2.13:11.0.1"
DERIVED_TEXT_COLUMNS = {
    "text_clean",
    "text_preprocessed",
    "text_stemmed",
    "text_final_classic",
    "text_final_transformer",
    "text_final_classic_stemmed",
    "text_stopword_removed",
    "text_slang_normalized",
}
GENERATED_COLUMNS = DERIVED_TEXT_COLUMNS | {
    "tokens",
    "normalized_token_count",
    "raw_char_count",
    "raw_word_count",
    "emoji_count",
    "url_count",
    "mention_count",
    "hashtag_count",
    "exclamation_count",
    "question_count",
    "uppercase_ratio",
    "is_all_caps",
    "contains_negation",
    "contains_domain_terms",
    "contains_profanity",
    "domain_term_count",
    "profanity_count",
    "is_duplicate_text",
    "preprocessing_version",
    "processed_at",
}

NEGATIONS = {"tidak", "bukan", "jangan", "belum", "tanpa", "kurang", "tak"}
INTENSIFIERS = {
    "sangat",
    "amat",
    "banget",
    "terlalu",
    "paling",
    "lebih",
    "semakin",
    "sekali",
}
DOMAIN_TERMS = {
    "tni",
    "dpr",
    "ruu",
    "uu",
    "sipil",
    "militer",
    "rakyat",
    "negara",
    "korupsi",
    "koruptor",
    "aset",
    "perampasan",
    "pemerintah",
    "presiden",
    "prabowo",
    "polisi",
    "demo",
    "mahasiswa",
    "orde",
    "orba",
    "oligarki",
    "demokrasi",
    "pasal",
}
SENTIMENT_TERMS = {
    "setuju",
    "mantap",
    "bagus",
    "buruk",
    "kacau",
    "rusak",
    "takut",
    "bahaya",
    "aman",
    "bravo",
    "bubarkan",
    "dukung",
    "tolak",
    "sahkan",
    "lawan",
    "adil",
    "zalim",
}
PROFANITY_TERMS = {
    "anjing",
    "anjir",
    "anjay",
    "bangsat",
    "bajingan",
    "brengsek",
    "goblok",
    "tolol",
    "bodoh",
    "kampret",
    "kontol",
    "memek",
    "ngentot",
    "tai",
    "sialan",
}
SPECIAL_TOKENS = {
    "emo_laugh",
    "emo_sad",
    "emo_angry",
    "emo_pos",
    "emo_neg",
    "emo_think",
    "emo_other",
    "url_token",
    "user_mention",
}
STEM_WHITELIST = {
    "tni",
    "dpr",
    "ruu",
    "uu",
    "prabowo",
    "jokowi",
    "polri",
    "orba",
    "1998",
    "pppk",
    "pasal",
    "demokrasi",
    "oligarki",
} | SPECIAL_TOKENS | NEGATIONS | INTENSIFIERS | DOMAIN_TERMS | SENTIMENT_TERMS
PRESERVED_STOPWORDS = NEGATIONS | INTENSIFIERS | DOMAIN_TERMS | SENTIMENT_TERMS

SLANG_MAP = {
    "yg": "yang",
    "ga": "tidak",
    "gak": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "ngak": "tidak",
    "gk": "tidak",
    "kagak": "tidak",
    "tdk": "tidak",
    "klo": "kalau",
    "kalo": "kalau",
    "gw": "saya",
    "gue": "saya",
    "gua": "saya",
    "ane": "saya",
    "lu": "kamu",
    "lo": "kamu",
    "loe": "kamu",
    "elu": "kamu",
    "dr": "dari",
    "dgn": "dengan",
    "dg": "dengan",
    "utk": "untuk",
    "krn": "karena",
    "karna": "karena",
    "jd": "jadi",
    "jdi": "jadi",
    "tp": "tapi",
    "trs": "terus",
    "trus": "terus",
    "bs": "bisa",
    "bgt": "banget",
    "bngt": "banget",
    "emg": "memang",
    "emang": "memang",
    "udah": "sudah",
    "sdh": "sudah",
    "blm": "belum",
    "blom": "belum",
    "org": "orang",
    "orng": "orang",
    "aja": "saja",
    "skrg": "sekarang",
    "skrng": "sekarang",
    "sampe": "sampai",
    "ampe": "sampai",
    "tau": "tahu",
    "gmn": "bagaimana",
    "gimana": "bagaimana",
    "knp": "kenapa",
    "kyk": "seperti",
    "kayak": "seperti",
    "kaya": "seperti",
    "cm": "hanya",
    "cuma": "hanya",
    "doang": "saja",
    "makin": "semakin",
    "pak": "bapak",
    "bkn": "bukan",
    "jgn": "jangan",
    "dah": "sudah",
    "udh": "sudah",
    "sm": "sama",
    "pake": "pakai",
    "pengen": "ingin",
    "makasih": "terima kasih",
    "makasi": "terima kasih",
}

EMOJI_GROUPS = {
    "emo_laugh": {"😂", "🤣", "😆", "😹"},
    "emo_sad": {"😢", "😭", "🥲", "😞", "😔"},
    "emo_angry": {"😡", "🤬", "😠"},
    "emo_pos": {"👍", "✅", "❤️", "❤", "🔥", "💪", "🙏"},
    "emo_neg": {"👎", "❌", "💩"},
    "emo_think": {"🤔", "🧐"},
}

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
MENTION_RE = re.compile(r"(?<!\w)@[\w.-]+")
HASHTAG_RE = re.compile(r"#([\w]+)")
ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u2060\ufeff]")
WHITESPACE_RE = re.compile(r"\s+")
ELONGATED_RE = re.compile(r"(?i)([a-z])\1{2,}")
CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z])(?=[A-Z])")
RAW_TOKEN_RE = regex.compile(r"[\p{L}\p{N}_]+")
ALL_CAPS_TOKEN_RE = regex.compile(r"\b\p{Lu}{2,}\b")

STOPWORDS = set(StopWordRemoverFactory().get_stop_words()) - PRESERVED_STOPWORDS
_STEMMER = None

PREPROCESS_SCHEMA = StructType(
    [
        StructField("text_stemmed", StringType(), False),
        StructField("tokens", ArrayType(StringType(), False), False),
        StructField("normalized_token_count", IntegerType(), False),
        StructField("raw_char_count", IntegerType(), False),
        StructField("raw_word_count", IntegerType(), False),
        StructField("emoji_count", IntegerType(), False),
        StructField("url_count", IntegerType(), False),
        StructField("mention_count", IntegerType(), False),
        StructField("hashtag_count", IntegerType(), False),
        StructField("exclamation_count", IntegerType(), False),
        StructField("question_count", IntegerType(), False),
        StructField("uppercase_ratio", DoubleType(), False),
        StructField("is_all_caps", BooleanType(), False),
        StructField("contains_negation", BooleanType(), False),
        StructField("contains_domain_terms", BooleanType(), False),
        StructField("contains_profanity", BooleanType(), False),
        StructField("domain_term_count", IntegerType(), False),
        StructField("profanity_count", IntegerType(), False),
    ]
)
REPORT_SCHEMA = StructType(
    [
        StructField("run_id", StringType(), False),
        StructField("processed_at", StringType(), False),
        StructField("input_collection", StringType(), False),
        StructField("output_collection", StringType(), False),
        StructField("preprocessing_version", StringType(), False),
        StructField("total_rows_input", LongType(), False),
        StructField("total_rows_output", LongType(), False),
        StructField("total_unique_videos", LongType(), False),
        StructField("total_unique_authors", LongType(), False),
        StructField("missing_text_count", LongType(), False),
        StructField("duplicate_comment_id_count", LongType(), False),
        StructField("duplicate_text_original_count", LongType(), False),
        StructField("duplicate_text_count", LongType(), False),
        StructField("short_comments_count", LongType(), False),
        StructField("long_comments_count", LongType(), False),
        StructField("comments_with_emoji_count", LongType(), False),
        StructField("comments_with_url_count", LongType(), False),
        StructField("comments_with_mention_count", LongType(), False),
        StructField("comments_with_hashtag_count", LongType(), False),
        StructField("label_distribution_json", StringType(), False),
        StructField("validation_metrics_json", StringType(), False),
        StructField("top_tokens_before_json", StringType(), False),
        StructField("top_tokens_after_json", StringType(), False),
        StructField("total_profanity", LongType(), False),
        StructField("total_domain_terms", LongType(), False),
        StructField("empty_text_stemmed_count", LongType(), False),
        StructField("warnings", ArrayType(StringType(), False), False),
    ]
)


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Konfigurasi wajib belum diisi: {name}")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "y"}


def basic_clean_text(text: Any) -> str:
    cleaned = ftfy.fix_text(html.unescape(str(text or "")))
    cleaned = unicodedata.normalize("NFKC", cleaned)
    cleaned = ZERO_WIDTH_RE.sub("", cleaned)
    cleaned = cleaned.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return WHITESPACE_RE.sub(" ", cleaned).strip()


def count_terms(tokens: list[str], terms: set[str]) -> int:
    return sum(token in terms for token in tokens)


def emoji_token(character: str) -> str:
    for token, characters in EMOJI_GROUPS.items():
        if character in characters:
            return token
    return "emo_other"


def replace_emojis(text: str) -> str:
    for item in emoji.emoji_list(text):
        text = text.replace(item["emoji"], f" {emoji_token(item['emoji'])} ")
    return text


def expand_hashtag(value: str) -> str:
    separated = CAMEL_BOUNDARY_RE.sub(" ", value).replace("_", " ").casefold()
    for combined, expanded in (
        ("tolakruutni", "tolak ruu tni"),
        ("tolakrevisiuutni", "tolak revisi uu tni"),
        ("revisiuutni", "revisi uu tni"),
        ("ruutni", "ruu tni"),
        ("uutni", "uu tni"),
    ):
        separated = separated.replace(combined, expanded)
    return separated


def normalize_token(token: str, slang: dict[str, str]) -> list[str]:
    token = ELONGATED_RE.sub(lambda match: match.group(1) * 2, token.casefold())
    normalized = slang.get(token)
    if normalized is None:
        collapsed = re.sub(r"(?i)([a-z])\1+", r"\1", token)
        normalized = slang.get(collapsed, token)
    normalized = slang.get(normalized, normalized)
    return RAW_TOKEN_RE.findall(normalized)


def get_stemmer():
    global _STEMMER
    if _STEMMER is None:
        _STEMMER = StemmerFactory().create_stemmer()
    return _STEMMER


@lru_cache(maxsize=100_000)
def stem_token(token: str) -> str:
    if token in STEM_WHITELIST:
        return token
    return get_stemmer().stem(token)


def build_preprocessor(slang_broadcast):
    def preprocess_text(text: Any):
        raw = basic_clean_text(text)
        raw_tokens = [token.casefold() for token in RAW_TOKEN_RE.findall(raw)]
        letters = [character for character in raw if character.isalpha()]
        uppercase_count = sum(character.isupper() for character in letters)
        uppercase_ratio = uppercase_count / len(letters) if letters else 0.0

        feature_tokens: list[str] = []
        for token in raw_tokens:
            feature_tokens.extend(normalize_token(token, slang_broadcast.value))
        for hashtag in HASHTAG_RE.findall(raw):
            for token in RAW_TOKEN_RE.findall(expand_hashtag(hashtag)):
                feature_tokens.extend(normalize_token(token, slang_broadcast.value))

        working = URL_RE.sub(" url_token ", raw)
        working = MENTION_RE.sub(" user_mention ", working)
        working = HASHTAG_RE.sub(lambda match: f" {expand_hashtag(match.group(1))} ", working)
        working = replace_emojis(working).casefold()

        normalized_tokens: list[str] = []
        for token in RAW_TOKEN_RE.findall(working):
            normalized_tokens.extend(normalize_token(token, slang_broadcast.value))

        filtered_tokens = [
            token
            for token in normalized_tokens
            if token in SPECIAL_TOKENS
            or token in PRESERVED_STOPWORDS
            or (len(token) > 1 and token not in STOPWORDS)
        ]
        stemmed_tokens = [stem_token(token) for token in filtered_tokens]
        stemmed_tokens = [token for token in stemmed_tokens if token]

        domain_count = count_terms(feature_tokens, DOMAIN_TERMS)
        profanity_count = count_terms(feature_tokens, PROFANITY_TERMS)
        return (
            " ".join(stemmed_tokens),
            stemmed_tokens,
            len(filtered_tokens),
            len(raw),
            len(raw_tokens),
            emoji.emoji_count(raw),
            len(URL_RE.findall(raw)),
            len(MENTION_RE.findall(raw)),
            len(HASHTAG_RE.findall(raw)),
            raw.count("!"),
            raw.count("?"),
            float(round(uppercase_ratio, 6)),
            bool(letters and uppercase_ratio >= 0.9 and len(letters) >= 3),
            any(token in NEGATIONS for token in feature_tokens),
            domain_count > 0,
            profanity_count > 0,
            domain_count,
            profanity_count,
        )

    return preprocess_text


def create_spark_session() -> SparkSession:
    mongo_uri = required_env("MONGO_URI")
    app_name = os.getenv("SPARK_APP_NAME", "IndonesianCommentStemmingPreprocessing").strip()
    master = os.getenv("SPARK_MASTER", "local[*]").strip()
    package = os.getenv("MONGO_SPARK_CONNECTOR_PACKAGE", MONGO_CONNECTOR_PACKAGE).strip()

    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.jars.packages", package)
        .config("spark.mongodb.read.connection.uri", mongo_uri)
        .config("spark.mongodb.write.connection.uri", mongo_uri)
        .config("spark.sql.execution.pythonUDF.arrow.enabled", "false")
    )
    if master.startswith("local"):
        os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
        builder = builder.config("spark.driver.host", "127.0.0.1").config(
            "spark.driver.bindAddress", "127.0.0.1"
        )
    return builder.getOrCreate()


def mongo_read(spark: SparkSession, database: str, collection: str) -> DataFrame:
    try:
        return (
            spark.read.format("mongodb")
            .option("database", database)
            .option("collection", collection)
            .option("aggregation.allowDiskUse", "true")
            .load()
        )
    except Exception as exc:
        raise RuntimeError(
            f"Gagal membaca MongoDB collection {database}.{collection}. "
            "Pastikan MongoDB aktif, URI benar, dan MongoDB Spark Connector tersedia."
        ) from exc


def mongo_write(df: DataFrame, database: str, collection: str, mode: str) -> None:
    try:
        (
            df.write.format("mongodb")
            .mode(mode)
            .option("database", database)
            .option("collection", collection)
            .save()
        )
    except Exception as exc:
        raise RuntimeError(f"Gagal menulis MongoDB collection {database}.{collection}.") from exc


def count_pattern(df: DataFrame, pattern: str) -> int:
    return df.filter(F.col("text_original").rlike(pattern)).count()


def top_tokens(df: DataFrame, tokens_column: str, limit: int = 30) -> list[dict[str, Any]]:
    rows = (
        df.select(F.explode(F.col(tokens_column)).alias("token"))
        .filter(F.col("token") != "")
        .groupBy("token")
        .count()
        .orderBy(F.desc("count"), F.asc("token"))
        .limit(limit)
        .collect()
    )
    return [{"token": row["token"], "count": int(row["count"])} for row in rows]


def build_validation_report(input_df: DataFrame) -> dict[str, Any]:
    report: dict[str, Any] = {
        "total_rows": input_df.count(),
        "total_unique_videos": input_df.select("video_id").distinct().count()
        if "video_id" in input_df.columns
        else 0,
        "total_unique_authors": input_df.select("author").distinct().count()
        if "author" in input_df.columns
        else 0,
        "missing_text_original": input_df.filter(
            F.col("text_original").isNull() | (F.trim(F.col("text_original")) == "")
        ).count(),
        "duplicate_comment_id": 0,
        "duplicate_text_original": input_df.groupBy("text_original")
        .count()
        .filter(F.col("count") > 1)
        .agg(F.sum(F.col("count") - 1).alias("duplicates"))
        .first()["duplicates"]
        or 0,
        "short_comments": input_df.filter(F.length(F.trim(F.col("text_original"))) < 10).count(),
        "long_comments": input_df.filter(F.length(F.col("text_original")) > 1000).count(),
        "comments_with_emoji": count_pattern(input_df, r"[\x{1F000}-\x{1FAFF}]"),
        "comments_with_url": count_pattern(input_df, r"(?i)(https?://|www\.)"),
        "comments_with_mention": count_pattern(input_df, r"@\w+"),
        "comments_with_hashtag": count_pattern(input_df, r"#\w+"),
    }
    if "comment_id" in input_df.columns:
        report["duplicate_comment_id"] = (
            input_df.groupBy("comment_id")
            .count()
            .filter(F.col("comment_id").isNotNull() & (F.col("count") > 1))
            .agg(F.sum(F.col("count") - 1).alias("duplicates"))
            .first()["duplicates"]
            or 0
        )
    if "label" in input_df.columns:
        report["label_distribution"] = {
            str(row["label"]): int(row["count"])
            for row in input_df.groupBy("label").count().collect()
        }
    return report


def add_raw_tokens(df: DataFrame) -> DataFrame:
    cleaned = F.regexp_replace(
        F.lower(F.coalesce(F.col("text_original"), F.lit(""))),
        r"[^\p{L}\p{N}_]+",
        " ",
    )
    return df.withColumn(
        "_raw_report_tokens",
        F.filter(F.split(F.trim(cleaned), r"\s+"), lambda token: token != ""),
    )


def preprocess_dataframe(input_df: DataFrame, slang_broadcast) -> DataFrame:
    preprocess_udf = F.udf(build_preprocessor(slang_broadcast), PREPROCESS_SCHEMA)
    columns_to_drop = [name for name in GENERATED_COLUMNS if name in input_df.columns]
    base_df = input_df.drop(*columns_to_drop)
    processed = base_df.withColumn("_preprocessing", preprocess_udf(F.col("text_original")))
    processed = processed.select("*", "_preprocessing.*").drop("_preprocessing")
    duplicate_window = Window.partitionBy("text_stemmed")
    return (
        processed.withColumn(
            "is_duplicate_text",
            (F.count(F.lit(1)).over(duplicate_window) > 1) & (F.col("text_stemmed") != ""),
        )
        .withColumn("preprocessing_version", F.lit(required_env("PREPROCESSING_VERSION")))
        .withColumn("processed_at", F.current_timestamp())
    )


def choose_output_collection(spark: SparkSession, database: str, requested: str) -> tuple[str, str]:
    if env_bool("OVERWRITE_EXISTING", False):
        return requested, "overwrite"
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{requested}_{suffix}", "append"


def build_final_report(
    validation: dict[str, Any],
    processed_df: DataFrame,
    input_collection: str,
    output_collection: str,
    raw_top_tokens: list[dict[str, Any]],
) -> dict[str, Any]:
    totals = processed_df.agg(
        F.count("*").alias("total_rows_output"),
        F.sum(F.col("profanity_count")).alias("total_profanity"),
        F.sum(F.col("domain_term_count")).alias("total_domain_terms"),
        F.sum(F.when(F.col("text_stemmed") == "", 1).otherwise(0)).alias("empty_text_stemmed"),
        F.sum(F.when(F.col("is_duplicate_text"), 1).otherwise(0)).alias("duplicate_text_count"),
        F.sum(
            F.when(
                F.col("contains_negation")
                & ~F.col("text_stemmed").rlike(
                    r"(^|\s)(tidak|bukan|jangan|belum|tanpa|kurang|tak)(\s|$)"
                ),
                1,
            ).otherwise(0)
        ).alias("lost_negation_count"),
        F.sum(
            F.when(
                F.col("contains_domain_terms")
                & ~F.col("text_stemmed").rlike(
                    r"(^|\s)(tni|dpr|ruu|uu|sipil|militer|rakyat|negara|korupsi|koruptor|aset|"
                    r"perampasan|pemerintah|presiden|prabowo|polisi|demo|mahasiswa|orde|orba|"
                    r"oligarki|demokrasi|pasal)(\s|$)"
                ),
                1,
            ).otherwise(0)
        ).alias("lost_domain_term_count"),
    ).first()
    warnings: list[str] = []
    if totals["empty_text_stemmed"]:
        warnings.append(f"{totals['empty_text_stemmed']} text_stemmed kosong.")
    if totals["lost_negation_count"]:
        warnings.append(f"{totals['lost_negation_count']} komentar terindikasi kehilangan negasi.")
    if totals["lost_domain_term_count"]:
        warnings.append(
            f"{totals['lost_domain_term_count']} komentar terindikasi kehilangan domain term."
        )
    return {
        "run_id": str(uuid.uuid4()),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "input_collection": input_collection,
        "output_collection": output_collection,
        "preprocessing_version": required_env("PREPROCESSING_VERSION"),
        "total_rows_input": int(validation["total_rows"]),
        "total_rows_output": int(totals["total_rows_output"]),
        "total_unique_videos": int(validation["total_unique_videos"]),
        "total_unique_authors": int(validation["total_unique_authors"]),
        "missing_text_count": int(validation["missing_text_original"]),
        "duplicate_comment_id_count": int(validation["duplicate_comment_id"]),
        "duplicate_text_original_count": int(validation["duplicate_text_original"]),
        "duplicate_text_count": int(totals["duplicate_text_count"] or 0),
        "short_comments_count": int(validation["short_comments"]),
        "long_comments_count": int(validation["long_comments"]),
        "comments_with_emoji_count": int(validation["comments_with_emoji"]),
        "comments_with_url_count": int(validation["comments_with_url"]),
        "comments_with_mention_count": int(validation["comments_with_mention"]),
        "comments_with_hashtag_count": int(validation["comments_with_hashtag"]),
        "label_distribution_json": json.dumps(
            validation.get("label_distribution", {}), ensure_ascii=False
        ),
        "validation_metrics_json": json.dumps(validation, ensure_ascii=False),
        "top_tokens_before_json": json.dumps(raw_top_tokens, ensure_ascii=False),
        "top_tokens_after_json": json.dumps(top_tokens(processed_df, "tokens"), ensure_ascii=False),
        "total_profanity": int(totals["total_profanity"] or 0),
        "total_domain_terms": int(totals["total_domain_terms"] or 0),
        "empty_text_stemmed_count": int(totals["empty_text_stemmed"] or 0),
        "warnings": warnings,
    }


def main() -> None:
    load_dotenv(override=False)
    database = required_env("MONGO_DATABASE")
    input_collection = required_env("MONGO_INPUT_COLLECTION")
    requested_output_collection = required_env("MONGO_OUTPUT_COLLECTION")
    report_collection = required_env("MONGO_REPORT_COLLECTION")
    if requested_output_collection == input_collection:
        raise ValueError(
            "MONGO_OUTPUT_COLLECTION tidak boleh sama dengan MONGO_INPUT_COLLECTION."
        )

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    print(
        f"Spark aktif: master={spark.sparkContext.master}; "
        f"input={database}.{input_collection}",
        flush=True,
    )
    try:
        input_df = mongo_read(spark, database, input_collection).persist(StorageLevel.MEMORY_AND_DISK)
        total_rows = input_df.count()
        if total_rows == 0:
            raise ValueError(f"Collection input kosong: {database}.{input_collection}")
        if "text_original" not in input_df.columns:
            raise ValueError("Kolom text_original wajib tersedia pada collection input.")

        validation = build_validation_report(input_df)
        raw_report_df = add_raw_tokens(input_df)
        raw_top_tokens = top_tokens(raw_report_df, "_raw_report_tokens")
        slang_broadcast = spark.sparkContext.broadcast(SLANG_MAP)

        processed_df = preprocess_dataframe(input_df, slang_broadcast).persist(
            StorageLevel.MEMORY_AND_DISK
        )
        output_collection, write_mode = choose_output_collection(
            spark, database, requested_output_collection
        )
        mongo_write(processed_df, database, output_collection, write_mode)

        report = build_final_report(
            validation, processed_df, input_collection, output_collection, raw_top_tokens
        )
        report_df = spark.createDataFrame([report], schema=REPORT_SCHEMA)
        mongo_write(report_df, database, report_collection, "append")

        print(json.dumps(report, ensure_ascii=False, indent=2, default=str), flush=True)
        print("\nContoh 10 hasil:", flush=True)
        preview_columns = ["text_original", "text_stemmed"]
        if "label" in processed_df.columns:
            preview_columns.append("label")
        processed_df.select(*preview_columns).show(10, truncate=100)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
