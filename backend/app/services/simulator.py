"""
What-If 政策仿真模拟器
基于历史回归关系，模拟指标变化对总分的影响
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.indicator import Indicator, SimulationLog, RawData
from app.services.evaluator import EvaluationEngine
from app.services.normalizer import Normalizer
import uuid


class WhatIfSimulator:
    """政策仿真模拟器"""

    def __init__(self, db: Session):
        self.db = db
        self.evaluator = EvaluationEngine(db)
        self.normalizer = Normalizer()

    def simulate(
        self,
        region_code: str,
        region_name: str,
        report_year: int,
        simulation_params: List[Dict],
        user_id: Optional[str] = None,
        simulation_name: Optional[str] = None
    ) -> Dict:
        """
        执行What-If仿真

        Args:
            region_code: 行政区划代码
            region_name: 行政区划名称
            report_year: 报告年份
            simulation_params: 仿真参数列表
                [{"indicator_code": "E01", "simulated_value": 6.5}, ...]
            user_id: 用户ID
            simulation_name: 仿真名称

        Returns:
            仿真结果
        """
        # 获取原始总分
        original_scores = self.evaluator.calculate_total_score(
            region_code, report_year
        )
        original_total = original_scores.get("total_score", 0)

        # 计算仿真后的分数
        simulated_scores = self._calculate_simulated_scores(
            region_code, report_year, simulation_params
        )

        # 计算变化
        score_delta = simulated_scores.get("total_score", 0) - original_total

        # 保存仿真记录
        log = SimulationLog(
            id=uuid.uuid4(),
            user_id=user_id,
            region_code=region_code,
            simulation_name=simulation_name or f"仿真_{report_year}",
            params=simulation_params,
            original_total_score=original_total,
            simulated_total_score=simulated_scores.get("total_score"),
            score_delta=score_delta,
            rank_change=0  # 简化处理，实际需要计算排名变化
        )
        self.db.add(log)
        self.db.commit()

        return {
            "simulation_id": str(log.id),
            "region_code": region_code,
            "region_name": region_name,
            "report_year": report_year,
            "original_scores": original_scores,
            "simulated_scores": simulated_scores,
            "score_delta": round(score_delta, 2),
            "score_change_percent": round((score_delta / original_total * 100) if original_total > 0 else 0, 2),
            "changed_dimensions": self._get_changed_dimensions(
                original_scores, simulated_scores
            )
        }

    def _calculate_simulated_scores(
        self,
        region_code: str,
        report_year: int,
        simulation_params: List[Dict]
    ) -> Dict:
        """
        计算仿真后的各维度得分

        Args:
            simulation_params: [{"indicator_code": "E01", "simulated_value": 6.5}, ...]

        Returns:
            仿真后的得分
        """
        # 创建仿真参数映射
        param_map = {
            p["indicator_code"]: p["simulated_value"]
            for p in simulation_params
        }

        dimension_scores = {}

        for dimension in ["economic", "culture", "human", "urban", "governance"]:
            score = self._simulate_dimension_score(
                dimension, region_code, report_year, param_map
            )
            dimension_scores[dimension] = score if score is not None else 0.0

        # 计算总分
        dimension_weights = {
            "economic": 0.25,
            "culture": 0.15,
            "human": 0.20,
            "urban": 0.20,
            "governance": 0.20
        }

        total_score = sum(
            dimension_weights[dim] * score
            for dim, score in dimension_scores.items()
        )

        return {
            "economic_score": dimension_scores.get("economic"),
            "culture_score": dimension_scores.get("culture"),
            "human_score": dimension_scores.get("human"),
            "urban_score": dimension_scores.get("urban"),
            "governance_score": dimension_scores.get("governance"),
            "total_score": round(total_score, 2)
        }

    def _simulate_dimension_score(
        self,
        dimension: str,
        region_code: str,
        report_year: int,
        param_map: Dict[str, float]
    ) -> Optional[float]:
        """
        计算仿真后某维度的得分
        """
        # 获取该维度下的所有指标
        prefix_map = {
            "economic": "E",
            "culture": "C",
            "human": "H",
            "urban": "U",
            "governance": "G"
        }

        indicators = self.db.query(Indicator).filter(
            Indicator.dimension == dimension,
            Indicator.status == 1
        ).all()

        if not indicators:
            return None

        total_weight = 0.0
        weighted_sum = 0.0

        for indicator in indicators:
            # 检查是否有仿真参数
            if indicator.indicator_code in param_map:
                # 使用仿真值计算
                simulated_value = param_map[indicator.indicator_code]
                score = self._calculate_single_score_with_value(
                    indicator, region_code, report_year, simulated_value
                )
            else:
                # 使用原始值
                score = self.evaluator.calculate_indicator_score(
                    indicator.indicator_code, region_code, report_year
                )

            if score is not None:
                weighted_sum += indicator.weight * score
                total_weight += indicator.weight

        if total_weight == 0:
            return None

        return round(weighted_sum / total_weight, 2)

    def _calculate_single_score_with_value(
        self,
        indicator: Indicator,
        region_code: str,
        report_year: int,
        simulated_value: float
    ) -> float:
        """
        使用仿真值计算单个指标得分
        """
        # 获取当期所有城市的该指标值
        all_values = self.db.query(RawData.raw_value).filter(
            RawData.indicator_code == indicator.indicator_code,
            RawData.report_year == report_year
        ).all()

        values = [v[0] for v in all_values]
        min_val, max_val = self.normalizer.calculate_bounds(values)

        return self.normalizer.normalize(
            simulated_value,
            min_val,
            max_val,
            indicator.polarity
        )

    def _get_changed_dimensions(
        self,
        original: Dict,
        simulated: Dict
    ) -> List[Dict]:
        """获取变化的维度"""
        changes = []
        dimension_names = {
            "economic_score": "经济活力",
            "culture_score": "文化繁荣",
            "human_score": "人力资源",
            "urban_score": "城乡融合",
            "governance_score": "城市治理"
        }

        for key, name in dimension_names.items():
            orig = original.get(key, 0) or 0
            sim = simulated.get(key, 0) or 0
            delta = sim - orig

            if abs(delta) > 0.01:
                changes.append({
                    "dimension": name,
                    "original": round(orig, 2),
                    "simulated": round(sim, 2),
                    "delta": round(delta, 2)
                })

        return changes

    def get_simulation_history(
        self,
        region_code: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """获取历史仿真记录"""
        query = self.db.query(SimulationLog)

        if region_code:
            query = query.filter(SimulationLog.region_code == region_code)
        if user_id:
            query = query.filter(SimulationLog.user_id == user_id)

        logs = query.order_by(SimulationLog.created_at.desc()).limit(limit).all()

        return [
            {
                "id": str(log.id),
                "region_code": log.region_code,
                "simulation_name": log.simulation_name,
                "original_total_score": log.original_total_score,
                "simulated_total_score": log.simulated_total_score,
                "score_delta": log.score_delta,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
