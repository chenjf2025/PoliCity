"""
生成CGDSS测试数据
包含51个指标，覆盖10个城市，2020-2025年数据
"""
import sys
sys.path.insert(0, '/app')

import random
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models.indicator import Indicator, RawData, StandardScore, Evaluation

# 上海时区
SHANGHAI_TZ = timezone(timedelta(hours=8))

def now_shanghai():
    return datetime.now(SHANGHAI_TZ)

# 测试区域
TEST_REGIONS = [
    {"code": "310000", "name": "上海市", "level": "一线城市"},
    {"code": "330100", "name": "杭州市", "level": "新一线城市"},
    {"code": "320100", "name": "南京市", "level": "新一线城市"},
    {"code": "330200", "name": "宁波市", "level": "新一线城市"},
    {"code": "320500", "name": "苏州市", "level": "新一线城市"},
    {"code": "330600", "name": "温州市", "level": "二线城市"},
    {"code": "320300", "name": "无锡市", "level": "新一线城市"},
    {"code": "330300", "name": "嘉兴市", "level": "二线城市"},
    {"code": "320400", "name": "常州市", "level": "二线城市"},
    {"code": "320600", "name": "南通市", "level": "二线城市"},
]

TEST_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# 指标值范围配置 (min, max, 是否递增趋势)
INDICATOR_RANGES = {
    # 经济活力 (E01-E08 计算指标, E09-E10 观察指标)
    "E01": (8, 28, True),      # 人均GDP (万元) - 正向，递增
    "E02": (0.5, 6, True),     # 地均GDP (亿元/km²) - 正向
    "E03": (45, 75, True),     # 第三产业占比 (%) - 正向
    "E04": (10, 50, True),     # 数字经济占比 (%) - 正向
    "E05": (1.5, 4.5, True),  # R&D投入强度 (%) - 正向
    "E06": (10, 90, True),    # 万人发明专利 (件) - 正向
    "E07": (8, 28, True),     # 全员劳动生产率 (万元/人) - 正向
    "E08": (5000, 35000, True), # 高新技术企业数量 (家) - 正向
    "E09": (-5, 15, False),   # 外资增长率 (%) - 观察指标
    "E10": (3, 15, False),    # 社消零增速 (%) - 观察指标

    # 文化繁荣 (C01-C08)
    "C01": (1, 5, True),       # 人均藏书 (册) - 正向
    "C02": (5, 25, True),     # 十万人博物馆数 (个) - 正向
    "C03": (8, 22, True),     # 人均文娱消费占比 (%) - 正向
    "C04": (0.5, 3.5, True),  # 年人均演出场次 - 正向
    "C05": (50, 600, True),    # 非遗项目数 (项) - 正向
    "C06": (0.5, 10, True),   # 入境旅游占比 (%) - 正向
    "C07": (3, 15, True),     # 文化产业增加值占比 (%) - 正向
    "C08": (2, 6, True),      # 人均体育场地 (m²) - 正向

    # 人力资源 (H01-H08)
    "H01": (10, 15, True),     # 平均受教育年限 (年) - 正向
    "H02": (15000, 45000, True), # 大专以上人数 (人/10万) - 正向
    "H03": (15, 40, True),    # 高技能人才占比 (%) - 正向
    "H04": (10000, 100000, True), # 净流入大学生 (人) - 正向
    "H05": (80, 99, True),   # 养老保险参保率 (%) - 正向
    "H06": (2, 6, True),     # 每千人医师数 (人) - 正向
    "H07": (75, 85, True),    # 人均预期寿命 (岁) - 正向
    "H08": (3, 7, False),    # 失业率 (%) - 负向

    # 城乡融合 (U01-U08)
    "U01": (5, 30, True),     # 涉农贷款增速 (%) - 正向
    "U02": (85, 100, True),  # 自来水普及率 (%) - 正向
    "U03": (85, 100, True),  # 通硬化路率 (%) - 正向
    "U04": (1.5, 2.8, False),# 城乡收入比 - 负向（越低越好）
    "U05": (28, 42, False),  # 农村恩格尔系数 (%) - 负向
    "U06": (0.8, 1.4, False),# 城乡教育经费差异系数 - 负向
    "U07": (55, 90, True),   # 城镇化率 (%) - 正向
    "U08": (70, 98, True),   # 县域内就诊率 (%) - 正向

    # 城市治理 (G01-G08, G09观察指标)
    "G01": (60, 100, True),  # 一网通管覆盖率 (%) - 正向
    "G02": (70, 100, True),  # 一网通办率 (%) - 正向
    "G03": (80, 99, True),   # 生命线工程完好率 (%) - 正向
    "G04": (60, 95, True),   # 空气优良天数 (%) - 正向
    "G05": (50, 98, True),   # 垃圾分类覆盖率 (%) - 正向
    "G06": (70, 98, True),   # 热线解决率 (%) - 正向
    "G07": (75, 98, True),   # 群众满意度 (%) - 正向
    "G08": (35, 55, True),   # 建成区绿化率 (%) - 正向
    "G09": (0.1, 1.5, False),# 安全事故死亡率 (人/万人) - 观察指标，负向

    # 生态环境 (EV01-EV08)
    "EV01": (60, 95, True),  # 空气优良天数比例 (%) - 正向
    "EV02": (1, 8, False),   # 单位GDP污染物排放强度 - 负向
    "EV03": (85, 100, True), # 垃圾无害化处理率 (%) - 正向
    "EV04": (80, 100, True), # 污水收集处理率 (%) - 正向
    "EV05": (35, 55, True),  # 建成区绿化覆盖率 (%) - 正向
    "EV06": (2, 10, True),   # 单位GDP能耗降低率 (%) - 正向
    "EV07": (50, 92, True),  # 地表水Ⅲ类水体比例 (%) - 正向
    "EV08": (3, 12, True),   # 万元GDP用水量下降率 (%) - 正向
}

