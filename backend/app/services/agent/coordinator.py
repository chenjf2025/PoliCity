"""
Agent多智能体协调器
负责协调各领域Agent的工作，进行政策推演分析
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.services.evaluator import EvaluationEngine
from app.services.simulator import WhatIfSimulator
from app.services.llm import llm_service, AgentAnalysisPrompter
import json


class BaseAgent:
    """Agent基类"""

    def __init__(self, name: str, dimension: str, db: Session):
        self.name = name
        self.dimension = dimension
        self.db = db
        self.evaluator = EvaluationEngine(db)

    def analyze(self, context: Dict) -> Dict:
        """
        分析给定上下文，返回该领域Agent的见解

        Args:
            context: 包含region_code, report_year等上下文信息

        Returns:
            分析结果
        """
        raise NotImplementedError

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return f"你是{self.name}，负责分析{self.dimension}领域的发展状况。"


class EconomyAgent(BaseAgent):
    """经济Agent - 分析经济增长、产业结构、创新能力"""

    def __init__(self, db: Session):
        super().__init__("经济分析师", "经济活力与结构优化", db)

    def analyze(self, context: Dict) -> Dict:
        region_code = context.get("region_code")
        report_year = context.get("report_year")

        # 获取经济维度得分
        economic_score = self.evaluator.calculate_dimension_score(
            "economic", region_code, report_year
        )

        # 获取经济相关指标得分
        indicators = self.db.query(
            __import__('app.models.indicator', fromlist=['Indicator']).Indicator
        ).filter(
            __import__('app.models.indicator', fromlist=['Indicator']).Indicator.dimension == "economic",
            __import__('app.models.indicator', fromlist=['Indicator']).Indicator.status == 1
        ).all()

        indicator_scores = []
        for ind in indicators:
            score = self.evaluator.calculate_indicator_score(
                ind.indicator_code, region_code, report_year
            )
            if score is not None:
                indicator_scores.append({
                    "code": ind.indicator_code,
                    "name": ind.indicator_name,
                    "score": score,
                    "weight": ind.weight
                })

        # 分析结论
        analysis = self._generate_economy_analysis(economic_score, indicator_scores)

        return {
            "agent": self.name,
            "dimension": self.dimension,
            "overall_score": economic_score,
            "indicator_details": indicator_scores,
            "insights": analysis["insights"],
            "recommendations": analysis["recommendations"]
        }

    def _generate_economy_analysis(self, score: float, indicators: List[Dict]) -> Dict:
        """生成经济分析结论"""
        insights = []
        recommendations = []

        if score and score >= 80:
            insights.append("经济活力充沛，产业结构持续优化")
        elif score and score >= 60:
            insights.append("经济运行平稳，但转型压力犹存")
            recommendations.append("建议加快传统产业数字化转型")
        else:
            insights.append("经济增长动能不足，需要政策加力")
            recommendations.append("建议加大科技创新支持力度")
            recommendations.append("优化营商环境，激发市场活力")

        # 检查具体指标短板
        low_indicators = [i for i in indicators if i["score"] < 60]
        if low_indicators:
            for ind in low_indicators[:3]:
                recommendations.append(f"重点关注：{ind['name']} (得分{ind['score']:.1f})")

        return {"insights": insights, "recommendations": recommendations}


class CultureAgent(BaseAgent):
    """文化Agent - 分析文化建设、旅游发展、软实力"""

    def __init__(self, db: Session):
        super().__init__("文化分析师", "文化繁荣与软实力", db)

    def analyze(self, context: Dict) -> Dict:
        region_code = context.get("region_code")
        report_year = context.get("report_year")

        culture_score = self.evaluator.calculate_dimension_score(
            "culture", region_code, report_year
        )

        # 获取文化相关指标
        from app.models.indicator import Indicator
        indicators = self.db.query(Indicator).filter(
            Indicator.dimension == "culture",
            Indicator.status == 1
        ).all()

        indicator_scores = []
        for ind in indicators:
            score = self.evaluator.calculate_indicator_score(
                ind.indicator_code, region_code, report_year
            )
            if score is not None:
                indicator_scores.append({
                    "code": ind.indicator_code,
                    "name": ind.indicator_name,
                    "score": score
                })

        return {
            "agent": self.name,
            "dimension": self.dimension,
            "overall_score": culture_score,
            "indicator_details": indicator_scores,
            "insights": self._generate_insights(culture_score, indicator_scores),
            "recommendations": self._generate_recommendations(indicator_scores)
        }

    def _generate_insights(self, score: float, indicators: List[Dict]) -> List[str]:
        insights = []
        if score and score >= 80:
            insights.append("文化繁荣发展，居民精神生活丰富")
        elif score and score >= 60:
            insights.append("文化设施基本完善，但特色不够突出")
        else:
            insights.append("文化设施和文化消费有较大提升空间")
        return insights

    def _generate_recommendations(self, indicators: List[Dict]) -> List[str]:
        recs = []
        low_indicators = [i for i in indicators if i["score"] < 60]
        for ind in low_indicators[:2]:
            recs.append(f"加强{int(ind['name'].replace('人均', '').replace('十万人', '每十万人'))}建设")
        return recs


class HumanAgent(BaseAgent):
    """人力Agent - 分析人才流动、民生保障、公共服务"""

    def __init__(self, db: Session):
        super().__init__("人才分析师", "人力资源与人才发展", db)

    def analyze(self, context: Dict) -> Dict:
        region_code = context.get("region_code")
        report_year = context.get("report_year")

        human_score = self.evaluator.calculate_dimension_score(
            "human", region_code, report_year
        )

        from app.models.indicator import Indicator
        indicators = self.db.query(Indicator).filter(
            Indicator.dimension == "human",
            Indicator.status == 1
        ).all()

        indicator_scores = []
        for ind in indicators:
            score = self.evaluator.calculate_indicator_score(
                ind.indicator_code, region_code, report_year
            )
            if score is not None:
                indicator_scores.append({
                    "code": ind.indicator_code,
                    "name": ind.indicator_name,
                    "score": score
                })

        return {
            "agent": self.name,
            "dimension": self.dimension,
            "overall_score": human_score,
            "indicator_details": indicator_scores,
            "insights": self._generate_insights(human_score),
            "recommendations": self._generate_recommendations(indicator_scores)
        }

    def _generate_insights(self, score: float) -> List[str]:
        if score and score >= 80:
            return ["人才集聚效应显著，人力资源丰富"]
        elif score and score >= 60:
            return ["人才结构基本合理，但高层次人才不足"]
        else:
            return ["人才吸引力不足，需加强人才引进政策"]

    def _generate_recommendations(self, indicators: List[Dict]) -> List[str]:
        recs = []
        low_indicators = [i for i in indicators if i["score"] < 60]
        for ind in low_indicators[:2]:
            recs.append(f"提升{int(ind['name'].replace('年均', '').replace('占比', '').replace('率', ''))}水平")
        return recs


class PolicyAgent(BaseAgent):
    """政策Agent - 基于历史数据进行政策推演和What-If分析"""

    def __init__(self, db: Session):
        super().__init__("政策分析师", "政策仿真与推演", db)
        self.simulator = WhatIfSimulator(db)

    def analyze(self, context: Dict) -> Dict:
        """
        分析政策影响，使用DeepSeek LLM生成智能分析

        Args:
            context: {
                "region_code": str,
                "region_name": str,
                "report_year": int,
                "policy_changes": [{"indicator_code": "E05", "change_percent": 10}]
            }
        """
        region_code = context.get("region_code")
        region_name = context.get("region_name", region_code)
        report_year = context.get("report_year")
        policy_changes = context.get("policy_changes", [])

        # 将百分比变化转换为具体值
        simulation_params = self._convert_policy_to_simulation(
            region_code, report_year, policy_changes
        )

        # 执行仿真
        result = self.simulator.simulate(
            region_code=region_code,
            region_name=region_name,
            report_year=report_year,
            simulation_params=simulation_params,
            simulation_name="Agent Policy Analysis"
        )

        # 使用DeepSeek LLM生成智能分析
        llm_analysis = self._generate_llm_analysis(
            region_name, report_year, result, policy_changes
        )

        return {
            "agent": self.name,
            "dimension": self.dimension,
            "policy_analysis": {
                "original_score": result["original_scores"].get("total_score"),
                "simulated_score": result["simulated_scores"].get("total_score"),
                "expected_change": result["score_delta"],
                "change_percent": result["score_change_percent"],
                "dimension_impacts": result["changed_dimensions"]
            },
            "insights": self._generate_policy_insights(result),
            "recommendations": self._generate_policy_recommendations(result),
            "llm_analysis": llm_analysis  # LLM生成的Markdown格式分析报告
        }

    def _generate_llm_analysis(
        self,
        region_name: str,
        report_year: int,
        result: Dict,
        policy_changes: list
    ) -> str:
        """使用DeepSeek LLM生成分析报告"""
        prompt = AgentAnalysisPrompter.generate_policy_analysis_prompt(
            region_name=region_name,
            report_year=report_year,
            original_score=result["original_scores"].get("total_score", 0),
            simulated_score=result["simulated_scores"].get("total_score", 0),
            score_delta=result["score_delta"],
            dimension_changes=result.get("changed_dimensions", []),
            policy_changes=policy_changes
        )

        system_prompt = """你是一位城市发展政策专家，擅长分析政策调整对城市发展的影响。
