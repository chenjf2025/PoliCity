"""
指标管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.indicator import Indicator

router = APIRouter(prefix="/indicators", tags=["指标管理"])


class IndicatorResponse(BaseModel):
    indicator_code: str
    dimension: str
    dimension_cn: str
    indicator_name: str
    indicator_name_en: Optional[str] = None
    weight: float
    polarity: int
    unit: Optional[str] = None
    data_source: Optional[str] = None
    description: Optional[str] = None
    status: int

    class Config:
        from_attributes = True


class DimensionSummary(BaseModel):
    dimension: str
    dimension_cn: str
    weight: float
    indicator_count: int
    indicators: List[IndicatorResponse]


@router.get("", response_model=List[IndicatorResponse])
def list_indicators(
    dimension: Optional[str] = Query(None, description="按维度筛选"),
    status: Optional[int] = Query(1, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """获取指标列表"""
    query = db.query(Indicator)
    if dimension:
        query = query.filter(Indicator.dimension == dimension)
    if status is not None:
        query = query.filter(Indicator.status == status)

    return query.order_by(Indicator.indicator_code).all()


@router.get("/dimensions", response_model=List[DimensionSummary])
def get_dimension_summary(db: Session = Depends(get_db)):
    """获取六大维度汇总"""
    dimensions = [
        ("economic", "经济活力", 0.20),
        ("culture", "文化繁荣", 0.15),
        ("human", "人力资源", 0.20),
        ("urban", "城乡融合", 0.20),
        ("governance", "城市治理", 0.20),
        ("environment", "生态环境", 0.15)
    ]

    result = []
    for dim_code, dim_cn, weight in dimensions:
        indicators = db.query(Indicator).filter(
            Indicator.dimension == dim_code,
            Indicator.status == 1
        ).all()

        result.append(DimensionSummary(
            dimension=dim_code,
            dimension_cn=dim_cn,
            weight=weight,
            indicator_count=len(indicators),
            indicators=[IndicatorResponse.model_validate(ind) for ind in indicators]
        ))

    return result


@router.get("/{code}", response_model=IndicatorResponse)
def get_indicator(code: str, db: Session = Depends(get_db)):
    """获取单个指标详情"""
    indicator = db.query(Indicator).filter(
        Indicator.indicator_code == code
    ).first()

    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    return indicator


@router.post("", response_model=IndicatorResponse)
def create_indicator(
    indicator: IndicatorResponse,
    db: Session = Depends(get_db)
):
    """创建指标"""
    existing = db.query(Indicator).filter(
        Indicator.indicator_code == indicator.indicator_code
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="指标编码已存在")

    db_indicator = Indicator(**indicator.model_dump())
    db.add(db_indicator)
    db.commit()
    db.refresh(db_indicator)

    return db_indicator


@router.put("/{code}", response_model=IndicatorResponse)
def update_indicator(
    code: str,
    indicator: IndicatorResponse,
    db: Session = Depends(get_db)
):
    """更新指标"""
    db_indicator = db.query(Indicator).filter(
        Indicator.indicator_code == code
    ).first()

    if not db_indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    for key, value in indicator.model_dump().items():
        setattr(db_indicator, key, value)

    db.commit()
    db.refresh(db_indicator)

    return db_indicator


@router.delete("/{code}")
def delete_indicator(code: str, db: Session = Depends(get_db)):
    """删除指标（软删除）"""
    db_indicator = db.query(Indicator).filter(
        Indicator.indicator_code == code
    ).first()

    if not db_indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    db_indicator.status = 0
    db.commit()

    return {"message": "指标已删除"}
