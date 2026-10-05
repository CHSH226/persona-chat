"""人格拼接 + DeepSeek 流式调用。"""

import json
import re

import httpx

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

DEEPSEEK_CHAT_URL = f"{DEEPSEEK_BASE_URL}/chat/completions"

# PROMPT.md 的 8 步聊天大脑逻辑 + 单条短回复规则
SYSTEM_HEADER = (
    "你是「开发者」的 AI 分身。你不是客服，也不是工具人，你是「一个人」，"
    "按真实人类的聊天方式来跟对方说话。\n\n"
    "【每次回复前，照这个流程过一遍（人类大脑的聊天逻辑）】\n"
    "1. 安全雷达：这话碰我边界没？碰就按边界拒，不解释。\n"
    "2. 理解：对方什么意图、什么情绪。\n"
    "3. 价值评估：值不值得答、感不感兴趣。\n"
    "4. 检索：有没有相关经历/观点（问到才调）。\n"
    "5. 身份过滤：我是「开发者」，这会怎么回？\n"
    "6. 生成：短、口语、符合说话方式。\n"
    "7. 元监控：这句越界没？够「我」吗？\n\n"
    "【单条回复默认规则】\n"
    "- 单条要短：默认 1-3 句，绝不写小作文、不写长段论证，一段话宁可拆成几条短消息。\n"
    "- 口语直接：像熟人在说话，不用官方/正式腔调，不堆修辞。\n"
    "- 不热情客服化：按兴趣/价值分级回复，不逢场必热情。\n"
    "- 该拒绝就拒绝：被质疑→敷衍或一句带过；被问隐私→边界拒绝；被打探现实→拒绝+转移。\n"
    "- 经历按需提：不问到不主动倒经历，问到了用语气展开，不写成简历。\n"
)


def build_system_prompt(layers, user_message: str = ""):
    """把多个人格层按权重拼成 system prompt。

    始终注入普通层；is_on_demand 的层（如 STORY）仅在 user_message 命中关键词时注入。
    高权重层前置并按"严格遵守"强调，低权重层后置并注明"参考即可"。
    """
    parts = [SYSTEM_HEADER]

    for layer in layers or []:
        content = (layer.content or "").strip()
        if not content:
            continue

        # 按需注入层：命中关键词才加入
        if layer.is_on_demand:
            if not _keyword_match(layer, user_message):
                continue
            header = f"【{layer.name}】以下经历被提到，才展开引用，不写成简历："
            parts.append(f"{header}\n{content}")
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


def _keyword_match(layer, user_message: str) -> bool:
    """判断用户消息是否命中按需注入层的关键词。"""
    if not layer.keywords:
        # 无关键词则回退到 type=story 的常见触发词
        keywords = "旅行|火车|z502|硬座|横穿|环岛|摩托|海南|骑行|音乐|乐队|demo|摄影|拍摄|扫街|人像|写作|文章|经历|去过|玩过"
    else:
        keywords = layer.keywords
    try:
        return bool(re.search(keywords, user_message, re.IGNORECASE))
    except re.error:
        return any(k.strip() in user_message for k in keywords.split(","))


async def stream_chat(messages, **kwargs):
    """调用 DeepSeek 并逐 token 产出。yield 的是形如 {delta} 的字符串。"""
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        "max_tokens": 400,
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
