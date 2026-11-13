"""Group consecutive screenshots that show the same social post."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher

from app.services.screenshot_ocr import extract_text

# Chrome that is the app, not the post. Matched after case and whitespace
# normalization, either as a whole line or as a token.
_UI_LINES = frozenset({
    "for you",
    "following",
    "follow",
    "like",
    "likes",
    "liked",
    "comment",
    "comments",
    "share",
    "shares",
    "send",
    "home",
    "search",
    "reels",
    "reel",
    "explore",
    "inbox",
    "shop",
    "live",
    "sponsored",
    "audio",
    "original audio",
    "add comment",
    "say something",
    "watch more",
    "see more",
    "more",
    "save",
    "saved",
    "repost",
    "stitch",
    "duet",
    "subscribe",
    "notifications",
    "profile",
    "friends",
    "discover",
    "create",
    "reply",
    "replies",
    "message",
    "messages",
    "story",
    "stories",
    "views",
    "view",
    "watch again",
    "not interested",
    "hide",
    "report",
    "copy link",
    "close",
    "back",
    "next",
    "skip",
    "log in",
    "sign up",
    "open app",
})

_UI_TOKENS = frozenset({
    "like",
    "likes",
    "liked",
    "comment",
    "comments",
    "share",
    "shares",
    "follow",
    "following",
    "followers",
    "follower",
    "repost",
    "reposts",
    "send",
    "sent",
    "save",
    "saved",
    "reply",
    "replies",
    "home",
    "search",
    "reels",
    "reel",
    "explore",
    "inbox",
    "shop",
    "live",
    "sponsored",
    "subscribe",
    "views",
    "view",
    "audio",
    "story",
    "stories",
    "stitch",
    "duet",
    "notifications",
    "profile",
})

# Words that show up in unrelated captions and must not count as a match.
_STOPWORDS = frozenset({
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "from",
    "is",
    "it",
    "this",
    "that",
    "you",
    "your",
    "my",
    "me",
    "we",
    "our",
    "so",
    "be",
    "are",
    "was",
    "were",
    "as",
    "if",
    "not",
    "no",
    "do",
    "did",
    "have",
    "has",
    "i",
    "im",
    "its",
    "amp",
})

_COUNT = re.compile(
    r"^(?:\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)[kmb]?$"
    r"|^\d{1,2}:\d{2}(?::\d{2})?$"
    r"|^\d+(?:\.\d+)?%$"
)
_TOKEN = re.compile(r"[a-z0-9']+")
_HANDLE = re.compile(r"@([A-Za-z0-9][A-Za-z0-9._]{1,29})")
_HANDLE_LINE = re.compile(r"^@?[A-Za-z0-9]*[._][A-Za-z0-9._]{1,28}$")
_DISPLAY_WORD = re.compile(r"[A-Za-z][A-Za-z'.-]{1,29}")


def _squash_line(line: str) -> str:
    text = unicodedata.normalize("NFKC", line).lower()
    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("`", "'")
    )
    text = re.sub(r"[^\w\s']", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _is_count(token: str) -> bool:
    return bool(_COUNT.fullmatch(token))


def _content_lines(raw_text: str) -> list[str]:
    lines = []
    for raw_line in raw_text.splitlines():
        line = _squash_line(raw_line)
        if not line or line in _UI_LINES:
            continue
        tokens = line.split()
        if all(token in _UI_TOKENS or _is_count(token) for token in tokens):
            continue
        if line.startswith(("liked by ", "view all ")):
            continue
        if not lines or lines[-1] != line:
            lines.append(line)
    return lines


def _strip_repeated_interface(lines_per_shot: list[list[str]]) -> list[list[str]]:
    """
    Drop a short line when it disappears and comes back later.

    A caption that stays on screen for one post is a single run and is kept.
    A control such as a tab label that returns on later posts is removed.
    """

    positions: dict[str, list[int]] = defaultdict(list)
    for index, lines in enumerate(lines_per_shot):
        for line in set(lines):
            if len(line.split()) <= 4:
                positions[line].append(index)

    chrome = set()
    for line, indexes in positions.items():
        if len(indexes) < 3:
            continue
        gaps = sum(
            1 for earlier, later in zip(indexes, indexes[1:])
            if later - earlier > 1
        )
        if gaps >= 1 and indexes[-1] - indexes[0] >= 4:
            chrome.add(line)

    return [
        [line for line in lines if line not in chrome]
        for lines in lines_per_shot
    ]


def _content_tokens(text: str) -> list[str]:
    tokens = []
    for token in _TOKEN.findall(text):
        if len(token) < 2 or token in _STOPWORDS or token in _UI_TOKENS:
            continue
        if _is_count(token):
            continue
        tokens.append(token)
    return tokens


def _widespread_tokens(token_lists: list[list[str]]) -> set[str]:
    """
    Tokens present on at least half of a longer recording.

    These are usually persistent chrome. They are ignored while comparing
    posts, then a near-duplicate check still joins frames of one post whose
    caption fills the whole recording.
    """

    total = len(token_lists)
    if total < 4:
        return set()

    counts = Counter()
    for tokens in token_lists:
        counts.update(set(tokens))

    return {token for token, count in counts.items() if count / total >= 0.5}


def _has_distinctive_token(text: str) -> bool:
    return any(len(token) > 2 for token in _content_tokens(text))


def _creator_key(name: str) -> str:
    name = unicodedata.normalize("NFKC", name).lower().lstrip("@")
    return re.sub(r"[^a-z0-9]", "", name)


def _valid_creator(key: str) -> bool:
    if len(key) < 3 or len(key) > 30 or not any(char.isalpha() for char in key):
        return False
    return key not in _STOPWORDS and key not in _UI_TOKENS and key not in _UI_LINES


def _remember_creator(found: list[dict], label: str) -> None:
    key = _creator_key(label)
    if not _valid_creator(key) or any(item["key"] == key for item in found):
        return
    readable = re.sub(r"\s+", " ", label.strip().lstrip("@")).strip(" .")
    found.append({"key": key, "label": readable})


def _creator_of(raw_text: str) -> dict:
    """
    The account name on a screenshot, when one is visible.

    Handles and username-shaped lines count. A caption sentence does not.
    """

    handles: list[dict] = []
    names: list[dict] = []
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        squashed = _squash_line(stripped)
        if not squashed or squashed.startswith(("liked by ", "view all ")):
            continue
        if squashed in _UI_LINES or _is_count(squashed.replace(" ", "")):
            continue

        for handle in _HANDLE.findall(stripped):
            _remember_creator(handles, handle)

        first = stripped.split()[0]
        if _HANDLE_LINE.fullmatch(first) and not _is_count(first.lower()):
            _remember_creator(names, first)
            continue

        words = stripped.split()
        single_name = (
            len(words) == 1
            and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{2,29}", words[0]) is not None
        )
        display_name = (
            2 <= len(words) <= 3
            and all(_DISPLAY_WORD.fullmatch(word) for word in words)
            and any(word[0].isupper() for word in words)
            and not all(word.isupper() for word in words)
            and all(_squash_line(word) not in _STOPWORDS for word in words)
            and all(_squash_line(word) not in _UI_TOKENS for word in words)
        )
        if single_name or display_name:
            _remember_creator(names, " ".join(words))

    if handles:
        return handles[0]
    if names:
        return names[0]
    return {"key": "", "label": ""}


def texts_match(
    left: str,
    right: str,
    ignored_tokens: set[str] | None = None,
) -> bool:
    """
    Decide whether two normalized OCR strings describe the same post.

    Overlap has to survive removal of interface words and words that are
    common across the recording. A shared "like" or "the" is not enough.
    """

    if not left or not right:
        return False

    ignored = ignored_tokens or set()
    left_tokens = [token for token in _content_tokens(left) if token not in ignored]
    right_tokens = [token for token in _content_tokens(right) if token not in ignored]

    # A raw character match is only a shortcut for the same short caption.
    # Longer strings can look alike while naming different posts.
    ratio = SequenceMatcher(None, left, right).ratio()
    if len(left_tokens) < 2 or len(right_tokens) < 2:
        return (
            ratio >= 0.92
            and _has_distinctive_token(left)
            and _has_distinctive_token(right)
        )

    left_set = set(left_tokens)
    right_set = set(right_tokens)
    shared = left_set & right_set
    if len(shared) < 2:
        return False

    jaccard = len(shared) / len(left_set | right_set)
    containment = len(shared) / min(len(left_set), len(right_set))
    token_ratio = SequenceMatcher(
        None,
        " ".join(left_tokens),
        " ".join(right_tokens),
    ).ratio()
    strong_overlap = jaccard >= 0.55 or containment >= 0.8
    return token_ratio >= 0.62 and strong_overlap


def _filename(screenshot: dict, position: int, timestamp: float) -> str:
    filename = str(screenshot.get("filename") or "").strip()
    if filename:
        return filename
    return f"screenshot_{position:04d}_t{timestamp:.2f}s.jpg"


def _ocr_text_for(screenshot: dict) -> str:
    if "ocr_text" in screenshot and screenshot["ocr_text"] is not None:
        return str(screenshot["ocr_text"])
    image = screenshot.get("image")
    if not image:
        return ""
    return extract_text(str(image))


def cluster_screenshots(
    screenshots: list[dict],
    max_gap_seconds: float = 12.0,
) -> list[dict]:
    """
    Group screenshots into potential posts.

    Only consecutive screenshots captured within max_gap_seconds can join a
    cluster. They join when the same creator is visible, or when their OCR
    text matches. Each screenshot keeps its filename, timestamp, raw OCR
    text, normalized text, and creator when one was found.
    """

    if max_gap_seconds <= 0:
        raise ValueError("max_gap_seconds must be greater than zero")

    ordered = sorted(
        enumerate(screenshots),
        key=lambda item: (float(item[1].get("timestamp_seconds", 0.0)), item[0]),
    )

    prepared = []
    for frame_index, screenshot in ordered:
        timestamp = round(float(screenshot.get("timestamp_seconds", 0.0)), 2)
        ocr_text = _ocr_text_for(screenshot)
        prepared.append({
            "frame_index": frame_index,
            "filename": _filename(screenshot, frame_index + 1, timestamp),
            "timestamp_seconds": timestamp,
            "ocr_text": ocr_text,
            "creator": _creator_of(ocr_text),
        })

    line_groups = [_content_lines(item["ocr_text"]) for item in prepared]
    normalized_lines = _strip_repeated_interface(line_groups)
    for item, lines in zip(prepared, normalized_lines):
        item["normalized_text"] = " ".join(lines)

    ignored_tokens = _widespread_tokens([
        _content_tokens(item["normalized_text"]) for item in prepared
    ])

    clusters: list[list[dict]] = []
    for item in prepared:
        if not clusters:
            clusters.append([item])
            continue

        previous = clusters[-1][-1]
        gap = item["timestamp_seconds"] - previous["timestamp_seconds"]
        close_enough = 0 <= gap <= max_gap_seconds
        same_creator = (
            previous["creator"]["key"] != ""
            and previous["creator"]["key"] == item["creator"]["key"]
        )
        if close_enough and (
            same_creator
            or texts_match(
                previous["normalized_text"],
                item["normalized_text"],
                ignored_tokens,
            )
        ):
            clusters[-1].append(item)
        else:
            clusters.append([item])

    grouped = []
    for cluster_id, screenshots_in_cluster in enumerate(clusters, start=1):
        for shot in screenshots_in_cluster:
            shot["creator"] = shot["creator"]["label"]
        grouped.append({
            "cluster_id": cluster_id,
            "screenshots": screenshots_in_cluster,
        })
    return grouped
