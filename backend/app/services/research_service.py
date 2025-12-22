"""研究服务 - 使用 Workflow 协调 Agent 执行研究任务"""
import asyncio
from datetime import datetime
from sqlalchemy import select

from ..config import get_settings
from ..database import async_session_factory
from ..models.research import ResearchTask, Report
from ..workflows.research_workflow import ResearchWorkflow
from ..utils.ws_manager import ws_manager

settings = get_settings()


def is_shutting_down() -> bool:
    """检查是否正在关闭"""
    try:
        from ..main import is_shutting_down as check_shutdown
        return check_shutdown()
    except ImportError:
        return False


class ResearchService:
    """研究服务 - 使用 Workflow 架构"""
    
    def __init__(self):
        # 使用新的 Workflow 架构
        self.workflow = ResearchWorkflow()
    
    async def run_research(self, task_id: str):
        """运行研究任务"""
        async with async_session_factory() as db:
            try:
                # 检查是否正在关闭
                if is_shutting_down():
                    print(f"[WARN] 应用正在关闭，跳过任务: {task_id}")
                    return
                
                # 获取任务
                result = await db.execute(
                    select(ResearchTask).where(ResearchTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    print(f"任务不存在: {task_id}")
                    return
                
                # 更新状态为运行中
                task.status = "running"
                task.started_at = datetime.utcnow()
                await db.commit()
                
                # 进度回调 - 更新数据库和 WebSocket
                async def progress_callback(progress: int, agent: str, task_desc: str, estimated: int = 0):
                    # 检查是否正在关闭
                    if is_shutting_down():
                        raise asyncio.CancelledError("Application is shutting down")
                    
                    task.progress = progress
                    task.current_agent = agent
                    task.current_task = task_desc
                    task.estimated_time = estimated
                    await db.commit()
                    
                    # 广播进度
                    await ws_manager.broadcast_progress(task_id, {
                        "progress": progress,
                        "status": "running",
                        "currentAgent": agent,
                        "currentTask": task_desc,
                        "estimatedTime": estimated
                    })
                
                # 使用 Workflow 执行研究
                report_data = await self.workflow.run(
                    company=task.company,
                    depth=task.depth,
                    focus_areas=task.focus_areas or [],
                    progress_callback=progress_callback
                )
                
                # 更新任务状态
                task.status = "completed"
                task.progress = 100
                task.completed_at = datetime.utcnow()
                task.report_data = report_data
                task.current_agent = ""
                task.current_task = "研究完成"
                await db.commit()
                
                # 创建报告记录
                report = Report(
                    task_id=task_id,
                    company=task.company,
                    content=report_data
                )
                db.add(report)
                await db.commit()
                
                # 广播完成
                await ws_manager.broadcast_progress(task_id, {
                    "progress": 100,
                    "status": "completed",
                    "currentAgent": "",
                    "currentTask": "研究完成",
                    "estimatedTime": 0
                })
                
            except asyncio.CancelledError:
                print(f"[INFO] 研究任务被取消: {task_id}")
                
                # 更新任务状态为取消
                task.status = "failed"
                task.error_message = "任务被取消（应用关闭）"
                task.completed_at = datetime.utcnow()
                await db.commit()
                
                # 广播取消
                await ws_manager.broadcast_progress(task_id, {
                    "progress": task.progress,
                    "status": "failed",
                    "currentAgent": "",
                    "currentTask": "任务已取消",
                    "estimatedTime": 0
                })
                
            except Exception as e:
                print(f"研究任务失败: {e}")
                import traceback
                traceback.print_exc()
                
                # 更新任务状态为失败
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                await db.commit()
                
                # 广播失败
                await ws_manager.broadcast_progress(task_id, {
                    "progress": task.progress,
                    "status": "failed",
                    "currentAgent": "",
                    "currentTask": f"研究失败: {str(e)}",
                    "estimatedTime": 0
                })
