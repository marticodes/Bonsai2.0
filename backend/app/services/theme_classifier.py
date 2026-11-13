"""
Primary theme classification for unique OCR-clustered posts.

Uses the text already extracted for each post. Screenshots are not read again.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path

from openai import OpenAI


CATEGORIES: list[str] = [
    "Beauty",
    "Gaming",
    "Sports",
    "Entertainment",
    "Lifestyle",
    "Education",
    "Technology",
    "Relationships",
    "News",
    "Other",
]

_STORE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "theme_classifications.json"
)

_WORD = re.compile(r"[^\W\d_]{3,}", re.UNICODE)

ClassifyBatch = Callable[[list[tuple[int, str]]], dict[int, str]]


def representative_text(post: dict) -> str:
    """Text that represents one unique post, preferring normalized OCR."""
    screenshots = post.get("screenshots")
    sources = screenshots if isinstance(screenshots, list) and screenshots else [post]

    normalized: list[str] = []
    raw: list[str] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        normalized_text = str(source.get("normalized_text") or "").strip()
        ocr_text = str(source.get("ocr_text") or "").strip()
        if normalized_text and normalized_text not in normalized:
            normalized.append(normalized_text)
        if ocr_text and ocr_text not in raw:
            raw.append(ocr_text)

    if normalized:
        return "\n".join(normalized)
    return "\n".join(raw)


def is_understandable(text: str) -> bool:
    """False when OCR text is empty, numeric, or too fragmentary to theme."""
    letters = sum(1 for char in text if char.isalpha())
    if letters < 5:
        return False
    words = _WORD.findall(text)
    return len(words) >= 2 or any(len(word) >= 5 for word in words)


def coerce_category(value: object) -> str:
    if not isinstance(value, str):
        return "Other"
    cleaned = value.strip().lower()
    for category in CATEGORIES:
        if cleaned == category.lower():
            return category
    return "Other"


def category_summary(posts: list[dict]) -> dict:
    """Count posts per category and percentages that sum to 100."""
    counts = {category: 0 for category in CATEGORIES}
    for post in posts:
        category = coerce_category(post.get("category"))
        counts[category] += 1

    total = sum(counts.values())
    percentages = _percentages(counts, total)
    return {
        "total_posts": total,
        "posts": [
            {
                "cluster_id": post.get("cluster_id"),
                "category": coerce_category(post.get("category")),
            }
            for post in posts
        ],
        "categories": [
            {
                "category": category,
                "count": counts[category],
                "percentage": percentages[category],
            }
            for category in CATEGORIES
        ],
    }


def classify_themes(
    posts: list[dict],
    classify_batch: ClassifyBatch | None = None,
    store_path: Path | None = None,
) -> dict:
    """
    Assign one primary category to each unique post and store the result.

    Posts whose OCR text cannot be understood are put in the closest category and are not sent
    to the model.
    """
    pending: list[tuple[int, str]] = []
    assigned: dict[int, str] = {}

    for index, post in enumerate(posts):
        text = representative_text(post)
        if is_understandable(text):
            pending.append((index, text[:4000]))
        else:
            assigned[index] = "Other"

    if pending:
        batch = classify_batch or _classify_with_model
        model_categories = batch(pending)
        for index, _text in pending:
            assigned[index] = coerce_category(model_categories.get(index))

    classified = [
        {
            "cluster_id": post.get("cluster_id"),
            "category": assigned[index],
        }
        for index, post in enumerate(posts)
    ]
    summary = category_summary(classified)
    save_classification(summary, store_path)
    return summary


def save_classification(payload: dict, path: Path | None = None) -> None:
    destination = path or _STORE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(destination)


def load_classification(path: Path | None = None) -> dict:
    destination = path or _STORE_PATH
    if not destination.exists():
        return category_summary([])
    try:
        stored = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return category_summary([])
    if not isinstance(stored, dict):
        return category_summary([])
    posts = stored.get("posts")
    if not isinstance(posts, list):
        return category_summary([])
    return category_summary([post for post in posts if isinstance(post, dict)])


def _percentages(counts: dict[str, int], total: int) -> dict[str, float]:
    if total <= 0:
        return {category: 0.0 for category in CATEGORIES}

    # Work in tenths of a percent, then give leftover tenths to the
    # largest remainders so the displayed percentages sum to 100.
    exact = {
        category: counts[category] * 1000 / total for category in CATEGORIES
    }
    floors = {category: int(exact[category]) for category in CATEGORIES}
    leftover = 1000 - sum(floors.values())
    order = sorted(
        CATEGORIES,
        key=lambda category: (
            exact[category] - floors[category],
            counts[category],
        ),
        reverse=True,
    )
    for index in range(leftover):
        floors[order[index % len(order)]] += 1
    return {category: floors[category] / 10 for category in CATEGORIES}


def _classify_with_model(items: list[tuple[int, str]]) -> dict[int, str]:
    found: dict[int, str] = {}
    for start in range(0, len(items), 25):
        found.update(_classify_batch(items[start : start + 25]))
    return found


def _classify_batch(items: list[tuple[int, str]]) -> dict[int, str]:
    category_list = ", ".join(CATEGORIES)
    blocks = "\n\n".join(f"ID {item_id}\n{text}" for item_id, text in items)
    prompt = f"""
Assign each social-media post exactly one primary theme from its OCR text.

Allowed categories, spelled exactly:
{category_list}

Use the closest category:
- Beauty: makeup, skincare, hair, nails, fragrance, or appearance-focused fashion
- Gaming: video games, gameplay, or esports
- Sports: athletic competition, teams, training, or scores
- Entertainment: film, music, television, celebrities, or comedy
- Lifestyle: daily life, travel, food, home, or hobbies outside the categories above
- Education: school, study, or teaching
- Technology: devices, software, apps, or gadgets
- Relationships: romance, friendship, family, or dating
- News: current events or reporting

Judge only the text provided. Do not infer a theme the words do not support.
If you cannot tell what the post is about, put it in the closest category.

Posts:
{blocks}

Return JSON only:
{{"classifications": [{{"id": 0, "category": "Other"}}]}}
Include every ID exactly once.
"""

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_THEME_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You classify social-media posts into one primary theme. "
                    "Use Other when the OCR text cannot be understood."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("The AI returned an empty theme classification")

    parsed = json.loads(content)
    classifications = parsed.get("classifications")
    if not isinstance(classifications, list):
        raise ValueError("The AI response did not include classifications")

    found: dict[int, str] = {}
    for entry in classifications:
        if not isinstance(entry, dict):
            continue
        try:
            item_id = int(entry.get("id"))
        except (TypeError, ValueError):
            continue
        found[item_id] = coerce_category(entry.get("category"))

    for item_id, _text in items:
        found.setdefault(item_id, "Other")
    return found
