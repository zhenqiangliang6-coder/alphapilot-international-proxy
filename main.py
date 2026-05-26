import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from google_adapter import call_google_gemini

app = FastAPI(
    title="AlphaPilot International Proxy",
    description="Production-grade model proxy for Google Gemini / future HF Agents / OpenAI",
    version="1.0.0",
)


@app.get("/")
def root() -> Dict[str, Any]:
    """
    健康检查 & 基本信息
    """
    return {
        "status": "ok",
        "service": "AlphaPilot International Proxy",
        "version": "1.0.0",
        "message": "Render Python 3 runtime is running.",
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Dict[str, Any]):
    """
    统一的聊天补全接口（OpenAI 兼容风格）

    请求示例：
    {
      "model": "google/gemini-2.0-pro",
      "messages": [
        {"role": "user", "content": "Hello"}
      ],
      "stream": true
    }
    """
    model: Optional[str] = request.get("model")
    messages: Optional[List[Dict[str, Any]]] = request.get("messages")
    stream: bool = bool(request.get("stream", False))

    if not model:
        raise HTTPException(status_code=400, detail="`model` is required")
    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="`messages` must be a non-empty list")

    # 未来这里可以扩展更多前缀：
    # - openai/...
    # - hf/...
    # - deepseek/...
    # 通过简单的 if/elif 路由到不同 adapter
    try:
        if model.startswith("google/"):
            return await call_google_gemini(messages=messages, model=model, stream=stream)

        # 未支持的模型前缀
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "unsupported_model",
                    "message": f"Unsupported model: {model}. "
                               f"Expected prefix: 'google/'."
                }
            },
        )
    except HTTPException:
        # 直接透传 FastAPI 抛出的 HTTPException
        raise
    except Exception as e:
        # 兜底异常处理，避免 500 堆栈泄露
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "Internal error in proxy layer.",
                    "detail": str(e),
                }
            },
        )
