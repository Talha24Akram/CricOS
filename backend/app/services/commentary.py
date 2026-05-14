from __future__ import annotations

import hashlib
import json
from functools import lru_cache

from anthropic import Anthropic

from app.core.config import settings


def _prompt_for_state(state: dict, tone: str) -> str:
    return (
        "Generate one line of cricket commentary. Keep it under 22 words. "
        f"Tone: {tone}. State: {json.dumps(state, ensure_ascii=True)}"
    )


@lru_cache(maxsize=2048)
def _cache_key_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_commentary_line(match_state: dict, tone: str = "normal") -> str:
    if not settings.anthropic_api_key:
        return "Commentary unavailable: set ANTHROPIC_API_KEY in backend/.env"

    payload = json.dumps({"tone": tone, "state": match_state}, sort_keys=True)
    _cache_key_hash(payload)

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=64,
        temperature=0.7,
        messages=[{"role": "user", "content": _prompt_for_state(match_state, tone)}],
    )
    text_blocks = [b.text for b in response.content if getattr(b, "type", "") == "text"]
    return (" ".join(text_blocks)).strip()
