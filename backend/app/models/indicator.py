import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

# 上海时区
SHANGHAI_TZ = timezone(timedelta(hours=8))

def now_shanghai():
    """返回上海时区的当前时间"""
    return datetime.now(SHANGHAI_TZ)


class Indicator(Base):
    """指标字典表"""
    __tablename__ = "dict_indicator"

    indicator_code = Column(String(10), primary_key=True)
    dimension = Column(String(20), nullable=False)  # economic/culture/human/urban/governance
    dimension_cn = Column(String(20), nullable=False)
    indicator_name = Column(String(100), nullable=False)
    indicator_name_en = Column(String(100))
    weight = Column(Float, nullable=False)
    polarity = Column(Integer, nullable=False)  # 1=正向, -1=负向
    unit = Column(String(20))
    data_source = Column(String(100))
    description = Column(Text)
    status = Column(Integer, default=1)
    version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=now_shanghai)
    updated_at = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)

    raw_data = relationship("RawData", back_populates="indicator")
    standard_scores = relationship("StandardScore", back_populates="indicator")


class RawData(Base):
    """原始数据表"""
    __tablename__ = "data_raw_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_code = Column(String(20), nullable=False)
    region_name = Column(String(50), nullable=False)
    indicator_code = Column(String(10), ForeignKey("dict_indicator.indicator_code"), nullable=False)
    report_year = Column(Integer, nullable=False)
    report_month = Column(Integer)
    raw_value = Column(Float, nullable=False)
    data_status = Column(Integer, default=1)  # 1=已审核, 0=待审核
    created_by = Column(String(50))
    created_at = Column(DateTime, default=now_shanghai)
    updated_at = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)

    __table_args__ = (
        UniqueConstraint('region_code', 'indicator_code', 'report_year', 'report_month', name='uq_raw_data'),
    )

    indicator = relationship("Indicator", back_populates="raw_data")


class StandardScore(Base):
    """标准化得分表"""
    __tablename__ = "data_standard_score"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_code = Column(String(20), nullable=False)
    region_name = Column(String(50), nullable=False)
    indicator_code = Column(String(10), ForeignKey("dict_indicator.indicator_code"), nullable=False)
    report_year = Column(Integer, nullable=False)
    report_month = Column(Integer)
    raw_value = Column(Float, nullable=False)
    min_value = Column(Float)
    max_value = Column(Float)
    standard_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=now_shanghai)

    __table_args__ = (
        UniqueConstraint('region_code', 'indicator_code', 'report_year', 'report_month', name='uq_standard_score'),
    )

    indicator = relationship("Indicator", back_populates="standard_scores")


class Evaluation(Base):
    """综合评价表"""
    __tablename__ = "data_evaluation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_code = Column(String(20), nullable=False)
    region_name = Column(String(50), nullable=False)
    report_year = Column(Integer, nullable=False)
    report_month = Column(Integer)

    # 五大维度得分
    economic_score = Column(Float)
    culture_score = Column(Float)
    human_score = Column(Float)
    urban_score = Column(Float)
    governance_score = Column(Float)

    # 综合得分
    total_score = Column(Float)
    city_rank = Column(Integer)
    province_rank = Column(Integer)

    created_at = Column(DateTime, default=now_shanghai)


class SimulationLog(Base):
    """仿真记录表"""
    __tablename__ = "data_simulation_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50))
    region_code = Column(String(20), nullable=False)
    region_name = Column(String(50))
    simulation_name = Column(String(100))
    params = Column(JSONB, nullable=False)
    original_total_score = Column(Float)
    simulated_total_score = Column(Float)
    score_delta = Column(Float)
    rank_change = Column(Integer)
    agent_analysis = Column(JSONB)
    analysis_report = Column(Text)  # Markdown格式的分析报告
    created_at = Column(DateTime, default=now_shanghai)


class BenchmarkCity(Base):
    """对标城市表"""
    __tablename__ = "dict_benchmark_city"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_code = Column(String(20), unique=True, nullable=False)
    city_name = Column(String(50), nullable=False)
    province = Column(String(50))
    city_level = Column(String(20))  # 一线城市/二线城市/三线城市
    population = Column(Float)
    gdp = Column(Float)
    description = Column(Text)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, default=now_shanghai)


class User(Base):
    """用户表"""
    __tablename__ = "sys_user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # admin/user/analyst
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=now_shanghai)