# 城市发展水平系数（影响指标生成的基础值）
CITY_COEFFICIENTS = {
    "310000": 1.2,   # 上海 - 最高
    "330100": 1.15,  # 杭州
    "320100": 1.1,   # 南京
    "320500": 1.12,  # 苏州
    "330200": 1.05,  # 宁波
    "320300": 0.98,  # 无锡
    "330600": 0.9,   # 温州
    "330300": 0.88,  # 嘉兴
    "320400": 0.92,  # 常州
    "320600": 0.9,   # 南通
}


def generate_value(code: str, city_code: str, year: int, base_year: int = 2020) -> float:
    """根据指标类型、城市系数、年份生成值"""
    if code not in INDICATOR_RANGES:
        return 50.0

    min_val, max_val, is_upward = INDICATOR_RANGES[code]
    city_coeff = CITY_COEFFICIENTS.get(city_code, 1.0)

    # 计算年份递增因子（每年递增2-5%）
    years_diff = year - base_year
    trend_factor = 1 + (years_diff * random.uniform(0.02, 0.05)) if is_upward else 1 - (years_diff * random.uniform(0.01, 0.03))
    trend_factor = max(0.5, min(2.0, trend_factor))

    # 基础值
    base_value = (min_val + max_val) / 2

    # 加入城市系数和趋势
    value = base_value * city_coeff * trend_factor

    # 添加随机波动（±10%）
    value = value * random.uniform(0.9, 1.1)

    # 确保在合理范围内
    value = max(min_val * 0.8, min(max_val * 1.2, value))

    return round(value, 2)


def clear_existing_data(db):
    """清除现有测试数据"""
    print("清除现有数据...")
    db.query(StandardScore).delete()
    db.query(RawData).delete()
    db.query(Evaluation).delete()
    db.commit()
    print("清除完成")


def generate_raw_data(db):
    """生成原始数据"""
    indicators = db.query(Indicator).all()
    total_count = 0

    for region in TEST_REGIONS:
        for year in TEST_YEARS:
            for indicator in indicators:
                # 检查是否已存在
                existing = db.query(RawData).filter(
                    RawData.region_code == region["code"],
                    RawData.indicator_code == indicator.indicator_code,
                    RawData.report_year == year
                ).first()

                if existing:
                    continue

                raw_value = generate_value(
                    indicator.indicator_code,
                    region["code"],
                    year
                )

                raw_data = RawData(
                    region_code=region["code"],
                    region_name=region["name"],
                    indicator_code=indicator.indicator_code,
                    report_year=year,
                    raw_value=raw_value,
                    data_status=1,
                    source_name=indicator.data_source or "测试数据",
                    created_by="system"
                )
                db.add(raw_data)
                total_count += 1

    db.commit()
    print(f"生成原始数据: {total_count} 条")


