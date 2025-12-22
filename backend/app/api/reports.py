"""报告相关 API 路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from ..database import get_db
from ..models.research import Report, ResearchTask
from ..services.report_service import ReportService

router = APIRouter()


@router.get("/reports")
async def list_reports(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取报告列表"""
    result = await db.execute(
        select(Report)
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    reports = result.scalars().all()
    
    return {
        "reports": [report.to_dict() for report in reports]
    }


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个报告详情（支持 report_id 或 task_id）"""
    # 先尝试通过 report_id 查询
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    # 如果没找到，尝试通过 task_id 查询
    if not report:
        result = await db.execute(
            select(Report).where(Report.task_id == report_id)
        )
        report = result.scalar_one_or_none()
    
    # 如果还没找到，尝试从 ResearchTask 获取并创建报告
    if not report:
        task_result = await db.execute(
            select(ResearchTask).where(ResearchTask.id == report_id)
        )
        task = task_result.scalar_one_or_none()
        
        if task and task.status == "completed" and task.report_data:
            # 自动创建报告记录
            report = Report(
                task_id=task.id,
                company=task.company,
                content=task.report_data
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return report.to_dict()


@router.get("/reports/{report_id}/pdf")
async def download_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """下载 PDF 报告"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 如果 PDF 不存在，先生成
    if not report.pdf_path or not os.path.exists(report.pdf_path):
        service = ReportService()
        pdf_path = await service.generate_pdf(report)
        report.pdf_path = pdf_path
        await db.commit()
    
    if not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=500, detail="PDF 生成失败")
    
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"{report.company}_研究报告.pdf"
    )


@router.post("/reports/{task_id}/generate")
async def generate_report_from_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """从研究任务生成报告"""
    # 获取研究任务
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="研究任务尚未完成")
    
    if not task.report_data:
        raise HTTPException(status_code=400, detail="没有可用的报告数据")
    
    # 检查是否已存在报告
    existing = await db.execute(
        select(Report).where(Report.task_id == task_id)
    )
    existing_report = existing.scalar_one_or_none()
    
    if existing_report:
        return {"report_id": existing_report.id, "message": "报告已存在"}
    
    # 创建新报告
    report = Report(
        task_id=task_id,
        company=task.company,
        content=task.report_data
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return {"report_id": report.id, "message": "报告创建成功"}



