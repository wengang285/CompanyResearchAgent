"""研究工作流 - 协调各个 Agent 完成研究任务"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from ..agents.search_agent import SearchAgent
from ..agents.data_agent import DataAgent
from ..agents.finance_agent import FinanceAgent
from ..agents.market_agent import MarketAgent
from ..agents.insight_agent import InsightAgent
from ..agents.writer_agent import WriterAgent


class WorkflowStep(Enum):
    """工作流步骤"""
    INIT = "init"
    SEARCH = "search"
    DATA_PROCESSING = "data_processing"
    FINANCIAL_ANALYSIS = "financial_analysis"
    MARKET_ANALYSIS = "market_analysis"
    INSIGHT_EXTRACTION = "insight_extraction"
    REPORT_WRITING = "report_writing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowState:
    """工作流状态"""
    company: str
    depth: str = "deep"
    focus_areas: List[str] = field(default_factory=list)
    
    # 各步骤结果
    search_result: Optional[Dict[str, Any]] = None
    data_result: Optional[Dict[str, Any]] = None
    finance_result: Optional[Dict[str, Any]] = None
    market_result: Optional[Dict[str, Any]] = None
    insight_result: Optional[Dict[str, Any]] = None
    report_result: Optional[Dict[str, Any]] = None
    
    # 状态信息
    current_step: WorkflowStep = WorkflowStep.INIT
    progress: int = 0
    error: Optional[str] = None


class ResearchWorkflow:
    """
    研究工作流
    
    协调 6 个核心 Agent 完成上市公司研究:
    1. SearchAgent  -> 搜索收集
    2. DataAgent    -> 数据整理
    3. FinanceAgent -> 财务分析 ─┬─> 并行执行
    4. MarketAgent  -> 市场分析 ─┘
    5. InsightAgent -> 洞察提炼
    6. WriterAgent  -> 报告撰写
    """
    
    def __init__(self):
        # 初始化所有 Agent
        self.search_agent = SearchAgent()
        self.data_agent = DataAgent()
        self.finance_agent = FinanceAgent()
        self.market_agent = MarketAgent()
        self.insight_agent = InsightAgent()
        self.writer_agent = WriterAgent()
    
    async def run(
        self,
        company: str,
        depth: str = "deep",
        focus_areas: List[str] = None,
        progress_callback: Optional[Callable] = None,
        result_callback: Optional[Callable] = None,
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        执行研究工作流
        
        Args:
            company: 公司名称或代码
            depth: 研究深度 (basic, standard, deep)
            focus_areas: 关注领域
            progress_callback: 进度回调 (progress, agent, task, estimated_time)
            result_callback: 结果回调 (agent, result_summary, result_data)
            stream_callback: 流式回调 (message_id, agent_name, chunk, finished)
        
        Returns:
            完整的研究报告
        """
        focus_areas = focus_areas or []
        
        # 初始化状态
        state = WorkflowState(
            company=company,
            depth=depth,
            focus_areas=focus_areas
        )
        
        print(f"\n{'='*60}")
        print(f"[Workflow] 开始研究: {company}")
        print(f"[Workflow] 研究深度: {depth}")
        print(f"[Workflow] 关注领域: {focus_areas}")
        print(f"{'='*60}\n")
        
        try:
            # ============ Step 1: 搜索收集 (0-15%) ============
            state.current_step = WorkflowStep.SEARCH
            if progress_callback:
                await progress_callback(5, "SearchAgent", "🔍 正在搜索公司信息...", 120)
            
            state.search_result = await self.search_agent.run(company, depth=depth)
            state.progress = 15
            
            # 发送搜索结果
            if result_callback:
                search_summary = self._summarize_search_result(state.search_result)
                await result_callback("SearchAgent", search_summary, {
                    "type": "search",
                    "company": company
                })
            
            # ============ Step 2: 数据整理 (15-30%) ============
            state.current_step = WorkflowStep.DATA_PROCESSING
            if progress_callback:
                await progress_callback(18, "DataAgent", "📊 正在整理数据...", 90)
            
            state.data_result = await self.data_agent.run(
                state.search_result,
                depth=depth,
                stream_callback=stream_callback
            )
            state.progress = 30
            
            # 发送数据整理结果
            if result_callback:
                data_summary = self._summarize_data_result(state.data_result)
                await result_callback("DataAgent", data_summary, {
                    "type": "data",
                    "structured_data": state.data_result.get("structured_data", {})
                })
            
            # ============ Step 3 & 4: 并行分析 (30-60%) ============
            state.current_step = WorkflowStep.FINANCIAL_ANALYSIS
            if progress_callback:
                await progress_callback(35, "FinanceAgent", "💰 正在进行财务分析...", 70)
            
            # 并行执行财务分析和市场分析
            finance_task = asyncio.create_task(
                self.finance_agent.run(state.data_result, depth=depth, stream_callback=stream_callback)
            )
            market_task = asyncio.create_task(
                self.market_agent.run(state.data_result, depth=depth, stream_callback=stream_callback)
            )
            
            state.finance_result, state.market_result = await asyncio.gather(
                finance_task,
                market_task
            )
            state.progress = 60
            
            # 发送财务分析结果
            if result_callback:
                fin_summary = self._summarize_finance_result(state.finance_result)
                await result_callback("FinanceAgent", fin_summary, {
                    "type": "finance",
                    "score": state.finance_result.get("financial_analysis", {}).get("overall_score", 5)
                })
            
            # 发送市场分析结果
            if result_callback:
                mkt_summary = self._summarize_market_result(state.market_result)
                await result_callback("MarketAgent", mkt_summary, {
                    "type": "market",
                    "score": state.market_result.get("market_analysis", {}).get("market_position", {}).get("score", 5)
                })
            
            # ============ Step 5: 洞察提炼 (60-80%) ============
            state.current_step = WorkflowStep.INSIGHT_EXTRACTION
            if progress_callback:
                await progress_callback(65, "InsightAgent", "💡 正在提炼投资洞察...", 30)
            
            state.insight_result = await self.insight_agent.run(
                company=company,
                data=state.data_result,
                financial_analysis=state.finance_result,
                market_analysis=state.market_result,
                depth=depth,
                stream_callback=stream_callback
            )
            state.progress = 80
            
            # 发送洞察结果
            if result_callback:
                insight_summary = self._summarize_insight_result(state.insight_result)
                await result_callback("InsightAgent", insight_summary, {
                    "type": "insight",
                    "recommendation": state.insight_result.get("insights", {}).get("recommendation", {}).get("rating", "观望")
                })
            
            # ============ Step 6: 报告撰写 (80-100%) ============
            state.current_step = WorkflowStep.REPORT_WRITING
            if progress_callback:
                await progress_callback(85, "WriterAgent", "📝 正在撰写研究报告...", 15)
            
            state.report_result = await self.writer_agent.run(
                company=company,
                data=state.data_result,
                financial_analysis=state.finance_result,
                market_analysis=state.market_result,
                insights=state.insight_result,
                depth=depth,
                stream_callback=stream_callback
            )
            state.progress = 100
            state.current_step = WorkflowStep.COMPLETED
            
            if progress_callback:
                await progress_callback(95, "WriterAgent", "✅ 报告生成完成", 5)
            
            print(f"\n{'='*60}")
            print(f"[Workflow] 研究完成: {company}")
            print(f"{'='*60}\n")
            
            # 返回最终报告
            return state.report_result.get("report", {})
            
        except Exception as e:
            state.current_step = WorkflowStep.FAILED
            state.error = str(e)
            
            print(f"\n[Workflow] 研究失败: {e}")
            import traceback
            traceback.print_exc()
            
            raise
    
    def _summarize_search_result(self, result: Dict) -> str:
        """生成搜索结果摘要"""
        search_results = result.get("search_results", {})
        news_count = 0
        news_data = search_results.get("news", {}).get("results", {})
        if isinstance(news_data, dict) and "news" in news_data:
            news_count = len(news_data.get("news", []))
        
        return f"已收集公司信息、财务数据和 {news_count} 条相关新闻"
    
    def _summarize_data_result(self, result: Dict) -> str:
        """生成数据整理摘要"""
        data = result.get("structured_data", {})
        company_name = data.get("company_name", "")
        industry = data.get("industry", "")
        if company_name and industry:
            return f"识别到「{company_name}」，所属行业：{industry}"
        return "已完成数据结构化整理"
    
    def _summarize_finance_result(self, result: Dict) -> str:
        """生成财务分析摘要"""
        analysis = result.get("financial_analysis", {})
        score = analysis.get("overall_score", 5)
        strengths = analysis.get("strengths", [])
        strength_text = "、".join(strengths[:2]) if strengths else "待进一步分析"
        return f"财务健康度评分 {score}/10，主要优势：{strength_text}"
    
    def _summarize_market_result(self, result: Dict) -> str:
        """生成市场分析摘要"""
        analysis = result.get("market_analysis", {})
        score = analysis.get("market_position", {}).get("score", 5)
        rating = analysis.get("outlook", {}).get("rating", "中性")
        return f"市场地位评分 {score}/10，发展前景：{rating}"
    
    def _summarize_insight_result(self, result: Dict) -> str:
        """生成洞察摘要"""
        insights = result.get("insights", {})
        recommendation = insights.get("recommendation", {}).get("rating", "观望")
        confidence = insights.get("recommendation", {}).get("confidence", "低")
        return f"投资评级：{recommendation}（置信度：{confidence}）"
    
    def get_workflow_diagram(self) -> str:
        """返回工作流图示"""
        return """
┌─────────────────────────────────────────────────────────────┐
│                    Research Workflow                         │
└─────────────────────────────────────────────────────────────┘

  ┌─────────────┐
  │ SearchAgent │  (1) 搜索收集公司信息
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  DataAgent  │  (2) 数据整理和结构化
  └──────┬──────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Finance│ │Market │  (3)(4) 并行分析
│ Agent │ │ Agent │
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         ▼
  ┌─────────────┐
  │InsightAgent │  (5) 提炼投资洞察
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ WriterAgent │  (6) 撰写研究报告
  └──────┬──────┘
         │
         ▼
    ┌─────────┐
    │  Report │
    └─────────┘
"""

