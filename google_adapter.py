import os
import httpx
from typing import Any, Dict, List
from fastapi.responses import StreamingResponse, JSONResponse

# 从 Render 环境变量读取 Google API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Google Gemini API 基础 URL
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _convert_messages_to_gemini(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将 OpenAI 风格 messages 转换为 Google Gemini 的 contents 格式。
    """
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("content", "")

        # Gemini 的 role 只有 user / model
        gemini_role = "user" if role == "user" else "model"

        contents.append({
            "role": gemini_role,
            "parts": [{"text": text}]
        })

    return contents


async def call_google_gemini(messages: List[Dict[str, Any]], model: str, stream: bool):
    """
    调用 Google Gemini API（支持流式和非流式）
    并将结果转换为 OpenAI 风格输出。
    """
    if not GOOGLE_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "GOOGLE_API_KEY is missing in server environment variables"}
        )

    gemini_model = model.split("/", 1)[1]  # "google/gemini-2.0-pro" → "gemini-2.0-pro"
    contents = _convert_messages_to_gemini(messages)

    # 非流式接口
    if not stream:
        url = f"{BASE_URL}/models/{gemini_model}:generateContent?key={GOOGLE_API_KEY}"
        payload = {"contents": contents}

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

                text = data["candidates"][0]["content"]["parts"][0]["text"]

                # 转换为 OpenAI 风格
                return {
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": text
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Gemini non-stream error: {str(e)}"}
            )

    # 流式接口
    url = f"{BASE_URL}/models/{gemini_model}:streamGenerateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": contents}

    async def event_stream():
        """
        将 Gemini 的流式输出转换为 OpenAI SSE delta 风格。
        """
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json=payload) as r:
                    async for line in r.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue

                        raw = line[6:]  # 去掉 "data: "
                        yield f"data: {raw}\n\n"

        except Exception as e:
            yield f"data: {{\"error\": \"Gemini stream error: {str(e)}\"}}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
