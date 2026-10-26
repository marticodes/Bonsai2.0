"""Synthetic social-media post generator for youth-media research (ages 10–16)."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import zipfile
from typing import Any, Literal

import httpx
from openai import AsyncOpenAI

Platform = Literal["snapchat", "instagram", "tiktok"]
Format = Literal["text", "image", "video"]

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You create ONE synthetic social media post for academic research on how
people aged 10–16 experience Snapchat, Instagram, and TikTok.

Hard rules:
- Invent a fully fictional minor (first name + vague age only). Never copy
  real creators, influencers, classmates, schools, brands-as-people, or
  identifiable photos/likenesses.
- Strongly concerning themes (FOMO, exclusion, appearance pressure, peer
  drama, risky trends) may appear when relevant.
- Match the selected platform's native style: captions, slang, emojis, pacing, and (for media prompts) candid phone-photo or vertical short-form aesthetics.
- Vary wording naturally; do not reuse stock templates.
- Some posts should contain subtle warning signs or contextual clues that a parent might overlook or interpret differently from a teenager. Examples include a friend insisting on secrecy, pressure to prove loyalty, an invitation to move a conversation elsewhere, a humiliating joke disguised as humor, or a risky trend presented as normal.

Return ONLY valid JSON with these keys:
{
  "username": "fictional handle without @",
  "display_name": "first name only",
  "age": 10-16 integer,
  "caption": "platform-native caption text",
  "image_prompt": "detailed image prompt or empty string",
  "video_prompt": "detailed vertical video prompt or empty string"
}
"""


def _build_user_prompt(
    platform: Platform,
    fmt: Format,
    topic: str,
    tone: str,
    context: str,
    values: str,
    constraints: str,
) -> str:
    media_instruction = {
        "text": "Format is TEXT ONLY. Leave image_prompt and video_prompt empty.",
        "image": (
            "Format is IMAGE + caption. Write a candid phone-photo style "
            "image_prompt (no real people/celebrities, no readable logos). "
            "Leave video_prompt empty."
        ),
        "video": (
            "Format is a ~10 second vertical short-form video + caption. "
            "Write a video_prompt describing camera, motion, setting, and "
            "teen-appropriate action (no real people/celebrities). "
            "Leave image_prompt empty."
        ),
    }[fmt]

    return f"""
Platform: {platform}
{media_instruction}

Topic: {topic}
Tone: {tone}
Context: {context}
Values to reflect: {values}
Optional constraints: {constraints or "none"}
"""


async def _llm_plan(
    platform: Platform,
    fmt: Format,
    topic: str,
    tone: str,
    context: str,
    values: str,
    constraints: str,
) -> dict[str, Any]:
    response = await client.chat.completions.create(
        model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
        temperature=0.95,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    platform, fmt, topic, tone, context, values, constraints
                ),
            },
        ],
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


async def _generate_image(prompt: str) -> tuple[bytes, str]:
    result = await client.images.generate(
        model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        prompt=(
            "Authentic candid smartphone photo aesthetic for a synthetic "
            "teen social-media research stimulus. No real celebrities, no "
            "readable brand logos, no sexualized content. "
            f"{prompt}"
        ),
        size="1024x1536",
        quality="medium",
        output_format="png",
    )
    b64 = result.data[0].b64_json
    if not b64:
        raise RuntimeError("Image API returned no image data")
    return base64.b64decode(b64), "image/png"


