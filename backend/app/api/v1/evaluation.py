"""
评价引擎API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.evaluator import EvaluationEngine

router = APIRouter(prefix="/evaluation", tags=["评价引擎"])


@router.get("/radar")
def get_radar_data(
    region_code: str = Query(..., description="行政区划代码"),
    report_year: int = Query(..., description="报告年份"),
    report_month: Optional[int] = Query(None, description="报告月份"),
    db: Session = Depends(get_db)
):
    """
    获取雷达图数据（五大维度得分）
    """
    evaluator = EvaluationEngine(db)
    return evaluator.get_radar_data(region_code, report_year, report_month)


@router.get("/total")
def get_total_score(
    region_code: str = Query(..., description="行政区划代码"),
    report_year: int = Query(..., description="报告年份"),
    report_month: Optional[int] = Query(None, description="报告月份"),
    db: Session = Depends(get_db)
):
    """
    获取总分及排名
    """
    evaluator = EvaluationEngine(db)
    scores = evaluator.calculate_total_score(region_code, report_year, report_month)

    # 计算排名（简化处理，实际需要查询所有城市）
    from app.models.indicator import Evaluation
    all_evals = db.query(Evaluation).filter(
        Evaluation.report_year == report_year
    ).order_by(Evaluation.total_score.desc()).all()

    rank = 1
    for eval_record in all_evals:
        if eval_record.region_code == region_code:
            break
        rank += 1

    scores["city_rank"] = rank
    scores["total_cities"] = len(all_evals)

    return scores


@router.get("/trend")
def get_trend(
    region_code: str = Query(..., description="行政区划代码"),
    years: Optional[int] = Query(5, description="查询年数"),
    db: Session = Depends(get_db)
):
    """
    获取历史趋势
    """
    from app.models.indicator import Evaluation

    evals = db.query(Evaluation).filter(
        Evaluation.region_code == region_code
    ).order_by(Evaluation.report_year.desc()).limit(years).all()

    return {
        "region_code": region_code,
        "trend": [
            {
                "report_year": e.report_year,
                "total_score": e.total_score,
                "economic_score": e.economic_score,
                "culture_score": e.culture_score,
                "human_score": e.human_score,
                "urban_score": e.urban_score,
                "governance_score": e.governance_score
            }
            for e in reversed(evals)
        ]
    }


@router.get("/shortboard")
def get_shortboard_indicators(
    region_code: str = Query(..., description="行政区划代码"),
    report_year: int = Query(..., description="报告年份"),
    benchmark_region_code: Optional[str] = Query(None, description="对标区域代码"),
    threshold: float = Query(10.0, description="差距阈值"),
    db: Session = Depends(get_db)
):
    """
    获取短板指标预警
    """
    evaluator = EvaluationEngine(db)
    shortboards = evaluator.identify_shortboards(
        region_code,
        report_year,
        benchmark_region_code,
        threshold
    )

    return {
        "region_code": region_code,
        "report_year": report_year,
        "benchmark_region_code": benchmark_region_code,
        "shortboard_count": len(shortboards),
        "shortboards": shortboards
    }


@router.get("/dimension/{dimension}")
def get_dimension_detail(
    dimension: str,
    region_code: str = Query(..., description="行政区划代码"),
    report_year: int = Query(..., description="报告年份"),
    db: Session = Depends(get_db)
):
    """
    获取某个维度的详细得分
    """
    evaluator = EvaluationEngine(db)
    dimension_score = evaluator.calculate_dimension_score(
        dimension, region_code, report_year
    )

    # 获取该维度下所有指标的得分
    from app.models.indicator import Indicator, StandardScore

    indicators = db.query(Indicator).filter(
        Indicator.dimension == dimension,
        Indicator.status == 1
    ).all()

    indicator_scores = []
    for ind in indicators:
        score = evaluator.calculate_indicator_score(
            ind.indicator_code, region_code, report_year
        )
        if score is not None:
            indicator_scores.append({
                "code": ind.indicator_code,
                "name": ind.indicator_name,
                "weight": ind.weight,
                "score": score,
                "unit": ind.unit
            })

    dimension_names = {
        "economic": "经济活力",
        "culture": "文化繁荣",
        "human": "人力资源",
        "urban": "城乡融合",
        "governance": "城市治理"
    }

    return {
        "dimension": dimension,
        "dimension_cn": dimension_names.get(dimension, dimension),
        "overall_score": dimension_score,
        "indicators": indicator_scores
    }
