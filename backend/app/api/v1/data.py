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
from app.models.indicator import RawData, StandardScore, Indicator, AnomalyRule, AnomalyRecord, now_shanghai
from app.services.normalizer import Normalizer

router = APIRouter(prefix="/data", tags=["数据采集"])


def detect_anomalies(db: Session, raw_data: RawData) -> List[AnomalyRecord]:
    """检测单条数据的异常"""
    anomalies = []

    # 获取该指标的所有异常规则
    rules = db.query(AnomalyRule).filter(
        AnomalyRule.indicator_code == raw_data.indicator_code,
        AnomalyRule.status == 1
    ).all()

    if not rules:
        return anomalies

    rule = rules[0]  # 每个指标只有一条规则

    # 1. 检查是否超出合理范围
    if rule.max_value is not None and raw_data.raw_value > rule.max_value:
        anomaly = AnomalyRecord(
            id=uuid.uuid4(),
            raw_data_id=raw_data.id,
            indicator_code=raw_data.indicator_code,
            region_code=raw_data.region_code,
            region_name=raw_data.region_name,
            report_year=raw_data.report_year,
            report_month=raw_data.report_month,
            value=raw_data.raw_value,
            anomaly_type="OVER_MAX",
            description=f"指标值{raw_data.raw_value}超过合理最大值{rule.max_value}",
            status="PENDING"
        )
        anomalies.append(anomaly)

    if rule.min_value is not None and raw_data.raw_value < rule.min_value:
        anomaly = AnomalyRecord(
            id=uuid.uuid4(),
            raw_data_id=raw_data.id,
            indicator_code=raw_data.indicator_code,
            region_code=raw_data.region_code,
            region_name=raw_data.region_name,
            report_year=raw_data.report_year,
            report_month=raw_data.report_month,
            value=raw_data.raw_value,
            anomaly_type="UNDER_MIN",
            description=f"指标值{raw_data.raw_value}低于合理最小值{rule.min_value}",
            status="PENDING"
        )
        anomalies.append(anomaly)

    # 2. 检查波动是否过大
    if rule.max_fluctuation is not None:
        # 获取上一年的数据
        prev_year = raw_data.report_year - 1
        prev_data = db.query(RawData).filter(
            RawData.region_code == raw_data.region_code,
            RawData.indicator_code == raw_data.indicator_code,
            RawData.report_year == prev_year,
            RawData.report_month == raw_data.report_month,
            RawData.is_deleted == 0
        ).first()

        if prev_data and prev_data.raw_value != 0:
            fluctuation = abs((raw_data.raw_value - prev_data.raw_value) / prev_data.raw_value) * 100
            if fluctuation > rule.max_fluctuation:
                anomaly = AnomalyRecord(
                    id=uuid.uuid4(),
                    raw_data_id=raw_data.id,
                    indicator_code=raw_data.indicator_code,
                    region_code=raw_data.region_code,
                    region_name=raw_data.region_name,
                    report_year=raw_data.report_year,
                    report_month=raw_data.report_month,
                    value=raw_data.raw_value,
                    anomaly_type="FLUCTUATION",
                    description=f"年度波动{fluctuation:.1f}%，超过阈值{rule.max_fluctuation}%（上年值:{prev_data.raw_value}）",
                    status="PENDING"
                )
                anomalies.append(anomaly)

    # 3. 检查趋势突变（需要连续3年数据）
    if raw_data.report_year >= 3:
        prev2_data = db.query(RawData).filter(
            RawData.region_code == raw_data.region_code,
            RawData.indicator_code == raw_data.indicator_code,
            RawData.report_year == raw_data.report_year - 2,
            RawData.report_month == raw_data.report_month,
            RawData.is_deleted == 0
        ).first()

        if prev2_data and prev_data:
            # 判断趋势方向
            trend1 = prev_data.raw_value - prev2_data.raw_value
            trend2 = raw_data.raw_value - prev_data.raw_value

            # 如果趋势方向相反，且幅度都较大
            if trend1 != 0 and trend2 != 0:
                same_direction = (trend1 > 0) == (trend2 > 0)
                if not same_direction:
                    prev_fluctuation = abs(trend1 / prev2_data.raw_value) * 100 if prev2_data.raw_value != 0 else 0
                    curr_fluctuation = abs(trend2 / prev_data.raw_value) * 100 if prev_data.raw_value != 0 else 0

                    if prev_fluctuation > 20 and curr_fluctuation > 20:
                        anomaly = AnomalyRecord(
                            id=uuid.uuid4(),
                            raw_data_id=raw_data.id,
                            indicator_code=raw_data.indicator_code,
                            region_code=raw_data.region_code,
                            region_name=raw_data.region_name,
                            report_year=raw_data.report_year,
                            report_month=raw_data.report_month,
                            value=raw_data.raw_value,
                            anomaly_type="TREND_CHANGE",
                            description=f"趋势突变：连续两年趋势方向相反",
                            status="PENDING"
                        )
                        anomalies.append(anomaly)

    return anomalies


