"""搜索 Agent - 负责执行所有搜索查询"""
import asyncio
from typing import Dict, Any, List

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings
from ..tools.serper_search import SerperSearchTool

settings = get_settings()


class SearchAgent:
    """
    搜索 Agent
    
    职责:
    - 执行各类搜索查询
    - 收集公司基本信息、财务数据、新闻、行业信息
    - 返回原始搜索结果
    """
    
    name = "SearchAgent"
    description = "负责执行搜索查询，收集公司相关的公开信息"
    
    def __init__(self):
        self.search_tool = SerperSearchTool()
    
    async def run(self, company: str, depth: str = "deep") -> Dict[str, Any]:
        """
        执行全面搜索
        
        Args:
            company: 公司名称或股票代码
            depth: 研究深度 (basic, standard, deep)
        
        Returns:
            原始搜索结果
        """
        print(f"[SearchAgent] 开始搜索: {company}, 深度: {depth}")
        
        # 根据深度选择搜索方法
        if depth == "basic":
            results = await self.search_tool.collect_basic_data(company)
        elif depth == "deep":
            results = await self.search_tool.collect_deep_data(company)
        else:
            results = await self.search_tool.collect_all_data(company)
        
        print(f"[SearchAgent] 搜索完成，收集了 {len(results)} 类数据")
        
        return {
            "company": company,
            "search_results": results,
            "depth": depth,
            "status": "success"
        }