def generate_standard_scores(db):
    """生成标准化得分"""
    print("计算标准化得分...")

    from collections import defaultdict
    indicator_values = defaultdict(list)

    raw_data_list = db.query(RawData).all()
    for rd in raw_data_list:
        indicator_values[rd.indicator_code].append(rd.raw_value)

    indicator_bounds = {}
    for code, values in indicator_values.items():
        indicator_bounds[code] = {"min": min(values), "max": max(values)}

    score_count = 0
    for rd in raw_data_list:
        existing = db.query(StandardScore).filter(
            StandardScore.region_code == rd.region_code,
            StandardScore.indicator_code == rd.indicator_code,
            StandardScore.report_year == rd.report_year
        ).first()

        if existing:
            continue

        indicator = db.query(Indicator).filter(
            Indicator.indicator_code == rd.indicator_code
        ).first()

        if not indicator:
            continue

        bounds = indicator_bounds.get(rd.indicator_code, {"min": 0, "max": 100})
        min_val, max_val = bounds["min"], bounds["max"]

        if max_val > min_val:
            if indicator.polarity == 1:
                standard_score = ((rd.raw_value - min_val) / (max_val - min_val)) * 100
            else:
                standard_score = ((max_val - rd.raw_value) / (max_val - min_val)) * 100
        else:
            standard_score = 50

        standard_score = max(0, min(100, standard_score))

        score = StandardScore(
            region_code=rd.region_code,
            region_name=rd.region_name,
            indicator_code=rd.indicator_code,
            report_year=rd.report_year,
            raw_value=rd.raw_value,
            min_value=min_val,
            max_value=max_val,
            standard_score=round(standard_score, 2)
        )
        db.add(score)
        score_count += 1

    db.commit()
    print(f"生成标准化得分: {score_count} 条")


def generate_evaluations(db):
    """生成综合评价数据"""
    print("计算综合评价...")

    DIMENSION_WEIGHTS = {
        "economic": 0.20,
        "culture": 0.15,
        "human": 0.20,
        "urban": 0.20,
        "governance": 0.20,
        "environment": 0.15
    }

    evaluation_count = 0

    for region in TEST_REGIONS:
        for year in TEST_YEARS:
            existing = db.query(Evaluation).filter(
                Evaluation.region_code == region["code"],
                Evaluation.report_year == year
            ).first()

            if existing:
                continue

            dimension_scores = {}

            for dim_code, weight in DIMENSION_WEIGHTS.items():
                indicators = db.query(Indicator).filter(
                    Indicator.dimension == dim_code,
                    Indicator.status == 1,
                    Indicator.is_observation == 0
                ).all()

                if not indicators:
                    dimension_scores[dim_code] = None
                    continue

                total_weight = 0
                weighted_sum = 0

                for ind in indicators:
                    score = db.query(StandardScore).filter(
                        StandardScore.region_code == region["code"],
                        StandardScore.indicator_code == ind.indicator_code,
                        StandardScore.report_year == year
                    ).first()

                    if score:
                        weighted_sum += ind.weight * score.standard_score
                        total_weight += ind.weight

                if total_weight > 0:
                    dimension_scores[dim_code] = round(weighted_sum / total_weight, 2)
                else:
                    dimension_scores[dim_code] = None

            total_score = sum(
                DIMENSION_WEIGHTS[dim] * (dimension_scores.get(dim) or 0)
                for dim in DIMENSION_WEIGHTS.keys()
            )

            evaluation = Evaluation(
                region_code=region["code"],
                region_name=region["name"],
                report_year=year,
                economic_score=dimension_scores.get("economic"),
                culture_score=dimension_scores.get("culture"),
                human_score=dimension_scores.get("human"),
                urban_score=dimension_scores.get("urban"),
                governance_score=dimension_scores.get("governance"),
                environment_score=dimension_scores.get("environment"),
                total_score=round(total_score, 2)
            )
            db.add(evaluation)
            evaluation_count += 1

    db.commit()
    print(f"生成综合评价: {evaluation_count} 条")


def main():
    print("=" * 50)
    print("CGDSS 测试数据生成")
    print("=" * 50)

    db = SessionLocal()
    try:
        clear_existing_data(db)
        generate_raw_data(db)
        generate_standard_scores(db)
        generate_evaluations(db)

        print("\n" + "=" * 50)
        print("数据生成完成！")
        print(f"区域: {len(TEST_REGIONS)} 个")
        print(f"年份: {len(TEST_YEARS)} 年 (2020-2025)")
        print(f"指标: 51 个 (含8个生态环境指标)")
        print("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
