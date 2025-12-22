"""研究相关 API 路由"""
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.research import ResearchTask
from ..utils.ws_manager import ws_manager

router = APIRouter()


class ResearchRequest(BaseModel):
    """研究请求"""
    company: str  # 公司名称或代码
    depth: str = "deep"  # 研究深度: basic, standard, deep
    focus: List[str] = []  # 关注重点领域


class ResearchResponse(BaseModel):
    """研究响应"""
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    id: str
    company: str
    status: str
    progress: int
    current_agent: str
    current_task: str
    estimated_time: int


@router.post("/research/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """启动新的研究任务"""
    # 创建研究任务
    task = ResearchTask(
        company=request.company,
        depth=request.depth,
        focus_areas=request.focus,
        status="pending",
        progress=0
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # 在后台启动研究任务
    asyncio.create_task(run_research_task(task.id))
    
    return ResearchResponse(
        task_id=task.id,
        message=f"已创建对 {request.company} 的研究任务"
    )


async def run_research_task(task_id: str):
    """后台运行研究任务"""
    # 延迟导入避免循环依赖
    from ..services.research_service import ResearchService
    service = ResearchService()
    await service.run_research(task_id)


@router.get("/research/{task_id}/status", response_model=TaskStatusResponse)
async def get_research_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取研究进度"""
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatusResponse(
        id=task.id,
        company=task.company,
        status=task.status,
        progress=task.progress,
        current_agent=task.current_agent or "",
        current_task=task.current_task or "",
        estimated_time=task.estimated_time or 0
    )


@router.get("/research/{task_id}/result")
async def get_research_result(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取研究结果"""
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="研究任务尚未完成")
    
    return {
        "task_id": task.id,
        "company": task.company,
        "status": task.status,
        "report": task.report_data,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }


@router.get("/research/history")
async def get_research_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取研究历史记录"""
    result = await db.execute(
        select(ResearchTask)
        .order_by(ResearchTask.created_at.desc())
        .limit(limit)
    )
    tasks = result.scalars().all()
    
    return {
        "tasks": [task.to_dict() for task in tasks]
    }


@router.websocket("/research/{task_id}/progress")
async def research_progress_ws(websocket: WebSocket, task_id: str):
    """WebSocket 实时进度推送"""
    await ws_manager.connect(task_id, websocket)
    
    try:
        while True:
            # 保持连接，等待消息或超时
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # 客户端发送心跳
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        ws_manager.disconnect(task_id, websocket)
    except Exception:
        ws_manager.disconnect(task_id, websocket)
