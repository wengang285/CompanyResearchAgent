"""数据收集 Agent - 使用 Agno 最新 API"""
import json
import re
from typing import Dict, Any

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings
from ..tools.serper_search import SerperSearchTool

settings = get_settings()


class DataCollectorAgent:
    """
    数据收集 Agent
    
    负责:
    1. 使用 Serper 搜索公司相关信息
    2. 收集财务数据、新闻、公告
    3. 整理并结构化数据
    """
    
    def __init__(self):
        # 创建 LLM 模型 - 使用 OpenAILike 兼容各种 API
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        # 搜索工具
        self.search_tool = SerperSearchTool()
        
        # 创建 Agno Agent
        self.agent = Agent(
            name="DataCollector",
            model=self.model,
            description="专业的数据收集助手，负责收集上市公司的各类信息",
            instructions="""你是一个专业的数据收集助手，负责收集上市公司的各类信息。
收集信息时要全面、准确，包括公司简介、财务数据、新闻动态等。
整理数据时要结构化，便于后续分析使用。
请用中文回复。""",
            markdown=True,
        )
    
    async def collect_company_data(self, company: str, depth: str = "deep") -> Dict[str, Any]:
        """
        收集公司全面数据
        
        Args:
            company: 公司名称或股票代码
            depth: 研究深度 (basic, standard, deep)
                - basic: 仅收集基本信息和最新新闻
                - standard: 收集公司信息、财务数据、新闻、行业分析
                - deep: 收集所有信息并进行更深入的搜索
        
        Returns:
            收集到的结构化数据
        """
        print(f"[DataCollector] 收集数据, 深度: {depth}")
        
        # 根据深度决定收集范围
        if depth == "basic":
            # 基础模式: 只收集核心信息
            all_data = await self.search_tool.collect_basic_data(company)
        elif depth == "deep":
            # 深度模式: 收集更全面的数据
            all_data = await self.search_tool.collect_deep_data(company)
        else:
            # 标准模式
            all_data = await self.search_tool.collect_all_data(company)
        
        # 使用 Agent 整理数据
        structured_data = await self._structure_data(all_data, company, depth)
        
        return structured_data
    
    async def _structure_data(self, raw_data: Dict[str, Any], company: str, depth: str = "deep") -> Dict[str, Any]:
        """使用 Agent 整理原始数据"""
        
        # 提取搜索结果中的关键信息
        company_info = self._extract_search_results(raw_data.get("company_info", {}))
        financial_data = self._extract_search_results(raw_data.get("financial_data", {}))
        news = self._extract_news_results(raw_data.get("news", {}))
        industry = self._extract_search_results(raw_data.get("industry_analysis", {}))
        
        # 根据深度调整提取结果数量
        result_count = {"basic": 2, "standard": 3, "deep": 5}.get(depth, 3)
        
        prompt = f"""请根据以下搜索结果，整理 {company} 公司的关键信息。

公司信息搜索结果:
{company_info}

财务数据搜索结果:
{financial_data}

最新新闻:
{news}

行业分析:
{industry}

请以 JSON 格式返回以下结构的信息:
{{
    "company_name": "公司全称",
    "stock_code": "股票代码(如有)",
    "industry": "所属行业",
    "main_business": "主营业务描述",
    "key_products": ["主要产品或服务"],
    "financial_highlights": {{
        "revenue": "营收情况",
        "profit": "利润情况",
        "growth": "增长情况"
    }},
    "recent_news": ["最新动态1", "最新动态2"],
    "market_position": "市场地位描述",
    "competitors": ["主要竞争对手"]
}}

只返回 JSON，不要其他内容。"""

        try:
            # 使用 Agno 最新 API
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 提取 JSON 内容
            json_match = re.search(r'\{[\s\S]*\}', content)
            
            if json_match:
                structured = json.loads(json_match.group())
                return {
                    "company": company,
                    "structured_info": structured,
                    "raw_data": raw_data
                }
        except Exception as e:
            print(f"[DataCollector] 数据结构化失败: {e}")
        
        # 返回默认结构
        return {
            "company": company,
            "structured_info": {
                "company_name": company,
                "stock_code": "",
                "industry": "",
                "main_business": "",
                "key_products": [],
                "financial_highlights": {},
                "recent_news": [],
                "market_position": "",
                "competitors": []
            },
            "raw_data": raw_data
        }
    
    def _extract_search_results(self, data: Dict[str, Any]) -> str:
        """从搜索结果中提取文本"""
        results = []
        for result_set in data.get("results", []):
            if isinstance(result_set, dict) and "organic" in result_set:
                for item in result_set["organic"][:3]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    results.append(f"- {title}: {snippet}")
        
        return "\n".join(results) if results else "无搜索结果"
    
    def _extract_news_results(self, data: Dict[str, Any]) -> str:
        """从新闻搜索结果中提取文本"""
        results = []
        news_data = data.get("results", {})
        
        if isinstance(news_data, dict) and "news" in news_data:
            for item in news_data["news"][:5]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                date = item.get("date", "")
                results.append(f"- [{date}] {title}: {snippet}")
        
        return "\n".join(results) if results else "无最新新闻"
