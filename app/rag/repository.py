from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings


def _normalize(text: str) -> str:
    return re.sub(r"[\s，。！？；：、“”‘’《》,.!?;:'\"()（）\-]+", "", text).lower()


def _is_meaningful_match(text: str) -> bool:
    normalized = _normalize(text)
    return len(normalized) >= 2


def _candidate_query_phrases(question: str) -> list[str]:
    normalized = _normalize(question)
    phrases = [normalized]
    lookup_markers = [
        "出自哪一首",
        "出自哪首",
        "出自哪里",
        "是哪一首",
        "是哪首",
        "哪一首",
        "哪首",
    ]
    for marker in lookup_markers:
        normalized_marker = _normalize(marker)
        if normalized_marker in normalized:
            before_marker = normalized.split(normalized_marker, 1)[0]
            if len(before_marker) >= 2:
                phrases.append(before_marker)
    return list(dict.fromkeys(phrase for phrase in phrases if len(phrase) >= 2))


@lru_cache(maxsize=1)
def load_poems() -> list[dict[str, Any]]:
    settings = get_settings()
    data = json.loads(Path(settings.data_file).read_text(encoding="utf-8"))
    return data


def list_poems() -> list[dict[str, Any]]:
    return load_poems()


def list_titles_by_author(author: str, limit: int = 20) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    normalized_author = _normalize(author)
    if not normalized_author:
        return titles

    for poem in load_poems():
        if _normalize(poem.get("author", "")) != normalized_author:
            continue
        title = poem.get("title", "").strip()
        if title and title not in seen:
            titles.append(title)
            seen.add(title)
        if len(titles) >= limit:
            break
    return titles


def get_poem_by_id(poem_id: str) -> dict[str, Any] | None:
    for poem in load_poems():
        if poem["id"] == poem_id:
            return poem
    return None


def search_exact(question: str) -> list[dict[str, Any]]:
    normalized_question = _normalize(question)
    query_phrases = _candidate_query_phrases(question)
    results: list[dict[str, Any]] = []
    for poem in load_poems():
        normalized_content = _normalize(poem["content"])
        haystacks = [
            poem["title"],
            poem["author"],
            poem["dynasty"],
            poem["content"],
            poem.get("translation", ""),
            poem.get("annotation", ""),
            poem.get("appreciation", ""),
        ]
        tags = poem.get("tags", [])
        if any(
            _is_meaningful_match(item) and _normalize(item) in normalized_question
            for item in haystacks + tags
        ):
            results.append(poem)
            continue
        if any(len(phrase) >= 4 and phrase in normalized_content for phrase in query_phrases):
            results.append(poem)
    return results


def search_by_tags(question: str, limit: int = 4) -> list[dict[str, Any]]:
    normalized_question = _normalize(question)
    scored: list[tuple[int, dict[str, Any]]] = []
    for poem in load_poems():
        tags = poem.get("tags", [])
        score = sum(1 for tag in tags if _normalize(tag) in normalized_question)
        if score > 0:
            scored.append((score, poem))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [poem for _, poem in scored[:limit]]


def render_poem_context(poem: dict[str, Any]) -> str:
    tags = "、".join(poem.get("tags", []))
    return (
        f"题目：{poem['title']}\n"
        f"作者：{poem['author']}\n"
        f"朝代：{poem['dynasty']}\n"
        f"正文：{poem['content']}\n"
        f"译文：{poem.get('translation', '暂无')}\n"
        f"注释：{poem.get('annotation', '暂无')}\n"
        f"赏析：{poem.get('appreciation', '暂无')}\n"
        f"标签：{tags or '暂无'}\n"
        f"来源：{poem.get('source', '未知来源')}"
    )
