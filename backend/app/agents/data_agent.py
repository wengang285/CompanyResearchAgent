"""数据整理 Agent - 负责将原始搜索结果结构化"""
import json
import re
import uuid
from typing import Dict, Any, Optional, Callable

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings
from ..utils.streaming_llm import streaming_llm

settings = get_settings()


class DataAgent:
    """
    数据整理 Agent
    
    职责:
    - 接收 SearchAgent 的原始搜索结果
    - 提取关键信息
    - 结构化数据，便于后续分析
    """
    
    name = "DataAgent"
    description = "负责整理和结构化搜索结果"
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="DataStructurer",
            model=self.model,
            description="数据整理专家，擅长从杂乱信息中提取结构化数据",
            instructions="""你是一个数据整理专家，负责将搜索结果整理成结构化数据。
提取信息时要准确、客观，不要添加没有依据的信息。
如果某项信息未找到，标注为"未找到"或留空。
请用中文回复。""",
            markdown=True,
        )
    
    async def run(
        self,
        search_data: Dict[str, Any],
        depth: str = "deep",
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        整理搜索结果
        
        Args:
            search_data: SearchAgent 返回的搜索结果
            depth: 研究深度 (basic, standard, deep)
            stream_callback: 流式回调函数 (message_id, agent_name, chunk, finished)
        
        Returns:
            结构化的公司数据
        """
        company = search_data.get("company", "")
        search_results = search_data.get("search_results", {})
        # 保留 depth 信息
        data_depth = search_data.get("depth", depth)
        
        print(f"[DataAgent] 开始整理数据: {company}")
        
        # 提取各类搜索结果的文本
        company_info = self._extract_text(search_results.get("company_info", {}))
        financial_data = self._extract_text(search_results.get("financial_data", {}))
        news = self._extract_news(search_results.get("news", {}))
        industry = self._extract_text(search_results.get("industry_analysis", {}))
        
        # 使用 LLM 整理数据
        prompt = f"""请根据以下搜索结果，整理 {company} 公司的关键信息。

## 公司信息
{company_info}

## 财务数据
{financial_data}

## 最新新闻
{news}

## 行业分析
{industry}

请以 JSON 格式返回以下结构:
{{
    "company_name": "公司全称",
    "stock_code": "股票代码(如有)",
    "industry": "所属行业",
    "main_business": "主营业务描述(50-100字)",
    "key_products": ["主要产品1", "主要产品2"],
    "financial_summary": {{
        "revenue": "最新营收情况",
        "profit": "最新利润情况",
        "growth_rate": "增长率情况"
    }},
    "recent_events": ["近期重要事件1", "近期重要事件2"],
    "market_position": "市场地位描述",
    "main_competitors": ["主要竞争对手1", "主要竞争对手2"]
}}

只返回 JSON，不要其他内容。"""

        try:
            # 创建流式消息ID
            message_id = str(uuid.uuid4())
            full_content = ""
            
            # 流式回调包装
            async def stream_handler(chunk: str, metadata: dict = None):
                nonlocal full_content
                full_content += chunk
                
                if stream_callback:
                    await stream_callback(
                        message_id=message_id,
                        agent_name="DataAgent",
                        chunk=chunk,
                        finished=metadata.get("finished", False) if metadata else False
                    )
            
            # 使用流式LLM调用
            content = await streaming_llm.stream_completion_with_metadata(
                prompt=prompt,
                system_prompt="你是一个数据整理专家，负责将搜索结果整理成结构化数据。提取信息时要准确、客观，不要添加没有依据的信息。如果某项信息未找到，标注为\"未找到\"或留空。请用中文回复。",
                stream_callback=stream_handler,
                temperature=0.3
            )
            
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                structured_data = json.loads(json_match.group())
                print(f"[DataAgent] 数据整理完成: {structured_data.get('company_name', company)}")
                
                return {
                    "company": company,
                    "structured_data": structured_data,
                    "raw_search_results": search_results,
                    "depth": data_depth,
                    "status": "success"
                }
        except Exception as e:
            print(f"[DataAgent] 数据整理失败: {e}")
        
        # 返回默认结构
        return {
            "company": company,
            "structured_data": self._default_structure(company),
            "raw_search_results": search_results,
            "depth": data_depth,
            "status": "partial"
        }
    
    def _extract_text(self, data: Dict[str, Any]) -> str:
        """从搜索结果中提取文本"""
        results = []
        for result_set in data.get("results", []):
            if isinstance(result_set, dict) and "organic" in result_set:
                for item in result_set["organic"][:3]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    results.append(f"- {title}: {snippet}")
        
        return "\n".join(results) if results else "无搜索结果"
    
    def _extract_news(self, data: Dict[str, Any]) -> str:
        """从新闻结果中提取文本"""
        results = []
        news_data = data.get("results", {})
        
        if isinstance(news_data, dict) and "news" in news_data:
            for item in news_data["news"][:5]:
                title = item.get("title", "")
                date = item.get("date", "")
                results.append(f"- [{date}] {title}")
        
        return "\n".join(results) if results else "无最新新闻"
    
    def _default_structure(self, company: str) -> Dict[str, Any]:
        """返回默认数据结构"""
        return {
            "company_name": company,
            "stock_code": "",
            "industry": "",
            "main_business": "",
            "key_products": [],
            "financial_summary": {},
            "recent_events": [],
            "market_position": "",
            "main_competitors": []
        }




