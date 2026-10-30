import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI
from . import config

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_client() -> OpenAI:
    if not config.API_KEY:
        raise RuntimeError("NEBIUS_API_KEY is missing. Add it to backend/.env and restart.")
    return OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL, timeout=90.0, max_retries=1)

def get_models() -> list[str]:
    client = get_client()
    return sorted({m.id for m in client.models.list().data}, key=str.lower)

def get_model_id() -> str:
    if not config.MODEL_ID:
        raise RuntimeError("NEBIUS_MODEL is not configured. Select an exact model ID from /api/models and add it to backend/.env.")
    return config.MODEL_ID

def chat(system: str, user: str, max_tokens: int = 1800) -> str:
    client = get_client()
    model = get_model_id()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.15,
        max_tokens=max_tokens,
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("The selected model returned an empty response.")
    return text

def extract_json(text: str) -> Any:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise ValueError("Model response did not contain valid JSON.")

def new_id() -> str:
    return uuid.uuid4().hex
