"""
Shared Gemini caller used by ai_helper.py and vision.py.

Why this exists: Gemini's free tier regularly answers 503 ("high demand") or 429
(rate limit) for a few seconds at a time. Instead of showing that raw error to
the user, we retry briefly, fall back to other Gemini models, and only then give
up with a short, readable message.
"""
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
FALLBACK_MODELS = [
    m.strip()
    for m in os.environ.get("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-2.5-flash-lite").split(",")
    if m.strip()
]

# Total time we're willing to spend on one AI request (retries + fallback models included).
# Keeps us safely inside a serverless function's time limit (vercel.json sets maxDuration=60).
TIME_BUDGET_SECONDS = float(os.environ.get("GEMINI_TIME_BUDGET", "40"))

RETRY_STATUSES = {429, 500, 502, 503, 504}
ATTEMPTS_PER_MODEL = 2
RETRY_DELAY_SECONDS = 1.5

BUSY_MESSAGE = "The AI service is very busy right now. Please try again in a minute."
RATE_LIMIT_MESSAGE = "The free AI limit was reached for the moment. Please wait a minute and try again."


def available() -> bool:
    return bool(API_KEY)


def _url(model: str) -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _google_message(resp) -> str:
    """Pull just the human-readable message out of Google's JSON error body."""
    try:
        return resp.json().get("error", {}).get("message", "") or ""
    except Exception:
        return ""


def _extract_text(data: dict) -> str:
    """Join the visible text parts (skips 'thinking' parts)."""
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return ""
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def generate(parts: list[dict], max_tokens: int, temperature: float = 0.3, json_mode: bool = False) -> str:
    """Send `parts` to Gemini and return the text reply. Raises RuntimeError with a friendly message."""
    if not API_KEY:
        raise RuntimeError(
            "AI features need a free GEMINI_API_KEY (see backend/.env.example). "
            "Get one at https://aistudio.google.com/apikey."
        )

    generation_config = {"temperature": temperature, "maxOutputTokens": max_tokens}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
    payload = {"contents": [{"parts": parts}], "generationConfig": generation_config}

    models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    saw_rate_limit = False
    deadline = time.monotonic() + TIME_BUDGET_SECONDS

    def nap(seconds: float):
        # only sleep if there's still time left to make another attempt afterwards
        if deadline - time.monotonic() > seconds + 5:
            time.sleep(seconds)

    for model in models:
        for attempt in range(ATTEMPTS_PER_MODEL):
            remaining = deadline - time.monotonic()
            if remaining < 4:
                raise RuntimeError(RATE_LIMIT_MESSAGE if saw_rate_limit else BUSY_MESSAGE)
            try:
                resp = requests.post(
                    _url(model), params={"key": API_KEY}, json=payload, timeout=min(25, remaining)
                )
            except requests.RequestException:
                nap(RETRY_DELAY_SECONDS)
                continue

            if resp.status_code == 200:
                data = resp.json()
                text = _extract_text(data).strip()
                if text:
                    return text
                # Empty reply (e.g. the token budget ran out while "thinking") -> try again / next model
                nap(RETRY_DELAY_SECONDS)
                continue

            if resp.status_code == 404:
                break  # this model name isn't available for this key -> next model

            if resp.status_code in RETRY_STATUSES:
                saw_rate_limit = saw_rate_limit or resp.status_code == 429
                if attempt < ATTEMPTS_PER_MODEL - 1:
                    nap(RETRY_DELAY_SECONDS * (attempt + 1))
                continue

            # 400 / 401 / 403 etc: retrying won't help (bad key, bad request...)
            detail = _google_message(resp)
            raise RuntimeError(f"Gemini rejected the request ({resp.status_code}). {detail}".strip())

    raise RuntimeError(RATE_LIMIT_MESSAGE if saw_rate_limit else BUSY_MESSAGE)
