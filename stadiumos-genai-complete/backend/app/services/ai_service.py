"""
Thin, defensive wrapper around the Google Gemini API.

Design goals
------------
* Single choke point for every outbound GenAI call -> easy to audit,
  rate-limit, log, and swap providers.
* Never raises out to the caller: on any failure (missing key, timeout,
  API error) it returns `None` so routers can fall back to deterministic,
  rule-based logic. This keeps the whole product demoable and testable
  with zero network access and zero API key (important for CI + judging).
* Retries with capped exponential backoff for transient failures.
* Strict max_tokens / timeout so a single request cannot hang the server
  or blow up cost.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Optional

from app.config import get_settings
from app.services import cache

logger = logging.getLogger("stadiumos.ai_service")
settings = get_settings()

_client = None
_client_init_failed = False


def _get_client():
    """Lazily construct the Gemini client so importing this module
    never fails even if the `google-generativeai` package or API key is
    absent (e.g. in unit tests)."""
    global _client, _client_init_failed
    if _client is not None or _client_init_failed:
        return _client
    if not settings.gemini_api_key:
        _client_init_failed = True
        return None
    try:
        import google.generativeai as genai  # imported lazily on purpose

        genai.configure(api_key=settings.gemini_api_key)
        _client = genai
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to initialize Gemini client: %s", exc)
        _client_init_failed = True
        _client = None
    return _client


async def generate(system_prompt: str, user_prompt: str, max_tokens: int = 500) -> Optional[str]:
    """Return the model's text reply, or None if GenAI is unavailable/fails.

    Callers MUST treat `None` as "use the rule-based fallback" and MUST
    NOT surface raw exceptions to end users.
    
    Results are cached in Redis with 300s TTL to improve performance.
    """
    # Generate cache key from prompts
    cache_key_data = f"{system_prompt}|{user_prompt}|{max_tokens}"
    cache_key_hash = hashlib.sha256(cache_key_data.encode()).hexdigest()[:16]
    cache_key = f"ai_response:{cache_key_hash}"
    
    # Try cache first
    cached_response = await cache.get_cached(cache_key)
    if cached_response is not None:
        logger.debug("AI response cache hit")
        return cached_response
    
    client = _get_client()
    if client is None:
        return None

    last_error: Optional[Exception] = None
    for attempt in range(settings.ai_max_retries + 1):
        try:
            model = client.GenerativeModel(
                settings.gemini_model,
                system_instruction=system_prompt,
            )
            response = await asyncio.wait_for(
                model.generate_content_async(
                    user_prompt,
                    generation_config={"max_output_tokens": max_tokens},
                ),
                timeout=settings.ai_request_timeout_seconds,
            )
            result = (getattr(response, "text", "") or "").strip() or None

            # Cache the result
            if result is not None:
                await cache.set_cached(cache_key, result, expire_seconds=300)

            return result
        except Exception as exc:  # broad on purpose: network, timeout, 4xx/5xx, SDK errors
            last_error = exc
            logger.warning("AI call failed (attempt %s/%s): %s", attempt + 1, settings.ai_max_retries + 1, exc)
            await asyncio.sleep(min(2 ** attempt * 0.5, 4))

    logger.error("AI call exhausted retries: %s", last_error)
    return None


def is_ai_available() -> bool:
    return _get_client() is not None
