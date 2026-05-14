#!/usr/bin/env python3
"""
小米 MiMo API Key 自检脚本
- 从 backend/.env 读取 MIMO_API_KEY / MIMO_BASE_URL / MIMO_MODEL
- 同时执行：原始 HTTP 请求 + openai SDK 调用，输出详细诊断
用法：
    /root/tzb/backend/venv/bin/python /root/tzb/backend/scripts/check_mimo_key.py
可选参数：
    --key  覆盖环境里的 key
    --base 覆盖 base_url
    --model 覆盖 model
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# 把 backend 目录加入 sys.path，方便复用 settings
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def _mask(key: str) -> str:
    if not key:
        return "<空>"
    if len(key) <= 10:
        return key[:2] + "***"
    return key[:6] + "..." + key[-4:]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default=None)
    parser.add_argument("--base", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--prompt", default="你好，用一句话自我介绍。")
    return parser.parse_args()


def load_env_from_dotenv():
    """优先尝试 pydantic Settings，失败则手工读 .env"""
    try:
        from config import settings  # type: ignore
        return {
            "key": settings.mimo_api_key,
            "base": settings.mimo_base_url,
            "model": settings.mimo_model,
            "timeout": settings.mimo_timeout,
        }
    except Exception:
        env_path = BACKEND_DIR / ".env"
        data = {"key": "", "base": "https://api.xiaomimimo.com/v1", "model": "mimo-v2.5-pro", "timeout": 60}
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip().upper()
                v = v.strip()
                if k == "MIMO_API_KEY":
                    data["key"] = v
                elif k == "MIMO_BASE_URL":
                    data["base"] = v or data["base"]
                elif k == "MIMO_MODEL":
                    data["model"] = v or data["model"]
        return data


def test_raw_http(base: str, key: str, model: str, prompt: str):
    print("\n[1/2] 原始 HTTP 请求 (urllib)")
    import urllib.request
    import urllib.error
    url = base.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 32,
        "temperature": 0.3,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    print(f"  URL  : {url}")
    print(f"  Model: {model}")
    print(f"  Key  : {_mask(key)}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", "replace")
            print(f"  HTTP : {resp.status}")
            try:
                parsed = json.loads(payload)
                content = parsed.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = parsed.get("usage")
                print(f"  回复 : {content[:200]}")
                if usage:
                    print(f"  用量 : {usage}")
            except Exception:
                print(f"  原文 : {payload[:500]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"  HTTP : {e.code} {e.reason}")
        print(f"  错误 : {body[:500]}")
        return False
    except Exception as e:
        print(f"  网络异常: {e}")
        return False


def test_openai_sdk(base: str, key: str, model: str, prompt: str, timeout: int):
    print("\n[2/2] openai SDK 调用")
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        print("  未安装 openai 包，跳过；请执行: pip install 'openai>=1.40.0'")
        return False
    client = OpenAI(api_key=key, base_url=base, timeout=timeout)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=32,
            temperature=0.3,
        )
        msg = completion.choices[0].message.content
        print(f"  回复 : {(msg or '').strip()[:200]}")
        if completion.usage:
            print(f"  用量 : prompt={completion.usage.prompt_tokens} "
                  f"completion={completion.usage.completion_tokens} "
                  f"total={completion.usage.total_tokens}")
        return True
    except Exception as e:
        print(f"  调用失败: {type(e).__name__}: {e}")
        return False


def main():
    args = parse_args()
    cfg = load_env_from_dotenv()
    key = args.key or cfg["key"]
    base = args.base or cfg["base"]
    model = args.model or cfg["model"]
    timeout = cfg.get("timeout", 60)

    print("===== 小米 MiMo API 连通性自检 =====")
    print(f"base_url = {base}")
    print(f"model    = {model}")
    print(f"api_key  = {_mask(key)}")
    if not key:
        print("\n❌ MIMO_API_KEY 为空，请先在 backend/.env 中配置")
        sys.exit(2)

    ok_http = test_raw_http(base, key, model, args.prompt)
    ok_sdk = test_openai_sdk(base, key, model, args.prompt, timeout)

    print("\n===== 结果 =====")
    print(f"  HTTP 直连 : {'✅ OK' if ok_http else '❌ 失败'}")
    print(f"  openai SDK : {'✅ OK' if ok_sdk else '❌ 失败'}")
    if ok_http and ok_sdk:
        print("\n🎉 Key 可用，AI 功能应当能正常使用。")
        sys.exit(0)
    print("\n⚠️ 调用失败：")
    print("  - 401 / Invalid API Key: 平台未识别该 key，请到控制台重新生成")
    print("  - 403: key 没有该 model 的调用权限，换 model 名再试 (如 mimo-v2-flash)")
    print("  - 404 / Not Found: base_url 不对，检查 MIMO_BASE_URL")
    print("  - 429: 触发限流，稍后再试")
    print("  - SSL/Timeout: 服务器网络不通到 MiMo")
    sys.exit(1)


if __name__ == "__main__":
    main()
