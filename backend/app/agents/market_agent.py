"""市场分析 Agent - 专注行业和竞争分析"""
import json
import re
from typing import Dict, Any

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class MarketAgent:
    """
    市场分析 Agent
    
    职责:
    - 分析行业格局和发展趋势
    - 评估公司市场地位和竞争力
    - 进行 SWOT 分析
    """
    
    name = "MarketAgent"
    description = "市场分析专家，负责行业和竞争分析"
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="MarketAnalyst",
            model=self.model,
            description="资深市场分析师",
            instructions="""你是一位资深市场分析师，擅长行业研究和竞争格局分析。
分析时要考虑行业发展周期、竞争态势、政策环境等因素。
SWOT 分析要全面客观，既看到机会也识别威胁。
请用中文回复。""",
            markdown=True,
        )
    
    async def run(self, data: Dict[str, Any], depth: str = "deep") -> Dict[str, Any]:
        """
        执行市场分析
        
        Args:
            data: DataAgent 整理后的结构化数据
            depth: 研究深度 (basic, standard, deep)
        
        Returns:
            市场分析结果
        """
        company = data.get("company", "")
        structured_data = data.get("structured_data", {})
        data_depth = data.get("depth", depth)
        
        print(f"[MarketAgent] 开始市场分析: {company}, 深度: {data_depth}")
        
        # 根据深度生成不同的 prompt
        prompt = self._build_prompt(company, structured_data, data_depth)

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis = json.loads(json_match.group())
                print(f"[MarketAgent] 分析完成，市场地位评分: {analysis.get('market_position', {}).get('score', 'N/A')}")
                
                return {
                    "company": company,
                    "market_analysis": analysis,
                    "status": "success"
                }
        except Exception as e:
            print(f"[MarketAgent] 分析失败: {e}")
        
        return {
            "company": company,
            "market_analysis": self._default_analysis(),
            "status": "partial"
        }
    
    def _build_prompt(self, company: str, structured_data: Dict, depth: str) -> str:
        """根据深度构建不同的市场分析 prompt"""
        base_info = f"""## 已知信息
- 公司名称: {structured_data.get('company_name', company)}
- 所属行业: {structured_data.get('industry', '未知')}
- 主营业务: {structured_data.get('main_business', '未知')}
- 主要产品: {json.dumps(structured_data.get('key_products', []), ensure_ascii=False)}
- 市场地位: {structured_data.get('market_position', '未知')}
- 主要竞争对手: {json.dumps(structured_data.get('main_competitors', []), ensure_ascii=False)}"""

        if depth == "deep":
            return f"""请对 {company} 公司进行深入全面的市场分析。

{base_info}

请进行深度分析，包括波特五力模型，以 JSON 格式返回:
{{
    "industry": {{
        "name": "行业名称",
        "size": "行业规模(包含具体数据或估算)",
        "stage": "发展阶段及判断依据",
        "growth_trend": "未来3-5年增长趋势预测",
        "key_drivers": ["核心驱动力1", "驱动力2", "驱动力3"],
        "policy_environment": "政策环境详细分析"
    }},
    "competition": {{
        "intensity": "竞争激烈程度(高/中/低)",
        "market_share_rank": "市场份额详细描述(含排名估算)",
        "main_competitors": ["竞争对手1", "竞争对手2", "竞争对手3", "竞争对手4"],
        "competitive_advantages": ["差异化优势1", "优势2", "优势3"],
        "competitive_disadvantages": ["竞争劣势1", "劣势2"],
        "entry_barriers": "进入壁垒分析"
    }},
    "porter_five_forces": {{
        "supplier_power": {{"score": 5, "analysis": "供应商议价能力分析"}},
        "buyer_power": {{"score": 5, "analysis": "买方议价能力分析"}},
        "competitive_rivalry": {{"score": 7, "analysis": "现有竞争者威胁分析"}},
        "threat_of_substitutes": {{"score": 4, "analysis": "替代品威胁分析"}},
        "threat_of_new_entrants": {{"score": 6, "analysis": "新进入者威胁分析"}}
    }},
    "market_position": {{
        "brand_power": "品牌影响力详细分析",
        "tech_leadership": "技术领先性分析",
        "customer_base": "客户基础分析",
        "score": 7,
        "moat_analysis": "护城河分析(公司的核心竞争壁垒)"
    }},
    "swot": {{
        "strengths": [
            {{"item": "优势1", "detail": "详细说明"}},
            {{"item": "优势2", "detail": "详细说明"}},
            {{"item": "优势3", "detail": "详细说明"}}
        ],
        "weaknesses": [
            {{"item": "劣势1", "detail": "详细说明"}},
            {{"item": "劣势2", "detail": "详细说明"}}
        ],
        "opportunities": [
            {{"item": "机会1", "detail": "详细说明"}},
            {{"item": "机会2", "detail": "详细说明"}},
            {{"item": "机会3", "detail": "详细说明"}}
        ],
        "threats": [
            {{"item": "威胁1", "detail": "详细说明"}},
            {{"item": "威胁2", "detail": "详细说明"}}
        ]
    }},
    "outlook": {{
        "short_term": "未来1年详细展望",
        "medium_term": "1-3年战略展望",
        "long_term": "3年以上长期愿景",
        "rating": "看好/中性/谨慎",
        "key_catalysts": ["上涨催化剂1", "催化剂2"],
        "key_risks": ["核心风险1", "风险2"]
    }}
}}

评分范围 1-10 分。只返回 JSON。"""
        else:
            # standard 模式
            return f"""请对 {company} 公司进行专业的市场分析。

{base_info}

请以 JSON 格式返回分析结果:
{{
    "industry": {{
        "name": "行业名称",
        "size": "行业规模描述",
        "stage": "发展阶段(导入期/成长期/成熟期/衰退期)",
        "growth_trend": "增长趋势描述",
        "key_drivers": ["驱动因素1", "驱动因素2"],
        "policy_environment": "政策环境描述"
    }},
    "competition": {{
        "intensity": "竞争激烈程度(高/中/低)",
        "market_share_rank": "市场份额排名描述",
        "main_competitors": ["竞争对手1", "竞争对手2"],
        "competitive_advantages": ["竞争优势1", "竞争优势2"],
        "competitive_disadvantages": ["竞争劣势1"]
    }},
    "market_position": {{
        "brand_power": "品牌影响力(强/中/弱)",
        "tech_leadership": "技术领先性描述",
        "customer_base": "客户基础描述",
        "score": 7
    }},
    "swot": {{
        "strengths": ["优势1", "优势2"],
        "weaknesses": ["劣势1", "劣势2"],
        "opportunities": ["机会1", "机会2"],
        "threats": ["威胁1", "威胁2"]
    }},
    "outlook": {{
        "short_term": "短期展望(1年)",
        "medium_term": "中期展望(1-3年)",
        "long_term": "长期展望(3年以上)",
        "rating": "看好/中性/谨慎"
    }}
}}

评分范围 1-10 分。只返回 JSON。"""

    def _default_analysis(self) -> Dict[str, Any]:
        """返回默认分析结构"""
        return {
            "industry": {
                "name": "",
                "size": "待分析",
                "stage": "待分析",
                "growth_trend": "待分析",
                "key_drivers": [],
                "policy_environment": "待分析"
            },
            "competition": {
                "intensity": "中",
                "market_share_rank": "待分析",
                "main_competitors": [],
                "competitive_advantages": [],
                "competitive_disadvantages": []
            },
            "market_position": {
                "brand_power": "中",
                "tech_leadership": "待分析",
                "customer_base": "待分析",
                "score": 5
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
                "rating": "中性"
            }
        }




