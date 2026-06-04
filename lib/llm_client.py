from __future__ import annotations

import json
import os
import re

from openai import OpenAI

MODEL_ID = "gpt-4.1-nano"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        _client = OpenAI(api_key=key)
    return _client


def chat(system: str, user: str, max_tokens: int = 2048) -> str:
    response = _get_client().chat.completions.create(
        model=MODEL_ID,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def chat_json(system: str, user: str, max_tokens: int = 2048, retries: int = 2) -> dict:
    """Call the model and parse the response as JSON. Retries on parse failure."""
    for attempt in range(retries + 1):
        suffix = "\n\nReturn ONLY valid JSON with no markdown fences, no commentary." if attempt > 0 else ""
        raw = chat(system, user + suffix, max_tokens)
        try:
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            if attempt == retries:
                raise ValueError(f"Model returned invalid JSON after {retries + 1} attempts:\n{raw}")
    return {}
