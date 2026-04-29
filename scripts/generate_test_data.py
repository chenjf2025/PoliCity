"""
测试数据生成脚本 - 生成虚拟测试数据
用于测试导入功能、评价引擎、仿真模拟等模块
"""
import sys
sys.path.insert(0, '/app')

import random
from datetime import datetime
from app.core.database import SessionLocal, engine, Base
from app.models.indicator import Indicator, RawData, StandardScore, Evaluation

# 地区配置
REGIONS = [
    {"code": "default", "name": "测试城市"},
    {"code": "BJ", "name": "北京市", "level": "一线城市"},
    {"code": "SH", "name": "上海市", "level": "一线城市"},
    {"code": "GZ", "name": "广州市", "level": "一线城市"},
    {"code": "SZ", "name": "深圳市", "level": "一线城市"},
    {"code": "HZ", "name": "杭州市", "level": "二线城市"},
    {"code": "NJ", "name": "南京市", "level": "二线城市"},
    {"code": "WH", "name": "武汉市", "level": "二线城市"},
    {"code": "CD", "name": "成都市", "level": "二线城市"},
    {"code": "XA", "name": "西安市", "level": "二线城市"},
]

# 年份范围
YEARS = [2020, 2021, 2022, 2023, 2024]

# 各指标合理取值范围 (min, max, 小数位数)
INDICATOR_RANGES = {
    # 经济活力 (E01-E10)
    "E01": (5.0, 25.0, 2),      # 人均地区生产总值 (万元)
    "E02": (0.5, 5.0, 2),       # 地均GDP产出 (亿元/km²)
    "E03": (40.0, 80.0, 1),     # 第三产业占比 (%)
    "E04": (5.0, 50.0, 2),       # 数字经济核心产业增加值占比 (%)
    "E05": (1.5, 6.0, 2),        # R&D经费投入强度 (%)
    "E06": (10.0, 100.0, 1),     # 万人发明专利拥有量 (件/万人)
    "E07": (-5.0, 20.0, 1),      # 外资增长率 (%)
    "E08": (3.0, 15.0, 1),       # 社会消费品零售总额增速 (%)
    "E09": (10.0, 30.0, 2),      # 全员劳动生产率 (万元/人)
    "E10": (1000, 10000, 0),     # 高新技术企业数量 (家)

    # 文化繁荣 (C01-C08)
    "C01": (1.0, 5.0, 2),        # 人均图书馆藏书量 (册/人)
    "C02": (5.0, 30.0, 1),       # 十万人博物馆数量 (个/10万人)
    "C03": (8.0, 20.0, 1),       # 人均文娱消费支出占比 (%)
    "C04": (0.5, 3.0, 2),        # 年人均演出场次 (场次/人)
    "C05": (50, 500, 0),         # 非遗项目数量 (项)
    "C06": (0.5, 10.0, 2),       # 入境旅游人数占比 (%)
    "C07": (2.0, 15.0, 2),       # 文化产业增加值占比 (%)
    "C08": (2.0, 6.0, 2),        # 人均体育场地面积 (m²/人)

    # 人力资源 (H01-H08)
    "H01": (9.0, 14.0, 1),       # 平均受教育年限 (年)
    "H02": (10000, 40000, 0),    # 十万人大专及以上学历人数 (人/10万人)
    "H03": (15.0, 40.0, 1),      # 高技能人才占比 (%)
    "H04": (50000, 500000, 0),  # 年度净流入大学生数 (人)
    "H05": (70.0, 99.0, 1),     # 基本养老保险参保率 (%)
    "H06": (2.0, 5.0, 2),        # 每千人医师数 (人/千人)
    "H07": (75.0, 85.0, 1),     # 人均预期寿命 (岁)
    "H08": (3.0, 6.0, 1),        # 城镇调查失业率 (%)

    # 城乡融合 (U01-U08)
    "U01": (70.0, 95.0, 1),     # 县域内就诊率 (%)
    "U02": (5.0, 25.0, 1),      # 涉农贷款增速 (%)
    "U03": (85.0, 100.0, 1),    # 自来水普及率 (%)
    "U04": (85.0, 100.0, 1),    # 通硬化路率 (%)
    "U05": (1.5, 3.0, 2),       # 城乡收入比 (比值)
    "U06": (25.0, 45.0, 1),     # 农村恩格尔系数 (%)
    "U07": (0.1, 0.5, 3),       # 城乡教育经费差异系数 (系数)
    "U08": (50.0, 90.0, 1),     # 城镇化率 (%)

    # 城市治理 (G01-G09)
    "G01": (50.0, 100.0, 1),    # "一网统管"覆盖率 (%)
    "G02": (80.0, 100.0, 1),    # "一网通办"办结率 (%)
    "G03": (80.0, 100.0, 1),    # 生命线工程完好率 (%)
    "G04": (60.0, 95.0, 0),     # 空气质量优良天数占比 (%)
    "G05": (50.0, 100.0, 1),    # 生活垃圾分类覆盖率 (%)
    "G06": (70.0, 95.0, 1),     # 市民热线问题解决率 (%)
    "G07": (80.0, 95.0, 1),     # 公众安全感指数 (指数)
    "G08": (35.0, 50.0, 1),     # 建成区绿化率 (%)
    "G09": (0.5, 2.0, 2),       # 安全事故死亡率 (人/万人)
}

