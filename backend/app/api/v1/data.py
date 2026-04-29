"""
数据采集API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import uuid
import pandas as pd
from app.core.database import get_db
from app.models.indicator import RawData, StandardScore, Indicator, now_shanghai
from app.services.normalizer import Normalizer

router = APIRouter(prefix="/data", tags=["数据采集"])


class RawDataCreate(BaseModel):
    region_code: str
    region_name: str
    indicator_code: str
    report_year: int
    report_month: Optional[int] = None
    raw_value: float


class RawDataResponse(BaseModel):
    id: str
    region_code: str
    region_name: str
    indicator_code: str
    report_year: int
    report_month: Optional[int]
    raw_value: float
    data_status: int

    class Config:
        from_attributes = True


class NormalizeRequest(BaseModel):
    report_year: int
    report_month: Optional[int] = None


@router.post("/raw", response_model=RawDataResponse)
def create_raw_data(
    data: RawDataCreate,
    db: Session = Depends(get_db)
):
    """单条录入原始数据"""
    # 验证指标存在
    indicator = db.query(Indicator).filter(
        Indicator.indicator_code == data.indicator_code
    ).first()

    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    # 检查是否已存在
    existing = db.query(RawData).filter(
        RawData.region_code == data.region_code,
        RawData.indicator_code == data.indicator_code,
        RawData.report_year == data.report_year,
        RawData.report_month == data.report_month
    ).first()

    if existing:
        # 更新
        existing.raw_value = data.raw_value
        existing.updated_at = now_shanghai()
        db.commit()
        db.refresh(existing)
        return RawDataResponse(
            id=str(existing.id),
            region_code=existing.region_code,
            region_name=existing.region_name,
            indicator_code=existing.indicator_code,
            report_year=existing.report_year,
            report_month=existing.report_month,
            raw_value=existing.raw_value,
            data_status=existing.data_status
        )

    # 创建新记录
    db_data = RawData(
        id=uuid.uuid4(),
        region_code=data.region_code,
        region_name=data.region_name,
        indicator_code=data.indicator_code,
        report_year=data.report_year,
        report_month=data.report_month,
        raw_value=data.raw_value
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)

    return RawDataResponse(
        id=str(db_data.id),
        region_code=db_data.region_code,
        region_name=db_data.region_name,
        indicator_code=db_data.indicator_code,
        report_year=db_data.report_year,
        report_month=db_data.report_month,
        raw_value=db_data.raw_value,
        data_status=db_data.data_status
    )


class ImportFormData(BaseModel):
    report_year: int = 2024


@router.post("/raw/import")
async def import_raw_data(
    request: Request,
    report_year: int = 2024,
    db: Session = Depends(get_db)
):
    """
    批量导入原始数据 (Excel格式)
    Excel格式要求:
    - 第一列: region_code (行政区划代码)
    - 第二列: region_name (行政区划名称)
    - 第三列开始: 指标编码 (E01, C01, ...)
    """
    # 获取上传的文件
    form = await request.form()
    file = form.get("file")

    if not file:
        raise HTTPException(status_code=400, detail="没有上传文件")

    # 读取文件内容
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")

    # 解析文件
    import io
    filename = file.filename.lower() if file.filename else ""
    if filename.endswith('.csv'):
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="仅支持Excel或CSV文件")

    # 验证列
    required_cols = ['region_code', 'region_name']
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"缺少必需列: {col}")

    # 获取指标列（除region_code和region_name外的所有列）
    indicator_codes = [col for col in df.columns if col not in required_cols]

    imported_count = 0
    errors = []

    for idx, row in df.iterrows():
        region_code = str(row['region_code'])
        region_name = str(row['region_name'])

        for indicator_code in indicator_codes:
            raw_value = row[indicator_code]

            if pd.isna(raw_value):
                continue

            try:
                # 检查指标是否存在
                indicator = db.query(Indicator).filter(
                    Indicator.indicator_code == indicator_code
                ).first()

                if not indicator:
                    errors.append(f"行{idx+2}: 指标{indicator_code}不存在")
                    continue

                # 创建或更新数据
                existing = db.query(RawData).filter(
                    RawData.region_code == region_code,
                    RawData.indicator_code == indicator_code,
                    RawData.report_year == report_year
                ).first()

                if existing:
                    existing.raw_value = float(raw_value)
                    existing.updated_at = now_shanghai()
                else:
                    db_data = RawData(
                        id=uuid.uuid4(),
                        region_code=region_code,
                        region_name=region_name,
                        indicator_code=indicator_code,
                        report_year=report_year,
                        raw_value=float(raw_value)
                    )
                    db.add(db_data)

                imported_count += 1

            except Exception as e:
                errors.append(f"行{idx+2}, 指标{indicator_code}: {str(e)}")

    db.commit()

    return {
        "message": "导入完成",
        "imported_count": imported_count,
        "errors": errors[:20]  # 最多返回20个错误
    }


@router.get("/raw", response_model=List[RawDataResponse])
def list_raw_data(
    region_code: Optional[str] = None,
    indicator_code: Optional[str] = None,
    report_year: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """查询原始数据列表"""
    query = db.query(RawData)

    if region_code:
        query = query.filter(RawData.region_code == region_code)
    if indicator_code:
        query = query.filter(RawData.indicator_code == indicator_code)
    if report_year:
        query = query.filter(RawData.report_year == report_year)

    records = query.order_by(
        RawData.report_year.desc(),
        RawData.indicator_code
    ).offset(skip).limit(limit).all()

    return [
        RawDataResponse(
            id=str(r.id),
            region_code=r.region_code,
            region_name=r.region_name,
            indicator_code=r.indicator_code,
            report_year=r.report_year,
            report_month=r.report_month,
            raw_value=r.raw_value,
            data_status=r.data_status
        )
        for r in records
    ]


@router.post("/normalize")
def normalize_data(
    request: NormalizeRequest,
    db: Session = Depends(get_db)
):
    """
    触发标准化计算
    将原始数据转换为0-100的标准化得分
    """
    normalizer = Normalizer()

    # 获取所有指标
    indicators = db.query(Indicator).filter(Indicator.status == 1).all()

    processed_count = 0
    errors = []

    for indicator in indicators:
        # 获取该指标当期所有原始数据
        raw_records = db.query(RawData).filter(
            RawData.indicator_code == indicator.indicator_code,
            RawData.report_year == request.report_year
        ).all()

        if not raw_records:
            continue

        values = [r.raw_value for r in raw_records]
        min_val, max_val = normalizer.calculate_bounds(values)

        for raw in raw_records:
            try:
                # 计算标准化得分
                score = normalizer.normalize(
                    raw.raw_value,
                    min_val,
                    max_val,
                    indicator.polarity
                )

                # 保存或更新标准化得分
                existing = db.query(StandardScore).filter(
                    StandardScore.region_code == raw.region_code,
                    StandardScore.indicator_code == indicator.indicator_code,
                    StandardScore.report_year == request.report_year
                ).first()

                if existing:
                    existing.raw_value = raw.raw_value
                    existing.min_value = min_val
                    existing.max_value = max_val
                    existing.standard_score = score
                else:
                    std_score = StandardScore(
                        id=uuid.uuid4(),
                        region_code=raw.region_code,
                        region_name=raw.region_name,
                        indicator_code=indicator.indicator_code,
                        report_year=request.report_year,
                        report_month=raw.report_month,
                        raw_value=raw.raw_value,
                        min_value=min_val,
                        max_value=max_val,
                        standard_score=score
                    )
                    db.add(std_score)

                processed_count += 1

            except Exception as e:
                errors.append(f"{indicator.indicator_code}: {str(e)}")

    db.commit()

    return {
        "message": "标准化计算完成",
        "processed_count": processed_count,
        "errors": errors
    }


@router.get("/standard-score")
def get_standard_scores(
    region_code: str,
    report_year: int,
    report_month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取标准化得分"""
    query = db.query(StandardScore).filter(
        StandardScore.region_code == region_code,
        StandardScore.report_year == report_year
    )

    if report_month:
        query = query.filter(StandardScore.report_month == report_month)

    scores = query.all()

    return {
        "region_code": region_code,
        "report_year": report_year,
        "scores": [
            {
                "indicator_code": s.indicator_code,
                "raw_value": s.raw_value,
                "standard_score": s.standard_score
            }
            for s in scores
        ]
    }
