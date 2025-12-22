"""会话和消息数据模型"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
import uuid

from .research import Base


class MessageRole(enum.Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"  # Agent 状态消息
    SYSTEM = "system"


class MessageType(enum.Enum):
    """消息类型"""
    TEXT = "text"  # 普通文本
    AGENT_STATUS = "agent_status"  # Agent 状态更新
    AGENT_RESULT = "agent_result"  # Agent 中间结果
    REPORT_PREVIEW = "report_preview"  # 报告预览
    ERROR = "error"  # 错误消息


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=True)  # 会话标题（通常是公司名）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的研究任务（如果有）
    task_id = Column(String(36), ForeignKey("research_tasks.id"), nullable=True)
    
    # 会话状态
    status = Column(String(20), default="active")  # active, completed, failed
    
    # 研究的公司（如果已确定）
    company = Column(String(100), nullable=True)
    
    # 消息列表
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title or "新对话",
            "company": self.company,
            "status": self.status,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    
    # 消息角色和类型
    role = Column(String(20), default="user")  # user, assistant, agent, system
    message_type = Column(String(30), default="text")  # text, agent_status, agent_result, report_preview, error
    
    # 消息内容
    content = Column(Text, nullable=False)
    
    # Agent 相关信息（如果是 agent 消息）
    agent_name = Column(String(50), nullable=True)
    agent_status = Column(String(30), nullable=True)  # working, completed, failed
    
    # 额外数据（JSON 格式，存储中间结果、报告预览等）
    extra_data = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    conversation = relationship("Conversation", back_populates="messages")
    
    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "message_type": self.message_type,
            "content": self.content,
            "agent_name": self.agent_name,
            "agent_status": self.agent_status,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

