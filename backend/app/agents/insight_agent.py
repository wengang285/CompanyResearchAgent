"""洞察提炼 Agent - 综合分析结果，提炼核心洞察"""
import json
import re
from typing import Dict, Any

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class InsightAgent:
    """
    洞察提炼 Agent
    
    职责:
    - 综合财务分析和市场分析结果
    - 提炼核心投资洞察
    - 识别关键风险因素
    - 给出投资建议
    """
    
    name = "InsightAgent"
    description = "投资研究专家，负责提炼核心洞察和投资建议"
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="InvestmentInsight",
            model=self.model,
            description="资深投资研究专家",
            instructions="""你是一位资深投资研究专家，擅长从多维度分析中提炼核心洞察。
你的任务是综合财务和市场分析，给出专业的投资建议。
投资建议要谨慎客观，风险提示要充分。
请用中文回复。""",
            markdown=True,
        )
    
    async def run(
        self,
        company: str,
        data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        market_analysis: Dict[str, Any],
        depth: str = "deep"
    ) -> Dict[str, Any]:
        """
        提炼投资洞察
        
        Args:
            company: 公司名称
            data: 结构化数据
            financial_analysis: 财务分析结果
            market_analysis: 市场分析结果
            depth: 研究深度 (basic, standard, deep)
        
        Returns:
            核心洞察和投资建议
        """
        print(f"[InsightAgent] 开始提炼洞察: {company}")
        
        structured_data = data.get("structured_data", {})
        fin_analysis = financial_analysis.get("financial_analysis", {})
        mkt_analysis = market_analysis.get("market_analysis", {})
        
        prompt = f"""请综合以下分析结果，为 {company} 提炼核心投资洞察。

## 公司概况
- 行业: {structured_data.get('industry', '未知')}
- 主营业务: {structured_data.get('main_business', '未知')}

## 财务分析摘要
- 综合评分: {fin_analysis.get('overall_score', 5)}/10
- 财务优势: {json.dumps(fin_analysis.get('strengths', []), ensure_ascii=False)}
- 财务风险: {json.dumps(fin_analysis.get('weaknesses', []), ensure_ascii=False)}

## 市场分析摘要
- 市场地位评分: {mkt_analysis.get('market_position', {}).get('score', 5)}/10
- 发展前景: {mkt_analysis.get('outlook', {}).get('rating', '中性')}
- SWOT 优势: {json.dumps(mkt_analysis.get('swot', {}).get('strengths', []), ensure_ascii=False)}
- SWOT 威胁: {json.dumps(mkt_analysis.get('swot', {}).get('threats', []), ensure_ascii=False)}

请以 JSON 格式返回:
{{
    "core_insights": [
        {{
            "title": "洞察标题",
            "content": "洞察内容(50-80字)",
            "impact": "正面/负面/中性"
        }}
    ],
    "investment_thesis": {{
        "bull_case": "看多逻辑(80-100字)",
        "bear_case": "看空逻辑(80-100字)"
    }},
    "key_risks": [
        {{
            "type": "风险类型(财务/市场/运营/政策)",
            "description": "风险描述",
            "severity": "高/中/低"
        }}
    ],
    "catalysts": [
        {{
            "event": "潜在催化剂",
            "timeline": "时间预期",
            "impact": "正面/负面"
        }}
    ],
    "recommendation": {{
        "rating": "买入/持有/卖出/观望",
        "confidence": "高/中/低",
        "reasoning": "投资建议理由(100-150字)",
        "target_audience": "适合的投资者类型"
    }},
    "overall_score": 7
}}

评分范围 1-10 分。只返回 JSON。"""

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                insights = json.loads(json_match.group())
                print(f"[InsightAgent] 洞察提炼完成，投资评级: {insights.get('recommendation', {}).get('rating', 'N/A')}")
                
                return {
                    "company": company,
                    "insights": insights,
                    "status": "success"
                }
        except Exception as e:
            print(f"[InsightAgent] 洞察提炼失败: {e}")
        
        return {
            "company": company,
            "insights": self._default_insights(),
            "status": "partial"
        }
    
    def _default_insights(self) -> Dict[str, Any]:
        """返回默认洞察结构"""
        return {
            "core_insights": [],
            "investment_thesis": {
                "bull_case": "需要更多信息进行分析",
                "bear_case": "需要更多信息进行分析"
            },
            "key_risks": [
                {
                    "type": "信息",
                    "description": "公开信息有限，分析可能不完整",
                    "severity": "中"
                }
            ],
            "catalysts": [],
            "recommendation": {
                "rating": "观望",
                "confidence": "低",
                "reasoning": "由于信息有限，建议投资者进一步研究后做出投资决策。",
                "target_audience": "风险承受能力较高的投资者"
            },
            "overall_score": 5
        }




