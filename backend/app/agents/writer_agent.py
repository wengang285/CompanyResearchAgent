"""报告撰写 Agent - 生成最终研究报告"""
import json
import re
from typing import Dict, Any, List
from datetime import datetime

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class WriterAgent:
    """
    报告撰写 Agent
    
    职责:
    - 整合所有分析结果
    - 撰写专业的研究报告
    - 生成结构化报告数据
    """
    
    name = "WriterAgent"
    description = "研究报告撰写专家"
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="ReportWriter",
            model=self.model,
            description="资深研究报告撰写专家",
            instructions="""你是一位资深研究报告撰写专家，擅长将分析结果整合成专业的研究报告。
报告要结构清晰、逻辑严谨、表述专业。
语言要简洁有力，重点突出。
请用中文回复。""",
            markdown=True,
        )
    
    async def run(
        self,
        company: str,
        data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        market_analysis: Dict[str, Any],
        insights: Dict[str, Any],
        depth: str = "deep"
    ) -> Dict[str, Any]:
        """
        生成研究报告
        
        Args:
            company: 公司名称
            data: 结构化数据
            financial_analysis: 财务分析结果
            market_analysis: 市场分析结果
            insights: 投资洞察
            depth: 研究深度 (basic, standard, deep)
        
        Returns:
            完整的研究报告
        """
        print(f"[WriterAgent] 开始撰写报告: {company}, 深度: {depth}")
        
        structured_data = data.get("structured_data", {})
        fin_analysis = financial_analysis.get("financial_analysis", {})
        mkt_analysis = market_analysis.get("market_analysis", {})
        insight_data = insights.get("insights", {})
        
        # 生成执行摘要
        executive_summary = await self._generate_executive_summary(
            company, structured_data, fin_analysis, mkt_analysis, insight_data
        )
        
        # 构建完整报告
        report = {
            "metadata": {
                "company": company,
                "company_name": structured_data.get("company_name", company),
                "stock_code": structured_data.get("stock_code", ""),
                "industry": structured_data.get("industry", ""),
                "research_date": datetime.now().isoformat(),
                "overall_score": insight_data.get("overall_score", 5),
                "recommendation": insight_data.get("recommendation", {}).get("rating", "观望")
            },
            "sections": [
                {
                    "id": "executive_summary",
                    "title": "执行摘要",
                    "content": executive_summary,
                    "key_points": self._extract_key_points(insight_data)
                },
                {
                    "id": "company_overview",
                    "title": "公司概况",
                    "subsections": [
                        {
                            "title": "基本信息",
                            "content": self._format_basic_info(structured_data)
                        },
                        {
                            "title": "主营业务",
                            "content": structured_data.get("main_business", "暂无信息")
                        },
                        {
                            "title": "近期动态",
                            "content": self._format_recent_events(structured_data)
                        }
                    ]
                },
                {
                    "id": "financial_analysis",
                    "title": "财务分析",
                    "overall_score": fin_analysis.get("overall_score", 5),
                    "summary": fin_analysis.get("summary", ""),
                    "subsections": [
                        {
                            "title": "盈利能力",
                            "score": fin_analysis.get("profitability", {}).get("score", 5),
                            "content": fin_analysis.get("profitability", {}).get("analysis", "")
                        },
                        {
                            "title": "偿债能力",
                            "score": fin_analysis.get("solvency", {}).get("score", 5),
                            "content": fin_analysis.get("solvency", {}).get("analysis", "")
                        },
                        {
                            "title": "运营效率",
                            "score": fin_analysis.get("efficiency", {}).get("score", 5),
                            "content": fin_analysis.get("efficiency", {}).get("analysis", "")
                        },
                        {
                            "title": "成长性",
                            "score": fin_analysis.get("growth", {}).get("score", 5),
                            "content": fin_analysis.get("growth", {}).get("analysis", "")
                        }
                    ],
                    "strengths": fin_analysis.get("strengths", []),
                    "weaknesses": fin_analysis.get("weaknesses", [])
                },
                {
                    "id": "market_analysis",
                    "title": "市场分析",
                    "overall_score": mkt_analysis.get("market_position", {}).get("score", 5),
                    "subsections": self._build_market_subsections(mkt_analysis, depth),
                    "swot": mkt_analysis.get("swot", {
                        "strengths": [],
                        "weaknesses": [],
                        "opportunities": [],
                        "threats": []
                    }),
                    "porter_five_forces": mkt_analysis.get("porter_five_forces", {}),
                    "summary": f"市场地位评分：{mkt_analysis.get('market_position', {}).get('score', 5)}/10，发展前景：{mkt_analysis.get('outlook', {}).get('rating', '中性')}"
                },
                {
                    "id": "investment_insights",
                    "title": "投资洞察",
                    "content": self._format_insights_content(insight_data),
                    "key_points": [i.get("content", "") for i in insight_data.get("core_insights", [])[:3]],
                    "subsections": [
                        {
                            "title": "看多逻辑",
                            "content": insight_data.get("investment_thesis", {}).get("bull_case", "")
                        },
                        {
                            "title": "看空逻辑",
                            "content": insight_data.get("investment_thesis", {}).get("bear_case", "")
                        }
                    ],
                    "catalysts": [c.get("event", c) if isinstance(c, dict) else c for c in insight_data.get("catalysts", [])]
                },
                {
                    "id": "risk_assessment",
                    "title": "风险评估",
                    "content": "以下是本公司面临的主要风险因素：",
                    "risks": insight_data.get("key_risks", [])
                },
                {
                    "id": "recommendation",
                    "title": "投资建议",
                    "recommendation": insight_data.get("recommendation", {}).get("rating", "观望"),
                    "confidence": insight_data.get("recommendation", {}).get("confidence", "低"),
                    "reasoning": insight_data.get("recommendation", {}).get("reasoning", ""),
                    "content": insight_data.get("recommendation", {}).get("reasoning", ""),
                    "catalysts": [c.get("event", c) if isinstance(c, dict) else c for c in insight_data.get("catalysts", [])],
                    "target_audience": insight_data.get("recommendation", {}).get("target_audience", "")
                }
            ]
        }
        
        print(f"[WriterAgent] 报告撰写完成，共 {len(report['sections'])} 个章节")
        
        return {
            "company": company,
            "report": report,
            "status": "success"
        }
    
    async def _generate_executive_summary(
        self,
        company: str,
        structured_data: Dict,
        fin_analysis: Dict,
        mkt_analysis: Dict,
        insights: Dict
    ) -> str:
        """生成执行摘要"""
        prompt = f"""请为 {company} 撰写一份专业的研究报告执行摘要。

## 公司信息
- 行业: {structured_data.get('industry', '未知')}
- 主营业务: {structured_data.get('main_business', '未知')}

## 核心数据
- 财务健康度: {fin_analysis.get('overall_score', 5)}/10
- 市场地位: {mkt_analysis.get('market_position', {}).get('score', 5)}/10
- 投资评级: {insights.get('recommendation', {}).get('rating', '观望')}
- 发展前景: {mkt_analysis.get('outlook', {}).get('rating', '中性')}

## 核心洞察
{json.dumps(insights.get('core_insights', []), ensure_ascii=False, indent=2)}

请撰写 200-300 字的执行摘要，包含:
1. 公司简介和核心业务
2. 财务状况要点
3. 市场竞争地位
4. 发展前景展望
5. 投资价值判断

直接返回摘要文本，不要标题。"""

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            return content.strip()
        except Exception as e:
            print(f"[WriterAgent] 生成执行摘要失败: {e}")
            return f"{company}是一家值得关注的企业，详细分析请参见报告各章节。"
    
    def _extract_key_points(self, insights: Dict) -> List[str]:
        """提取关键要点"""
        points = []
        for insight in insights.get("core_insights", [])[:3]:
            if isinstance(insight, dict) and insight.get("content"):
                points.append(insight["content"])
        return points
    
    def _format_basic_info(self, data: Dict) -> str:
        """格式化基本信息"""
        parts = []
        if data.get("company_name"):
            parts.append(f"公司名称：{data['company_name']}")
        if data.get("stock_code"):
            parts.append(f"股票代码：{data['stock_code']}")
        if data.get("industry"):
            parts.append(f"所属行业：{data['industry']}")
        if data.get("key_products"):
            products = data['key_products']
            if isinstance(products, list) and products:
                parts.append(f"主要产品：{', '.join(products)}")
        return "\n".join(parts) if parts else "暂无详细信息"
    
    def _format_recent_events(self, data: Dict) -> str:
        """格式化近期动态"""
        events = data.get("recent_events", [])
        if isinstance(events, list) and events:
            return "\n".join([f"• {e}" for e in events])
        return "暂无近期重要动态"
    
    def _format_industry(self, industry: Dict) -> str:
        """格式化行业信息"""
        parts = []
        if industry.get("name"):
            parts.append(f"行业：{industry['name']}")
        if industry.get("size"):
            parts.append(f"规模：{industry['size']}")
        if industry.get("stage"):
            parts.append(f"发展阶段：{industry['stage']}")
        if industry.get("growth_trend"):
            parts.append(f"增长趋势：{industry['growth_trend']}")
        return "\n".join(parts) if parts else "暂无行业分析"
    
    def _format_competition(self, competition: Dict) -> str:
        """格式化竞争格局"""
        parts = []
        if competition.get("intensity"):
            parts.append(f"竞争强度：{competition['intensity']}")
        if competition.get("main_competitors"):
            competitors = competition['main_competitors']
            if isinstance(competitors, list) and competitors:
                parts.append(f"主要竞争对手：{', '.join(competitors)}")
        if competition.get("competitive_advantages"):
            advantages = competition['competitive_advantages']
            if isinstance(advantages, list) and advantages:
                parts.append(f"竞争优势：{', '.join(advantages)}")
        return "\n".join(parts) if parts else "暂无竞争分析"
    
    def _format_market_position(self, position: Dict) -> str:
        """格式化市场地位"""
        parts = []
        if position.get("brand_power"):
            parts.append(f"品牌影响力：{position['brand_power']}")
        if position.get("tech_leadership"):
            parts.append(f"技术领先性：{position['tech_leadership']}")
        if position.get("customer_base"):
            parts.append(f"客户基础：{position['customer_base']}")
        return "\n".join(parts) if parts else "暂无市场地位分析"
    
    def _format_swot(self, swot: Dict) -> str:
        """格式化 SWOT 分析"""
        parts = []
        
        def format_items(items: list, title: str) -> str:
            """格式化 SWOT 项目列表，支持字符串和字典两种格式"""
            if not items:
                return ""
            formatted_items = []
            for item in items:
                if isinstance(item, dict):
                    # deep 模式: {"item": "...", "detail": "..."}
                    name = item.get("item", "")
                    detail = item.get("detail", "")
                    if detail:
                        formatted_items.append(f"• {name}：{detail}")
                    else:
                        formatted_items.append(f"• {name}")
                else:
                    # 简单字符串格式
                    formatted_items.append(f"• {item}")
            return f"【{title}】\n" + "\n".join(formatted_items)
        
        if swot.get("strengths"):
            items = swot['strengths']
            if isinstance(items, list) and items:
                parts.append(format_items(items, "优势 (S)"))
        if swot.get("weaknesses"):
            items = swot['weaknesses']
            if isinstance(items, list) and items:
                parts.append(format_items(items, "劣势 (W)"))
        if swot.get("opportunities"):
            items = swot['opportunities']
            if isinstance(items, list) and items:
                parts.append(format_items(items, "机会 (O)"))
        if swot.get("threats"):
            items = swot['threats']
            if isinstance(items, list) and items:
                parts.append(format_items(items, "威胁 (T)"))
        return "\n\n".join(parts) if parts else "暂无 SWOT 分析"
    
    def _format_outlook(self, outlook: Dict) -> str:
        """格式化发展前景"""
        parts = []
        if outlook.get("short_term"):
            parts.append(f"短期展望（1年）：{outlook['short_term']}")
        if outlook.get("medium_term"):
            parts.append(f"中期展望（1-3年）：{outlook['medium_term']}")
        if outlook.get("long_term"):
            parts.append(f"长期展望（3年以上）：{outlook['long_term']}")
        if outlook.get("rating"):
            parts.append(f"总体评级：{outlook['rating']}")
        # deep 模式的额外字段
        if outlook.get("key_catalysts"):
            catalysts = outlook['key_catalysts']
            if isinstance(catalysts, list):
                parts.append(f"关键催化剂：{', '.join(catalysts)}")
        if outlook.get("key_risks"):
            risks = outlook['key_risks']
            if isinstance(risks, list):
                parts.append(f"核心风险：{', '.join(risks)}")
        return "\n".join(parts) if parts else "暂无发展前景分析"
    
    def _build_market_subsections(self, mkt_analysis: Dict, depth: str) -> List[Dict]:
        """根据深度构建市场分析子章节"""
        subsections = [
            {
                "title": "行业分析",
                "content": self._format_industry(mkt_analysis.get("industry", {}))
            },
            {
                "title": "竞争格局",
                "content": self._format_competition(mkt_analysis.get("competition", {}))
            },
            {
                "title": "市场地位",
                "score": mkt_analysis.get("market_position", {}).get("score", 5),
                "content": self._format_market_position(mkt_analysis.get("market_position", {}))
            },
            {
                "title": "SWOT 分析",
                "content": self._format_swot(mkt_analysis.get("swot", {}))
            },
            {
                "title": "发展前景",
                "content": self._format_outlook(mkt_analysis.get("outlook", {}))
            }
        ]
        
        # deep 模式添加波特五力和护城河分析
        if depth == "deep":
            porter = mkt_analysis.get("porter_five_forces", {})
            if porter:
                subsections.insert(2, {
                    "title": "波特五力分析",
                    "content": self._format_porter_five_forces(porter)
                })
            
            moat = mkt_analysis.get("market_position", {}).get("moat_analysis", "")
            if moat:
                subsections.append({
                    "title": "护城河分析",
                    "content": moat
                })
        
        return subsections
    
    def _format_porter_five_forces(self, porter: Dict) -> str:
        """格式化波特五力分析"""
        parts = []
        
        def format_force(force_data, name: str) -> str:
            if isinstance(force_data, dict):
                score = force_data.get("score", "N/A")
                analysis = force_data.get("analysis", "")
                return f"{name}：{score}/10 - {analysis}"
            else:
                return f"{name}：{force_data}"
        
        if porter.get("supplier_power"):
            parts.append(format_force(porter['supplier_power'], "供应商议价能力"))
        if porter.get("buyer_power"):
            parts.append(format_force(porter['buyer_power'], "买方议价能力"))
        if porter.get("competitive_rivalry"):
            parts.append(format_force(porter['competitive_rivalry'], "现有竞争者威胁"))
        if porter.get("threat_of_substitutes"):
            parts.append(format_force(porter['threat_of_substitutes'], "替代品威胁"))
        if porter.get("threat_of_new_entrants"):
            parts.append(format_force(porter['threat_of_new_entrants'], "新进入者威胁"))
        
        return "\n".join(parts) if parts else "暂无波特五力分析"
    
    def _format_insights_content(self, insights: Dict) -> str:
        """格式化投资洞察内容"""
        parts = []
        
        # 核心洞察
        core_insights = insights.get("core_insights", [])
        if core_insights:
            parts.append("【核心洞察】")
            for i, insight in enumerate(core_insights, 1):
                if isinstance(insight, dict):
                    title = insight.get("title", "")
                    content = insight.get("content", "")
                    impact = insight.get("impact", "")
                    parts.append(f"{i}. {title}：{content}（{impact}）")
                else:
                    parts.append(f"{i}. {insight}")
        
        # 投资论点
        thesis = insights.get("investment_thesis", {})
        if thesis:
            parts.append("\n【投资逻辑】")
            if thesis.get("bull_case"):
                parts.append(f"看多逻辑：{thesis['bull_case']}")
            if thesis.get("bear_case"):
                parts.append(f"看空逻辑：{thesis['bear_case']}")
        
        return "\n".join(parts) if parts else "暂无投资洞察"

