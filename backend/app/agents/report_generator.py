"""报告生成 Agent - 使用 Agno 最新 API"""
import json
import re
from typing import Dict, Any
from datetime import datetime

from agno.agent import Agent
from agno.models.openai import OpenAILike

from ..config import get_settings

settings = get_settings()


class ReportGeneratorAgent:
    """
    报告生成 Agent
    
    负责:
    1. 整合所有分析结果
    2. 生成结构化报告
    3. 生成投资建议
    """
    
    def __init__(self):
        self.model = OpenAILike(
            id=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        
        self.agent = Agent(
            name="ReportGenerator",
            model=self.model,
            description="专业的研究报告撰写专家",
            instructions="""你是一个专业的研究报告撰写专家，擅长将分析结果整合成专业的研究报告。
报告要结构清晰、逻辑严谨、表述专业。
投资建议要谨慎客观，风险提示要充分。
请用中文回复。""",
            markdown=True,
        )
    
    async def generate_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整研究报告"""
        company = analysis_results.get("company", "")
        collected_data = analysis_results.get("collected_data", {})
        financial_analysis = analysis_results.get("financial_analysis", {})
        market_analysis = analysis_results.get("market_analysis", {})
        depth = analysis_results.get("depth", "deep")
        
        print(f"[ReportGenerator] 报告生成深度: {depth}")
        
        structured_info = collected_data.get("structured_info", {})
        
        # 生成执行摘要
        executive_summary = await self._generate_executive_summary(
            company, structured_info, financial_analysis, market_analysis
        )
        
        # 生成投资建议
        investment_recommendation = await self._generate_investment_recommendation(
            company, financial_analysis, market_analysis
        )
        
        # 构建完整报告
        report = {
            "company": company,
            "stock_code": structured_info.get("stock_code", ""),
            "research_date": datetime.now().isoformat(),
            "sections": [
                {
                    "title": "执行摘要",
                    "content": executive_summary,
                    "key_points": self._extract_key_points(executive_summary)
                },
                {
                    "title": "公司概况",
                    "subsections": [
                        {
                            "title": "基本信息",
                            "content": self._format_company_info(structured_info)
                        },
                        {
                            "title": "主营业务",
                            "content": structured_info.get("main_business", "暂无信息")
                        }
                    ]
                },
                {
                    "title": "财务分析",
                    "subsections": [
                        {
                            "title": "盈利能力分析",
                            "content": financial_analysis.get("profitability", {}).get("analysis", ""),
                            "score": financial_analysis.get("profitability", {}).get("score", 5)
                        },
                        {
                            "title": "偿债能力分析",
                            "content": financial_analysis.get("solvency", {}).get("analysis", ""),
                            "score": financial_analysis.get("solvency", {}).get("score", 5)
                        },
                        {
                            "title": "运营效率分析",
                            "content": financial_analysis.get("efficiency", {}).get("analysis", ""),
                            "score": financial_analysis.get("efficiency", {}).get("score", 5)
                        },
                        {
                            "title": "成长性分析",
                            "content": financial_analysis.get("growth", {}).get("analysis", ""),
                            "score": financial_analysis.get("growth", {}).get("score", 5)
                        }
                    ],
                    "overall_score": financial_analysis.get("overall", {}).get("score", 5),
                    "summary": financial_analysis.get("overall", {}).get("summary", "")
                },
                {
                    "title": "市场分析",
                    "subsections": self._build_market_subsections(market_analysis, depth)
                },
                {
                    "title": "风险评估",
                    "risks": self._compile_risks(financial_analysis, market_analysis)
                },
                {
                    "title": "投资建议",
                    "recommendation": investment_recommendation.get("recommendation", "中性"),
                    "target_price": investment_recommendation.get("target_price"),
                    "reasoning": investment_recommendation.get("reasoning", ""),
                    "catalysts": investment_recommendation.get("catalysts", []),
                    "risks": investment_recommendation.get("risks", [])
                }
            ]
        }
        
        return report
    
    async def _generate_executive_summary(
        self,
        company: str,
        structured_info: Dict,
        financial_analysis: Dict,
        market_analysis: Dict
    ) -> str:
        """生成执行摘要"""
        prompt = f"""请为 {company} 公司撰写一份专业的研究报告执行摘要。

公司信息:
- 行业: {structured_info.get('industry', '未知')}
- 主营业务: {structured_info.get('main_business', '未知')}

财务分析要点:
- 财务健康度评分: {financial_analysis.get('overall', {}).get('score', 5)}/10
- 主要优势: {json.dumps(financial_analysis.get('overall', {}).get('strengths', []), ensure_ascii=False)}
- 主要风险: {json.dumps(financial_analysis.get('overall', {}).get('risks', []), ensure_ascii=False)}

市场分析要点:
- 市场地位评分: {market_analysis.get('market_position', {}).get('position_score', 5)}/10
- 发展前景: {market_analysis.get('outlook', {}).get('overall_rating', '中性')}

请撰写200-300字的执行摘要，包含:
1. 公司简介
2. 核心竞争力
3. 财务状况概述
4. 发展前景展望
5. 投资价值判断

直接返回摘要文本，不要标题和格式标记。"""

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            return content.strip()
        except Exception as e:
            print(f"[ReportGenerator] 生成执行摘要失败: {e}")
            return f"{company}是一家值得关注的企业，具体分析请参见报告各章节。"
    
    async def _generate_investment_recommendation(
        self,
        company: str,
        financial_analysis: Dict,
        market_analysis: Dict
    ) -> Dict:
        """生成投资建议"""
        prompt = f"""请基于以下分析结果，为 {company} 给出专业的投资建议。

财务分析:
- 财务健康度: {financial_analysis.get('overall', {}).get('score', 5)}/10
- 主要优势: {json.dumps(financial_analysis.get('overall', {}).get('strengths', []), ensure_ascii=False)}
- 主要风险: {json.dumps(financial_analysis.get('overall', {}).get('risks', []), ensure_ascii=False)}

市场分析:
- 市场地位: {market_analysis.get('market_position', {}).get('position_score', 5)}/10
- 发展前景: {market_analysis.get('outlook', {}).get('overall_rating', '中性')}
- SWOT: {json.dumps(market_analysis.get('swot', {}), ensure_ascii=False)}

请以 JSON 格式返回投资建议:
{{
    "recommendation": "买入/持有/卖出/观望",
    "target_price": null,
    "reasoning": "投资建议理由(100-150字)",
    "catalysts": ["上涨催化剂1", "上涨催化剂2"],
    "risks": ["主要风险1", "主要风险2"]
}}

只返回 JSON，不要其他内容。"""

        try:
            response = self.agent.run(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\{[\s\S]*\}', content)
            
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"[ReportGenerator] 生成投资建议失败: {e}")
        
        return {
            "recommendation": "观望",
            "target_price": None,
            "reasoning": "由于信息有限，建议投资者进一步研究后做出投资决策。",
            "catalysts": [],
            "risks": ["信息披露有限"]
        }
    
    def _extract_key_points(self, text: str) -> list:
        """提取关键点"""
        sentences = text.replace("。", ".").split(".")
        return [s.strip() for s in sentences[:3] if s.strip() and len(s.strip()) > 10]
    
    def _format_company_info(self, info: Dict) -> str:
        """格式化公司信息"""
        parts = []
        if info.get("company_name"):
            parts.append(f"公司名称：{info['company_name']}")
        if info.get("stock_code"):
            parts.append(f"股票代码：{info['stock_code']}")
        if info.get("industry"):
            parts.append(f"所属行业：{info['industry']}")
        if info.get("key_products"):
            products = info['key_products']
            if isinstance(products, list):
                parts.append(f"主要产品：{', '.join(products)}")
        return "\n".join(parts) if parts else "暂无详细信息"
    
    def _build_market_subsections(self, market_analysis: Dict, depth: str) -> list:
        """根据深度构建市场分析子章节"""
        print(f"[ReportGenerator] 构建市场分析子章节, depth={depth}")
        print(f"[ReportGenerator] market_analysis keys: {market_analysis.keys()}")
        
        subsections = [
            {
                "title": "行业分析",
                "content": self._format_industry_analysis(market_analysis.get("industry_analysis", {}), depth)
            },
            {
                "title": "竞争格局",
                "content": self._format_competitive_landscape(market_analysis.get("competitive_landscape", {}), depth)
            },
            {
                "title": "SWOT分析",
                "content": self._format_swot(market_analysis.get("swot", {}))
            }
        ]
        
        # deep 模式下添加波特五力分析
        if depth == "deep":
            porter = market_analysis.get("porter_five_forces", {})
            print(f"[ReportGenerator] 波特五力数据: {porter}")
            if porter:
                subsections.insert(2, {
                    "title": "波特五力分析",
                    "content": self._format_porter_five_forces(porter)
                })
            else:
                print("[ReportGenerator] 警告: 未找到波特五力数据")
            
            # 添加护城河分析
            moat = market_analysis.get("market_position", {}).get("moat_analysis", "")
            print(f"[ReportGenerator] 护城河分析: {moat}")
            if moat:
                subsections.append({
                    "title": "护城河分析",
                    "content": moat
                })
            
            # 添加市场前景分析
            outlook = market_analysis.get("outlook", {})
            if outlook.get("key_catalysts") or outlook.get("key_risks"):
                outlook_content = self._format_outlook(outlook)
                subsections.append({
                    "title": "市场前景展望",
                    "content": outlook_content
                })
        
        print(f"[ReportGenerator] 生成了 {len(subsections)} 个子章节")
        return subsections
    
    def _format_outlook(self, outlook: Dict) -> str:
        """格式化前景展望"""
        parts = []
        if outlook.get("short_term"):
            parts.append(f"短期展望：{outlook['short_term']}")
        if outlook.get("medium_term"):
            parts.append(f"中期展望：{outlook['medium_term']}")
        if outlook.get("long_term"):
            parts.append(f"长期展望：{outlook['long_term']}")
        if outlook.get("overall_rating"):
            parts.append(f"总体评级：{outlook['overall_rating']}")
        if outlook.get("key_catalysts"):
            catalysts = outlook['key_catalysts']
            if isinstance(catalysts, list):
                parts.append(f"关键催化剂：{', '.join(catalysts)}")
        if outlook.get("key_risks"):
            risks = outlook['key_risks']
            if isinstance(risks, list):
                parts.append(f"核心风险：{', '.join(risks)}")
        return "\n".join(parts) if parts else "暂无前景展望"
    
    def _format_porter_five_forces(self, porter: Dict) -> str:
        """格式化波特五力分析"""
        parts = []
        if porter.get("supplier_power"):
            parts.append(f"供应商议价能力：{porter['supplier_power']}")
        if porter.get("buyer_power"):
            parts.append(f"买方议价能力：{porter['buyer_power']}")
        if porter.get("competitive_rivalry"):
            parts.append(f"现有竞争者威胁：{porter['competitive_rivalry']}")
        if porter.get("threat_of_substitutes"):
            parts.append(f"替代品威胁：{porter['threat_of_substitutes']}")
        if porter.get("threat_of_new_entrants"):
            parts.append(f"新进入者威胁：{porter['threat_of_new_entrants']}")
        return "\n".join(parts) if parts else "暂无波特五力分析"

    def _format_industry_analysis(self, analysis: Dict, depth: str = "deep") -> str:
        """格式化行业分析"""
        parts = []
        if analysis.get("industry_size"):
            parts.append(f"行业规模：{analysis['industry_size']}")
        if analysis.get("growth_stage"):
            parts.append(f"发展阶段：{analysis['growth_stage']}")
        if analysis.get("growth_trend"):
            parts.append(f"增长趋势：{analysis['growth_trend']}")
        if analysis.get("policy_impact"):
            parts.append(f"政策影响：{analysis['policy_impact']}")
        
        # deep 模式额外字段
        if depth == "deep" and analysis.get("key_drivers"):
            drivers = analysis['key_drivers']
            if isinstance(drivers, list):
                parts.append(f"核心驱动力：{', '.join(drivers)}")
        
        return "\n".join(parts) if parts else "暂无详细分析"
    
    def _format_competitive_landscape(self, landscape: Dict, depth: str = "deep") -> str:
        """格式化竞争格局"""
        parts = []
        if landscape.get("market_share"):
            parts.append(f"市场份额：{landscape['market_share']}")
        if landscape.get("main_competitors"):
            competitors = landscape['main_competitors']
            if isinstance(competitors, list):
                parts.append(f"主要竞争对手：{', '.join(competitors)}")
        if landscape.get("competitive_advantages"):
            advantages = landscape['competitive_advantages']
            if isinstance(advantages, list):
                parts.append(f"竞争优势：{', '.join(advantages)}")
        if landscape.get("competitive_disadvantages"):
            disadvantages = landscape['competitive_disadvantages']
            if isinstance(disadvantages, list):
                parts.append(f"竞争劣势：{', '.join(disadvantages)}")
        
        # deep 模式额外字段
        if depth == "deep" and landscape.get("entry_barriers"):
            parts.append(f"进入壁垒：{landscape['entry_barriers']}")
        
        return "\n".join(parts) if parts else "暂无详细分析"
    
    def _format_swot(self, swot: Dict) -> str:
        """格式化 SWOT 分析"""
        parts = []
        
        def format_items(items: list) -> str:
            """格式化 SWOT 项目，支持简单字符串或带详情的字典"""
            formatted = []
            for item in items:
                if isinstance(item, dict):
                    # deep 模式: {"item": "xxx", "detail": "xxx"}
                    name = item.get("item", "")
                    detail = item.get("detail", "")
                    if detail:
                        formatted.append(f"{name}（{detail}）")
                    else:
                        formatted.append(name)
                else:
                    # 简单字符串
                    formatted.append(str(item))
            return ', '.join(formatted)
        
        if swot.get("strengths"):
            items = swot['strengths']
            if isinstance(items, list):
                parts.append(f"优势 (S)：{format_items(items)}")
        if swot.get("weaknesses"):
            items = swot['weaknesses']
            if isinstance(items, list):
                parts.append(f"劣势 (W)：{format_items(items)}")
        if swot.get("opportunities"):
            items = swot['opportunities']
            if isinstance(items, list):
                parts.append(f"机会 (O)：{format_items(items)}")
        if swot.get("threats"):
            items = swot['threats']
            if isinstance(items, list):
                parts.append(f"威胁 (T)：{format_items(items)}")
        return "\n".join(parts) if parts else "暂无 SWOT 分析"
    
    def _compile_risks(self, financial_analysis: Dict, market_analysis: Dict) -> list:
        """汇总风险因素"""
        risks = []
        
        fin_risks = financial_analysis.get("overall", {}).get("risks", [])
        if isinstance(fin_risks, list):
            risks.extend([{"type": "财务风险", "description": r} for r in fin_risks])
        
        threats = market_analysis.get("swot", {}).get("threats", [])
        if isinstance(threats, list):
            for t in threats:
                if isinstance(t, dict):
                    # deep 模式: {"item": "xxx", "detail": "xxx"}
                    desc = t.get("item", "")
                    detail = t.get("detail", "")
                    if detail:
                        desc = f"{desc}: {detail}"
                    risks.append({"type": "市场风险", "description": desc})
                else:
                    risks.append({"type": "市场风险", "description": str(t)})
        
        # 添加 outlook 中的 key_risks (deep 模式)
        key_risks = market_analysis.get("outlook", {}).get("key_risks", [])
        if isinstance(key_risks, list):
            risks.extend([{"type": "核心风险", "description": r} for r in key_risks])
        
        return risks
