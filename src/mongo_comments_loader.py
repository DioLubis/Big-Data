from __future__ import annotations

import json
import os
import sys
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


def create_spark_session(
    app_name: str = "mongo-comments-loader",
    cores: Optional[int] = None,
    executor_cores: Optional[int] = None,
    memory: Optional[str] = None,
) -> SparkSession:
    config = load_mongo_config()
    src_dir = str(Path(__file__).resolve().parent)
    spark_master = config.spark_master

    if cores is not None and spark_master.startswith("local"):
        spark_master = f"local[{cores}]"

    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    os.environ["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (src_dir, os.environ.get("PYTHONPATH", ""))
        if part
    )
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    builder = (
        SparkSession.builder.appName(app_name)
        .master(spark_master)
        .config("spark.python.worker.faulthandler.enabled", "true")
        .config("spark.sql.execution.pyspark.udf.faulthandler.enabled", "true")
    )

    if executor_cores is not None:
        builder = builder.config("spark.executor.cores", str(executor_cores))

    if cores is not None:
        builder = builder.config("spark.cores.max", str(cores))

    if memory:
        builder = (
            builder.config("spark.driver.memory", memory)
            .config("spark.executor.memory", memory)
        )

    if spark_master.startswith("local"):
        os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
        builder = (
            builder.config("spark.driver.host", "127.0.0.1")
            .config("spark.driver.bindAddress", "127.0.0.1")
        )

    return builder.getOrCreate()


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
