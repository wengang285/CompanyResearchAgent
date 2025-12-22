"""聊天服务 - 管理会话和消息"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from ..database import async_session_factory
from ..models.conversation import Conversation, Message
from ..models.research import ResearchTask, Report
from ..agents.intent_agent import IntentAgent, IntentType, ParsedIntent
from ..workflows.research_workflow import ResearchWorkflow
from ..utils.ws_manager import ws_manager


class ChatService:
    """聊天服务"""
    
    def __init__(self):
        self.intent_agent = IntentAgent()
        self.workflow = ResearchWorkflow()
    
    async def create_conversation(self) -> Conversation:
        """创建新会话"""
        async with async_session_factory() as db:
            conversation = Conversation()
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取会话详情"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(Conversation.id == conversation_id)
            )
            return result.scalar_one_or_none()
    
    async def get_conversation_list(self, limit: int = 50) -> List[Dict]:
        """获取会话列表"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(Conversation)
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
            )
            conversations = result.scalars().all()
            # 避免惰性加载问题，手动构建字典
            return [
                {
                    "id": c.id,
                    "title": c.title or "新对话",
                    "company": c.company,
                    "status": c.status,
                    "task_id": c.task_id,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                    "message_count": 0  # 列表中不需要准确的消息数
                }
                for c in conversations
            ]
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        agent_name: str = None,
        agent_status: str = None,
        extra_data: Dict = None
    ) -> Message:
        """添加消息"""
        async with async_session_factory() as db:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_type=message_type,
                agent_name=agent_name,
                agent_status=agent_status,
                extra_data=extra_data
            )
            db.add(message)
            
            # 更新会话时间
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(message)
            return message
    
    async def process_user_message(
        self,
        conversation_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        处理用户消息
        
        Returns:
            {
                "success": bool,
                "intent": ParsedIntent,
                "task_id": str (如果启动了研究任务)
            }
        """
        # 1. 保存用户消息
        await self.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_input
        )
        
        # 2. 解析意图
        intent = await self.intent_agent.parse(user_input)
        
        # 3. 根据意图处理
        if intent.intent_type == IntentType.RESEARCH_REPORT:
            # 保存助手确认消息
            await self.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=intent.message
            )
            
            # 更新会话信息
            async with async_session_factory() as db:
                result = await db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    conversation.company = intent.company
                    conversation.title = f"{intent.company} 研究报告"
                    await db.commit()
            
            # 创建研究任务
            task_id = await self._create_research_task(
                conversation_id=conversation_id,
                company=intent.company
            )
            
            # 后台启动研究
            asyncio.create_task(
                self._run_research_with_chat(conversation_id, task_id, intent.company)
            )
            
            return {
                "success": True,
                "intent": intent.to_dict(),
                "task_id": task_id
            }
        else:
            # 保存提示消息
            await self.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=intent.message
            )
            
            return {
                "success": False,
                "intent": intent.to_dict(),
                "task_id": None
            }
    
    async def _create_research_task(self, conversation_id: str, company: str) -> str:
        """创建研究任务"""
        async with async_session_factory() as db:
            task = ResearchTask(
                company=company,
                depth="deep",
                focus_areas=[],
                status="pending",
                progress=0
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            
            # 关联到会话
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.task_id = task.id
                await db.commit()
            
            return task.id
    
    async def _run_research_with_chat(
        self,
        conversation_id: str,
        task_id: str,
        company: str
    ):
        """运行研究并通过聊天更新状态"""
        try:
            async with async_session_factory() as db:
                # 获取任务
                result = await db.execute(
                    select(ResearchTask).where(ResearchTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if not task:
                    return
                
                task.status = "running"
                task.started_at = datetime.utcnow()
                await db.commit()
            
            # 进度回调 - 发送 Agent 状态消息
            async def progress_callback(progress: int, agent: str, task_desc: str, estimated: int = 0):
                # 保存 Agent 状态消息
                message = await self.add_message(
                    conversation_id=conversation_id,
                    role="agent",
                    content=task_desc,
                    message_type="agent_status",
                    agent_name=agent,
                    agent_status="working",
                    extra_data={
                        "progress": progress,
                        "estimated_time": estimated
                    }
                )
                
                # 广播到 WebSocket
                await ws_manager.broadcast_to_conversation(conversation_id, {
                    "type": "agent_status",
                    "message": message.to_dict()
                })
                
                # 更新任务进度
                async with async_session_factory() as db:
                    result = await db.execute(
                        select(ResearchTask).where(ResearchTask.id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    if task:
                        task.progress = progress
                        task.current_agent = agent
                        task.current_task = task_desc
                        await db.commit()
            
            # Agent 结果回调 - 发送中间结果
            async def result_callback(agent: str, result_summary: str, result_data: Dict = None):
                message = await self.add_message(
                    conversation_id=conversation_id,
                    role="agent",
                    content=result_summary,
                    message_type="agent_result",
                    agent_name=agent,
                    agent_status="completed",
                    extra_data=result_data
                )
                
                await ws_manager.broadcast_to_conversation(conversation_id, {
                    "type": "agent_result",
                    "message": message.to_dict()
                })
            
            # 运行 Workflow
            report = await self.workflow.run(
                company=company,
                depth="deep",
                focus_areas=[],
                progress_callback=progress_callback,
                result_callback=result_callback
            )
            
            # 更新任务状态并创建报告
            report_id = None
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ResearchTask).where(ResearchTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    task.status = "completed"
                    task.progress = 100
                    task.completed_at = datetime.utcnow()
                    task.report_data = report
                    await db.commit()
                    
                    # 创建报告记录
                    new_report = Report(
                        task_id=task_id,
                        company=company,
                        content=report
                    )
                    db.add(new_report)
                    await db.commit()
                    await db.refresh(new_report)
                    report_id = new_report.id
                
                # 更新会话状态
                result = await db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    conversation.status = "completed"
                    await db.commit()
            
            # 发送报告预览消息
            report_preview = self._create_report_preview(report, report_id or task_id)
            message = await self.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=f"✅ {company} 的研究报告已生成完成！",
                message_type="report_preview",
                extra_data=report_preview
            )
            
            await ws_manager.broadcast_to_conversation(conversation_id, {
                "type": "report_complete",
                "message": message.to_dict()
            })
            
        except Exception as e:
            print(f"研究任务失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 保存错误消息
            await self.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=f"抱歉，研究过程中遇到了问题：{str(e)}",
                message_type="error"
            )
            
            # 更新状态
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ResearchTask).where(ResearchTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    await db.commit()
                
                result = await db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    conversation.status = "failed"
                    await db.commit()
    
    def _create_report_preview(self, report: Dict, report_id: str) -> Dict:
        """创建报告预览数据"""
        metadata = report.get("metadata", {})
        sections = report.get("sections", [])
        
        # 获取执行摘要
        executive_summary = ""
        for section in sections:
            if section.get("id") == "executive_summary":
                executive_summary = section.get("content", "")[:200]
                break
        
        return {
            "report_id": report_id,
            "company": metadata.get("company", ""),
            "company_name": metadata.get("company_name", ""),
            "overall_score": metadata.get("overall_score", 5),
            "recommendation": metadata.get("recommendation", "观望"),
            "executive_summary": executive_summary,
            "report_url": f"/report/{report_id}"
        }


# 单例
chat_service = ChatService()

