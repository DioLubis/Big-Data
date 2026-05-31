from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pyspark.sql import DataFrame, SparkSession

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # pragma: no cover - fallback for missing dependency
    _load_dotenv = None


@dataclass(frozen=True)
class MongoConfig:
    mongo_uri: str
    mongo_db: str
    mongo_comments_collection: str
    spark_master: str


def load_project_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"

    if _load_dotenv is not None:
        _load_dotenv(dotenv_path=env_path, override=False)
        return

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_mongo_config() -> MongoConfig:
    load_project_env()

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
