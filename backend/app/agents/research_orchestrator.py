"""主协调 Agent - 使用 Agno 最新 API 协调各子 Agent"""
import asyncio
from typing import List, Callable, Optional

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings
from .data_collector import DataCollectorAgent
from .financial_analyzer import FinancialAnalyzerAgent
from .market_analyzer import MarketAnalyzerAgent
from .report_generator import ReportGeneratorAgent

settings = get_settings()


class ResearchOrchestrator:
    """
    主协调 Agent
    
    负责:
    1. 分解研究任务
    2. 协调其他 Agent
    3. 汇总研究结果
    4. 生成最终报告
    """
    
    def __init__(self):
        # 创建 LLM 模型
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        # 主协调 Agent
        self.coordinator = Agent(
            name="ResearchCoordinator",
            model=self.model,
            description="研究协调员，负责协调整个研究流程",
            instructions="""你是一个专业的研究协调员，负责协调上市公司研究流程。
你的任务是确保数据收集、财务分析、市场分析和报告生成各环节顺利进行。
请用中文回复。""",
            markdown=True,
        )
        
        # 初始化子 Agent
        self.data_collector = DataCollectorAgent()
        self.financial_analyzer = FinancialAnalyzerAgent()
        self.market_analyzer = MarketAnalyzerAgent()
        self.report_generator = ReportGeneratorAgent()
    
    async def run_research(
        self,
        company: str,
        depth: str = "deep",
        focus_areas: List[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        执行完整的研究流程
        
        Args:
            company: 公司名称或代码
            depth: 研究深度 (basic, standard, deep)
            focus_areas: 关注重点领
            progress_callback: 进度回调函数
        
        Returns:
            完整的研究报告
        """
        focus_areas = focus_areas or []
        
        print(f"[Orchestrator] 开始研究: {company}")
        print(f"[Orchestrator] 研究深度: {depth}")
        print(f"[Orchestrator] 关注领域: {focus_areas}")
        
        try:
            # ========== 阶段1: 数据收集 (0-30%) ==========
            if progress_callback:
                await progress_callback(5, "DataCollector", "开始收集公司数据...", 180)
            
            print("[Orchestrator] 阶段1: 数据收集")
            collected_data = await self.data_collector.collect_company_data(company, depth=depth)
            print(f"[Orchestrator] 数据收集完成, 公司: {collected_data.get('structured_info', {}).get('company_name', company)}")
            
            if progress_callback:
                await progress_callback(30, "DataCollector", "数据收集完成", 120)
            
            # ========== 阶段2: 并行分析 (30-70%) ==========
            if progress_callback:
                await progress_callback(35, "Analyzers", "开始分析...", 100)
            
            print("[Orchestrator] 阶段2: 并行分析 (财务 + 市场)")
            
            # 并行执行财务分析和市场分析，传递深度参数
            financial_task = asyncio.create_task(
                self.financial_analyzer.analyze_financials(collected_data, company, depth=depth)
            )
            market_task = asyncio.create_task(
                self.market_analyzer.analyze_market_position(collected_data, company, depth=depth)
            )
            
            if progress_callback:
                await progress_callback(45, "FinancialAnalyzer", "分析财务数据...", 80)
            
            # 等待分析完成
            financial_analysis, market_analysis = await asyncio.gather(
                financial_task,
                market_task
            )
            
            print(f"[Orchestrator] 财务分析完成, 评分: {financial_analysis.get('overall', {}).get('score', 'N/A')}")
            print(f"[Orchestrator] 市场分析完成, 评级: {market_analysis.get('outlook', {}).get('overall_rating', 'N/A')}")
            
            if progress_callback:
                await progress_callback(70, "Analyzers", "分析完成", 50)
            
            # ========== 阶段3: 报告生成 (70-100%) ==========
            if progress_callback:
                await progress_callback(75, "ReportGenerator", "生成研究报告...", 30)
            
            print("[Orchestrator] 阶段3: 生成报告")
            
            # 汇总分析结果
            analysis_results = {
                "company": company,
                "collected_data": collected_data,
                "financial_analysis": financial_analysis,
                "market_analysis": market_analysis,
                "depth": depth,
                "focus_areas": focus_areas
            }
            
            # 生成最终报告
            report = await self.report_generator.generate_report(analysis_results)
            
            print(f"[Orchestrator] 报告生成完成, 章节数: {len(report.get('sections', []))}")
            
            if progress_callback:
                await progress_callback(95, "ReportGenerator", "报告生成完成", 5)
            
            print(f"[Orchestrator] 研究完成: {company}")
            return report
            
        except Exception as e:
            print(f"[Orchestrator] 研究过程出错: {e}")
            import traceback
            traceback.print_exc()
            raise
