import httpx
import json
from fastapi.responses import StreamingResponse

GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1/models"


def normalize_model_name(model: str) -> str:
    """
    用户传入 google/gemini-2.0-pro → 转成 gemini-2.0-pro
    """
    if model.startswith("google/"):
        return model.split("google/")[1]
    return model

async def call_google_gemini(api_key: str, model: str, messages: list, stream: bool):
    # 统一模型名
    model = normalize_model_name(model)

    # 转换 OpenAI 风格消息为 Gemini 风格
    contents = []
    for msg in messages:
        role = msg["role"]
        text = msg["content"]

        if role == "user":
            contents.append({"role": "user", "parts": [{"text": text}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": text}]})

    url = f"{GOOGLE_API_URL}/{model}:generateContent?key={api_key}"

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        if not stream:
            # 非流式
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                return {"error": f"Gemini non-stream error: {response.text}"}

            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]

            return {
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop"
                    }
                ]
            }

        else:
            # 流式 SSE
            async def event_stream():
                async with client.stream("POST", url, json=payload) as r:
                    async for line in r.aiter_lines():
                        if line.strip():
                            yield f"data: {line}\n\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream")
