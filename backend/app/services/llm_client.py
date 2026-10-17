"""A small OpenAI client: text in, text out, and embeddings.

Plain HTTP through httpx rather than the openai package, so the image gains no
dependency for two endpoints. Used in two places:

  * live, by explanation_service (Explain in my code, the compiler-error
    explainer, the similar worked example), and
  * offline, by dev_tools/mutation/generate_base_programs.py, which asks for
    correct beginner methods to mutate.

Every call either returns text or raises LLMUnavailable. Callers decide what
to fall back to; nothing here retries forever or logs a key.
"""

from __future__ import annotations

from typing import List, Optional

import httpx

from app.core.config import get_settings

OPENAI_BASE_URL = "https://api.openai.com/v1"


class LLMUnavailable(RuntimeError):
    """No key, the network failed, or the model gave no answer."""


def configured() -> bool:
    return bool(get_settings().openai_api_key)


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _output_text(body: dict) -> str:
    # The Responses API returns a list of output items; the answer is the
    # output_text parts of the message items. Reasoning items carry none.
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    parts: List[str] = []
    for item in body.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                parts.append(content["text"])
    return "".join(parts)


def complete(
    prompt: str,
    *,
    instructions: Optional[str] = None,
    max_output_tokens: int = 1200,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    timeout: Optional[float] = None,
    json_output: bool = False,
) -> str:
    settings = get_settings()
    key = api_key or settings.openai_api_key
    if not key:
        raise LLMUnavailable("OPENAI_API_KEY is not set")

    payload: dict = {
        "model": model or settings.openai_model,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }
    if instructions:
        payload["instructions"] = instructions
    effort = reasoning_effort if reasoning_effort is not None else settings.openai_reasoning_effort
    if effort:
        payload["reasoning"] = {"effort": effort}
    if json_output:
        payload["text"] = {"format": {"type": "json_object"}}

    try:
        response = httpx.post(
            f"{OPENAI_BASE_URL}/responses",
            json=payload,
            headers=_headers(key),
            timeout=timeout or settings.openai_timeout_seconds,
        )
    except httpx.HTTPError as error:
        raise LLMUnavailable(f"request failed: {type(error).__name__}") from error

    if response.status_code != 200:
        raise LLMUnavailable(f"OpenAI answered {response.status_code}")
    text = _output_text(response.json()).strip()
    if not text:
        raise LLMUnavailable("empty answer")
    return text


def embed(texts: List[str], *, api_key: Optional[str] = None, timeout: Optional[float] = None,
          dimensions: Optional[int] = None) -> List[List[float]]:
    settings = get_settings()
    key = api_key or settings.openai_api_key
    if not key:
        raise LLMUnavailable("OPENAI_API_KEY is not set")
    try:
        response = httpx.post(
            f"{OPENAI_BASE_URL}/embeddings",
            json={"model": settings.openai_embedding_model, "input": texts,
                  **({"dimensions": dimensions} if dimensions else {})},
            headers=_headers(key),
            timeout=timeout or settings.openai_timeout_seconds,
        )
    except httpx.HTTPError as error:
        raise LLMUnavailable(f"request failed: {type(error).__name__}") from error
    if response.status_code != 200:
        raise LLMUnavailable(f"OpenAI answered {response.status_code}")
    data = sorted(response.json().get("data") or [], key=lambda item: item.get("index", 0))
    return [item["embedding"] for item in data]
