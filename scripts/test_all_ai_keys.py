"""驗證 .env 內所有 AI API key（Gemini 主/備、OpenAI Fallback/Consult）。"""
from __future__ import annotations

import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def mask(k: str | None) -> str:
    if not k:
        return "(空)"
    return f"{k[:6]}...{k[-4:]}" if len(k) > 12 else "(短)"


def is_placeholder(k: str | None) -> bool:
    if not k:
        return True
    low = k.lower()
    return "your_" in low or "新的key" in low or k.endswith("_here")


def test_gemini(label: str, key_env: str, model_env: str | None = None,
                default_model: str = "gemini-2.5-flash") -> str:
    key = os.getenv(key_env)
    model = os.getenv(model_env) if model_env else None
    model = model or default_model
    print(f"=== {label} ({key_env}) ===")
    print(f"  key   = {mask(key)}")
    print(f"  model = {model}")

    if is_placeholder(key):
        print("  ✗ 尚未填入真實 key，略過\n")
        return "no-key"

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    payload = {
        "contents": [{"parts": [{"text": "用兩個字回覆：OK"}]}],
        "generationConfig": {"maxOutputTokens": 20, "temperature": 0.0},
    }
    t0 = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=20)
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ exception: {e}\n")
        return "exception"
    dt = (time.time() - t0) * 1000

    if resp.status_code == 200:
        data = resp.json()
        try:
            ans = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            ans = "(無內容)"
        usage = data.get("usageMetadata", {}) or {}
        tin = usage.get("promptTokenCount")
        tout = usage.get("candidatesTokenCount")
        print(f"  ✓ 200  {dt:.0f}ms  ans={ans!r}  tokens_in={tin} tokens_out={tout}\n")
        return "ok"

    print(f"  ✗ {resp.status_code}  {dt:.0f}ms")
    print(f"     body: {resp.text[:300]}\n")
    return f"http-{resp.status_code}"


def test_openai(label: str, key_env: str,
                model_env: str = "", base_env: str = "",
                default_model: str = "gpt-4o-mini") -> str:
    key = os.getenv(key_env)
    model = os.getenv(model_env, default_model) if model_env else default_model
    base = os.getenv(base_env, "https://api.openai.com/v1") if base_env else "https://api.openai.com/v1"
    print(f"=== {label} ({key_env}) ===")
    print(f"  key   = {mask(key)}")
    print(f"  model = {model}")
    print(f"  base  = {base}")

    if is_placeholder(key):
        print("  ✗ 尚未填入真實 key，略過\n")
        return "no-key"

    t0 = time.time()
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "用兩個字回覆：OK"}],
                "max_tokens": 8,
            },
            timeout=20,
        )
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ exception: {e}\n")
        return "exception"
    dt = (time.time() - t0) * 1000

    if resp.status_code == 200:
        body = resp.json()
        ans = body["choices"][0]["message"]["content"].strip()
        usage = body.get("usage", {}) or {}
        tin = usage.get("prompt_tokens")
        tout = usage.get("completion_tokens")
        print(f"  ✓ 200  {dt:.0f}ms  ans={ans!r}  tokens_in={tin} tokens_out={tout}\n")
        return "ok"

    print(f"  ✗ {resp.status_code}  {dt:.0f}ms")
    print(f"     body: {resp.text[:300]}\n")
    return f"http-{resp.status_code}"


def main() -> int:
    results: dict[str, str] = {}

    results["Gemini 主 Key"] = test_gemini(
        "Gemini 主 Key",
        key_env="GEMINI_API_KEY",
        default_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
    results["Gemini 備用 Key"] = test_gemini(
        "Gemini 備用 Key",
        key_env="GEMINI_BACKUP_API_KEY",
        model_env="GEMINI_BACKUP_MODEL",
        default_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
    results["OpenAI Fallback (備用辨識)"] = test_openai(
        "OpenAI Fallback (備用辨識)",
        key_env="OPENAI_FALLBACK_API_KEY",
        model_env="OPENAI_FALLBACK_MODEL",
        base_env="OPENAI_FALLBACK_BASE_URL",
    )
    results["OpenAI Consult (AI 諮詢)"] = test_openai(
        "OpenAI Consult (AI 諮詢)",
        key_env="OPENAI_CONSULT_API_KEY",
        model_env="OPENAI_CONSULT_MODEL",
        base_env="OPENAI_CONSULT_BASE_URL",
    )

    print("=== 總結 ===")
    bad = 0
    for label, status in results.items():
        flag = "✓" if status == "ok" else ("－" if status == "no-key" else "✗")
        print(f"  {flag} {label}: {status}")
        if status not in ("ok", "no-key"):
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
