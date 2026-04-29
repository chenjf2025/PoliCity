"""
数据初始化脚本 - 43个指标数据初始化
"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal, engine, Base
from app.models.indicator import Indicator

# 43个指标定义
INDICATORS = [
    # 经济活力与结构优化 (E01-E10)
    {"code": "E01", "dimension": "economic", "dimension_cn": "经济活力", "name": "人均地区生产总值", "weight": 0.10, "polarity": 1, "unit": "万元", "source": "统计局"},
    {"code": "E02", "dimension": "economic", "dimension_cn": "经济活力", "name": "地均GDP产出", "weight": 0.10, "polarity": 1, "unit": "亿元/km²", "source": "统计局"},
    {"code": "E03", "dimension": "economic", "dimension_cn": "经济活力", "name": "第三产业占比", "weight": 0.10, "polarity": 1, "unit": "%", "source": "统计局"},
    {"code": "E04", "dimension": "economic", "dimension_cn": "经济活力", "name": "数字经济核心产业增加值占比", "weight": 0.10, "polarity": 1, "unit": "%", "source": "大数据局"},
    {"code": "E05", "dimension": "economic", "dimension_cn": "经济活力", "name": "R&D经费投入强度", "weight": 0.15, "polarity": 1, "unit": "%", "source": "科技局"},
    {"code": "E06", "dimension": "economic", "dimension_cn": "经济活力", "name": "万人发明专利拥有量", "weight": 0.10, "polarity": 1, "unit": "件/万人", "source": "科技局"},
    {"code": "E07", "dimension": "economic", "dimension_cn": "经济活力", "name": "外资增长率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "商务局"},
    {"code": "E08", "dimension": "economic", "dimension_cn": "经济活力", "name": "社会消费品零售总额增速", "weight": 0.10, "polarity": 1, "unit": "%", "source": "商务局"},
    {"code": "E09", "dimension": "economic", "dimension_cn": "经济活力", "name": "全员劳动生产率", "weight": 0.10, "polarity": 1, "unit": "万元/人", "source": "人社局"},
    {"code": "E10", "dimension": "economic", "dimension_cn": "经济活力", "name": "高新技术企业数量", "weight": 0.15, "polarity": 1, "unit": "家", "source": "科技局"},

    # 文化繁荣与软实力 (C01-C08)
    {"code": "C01", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "人均图书馆藏书量", "weight": 0.15, "polarity": 1, "unit": "册/人", "source": "文旅局"},
    {"code": "C02", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "十万人博物馆数量", "weight": 0.12, "polarity": 1, "unit": "个/10万人", "source": "文旅局"},
    {"code": "C03", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "人均文娱消费支出占比", "weight": 0.13, "polarity": 1, "unit": "%", "source": "统计局"},
    {"code": "C04", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "年人均演出场次", "weight": 0.12, "polarity": 1, "unit": "场次/人", "source": "文旅局"},
    {"code": "C05", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "非遗项目数量", "weight": 0.13, "polarity": 1, "unit": "项", "source": "文旅局"},
    {"code": "C06", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "入境旅游人数占比", "weight": 0.10, "polarity": 1, "unit": "%", "source": "文旅局"},
    {"code": "C07", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "文化产业增加值占比", "weight": 0.15, "polarity": 1, "unit": "%", "source": "文旅局"},
    {"code": "C08", "dimension": "culture", "dimension_cn": "文化繁荣", "name": "人均体育场地面积", "weight": 0.10, "polarity": 1, "unit": "m²/人", "source": "体育局"},

    # 人力资源与人才发展 (H01-H08)
    {"code": "H01", "dimension": "human", "dimension_cn": "人力资源", "name": "平均受教育年限", "weight": 0.15, "polarity": 1, "unit": "年", "source": "教育局"},
    {"code": "H02", "dimension": "human", "dimension_cn": "人力资源", "name": "十万人大专及以上学历人数", "weight": 0.15, "polarity": 1, "unit": "人/10万人", "source": "统计局"},
    {"code": "H03", "dimension": "human", "dimension_cn": "人力资源", "name": "高技能人才占比", "weight": 0.12, "polarity": 1, "unit": "%", "source": "人社局"},
    {"code": "H04", "dimension": "human", "dimension_cn": "人力资源", "name": "年度净流入大学生数", "weight": 0.13, "polarity": 1, "unit": "人", "source": "人社局"},
    {"code": "H05", "dimension": "human", "dimension_cn": "人力资源", "name": "基本养老保险参保率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "人社局"},
    {"code": "H06", "dimension": "human", "dimension_cn": "人力资源", "name": "每千人医师数", "weight": 0.13, "polarity": 1, "unit": "人/千人", "source": "卫健委"},
    {"code": "H07", "dimension": "human", "dimension_cn": "人力资源", "name": "人均预期寿命", "weight": 0.10, "polarity": 1, "unit": "岁", "source": "卫健委"},
    {"code": "H08", "dimension": "human", "dimension_cn": "人力资源", "name": "城镇调查失业率", "weight": 0.10, "polarity": -1, "unit": "%", "source": "统计局"},

    # 城乡融合与均衡发展 (U01-U08)
    {"code": "U01", "dimension": "urban", "dimension_cn": "城乡融合", "name": "县域内就诊率", "weight": 0.15, "polarity": 1, "unit": "%", "source": "卫健委"},
    {"code": "U02", "dimension": "urban", "dimension_cn": "城乡融合", "name": "涉农贷款增速", "weight": 0.12, "polarity": 1, "unit": "%", "source": "金融办"},
    {"code": "U03", "dimension": "urban", "dimension_cn": "城乡融合", "name": "自来水普及率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "住建局"},
    {"code": "U04", "dimension": "urban", "dimension_cn": "城乡融合", "name": "通硬化路率", "weight": 0.13, "polarity": 1, "unit": "%", "source": "交通局"},
    {"code": "U05", "dimension": "urban", "dimension_cn": "城乡融合", "name": "城乡收入比", "weight": 0.16, "polarity": -1, "unit": "比值", "source": "统计局"},
    {"code": "U06", "dimension": "urban", "dimension_cn": "城乡融合", "name": "农村恩格尔系数", "weight": 0.12, "polarity": -1, "unit": "%", "source": "统计局"},
    {"code": "U07", "dimension": "urban", "dimension_cn": "城乡融合", "name": "城乡教育经费差异系数", "weight": 0.10, "polarity": -1, "unit": "系数", "source": "教育局"},
    {"code": "U08", "dimension": "urban", "dimension_cn": "城乡融合", "name": "城镇化率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "统计局"},

    # 城市治理能力与韧性 (G01-G09)
    {"code": "G01", "dimension": "governance", "dimension_cn": "城市治理", "name": "\"一网统管\"覆盖率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "大数据局"},
    {"code": "G02", "dimension": "governance", "dimension_cn": "城市治理", "name": "\"一网通办\"办结率", "weight": 0.12, "polarity": 1, "unit": "%", "source": "行政审批局"},
    {"code": "G03", "dimension": "governance", "dimension_cn": "城市治理", "name": "生命线工程完好率", "weight": 0.11, "polarity": 1, "unit": "%", "source": "应急局"},
    {"code": "G04", "dimension": "governance", "dimension_cn": "城市治理", "name": "空气质量优良天数占比", "weight": 0.12, "polarity": 1, "unit": "%", "source": "生态环境局"},
    {"code": "G05", "dimension": "governance", "dimension_cn": "城市治理", "name": "生活垃圾分类覆盖率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "城管局"},
    {"code": "G06", "dimension": "governance", "dimension_cn": "城市治理", "name": "市民热线问题解决率", "weight": 0.11, "polarity": 1, "unit": "%", "source": "信访局"},
    {"code": "G07", "dimension": "governance", "dimension_cn": "城市治理", "name": "公众安全感指数", "weight": 0.11, "polarity": 1, "unit": "指数", "source": "公安局"},
    {"code": "G08", "dimension": "governance", "dimension_cn": "城市治理", "name": "建成区绿化率", "weight": 0.10, "polarity": 1, "unit": "%", "source": "住建局"},
    {"code": "G09", "dimension": "governance", "dimension_cn": "城市治理", "name": "安全事故死亡率", "weight": 0.11, "polarity": -1, "unit": "人/万人", "source": "应急局"},
]


def init_indicators():
    """初始化43个指标"""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for ind_data in INDICATORS:
            existing = db.query(Indicator).filter(
                Indicator.indicator_code == ind_data["code"]
            ).first()

            if existing:
                print(f"指标 {ind_data['code']} 已存在，跳过")
                continue

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
                version="1.0"
            )
            db.add(indicator)
            print(f"添加指标: {ind_data['code']} - {ind_data['name']}")

        db.commit()
        print(f"\n成功初始化 {len(INDICATORS)} 个指标")

    finally:
        db.close()


if __name__ == "__main__":
    init_indicators()
