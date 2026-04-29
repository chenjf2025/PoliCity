"""
Dify AI对话集成API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import asyncio
from app.core.database import get_db
from app.core.config import settings
from app.services.evaluator import EvaluationEngine

router = APIRouter(prefix="/dify", tags=["AI对话"])


class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    message_id: str


@router.post("/chat/stream")
async def chat_with_dify_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    与Dify AI对话 (流式响应)
    携带当前城市指标上下文
    """
    # 获取当前城市指标上下文
    evaluator = EvaluationEngine(db)

    # 简化处理：使用默认区域
    region_code = "default"
    report_year = 2024

    try:
        radar_data = evaluator.get_radar_data(region_code, report_year)
    except Exception:
        radar_data = {"total_score": 0, "dimensions": []}

    # 构建上下文
    context = f"""
    当前城市发展评价信息：
    - 总分：{radar_data.get('total_score', 'N/A')}
    - 经济活力：{radar_data.get('dimensions', [{}])[0].get('score', 'N/A')} (权重25%)
    - 文化繁荣：{radar_data.get('dimensions', [{}])[1].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 1 else 'N/A'} (权重15%)
    - 人力资源：{radar_data.get('dimensions', [{}])[2].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 2 else 'N/A'} (权重20%)
    - 城乡融合：{radar_data.get('dimensions', [{}])[3].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 3 else 'N/A'} (权重20%)
    - 城市治理：{radar_data.get('dimensions', [{}])[4].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 4 else 'N/A'} (权重20%)
    """

    # 调用Dify API (流式模式)
    dify_url = f"{settings.DIFY_API_URL}/chat-messages"

    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": request.query,
        "user": request.user_id,
        "response_mode": "streaming",
        "inputs": {
            "city_context": context
        }
    }

    if request.conversation_id:
        payload["conversation_id"] = request.conversation_id

    async def stream_from_dify():
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", dify_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n".encode()

    return StreamingResponse(
        stream_from_dify(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_dify(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    与Dify AI对话 (阻塞模式)
    携带当前城市指标上下文
    """
    # 获取当前城市指标上下文
    evaluator = EvaluationEngine(db)

    # 简化处理：使用默认区域
    region_code = "default"
    report_year = 2024

    try:
        radar_data = evaluator.get_radar_data(region_code, report_year)
    except Exception:
        radar_data = {"total_score": 0, "dimensions": []}

    # 构建上下文
    context = f"""
    当前城市发展评价信息：
    - 总分：{radar_data.get('total_score', 'N/A')}
    - 经济活力：{radar_data.get('dimensions', [{}])[0].get('score', 'N/A')} (权重25%)
    - 文化繁荣：{radar_data.get('dimensions', [{}])[1].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 1 else 'N/A'} (权重15%)
    - 人力资源：{radar_data.get('dimensions', [{}])[2].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 2 else 'N/A'} (权重20%)
    - 城乡融合：{radar_data.get('dimensions', [{}])[3].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 3 else 'N/A'} (权重20%)
    - 城市治理：{radar_data.get('dimensions', [{}])[4].get('score', 'N/A') if len(radar_data.get('dimensions', [])) > 4 else 'N/A'} (权重20%)
    """

    # 调用Dify API
    dify_url = f"{settings.DIFY_API_URL}/chat-messages"

    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": request.query,
        "user": request.user_id,
        "response_mode": "blocking",
        "inputs": {
            "city_context": context
        }
    }

    if request.conversation_id:
        payload["conversation_id"] = request.conversation_id

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(dify_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            return ChatResponse(
                answer=result.get("answer", ""),
                conversation_id=result.get("conversation_id", ""),
                message_id=result.get("message_id", "")
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Dify API错误: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用Dify失败: {str(e)}")


@router.get("/conversations")
async def list_conversations(
    user_id: str = "anonymous",
    limit: int = 20
):
    """
    获取对话历史列表
    """
    dify_url = f"{settings.DIFY_API_URL}/conversations"

    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}"
    }

    params = {
        "user": user_id,
        "limit": limit
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(dify_url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            return result

    except Exception as e:
        return {"error": str(e), "conversations": []}


@router.get("/messages")
async def get_messages(
    conversation_id: str,
    user_id: str = "anonymous"
):
    """
    获取对话消息历史
    """
    dify_url = f"{settings.DIFY_API_URL}/messages"

    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}"
    }

    params = {
        "conversation_id": conversation_id,
        "user": user_id
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(dify_url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            return result

    except Exception as e:
        return {"error": str(e), "messages": []}
