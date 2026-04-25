"""Local LLM client — supports Hermes Agent (local), Ollama, and llama.cpp."""

import json
import subprocess
import requests
from typing import Generator
import config_local as config

# ═══════════════════════════════════════════════════════════════════════════════
# Backend 1: Local Hermes Agent (assumes Hermes Agent runs locally on port 8000)
# ═══════════════════════════════════════════════════════════════════════════════


def stream_response_hermes(user_text: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    """Stream from a locally-running Hermes Agent (OpenAI-compatible endpoint)."""
    url = f"{config.HERMES_LOCAL_URL}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if config.HERMES_LOCAL_TOKEN:
        headers["Authorization"] = f"Bearer {config.HERMES_LOCAL_TOKEN}"

    messages = [{"role": "system", "content": config.LOCAL_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    body = {"model": "hermes-local", "stream": True, "messages": messages, "max_tokens": 300}

    resp = requests.post(url, json=body, headers=headers, stream=True, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Hermes local error {resp.status_code}: {resp.text[:200]}")

    for line in resp.iter_lines():
        if not line:
            continue
        if line.startswith(b"data:"):
            data_str = line[5:].strip()
            if data_str == b"[DONE]":
                break
            try:
                data = json.loads(data_str)
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
            except json.JSONDecodeError:
                continue


# ═══════════════════════════════════════════════════════════════════════════════
# Backend 2: Ollama
# ═══════════════════════════════════════════════════════════════════════════════


def stream_response_ollama(user_text: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    """Stream from Ollama (http://localhost:11434)."""
    url = f"{config.OLLAMA_URL}/api/chat"
    messages = []
    if history:
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
    else:
        messages = [{"role": "system", "content": config.LOCAL_SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": user_text})

    body = {"model": config.OLLAMA_MODEL, "messages": messages, "stream": True}

    resp = requests.post(url, json=body, stream=True, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama error {resp.status_code}: {resp.text[:200]}")

    for line in resp.iter_lines():
        if not line:
            continue
        try:
            data = json.loads(line)
            if "message" in data:
                content = data["message"].get("content", "")
                if content:
                    yield content
            if data.get("done"):
                break
        except json.JSONDecodeError:
            continue


# ═══════════════════════════════════════════════════════════════════════════════
# Backend 3: llama.cpp OpenAI-compatible server
# ═══════════════════════════════════════════════════════════════════════════════


def stream_response_llamacpp(user_text: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    """Stream from llama.cpp /v1/chat/completions endpoint."""
    return stream_response_hermes(user_text, history)  # same format


# ═══════════════════════════════════════════════════════════════════════════════
# Dispatcher
# ═══════════════════════════════════════════════════════════════════════════════


def stream_response(user_text: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    backend = config.LOCAL_BACKEND
    if backend == "ollama":
        yield from stream_response_ollama(user_text, history)
    elif backend == "llamacpp":
        yield from stream_response_llamacpp(user_text, history)
    else:  # hermes (default)
        yield from stream_response_hermes(user_text, history)


def check_health() -> bool:
    try:
        url = f"{config.HERMES_LOCAL_URL}/health"
        resp = requests.get(url, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False
