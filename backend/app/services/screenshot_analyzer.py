import json
import os

from openai import OpenAI


def analyze_screenshot(image_data: str) -> dict:
    """
    Interpret the potential meaning and values communicated
    by a social media screenshot.
    """

    if not image_data.startswith("data:image/"):
        raise ValueError("Invalid image data URL")

    prompt = """
You are a researcher studying the values and messages communicated
through social media content.

Your task is NOT to describe the image. Your task is to interpret
what the content may communicate to its audience.

Analyze the screenshot and return a JSON object with this structure:

{
    "interpretation": "A concise interpretation of the main message.",
    "values": [
        {
            "value": "The value, belief, attitude, or ideal identified",
            "type": "explicit or inferred",
            "direction": "promotes, normalizes, questions, criticizes, or unclear",
            "evidence": "Specific words or visual elements supporting the interpretation",
            "confidence": "high, medium, or low"
        }
    ],
    "possible_norms": [
        "A social norm or expectation the content may reinforce or challenge"
    ],
    "uncertainty": "The most important limitation of this interpretation"
}

ANALYSIS PRINCIPLES:

1. INTERPRET MEANING
Focus on the message, underlying assumptions, ideals, attitudes,
and perspectives communicated by the content. Do not narrate
what people or objects look like.

2. IDENTIFY VALUES
Consider values such as beauty, success, popularity, authenticity,
independence, belonging, consumerism, social status, gender roles,
cultural identity, competition, kindness, or conformity.
These are examples, not a checklist. Identify other values when
supported by the content.

3. DO NOT FORCE INTERPRETATIONS
Return only values supported by evidence. If no meaningful value
can be identified, return an empty values array.

4. DISTINGUISH EVIDENCE FROM INFERENCE
An explicit value is directly communicated through words or actions.
An inferred value is a plausible interpretation of the message.
Do not present an inference as an established fact.

5. EXPLAIN THE DIRECTION
Determine whether a value appears to be promoted, normalized,
questioned, or criticized. Do not assume that showing something
means endorsing it.

6. BE CRITICAL BUT NEUTRAL
Consider implied ideals and social expectations, including subtle
messages about what is desirable, successful, normal, or acceptable.
Do not automatically classify content as positive or negative.

7. ACKNOWLEDGE MISSING CONTEXT
You are analyzing one screenshot, not the complete video.
Use visible text, captions, and visual evidence. Do not invent
dialogue, intentions, events, or messages that cannot be established.
If the meaning depends on missing audio or surrounding scenes,
lower your confidence and state the limitation.

8. KEEP IT SHORT
The interpretation must be at most two sentences.
Return at most three values and two possible norms.
Keep evidence concise.
Use empty arrays when appropriate.
Return valid JSON only, without Markdown or additional commentary.
"""

    client = OpenAI()

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a critical, careful researcher interpreting "
                    "values communicated through social media. "
                    "Distinguish evidence from inference and never "
                    "invent unsupported meanings."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data,
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=700,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The AI returned an empty response")

    return json.loads(content)