"""市场分析 Agent - 使用 Agno 最新 API"""
import json
import re
from typing import Dict, Any

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class MarketAnalyzerAgent:
    """
    市场分析 Agent
    
    负责:
    1. 行业地位分析
    2. 竞争格局分析
    3. 市场趋势分析
    4. SWOT 分析
    """
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="MarketAnalyzer",
            model=self.model,
            description="专业的市场分析师，擅长行业研究和竞争分析",
            instructions="""你是一个专业的市场分析师，擅长分析行业格局和企业竞争地位。
分析时要考虑行业发展趋势、竞争态势、政策环境等因素。
SWOT 分析要客观全面，既看到机会也看到威胁。
请用中文回复。""",
            markdown=True,
        )
    
    async def analyze_market_position(self, collected_data: Dict[str, Any], company: str, depth: str = "deep") -> Dict[str, Any]:
        """
        市场地位分析
        
        Args:
            collected_data: 收集的公司数据
            company: 公司名称
            depth: 研究深度 (basic, standard, deep)
        """
        print(f"[MarketAnalyzer] 分析深度: {depth}")
        
        structured_info = collected_data.get("structured_info", {})
        
        # 根据深度调整分析要求
        depth_config = {
            "basic": {
                "sections": "行业分析和竞争格局",
                "detail_level": "简要",
                "swot_items": 2
            },
            "standard": {
                "sections": "行业分析、竞争格局、市场地位、SWOT和前景展望",
                "detail_level": "标准",
                "swot_items": 3
            },
            "deep": {
                "sections": "行业分析、竞争格局、市场地位、SWOT、前景展望、波特五力分析",
                "detail_level": "深入，包含市场数据和趋势预测",
                "swot_items": 5
            }
        }
        config = depth_config.get(depth, depth_config["standard"])
        
        # 深度模式下包含管理层信息
        extra_data = ""
        if depth == "deep":
            raw_data = collected_data.get("raw_data", {})
            management = raw_data.get("management", {})
            risk_factors = raw_data.get("risk_factors", {})
            if management or risk_factors:
                extra_data = f"\n管理团队信息: {json.dumps(management, ensure_ascii=False)}\n风险因素: {json.dumps(risk_factors, ensure_ascii=False)}"
        
        # 根据深度构建不同的 prompt
        prompt = self._build_market_prompt(company, structured_info, extra_data, depth, config)

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\{[\s\S]*\}', content)
            
            if json_match:
                result = json.loads(json_match.group())
                print(f"[MarketAnalyzer] 分析完成, depth={depth}")
                print(f"[MarketAnalyzer] 返回字段: {result.keys()}")
                if depth == "deep":
                    print(f"[MarketAnalyzer] porter_five_forces: {'有' if result.get('porter_five_forces') else '无'}")
                    print(f"[MarketAnalyzer] moat_analysis: {'有' if result.get('market_position', {}).get('moat_analysis') else '无'}")
                return result
        except Exception as e:
            print(f"[MarketAnalyzer] 分析失败: {e}")
            import traceback
            traceback.print_exc()
        
        return self._default_analysis()
    
    def _build_market_prompt(self, company: str, structured_info: Dict, extra_data: str, depth: str, config: Dict) -> str:
        """根据深度构建不同的市场分析 prompt"""
        
        base_info = f"""公司信息:
- 所属行业: {structured_info.get('industry', '未知')}
- 主营业务: {structured_info.get('main_business', '未知')}
- 主要产品: {json.dumps(structured_info.get('key_products', []), ensure_ascii=False)}
- 市场地位: {structured_info.get('market_position', '未知')}
- 主要竞争对手: {json.dumps(structured_info.get('competitors', []), ensure_ascii=False)}{extra_data}"""

        if depth == "basic":
            return f"""请对 {company} 公司进行简要的市场分析。

{base_info}

请以 JSON 格式返回简要分析:
{{
    "industry_analysis": {{
        "industry_size": "行业规模",
        "growth_stage": "发展阶段",
        "growth_trend": "增长趋势",
        "policy_impact": "政策影响"
    }},
    "competitive_landscape": {{
        "market_share": "市场份额",
        "main_competitors": ["竞争对手1", "竞争对手2"],
        "competitive_advantages": ["核心优势"],
        "competitive_disadvantages": ["主要劣势"]
    }},
    "market_position": {{
        "brand_influence": "品牌影响力",
        "tech_barriers": "技术壁垒",
        "customer_loyalty": "客户粘性",
        "position_score": 7
    }},
    "swot": {{
        "strengths": ["优势1", "优势2"],
        "weaknesses": ["劣势1", "劣势2"],
        "opportunities": ["机会1", "机会2"],
        "threats": ["威胁1", "威胁2"]
    }},
    "outlook": {{
        "short_term": "短期展望",
        "medium_term": "中期展望",
        "long_term": "长期展望",
        "overall_rating": "看好/中性/谨慎"
    }}
}}

评分1-10分。只返回 JSON。"""

        elif depth == "deep":
            return f"""请对 {company} 公司进行深入全面的市场分析。

{base_info}

请进行深度分析，包括波特五力模型，以 JSON 格式返回:
{{
    "industry_analysis": {{
        "industry_size": "行业规模(包含具体市场规模数据或估算)",
        "growth_stage": "发展阶段及判断依据",
        "growth_trend": "未来3-5年增长趋势预测及驱动因素",
        "policy_impact": "政策环境详细分析(包括利好和利空政策)",
        "key_drivers": ["行业增长核心驱动力1", "驱动力2", "驱动力3"]
    }},
    "competitive_landscape": {{
        "market_share": "市场份额详细描述(包括排名和份额估算)",
        "main_competitors": ["竞争对手1", "竞争对手2", "竞争对手3", "竞争对手4"],
        "competitive_advantages": ["差异化优势1", "优势2", "优势3"],
        "competitive_disadvantages": ["竞争劣势1", "劣势2"],
        "entry_barriers": "进入壁垒分析"
    }},
    "porter_five_forces": {{
        "supplier_power": "供应商议价能力分析(1-10分及说明)",
        "buyer_power": "买方议价能力分析(1-10分及说明)",
        "competitive_rivalry": "现有竞争者威胁(1-10分及说明)",
        "threat_of_substitutes": "替代品威胁(1-10分及说明)",
        "threat_of_new_entrants": "新进入者威胁(1-10分及说明)"
    }},
    "market_position": {{
        "brand_influence": "品牌影响力深度分析(包括品牌价值、知名度)",
        "tech_barriers": "技术壁垒详细分析(专利、研发投入等)",
        "customer_loyalty": "客户粘性分析(复购率、转换成本等)",
        "position_score": 7,
        "moat_analysis": "护城河分析(公司的核心竞争壁垒)"
    }},
    "swot": {{
        "strengths": [
            {{"item": "优势1", "detail": "详细说明"}},
            {{"item": "优势2", "detail": "详细说明"}},
            {{"item": "优势3", "detail": "详细说明"}},
            {{"item": "优势4", "detail": "详细说明"}},
            {{"item": "优势5", "detail": "详细说明"}}
        ],
        "weaknesses": [
            {{"item": "劣势1", "detail": "详细说明"}},
            {{"item": "劣势2", "detail": "详细说明"}},
            {{"item": "劣势3", "detail": "详细说明"}}
        ],
        "opportunities": [
            {{"item": "机会1", "detail": "详细说明"}},
            {{"item": "机会2", "detail": "详细说明"}},
            {{"item": "机会3", "detail": "详细说明"}},
            {{"item": "机会4", "detail": "详细说明"}}
        ],
        "threats": [
            {{"item": "威胁1", "detail": "详细说明"}},
            {{"item": "威胁2", "detail": "详细说明"}},
            {{"item": "威胁3", "detail": "详细说明"}}
        ]
    }},
    "outlook": {{
        "short_term": "未来1年详细展望(包括关键事件和催化剂)",
        "medium_term": "1-3年战略展望",
        "long_term": "3年以上长期愿景",
        "overall_rating": "看好/中性/谨慎",
        "key_catalysts": ["上涨催化剂1", "催化剂2"],
        "key_risks": ["核心风险1", "风险2"]
    }}
}}

请提供深入、专业的分析。评分1-10分。只返回 JSON。"""

        else:  # standard
            return f"""请对 {company} 公司进行标准市场分析。

{base_info}

请以 JSON 格式返回分析结果:
{{
    "industry_analysis": {{
        "industry_size": "行业规模描述",
        "growth_stage": "发展阶段(导入期/成长期/成熟期/衰退期)",
        "growth_trend": "增长趋势描述",
        "policy_impact": "政策环境影响"
    }},
    "competitive_landscape": {{
        "market_share": "市场份额描述",
        "main_competitors": ["竞争对手1", "竞争对手2", "竞争对手3"],
        "competitive_advantages": ["优势1", "优势2"],
        "competitive_disadvantages": ["劣势1"]
    }},
    "market_position": {{
        "brand_influence": "品牌影响力描述",
        "tech_barriers": "技术壁垒描述",
        "customer_loyalty": "客户粘性描述",
        "position_score": 7
    }},
    "swot": {{
        "strengths": ["优势1", "优势2", "优势3"],
        "weaknesses": ["劣势1", "劣势2", "劣势3"],
        "opportunities": ["机会1", "机会2", "机会3"],
        "threats": ["威胁1", "威胁2", "威胁3"]
    }},
    "outlook": {{
        "short_term": "短期展望(1年内)",
        "medium_term": "中期展望(1-3年)",
        "long_term": "长期展望(3年以上)",
        "overall_rating": "看好/中性/谨慎"
    }}
}}

评分范围1-10分。只返回 JSON，不要其他内容。"""

    def _default_analysis(self) -> Dict[str, Any]:
        """返回默认分析结构"""
        return {
            "industry_analysis": {
                "industry_size": "待分析",
                "growth_stage": "待分析",
                "growth_trend": "待分析",
                "policy_impact": "待分析"
            },
            "competitive_landscape": {
                "market_share": "待分析",
                "main_competitors": [],
                "competitive_advantages": [],
                "competitive_disadvantages": []
            },
            "market_position": {
                "brand_influence": "待分析",
                "tech_barriers": "待分析",
                "customer_loyalty": "待分析",
                "position_score": 5
            },
            "swot": {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": []
            },
            "outlook": {
                "short_term": "待分析",
                "medium_term": "待分析",
                "long_term": "待分析",
                "overall_rating": "中性"
            }
        }
