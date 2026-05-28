from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pyspark.sql import DataFrame, SparkSession


@dataclass(frozen=True)
class MongoConfig:
    mongo_uri: str
    mongo_db: str
    mongo_comments_collection: str
    spark_master: str


def load_mongo_config() -> MongoConfig:
    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    mongo_db = os.getenv("MONGO_DB", "").strip()
    mongo_comments_collection = (
        os.getenv("MONGO_COMMENTS_COLLECTION")
        or os.getenv("MONGO_COLLECTION")
        or "comments"
    ).strip()
    spark_master = os.getenv("SPARK_MASTER", "local[*]").strip()

    if not mongo_uri:
        raise ValueError("MONGO_URI belum diisi di .env")
    if not mongo_db:
        raise ValueError("MONGO_DB belum diisi di .env")
    if not mongo_comments_collection:
        raise ValueError("MONGO_COMMENTS_COLLECTION belum diisi di .env")

    return MongoConfig(
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        mongo_comments_collection=mongo_comments_collection,
        spark_master=spark_master,
    )


def create_spark_session(app_name: str = "mongo-comments-loader") -> SparkSession:
    config = load_mongo_config()

    return (
        SparkSession.builder.appName(app_name)
        .master(config.spark_master)
        .getOrCreate()
    )


def fetch_comments_documents() -> List[Dict[str, Any]]:
    config = load_mongo_config()
    client = MongoClient(config.mongo_uri)
    collection = client[config.mongo_db][config.mongo_comments_collection]

    documents: List[Dict[str, Any]] = []
    for document in collection.find({}):
        document.pop("_id", None)
        documents.append(document)

    client.close()
    return documents


def _normalize_value_for_spark(value: Any) -> Any:
    if isinstance(value, dict) or isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def _normalize_document_for_spark(document: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: _normalize_value_for_spark(value)
        for key, value in document.items()
    }


def load_comments_spark_df(spark: Optional[SparkSession] = None) -> DataFrame:
    documents = [
        _normalize_document_for_spark(document)
        for document in fetch_comments_documents()
    ]
    if not documents:
        raise ValueError(
            "Collection MongoDB kosong. Pastikan collection 'comments' berisi data."
        )

    spark = spark or create_spark_session()
    return spark.createDataFrame(documents)


def main() -> None:
    spark = create_spark_session()
    df = load_comments_spark_df(spark)
    print(f"Total documents: {df.count()}")
    df.printSchema()
    df.show(5, truncate=False)


if __name__ == "__main__":
    main()
