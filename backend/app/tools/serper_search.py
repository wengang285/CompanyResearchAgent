"""Google Serper API 搜索工具"""
import logging
from datetime import datetime, timedelta

import httpx
from typing import List, Dict, Any, Optional
from ..config import get_settings

settings = get_settings()


class SerperSearchTool:
    """Google Serper API 搜索工具"""
    
    def __init__(self):
        self.api_key = settings.serper_api_key
        self.base_url = "https://google.serper.dev/search"
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search",
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            search_type: 搜索类型 (search, news, images)
            time_range: 时间范围 (d: 天, w: 周, m: 月, y: 年)
        
        Returns:
            搜索结果字典
        """
        # 构建搜索参数
        search_params = {
            "q": query,
            "num": num_results,
            "gl": "cn",
            "hl": "zh-cn",
        }
        
        # 添加时间范围（如果指定）
        if time_range:
            search_params["tbs"] = f"qdr:{time_range}"  # qdr:d(天), qdr:w(周), qdr:m(月), qdr:y(年)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                json=search_params,
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            print(f"results: {response.json()}")
            return response.json()
    
    async def search_company_info(self, company: str) -> Dict[str, Any]:
        """搜索公司基本信息"""
        queries = [
            f"{company} 公司简介 主营业务",
            f"{company} 公司官网 企业介绍",
        ]
        
        results = []
        for query in queries:
            try:
                result = await self.search(query, num_results=5)
                results.append(result)
            except Exception as e:
                print(f"搜索失败: {query}, 错误: {e}")
        
        return {"type": "company_info", "results": results}
    
    async def search_financial_data(self, company: str) -> Dict[str, Any]:
        """搜索财务数据（优先最新数据）"""
        current_year = datetime.now().year
        last_year = current_year - 1
        
        # 优先搜索最新年份的财务数据
        queries = [
            f"{company} {current_year}年 财务报表 年报",
            f"{company} {last_year}年 年报 财务数据",
            f"{company} 最新 营收 净利润 {current_year}",
            f"{company} 股票 市值 估值 最新",
        ]
        
        results = []
        for query in queries:
            try:
                # 财务数据优先搜索最近一年的
                result = await self.search(query, num_results=5, time_range="y")
                results.append(result)
            except Exception as e:
                print(f"搜索失败: {query}, 错误: {e}")
        
        return {"type": "financial_data", "results": results}
    
    async def search_recent_news(self, company: str, days: int = 30) -> Dict[str, Any]:
        """
        搜索最新新闻
        
        Args:
            company: 公司名称
            days: 搜索最近N天的新闻（默认30天）
        """
        # 根据天数选择时间范围关键词
        if days <= 7:
            time_keyword = "最近一周"
        elif days <= 30:
            time_keyword = "最近一个月"
        elif days <= 90:
            time_keyword = "最近三个月"
        else:
            time_keyword = "最新"
        
        query = f"{company} {time_keyword} 新闻 动态"
        
        try:
            # 使用新闻搜索
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 新闻API可能支持时间参数
                news_params = {
                    "q": query,
                    "num": 10,
                    "gl": "cn",
                    "hl": "zh-cn",
                }
                
                # 尝试添加时间范围（如果API支持）
                if days <= 7:
                    news_params["tbs"] = "qdr:d"  # 最近一天
                elif days <= 30:
                    news_params["tbs"] = "qdr:w"  # 最近一周
                elif days <= 90:
                    news_params["tbs"] = "qdr:m"  # 最近一个月
                
                response = await client.post(
                    "https://google.serper.dev/news",
                    json=news_params,
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return {"type": "news", "results": response.json()}
        except Exception as e:
            print(f"新闻搜索失败: {e}")
            return {"type": "news", "results": [], "error": str(e)}
    
    async def search_industry_analysis(self, company: str) -> Dict[str, Any]:
        """搜索行业分析（优先最新分析）"""
        current_year = datetime.now().year
        queries = [
            f"{company} {current_year}年 行业分析 市场地位",
            f"{company} 最新 竞争对手 行业格局",
            f"{company} 行业趋势 发展前景 {current_year}",
        ]
        
        results = []
        for query in queries:
            try:
                # 行业分析优先搜索最近一年的
                result = await self.search(query, num_results=5, time_range="y")
                results.append(result)
            except Exception as e:
                print(f"搜索失败: {query}, 错误: {e}")
        
        return {"type": "industry_analysis", "results": results}
    
    async def collect_basic_data(self, company: str) -> Dict[str, Any]:
        """收集基础数据 (basic 深度)"""
        import asyncio
        
        print(f"[SerperSearch] 基础数据收集: {company}")
        
        # 只收集公司基本信息和最新新闻
        tasks = [
            self.search_company_info(company),
            self.search_recent_news(company),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "company": company,
            "company_info": results[0] if not isinstance(results[0], Exception) else {},
            "financial_data": {},  # 基础模式不收集财务数据
            "news": results[1] if not isinstance(results[1], Exception) else {},
            "industry_analysis": {},  # 基础模式不收集行业分析
        }
    
    async def collect_all_data(self, company: str) -> Dict[str, Any]:
        """收集标准数据 (standard 深度)"""
        import asyncio
        
        print(f"[SerperSearch] 标准数据收集: {company}")
        
        # 并行执行所有搜索
        tasks = [
            self.search_company_info(company),
            self.search_financial_data(company),
            self.search_recent_news(company),
            self.search_industry_analysis(company),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "company": company,
            "company_info": results[0] if not isinstance(results[0], Exception) else {},
            "financial_data": results[1] if not isinstance(results[1], Exception) else {},
            "news": results[2] if not isinstance(results[2], Exception) else {},
            "industry_analysis": results[3] if not isinstance(results[3], Exception) else {},
        }
    
    async def collect_deep_data(self, company: str) -> Dict[str, Any]:
        """收集深度数据 (deep 深度)"""
        import asyncio
        
        print(f"[SerperSearch] 深度数据收集: {company}")
        
        # 深度模式: 更多搜索查询
        tasks = [
            self.search_company_info(company),
            self.search_financial_data(company),
            self.search_recent_news(company),
            self.search_industry_analysis(company),
            self._search_deep_financials(company),
            self._search_management_team(company),
            self._search_risk_factors(company),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "company": company,
            "company_info": results[0] if not isinstance(results[0], Exception) else {},
            "financial_data": results[1] if not isinstance(results[1], Exception) else {},
            "news": results[2] if not isinstance(results[2], Exception) else {},
            "industry_analysis": results[3] if not isinstance(results[3], Exception) else {},
            "deep_financials": results[4] if not isinstance(results[4], Exception) else {},
            "management": results[5] if not isinstance(results[5], Exception) else {},
            "risk_factors": results[6] if not isinstance(results[6], Exception) else {},
        }
    
    async def _search_deep_financials(self, company: str) -> Dict[str, Any]:
        """深度搜索财务数据（优先最新数据）"""
        current_year = datetime.now().year
        last_year = current_year - 1
        queries = [
            f"{company} {current_year}年 资产负债表 详细",
            f"{company} {last_year}年 现金流量表 分析",
            f"{company} 最新 毛利率 净利率 ROE {current_year}",
            f"{company} {current_year}年 应收账款 存货周转",
        ]
        
        results = []
        for query in queries:
            try:
                # 财务数据优先搜索最近一年的
                result = await self.search(query, num_results=5, time_range="y")
                results.append(result)
            except Exception as e:
                print(f"搜索失败: {query}, 错误: {e}")
        
        return {"type": "deep_financials", "results": results}
    
    async def _search_management_team(self, company: str) -> Dict[str, Any]:
        """搜索管理团队信息"""
        queries = [
            f"{company} 管理层 高管团队",
            f"{company} 董事长 CEO 简历",
        ]
        
        results = []
        for query in queries:
            try:
                result = await self.search(query, num_results=5)
                results.append(result)
            except Exception as e:
                print(f"搜索失败: {query}, 错误: {e}")
        
        return {"type": "management", "results": results}
    
    async def _search_risk_factors(self, company: str) -> Dict[str, Any]:
        """搜索风险因素（优先最新风险）"""
        current_year = datetime.now().year
        queries = [
            f"{company} {current_year}年 风险提示 风险因素",
            f"{company} 最新 诉讼 监管 处罚",
            f"{company} 最近 风险事件 负面新闻",
        ]
        
        results = []
        for query in queries:
            try:
                # 风险因素优先搜索最近一年的
                result = await self.search(query, num_results=5, time_range="y")
                results.append(result)
            except Exception as e:
                print(f"搜索失败: {query}, 错误: {e}")
        
        return {"type": "risk_factors", "results": results}


# Agno Tool 包装器
def create_serper_tool():
    """创建 Agno 兼容的搜索工具"""
    from agno.tools import tool
    
    searcher = SerperSearchTool()
    
    @tool(name="web_search", description="使用 Google 搜索网络信息")
    async def web_search(query: str, num_results: int = 10) -> str:
        """
        搜索网络信息
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
        
        Returns:
            搜索结果的文本摘要
        """
        result = await searcher.search(query, num_results)
        
        # 格式化结果
        output = []
        if "organic" in result:
            for item in result["organic"][:num_results]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                output.append(f"标题: {title}\n摘要: {snippet}\n链接: {link}\n")
        
        return "\n---\n".join(output) if output else "未找到相关结果"
    
    return web_search






