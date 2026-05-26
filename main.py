import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from google_adapter import call_google_gemini

app = FastAPI(
    title="AlphaPilot International Proxy",
    description="Production-grade model proxy for Google Gemini / future HF Agents / OpenAI",
    version="1.0.0",
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "AlphaPilot International Proxy",
        "version": "1.0.0",
        "message": "Render Python 3 runtime is running.",
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    model: Optional[str] = body.get("model")
    messages: Optional[List[Dict[str, Any]]] = body.get("messages")
    stream: bool = bool(body.get("stream", False))

    if not model:
        raise HTTPException(status_code=400, detail="`model` is required")
    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="`messages` must be a non-empty list")

    try:
        if model.startswith("google/") or model.startswith("gemini-"):
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is missing")

            return await call_google_gemini(
                api_key=api_key,
                model=model,
                messages=messages,
                stream=stream
            )

        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "unsupported_model",
                    "message": f"Unsupported model: {model}. Expected prefix: 'google/' or bare Gemini model like 'gemini-2.0-pro'."
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
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
