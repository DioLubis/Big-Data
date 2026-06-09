from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator

from pymongo import MongoClient
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression, NaiveBayes
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import CountVectorizer, IDF, RegexTokenizer, StringIndexer, NGram, VectorAssembler
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql.functions import col, lit, monotonically_increasing_id, rand, row_number, udf
from pyspark.sql.window import Window


SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mongo_comments_loader import (  # noqa: E402
    create_spark_session as create_project_spark_session,
    load_project_env,
)


SEED = 42
TEXT_COL = "text_preprocessed"
LABEL_COL = "label"
MONGO_RESULTS_COLLECTION = "sentiment_model_results"
VALID_LABELS = ("positive", "neutral", "negative")


# Load file .env untuk konfigurasi environment.
def load_env() -> None:
    load_project_env()


# Menerima input angka bulat positif dari user dengan nilai default.
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


# Menerima input memori Spark dan memvalidasi formatnya.
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


# Membuat dan mengonfigurasi Spark Session berdasarkan input resource user.
def create_spark_session() -> SparkSession:
    spark_master = os.getenv("SPARK_MASTER", "local[*]").strip()
    default_cores = int(os.getenv("SPARK_CORES", os.getenv("SPARK_NUM_PARTITIONS", "4")))
    default_memory = os.getenv(
        "SPARK_MEMORY",
        os.getenv("SPARK_EXECUTOR_MEMORY", "2g"),
    ).strip()

    print("Masukkan resource Spark untuk eksperimen MLlib.", flush=True)
    print(f"Target Spark master: {spark_master}", flush=True)
    cores = _prompt_positive_int("Total core aplikasi", default=default_cores)
    memory = _prompt_memory("Memory per executor/driver", default=default_memory)

    return create_project_spark_session(
        app_name="youtube-sentiment-spark-mllib-experiments",
        cores=cores,
        memory=memory,
    )


# Mengambil dan memvalidasi konfigurasi MongoDB dari environment.
def _require_mongo_config() -> tuple[str, str, str]:
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    mongo_db = os.getenv("MONGO_DB", "").strip()
    labeled_collection = os.getenv(
        "MONGO_LABELED_COLLECTION",
        "comments_labeled",
    ).strip()

    if not mongo_uri:
        raise ValueError("MONGO_URI belum diisi di .env")
    if not mongo_db:
        raise ValueError("MONGO_DB belum diisi di .env")
    if not labeled_collection:
        raise ValueError("MONGO_LABELED_COLLECTION belum diisi di .env")

    return mongo_uri, mongo_db, labeled_collection


