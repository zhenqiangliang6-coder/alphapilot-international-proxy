import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from google_adapter import call_google_gemini

app = FastAPI(
    title="AlphaPilot International Proxy",
    version="1.1.0",
)

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": "AlphaPilot Proxy is running. Version 1.1.0",
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    model: Optional[str] = body.get("model")
    messages: Optional[List[Dict[str, Any]]] = body.get("messages")
    stream: bool = bool(body.get("stream", False))

    if not model:
        raise HTTPException(status_code=400, detail="`model` is required")
    if not messages:
        raise HTTPException(status_code=400, detail="`messages` is required")

    # 只要是 google 路径或者以 gemini 开头的模型，都走 google_adapter
    if model.startswith("google/") or model.startswith("gemini-"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # 这里返回 500 是因为这是服务器配置问题
            return JSONResponse(
                status_code=500,
                content={"error": {"message": "GOOGLE_API_KEY is not set on the server."}}
            )

        # 直接返回 adapter 的结果（无论是 StreamingResponse 还是 dict，FastAPI 都能自动处理）
        response = await call_google_gemini(
            api_key=api_key,
            model=model,
            messages=messages,
            stream=stream
        )
        
        # 如果 adapter 返回的是字典且包含 error 键，我们可以把状态码调成 400 或 500
        if isinstance(response, dict) and "error" in response:
            return JSONResponse(status_code=400, content=response)
            
        return response

    # 其他模型前缀报错
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": f"Model '{model}' not found or supported. Use 'gemini-1.5-flash' etc.",
                "type": "invalid_request_error"
            }
        },
    )