async def _generate_video(prompt: str) -> tuple[bytes, str]:
    """Generate a short vertical video via fal.ai (OpenAI Sora API is shut down)."""
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        raise RuntimeError(
            "Video generation requires FAL_KEY. OpenAI Sora / Videos API "
            "was shut down; set FAL_KEY for fal.ai text-to-video."
        )

    model = os.getenv(
        "FAL_VIDEO_MODEL",
        "fal-ai/minimax/video-01",
    )
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }
    body = {
        "prompt": (
            "Vertical 9:16 smartphone video, about 10 seconds, candid "
            "teen social-media style, synthetic research stimulus, no "
            "real celebrities or sexualized content. "
            f"{prompt}"
        ),
        "prompt_optimizer": True,
    }

    async with httpx.AsyncClient(timeout=300.0) as http:
        submit = await http.post(
            f"https://queue.fal.run/{model}",
            headers=headers,
            json=body,
        )
        submit.raise_for_status()
        job = submit.json()
        status_url = job.get("status_url") or (
            f"https://queue.fal.run/{model}/requests/{job['request_id']}/status"
        )
        result_url = job.get("response_url") or (
            f"https://queue.fal.run/{model}/requests/{job['request_id']}"
        )

        for _ in range(90):
            status_resp = await http.get(status_url, headers=headers)
            status_resp.raise_for_status()
            status = status_resp.json()
            state = status.get("status")
            if state == "COMPLETED":
                break
            if state == "FAILED":
                raise RuntimeError(f"Video generation failed: {status}")
            await asyncio.sleep(2)
        else:
            raise RuntimeError("Video generation timed out")

        result_resp = await http.get(result_url, headers=headers)
        result_resp.raise_for_status()
        result = result_resp.json()

        video_url = (
            (result.get("video") or {}).get("url")
            or result.get("video_url")
            or (result.get("output") or {}).get("url")
        )
        if not video_url:
            raise RuntimeError(f"No video URL in fal response: {result}")

        media = await http.get(video_url)
        media.raise_for_status()
        return media.content, "video/mp4"


def _zip_files(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _package_download(
    fmt: Format,
    caption: str,
    media_bytes: bytes | None,
    media_mime: str | None,
) -> dict[str, str]:
    caption_bytes = caption.encode("utf-8")

    if fmt == "text":
        return {
            "filename": "post.txt",
            "mime": "text/plain; charset=utf-8",
            "base64": base64.b64encode(caption_bytes).decode("ascii"),
        }

    if fmt == "image":
        assert media_bytes is not None
        if caption.strip():
            payload = _zip_files(
                {"caption.txt": caption_bytes, "post.png": media_bytes}
            )
            return {
                "filename": "post.zip",
                "mime": "application/zip",
                "base64": base64.b64encode(payload).decode("ascii"),
            }
        return {
            "filename": "post.png",
            "mime": "image/png",
            "base64": base64.b64encode(media_bytes).decode("ascii"),
        }

    # video
    assert media_bytes is not None
    if caption.strip():
        payload = _zip_files(
            {"caption.txt": caption_bytes, "post.mp4": media_bytes}
        )
        return {
            "filename": "post.zip",
            "mime": "application/zip",
            "base64": base64.b64encode(payload).decode("ascii"),
        }
    return {
        "filename": "post.mp4",
        "mime": media_mime or "video/mp4",
        "base64": base64.b64encode(media_bytes).decode("ascii"),
    }


async def generate_post(
    platform: Platform,
    fmt: Format,
    topic: str,
    tone: str,
    context: str,
    values: str,
    constraints: str = "",
) -> dict[str, Any]:
    plan = await _llm_plan(
        platform, fmt, topic, tone, context, values, constraints
    )

    caption = str(plan.get("caption") or "").strip()
    media_bytes: bytes | None = None
    media_mime: str | None = None
    media_base64: str | None = None

    if fmt == "image":
        image_prompt = str(plan.get("image_prompt") or caption)
        media_bytes, media_mime = await _generate_image(image_prompt)
        media_base64 = base64.b64encode(media_bytes).decode("ascii")
    elif fmt == "video":
        video_prompt = str(plan.get("video_prompt") or caption)
        media_bytes, media_mime = await _generate_video(video_prompt)
        media_base64 = base64.b64encode(media_bytes).decode("ascii")

    download = _package_download(fmt, caption, media_bytes, media_mime)

    age_raw = plan.get("age")
    try:
        age = int(age_raw) if age_raw is not None else None
        if age is not None and not 10 <= age <= 16:
            age = None
    except (TypeError, ValueError):
        age = None

    return {
        "platform": platform,
        "format": fmt,
        "username": plan.get("username") or "anon_teen",
        "display_name": plan.get("display_name") or "Alex",
        "age": age,
        "caption": caption,
        "media_mime": media_mime,
        "media_base64": media_base64,
        "download": download,
    }
