from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from preprocess import (
    clean_text,
    extract_text_features,
    normalize_and_stem,
    normalize_without_stem,
)


DEFAULT_INPUT = Path("notebooks/data/raw/comments_raw_all_videos.json")
DEFAULT_OUTPUT_CSV = Path("notebooks/data/processed/comments_preprocessed_all_videos.csv")
DEFAULT_OUTPUT_JSONL = Path("notebooks/data/processed/comments_preprocessed_all_videos.jsonl")


OUTPUT_FIELDS = [
    "comment_id",
    "thread_id",
    "video_id",
    "author",
    "author_channel_id",
    "published_at",
    "updated_at",
    "like_count",
    "total_reply_count",
    "text_original",
    "text_clean",
    "text_preprocessed",
    "text_stemmed",
    "char_count",
    "word_count",
    "emoji_count",
    "url_count",
    "hashtag_count",
    "mention_count",
    "exclamation_count",
    "question_count",
    "uppercase_ratio",
]


def _get_nested(document: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = document
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def iter_raw_comments(data: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for thread in data.get("raw_comment_threads", []):
        snippet = thread.get("snippet", {})
        top_level = snippet.get("topLevelComment", {})
        comment_snippet = top_level.get("snippet", {})
        author_channel_id = _get_nested(comment_snippet, "authorChannelId", "value")
        text_original = (
            comment_snippet.get("textOriginal")
            or comment_snippet.get("textDisplay")
            or ""
        )

        yield {
            "comment_id": top_level.get("id") or thread.get("id"),
            "thread_id": thread.get("id"),
            "video_id": snippet.get("videoId") or thread.get("video_id"),
            "author": comment_snippet.get("authorDisplayName"),
            "author_channel_id": author_channel_id,
            "published_at": comment_snippet.get("publishedAt"),
            "updated_at": comment_snippet.get("updatedAt"),
            "like_count": comment_snippet.get("likeCount", 0),
            "total_reply_count": snippet.get("totalReplyCount", 0),
            "text_original": text_original,
        }


def preprocess_row(row: dict[str, Any], with_stem: bool = False) -> dict[str, Any]:
    text = str(row.get("text_original") or "")
    features = extract_text_features(text)
    stemmed = normalize_and_stem(text) if with_stem else ""
    return {
        **row,
        "text_clean": clean_text(text),
        "text_preprocessed": normalize_without_stem(text),
        "text_stemmed": stemmed,
        **features,
    }


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def preprocess_raw_file(
    input_path: Path = DEFAULT_INPUT,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    output_jsonl: Path = DEFAULT_OUTPUT_JSONL,
    with_stem: bool = False,
) -> dict[str, int]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    seen_comment_ids: set[str] = set()
    rows: list[dict[str, Any]] = []
    skipped_empty = 0
    skipped_duplicate = 0

    for raw_row in iter_raw_comments(data):
        comment_id = str(raw_row.get("comment_id") or "")
        text_original = str(raw_row.get("text_original") or "")
        if not text_original.strip():
            skipped_empty += 1
            continue
        if comment_id and comment_id in seen_comment_ids:
            skipped_duplicate += 1
            continue
        if comment_id:
            seen_comment_ids.add(comment_id)

        processed_row = preprocess_row(raw_row, with_stem=with_stem)
        if processed_row["text_preprocessed"]:
            rows.append(processed_row)
        else:
            skipped_empty += 1

    write_csv(rows, output_csv)
    write_jsonl(rows, output_jsonl)

    return {
        "raw_threads": len(data.get("raw_comment_threads", [])),
        "processed_rows": len(rows),
        "skipped_empty": skipped_empty,
        "skipped_duplicate": skipped_duplicate,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess raw YouTube commentThread JSON into processed CSV and JSONL."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument(
        "--with-stem",
        action="store_true",
        help="Tambahkan kolom text_stemmed memakai Sastrawi. Lebih lambat.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = preprocess_raw_file(
        input_path=args.input,
        output_csv=args.output_csv,
        output_jsonl=args.output_jsonl,
        with_stem=args.with_stem,
    )
    print(
        "Preprocessing selesai: "
        f"raw_threads={result['raw_threads']}, "
        f"processed_rows={result['processed_rows']}, "
        f"skipped_empty={result['skipped_empty']}, "
        f"skipped_duplicate={result['skipped_duplicate']}"
    )
    print(f"CSV: {args.output_csv}")
    print(f"JSONL: {args.output_jsonl}")


if __name__ == "__main__":
    main()
