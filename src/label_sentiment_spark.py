from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import partial
from typing import Any, Iterable, Iterator

from pymongo import MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError
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


def _prepare_output_collection(
    mongo_uri: str,
    mongo_db: str,
    collection_name: str,
) -> tuple[int, int]:
    """Remove retry duplicates and enforce one labeled document per comment."""
    removed_count = 0

    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        collection = client[mongo_db][collection_name]
        duplicate_groups = collection.aggregate(
            [
                {"$match": {"comment_id": {"$exists": True, "$ne": None}}},
                {
                    "$group": {
                        "_id": "$comment_id",
                        "document_ids": {"$push": "$_id"},
                        "count": {"$sum": 1},
                    }
                },
                {"$match": {"count": {"$gt": 1}}},
            ],
            allowDiskUse=True,
        )

        for group in duplicate_groups:
            duplicate_ids = group["document_ids"][1:]
            if duplicate_ids:
                removed_count += collection.delete_many(
                    {"_id": {"$in": duplicate_ids}}
                ).deleted_count

        collection.create_index("comment_id", unique=True)
        existing_count = collection.count_documents({})

    return removed_count, existing_count


def _load_existing_comment_ids(
    mongo_uri: str,
    mongo_db: str,
    collection_name: str,
) -> set[str]:
    with MongoClient(mongo_uri, serverSelectionTimeoutMS=10000) as client:
        return {
            str(comment_id)
            for comment_id in client[mongo_db][collection_name].distinct("comment_id")
            if comment_id is not None
        }


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


def _upsert_documents(collection, documents: list[dict[str, Any]]) -> None:
    operations = [
        ReplaceOne(
            {"comment_id": document["comment_id"]},
            document,
            upsert=True,
        )
        for document in documents
    ]
    try:
        collection.bulk_write(operations, ordered=False)
    except BulkWriteError as exc:
        non_duplicate_errors = [
            error
            for error in exc.details.get("writeErrors", [])
            if error.get("code") != 11000
        ]
        if non_duplicate_errors:
            raise

        # A concurrent Spark retry may win the upsert race. Replace again now
        # that the unique comment_id document exists.
        for document in documents:
            collection.replace_one(
                {"comment_id": document["comment_id"]},
                document,
                upsert=True,
            )


def label_partition(
    rows: Iterable[Row],
    *,
    mongo_uri: str,
    mongo_db: str,
    output_collection: str,
    model_name: str,
    batch_size: int,
    device: int,
    max_length: int,
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
                    max_length=max_length,
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
                _upsert_documents(collection, documents)
                processed_count += len(documents)
                inserted_count += len(documents)

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
    max_length = int(os.getenv("SENTIMENT_MAX_LENGTH", "512"))

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
    if max_length < 1:
        raise ValueError("SENTIMENT_MAX_LENGTH harus lebih besar dari 0")

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

        if not all(document.get("comment_id") for document in documents):
            raise ValueError(
                "Semua dokumen sumber harus memiliki comment_id untuk upsert idempotent."
            )

        removed_duplicates, existing_count = _prepare_output_collection(
            mongo_uri,
            mongo_db,
            output_collection,
        )
        existing_comment_ids = _load_existing_comment_ids(
            mongo_uri,
            mongo_db,
            output_collection,
        )
        pending_documents = [
            document
            for document in documents
            if str(document["comment_id"]) not in existing_comment_ids
        ]
        print(
            "Status collection output sebelum labeling: "
            f"existing={existing_count}, "
            f"duplikat_dihapus={removed_duplicates}, "
            f"belum_dilabel={len(pending_documents)}",
            flush=True,
        )

        if not pending_documents:
            print("Semua komentar sudah memiliki label.", flush=True)
            return

        input_df = spark.createDataFrame(pending_documents).repartition(num_partitions)

        partition_labeler = partial(
            label_partition,
            mongo_uri=mongo_uri,
            mongo_db=mongo_db,
            output_collection=output_collection,
            model_name=model_name,
            batch_size=batch_size,
            device=device,
            max_length=max_length,
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
