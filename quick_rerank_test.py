#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quick_rerank_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
向 https://api-ai.vivo.com.cn/rerank 发送一次示例请求，
打印相似度分数列表。

用法:
    python quick_rerank_test.py
"""

import json
import time
import hmac
import hashlib
import random
import string
import requests

# ——— 1. 你的凭证  ——————————————————————————————
VIVO_APP_ID = "2025827557"
VIVO_APP_KEY = "kIFmdMYqpZHhbgap"

# ——— 2. 固定 API 常量 ————————————————————————————
DOMAIN   = "api-ai.vivo.com.cn"
URI      = "/rerank"
FULL_URL = f"https://{DOMAIN}{URI}"
METHOD   = "POST"

# ——— 3. 待测试的文本 ————————————————————————————
POST_DATA = {
    "model_name": "bge-reranker-v2-m3",
    "query": "云南植物园",
    "sentences": [
        "昆明植物园",
        "云南丰泽源植物园",
        "昆明国兴多肉植物园"
    ]
}

# ---------------- 签名工具 ---------------------------------
def _nonce(n: int = 8) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def _signature(app_key: str,
               method: str,
               uri: str,
               ts: str,
               nonce: str) -> str:
    msg = f"{method}\n{uri}\n{ts}\n{nonce}"
    return (
        hmac.new(app_key.encode("utf-8"),
                 msg.encode("utf-8"),
                 hashlib.sha256)
        .hexdigest()
    )

def build_headers(app_id: str, app_key: str) -> dict:
    ts    = str(int(time.time()))
    nonce = _nonce()
    sig   = _signature(app_key, "POST", "/rerank", ts, nonce)

    return {
        "Content-Type":                  "application/json",
        "X-AI-GATEWAY-APP-ID":           app_id,
        "X-AI-GATEWAY-TIMESTAMP":        ts,
        "X-AI-GATEWAY-NONCE":            nonce,
        "X-AI-GATEWAY-SIGNED-HEADERS":   "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce",
        "X-AI-GATEWAY-SIGNATURE":        sig,
    }

# ---------------- 主流程 -----------------------------------
def main():
    headers = build_headers(VIVO_APP_ID, VIVO_APP_KEY)
    r = requests.post(FULL_URL, headers=headers,
                      data=json.dumps(POST_DATA, ensure_ascii=False),
                      timeout=10)
    if r.ok:
        print("Similarity:", r.json()["data"])
    else:
        print(r.status_code, r.text)

if __name__ == "__main__":
    main()