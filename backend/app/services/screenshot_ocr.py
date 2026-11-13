"""Extract visible text from a screenshot with a local OCR engine."""

from __future__ import annotations

import base64
import threading

_engine = None
_engine_lock = threading.Lock()


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR

        _engine = RapidOCR()
    return _engine


def extract_text(image_data: str) -> str:
    """
    Read every text region in a data-URL image.

    Lines are returned in top-to-bottom, left-to-right order.
    """

    if not image_data.startswith("data:image/"):
        raise ValueError("Invalid image data URL")

    _, _, payload = image_data.partition(",")
    if not payload:
        raise ValueError("Image data URL is missing a payload")

    try:
        raw = base64.b64decode(payload, validate=True)
    except Exception as error:
        raise ValueError("Image data URL is not valid base64") from error

    with _engine_lock:
        result, _elapsed = _get_engine()(raw)

    if not result:
        return ""

    def reading_order(item):
        box = item[0]
        ys = [point[1] for point in box]
        xs = [point[0] for point in box]
        return (min(ys), min(xs))

    lines = []
    for _box, text, _score in sorted(result, key=reading_order):
        cleaned = str(text).strip()
        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)
