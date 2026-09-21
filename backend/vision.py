"""
Ingredient detection from a photo.

Uses Google's Gemini API, which has a genuinely free tier (no credit card
required) at ai.google.dev. If no GEMINI_API_KEY is set, this module tells
the frontend to fall back to manual ingredient entry -- the app is fully
usable with zero API keys, you just type/check off ingredients instead of
having them auto-detected from the photo.
"""
import base64
import json
import re

import gemini

PROMPT = (
    "You are looking at a photo of a fridge, pantry, or kitchen counter. "
    "List every distinct food ingredient you can visually identify. "
    "Use simple, singular, lowercase common names (e.g. 'tomato' not "
    "'tomatoes', 'egg' not 'eggs carton'). Ignore non-food items, brand "
    "names, and packaging text. Respond with ONLY a JSON array of strings, "
    "nothing else, e.g. [\"egg\", \"milk\", \"carrot\"]."
)


def vision_available() -> bool:
    return gemini.available()


def detect_ingredients(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[str]:
    """Returns a list of detected ingredient names. Raises RuntimeError on failure."""
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    text = gemini.generate(
        [{"text": PROMPT}, {"inline_data": {"mime_type": mime_type, "data": b64_image}}],
        max_tokens=1500,
        temperature=0.2,
    )

    # Strip markdown code fences if the model added them despite instructions
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()

    try:
        items = json.loads(text)
        if not isinstance(items, list):
            raise ValueError
        return [str(i).strip().lower() for i in items if str(i).strip()]
    except (json.JSONDecodeError, ValueError):
        # Last-resort fallback: pull comma/newline separated words out of the text
        parts = re.split(r"[,\n]", text)
        return [p.strip().lower().strip('"[]') for p in parts if p.strip()]