请基于提供的数据，生成结构清晰、分析深入的建议报告。
输出必须使用Markdown格式，包含标题、列表、表格等格式。"""

        try:
            messages = [{"role": "user", "content": prompt}]
            analysis = llm_service.chat(messages, system_prompt=system_prompt)
            return analysis
        except Exception as e:
            return f"**LLM分析生成失败**: {str(e)}\n\n请稍后重试或检查API配置。"

    def _convert_policy_to_simulation(
        self,
        region_code: str,
        report_year: int,
        policy_changes: List[Dict]
    ) -> List[Dict]:
        """将政策变化转换为仿真参数"""
        from app.models.indicator import RawData

        params = []
        for change in policy_changes:
            indicator_code = change.get("indicator_code")
            change_percent = change.get("change_percent", 0)

            # 获取当前值
            raw_data = self.db.query(RawData).filter(
                RawData.indicator_code == indicator_code,
                RawData.region_code == region_code,
                RawData.report_year == report_year
            ).first()

            if raw_data:
                new_value = raw_data.raw_value * (1 + change_percent / 100)
                params.append({
                    "indicator_code": indicator_code,
                    "original_value": raw_data.raw_value,
                    "simulated_value": round(new_value, 2)
                })

        return params

    def _generate_policy_insights(self, result: Dict) -> List[str]:
        insights = []
        delta = result["score_delta"]

        if delta > 0:
            insights.append(f"政策调整预计可使总分提升{delta:.2f}分")
        elif delta < 0:
            insights.append(f"注意：该政策调整可能导致总分下降{-delta:.2f}分")
        else:
            insights.append("政策调整对总分影响较小")

        return insights

    def _generate_policy_recommendations(self, result: Dict) -> List[str]:
        recs = []
        dim_changes = result.get("changed_dimensions", [])

        positive_changes = [d for d in dim_changes if d.get("delta", 0) > 0]
        negative_changes = [d for d in dim_changes if d.get("delta", 0) < 0]

        if positive_changes:
            best = max(positive_changes, key=lambda x: x["delta"])
            recs.append(f"政策对{best['dimension']}拉动效果最明显 (+{best['delta']:.2f})")

        if negative_changes:
            worst = min(negative_changes, key=lambda x: x["delta"])
            recs.append(f"需关注{negative_changes[0]['dimension']}的负面影响")

        return recs


class AgentCoordinator:
    """多智能体协调器"""

    def __init__(self, db: Session):
        self.db = db
        self.agents = {
            "economy": EconomyAgent(db),
            "culture": CultureAgent(db),
            "human": HumanAgent(db),
            "policy": PolicyAgent(db)
        }

    def analyze_all_dimensions(self, context: Dict) -> Dict:
        """
        调用所有领域Agent进行全方位分析

        Args:
            context: {"region_code": str, "report_year": int}

        Returns:
            汇总所有Agent的分析结果
        """
        results = {}

        for key, agent in self.agents.items():
            if key != "policy":  # policy需要特殊参数
                try:
                    results[key] = agent.analyze(context)
                except Exception as e:
                    results[key] = {"error": str(e)}

        # 获取总体评分
        evaluator = EvaluationEngine(self.db)
        total_scores = evaluator.calculate_total_score(
            context.get("region_code"),
            context.get("report_year")
        )

        return {
            "region_code": context.get("region_code"),
            "report_year": context.get("report_year"),
            "total_score": total_scores.get("total_score"),
            "dimension_scores": {
                "economic": results.get("economy", {}).get("overall_score"),
                "culture": results.get("culture", {}).get("overall_score"),
                "human": results.get("human", {}).get("overall_score")
            },
            "agent_results": results,
            "summary": self._generate_summary(results, total_scores)
        }

    def analyze_policy_impact(self, context: Dict) -> Dict:
        """
        分析政策变化影响（调用Policy Agent）

        Args:
            context: {
                "region_code": str,
                "region_name": str,
                "report_year": int,
                "policy_changes": [...]
            }
        """
        policy_agent = self.agents["policy"]
        return policy_agent.analyze(context)

    def _generate_summary(self, results: Dict, total_scores: Dict) -> Dict:
        """生成综合分析摘要"""
        all_insights = []
        all_recommendations = []

        for key, result in results.items():
            if isinstance(result, dict):
                all_insights.extend(result.get("insights", []))
                all_recommendations.extend(result.get("recommendations", []))

        return {
            "key_insights": all_insights[:5],  # 保留前5条
            "priority_recommendations": all_recommendations[:5]  # 保留前5条
        }