# 城市等级系数 (影响指标数值)
CITY_LEVEL_FACTOR = {
    "default": 0.7,
    "一线城市": 1.0,
    "二线城市": 0.8,
    "三线城市": 0.6,
}


def generate_value(indicator_code: str, region_level: str, year: int, base_year: int = 2020) -> float:
    """
    根据指标编码、地区等级和年份生成合理的数值
    """
    if indicator_code not in INDICATOR_RANGES:
        return 0.0

    min_val, max_val, decimals = INDICATOR_RANGES[indicator_code]
    level_factor = CITY_LEVEL_FACTOR.get(region_level, 0.7)

    # 年份增长系数 (每年增长 1-3%)
    year_growth = 1 + (year - base_year) * random.uniform(0.01, 0.03)

    # 基础值
    base_value = (min_val + max_val) / 2

    # 加入随机波动 (±10%)
    random_factor = random.uniform(0.9, 1.1)

    # 计算最终值
    value = base_value * level_factor * year_growth * random_factor

    # 确保在范围内
    value = max(min_val * 0.8, min(max_val * 1.2, value))

    return round(value, decimals)


def get_region_level(region_code: str) -> str:
    """获取地区等级"""
    for r in REGIONS:
        if r["code"] == region_code:
            return r.get("level", "二线城市")
    return "二线城市"


def generate_raw_data(db: SessionLocal, clear_existing: bool = False):
    """
    生成原始数据
    """
    # 清空现有数据
    if clear_existing:
        db.query(RawData).delete()
        db.commit()
        print("已清空现有原始数据")

    # 获取所有指标
    indicators = db.query(Indicator).all()
    indicator_codes = [ind.indicator_code for ind in indicators]

    total_count = 0

    for region in REGIONS:
        for year in YEARS:
            for code in indicator_codes:
                # 检查是否已存在
                existing = db.query(RawData).filter(
                    RawData.region_code == region["code"],
                    RawData.indicator_code == code,
                    RawData.report_year == year,
                    RawData.report_month.is_(None)
                ).first()

                if existing:
                    continue

                region_level = get_region_level(region["code"])
                raw_value = generate_value(code, region_level, year)

                raw_data = RawData(
                    region_code=region["code"],
                    region_name=region["name"],
                    indicator_code=code,
                    report_year=year,
                    raw_value=raw_value,
                    data_status=1,
                    created_by="system"
                )
                db.add(raw_data)
                total_count += 1

    db.commit()
    print(f"成功生成 {total_count} 条原始数据记录")
    return total_count


