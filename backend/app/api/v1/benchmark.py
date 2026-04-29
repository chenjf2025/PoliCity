"""
对标分析API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.indicator import BenchmarkCity, Evaluation
from app.services.evaluator import EvaluationEngine

router = APIRouter(prefix="/benchmark", tags=["对标分析"])


class BenchmarkCityResponse(BaseModel):
    id: str
    city_code: str
    city_name: str
    province: Optional[str]
    city_level: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class CompareRequest(BaseModel):
    region_code: str
    region_name: str
    benchmark_city_codes: List[str]
    report_year: int


@router.get("/cities")
def list_benchmark_cities(
    city_level: Optional[str] = Query(None, description="城市级别筛选"),
    db: Session = Depends(get_db)
):
    """获取对标城市列表（同时从BenchmarkCity表和已导入数据的区域获取）"""
    from app.models.indicator import RawData

    # 从 BenchmarkCity 表获取城市
    query = db.query(BenchmarkCity).filter(BenchmarkCity.status == 1)
    if city_level:
        query = query.filter(BenchmarkCity.city_level == city_level)
    benchmark_cities = query.all()

    # 从 RawData 表获取已导入的区域
    raw_regions = db.query(
        RawData.region_code,
        RawData.region_name
    ).distinct().all()

    # 合并去重
    city_map = {}
    for c in benchmark_cities:
        city_map[c.city_code] = {
            "id": str(c.id),
            "city_code": c.city_code,
            "city_name": c.city_name,
            "province": c.province,
            "city_level": c.city_level,
            "description": c.description
        }
    for region_code, region_name in raw_regions:
        if region_code not in city_map:
            city_map[region_code] = {
                "id": region_code,
                "city_code": region_code,
                "city_name": region_name,
                "province": None,
                "city_level": None,
                "description": "已导入数据的区域"
            }

    cities = list(city_map.values())
    return {
        "count": len(cities),
        "cities": cities
    }


@router.post("/cities")
def create_benchmark_city(
    city: BenchmarkCityResponse,
    db: Session = Depends(get_db)
):
    """添加对标城市"""
    existing = db.query(BenchmarkCity).filter(
        BenchmarkCity.city_code == city.city_code
    ).first()

    if existing:
        return {"error": "城市编码已存在"}

    db_city = BenchmarkCity(**city.model_dump())
    db.add(db_city)
    db.commit()
    db.refresh(db_city)

    return {"id": str(db_city.id), "message": "添加成功"}


@router.post("/compare")
def compare_with_benchmark(
    request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    与对标城市进行全方位对比
    """
    evaluator = EvaluationEngine(db)

    # 获取本区域的雷达图数据
    self_radar = evaluator.get_radar_data(
        request.region_code,
        request.report_year
    )

    # 获取对标城市的雷达图数据
    benchmark_radars = []
    for city_code in request.benchmark_city_codes:
        city = db.query(BenchmarkCity).filter(
            BenchmarkCity.city_code == city_code
        ).first()

        if city:
            radar = evaluator.get_radar_data(city_code, request.report_year)
            radar["city_name"] = city.city_name
            radar["city_code"] = city_code
            benchmark_radars.append(radar)

    # 识别竞争劣势
    competitive_weaknesses = []

    if benchmark_radars:
        # 对每个维度进行比较
        for dim in self_radar["dimensions"]:
            self_score = dim["score"] or 0

            for benchmark in benchmark_radars:
                for b_dim in benchmark["dimensions"]:
                    if b_dim["name"] == dim["name"]:
                        b_score = b_dim["score"] or 0
                        gap = b_score - self_score

                        if gap > 10:  # 落后超过10分
                            competitive_weaknesses.append({
                                "dimension": dim["name"],
                                "self_score": round(self_score, 2),
                                "benchmark_score": round(b_score, 2),
                                "gap": round(gap, 2),
                                "benchmark_city": benchmark["city_name"]
                            })

    # 计算总分对比
    self_total = self_radar.get("total_score", 0)
    benchmark_totals = []

    for benchmark in benchmark_radars:
        benchmark_totals.append({
            "city_code": benchmark["city_code"],
            "city_name": benchmark["city_name"],
            "total_score": benchmark.get("total_score", 0)
        })

    # 排序找出排名
    all_totals = benchmark_totals + [{"city_code": request.region_code, "city_name": request.region_name, "total_score": self_total}]
    all_totals.sort(key=lambda x: x["total_score"], reverse=True)

    rank = 1
    for t in all_totals:
        if t["city_code"] == request.region_code:
            break
        rank += 1

    return {
        "region_code": request.region_code,
        "region_name": request.region_name,
        "report_year": request.report_year,
        "self_analysis": {
            "radar": self_radar,
            "total_score": self_total,
            "rank": rank,
            "total_cities": len(all_totals)
        },
        "benchmark_cities": benchmark_radars,
        "competitive_weaknesses": sorted(
            competitive_weaknesses,
            key=lambda x: x["gap"],
            reverse=True
        )[:10],  # 最多返回10个劣势
        "rankings": all_totals
    }


@router.get("/result/{compare_id}")
def get_compare_result(
    compare_id: str,
    db: Session = Depends(get_db)
):
    """
    获取对标结果详情
    """
    # 简化实现，实际应存储对标结果
    return {
        "compare_id": compare_id,
        "message": "详情查询接口"
    }
