"""财务分析 Agent - 专注财务数据分析"""
import json
import re
import uuid
from typing import Dict, Any, Optional, Callable

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings
from ..utils.streaming_llm import streaming_llm

settings = get_settings()


class FinanceAgent:
    """
    财务分析 Agent
    
    职责:
    - 分析公司财务状况
    - 评估盈利能力、偿债能力、运营效率、成长性
    - 给出财务健康度评分
    """
    
    name = "FinanceAgent"
    description = "专业财务分析师，负责分析公司财务状况"
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="FinancialAnalyst",
            model=self.model,
            description="资深财务分析师",
            instructions="""你是一位资深财务分析师，拥有丰富的上市公司财务分析经验。
分析时要全面、专业，从多个维度评估公司财务健康状况。
评分要客观，有理有据。
如果信息不足，要明确指出并给出合理的判断依据。
请用中文回复。""",
            markdown=True,
        )
    
    async def run(
        self,
        data: Dict[str, Any],
        depth: str = "deep",
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        执行财务分析
        
        Args:
            data: DataAgent 整理后的结构化数据
            depth: 研究深度 (basic, standard, deep)
            stream_callback: 流式回调函数 (message_id, agent_name, chunk, finished)
        
        Returns:
            财务分析结果
        """
        company = data.get("company", "")
        structured_data = data.get("structured_data", {})
        data_depth = data.get("depth", depth)
        
        print(f"[FinanceAgent] 开始财务分析: {company}, 深度: {data_depth}")
        
        prompt = f"""请对 {company} 公司进行专业的财务分析。

## 已知信息
- 公司名称: {structured_data.get('company_name', company)}
- 所属行业: {structured_data.get('industry', '未知')}
- 主营业务: {structured_data.get('main_business', '未知')}
- 财务概况: {json.dumps(structured_data.get('financial_summary', {}), ensure_ascii=False)}

请从以下四个维度进行分析，以 JSON 格式返回:
{{
    "profitability": {{
        "score": 7,
        "analysis": "盈利能力分析(100-150字)",
        "key_metrics": ["关键指标1", "关键指标2"]
    }},
    "solvency": {{
        "score": 7,
        "analysis": "偿债能力分析(100-150字)",
        "key_metrics": ["关键指标1"]
    }},
    "efficiency": {{
        "score": 7,
        "analysis": "运营效率分析(100-150字)",
        "key_metrics": ["关键指标1"]
    }},
    "growth": {{
        "score": <根据成长性分析给出1-10分>,
        "analysis": "成长性分析(100-150字)",
        "key_metrics": ["关键指标1"]
    }},
    "overall_score": <根据以下规则计算>,
    "summary": "财务健康度综合评价(100-150字)",
    "strengths": ["财务优势1", "财务优势2"],
    "weaknesses": ["财务风险1", "财务风险2"]
}}

## 财务综合评分计算规则（重要）：
overall_score = (盈利能力评分 × 0.3 + 偿债能力评分 × 0.25 + 运营效率评分 × 0.25 + 成长性评分 × 0.2)

评分标准（1-10分）：
- 盈利能力：根据营收、利润、毛利率等指标评估
- 偿债能力：根据负债率、流动比率、偿债能力评估
- 运营效率：根据资产周转率、存货周转等评估
- 成长性：根据营收增长率、利润增长率等评估

最终评分需要四舍五入到整数，范围严格控制在 1-10 分。

请根据实际财务数据和分析结果，严格按照上述规则计算各维度评分和综合评分，不要默认给7分。只返回 JSON。"""

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
                        agent_name="FinanceAgent",
                        chunk=chunk,
                        finished=metadata.get("finished", False) if metadata else False
                    )
            
            # 使用流式LLM调用
            content = await streaming_llm.stream_completion_with_metadata(
                prompt=prompt,
                system_prompt="你是一位资深财务分析师，拥有丰富的上市公司财务分析经验。分析时要全面、专业，从多个维度评估公司财务健康状况。评分要客观，有理有据。如果信息不足，要明确指出并给出合理的判断依据。请用中文回复。",
                stream_callback=stream_handler,
                temperature=0.7
            )
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis = json.loads(json_match.group())
                print(f"[FinanceAgent] 分析完成，综合评分: {analysis.get('overall_score', 'N/A')}")
                
                return {
                    "company": company,
                    "financial_analysis": analysis,
                    "status": "success"
                }
        except Exception as e:
            print(f"[FinanceAgent] 分析失败: {e}")
        
        return {
            "company": company,
            "financial_analysis": self._default_analysis(),
            "status": "partial"
        }
    
    def _default_analysis(self) -> Dict[str, Any]:
        """返回默认分析结构"""
        return {
            "profitability": {
                "score": 5,
                "analysis": "由于公开信息有限，无法进行详细的盈利能力分析。",
                "key_metrics": []
            },
            "solvency": {
                "score": 5,
                "analysis": "由于公开信息有限，无法进行详细的偿债能力分析。",
                "key_metrics": []
            },
            "efficiency": {
                "score": 5,
                "analysis": "由于公开信息有限，无法进行详细的运营效率分析。",
                "key_metrics": []
            },
            "growth": {
                "score": 5,
                "analysis": "由于公开信息有限，无法进行详细的成长性分析。",
                "key_metrics": []
            },
            "overall_score": 5,
            "summary": "建议参考公司正式财报进行深入分析。",
            "strengths": [],
            "weaknesses": ["公开信息有限"]
        }




