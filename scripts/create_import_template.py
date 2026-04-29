"""
生成数据导入Excel模板
"""
import pandas as pd
import os

# 所有指标编码
INDICATORS = [
    # 经济活力 (E01-E10)
    "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10",
    # 文化繁荣 (C01-C08)
    "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08",
    # 人力资源 (H01-H08)
    "H01", "H02", "H03", "H04", "H05", "H06", "H07", "H08",
    # 城乡融合 (U01-U08)
    "U01", "U02", "U03", "U04", "U05", "U06", "U07", "U08",
    # 城市治理 (G01-G09)
    "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09"
]

# 地区配置
REGIONS = [
    {"code": "default", "name": "测试城市", "level": 0.7},
    {"code": "BJ", "name": "北京市", "level": 1.0},
    {"code": "SH", "name": "上海市", "level": 1.0},
    {"code": "GZ", "name": "广州市", "level": 0.95},
    {"code": "SZ", "name": "深圳市", "level": 0.95},
    {"code": "HZ", "name": "杭州市", "level": 0.85},
    {"code": "NJ", "name": "南京市", "level": 0.85},
    {"code": "WH", "name": "武汉市", "level": 0.80},
    {"code": "CD", "name": "成都市", "level": 0.80},
    {"code": "XA", "name": "西安市", "level": 0.75},
]

# 指标取值范围 (min, max)
INDICATOR_RANGES = {
    "E01": (5.0, 25.0), "E02": (0.5, 5.0), "E03": (40.0, 80.0), "E04": (5.0, 50.0),
    "E05": (1.5, 6.0), "E06": (10.0, 100.0), "E07": (-5.0, 20.0), "E08": (3.0, 15.0),
    "E09": (10.0, 30.0), "E10": (1000, 10000),
    "C01": (1.0, 5.0), "C02": (5.0, 30.0), "C03": (8.0, 20.0), "C04": (0.5, 3.0),
    "C05": (50, 500), "C06": (0.5, 10.0), "C07": (2.0, 15.0), "C08": (2.0, 6.0),
    "H01": (9.0, 14.0), "H02": (10000, 40000), "H03": (15.0, 40.0), "H04": (50000, 500000),
    "H05": (70.0, 99.0), "H06": (2.0, 5.0), "H07": (75.0, 85.0), "H08": (3.0, 6.0),
    "U01": (70.0, 95.0), "U02": (5.0, 25.0), "U03": (85.0, 100.0), "U04": (85.0, 100.0),
    "U05": (1.5, 3.0), "U06": (25.0, 45.0), "U07": (0.1, 0.5), "U08": (50.0, 90.0),
    "G01": (50.0, 100.0), "G02": (80.0, 100.0), "G03": (80.0, 100.0), "G04": (60.0, 95.0),
    "G05": (50.0, 100.0), "G06": (70.0, 95.0), "G07": (80.0, 95.0), "G08": (35.0, 50.0),
    "G09": (0.5, 2.0),
}

import random
random.seed(42)  # 固定随机种子保证可复现

def generate_value(indicator_code, level_factor):
    """根据指标和等级生成数值"""
    min_val, max_val = INDICATOR_RANGES[indicator_code]
    base = (min_val + max_val) / 2
    # 加入随机波动
    value = base * level_factor * random.uniform(0.9, 1.1)
    return round(max(min_val * 0.7, min(max_val * 1.2, value)), 2)

def create_import_template():
    """创建导入模板"""
    data = []

    for region in REGIONS:
        row = {"region_code": region["code"], "region_name": region["name"]}
        for code in INDICATORS:
            row[code] = generate_value(code, region["level"])
        data.append(row)

    df = pd.DataFrame(data)

    # 确保列顺序：region_code, region_name, 然后是指标
    cols = ["region_code", "region_name"] + INDICATORS
    df = df[cols]

    return df

def main():
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "测试数据导入")
    os.makedirs(output_dir, exist_ok=True)

    # 生成2024年数据
    df_2024 = create_import_template()
    output_path_2024 = os.path.join(output_dir, "年度数据导入模板_2024.xlsx")
    df_2024.to_excel(output_path_2024, index=False, sheet_name="2024年数据")
    print(f"已生成: {output_path_2024}")

    # 也生成CSV格式作为备份
    csv_path_2024 = os.path.join(output_dir, "年度数据导入模板_2024.csv")
    df_2024.to_csv(csv_path_2024, index=False, encoding="utf-8-sig")
    print(f"已生成: {csv_path_2024}")

    # 打印数据预览
    print("\n数据预览 (前5行):")
    print(df_2024.head())

    print(f"\n共 {len(df_2024)} 条记录，{len(INDICATORS)} 个指标")

if __name__ == "__main__":
    main()
