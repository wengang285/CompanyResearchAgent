"""研究任务和报告数据模型"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ResearchTask(Base):
    """研究任务模型"""
    __tablename__ = "research_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company = Column(String(200), nullable=False, comment="公司名称或代码")
    status = Column(String(50), default="pending", comment="状态: pending, running, completed, failed")
    depth = Column(String(50), default="deep", comment="研究深度: basic, standard, deep")
    focus_areas = Column(JSON, default=list, comment="关注重点领域")
    
    # 进度信息
    progress = Column(Integer, default=0, comment="进度百分比 0-100")
    current_agent = Column(String(100), default="", comment="当前执行的 Agent")
    current_task = Column(String(200), default="", comment="当前执行的任务")
    estimated_time = Column(Integer, default=0, comment="预计剩余时间(秒)")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 结果
    report_data = Column(JSON, nullable=True, comment="研究报告数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "company": self.company,
            "status": self.status,
            "depth": self.depth,
            "focus_areas": self.focus_areas or [],
            "progress": self.progress,
            "current_agent": self.current_agent,
            "current_task": self.current_task,
            "estimated_time": self.estimated_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "report_data": self.report_data,
            "error_message": self.error_message,
        }


class Report(Base):
    """研究报告模型"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False, comment="关联的研究任务ID")
    company = Column(String(200), nullable=False, comment="公司名称")
    stock_code = Column(String(20), nullable=True, comment="股票代码")
    
    # 报告内容
    content = Column(JSON, nullable=False, comment="报告内容")
    pdf_path = Column(String(500), nullable=True, comment="PDF文件路径")
    
    # 元数据
    research_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "company": self.company,
            "stock_code": self.stock_code,
            "content": self.content,
            "pdf_path": self.pdf_path,
            "research_date": self.research_date.isoformat() if self.research_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }






