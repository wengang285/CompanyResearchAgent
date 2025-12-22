"""财务分析 Agent - 使用 Agno 最新 API"""
import json
import re
from typing import Dict, Any

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class FinancialAnalyzerAgent:
    """
    财务分析 Agent
    
    负责:
    1. 分析财务报表
    2. 计算财务指标
    3. 评估财务健康度
    4. 同行业对比
    """
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="FinancialAnalyzer",
            model=self.model,
            description="专业的财务分析师，擅长分析上市公司财务状况",
            instructions="""你是一个专业的财务分析师，擅长分析上市公司的财务报表和财务指标。
分析时要全面考虑盈利能力、偿债能力、运营效率和成长性。
给出的分析要有理有据，数据支撑。
如果数据不足，要明确指出并给出合理的假设。
请用中文回复。""",
            markdown=True,
        )
    
    async def analyze_financials(self, collected_data: Dict[str, Any], company: str, depth: str = "deep") -> Dict[str, Any]:
        """
        深度财务分析
        
        Args:
            collected_data: 收集的公司数据
            company: 公司名称
            depth: 研究深度 (basic, standard, deep)
        """
        print(f"[FinancialAnalyzer] 分析深度: {depth}")
        
        structured_info = collected_data.get("structured_info", {})
        financial_highlights = structured_info.get("financial_highlights", {})
        
        # 根据深度调整分析要求
        depth_config = {
            "basic": {
                "analysis_length": "50-100字",
                "dimensions": "盈利能力和成长性",
                "detail_level": "简要"
            },
            "standard": {
                "analysis_length": "100-200字",
                "dimensions": "盈利能力、偿债能力、运营效率和成长性",
                "detail_level": "标准"
            },
            "deep": {
                "analysis_length": "200-400字",
                "dimensions": "盈利能力、偿债能力、运营效率、成长性、现金流质量、杜邦分析",
                "detail_level": "深入，包含具体指标数据和同行业对比"
            }
        }
        config = depth_config.get(depth, depth_config["standard"])
        
        # 深度模式下包含更多数据
        extra_data = ""
        if depth == "deep":
            raw_data = collected_data.get("raw_data", {})
            deep_financials = raw_data.get("deep_financials", {})
            if deep_financials:
                extra_data = f"\n深度财务数据:\n{json.dumps(deep_financials, ensure_ascii=False, indent=2)}"
        
        prompt = f"""请对 {company} 公司进行{config['detail_level']}的财务分析。

已收集的财务信息:
{json.dumps(financial_highlights, ensure_ascii=False, indent=2)}{extra_data}

公司基本信息:
- 主营业务: {structured_info.get('main_business', '未知')}
- 所属行业: {structured_info.get('industry', '未知')}

请从 {config['dimensions']} 维度进行分析，并以 JSON 格式返回:
{{
    "profitability": {{
        "analysis": "盈利能力分析文本({config['analysis_length']})",
        "score": 7,
        "highlights": ["亮点1", "亮点2"]
    }},
    "solvency": {{
        "analysis": "偿债能力分析文本({config['analysis_length']})",
        "score": 7,
        "highlights": ["亮点1"]
    }},
    "efficiency": {{
        "analysis": "运营效率分析文本({config['analysis_length']})",
        "score": 7,
        "highlights": ["亮点1"]
    }},
    "growth": {{
        "analysis": "成长性分析文本({config['analysis_length']})",
        "score": 7,
        "highlights": ["亮点1"]
    }},
    "overall": {{
        "score": 7,
        "summary": "财务健康度综合评价({config['analysis_length']})",
        "strengths": ["优势1", "优势2"],
        "risks": ["风险1", "风险2"]
    }}
}}

评分范围1-10分。只返回 JSON，不要其他内容。"""

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\{[\s\S]*\}', content)
            
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"[FinancialAnalyzer] 分析失败: {e}")
        
        return self._default_analysis()
    
    def _default_analysis(self) -> Dict[str, Any]:
        """返回默认分析结构"""
        return {
            "profitability": {
                "analysis": "由于数据有限，无法进行详细的盈利能力分析。建议查阅公司年报获取完整财务数据。",
                "score": 5,
                "highlights": []
            },
            "solvency": {
                "analysis": "由于数据有限，无法进行详细的偿债能力分析。",
                "score": 5,
                "highlights": []
            },
            "efficiency": {
                "analysis": "由于数据有限，无法进行详细的运营效率分析。",
                "score": 5,
                "highlights": []
            },
            "growth": {
                "analysis": "由于数据有限，无法进行详细的成长性分析。",
                "score": 5,
                "highlights": []
            },
            "overall": {
                "score": 5,
                "summary": "由于公开数据有限，建议参考公司正式财报进行深入分析。",
                "strengths": [],
                "risks": ["信息披露有限"]
            }
        }
