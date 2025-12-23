"""聊天服务 - 管理会话和消息"""
import asyncio
import uuid
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
        extra_data: Dict = None,
        message_id: str = None
    ) -> Message:
        """添加消息"""
        async with async_session_factory() as db:
            message = Message(
                id=message_id or str(uuid.uuid4()),
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
    
    async def update_message(
        self,
        message_id: str,
        content: str = None,
        agent_status: str = None,
        extra_data: Dict = None,
        message_type: str = None
    ) -> Optional[Message]:
        """更新现有消息"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(Message).where(Message.id == message_id)
            )
            message = result.scalar_one_or_none()
            
            if not message:
                return None
            
            if content is not None:
                message.content = content
            if agent_status is not None:
                message.agent_status = agent_status
            if extra_data is not None:
                message.extra_data = extra_data
            if message_type is not None:
                message.message_type = message_type
            
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
            
            # 存储每个agent的消息ID，用于更新而不是创建新消息
            agent_message_ids: Dict[str, str] = {}
            # 存储流式消息内容
            streamingMessages: Dict[str, str] = {}
            
            # 进度回调 - 更新或创建 Agent 状态消息
            async def progress_callback(progress: int, agent: str, task_desc: str, estimated: int = 0):
                # 获取或创建该agent的消息ID
                if agent not in agent_message_ids:
                    agent_message_ids[agent] = str(uuid.uuid4())
                
                message_id = agent_message_ids[agent]
                
                # 尝试更新现有消息，如果不存在则创建
                message = await self.update_message(
                    message_id=message_id,
                    content=task_desc,
                    agent_status="working",
                    extra_data={
                        "progress": progress,
                        "estimated_time": estimated
                    },
                    message_type="agent_status"
                )
                
                if not message:
                    # 消息不存在，创建新消息
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
                        },
                        message_id=message_id
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
            
            # Agent 结果回调 - 更新现有消息为完成状态
            async def result_callback(agent: str, result_summary: str, result_data: Dict = None):
                # 使用已有的message_id更新消息
                if agent in agent_message_ids:
                    message_id = agent_message_ids[agent]
                    # 更新现有消息
                    message = await self.update_message(
                        message_id=message_id,
                        content=result_summary if not streamingMessages.get(message_id) else streamingMessages[message_id],
                        agent_status="completed",
                        message_type="agent_result",
                        extra_data=result_data
                    )
                    
                    if message:
                        await ws_manager.broadcast_to_conversation(conversation_id, {
                            "type": "agent_result",
                            "message": message.to_dict()
                        })
                        return
                
                # 如果没有找到现有消息，创建新消息（兜底）
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
            
            # 流式回调 - 推送流式输出，使用与状态消息相同的message_id
            async def stream_callback(message_id: str, agent_name: str, chunk: str, finished: bool):
                # 如果agent还没有消息ID，使用传入的message_id
                if agent_name not in agent_message_ids:
                    agent_message_ids[agent_name] = message_id
                else:
                    # 使用已有的message_id，确保状态和流式输出在同一个消息中
                    message_id = agent_message_ids[agent_name]
                
                # 如果是第一次流式输出，创建或更新消息为streaming状态
                if chunk and not streamingMessages.get(message_id):
                    streamingMessages[message_id] = ""
                    # 确保消息存在
                    message = await self.update_message(
                        message_id=message_id,
                        agent_status="streaming",
                        message_type="streaming"
                    )
                    if not message:
                        # 如果消息不存在，创建它
                        await self.add_message(
                            conversation_id=conversation_id,
                            role="agent",
                            content="",
                            message_type="streaming",
                            agent_name=agent_name,
                            agent_status="streaming",
                            message_id=message_id
                        )
                
                # 更新流式内容
                if chunk:
                    streamingMessages[message_id] = streamingMessages.get(message_id, "") + chunk
                    # 更新消息内容
                    await self.update_message(
                        message_id=message_id,
                        content=streamingMessages[message_id]
                    )
                
                # 流式完成，更新状态
                if finished:
                    await self.update_message(
                        message_id=message_id,
                        agent_status="completed",
                        message_type="agent_result"
                    )
                
                await ws_manager.broadcast_stream_chunk(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    agent_name=agent_name,
                    chunk=chunk,
                    finished=finished
                )
            
            # 运行 Workflow
            report = await self.workflow.run(
                company=company,
                depth="deep",
                focus_areas=[],
                progress_callback=progress_callback,
                result_callback=result_callback,
                stream_callback=stream_callback
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

