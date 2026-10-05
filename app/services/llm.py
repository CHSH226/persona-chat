"""人格拼接 + DeepSeek 流式调用。"""

import json

import httpx

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

DEEPSEEK_CHAT_URL = f"{DEEPSEEK_BASE_URL}/chat/completions"


DEFAULT_OUTPUT_RULE = (
    "【输出规则】回复要简洁克制，一般不超过150个中文字符。"
    "除非用户明确要求长篇，否则不要长篇大论。先直接回答，别铺垫。"
    "人格层若有更高的输出要求，以人格层为准。"
)


def build_system_prompt(layers):
    """把多个人格层按权重拼成 system prompt。

    高权重层前置并按"严格遵守"强调，低权重层后置并注明"参考即可"。
    """
    parts = [DEFAULT_OUTPUT_RULE]

    if not layers:
        return "\n\n".join(parts)

    # 权重从高到低排序
    layers = sorted(layers, key=lambda l: l.weight or 0, reverse=True)

    for layer in layers:
        content = (layer.content or "").strip()
        if not content:
            continue
        weight = layer.weight or 0
        if weight >= 0.8:
            header = f"【{layer.name}】以下内容很重要，必须严格遵守："
        elif weight >= 0.5:
            header = f"【{layer.name}】以下内容请重点参考："
        else:
            header = f"【{layer.name}】以下内容仅供参考："
        parts.append(f"{header}\n{content}")

    return "\n\n".join(parts)


async def stream_chat(messages, **kwargs):
    """调用 DeepSeek 并逐 token 产出。yield 的是形如 {delta} 的字符串。"""
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        **kwargs,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", DEEPSEEK_CHAT_URL, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = obj["choices"][0]["delta"].get("content", "")
                if delta:
                    yield delta
