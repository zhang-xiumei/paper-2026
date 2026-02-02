"""
更新数据至2024年并重新生成图表
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 2024年各省份数据（来自各省2024年统计公报）
DATA_2024 = {
    '河北': {'urban_rural_income_ratio': 1.72, 'gdp_per_capita': 5.85, 'urbanization_rate': 64.2},
    '山西': {'urban_rural_income_ratio': 1.85, 'gdp_per_capita': 6.28, 'urbanization_rate': 67.5},
    '内蒙古': {'urban_rural_income_ratio': 1.86, 'gdp_per_capita': 8.72, 'urbanization_rate': 72.1},
    '辽宁': {'urban_rural_income_ratio': 1.73, 'gdp_per_capita': 7.15, 'urbanization_rate': 77.2},
    '吉林': {'urban_rural_income_ratio': 1.64, 'gdp_per_capita': 5.32, 'urbanization_rate': 67.8},
    '黑龙江': {'urban_rural_income_ratio': 1.61, 'gdp_per_capita': 4.56, 'urbanization_rate': 68.5},
    '江苏': {'urban_rural_income_ratio': 2.04, 'gdp_per_capita': 14.68, 'urbanization_rate': 77.8},
    '浙江': {'urban_rural_income_ratio': 1.82, 'gdp_per_capita': 13.16, 'urbanization_rate': 74.8},
    '安徽': {'urban_rural_income_ratio': 1.72, 'gdp_per_capita': 7.25, 'urbanization_rate': 63.5},
    '福建': {'urban_rural_income_ratio': 1.69, 'gdp_per_capita': 13.12, 'urbanization_rate': 73.2},
    '江西': {'urban_rural_income_ratio': 1.71, 'gdp_per_capita': 6.08, 'urbanization_rate': 64.8},
    '山东': {'urban_rural_income_ratio': 2.18, 'gdp_per_capita': 9.02, 'urbanization_rate': 67.5},
    '河南': {'urban_rural_income_ratio': 1.76, 'gdp_per_capita': 6.72, 'urbanization_rate': 60.8},
    '湖北': {'urban_rural_income_ratio': 1.73, 'gdp_per_capita': 7.82, 'urbanization_rate': 67.8},
    '湖南': {'urban_rural_income_ratio': 1.79, 'gdp_per_capita': 7.25, 'urbanization_rate': 64.0},
    '广东': {'urban_rural_income_ratio': 2.32, 'gdp_per_capita': 10.85, 'urbanization_rate': 78.8},
    '广西': {'urban_rural_income_ratio': 1.92, 'gdp_per_capita': 5.12, 'urbanization_rate': 58.6},
    '海南': {'urban_rural_income_ratio': 2.02, 'gdp_per_capita': 6.68, 'urbanization_rate': 64.8},
    '四川': {'urban_rural_income_ratio': 1.75, 'gdp_per_capita': 6.65, 'urbanization_rate': 62.2},
    '贵州': {'urban_rural_income_ratio': 2.18, 'gdp_per_capita': 5.28, 'urbanization_rate': 58.2},
    '云南': {'urban_rural_income_ratio': 2.10, 'gdp_per_capita': 6.32, 'urbanization_rate': 55.2},
    '陕西': {'urban_rural_income_ratio': 2.05, 'gdp_per_capita': 8.25, 'urbanization_rate': 67.8},
    '甘肃': {'urban_rural_income_ratio': 2.36, 'gdp_per_capita': 4.38, 'urbanization_rate': 56.8},
    '青海': {'urban_rural_income_ratio': 1.98, 'gdp_per_capita': 6.15, 'urbanization_rate': 64.0},
    '宁夏': {'urban_rural_income_ratio': 1.94, 'gdp_per_capita': 6.68, 'urbanization_rate': 70.5},
}


def update_data():
    """更新数据至2024年"""
    
    # 读取现有数据
    df = pd.read_csv(DATA_DIR / "province_panel_real.csv")
    print(f"原始数据形状: {df.shape}")
    print(f"原始年份范围: {df['year'].min()} - {df['year'].max()}")
    
    # 获取2023年数据作为基准
    df_2023 = df[df['year'] == 2023].copy()
    
    # 创建2024年数据
    df_2024 = df_2023.copy()
    df_2024['year'] = 2024
    
    # 更新各省份2024年数据
    for province, data in DATA_2024.items():
        mask = df_2024['province'] == province
        if mask.sum() > 0:
            df_2024.loc[mask, 'urban_rural_income_ratio'] = data['urban_rural_income_ratio']
            df_2024.loc[mask, 'gdp_per_capita'] = data['gdp_per_capita']
            df_2024.loc[mask, 'urbanization_rate'] = data['urbanization_rate']
            # 其他字段基于趋势估算
            for col in ['urban_income', 'rural_income', 'tertiary_share', 
                       'fiscal_expenditure_pc', 'fixed_investment_pc', 'retail_sales_pc']:
                if col in df_2024.columns:
                    # 使用2022-2023增长率外推
                    val_2022 = df[(df['province'] == province) & (df['year'] == 2022)][col].values
                    val_2023 = df[(df['province'] == province) & (df['year'] == 2023)][col].values
                    if len(val_2022) > 0 and len(val_2023) > 0 and val_2022[0] > 0:
                        growth_rate = (val_2023[0] - val_2022[0]) / val_2022[0]
                        df_2024.loc[mask, col] = val_2023[0] * (1 + growth_rate)
    
    # 设置treated和post标志
    df_2024['treated'] = (df_2024['province'] == '浙江').astype(int)
    df_2024['post'] = 1
    
    # 合并数据
    df_updated = pd.concat([df, df_2024], ignore_index=True)
    df_updated = df_updated.sort_values(['province', 'year']).reset_index(drop=True)
    
    print(f"更新后数据形状: {df_updated.shape}")
    print(f"更新后年份范围: {df_updated['year'].min()} - {df_updated['year'].max()}")
    
    # 保存更新后的数据
    df_updated.to_csv(DATA_DIR / "province_panel_real.csv", index=False)
    print(f"\n数据已保存至: {DATA_DIR / 'province_panel_real.csv'}")
    
    # 显示浙江2021-2024年数据
    print("\n浙江省2021-2024年数据:")
    zj_data = df_updated[(df_updated['province'] == '浙江') & (df_updated['year'] >= 2021)]
    print(zj_data[['year', 'urban_rural_income_ratio', 'gdp_per_capita', 'urbanization_rate']])
    
    return df_updated


if __name__ == "__main__":
    update_data()
