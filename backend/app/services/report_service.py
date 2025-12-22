"""报告服务"""
import os
from datetime import datetime
from typing import Optional
from pathlib import Path
from ..models.research import Report
from ..tools.pdf_generator import PDFGenerator


class ReportService:
    """报告服务"""
    
    def __init__(self):
        self.pdf_generator = PDFGenerator()
        # 使用绝对路径，确保目录存在
        self.reports_dir = Path(__file__).parent.parent.parent / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_pdf(self, report: Report) -> str:
        """生成 PDF 报告"""
        try:
            # 生成文件名（移除可能导致问题的字符）
            safe_company = "".join(c for c in report.company if c.isalnum() or c in "_ -")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_company}_{timestamp}.pdf"
            filepath = str(self.reports_dir / filename)
            
            # 生成 PDF
            self.pdf_generator.generate_report_pdf(report.content, filepath)
            
            print(f"[PDF] 报告已生成: {filepath}")
            return filepath
        except Exception as e:
            print(f"[PDF] 生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def format_report_content(self, report_data: dict) -> dict:
        """格式化报告内容用于展示"""
        return {
            "company": report_data.get("company", ""),
            "stockCode": report_data.get("stock_code", ""),
            "researchDate": report_data.get("research_date", datetime.now().isoformat()),
            "sections": report_data.get("sections", [])
        }


