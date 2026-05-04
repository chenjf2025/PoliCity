"""
数据初始化脚本 - 50个指标数据初始化（含生态环境维度）
"""
import sys
sys.path.insert(0, '/app')

import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.indicator import Indicator, RawData, StandardScore, Evaluation

# 50个指标定义
INDICATORS = [
    # ========== 经济活力与结构优化 (E01-E09, 共9个计算指标 + 2个观察指标) ==========
    # 计算指标
    {"code": "E01", "dimension": "economic", "dimension_cn": "经济活力", "name": "人均地区生产总值", "weight": 0.11, "polarity": 1, "unit": "万元", "source": "统计局", "is_observation": 0},
    {"code": "E02", "dimension": "economic", "dimension_cn": "经济活力", "name": "地均GDP产出", "weight": 0.11, "polarity": 1, "unit": "亿元/km²", "source": "统计局", "is_observation": 0},
    {"code": "E03", "dimension": "economic", "dimension_cn": "经济活力", "name": "第三产业占比", "weight": 0.11, "polarity": 1, "unit": "%", "source": "统计局", "is_observation": 0},
    {"code": "E04", "dimension": "economic", "dimension_cn": "经济活力", "name": "数字经济核心产业增加值占比", "weight": 0.11, "polarity": 1, "unit": "%", "source": "大数据局", "is_observation": 0},
    {"code": "E05", "dimension": "economic", "dimension_cn": "经济活力", "name": "R&D经费投入强度", "weight": 0.17, "polarity": 1, "unit": "%", "source": "科技局", "is_observation": 0},
    {"code": "E06", "dimension": "economic", "dimension_cn": "经济活力", "name": "万人发明专利拥有量", "weight": 0.11, "polarity": 1, "unit": "件/万人", "source": "科技局", "is_observation": 0},
    {"code": "E07", "dimension": "economic", "dimension_cn": "经济活力", "name": "全员劳动生产率", "weight": 0.14, "polarity": 1, "unit": "万元/人", "source": "人社局", "is_observation": 0},
    {"code": "E08", "dimension": "economic", "dimension_cn": "经济活力", "name": "高新技术企业数量", "weight": 0.14, "polarity": 1, "unit": "家", "source": "科技局", "is_observation": 0},
    # 观察指标（不参与权重计算）
    {"code": "E09", "dimension": "economic", "dimension_cn": "经济活力", "name": "外资增长率", "weight": 0.0, "polarity": 1, "unit": "%", "source": "商务局", "is_observation": 1},
    {"code": "E10", "dimension": "economic", "dimension_cn": "经济活力", "name": "社会消费品零售总额增速", "weight": 0.0, "polarity": 1, "unit": "%", "source": "商务局", "is_observation": 1},

    # ========== 文化繁荣与软实力 (C01-C08) ==========
    {"code": "C01", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "人均图书馆藏书量", "weight": 0.15, "polarity": 1, "unit": "册/人", "source": "文旅局", "is_observation": 0},
    {"code": "C02", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "十万人博物馆数量", "weight": 0.12, "polarity": 1, "unit": "个/10万人", "source": "文旅局", "is_observation": 0},
    {"code": "C03", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "人均文娱消费支出占比", "weight": 0.13, "polarity": 1, "unit": "%", "source": "统计局", "is_observation": 0},
    {"code": "C04", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "年人均演出场次", "weight": 0.12, "polarity": 1, "unit": "场次/人", "source": "文旅局", "is_observation": 0},
    {"code": "C05", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "非遗项目数量", "weight": 0.13, "polarity": 1, "unit": "项", "source": "文旅局", "is_observation": 0},
    {"code": "C06", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "入境旅游人数占比", "weight": 0.10, "polarity": 1, "unit": "%", "source": "文旅局", "is_observation": 0},
    {"code": "C07", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "文化产业增加值占比", "weight": 0.15, "polarity": 1, "unit": "%", "source": "文旅局", "is_observation": 0},
    {"code": "C08", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "人均体育场地面积", "weight": 0.10, "polarity": 1, "unit": "m²/人", "source": "体育局", "is_observation": 0},

    # ========== 人力资源与人才发展 (H01-H08) ==========
    {"code": "H01", "dimension": "human", "dimension_cn": "人力资源", "name": "平均受教育年限", "weight": 0.15, "polarity": 1, "unit": "年", "source": "教育局", "is_observation": 0},
    {"code": "H02", "dimension": "human", "dimension_cn": "人力资源", "name": "十万人大专及以上学历人数", "weight": 0.15, "polarity": 1, "unit": "人/10万人", "source": "统计局", "is_observation": 0},
    {"code": "H03", "dimension": "human", "dimension_cn": "人力资源", "name": "高技能人才占比", "weight": 0.12, "polarity": 1, "unit": "%", "source": "人社局", "is_observation": 0},
    {"code": "H04", "dimension": "human", "dimension_cn": "人力资源", "name": "年度净流入大学生数", "weight": 0.13, "polarity": 1, "unit": "人", "source": "人社局", "is_observation": 0},
    {"code": "H05", "dimension": "human", "dimension_cn": "人力资源", "name": "基本养老保险覆盖率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "人社局", "is_observation": 0},
    {"code": "H06", "dimension": "human", "dimension_cn": "人力资源", "name": "每千人医师数", "weight": 0.13, "polarity": 1, "unit": "人/千人", "source": "卫健委", "is_observation": 0},
    {"code": "H07", "dimension": "human", "dimension_cn": "人力资源", "name": "人均预期寿命", "weight": 0.10, "polarity": 1, "unit": "岁", "source": "卫健委", "is_observation": 0},
    {"code": "H08", "dimension": "human", "dimension_cn": "人力资源", "name": "城镇调查失业率", "weight": 0.10, "polarity": -1, "unit": "%", "source": "统计局", "is_observation": 0},

    # ========== 城乡融合与均衡发展 (U01-U08) ==========
    {"code": "U01", "dimension": "urban", "dimension_cn": "城乡融合", "name": "涉农贷款增速", "weight": 0.14, "polarity": 1, "unit": "%", "source": "金融办", "is_observation": 0},
    {"code": "U02", "dimension": "urban", "dimension_cn": "城乡融合", "name": "自来水普及率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "住建局", "is_observation": 0},
    {"code": "U03", "dimension": "urban", "dimension_cn": "城乡融合", "name": "通硬化路率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "交通局", "is_observation": 0},
    {"code": "U04", "dimension": "urban", "dimension_cn": "城乡融合", "name": "城乡收入比", "weight": 0.16, "polarity": -1, "unit": "比值", "source": "统计局", "is_observation": 0},
    {"code": "U05", "dimension": "urban", "dimension_cn": "城乡融合", "name": "农村恩格尔系数", "weight": 0.12, "polarity": -1, "unit": "%", "source": "统计局", "is_observation": 0},
    {"code": "U06", "dimension": "urban", "dimension_cn": "城乡融合", "name": "城乡教育经费差异系数", "weight": 0.10, "polarity": -1, "unit": "系数", "source": "教育局", "is_observation": 0},
    {"code": "U07", "dimension": "urban", "dimension_cn": "城乡融合", "name": "城镇化率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "统计局", "is_observation": 0},
    {"code": "U08", "dimension": "urban", "dimension_cn": "城乡融合", "name": "县域内就诊率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "卫健委", "is_observation": 0},

    # ========== 城市治理能力与韧性 (G01-G08, G09为观察指标) ==========
    # 计算指标
    {"code": "G01", "dimension": "governance", "dimension_cn": "城市治理", "name": "\"一网通管\"覆盖率", "weight": 0.14, "polarity": 1, "unit": "%", "source": "大数据局", "is_observation": 0},
    {"code": "G02", "dimension": "governance", "dimension_cn": "城市治理", "name": "\"一网通办\"率", "weight": 0.14, "polarity": 1, "unit": "%", "source": "行政审批局", "is_observation": 0},
    {"code": "G03", "dimension": "governance", "dimension_cn": "城市治理", "name": "生命线工程完好率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "应急局", "is_observation": 0},
    {"code": "G04", "dimension": "governance", "dimension_cn": "城市治理", "name": "空气质量优良天数占比", "weight": 0.14, "polarity": 1, "unit": "%", "source": "生态环境局", "is_observation": 0},
    {"code": "G05", "dimension": "governance", "dimension_cn": "城市治理", "name": "生活垃圾分类覆盖率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "城管局", "is_observation": 0},
    {"code": "G06", "dimension": "governance", "dimension_cn": "城市治理", "name": "市民热线问题解决率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "信访局", "is_observation": 0},
    {"code": "G07", "dimension": "governance", "dimension_cn": "城市治理", "name": "群众对城市管理满意度", "weight": 0.10, "polarity": 1, "unit": "%", "source": "统计局", "is_observation": 0},
    {"code": "G08", "dimension": "governance", "dimension_cn": "城市治理", "name": "建成区绿化率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "住建局", "is_observation": 0},
    # 观察指标
    {"code": "G09", "dimension": "governance", "dimension_cn": "城市治理", "name": "安全事故死亡率", "weight": 0.0, "polarity": -1, "unit": "人/万人", "source": "应急局", "is_observation": 1},

    # ========== 生态环境与绿色低碳 (EV01-EV08) - 新增第6维度 ==========
    {"code": "EV01", "dimension": "environment", "dimension_cn": "生态环境", "name": "空气优良天数比例", "weight": 0.15, "polarity": 1, "unit": "%", "source": "生态环境局", "is_observation": 0},
    {"code": "EV02", "dimension": "environment", "dimension_cn": "生态环境", "name": "单位GDP主要污染物排放强度", "weight": 0.12, "polarity": -1, "unit": "kg/万元", "source": "生态环境局", "is_observation": 0},
    {"code": "EV03", "dimension": "environment", "dimension_cn": "生态环境", "name": "城镇生活垃圾无害化处理率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "城管局", "is_observation": 0},
    {"code": "EV04", "dimension": "environment", "dimension_cn": "生态环境", "name": "城镇生活污水收集处理率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "水务局", "is_observation": 0},
    {"code": "EV05", "dimension": "environment", "dimension_cn": "生态环境", "name": "建成区绿化覆盖率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "城管局/规划局", "is_observation": 0},
    {"code": "EV06", "dimension": "environment", "dimension_cn": "生态环境", "name": "单位GDP能耗降低率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "发改委/统计局", "is_observation": 0},
    {"code": "EV07", "dimension": "environment", "dimension_cn": "生态环境", "name": "地表水达到或好于Ⅲ类水体比例", "weight": 0.13, "polarity": 1, "unit": "%", "source": "生态环境局", "is_observation": 0},
    {"code": "EV08", "dimension": "environment", "dimension_cn": "生态环境", "name": "万元GDP用水量下降率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "水务局/统计局", "is_observation": 0},
]

# 测试数据年份
TEST_YEARS = [2023, 2024, 2025]

# 测试区域
TEST_REGIONS = [
    {"code": "310000", "name": "上海市"},
    {"code": "330000", "name": "杭州市"},
    {"code": "320000", "name": "南京市"},
    {"code": "330200", "name": "宁波市"},
    {"code": "320500", "name": "苏州市"},
]


def init_indicators():
    """初始化50个指标"""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for ind_data in INDICATORS:
            existing = db.query(Indicator).filter(
                Indicator.indicator_code == ind_data["code"]
            ).first()

            if existing:
                # 更新现有指标的属性
                existing.dimension = ind_data["dimension"]
                existing.dimension_cn = ind_data["dimension_cn"]
                existing.indicator_name = ind_data["name"]
                existing.weight = ind_data["weight"]
                existing.polarity = ind_data["polarity"]
                existing.data_source = ind_data["source"]
                existing.is_observation = ind_data.get("is_observation", 0)
                print(f"更新指标: {ind_data['code']} - {ind_data['name']}")
            else:
                indicator = Indicator(
                    indicator_code=ind_data["code"],
                    dimension=ind_data["dimension"],
                    dimension_cn=ind_data["dimension_cn"],
                    indicator_name=ind_data["name"],
                    weight=ind_data["weight"],
                    polarity=ind_data["polarity"],
                    unit=ind_data.get("unit"),
                    data_source=ind_data.get("source"),
                    status=1,
                    is_observation=ind_data.get("is_observation", 0),
                    version="2.0"  # 修订版
                )
                db.add(indicator)
                print(f"添加指标: {ind_data['code']} - {ind_data['name']}")

        db.commit()
        print(f"\n成功初始化 {len(INDICATORS)} 个指标")

    finally:
        db.close()


def generate_test_data():
    """生成模拟测试数据"""
    db = SessionLocal()
    try:
        # 为每个区域和年份生成数据
        for region in TEST_REGIONS:
            for year in TEST_YEARS:
                for ind_data in INDICATORS:
                    # 检查是否已有数据
                    existing = db.query(RawData).filter(
                        RawData.region_code == region["code"],
                        RawData.indicator_code == ind_data["code"],
                        RawData.report_year == year
                    ).first()

                    if existing:
                        continue

                    # 生成模拟值（根据指标类型和极性生成合理范围）
                    raw_value = generate_value(ind_data)

                    raw_data = RawData(
                        region_code=region["code"],
                        region_name=region["name"],
                        indicator_code=ind_data["code"],
                        report_year=year,
                        raw_value=raw_value,
                        data_status=1,
                        source_name=ind_data.get("source", "测试数据"),
                        created_by="system"
                    )
                    db.add(raw_data)

                print(f"生成 {region['name']} {year} 年数据完成")

        db.commit()
        print(f"\n成功生成模拟测试数据")

        # 生成标准化得分
        generate_standard_scores(db)

    finally:
        db.close()


def generate_value(ind_data: dict) -> float:
    """根据指标类型生成合理的模拟值"""
    code = ind_data["code"]
    polarity = ind_data["polarity"]

    # 为每个指标生成合理范围内的随机值
    ranges = {
        # 经济指标
        "E01": (8, 25),        # 人均GDP (万元)
        "E02": (0.5, 5),       # 地均GDP (亿元/km²)
        "E03": (45, 80),       # 第三产业占比 (%)
        "E04": (10, 45),       # 数字经济占比 (%)
        "E05": (1.5, 4.5),     # R&D投入强度 (%)
        "E06": (10, 80),       # 万人发明专利 (件)
        "E07": (8, 25),        # 全员劳动生产率 (万元/人)
        "E08": (5000, 30000),  # 高企数量 (家)
        "E09": (-5, 15),       # 外资增长率 (%)
        "E10": (3, 15),        # 社消零增速 (%)

        # 文化指标
        "C01": (1, 5),         # 人均藏书 (册)
        "C02": (5, 20),        # 十万人博物馆数 (个)
        "C03": (8, 20),        # 人均文娱消费占比 (%)
        "C04": (0.5, 3),       # 年人均演出场次
        "C05": (50, 500),      # 非遗项目数 (项)
        "C06": (0.5, 8),       # 入境旅游占比 (%)
        "C07": (3, 12),        # 文化产业增加值占比 (%)
        "C08": (2, 5),         # 人均体育场地 (m²)

        # 人力指标
        "H01": (10, 15),       # 平均受教育年限 (年)
        "H02": (15000, 40000), # 大专以上人数 (人/10万)
        "H03": (15, 35),       # 高技能人才占比 (%)
        "H04": (10000, 80000), # 净流入大学生 (人)
        "H05": (80, 99),       # 养老保险参保率 (%)
        "H06": (2, 5),         # 每千人医师数 (人)
        "H07": (75, 85),       # 人均预期寿命 (岁)
        "H08": (3, 7),         # 失业率 (%)

        # 城乡指标
        "U01": (5, 25),        # 涉农贷款增速 (%)
        "U02": (85, 100),      # 自来水普及率 (%)
        "U03": (85, 100),      # 通硬化路率 (%)
        "U04": (1.5, 3),       # 城乡收入比
        "U05": (28, 45),       # 农村恩格尔系数 (%)
        "U06": (0.8, 1.5),     # 城乡教育经费差异系数
        "U07": (55, 90),       # 城镇化率 (%)
        "U08": (70, 95),       # 县域内就诊率 (%), 负向

        # 治理指标
        "G01": (60, 100),      # 一网通管覆盖率 (%)
        "G02": (70, 100),      # 一网通办率 (%)
        "G03": (80, 99),       # 生命线工程完好率 (%)
        "G04": (60, 95),       # 空气优良天数 (%)
        "G05": (50, 95),       # 垃圾分类覆盖率 (%)
        "G06": (70, 95),       # 热线解决率 (%)
        "G07": (75, 95),       # 群众满意度 (%)
        "G08": (35, 55),       # 建成区绿化率 (%)
        "G09": (0.1, 1.5),     # 安全事故死亡率 (人/万人)

        # 生态环境指标
        "EV01": (60, 95),      # 空气优良天数比例 (%)
        "EV02": (1, 8),        # 单位GDP污染物排放强度 (kg/万元), 负向
        "EV03": (85, 100),     # 垃圾无害化处理率 (%)
        "EV04": (80, 100),     # 污水收集处理率 (%)
        "EV05": (35, 55),      # 建成区绿化覆盖率 (%)
        "EV06": (2, 8),        # 单位GDP能耗降低率 (%)
        "EV07": (50, 90),      # 地表水Ⅲ类水体比例 (%)
        "EV08": (3, 10),       # 万元GDP用水量下降率 (%)
    }

    min_val, max_val = ranges.get(code, (30, 90))
    value = random.uniform(min_val, max_val)

    # 负向指标随机加减一些波动
    if polarity == -1 and random.random() > 0.7:
        value = value * random.uniform(1.1, 1.3)

    return round(value, 2)


def generate_standard_scores(db: Session):
    """生成标准化得分"""
    # 获取所有原始数据
    raw_data_list = db.query(RawData).all()

    # 按指标分组计算min/max
    from collections import defaultdict
    indicator_values = defaultdict(list)

    for rd in raw_data_list:
        indicator_values[rd.indicator_code].append(rd.raw_value)

    # 计算每个指标的极值
    indicator_bounds = {}
    for code, values in indicator_values.items():
        indicator_bounds[code] = {
            "min": min(values),
            "max": max(values)
        }

    # 为每个原始数据计算标准化得分
    for rd in raw_data_list:
        # 检查是否已有得分
        existing = db.query(StandardScore).filter(
            StandardScore.region_code == rd.region_code,
            StandardScore.indicator_code == rd.indicator_code,
            StandardScore.report_year == rd.report_year
        ).first()

        if existing:
            continue

        bounds = indicator_bounds.get(rd.indicator_code, {"min": 0, "max": 100})
        min_val, max_val = bounds["min"], bounds["max"]

        # 获取指标极性
        indicator = db.query(Indicator).filter(
            Indicator.indicator_code == rd.indicator_code
        ).first()

        if not indicator:
            continue

        # Min-Max标准化
        if max_val > min_val:
            if indicator.polarity == 1:  # 正向
                standard_score = ((rd.raw_value - min_val) / (max_val - min_val)) * 100
            else:  # 负向
                standard_score = ((max_val - rd.raw_value) / (max_val - min_val)) * 100
        else:
            standard_score = 50  # 默认中间值

        standard_score = max(0, min(100, standard_score))  # 限制在0-100

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

    db.commit()
    print("成功生成标准化得分")


if __name__ == "__main__":
    init_indicators()
    generate_test_data()