class RawDataCreate(BaseModel):
    region_code: str
    region_name: str
    indicator_code: str
    report_year: int
    report_month: Optional[int] = None
    raw_value: float
    source_name: Optional[str] = None
    source_url: Optional[str] = None


class RawDataResponse(BaseModel):
    id: str
    region_code: str
    region_name: str
    indicator_code: str
    report_year: int
    report_month: Optional[int]
    raw_value: float
    data_status: int
    source_name: Optional[str] = None
    source_url: Optional[str] = None

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
        RawData.report_month == data.report_month,
        RawData.is_deleted == 0
    ).first()

    if existing:
        # 更新
        existing.raw_value = data.raw_value
        existing.source_name = data.source_name
        existing.source_url = data.source_url
        existing.updated_at = now_shanghai()
        db.commit()
        db.refresh(existing)

        # 检测异常
        anomalies = detect_anomalies(db, existing)
        for anomaly in anomalies:
            db.add(anomaly)
        db.commit()

        return RawDataResponse(
            id=str(existing.id),
            region_code=existing.region_code,
            region_name=existing.region_name,
            indicator_code=existing.indicator_code,
            report_year=existing.report_year,
            report_month=existing.report_month,
            raw_value=existing.raw_value,
            data_status=existing.data_status,
            source_name=existing.source_name,
            source_url=existing.source_url
        )

    # 创建新记录
    db_data = RawData(
        id=uuid.uuid4(),
        region_code=data.region_code,
        region_name=data.region_name,
        indicator_code=data.indicator_code,
        report_year=data.report_year,
        report_month=data.report_month,
        raw_value=data.raw_value,
        source_name=data.source_name,
        source_url=data.source_url
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)

    # 检测异常
    anomalies = detect_anomalies(db, db_data)
    for anomaly in anomalies:
        db.add(anomaly)
    db.commit()

    return RawDataResponse(
        id=str(db_data.id),
        region_code=db_data.region_code,
        region_name=db_data.region_name,
        indicator_code=db_data.indicator_code,
        report_year=db_data.report_year,
        report_month=db_data.report_month,
        raw_value=db_data.raw_value,
        data_status=db_data.data_status,
        source_name=db_data.source_name,
        source_url=db_data.source_url
    )


class ImportFormData(BaseModel):
    report_year: int = 2024


@router.post("/raw/import")
async def import_raw_data(
    request: Request,
    report_year: int = 2024,
    source_name: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    批量导入原始数据 (Excel格式)
    Excel格式要求:
    - 第一列: region_code (行政区划代码)
    - 第二列: region_name (行政区划名称)
    - 第三列开始: 指标编码 (E01, C01, ...)
    - 可选: source_name (来源名称), source_url (来源链接) 列
    也可通过表单参数指定统一的来源信息
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
    exclude_cols = required_cols + ['source_name', 'source_url']
    indicator_codes = [col for col in df.columns if col not in exclude_cols]

    imported_count = 0
    anomaly_count = 0
    errors = []
    new_raw_data_list = []  # 用于后续异常检测

    for idx, row in df.iterrows():
        region_code = str(row['region_code'])
        region_name = str(row['region_name'])

        # 获取来源（行内优先，其次表单参数）
        row_source_name = str(row['source_name']) if 'source_name' in df.columns and pd.notna(row.get('source_name')) else source_name
        row_source_url = str(row['source_url']) if 'source_url' in df.columns and pd.notna(row.get('source_url')) else source_url

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
                    RawData.report_year == report_year,
                    RawData.is_deleted == 0
                ).first()

                if existing:
                    existing.raw_value = float(raw_value)
                    existing.source_name = row_source_name
                    existing.source_url = row_source_url
                    existing.updated_at = now_shanghai()
                    new_raw_data_list.append(existing)
                else:
                    db_data = RawData(
                        id=uuid.uuid4(),
                        region_code=region_code,
                        region_name=region_name,
                        indicator_code=indicator_code,
                        report_year=report_year,
                        raw_value=float(raw_value),
                        source_name=row_source_name,
                        source_url=row_source_url
                    )
                    db.add(db_data)
                    new_raw_data_list.append(db_data)

                imported_count += 1

            except Exception as e:
                errors.append(f"行{idx+2}, 指标{indicator_code}: {str(e)}")

    db.commit()

    # 批量检测异常
    for raw_data in new_raw_data_list:
        anomalies = detect_anomalies(db, raw_data)
        for anomaly in anomalies:
            db.add(anomaly)
            anomaly_count += 1

    db.commit()

    return {
        "message": "导入完成",
        "imported_count": imported_count,
        "anomaly_count": anomaly_count,
        "errors": errors[:20]
    }

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
    query = db.query(RawData).filter(RawData.is_deleted == 0)

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
            data_status=r.data_status,
            source_name=r.source_name,
            source_url=r.source_url
        )
        for r in records
    ]


