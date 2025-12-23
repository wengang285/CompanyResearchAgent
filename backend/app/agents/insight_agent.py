"""洞察提炼 Agent - 综合分析结果，提炼核心洞察"""
import json
import re
import uuid
from typing import Dict, Any, Optional, Callable

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings
from ..utils.streaming_llm import streaming_llm

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
        depth: str = "deep",
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        提炼投资洞察
        
        Args:
            company: 公司名称
            data: 结构化数据
            financial_analysis: 财务分析结果
            market_analysis: 市场分析结果
            depth: 研究深度 (basic, standard, deep)
            stream_callback: 流式回调函数 (message_id, agent_name, chunk, finished)
        
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
    "overall_score": <根据以下规则计算综合评分>
}}

## 综合评分计算规则（重要）：
综合评分 = (财务评分 × 0.4 + 市场评分 × 0.35 + 成长潜力 × 0.15 + 风险调整 × 0.1)

其中：
- 财务评分：使用财务分析的综合评分
- 市场评分：使用市场地位评分
- 成长潜力：根据发展前景评级计算（看好=8分，中性=6分，谨慎=4分）
- 风险调整：根据关键风险数量调整（无风险=+1，低风险=0，中风险=-1，高风险=-2）

最终评分需要四舍五入到整数，范围严格控制在 1-10 分。

评分标准：
- 9-10分：优秀，财务和市场表现突出，风险可控，强烈推荐
- 7-8分：良好，整体表现不错，有一定投资价值
- 5-6分：一般，表现平平，需要谨慎考虑
- 3-4分：较差，存在明显问题，不推荐
- 1-2分：很差，严重问题，强烈不推荐

请根据实际分析结果，严格按照上述规则计算综合评分，不要默认给7分。只返回 JSON。"""

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
                        agent_name="InsightAgent",
                        chunk=chunk,
                        finished=metadata.get("finished", False) if metadata else False
                    )
            
            # 使用流式LLM调用
            content = await streaming_llm.stream_completion_with_metadata(
                prompt=prompt,
                system_prompt="你是一位资深投资研究专家，擅长从多维度分析中提炼核心洞察。你的任务是综合财务和市场分析，给出专业的投资建议。投资建议要谨慎客观，风险提示要充分。请用中文回复。",
                stream_callback=stream_handler,
                temperature=0.7
            )
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                insights = json.loads(json_match.group())
                
                # 验证并修正综合评分
                calculated_score = self._calculate_overall_score(
                    fin_analysis.get('overall_score', 5),
                    mkt_analysis.get('market_position', {}).get('score', 5),
                    mkt_analysis.get('outlook', {}).get('rating', '中性'),
                    len(insights.get('key_risks', []))
                )
                
                # 如果LLM给出的评分是默认值（7分）或与计算值差异较大，使用计算值
                llm_score = insights.get('overall_score', 7)
                if llm_score == 7 and abs(llm_score - calculated_score) > 1.5:
                    insights['overall_score'] = round(calculated_score)
                    print(f"[InsightAgent] 评分修正: LLM={llm_score} -> 计算值={insights['overall_score']}")
                else:
                    # 使用LLM评分，但确保在合理范围内
                    insights['overall_score'] = max(1, min(10, round(llm_score)))
                
                print(f"[InsightAgent] 洞察提炼完成，投资评级: {insights.get('recommendation', {}).get('rating', 'N/A')}, 综合评分: {insights['overall_score']}")
                
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
    
    def _calculate_overall_score(
        self,
        financial_score: float,
        market_score: float,
        outlook_rating: str,
        risk_count: int
    ) -> float:
        """
        基于公式计算综合评分
        
        Args:
            financial_score: 财务分析评分 (1-10)
            market_score: 市场地位评分 (1-10)
            outlook_rating: 发展前景评级 (看好/中性/谨慎)
            risk_count: 关键风险数量
        
        Returns:
            综合评分 (1-10)
        """
        # 成长潜力评分（根据发展前景）
        growth_scores = {
            "看好": 8.0,
            "中性": 6.0,
            "谨慎": 4.0
        }
        growth_score = growth_scores.get(outlook_rating, 6.0)
        
        # 风险调整（风险越多，扣分越多）
        risk_adjustment = 0.0
        if risk_count == 0:
            risk_adjustment = 1.0  # 无风险加分
        elif risk_count <= 2:
            risk_adjustment = 0.0  # 低风险不调整
        elif risk_count <= 4:
            risk_adjustment = -1.0  # 中风险扣分
        else:
            risk_adjustment = -2.0  # 高风险扣分
        
        # 加权计算
        overall_score = (
            financial_score * 0.4 +      # 财务分析权重 40%
            market_score * 0.35 +         # 市场分析权重 35%
            growth_score * 0.15 +         # 成长潜力权重 15%
            risk_adjustment * 0.1         # 风险调整权重 10%
        )
        
        # 确保在 1-10 范围内
        return max(1.0, min(10.0, overall_score))
    
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




