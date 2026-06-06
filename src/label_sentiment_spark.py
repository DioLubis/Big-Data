from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import partial
from typing import Any, Iterable, Iterator

from pymongo import MongoClient
from pyspark.sql import Row, SparkSession

from mongo_comments_loader import (
    create_spark_session as create_project_spark_session,
    load_project_env,
)


DEFAULT_SENTIMENT_MODEL = "w11wo/indonesian-roberta-base-sentiment-classifier"
LABEL_ALIASES = {
    "label_0": "positive",
    "label_1": "neutral",
    "label_2": "negative",
    "negatif": "negative",
    "netral": "neutral",
    "positif": "positive",
}
VALID_LABELS = {"positive", "negative", "neutral"}


def load_env() -> None:
    """Load the project .env file without overriding existing environment values."""
    load_project_env()


def create_spark_session() -> SparkSession:
    """Create SparkSession with the same project configuration as preprocessing."""
    cores = int(os.getenv("SPARK_CORES", os.getenv("SPARK_NUM_PARTITIONS", "4")))
    memory = os.getenv(
        "SPARK_MEMORY",
        os.getenv("SPARK_EXECUTOR_MEMORY", "2g"),
    ).strip()
    return create_project_spark_session(
        app_name="mongo-comments-sentiment-labeling",
        cores=cores,
        memory=memory,
    )


def _normalize_value_for_spark(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def _load_processed_documents(
    mongo_uri: str,
    mongo_db: str,
    collection_name: str,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    projection = {"_id": False}

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        for document in client[mongo_db][collection_name].find({}, projection):
            documents.append(
                {
                    key: _normalize_value_for_spark(value)
                    for key, value in document.items()
                }
            )

    return documents


def _normalize_label(raw_label: Any) -> str:
    label = str(raw_label or "").strip().lower()
    label = LABEL_ALIASES.get(label, label)
    if label not in VALID_LABELS:
        raise ValueError(
            f"Label model tidak dikenali: {raw_label!r}. "
            "Model harus menghasilkan positive, negative, atau neutral."
        )
    return label


def _validate_runtime_dependencies() -> None:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Dependency labeling belum terpasang. Jalankan: "
            "pip install -r requirements.txt"
        ) from exc


def _batched(rows: Iterable[Row], batch_size: int) -> Iterator[list[Row]]:
    batch: list[Row] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def label_partition(
    rows: Iterable[Row],
    *,
    mongo_uri: str,
    mongo_db: str,
    output_collection: str,
    model_name: str,
    batch_size: int,
    device: int,
) -> Iterator[tuple[int, int]]:
    """Label and insert one Spark partition, loading the model only once."""
    from transformers import pipeline

    classifier = None
    processed_count = 0
    inserted_count = 0

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        collection = client[mongo_db][output_collection]

        for row_batch in _batched(rows, batch_size):
            documents = [row.asDict(recursive=True) for row in row_batch]
            non_empty_indexes: list[int] = []
            texts: list[str] = []

            for index, document in enumerate(documents):
                text = str(document.get("text_preprocessed") or "")
                if text.strip():
                    non_empty_indexes.append(index)
                    texts.append(text)
                else:
                    document["label"] = "neutral"
                    document["score"] = 0.0
                    document["sentiment_score"] = 0.0

            if texts:
                if classifier is None:
                    classifier = pipeline(
                        "text-classification",
                        model=model_name,
                        tokenizer=model_name,
                        device=device,
                    )

                predictions = classifier(
                    texts,
                    truncation=True,
                    batch_size=batch_size,
                )
                for index, prediction in zip(non_empty_indexes, predictions):
                    if isinstance(prediction, list):
                        prediction = max(
                            prediction,
                            key=lambda item: float(item.get("score", 0.0)),
                        )
                    score = float(prediction.get("score", 0.0))
                    documents[index]["label"] = _normalize_label(prediction.get("label"))
                    documents[index]["score"] = score
                    documents[index]["sentiment_score"] = score

            labeled_at = datetime.now(timezone.utc).isoformat()
            for document in documents:
                document.pop("_id", None)
                document["labeled_at"] = labeled_at

            if documents:
                result = collection.insert_many(documents, ordered=False)
                processed_count += len(documents)
                inserted_count += len(result.inserted_ids)

    yield processed_count, inserted_count


def main() -> None:
    load_env()
    _validate_runtime_dependencies()

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    mongo_db = os.getenv("MONGO_DB", "").strip()
    input_collection = os.getenv(
        "MONGO_PROCESSED_COLLECTION",
        "comments_processed",
    ).strip()
    output_collection = os.getenv(
        "MONGO_LABELED_COLLECTION",
        "comments_labeled",
    ).strip()
    model_name = os.getenv("SENTIMENT_MODEL", DEFAULT_SENTIMENT_MODEL).strip()
    num_partitions = int(os.getenv("SPARK_NUM_PARTITIONS", "4"))
    batch_size = int(os.getenv("SENTIMENT_BATCH_SIZE", "16"))
    device = int(os.getenv("SENTIMENT_DEVICE", "-1"))

    if not mongo_uri:
        raise ValueError("MONGO_URI belum diisi di .env")
    if not mongo_db:
        raise ValueError("MONGO_DB belum diisi di .env")
    if not input_collection:
        raise ValueError("MONGO_PROCESSED_COLLECTION belum diisi di .env")
    if not output_collection:
        raise ValueError("MONGO_LABELED_COLLECTION belum diisi di .env")
    if batch_size < 1:
        raise ValueError("SENTIMENT_BATCH_SIZE harus lebih besar dari 0")

    spark = create_spark_session()
    print(
        "Spark session aktif: "
        f"app_id={spark.sparkContext.applicationId}, "
        f"master={spark.sparkContext.master}, "
        f"partitions={num_partitions}, "
        f"model={model_name}",
        flush=True,
    )
    print(
        f"MongoDB input: {mongo_db}.{input_collection}; "
        f"output: {mongo_db}.{output_collection}",
        flush=True,
    )

    try:
        documents = _load_processed_documents(
            mongo_uri,
            mongo_db,
            input_collection,
        )
        total_read = len(documents)
        print(f"Jumlah komentar dibaca: {total_read}", flush=True)
        if total_read == 0:
            raise ValueError(
                f"Collection sumber kosong: {mongo_db}.{input_collection}"
            )

        if not any("text_preprocessed" in document for document in documents):
            raise ValueError(
                "Kolom text_preprocessed tidak ditemukan di collection sumber."
            )

        input_df = spark.createDataFrame(documents).repartition(num_partitions)

        with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
            client[mongo_db][output_collection].delete_many({})

        partition_labeler = partial(
            label_partition,
            mongo_uri=mongo_uri,
            mongo_db=mongo_db,
            output_collection=output_collection,
            model_name=model_name,
            batch_size=batch_size,
            device=device,
        )
        stats = input_df.rdd.mapPartitions(partition_labeler).collect()
        processed_count = sum(item[0] for item in stats)
        inserted_count = sum(item[1] for item in stats)

        print(f"Jumlah komentar diproses: {processed_count}", flush=True)
        print(f"Jumlah dokumen ditulis: {inserted_count}", flush=True)
        print(
            f"Hasil labeling tersimpan di: {mongo_db}.{output_collection}",
            flush=True,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
