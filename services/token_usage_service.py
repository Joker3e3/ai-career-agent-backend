import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract(response: Any) -> dict[str, int | str | None]:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    model_name: str | None = None
    provider: str | None = None

    usage_metadata = getattr(response, "usage_metadata", None)
    if isinstance(usage_metadata, dict):
        input_tokens = _safe_int(usage_metadata.get("input_tokens"))
        output_tokens = _safe_int(usage_metadata.get("output_tokens"))
        total_tokens = _safe_int(usage_metadata.get("total_tokens"))

    response_metadata = getattr(response, "response_metadata", None)
    if isinstance(response_metadata, dict):
        model_name = response_metadata.get("model_name") or response_metadata.get("model")
        provider = response_metadata.get("model_provider") or response_metadata.get("provider")

        token_usage = response_metadata.get("token_usage")
        if isinstance(token_usage, dict):
            input_tokens = input_tokens or _safe_int(
                token_usage.get("prompt_tokens") or token_usage.get("input_tokens")
            )
            output_tokens = output_tokens or _safe_int(
                token_usage.get("completion_tokens") or token_usage.get("output_tokens")
            )
            total_tokens = total_tokens or _safe_int(token_usage.get("total_tokens"))

        usage = response_metadata.get("usage")
        if isinstance(usage, dict):
            input_tokens = input_tokens or _safe_int(
                usage.get("prompt_tokens") or usage.get("input_tokens")
            )
            output_tokens = output_tokens or _safe_int(
                usage.get("completion_tokens") or usage.get("output_tokens")
            )
            total_tokens = total_tokens or _safe_int(usage.get("total_tokens"))

    llm_output = getattr(response, "llm_output", None)
    if isinstance(llm_output, dict):
        token_usage = llm_output.get("token_usage")
        if isinstance(token_usage, dict):
            input_tokens = input_tokens or _safe_int(
                token_usage.get("prompt_tokens") or token_usage.get("input_tokens")
            )
            output_tokens = output_tokens or _safe_int(
                token_usage.get("completion_tokens") or token_usage.get("output_tokens")
            )
            total_tokens = total_tokens or _safe_int(token_usage.get("total_tokens"))

    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = (input_tokens or 0) + (output_tokens or 0)

    if model_name is None:
        model_name = os.getenv("DEEPSEEK_MODEL")

    if provider is None:
        base_url = os.getenv("DEEPSEEK_BASE_URL", "").lower()
        provider = "deepseek" if "deepseek" in base_url else "unknown"

    if total_tokens is None:
        logger.warning("[LLM_TOKEN][WARN] token usage not found")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "model_name": model_name,
        "provider": provider,
    }