from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "external" / "chinese-poetry"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "poems.json"
SOURCE_NAME = "chinese-poetry/chinese-poetry"


DATASETS = {
    "tang": {
        "path": "全唐诗",
        "pattern": "poet.tang.*.json",
        "dynasty": "唐",
        "tags": ["唐诗"],
        "limit": None,
    },
    "song-ci": {
        "path": "宋词",
        "pattern": "ci.song.*.json",
        "dynasty": "宋",
        "tags": ["宋词"],
        "limit": None,
    },
    "shijing": {
        "path": "诗经",
        "pattern": "*.json",
        "dynasty": "先秦",
        "tags": ["诗经"],
        "limit": None,
    },
    "chuci": {
        "path": "楚辞",
        "pattern": "*.json",
        "dynasty": "战国",
        "tags": ["楚辞"],
        "limit": None,
    },
}


def _slugify(value: str, fallback: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or fallback


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _as_text(value: Any) -> str:
    if isinstance(value, list):
        return "".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


def _iter_records(path: Path) -> Iterable[dict[str, Any]]:
    data = _read_json(path)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        yield data


def _convert_record(record: dict[str, Any], dataset_key: str, index: int) -> dict[str, Any] | None:
    config = DATASETS[dataset_key]
    title = _as_text(record.get("title") or record.get("rhythmic") or record.get("chapter") or record.get("section"))
    author = _as_text(record.get("author") or record.get("poet") or record.get("writer") or "佚名")
    content = _as_text(record.get("paragraphs") or record.get("content") or record.get("paragraph"))

    if not title or not content:
        return None

    poem_id = "-".join(
        [
            "cp",
            dataset_key,
            _slugify(author, "unknown"),
            _slugify(title, f"item-{index}"),
        ]
    )

    return {
        "id": poem_id,
        "title": title,
        "author": author,
        "dynasty": config["dynasty"],
        "content": content,
        "translation": "",
        "annotation": "",
        "appreciation": "",
        "tags": [*config["tags"], config["dynasty"]],
        "source": SOURCE_NAME,
    }


def _load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = _read_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return data


def import_dataset(source_dir: Path, dataset_key: str, limit: int | None) -> list[dict[str, Any]]:
    config = DATASETS[dataset_key]
    dataset_dir = source_dir / config["path"]
    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Missing dataset directory: {dataset_dir}\n"
            "Please clone https://github.com/chinese-poetry/chinese-poetry.git "
            "into external/chinese-poetry first."
        )

    imported: list[dict[str, Any]] = []
    for file_path in sorted(dataset_dir.glob(config["pattern"])):
        for record in _iter_records(file_path):
            item = _convert_record(record, dataset_key, len(imported))
            if item is not None:
                imported.append(item)
                if limit is not None and len(imported) >= limit:
                    return imported
    return imported


def merge_poems(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in existing}
    seen_signatures = {
        (item.get("title", ""), item.get("author", ""), item.get("content", "")) for item in existing
    }

    for item in incoming:
        signature = (item["title"], item["author"], item["content"])
        if item["id"] in by_id or signature in seen_signatures:
            continue
        by_id[item["id"]] = item
        seen_signatures.add(signature)

    return list(by_id.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import chinese-poetry/chinese-poetry into data/poems.json")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument(
        "--dataset",
        action="append",
        choices=sorted(DATASETS.keys()),
        help="Dataset to import. Repeat this flag to import multiple datasets. Defaults to tang and song-ci.",
    )
    parser.add_argument("--limit", type=int, default=2000, help="Max records per dataset. Use 0 for no limit.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_keys = args.dataset or ["tang", "song-ci"]
    limit = None if args.limit == 0 else args.limit

    existing = _load_existing(args.output)
    incoming: list[dict[str, Any]] = []
    for dataset_key in dataset_keys:
        imported = import_dataset(args.source_dir, dataset_key, limit)
        incoming.extend(imported)
        print(f"{dataset_key}: imported {len(imported)} records")

    merged = merge_poems(existing, incoming)
    added_count = len(merged) - len(existing)

    print(f"existing: {len(existing)}")
    print(f"incoming: {len(incoming)}")
    print(f"added: {added_count}")
    print(f"total: {len(merged)}")

    if not args.dry_run:
        _write_json(args.output, merged)
        print(f"wrote: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