@router.delete("/raw/{data_id}")
def delete_raw_data(
    data_id: str,
    db: Session = Depends(get_db)
):
    """删除原始数据（软删除，需管理员审核）"""
    raw_data = db.query(RawData).filter(RawData.id == data_id).first()

    if not raw_data:
        raise HTTPException(status_code=404, detail="数据不存在")

    if raw_data.is_deleted == 1:
        raise HTTPException(status_code=400, detail="数据已提交删除申请")

    # 软删除
    raw_data.is_deleted = 1
    raw_data.data_status = -1  # 待审核状态
    raw_data.updated_at = now_shanghai()
    db.commit()

    return {"message": "删除申请已提交，请等待管理员审核"}


# ============== 异常数据管理API ==============

class AnomalyRecordResponse(BaseModel):
    id: str
    raw_data_id: str
    indicator_code: str
    region_code: str
    region_name: Optional[str]
    report_year: int
    report_month: Optional[int]
    value: float
    anomaly_type: str
    description: Optional[str]
    status: str
    confirmed_by: Optional[str]
    confirmed_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/anomalies", response_model=List[AnomalyRecordResponse])
def list_anomalies(
    status: Optional[str] = None,
    indicator_code: Optional[str] = None,
    region_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """查询异常记录列表"""
    query = db.query(AnomalyRecord)

    if status:
        query = query.filter(AnomalyRecord.status == status)
    if indicator_code:
        query = query.filter(AnomalyRecord.indicator_code == indicator_code)
    if region_code:
        query = query.filter(AnomalyRecord.region_code == region_code)

    records = query.order_by(
        AnomalyRecord.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        AnomalyRecordResponse(
            id=str(r.id),
            raw_data_id=str(r.raw_data_id),
            indicator_code=r.indicator_code,
            region_code=r.region_code,
            region_name=r.region_name,
            report_year=r.report_year,
            report_month=r.report_month,
            value=r.value,
            anomaly_type=r.anomaly_type,
            description=r.description,
            status=r.status,
            confirmed_by=r.confirmed_by,
            confirmed_at=r.confirmed_at.isoformat() if r.confirmed_at else None,
            created_at=r.created_at.isoformat() if r.created_at else None
        )
        for r in records
    ]


@router.post("/anomalies/{anomaly_id}/confirm")
def confirm_anomaly(
    anomaly_id: str,
    db: Session = Depends(get_db)
):
    """确认异常（管理员操作）"""
    anomaly = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()

    if not anomaly:
        raise HTTPException(status_code=404, detail="异常记录不存在")

    anomaly.status = "CONFIRMED"
    anomaly.confirmed_at = now_shanghai()
    db.commit()

    return {"message": "已确认异常"}


@router.post("/anomalies/{anomaly_id}/ignore")
def ignore_anomaly(
    anomaly_id: str,
    db: Session = Depends(get_db)
):
    """忽略异常（管理员操作）"""
    anomaly = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()

    if not anomaly:
        raise HTTPException(status_code=404, detail="异常记录不存在")

    anomaly.status = "IGNORED"
    anomaly.confirmed_at = now_shanghai()
    db.commit()

    return {"message": "已忽略异常"}


@router.post("/anomalies/batch-confirm")
def batch_confirm_anomalies(
    anomaly_ids: List[str],
    db: Session = Depends(get_db)
):
    """批量确认异常"""
    count = 0
    for anomaly_id in anomaly_ids:
        anomaly = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()
        if anomaly and anomaly.status == "PENDING":
            anomaly.status = "CONFIRMED"
            anomaly.confirmed_at = now_shanghai()
            count += 1

    db.commit()

    return {"message": f"已确认{count}条异常"}


@router.post("/anomalies/batch-ignore")
def batch_ignore_anomalies(
    anomaly_ids: List[str],
    db: Session = Depends(get_db)
):
    """批量忽略异常"""
    count = 0
    for anomaly_id in anomaly_ids:
        anomaly = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()
        if anomaly and anomaly.status == "PENDING":
            anomaly.status = "IGNORED"
            anomaly.confirmed_at = now_shanghai()
            count += 1

    db.commit()

    return {"message": f"已忽略{count}条异常"}


# ============== 异常规则管理API ==============

class AnomalyRuleCreate(BaseModel):
    indicator_code: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    max_fluctuation: Optional[float] = None
    description: Optional[str] = None


class AnomalyRuleResponse(BaseModel):
    id: str
    indicator_code: str
    min_value: Optional[float]
    max_value: Optional[float]
    max_fluctuation: Optional[float]
    description: Optional[str]
    status: int

    class Config:
        from_attributes = True


@router.get("/anomaly-rules", response_model=List[AnomalyRuleResponse])
def list_anomaly_rules(
    indicator_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """查询异常检测规则"""
    query = db.query(AnomalyRule)

    if indicator_code:
        query = query.filter(AnomalyRule.indicator_code == indicator_code)

    rules = query.all()

    return [
        AnomalyRuleResponse(
            id=str(r.id),
            indicator_code=r.indicator_code,
            min_value=r.min_value,
            max_value=r.max_value,
            max_fluctuation=r.max_fluctuation,
            description=r.description,
            status=r.status
        )
        for r in rules
    ]


@router.post("/anomaly-rules")
def create_or_update_anomaly_rule(
    rule: AnomalyRuleCreate,
    db: Session = Depends(get_db)
):
    """创建或更新异常检测规则"""
    # 验证指标存在
    indicator = db.query(Indicator).filter(
        Indicator.indicator_code == rule.indicator_code
    ).first()

    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    # 查找是否已存在
    existing = db.query(AnomalyRule).filter(
        AnomalyRule.indicator_code == rule.indicator_code
    ).first()

    if existing:
        existing.min_value = rule.min_value
        existing.max_value = rule.max_value
        existing.max_fluctuation = rule.max_fluctuation
        existing.description = rule.description
        existing.updated_at = now_shanghai()
        db.commit()
        return {"message": "规则已更新"}
    else:
        new_rule = AnomalyRule(
            id=uuid.uuid4(),
            indicator_code=rule.indicator_code,
            min_value=rule.min_value,
            max_value=rule.max_value,
            max_fluctuation=rule.max_fluctuation,
            description=rule.description,
            status=1
        )
        db.add(new_rule)
        db.commit()
        return {"message": "规则已创建"}


@router.delete("/anomaly-rules/{indicator_code}")
def delete_anomaly_rule(
    indicator_code: str,
    db: Session = Depends(get_db)
):
    """删除异常检测规则"""
    rule = db.query(AnomalyRule).filter(
        AnomalyRule.indicator_code == indicator_code
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    db.delete(rule)
    db.commit()

    return {"message": "规则已删除"}



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
        # 获取该指标当期所有原始数据（排除已删除的）
        raw_records = db.query(RawData).filter(
            RawData.indicator_code == indicator.indicator_code,
            RawData.report_year == request.report_year,
            RawData.is_deleted == 0
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


# ============== 删除审核管理API ==============

class PendingDeleteResponse(BaseModel):
    id: str
    region_code: str
    region_name: str
    indicator_code: str
    report_year: int
    report_month: Optional[int]
    raw_value: float
    source_name: Optional[str]
    source_url: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/pending-deletes", response_model=List[PendingDeleteResponse])
def list_pending_deletes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """查询待审核的删除申请"""
    records = db.query(RawData).filter(
        RawData.is_deleted == 1,
        RawData.data_status == -1
    ).order_by(
        RawData.updated_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        PendingDeleteResponse(
            id=str(r.id),
            region_code=r.region_code,
            region_name=r.region_name,
            indicator_code=r.indicator_code,
            report_year=r.report_year,
            report_month=r.report_month,
            raw_value=r.raw_value,
            source_name=r.source_name,
            source_url=r.source_url,
            updated_at=r.updated_at.isoformat() if r.updated_at else None
        )
        for r in records
    ]


@router.post("/pending-deletes/{data_id}/approve")
def approve_delete(
    data_id: str,
    db: Session = Depends(get_db)
):
    """审批通过删除申请（物理删除数据）"""
    raw_data = db.query(RawData).filter(RawData.id == data_id).first()

    if not raw_data:
        raise HTTPException(status_code=404, detail="数据不存在")

    if raw_data.is_deleted != 1:
        raise HTTPException(status_code=400, detail="该数据未申请删除")

    # 物理删除
    db.delete(raw_data)
    db.commit()

    return {"message": "删除申请已批准，数据已物理删除"}


@router.post("/pending-deletes/{data_id}/reject")
def reject_delete(
    data_id: str,
    db: Session = Depends(get_db)
):
    """拒绝删除申请（恢复数据）"""
    raw_data = db.query(RawData).filter(RawData.id == data_id).first()

    if not raw_data:
        raise HTTPException(status_code=404, detail="数据不存在")

    if raw_data.is_deleted != 1:
        raise HTTPException(status_code=400, detail="该数据未申请删除")

    # 恢复数据
    raw_data.is_deleted = 0
    raw_data.data_status = 1
    raw_data.updated_at = now_shanghai()
    db.commit()

    return {"message": "删除申请已拒绝，数据已恢复"}
