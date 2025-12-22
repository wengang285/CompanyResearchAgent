"""意图理解 Agent - 解析用户自然语言输入"""
import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class IntentType(Enum):
    """意图类型"""
    RESEARCH_REPORT = "research_report"  # 生成研究报告
    INVALID = "invalid"  # 无效意图
    UNCLEAR = "unclear"  # 意图不明确


@dataclass
class ParsedIntent:
    """解析后的意图"""
    intent_type: IntentType
    company: Optional[str] = None
    confidence: float = 0.0
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type.value,
            "company": self.company,
            "confidence": self.confidence,
            "message": self.message
        }


class IntentAgent:
    """
    意图理解 Agent
    
    职责:
    - 解析用户自然语言输入
    - 提取公司名称
    - 判断意图是否有效
    """
    
    name = "IntentAgent"
    description = "理解用户意图，提取关键信息"
    
    # 提示格式
    FORMAT_HINT = """请输入您想研究的公司，例如：
• "帮我分析一下贵州茅台"
• "生成腾讯的研究报告"
• "我想了解比亚迪这家公司"

每次只能分析一家公司哦~"""
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="IntentParser",
            model=self.model,
            description="用户意图解析专家",
            instructions="""你是一个意图解析专家，负责理解用户的自然语言输入。
你需要判断用户是否想生成上市公司研究报告，并提取公司名称。
请用中文回复。""",
            markdown=True,
        )
    
    async def parse(self, user_input: str) -> ParsedIntent:
        """
        解析用户输入
        
        Args:
            user_input: 用户输入的自然语言
        
        Returns:
            解析后的意图
        """
        if not user_input or not user_input.strip():
            return ParsedIntent(
                intent_type=IntentType.UNCLEAR,
                message=self.FORMAT_HINT
            )
        
        prompt = f"""请分析以下用户输入，判断用户意图并提取公司名称。

用户输入: "{user_input}"

请以 JSON 格式返回分析结果:
{{
    "intent": "research_report 或 unclear 或 invalid",
    "company": "提取到的公司名称，如果没有则为 null",
    "company_count": 提取到的公司数量,
    "confidence": 0.0-1.0 的置信度,
    "reason": "判断理由"
}}

判断规则:
1. 如果用户明确想分析某家公司/生成研究报告，intent 为 "research_report"
2. 如果用户输入不明确（如"帮我分析"没有公司名），intent 为 "unclear"
3. 如果用户意图与研究报告无关（如"今天天气怎么样"），intent 为 "invalid"
4. 如果提到多家公司，仍标记为 "unclear"，并在 reason 中说明

只返回 JSON，不要其他内容。"""

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return self._process_result(result)
        except Exception as e:
            print(f"[IntentAgent] 解析失败: {e}")
        
        # 默认返回不明确
        return ParsedIntent(
            intent_type=IntentType.UNCLEAR,
            message=self.FORMAT_HINT
        )
    
    def _process_result(self, result: Dict[str, Any]) -> ParsedIntent:
        """处理 LLM 返回的结果"""
        intent = result.get("intent", "unclear")
        company = result.get("company")
        company_count = result.get("company_count", 0)
        confidence = result.get("confidence", 0.0)
        reason = result.get("reason", "")
        
        # 多公司情况
        if company_count > 1:
            return ParsedIntent(
                intent_type=IntentType.UNCLEAR,
                message=f"检测到多家公司，目前每次只能分析一家公司。\n\n{self.FORMAT_HINT}"
            )
        
        # 研究报告意图
        if intent == "research_report" and company:
            return ParsedIntent(
                intent_type=IntentType.RESEARCH_REPORT,
                company=company,
                confidence=confidence,
                message=f"好的，我将为您生成「{company}」的深度研究报告。"
            )
        
        # 无效意图
        if intent == "invalid":
            return ParsedIntent(
                intent_type=IntentType.INVALID,
                message=f"抱歉，我目前只能帮您生成上市公司研究报告。\n\n{self.FORMAT_HINT}"
            )
        
        # 不明确
        return ParsedIntent(
            intent_type=IntentType.UNCLEAR,
            message=self.FORMAT_HINT
        )