def generate_standard_scores(db: SessionLocal):
    """
    生成标准化得分
    基于极差标准化: P = (x - min) / (max - min) * 100
    """
    from app.services.normalizer import Normalizer
    from app.models.indicator import Indicator, RawData, StandardScore

    normalizer = Normalizer()
    count = 0

    for region in REGIONS:
        for year in YEARS:
            # 获取该年份所有指标数据
            raw_records = db.query(RawData).filter(
                RawData.region_code == region["code"],
                RawData.report_year == year,
                RawData.report_month.is_(None)
            ).all()

            for raw in raw_records:
                # 检查是否已存在标准化得分
                existing = db.query(StandardScore).filter(
                    StandardScore.region_code == region["code"],
                    StandardScore.indicator_code == raw.indicator_code,
                    StandardScore.report_year == year
                ).first()

                if existing:
                    continue

                # 获取指标信息
                indicator = db.query(Indicator).filter(
                    Indicator.indicator_code == raw.indicator_code
                ).first()

                if not indicator:
                    continue

                # 获取当期所有城市的该指标值用于计算边界
                all_values = db.query(RawData.raw_value).filter(
                    RawData.indicator_code == raw.indicator_code,
                    RawData.report_year == year
                ).all()

                values = [v[0] for v in all_values]
                min_val, max_val = normalizer.calculate_bounds(values)

                # 标准化计算
                score = normalizer.normalize(
                    raw.raw_value,
                    min_val,
                    max_val,
                    indicator.polarity
                )

                # 保存标准化得分
                std_score = StandardScore(
                    region_code=region["code"],
                    region_name=region["name"],
                    indicator_code=raw.indicator_code,
                    report_year=year,
                    raw_value=raw.raw_value,
                    min_value=min_val,
                    max_value=max_val,
                    standard_score=score
                )
                db.add(std_score)
                count += 1

    db.commit()
    print(f"成功生成 {count} 条标准化得分记录")
    return count


def generate_evaluations(db: SessionLocal):
    """
    生成综合评价数据
    """
    from app.services.evaluator import EvaluationEngine

    evaluator = EvaluationEngine(db)

    count = 0
    for region in REGIONS:
        for year in YEARS:
            # 检查是否已存在
            existing = db.query(Evaluation).filter(
                Evaluation.region_code == region["code"],
                Evaluation.report_year == year
            ).first()

            if existing:
                continue

            try:
                result = evaluator.calculate_total_score(region["code"], year)

                # 保存评价结果
                eval_record = Evaluation(
                    region_code=region["code"],
                    region_name=region["name"],
                    report_year=year,
                    economic_score=result.get("economic_score"),
                    culture_score=result.get("culture_score"),
                    human_score=result.get("human_score"),
                    urban_score=result.get("urban_score"),
                    governance_score=result.get("governance_score"),
                    total_score=result.get("total_score")
                )
                db.add(eval_record)
                count += 1
            except Exception as e:
                print(f"  评价计算失败 {region['name']} {year}: {e}")

    db.commit()
    print(f"成功生成 {count} 条评价记录")
    return count


def main():
    """主函数"""
    print("=" * 50)
    print("CGDSS 测试数据生成脚本")
    print("=" * 50)

    # 确保表已创建
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. 生成原始数据
        print("\n[1/3] 生成原始数据...")
        raw_count = generate_raw_data(db, clear_existing=True)

        # 2. 生成标准化得分
        print("\n[2/3] 生成标准化得分...")
        score_count = generate_standard_scores(db)

        # 3. 生成综合评价
        print("\n[3/3] 生成综合评价...")
        eval_count = generate_evaluations(db)

        print("\n" + "=" * 50)
        print("数据生成完成!")
        print(f"  - 原始数据: {raw_count} 条")
        print(f"  - 标准化结果: {score_count} 个")
        print(f"  - 评价记录: {eval_count} 条")
        print("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
