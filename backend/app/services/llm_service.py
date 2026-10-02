import json
import httpx
from ..config import settings

SYSTEM = """You are DSCE AI Academic Assistant.
Use retrieved academic material when available. Never invent syllabus content, college rules, CO/PO mappings, examination patterns, or official information.
Clearly separate general explanation from source-backed information.
If evidence is insufficient, say: I couldn't find sufficient information in the available academic materials to answer this confidently.
"""


def _build_messages(question: str, context: str, mode: str, system_prompt: str | None = None) -> list[dict]:
    prompt = (
        f"Mode: {mode}\n\n"
        f"Question: {question}\n\n"
        f"Retrieved academic context:\n{context or 'No local notes were found for this query.'}\n\n"
        "Answer using the available context first. If the context is weak or missing, say so clearly."
    )
    return [
        {"role": "system", "content": system_prompt or SYSTEM},
        {"role": "user", "content": prompt},
    ]


async def answer(question: str, context: str, mode: str, system_prompt: str | None = None) -> str:
    provider = (settings.llm_provider or "openai").lower()
    model = settings.llm_model.strip() or ("gpt-4o-mini" if provider in {"openai", "openai-compatible"} else "llama3.1")
    base_url = settings.llm_base_url.strip().rstrip("/")

    if provider in {"openai", "openai-compatible"}:
        if not base_url and not settings.llm_api_key:
            raise RuntimeError(
                "LLM provider is not configured. Set LLM_API_KEY and LLM_MODEL or provide LLM_BASE_URL in the environment."
            )
        url = (base_url or "https://api.openai.com/v1") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        payload = {
            "model": model,
            "messages": _build_messages(question, context, mode, system_prompt),
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        }
    elif provider == "ollama":
        if not base_url:
            base_url = "http://localhost:11434"
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": _build_messages(question, context, mode, system_prompt),
            "stream": False,
            "options": {"temperature": settings.llm_temperature},
        }
        headers = {"Content-Type": "application/json"}
    else:
        raise RuntimeError(f"Unsupported LLM provider '{provider}'. Use openai, openai-compatible, or ollama.")

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response else str(exc)
        raise RuntimeError(f"AI service rejected the request: {detail}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("AI service is temporarily unavailable. Please check the LLM configuration or provider connectivity.") from exc

    if provider in {"openai", "openai-compatible"}:
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("The AI provider returned an unexpected response format.")

    try:
        return data["message"]["content"].strip()
    except (KeyError, TypeError):
        raise RuntimeError("The local AI provider returned an unexpected response format.")


async def stream_answer(question: str, context: str, mode: str, system_prompt: str | None = None):
    provider = (settings.llm_provider or "openai").lower()
    model = settings.llm_model.strip() or ("gpt-4o-mini" if provider in {"openai", "openai-compatible"} else "llama3.1")
    base_url = settings.llm_base_url.strip().rstrip("/")

    if provider in {"openai", "openai-compatible"}:
        if not base_url and not settings.llm_api_key:
            raise RuntimeError(
                "LLM provider is not configured. Set LLM_API_KEY and LLM_MODEL or provide LLM_BASE_URL in the environment."
            )
        url = (base_url or "https://api.openai.com/v1") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        payload = {
            "model": model,
            "messages": _build_messages(question, context, mode, system_prompt),
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "stream": True,
        }
    elif provider == "ollama":
        if not base_url:
            base_url = "http://localhost:11434"
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": _build_messages(question, context, mode, system_prompt),
            "stream": True,
            "options": {"temperature": settings.llm_temperature},
        }
        headers = {"Content-Type": "application/json"}
    else:
        raise RuntimeError(f"Unsupported LLM provider '{provider}'. Use openai, openai-compatible, or ollama.")

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if provider in {"openai", "openai-compatible"}:
                        if line.startswith("data: "):
                            payload_line = line[6:].strip()
                            if payload_line == "[DONE]":
                                break
                            try:
                                item = json.loads(payload_line)
                            except json.JSONDecodeError:
                                continue
                            delta = item.get("choices", [{}])[0].get("delta", {}).get("content")
                            if delta:
                                yield delta
                    else:
                        if line.startswith("{"):
                            try:
                                item = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            content = item.get("message", {}).get("content")
                            if content:
                                yield content
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response else str(exc)
        raise RuntimeError(f"AI service rejected the request: {detail}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("AI service is temporarily unavailable. Please check the LLM configuration or provider connectivity.") from exc
