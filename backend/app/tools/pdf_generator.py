"""PDF 报告生成器"""
import os
import io
import tempfile
from typing import Dict, Any, List
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# 全局中文字体配置
import matplotlib.font_manager as fm

# 中文字体路径和属性
_CHINESE_FONT_PATH = None
_CHINESE_FONT_PROP = None

def _get_chinese_font():
    """获取中文字体 FontProperties"""
    global _CHINESE_FONT_PATH, _CHINESE_FONT_PROP
    
    if _CHINESE_FONT_PROP is not None:
        return _CHINESE_FONT_PROP
    
    # 尝试的字体路径
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/msyh.ttc',
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                _CHINESE_FONT_PROP = fm.FontProperties(fname=path)
                _CHINESE_FONT_PATH = path
                print(f"matplotlib 使用字体文件: {path}")
                return _CHINESE_FONT_PROP
            except Exception as e:
                print(f"加载字体失败 {path}: {e}")
    
    print("警告: 未找到中文字体")
    return None

# 初始化字体
_get_chinese_font()

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..config import get_settings

settings = get_settings()


class PDFGenerator:
    """PDF 报告生成器"""
    
    def __init__(self):
        # 注册中文字体
        self._register_fonts()
        
        # 创建样式
        self.styles = self._create_styles()
    
    def _register_fonts(self):
        """注册中文字体"""
        try:
            font_path = settings.pdf_font_path
            font_name = settings.pdf_font_name
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                pdfmetrics.registerFont(TTFont(f'{font_name}-Bold', font_path))
                self.font_name = font_name
                print(f"使用配置字体: {font_path}")
            else:
                # 尝试备用字体路径 (Windows + Linux/Docker)
                # 优先使用 TTF 格式的 WenQuanYi 字体
                backup_paths = [
                    # Linux/Docker - WenQuanYi 字体 (TTF 格式，reportlab 兼容)
                    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                    "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
                    "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
                    # Windows
                    "C:/Windows/Fonts/simhei.ttf",
                    "C:/Windows/Fonts/simsun.ttc",
                    "C:/Windows/Fonts/msyh.ttc",
                    "C:/Windows/Fonts/msyhl.ttc",
                ]
                
                font_registered = False
                for path in backup_paths:
                    if os.path.exists(path):
                        try:
                            # 对于 TTC 文件，尝试指定子字体索引
                            if path.endswith('.ttc'):
                                pdfmetrics.registerFont(TTFont('ChineseFont', path, subfontIndex=0))
                            else:
                                pdfmetrics.registerFont(TTFont('ChineseFont', path))
                            self.font_name = 'ChineseFont'
                            print(f"reportlab 使用字体: {path}")
                            font_registered = True
                            break
                        except Exception as font_err:
                            print(f"字体加载失败 {path}: {font_err}")
                            continue
                
                if not font_registered:
                    print("警告: 未找到中文字体，PDF 中文将无法正常显示")
                    self.font_name = 'Helvetica'
        except Exception as e:
            print(f"字体注册失败: {e}")
            self.font_name = 'Helvetica'
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """创建文档样式"""
        base_styles = getSampleStyleSheet()
        
        styles = {
            'title': ParagraphStyle(
                'Title',
                parent=base_styles['Title'],
                fontName=self.font_name,
                fontSize=24,
                leading=30,
                alignment=1,  # 居中
                spaceAfter=20,
                textColor=HexColor('#1a1a2e')
            ),
            'subtitle': ParagraphStyle(
                'Subtitle',
                parent=base_styles['Normal'],
                fontName=self.font_name,
                fontSize=12,
                leading=16,
                alignment=1,
                spaceAfter=30,
                textColor=HexColor('#666666')
            ),
            'heading1': ParagraphStyle(
                'Heading1',
                parent=base_styles['Heading1'],
                fontName=self.font_name,
                fontSize=18,
                leading=24,
                spaceBefore=20,
                spaceAfter=12,
                textColor=HexColor('#16213e')
            ),
            'heading2': ParagraphStyle(
                'Heading2',
                parent=base_styles['Heading2'],
                fontName=self.font_name,
                fontSize=14,
                leading=18,
                spaceBefore=15,
                spaceAfter=8,
                textColor=HexColor('#0f3460')
            ),
            'body': ParagraphStyle(
                'Body',
                parent=base_styles['Normal'],
                fontName=self.font_name,
                fontSize=11,
                leading=16,
                spaceAfter=10,
                textColor=HexColor('#333333')
            ),
            'highlight': ParagraphStyle(
                'Highlight',
                parent=base_styles['Normal'],
                fontName=self.font_name,
                fontSize=11,
                leading=16,
                backColor=HexColor('#f0f4f8'),
                borderPadding=10,
                spaceAfter=10
            ),
            'footer': ParagraphStyle(
                'Footer',
                parent=base_styles['Normal'],
                fontName=self.font_name,
                fontSize=9,
                textColor=HexColor('#999999'),
                alignment=1
            )
        }
        
        return styles
    
    def generate_report_pdf(self, report: Dict[str, Any], output_path: str):
        """
        生成研究报告 PDF
        
        Args:
            report: 报告内容字典
            output_path: 输出文件路径
        """
        # 创建文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        temp_files = []  # 收集需要清理的临时文件
        
        # 添加封面
        story.extend(self._create_cover(report))
        story.append(PageBreak())
        
        # 添加评分概览
        overview_elements, overview_temps = self._create_score_overview(report)
        story.extend(overview_elements)
        temp_files.extend(overview_temps)
        story.append(PageBreak())
        
        # 添加目录
        story.extend(self._create_toc(report))
        story.append(PageBreak())
        
        # 添加各个章节
        for section in report.get('sections', []):
            story.extend(self._create_section(section))
            story.append(Spacer(1, 20))
            
            # 如果是市场分析章节，添加 SWOT 表格
            if section.get('id') == 'market_analysis' and section.get('swot'):
                story.extend(self._create_swot_table(section.get('swot')))
                story.append(Spacer(1, 20))
        
        # 添加免责声明
        story.extend(self._create_disclaimer())
        
        # 生成 PDF
        try:
            doc.build(story)
        finally:
            # 清理临时文件
            for path in temp_files:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass
    
    def _get_metadata(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """获取报告 metadata"""
        return report.get('metadata', {})
    
    def _create_cover(self, report: Dict[str, Any]) -> List:
        """创建封面"""
        elements = []
        metadata = self._get_metadata(report)
        
        # 顶部留白
        elements.append(Spacer(1, 100))
        
        # 标题 - 从 metadata 中获取公司名称
        company = metadata.get('company_name') or metadata.get('company') or report.get('company', '未知公司')
        elements.append(Paragraph(
            f"{company}",
            self.styles['title']
        ))
        
        elements.append(Paragraph(
            "深度研究报告",
            self.styles['title']
        ))
        
        elements.append(Spacer(1, 30))
        
        # 副标题信息
        stock_code = metadata.get('stock_code') or report.get('stock_code', '')
        if stock_code:
            elements.append(Paragraph(
                f"股票代码：{stock_code}",
                self.styles['subtitle']
            ))
        
        # 行业信息
        industry = metadata.get('industry', '')
        if industry:
            elements.append(Paragraph(
                f"所属行业：{industry}",
                self.styles['subtitle']
            ))
        
        research_date = metadata.get('research_date') or report.get('research_date', datetime.now().isoformat())
        if isinstance(research_date, str):
            try:
                date_obj = datetime.fromisoformat(research_date.replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y年%m月%d日')
            except:
                date_str = research_date[:10]
        else:
            date_str = research_date.strftime('%Y年%m月%d日')
        
        elements.append(Paragraph(
            f"研究日期：{date_str}",
            self.styles['subtitle']
        ))
        
        elements.append(Spacer(1, 50))
        
        # 报告类型标签
        elements.append(Paragraph(
            "AI Agent 自动生成研究报告",
            self.styles['subtitle']
        ))
        
        return elements
    
    def _create_score_overview(self, report: Dict[str, Any]) -> tuple:
        """创建评分概览页，返回 (元素列表, 临时文件列表)"""
        elements = []
        temp_files = []
        metadata = self._get_metadata(report)
        sections = report.get('sections', [])
        
        elements.append(Paragraph("投资评分概览", self.styles['heading1']))
        elements.append(Spacer(1, 20))
        
        # 综合评分和建议
        overall_score = metadata.get('overall_score', 5)
        recommendation = metadata.get('recommendation', '观望')
        
        # 准备多维度数据
        dimensions = [
            ('财务分析', self._get_section_score(sections, 'financial_analysis')),
            ('市场分析', self._get_section_score(sections, 'market_analysis')),
            ('风险控制', self._calc_risk_score(sections)),
            ('投资价值', overall_score),
            ('成长潜力', round((self._get_section_score(sections, 'financial_analysis') + 
                            self._get_section_score(sections, 'market_analysis')) / 2)),
        ]
        
        # 生成仪表盘图
        gauge_path = self._create_gauge_chart(overall_score, recommendation)
        if gauge_path:
            temp_files.append(gauge_path)
        
        # 生成雷达图
        radar_path = self._create_radar_chart(dimensions)
        if radar_path:
            temp_files.append(radar_path)
        
        # 使用表格并排显示两个图表
        chart_row = []
        if gauge_path and os.path.exists(gauge_path):
            chart_row.append(Image(gauge_path, width=180, height=135))
        else:
            chart_row.append(Paragraph(f"综合评分: {overall_score}/10", self.styles['body']))
        
        if radar_path and os.path.exists(radar_path):
            chart_row.append(Image(radar_path, width=220, height=220))
        else:
            chart_row.append(Paragraph("多维度评分分析", self.styles['body']))
        
        if chart_row:
            chart_table = Table([chart_row], colWidths=[200, 250])
            chart_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(chart_table)
            elements.append(Spacer(1, 20))
        
        # 评分详情表格
        elements.append(Paragraph("评分详情", self.styles['heading2']))
        elements.append(Spacer(1, 10))
        
        dimension_data = [['维度', '评分', '评级']]
        for dim_name, dim_score in dimensions:
            rating = '优秀' if dim_score >= 8 else ('良好' if dim_score >= 6 else '一般')
            dimension_data.append([dim_name, f"{dim_score} / 10", rating])
        
        dim_table = Table(dimension_data, colWidths=[150, 100, 100])
        dim_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#dddddd')),
        ]))
        elements.append(dim_table)
        
        return elements, temp_files
    
    def _get_score_color(self, score: float) -> HexColor:
        """根据评分返回颜色"""
        if score >= 8:
            return HexColor('#10b981')
        elif score >= 6:
            return HexColor('#f59e0b')
        else:
            return HexColor('#ef4444')
    
    def _get_section_score(self, sections: List, section_id: str) -> float:
        """获取章节评分"""
        for section in sections:
            if section.get('id') == section_id:
                return section.get('overall_score', 5)
        return 5
    
    def _calc_risk_score(self, sections: List) -> float:
        """计算风险评分（风险越少分越高）"""
        for section in sections:
            if section.get('id') == 'risk_assessment':
                risk_count = len(section.get('risks', []))
                return max(10 - risk_count * 2, 3)
        return 5
    
    def _create_radar_chart(self, dimensions: List[tuple]) -> str:
        """
        创建雷达图并返回临时文件路径
        
        Args:
            dimensions: [(维度名, 分数), ...]
        
        Returns:
            临时图片文件路径
        """
        try:
            # 获取中文字体
            font_prop = _get_chinese_font()
            
            # 准备数据
            labels = [d[0] for d in dimensions]
            values = [d[1] for d in dimensions]
            num_vars = len(labels)
            
            # 计算角度
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            values += values[:1]  # 闭合多边形
            angles += angles[:1]
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            
            # 绘制雷达图
            ax.fill(angles, values, color='#6366f1', alpha=0.25)
            ax.plot(angles, values, color='#6366f1', linewidth=2)
            ax.scatter(angles[:-1], values[:-1], color='#6366f1', s=50, zorder=5)
            
            # 设置标签 (使用中文字体)
            ax.set_xticks(angles[:-1])
            if font_prop:
                ax.set_xticklabels(labels, size=12, fontproperties=font_prop)
            else:
                ax.set_xticklabels(labels, size=12)
            
            # 设置刻度范围
            ax.set_ylim(0, 10)
            ax.set_yticks([2, 4, 6, 8, 10])
            ax.set_yticklabels(['2', '4', '6', '8', '10'], size=8, color='gray')
            
            # 设置网格样式
            ax.grid(color='#e5e7eb', linestyle='-', linewidth=0.5)
            ax.spines['polar'].set_color('#d1d5db')
            
            # 添加标题 (使用中文字体)
            if font_prop:
                ax.set_title('多维度评分分析', size=14, fontweight='bold', pad=20, fontproperties=font_prop)
            else:
                ax.set_title('Score Analysis', size=14, fontweight='bold', pad=20)
            
            # 保存到临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"雷达图生成失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_gauge_chart(self, score: float, recommendation: str) -> str:
        """
        创建仪表盘图并返回临时文件路径
        """
        try:
            # 获取中文字体
            font_prop = _get_chinese_font()
            
            fig, ax = plt.subplots(figsize=(4, 3))
            
            # 确定颜色
            if score >= 8:
                color = '#10b981'
            elif score >= 6:
                color = '#f59e0b'
            else:
                color = '#ef4444'
            
            # 绘制半圆进度条
            theta = np.linspace(0, np.pi, 100)
            r = 1
            
            # 背景弧
            ax.fill_between(theta, 0.7, 1, alpha=0.1, color='gray')
            
            # 进度弧
            progress_angle = np.pi * (score / 10)
            theta_progress = np.linspace(0, progress_angle, 100)
            ax.fill_between(theta_progress, 0.7, 1, alpha=0.8, color=color)
            
            # 设置为极坐标效果
            ax.set_xlim(-0.2, np.pi + 0.2)
            ax.set_ylim(0, 1.5)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # 添加分数文本
            ax.text(np.pi/2, 0.3, f'{score}', ha='center', va='center', 
                   fontsize=36, fontweight='bold', color=color)
            
            # 添加"综合评分"文本 (使用中文字体)
            if font_prop:
                ax.text(np.pi/2, 0, '综合评分', ha='center', va='center', 
                       fontsize=12, color='gray', fontproperties=font_prop)
            else:
                ax.text(np.pi/2, 0, 'Score', ha='center', va='center', 
                       fontsize=12, color='gray')
            
            # 添加建议标签 (使用中文字体)
            rec_colors = {
                '买入': '#10b981', '持有': '#f59e0b', 
                '卖出': '#ef4444', '观望': '#6b7280'
            }
            rec_color = rec_colors.get(recommendation, '#6b7280')
            if font_prop:
                ax.text(np.pi/2, -0.3, recommendation, ha='center', va='center',
                       fontsize=14, fontweight='bold', color=rec_color,
                       fontproperties=font_prop,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=rec_color, alpha=0.15))
            else:
                ax.text(np.pi/2, -0.3, recommendation, ha='center', va='center',
                       fontsize=14, fontweight='bold', color=rec_color,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=rec_color, alpha=0.15))
            
            # 保存
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"仪表盘图生成失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_swot_table(self, swot: Dict[str, Any]) -> List:
        """创建 SWOT 分析表格"""
        elements = []
        
        elements.append(Paragraph("SWOT 分析矩阵", self.styles['heading2']))
        elements.append(Spacer(1, 10))
        
        # 格式化 SWOT 数据
        def format_items(items: List) -> str:
            if not items:
                return "暂无数据"
            return "\n".join([f"• {item}" for item in items[:5]])
        
        strengths = format_items(swot.get('strengths', []))
        weaknesses = format_items(swot.get('weaknesses', []))
        opportunities = format_items(swot.get('opportunities', []))
        threats = format_items(swot.get('threats', []))
        
        swot_data = [
            ['优势 (Strengths)', '劣势 (Weaknesses)'],
            [strengths, weaknesses],
            ['机会 (Opportunities)', '威胁 (Threats)'],
            [opportunities, threats],
        ]
        
        swot_table = Table(swot_data, colWidths=[230, 230])
        swot_table.setStyle(TableStyle([
            # 标题行样式
            ('BACKGROUND', (0, 0), (0, 0), HexColor('#10b981')),
            ('BACKGROUND', (1, 0), (1, 0), HexColor('#f59e0b')),
            ('BACKGROUND', (0, 2), (0, 2), HexColor('#3b82f6')),
            ('BACKGROUND', (1, 2), (1, 2), HexColor('#ef4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 2), (-1, 2), white),
            # 内容行样式
            ('BACKGROUND', (0, 1), (0, 1), HexColor('#ecfdf5')),
            ('BACKGROUND', (1, 1), (1, 1), HexColor('#fffbeb')),
            ('BACKGROUND', (0, 3), (0, 3), HexColor('#eff6ff')),
            ('BACKGROUND', (1, 3), (1, 3), HexColor('#fef2f2')),
            # 通用样式
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 2), (-1, 2), 11),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('FONTSIZE', (0, 3), (-1, 3), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#dddddd')),
        ]))
        elements.append(swot_table)
        
        return elements
    
    def _create_toc(self, report: Dict[str, Any]) -> List:
        """创建目录"""
        elements = []
        
        elements.append(Paragraph("目 录", self.styles['heading1']))
        elements.append(Spacer(1, 20))
        
        for i, section in enumerate(report.get('sections', []), 1):
            title = section.get('title', '')
            elements.append(Paragraph(
                f"{i}. {title}",
                self.styles['body']
            ))
            
            # 二级标题
            for j, subsection in enumerate(section.get('subsections', []), 1):
                sub_title = subsection.get('title', '')
                elements.append(Paragraph(
                    f"    {i}.{j} {sub_title}",
                    self.styles['body']
                ))
        
        return elements
    
    def _create_section(self, section: Dict[str, Any]) -> List:
        """创建章节内容"""
        elements = []
        
        title = section.get('title', '')
        elements.append(Paragraph(title, self.styles['heading1']))
        
        # 主内容
        content = section.get('content', '')
        if content:
            elements.append(Paragraph(content, self.styles['body']))
        
        # 关键点
        key_points = section.get('key_points', [])
        if key_points:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("要点：", self.styles['heading2']))
            for point in key_points:
                elements.append(Paragraph(f"• {point}", self.styles['body']))
        
        # 子章节
        for subsection in section.get('subsections', []):
            sub_title = subsection.get('title', '')
            sub_content = subsection.get('content', '')
            
            elements.append(Paragraph(sub_title, self.styles['heading2']))
            if sub_content:
                elements.append(Paragraph(sub_content, self.styles['body']))
            
            # 评分
            score = subsection.get('score')
            if score is not None:
                elements.append(Paragraph(
                    f"评分：{score}/10",
                    self.styles['highlight']
                ))
        
        # 风险列表 - 使用表格展示
        risks = section.get('risks', [])
        if risks:
            elements.append(Paragraph("风险因素：", self.styles['heading2']))
            elements.append(Spacer(1, 10))
            
            risk_data = [['风险类型', '风险描述', '严重程度']]
            for risk in risks:
                if isinstance(risk, dict):
                    risk_type = risk.get('type', '其他')
                    risk_desc = risk.get('description', '')
                    severity = risk.get('severity', '中')
                    risk_data.append([risk_type, risk_desc, severity])
                else:
                    risk_data.append(['风险', str(risk), '中'])
            
            risk_table = Table(risk_data, colWidths=[80, 280, 60])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#dddddd')),
            ]))
            elements.append(risk_table)
        
        # 投资建议特殊处理
        if section.get('recommendation'):
            elements.append(Paragraph(
                f"投资建议：{section['recommendation']}",
                self.styles['highlight']
            ))
        
        if section.get('reasoning'):
            elements.append(Paragraph(section['reasoning'], self.styles['body']))
        
        # 催化剂
        catalysts = section.get('catalysts', [])
        if catalysts:
            elements.append(Paragraph("上涨催化剂：", self.styles['heading2']))
            for catalyst in catalysts:
                elements.append(Paragraph(f"• {catalyst}", self.styles['body']))
        
        return elements
    
    def _create_disclaimer(self) -> List:
        """创建免责声明"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("免责声明", self.styles['heading1']))
        elements.append(Spacer(1, 10))
        
        disclaimer_text = """
        本报告由 AI Agent 系统自动生成，仅供参考，不构成任何投资建议。
        
        报告中的信息来源于公开渠道，我们力求但不保证信息的准确性和完整性。
        
        投资者应当自行判断并承担投资决策的风险。过往业绩不代表未来表现。
        
        未经许可，不得转载或引用本报告内容。
        """
        
        elements.append(Paragraph(disclaimer_text, self.styles['body']))
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['footer']
        ))
        
        return elements