# Konversi dict atau list ke format string JSON agar kompatibel dengan Spark.
def _normalize_value_for_spark(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


# Load data komentar berlabel dari MongoDB ke DataFrame Spark.
def load_labeled_comments(spark: SparkSession) -> DataFrame:
    mongo_uri, mongo_db, labeled_collection = _require_mongo_config()
    projection = {
        "_id": False,
        TEXT_COL: True,
        LABEL_COL: True,
    }

    documents: list[dict[str, object]] = []
    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        cursor = client[mongo_db][labeled_collection].find(
            {
                TEXT_COL: {"$exists": True, "$ne": ""},
                LABEL_COL: {"$exists": True, "$ne": ""},
            },
            projection,
        )
        for document in cursor:
            documents.append(
                {
                    key: _normalize_value_for_spark(value)
                    for key, value in document.items()
                }
            )

    if not documents:
        raise ValueError(
            f"Collection MongoDB kosong atau tidak valid: {mongo_db}.{labeled_collection}"
        )

    df = spark.createDataFrame(documents)
    df = (
        df.select(
            col(TEXT_COL).cast("string").alias(TEXT_COL),
            col(LABEL_COL).cast("string").alias(LABEL_COL),
        )
        .filter(col(TEXT_COL).isNotNull() & (col(TEXT_COL) != ""))
        .filter(col(LABEL_COL).isin(*VALID_LABELS))
        .withColumn("row_id", monotonically_increasing_id())
    )

    print(
        f"MongoDB input: {mongo_db}.{labeled_collection}; "
        f"rows_terbaca={df.count()}",
        flush=True,
    )
    return df


# Membuat pipeline model ML (Logistic Regression / Naive Bayes) dengan text processing.
def build_pipeline(model_name: str) -> Pipeline:
    tokenizer = RegexTokenizer(
        inputCol=TEXT_COL,
        outputCol="tokens",
        pattern=r"\s+",
        gaps=True,
        minTokenLength=2,
    )
    
    label_indexer = StringIndexer(
        inputCol=LABEL_COL,
        outputCol="label_index",
        handleInvalid="skip",
    )
    
    normalized_name = model_name.strip().lower()
    stages = [tokenizer]
    
    if normalized_name in {"logistic_regression", "logistic regression", "lr"}:
        # Logistic Regression: Unigrams + Bigrams, minDF=10.0 to strongly prune features, 10% L1 penalty
        ngram = NGram(n=2, inputCol="tokens", outputCol="bigrams")
        cv_unigram = CountVectorizer(inputCol="tokens", outputCol="unigram_features", vocabSize=8000, minDF=10.0)
        cv_bigram = CountVectorizer(inputCol="bigrams", outputCol="bigram_features", vocabSize=8000, minDF=10.0)
        assembler = VectorAssembler(inputCols=["unigram_features", "bigram_features"], outputCol="raw_features")
        idf = IDF(inputCol="raw_features", outputCol="features")
        
        classifier = LogisticRegression(
            featuresCol="features",
            labelCol="label_index",
            predictionCol="prediction_index",
            maxIter=100,
            regParam=0.03,        # Optimized regularization parameter
            elasticNetParam=0.1,  # 10% L1, 90% L2
            family="multinomial",
        )
        stages.extend([ngram, cv_unigram, cv_bigram, assembler, idf, label_indexer, classifier])
        
    elif normalized_name in {"naive_bayes", "naive bayes", "nb"}:
        # Naive Bayes: Unigrams + Bigrams, minDF=3.0, using raw counts directly (no IDF)
        ngram = NGram(n=2, inputCol="tokens", outputCol="bigrams")
        cv_unigram = CountVectorizer(inputCol="tokens", outputCol="unigram_features", vocabSize=8000, minDF=3.0)
        cv_bigram = CountVectorizer(inputCol="bigrams", outputCol="bigram_features", vocabSize=8000, minDF=3.0)
        assembler = VectorAssembler(inputCols=["unigram_features", "bigram_features"], outputCol="features")
        
        classifier = NaiveBayes(
            featuresCol="features",
            labelCol="label_index",
            predictionCol="prediction_index",
            modelType="multinomial",
            smoothing=1.0,
        )
        stages.extend([ngram, cv_unigram, cv_bigram, assembler, label_indexer, classifier])
        
    else:
        raise ValueError(f"Model tidak dikenali: {model_name}")

    return Pipeline(stages=stages)


# Map index prediksi numerik kembali ke label teks (positive, neutral, negative).
def _with_prediction_label(predictions: DataFrame, labels: list[str]) -> DataFrame:
    def map_prediction(index):
        if index is None:
            return None
        position = int(index)
        if position < 0 or position >= len(labels):
            return None
        return labels[position]

    map_prediction_udf = udf(map_prediction, "string")
    return predictions.withColumn(
        "prediction",
        map_prediction_udf(col("prediction_index")),
    )


# Menhitung precision, recall, f1-score, support, dan akurasi model.
def _classification_report(predictions: DataFrame) -> str:
    labels = list(VALID_LABELS)
    total = predictions.count()
    if total == 0:
        return "Tidak ada data untuk dievaluasi."

    rows = {
        (row[LABEL_COL], row["prediction"]): row["count"]
        for row in predictions.groupBy(LABEL_COL, "prediction").count().collect()
    }

    lines = [
        f"{'label':<12}{'precision':>12}{'recall':>12}{'f1-score':>12}{'support':>12}"
    ]
    weighted_precision = 0.0
    weighted_recall = 0.0
    weighted_f1 = 0.0

    for label in labels:
        tp = rows.get((label, label), 0)
        fp = sum(rows.get((actual, label), 0) for actual in labels if actual != label)
        fn = sum(rows.get((label, predicted), 0) for predicted in labels if predicted != label)
        support = tp + fn
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / support if support else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        weighted_precision += precision * support
        weighted_recall += recall * support
        weighted_f1 += f1 * support
        lines.append(
            f"{label:<12}{precision:>12.4f}{recall:>12.4f}{f1:>12.4f}{support:>12}"
        )

    evaluator = MulticlassClassificationEvaluator(
        labelCol="label_index",
        predictionCol="prediction_index",
        metricName="accuracy",
    )
    accuracy = evaluator.evaluate(predictions)
    lines.append("")
    lines.append(f"{'accuracy':<12}{accuracy:>36.4f}{total:>12}")
    lines.append(
        f"{'weighted avg':<12}"
        f"{weighted_precision / total:>12.4f}"
        f"{weighted_recall / total:>12.4f}"
        f"{weighted_f1 / total:>12.4f}"
        f"{total:>12}"
    )
    return "\n".join(lines)


# Membuat visualisasi confusion matrix dalam bentuk teks.
def _confusion_matrix(predictions: DataFrame) -> str:
    labels = list(VALID_LABELS)
    rows = {
        (row[LABEL_COL], row["prediction"]): row["count"]
        for row in predictions.groupBy(LABEL_COL, "prediction").count().collect()
    }

    header = f"{'actual/pred':<14}" + "".join(f"{label:>12}" for label in labels)
    lines = [header]
    for actual in labels:
        values = "".join(f"{rows.get((actual, predicted), 0):>12}" for predicted in labels)
        lines.append(f"{actual:<14}{values}")
    return "\n".join(lines)


# Menyeleksi kolom hasil prediksi untuk disimpan.
def _prepare_output_predictions(
    predictions: DataFrame,
    model_name: str,
    dataset_name: str,
    fold: str,
) -> DataFrame:
    return predictions.select(
        lit(model_name).alias("model_name"),
        lit(dataset_name).alias("dataset_name"),
        lit(fold).alias("fold"),
        col(TEXT_COL),
        col(LABEL_COL),
        col("prediction"),
    )


# Menyimpan data hasil prediksi ke MongoDB secara bulk per partisi.
def save_predictions(prediction_df: DataFrame) -> None:
    mongo_uri, mongo_db, _ = _require_mongo_config()

    def insert_partition(rows: Iterable[Row]) -> Iterator[int]:
        batch: list[dict[str, object]] = []
        inserted = 0
        with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
            collection = client[mongo_db][MONGO_RESULTS_COLLECTION]
            for row in rows:
                document = row.asDict(recursive=True)
                batch.append(document)
                if len(batch) >= 500:
                    result = collection.insert_many(batch, ordered=False)
                    inserted += len(result.inserted_ids)
                    batch.clear()

            if batch:
                result = collection.insert_many(batch, ordered=False)
                inserted += len(result.inserted_ids)

        yield inserted

    total_inserted = sum(prediction_df.rdd.mapPartitions(insert_partition).collect())
    print(
        f"Prediksi disimpan ke MongoDB: {mongo_db}.{MONGO_RESULTS_COLLECTION}; "
        f"inserted={total_inserted}",
        flush=True,
    )


# Latih model, evaluasi data train/val/test, dan simpan hasilnya ke MongoDB.
def train_and_evaluate_pipeline(
    pipeline: Pipeline,
    train_df: DataFrame,
    val_df: DataFrame,
    test_df: DataFrame,
    dataset_name: str,
    model_name: str,
) -> None:
    print(f"\n=== {model_name} | {dataset_name} ===", flush=True)
    train_count = train_df.count()
    val_count = val_df.count()
    test_count = test_df.count()
    print(
        f"Jumlah data: train={train_count}, val={val_count}, test={test_count}",
        flush=True,
    )

    fitted_pipeline = pipeline.fit(train_df)
    label_indexer_model = fitted_pipeline.stages[-2]
    labels = list(label_indexer_model.labels)

    for fold, fold_df in (
        ("train", train_df),
        ("val", val_df),
        ("test", test_df),
    ):
        predictions = _with_prediction_label(fitted_pipeline.transform(fold_df), labels)
        predictions = predictions.cache()

        print(f"\n[{model_name} | {dataset_name} | {fold}]", flush=True)
        print(_classification_report(predictions), flush=True)
        print("\nConfusion Matrix:", flush=True)
        print(_confusion_matrix(predictions), flush=True)

        output_df = _prepare_output_predictions(
            predictions,
            model_name=model_name,
            dataset_name=dataset_name,
            fold=fold,
        )
        save_predictions(output_df)
        predictions.unpersist()


# Mengambil sample acak sejumlah n untuk label tertentu.
def _exact_label_sample(df: DataFrame, label: str, n: int) -> DataFrame:
    return (
        df.filter(col(LABEL_COL) == label)
        .orderBy(rand(SEED + sum(ord(char) for char in label)))
        .limit(n)
    )


# Melakukan split data tersstratifikasi secara presisi (exact split) agar jumlah baris train, val, dan test sesuai target.
def _stratified_exact_split(df: DataFrame, train_ratio: float, val_ratio: float, seed: int) -> tuple[DataFrame, DataFrame, DataFrame]:
    window_spec = Window.partitionBy(LABEL_COL).orderBy(rand(seed))
    df_ranked = df.withColumn("row_num", row_number().over(window_spec))

    label_counts = {row[LABEL_COL]: row["count"] for row in df.groupBy(LABEL_COL).count().collect()}

    train_cond = None
    val_cond = None
    test_cond = None

    for label in VALID_LABELS:
        count = label_counts.get(label, 0)
        if count == 0:
            continue
        train_limit = int(round(count * train_ratio))
        val_limit = int(round(count * val_ratio))

        c_train = (col(LABEL_COL) == label) & (col("row_num") <= train_limit)
        c_val = (col(LABEL_COL) == label) & (col("row_num") > train_limit) & (col("row_num") <= train_limit + val_limit)
        c_test = (col(LABEL_COL) == label) & (col("row_num") > train_limit + val_limit)

        train_cond = c_train if train_cond is None else train_cond | c_train
        val_cond = c_val if val_cond is None else val_cond | c_val
        test_cond = c_test if test_cond is None else test_cond | c_test

    train_df = df_ranked.filter(train_cond).drop("row_num")
    val_df = df_ranked.filter(val_cond).drop("row_num")
    test_df = df_ranked.filter(test_cond).drop("row_num")

    return train_df, val_df, test_df


# Membuat dataset eksperimen (10k pure, 10k + sisa negative, dan 15k full) dengan split data tersstratifikasi.
def _build_experiment_datasets(df: DataFrame) -> dict[str, tuple[DataFrame, DataFrame, DataFrame]]:
    positive_df = _exact_label_sample(df, "positive", 2640)
    neutral_df = _exact_label_sample(df, "neutral", 3324)
    negative_10k_df = _exact_label_sample(df, "negative", 4036)

    used_negative_with_id = negative_10k_df.select("row_id")
    discarded_negative_df = df.filter(col(LABEL_COL) == "negative").join(
        used_negative_with_id,
        on="row_id",
        how="left_anti",
    )

    dataset_10k = positive_df.unionByName(neutral_df).unionByName(negative_10k_df).cache()
    dataset_full = df.cache()
    discarded_negative_df = discarded_negative_df.cache()

    print("\nDataset eksperimen:", flush=True)
    print(f"10k pure={dataset_10k.count()}", flush=True)
    print(f"sisa negative untuk test tambahan={discarded_negative_df.count()}", flush=True)
    print(f"15.516 full={dataset_full.count()}", flush=True)

    train_10k, val_10k, test_10k = _stratified_exact_split(dataset_10k, 0.60, 0.15, seed=SEED)
    train_full, val_full, test_full = _stratified_exact_split(dataset_full, 0.60, 0.15, seed=SEED)
    test_10k_plus_discarded = test_10k.unionByName(discarded_negative_df)

    return {
        "10k_pure": (train_10k.cache(), val_10k.cache(), test_10k.cache()),
        "10k_plus_discarded_negative_test": (
            train_10k.cache(),
            val_10k.cache(),
            test_10k_plus_discarded.cache(),
        ),
        "15516_full": (train_full.cache(), val_full.cache(), test_full.cache()),
    }


# Main program untuk menjalankan semua eksperimen.
def main() -> None:
    load_env()
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        labeled_df = load_labeled_comments(spark).cache()
        print("Distribusi label input:", flush=True)
        labeled_df.groupBy(LABEL_COL).count().orderBy(LABEL_COL).show(truncate=False)

        datasets = _build_experiment_datasets(labeled_df)
        models = (
            ("Logistic Regression", "logistic_regression"),
            ("Naive Bayes", "naive_bayes"),
        )

        for display_name, pipeline_name in models:
            for dataset_name, (train_df, val_df, test_df) in datasets.items():
                pipeline = build_pipeline(pipeline_name)
                train_and_evaluate_pipeline(
                    pipeline=pipeline,
                    train_df=train_df,
                    val_df=val_df,
                    test_df=test_df,
                    dataset_name=dataset_name,
                    model_name=display_name,
                )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
