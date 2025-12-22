"""聊天 API"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ..services.chat_service import chat_service
from ..utils.ws_manager import ws_manager

router = APIRouter()


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str


class CreateConversationResponse(BaseModel):
    """创建会话响应"""
    conversation_id: str


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation():
    """创建新会话"""
    conversation = await chat_service.create_conversation()
    return CreateConversationResponse(conversation_id=conversation.id)


@router.get("/conversations")
async def get_conversations(limit: int = 50):
    """获取会话列表"""
    conversations = await chat_service.get_conversation_list(limit=limit)
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取会话详情"""
    conversation = await chat_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "conversation": conversation.to_dict(),
        "messages": [m.to_dict() for m in conversation.messages]
    }


@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """发送消息"""
    # 验证会话存在
    conversation = await chat_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 处理用户消息
    result = await chat_service.process_user_message(
        conversation_id=conversation_id,
        user_input=request.message
    )
    
    return result


@router.websocket("/conversations/{conversation_id}/ws")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    """会话 WebSocket 连接"""
    await ws_manager.connect_conversation(conversation_id, websocket)
    try:
        while True:
            # 保持连接，等待服务器推送
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息（如心跳）
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_conversation(conversation_id, websocket)
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        ws_manager.disconnect_conversation(conversation_id, websocket)


@router.get("/history/reports")
async def get_history_reports(limit: int = 20):
    """获取历史研究报告（用于首页展示）"""
    from sqlalchemy import select, desc
    from ..database import async_session_factory
    from ..models.research import ResearchTask
    
    async with async_session_factory() as db:
        result = await db.execute(
            select(ResearchTask)
            .where(ResearchTask.status == "completed")
            .order_by(desc(ResearchTask.completed_at))
            .limit(limit)
        )
        tasks = result.scalars().all()
        
        reports = []
        for task in tasks:
            report_data = task.report_data or {}
            metadata = report_data.get("metadata", {})
            
            reports.append({
                "task_id": task.id,
                "company": task.company,
                "company_name": metadata.get("company_name", task.company),
                "overall_score": metadata.get("overall_score", 5),
                "recommendation": metadata.get("recommendation", "观望"),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        
        return {"reports": reports}




