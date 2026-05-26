import httpx
import json
from fastapi.responses import StreamingResponse

# 修改 1: 必须使用 v1beta 才能支持 gemini-1.5 等简写模型名
GOOGLE_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def normalize_model_name(model: str) -> str:
    """
    用户传入 google/gemini-2.0-pro → 转成 gemini-2.0-pro
    """
    if model.startswith("google/"):
        return model.split("google/")[1]
    return model

async def call_google_gemini(api_key: str, model: str, messages: list, stream: bool):
    # 统一模型名
    model_name = normalize_model_name(model)

    # 转换 OpenAI 风格消息为 Gemini 风格
    contents = []
    for msg in messages:
        role = msg["role"]
        text = msg["content"]
        # Gemini 识别 'user' 和 'model'
        contents.append({
            "role": "user" if role == "user" else "model",
            "parts": [{"text": text}]
        })

    # 修改 2: 非流式用 generateContent，流式必须用 streamGenerateContent
    method = "streamGenerateContent" if stream else "generateContent"
    url = f"{GOOGLE_API_BASE}/{model_name}:{method}?key={api_key}"

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
            # --- 非流式 ---
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                # 这里会打印出 Google 返回的具体错误，方便调试
                return {"error": f"Gemini error (status {response.status_code}): {response.text}"}

            data = response.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "id": "chatcmpl-gemini",
                    "object": "chat.completion",
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": text},
                            "finish_reason": "stop"
                        }
                    ]
                }
            except (KeyError, IndexError):
                return {"error": f"Unexpected response structure: {data}"}

        else:
            # --- 流式 SSE ---
            async def event_stream():
                async with client.stream("POST", url, json=payload) as r:
                    if r.status_code != 200:
                        err = await r.aread()
                        yield f"data: {err.decode()}\n\n"
                        return
                    
                    async for line in r.aiter_lines():
                        if line.strip():
                            # Google 的流式返回带有一些特殊符号，这里简单转发，
                            # 以后你可以根据需要解析成 OpenAI 兼容格式
                            yield f"data: {line}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream")