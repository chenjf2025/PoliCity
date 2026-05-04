"""
评价引擎 - 基于AHP层次分析法和线性加权综合法
总指数 S = Σ(Wi * Pi)
"""
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.indicator import Indicator, RawData, StandardScore, Evaluation
from app.services.normalizer import Normalizer


class EvaluationEngine:
    """城市发展评价引擎"""

    # 六大维度权重配置
    DIMENSION_WEIGHTS = {
        "economic": 0.20,    # 经济活力与结构优化
        "culture": 0.15,    # 文化繁荣与软实力
        "human": 0.20,      # 人力资源与人才发展
        "urban": 0.20,      # 城乡融合与均衡发展
        "governance": 0.20, # 城市治理能力与韧性
        "environment": 0.15  # 生态环境与绿色低碳
    }

    # 维度编码前缀映射
    DIMENSION_PREFIX = {
        "E": "economic",
        "C": "culture",
        "H": "human",
        "U": "urban",
        "G": "governance",
        "EV": "environment"
    }

    def __init__(self, db: Session):
        self.db = db
        self.normalizer = Normalizer()

    def get_dimension_from_code(self, code: str) -> str:
        """从指标编码获取维度名称"""
        prefix = code[0]
        return self.DIMENSION_PREFIX.get(prefix, "unknown")

    def calculate_indicator_score(
        self,
        indicator_code: str,
        region_code: str,
        report_year: int,
        report_month: Optional[int] = None
    ) -> Optional[float]:
        """
        计算单个指标的标准化得分

        Args:
            indicator_code: 指标编码
            region_code: 行政区划代码
            report_year: 报告年份
            report_month: 报告月份

        Returns:
            标准化得分 [0, 100]
        """
        # 获取指标信息
        indicator = self.db.query(Indicator).filter(
            Indicator.indicator_code == indicator_code
        ).first()

        if not indicator:
            return None

        # 获取原始数据
        query = self.db.query(RawData).filter(
            RawData.indicator_code == indicator_code,
            RawData.report_year == report_year,
            RawData.region_code == region_code
        )
        if report_month:
            query = query.filter(RawData.report_month == report_month)

        raw_data = query.first()
        if not raw_data:
            return None

        # 获取当期所有城市的该指标值用于计算边界
        all_values = self.db.query(RawData.raw_value).filter(
            RawData.indicator_code == indicator_code,
            RawData.report_year == report_year
        ).all()

        values = [v[0] for v in all_values]
        min_val, max_val = self.normalizer.calculate_bounds(values)

        # 标准化计算
        score = self.normalizer.normalize(
            raw_data.raw_value,
            min_val,
            max_val,
            indicator.polarity
        )

        return score

    def calculate_dimension_score(
        self,
        dimension: str,
        region_code: str,
        report_year: int,
        report_month: Optional[int] = None
    ) -> Optional[float]:
        """
        计算某个维度的加权得分

        Args:
            dimension: 维度名称 (economic/culture/human/urban/governance)
            report_year: 报告年份
            region_code: 行政区划代码
            report_month: 报告月份

        Returns:
            维度加权得分
        """
        # 获取该维度下的所有指标
        dimension_cn_map = {
            "economic": "经济活力",
            "culture": "文化繁荣",
            "human": "人力资源",
            "urban": "城乡融合",
            "governance": "城市治理",
            "environment": "生态环境"
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
            score = self.calculate_indicator_score(
                indicator.indicator_code,
                region_code,
                report_year,
                report_month
            )

            if score is not None:
                weighted_sum += indicator.weight * score
                total_weight += indicator.weight

        if total_weight == 0:
            return None

        # 归一化处理
        return round(weighted_sum / total_weight, 2)

    def calculate_total_score(
        self,
        region_code: str,
        report_year: int,
        report_month: Optional[int] = None
    ) -> Dict[str, float]:
        """
        计算综合评价总分

        Returns:
            包含各维度得分和总分的字典
        """
        dimension_scores = {}

        for dimension in self.DIMENSION_WEIGHTS.keys():
            score = self.calculate_dimension_score(
                dimension,
                region_code,
                report_year,
                report_month
            )
            dimension_scores[dimension] = score if score is not None else 0.0

        # 计算总分 S = Σ(Wi * Pi)
        total_score = sum(
            self.DIMENSION_WEIGHTS[dim] * score
            for dim, score in dimension_scores.items()
        )

        dimension_scores["total"] = round(total_score, 2)

        # 转换维度名称为中文
        result = {
            "region_code": region_code,
            "report_year": report_year,
            "report_month": report_month,
            "economic_score": dimension_scores.get("economic"),
            "culture_score": dimension_scores.get("culture"),
            "human_score": dimension_scores.get("human"),
            "urban_score": dimension_scores.get("urban"),
            "governance_score": dimension_scores.get("governance"),
            "environment_score": dimension_scores.get("environment"),
            "total_score": dimension_scores.get("total")
        }

        return result

    def get_radar_data(
        self,
        region_code: str,
        report_year: int,
        report_month: Optional[int] = None
    ) -> Dict:
        """
        获取雷达图数据

        Returns:
            五大维度得分用于雷达图展示
        """
        scores = self.calculate_total_score(region_code, report_year, report_month)

        # 获取数据来源信息
        raw_data = self.db.query(RawData).filter(
            RawData.region_code == region_code,
            RawData.report_year == report_year,
            RawData.is_deleted == 0
        ).first()

        source_info = None
        if raw_data and raw_data.source_name:
            source_info = {
                "source_name": raw_data.source_name,
                "source_url": raw_data.source_url
            }

        return {
            "dimensions": [
                {"name": "经济活力", "code": "economic", "score": scores.get("economic_score"), "weight": 0.20},
                {"name": "文化繁荣", "code": "culture", "score": scores.get("culture_score"), "weight": 0.15},
                {"name": "人力资源", "code": "human", "score": scores.get("human_score"), "weight": 0.20},
                {"name": "城乡融合", "code": "urban", "score": scores.get("urban_score"), "weight": 0.20},
                {"name": "城市治理", "code": "governance", "score": scores.get("governance_score"), "weight": 0.20},
                {"name": "生态环境", "code": "environment", "score": scores.get("environment_score"), "weight": 0.15}
            ],
            "total_score": scores.get("total_score"),
            "source": source_info
        }

    def identify_shortboards(
        self,
        region_code: str,
        report_year: int,
        benchmark_region_code: Optional[str] = None,
        threshold: float = 10.0
    ) -> List[Dict]:
        """
        识别短板指标

        Args:
            region_code: 目标区域代码
            benchmark_region_code: 对标区域代码（可选）
            threshold: 差距阈值（默认10分）

        Returns:
            短板指标列表
        """
        shortboards = []

        indicators = self.db.query(Indicator).filter(
            Indicator.status == 1
        ).all()

        for indicator in indicators:
            target_score = self.calculate_indicator_score(
                indicator.indicator_code,
                region_code,
                report_year
            )

            if target_score is None:
                continue

            # 如果有对标区域，比较差距
            if benchmark_region_code:
                benchmark_score = self.calculate_indicator_score(
                    indicator.indicator_code,
                    benchmark_region_code,
                    report_year
                )

                if benchmark_score and (benchmark_score - target_score) > threshold:
                    shortboards.append({
                        "indicator_code": indicator.indicator_code,
                        "indicator_name": indicator.indicator_name,
                        "dimension": indicator.dimension_cn,
                        "target_score": target_score,
                        "benchmark_score": benchmark_score,
                        "gap": round(benchmark_score - target_score, 2),
                        "suggestion": f"建议提升{indicator.indicator_name}"
                    })
            else:
                # 无对标时，低于60分的视为短板
                if target_score < 60:
                    shortboards.append({
                        "indicator_code": indicator.indicator_code,
                        "indicator_name": indicator.indicator_name,
                        "dimension": indicator.dimension_cn,
                        "score": target_score,
                        "suggestion": f"{indicator.indicator_name}需要重点关注"
                    })

        return sorted(shortboards, key=lambda x: x.get("gap", 0), reverse=True)
