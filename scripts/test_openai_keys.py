"""快速驗證 .env 內兩把 OpenAI key 是否可用。"""
from __future__ import annotations

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def mask(k: str | None) -> str:
    if not k:
        return "(空)"
    return f"{k[:7]}...{k[-4:]}" if len(k) > 12 else "(短)"


def test_key(label: str, env_prefix: str) -> str:
    key = os.getenv(f"{env_prefix}_API_KEY")
    model = os.getenv(f"{env_prefix}_MODEL", "gpt-4o-mini")
    base = os.getenv(f"{env_prefix}_BASE_URL", "https://api.openai.com/v1")
    print(f"=== {label} ({env_prefix}_API_KEY) ===")
    print(f"  key   = {mask(key)}")
    print(f"  model = {model}")
    print(f"  base  = {base}")

    if not key or "your_" in key or "新的Key" in key:
        print("  ✗ 尚未填入真實 key，略過")
        print()
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
        print(f"  ✗ exception: {e}")
        print()
        return "exception"

    dt = (time.time() - t0) * 1000
    if resp.status_code == 200:
        body = resp.json()
        answer = body["choices"][0]["message"]["content"].strip()
        usage = body.get("usage", {}) or {}
        tin = usage.get("prompt_tokens")
        tout = usage.get("completion_tokens")
        print(f"  ✓ 200  {dt:.0f}ms  ans={answer!r}  tokens_in={tin}  tokens_out={tout}")
        print()
        return "ok"
    print(f"  ✗ {resp.status_code}  {dt:.0f}ms")
    print(f"     body: {resp.text[:300]}")
    print()
    return f"http-{resp.status_code}"


def main() -> None:
    results = {
        "FALLBACK 備用辨識": test_key("FALLBACK 備用辨識", "OPENAI_FALLBACK"),
        "CONSULT AI 諮詢": test_key("CONSULT AI 諮詢", "OPENAI_CONSULT"),
    }
    print("=== 結果 ===")
    for label, status in results.items():
        print(f"  {label}: {status}")


if __name__ == "__main__":
    main()
