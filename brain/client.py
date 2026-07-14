import base64
import io
import json
import re

import requests
from PIL import Image

from brain.prompts import SYSTEM_PROMPT, build_user_prompt
from config import (
    API_KEY,
    GEMINI_API_VERSION,
    GEMINI_MODEL,
    MAX_OUTPUT_TOKENS,
    REQUEST_TIMEOUT_SECONDS,
    THINKING_LEVEL,
)

_session = requests.Session()

def encode_image(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def clean_json_response(raw_text: str) -> dict:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(0)
    try:
        data = json.loads(raw_text)
        if "answer" not in data:
            data["answer"] = "No explicit answer provided."
        if "bbox" not in data or not isinstance(data["bbox"], list) or len(data["bbox"]) != 4:
            data["bbox"] = None
        return data
    except Exception:
        return {"answer": raw_text.strip() or "No answer generated.", "bbox": None}


def _build_payload(user_prompt: str, base64_img: str) -> dict:
    return {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": base64_img}},
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
        },
    }


def query_vision_llm(image: Image.Image, query_text: str, history: list | None = None) -> dict:
    clean_key = API_KEY.strip()
    if not clean_key:
        return {
            "answer": "Error: GEMINI_API_KEY environment variable is not set.",
            "bbox": None,
        }

    base64_img = encode_image(image)
    user_prompt = build_user_prompt(query_text, history)
    payload = _build_payload(user_prompt, base64_img)

    url = (
        f"https://generativelanguage.googleapis.com/{GEMINI_API_VERSION}"
        f"/models/{GEMINI_MODEL}:generateContent"
    )
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": clean_key,
    }

    try:
        response = _session.post(
            url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.exceptions.Timeout:
        return {"answer": "The request timed out. Check your connection and try again.", "bbox": None}
    except requests.exceptions.ConnectionError:
        return {"answer": "Couldn't reach Gemini. Check your internet connection.", "bbox": None}

    if response.status_code in (401, 403):
        return {"answer": "Authentication failed — check your GEMINI_API_KEY.", "bbox": None}
    if response.status_code == 503:
        return {"answer": "Gemini is at capacity right now. Try again in a moment.", "bbox": None}
    if response.status_code == 429:
        return {"answer": "Rate limited — slow down requests a little.", "bbox": None}

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(response.text)
        return {"answer": f"Gemini returned an error ({response.status_code}).", "bbox": None}

    try:
        res_data = response.json()
        content = res_data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError):
        print(response.text)
        return {"answer": "Received an unexpected response format from Gemini.", "bbox": None}

    return clean_json_response(content)