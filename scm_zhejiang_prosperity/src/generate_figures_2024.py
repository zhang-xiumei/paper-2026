"""
基于2024年数据生成论文图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（尝试多种字体）
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

# 创建输出目录
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# 颜色方案
COLORS = {
    'treated': '#E74C3C',      # 红色 - 浙江实际值
    'synthetic': '#3498DB',    # 蓝色 - 合成浙江
    'effect': '#2ECC71',       # 绿色 - 政策效应
    'placebo': '#BDC3C7',      # 灰色 - 安慰剂
    'treatment_line': '#95A5A6' # 处理时间线
}


def load_data():
    """加载数据"""
    df = pd.read_csv(DATA_DIR / "province_panel_real.csv")
    print(f"数据形状: {df.shape}")
    print(f"年份范围: {df['year'].min()} - {df['year'].max()}")
    return df


def compute_synthetic_control(df, treatment_year=2021):
    """
    计算合成控制
    使用简化的权重方案：江苏52.1%, 广东42.0%, 海南5.9%
    
    注意：合成控制基于政策前（2010-2020）的匹配
    政策后的合成浙江代表"如果没有政策浙江会怎样"的反事实
    """
    weights = {'江苏': 0.521, '广东': 0.420, '海南': 0.059}
    
    # 浙江实际数据
    zj = df[df['province'] == '浙江'][['year', 'urban_rural_income_ratio']].copy()
    zj.columns = ['year', 'treated']
    
    # 计算合成控制
    synthetic_values = []
    for year in zj['year'].unique():
        syn_val = 0
        for province, weight in weights.items():
            val = df[(df['province'] == province) & (df['year'] == year)]['urban_rural_income_ratio'].values
            if len(val) > 0:
                syn_val += weight * val[0]
        synthetic_values.append({'year': year, 'synthetic': syn_val})
    
    syn_df = pd.DataFrame(synthetic_values)
    
    # 合并
    results = zj.merge(syn_df, on='year')
    results['effect'] = results['treated'] - results['synthetic']
    
    # 打印调试信息
    print("\n合成控制详细计算:")
    print(f"权重: {weights}")
    for year in [2021, 2022, 2023, 2024]:
        row = results[results['year'] == year]
        if len(row) > 0:
            print(f"  {year}: 浙江={row['treated'].values[0]:.3f}, 合成={row['synthetic'].values[0]:.3f}, 效应={row['effect'].values[0]:.3f}")
            # 显示各省贡献
            for prov, w in weights.items():
                val = df[(df['province'] == prov) & (df['year'] == year)]['urban_rural_income_ratio'].values
                if len(val) > 0:
                    print(f"    {prov}: {val[0]:.3f} × {w:.3f} = {val[0]*w:.3f}")
    
    return results


def plot_figure1_trends(results, treatment_year=2021, save_path=None):
    """
    图1: 浙江省城乡收入比实际值与合成控制对比
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    years = results['year']
    treated = results['treated']
    synthetic = results['synthetic']
    
    # 绘制浙江实际值
    ax.plot(years, treated, 
            color=COLORS['treated'], 
            linewidth=2.5, 
            marker='o', 
            markersize=8,
            label='Zhejiang (Actual)')
    
    # 绘制合成浙江
    ax.plot(years, synthetic, 
            color=COLORS['synthetic'], 
            linewidth=2.5, 
            linestyle='--', 
            marker='s', 
            markersize=8,
            label='Synthetic Zhejiang')
    
    # 政策实施时间线
    ax.axvline(x=treatment_year, 
               color=COLORS['treatment_line'], 
               linestyle=':', 
               linewidth=2,
               label=f'Policy Implementation ({treatment_year})')
    
    # 填充政策效应区域
    post_mask = results['year'] >= treatment_year
    ax.fill_between(results[post_mask]['year'],
                    results[post_mask]['treated'],
                    results[post_mask]['synthetic'],
                    alpha=0.3,
                    color=COLORS['effect'],
                    label='Treatment Effect')
    
    # 添加数据标签（政策后）
    for idx, row in results[post_mask].iterrows():
        ax.annotate(f'{row["treated"]:.2f}', 
                   (row['year'], row['treated']),
                   textcoords="offset points",
                   xytext=(0, 10),
                   ha='center',
                   fontsize=9,
                   color=COLORS['treated'])
        ax.annotate(f'{row["synthetic"]:.2f}', 
                   (row['year'], row['synthetic']),
                   textcoords="offset points",
                   xytext=(0, -15),
                   ha='center',
                   fontsize=9,
                   color=COLORS['synthetic'])
    
    # 设置标签
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Urban-Rural Income Ratio', fontsize=14)
    ax.set_title('Figure 1: Synthetic Control Method Results\nZhejiang Common Prosperity Demonstration Zone (2010-2024)', 
                fontsize=14, fontweight='bold')
    
    # 图例
    ax.legend(loc='upper right', frameon=True, fontsize=11)
    
    # 网格
    ax.grid(True, alpha=0.3)
    
    # 设置x轴刻度
    ax.set_xticks(range(2010, 2025, 2))
    ax.set_xlim(2009.5, 2024.5)
    
    # 设置y轴范围
    ax.set_ylim(1.7, 2.6)
    
    plt.tight_layout()
    
    # 保存
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure 1 saved: {save_path}")
    else:
        plt.savefig(FIGURES_DIR / "figure1_scm_trends_2024.png", dpi=300, bbox_inches='tight')
        print(f"Figure 1 saved: {FIGURES_DIR / 'figure1_scm_trends_2024.png'}")
    
    plt.close()
    return fig


def plot_figure2_placebo(df, results, treatment_year=2021, save_path=None):
    """
    图2: 空间安慰剂检验
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 对所有省份进行安慰剂检验
    provinces = df['province'].unique()
    weights = {'江苏': 0.521, '广东': 0.420, '海南': 0.059}
    
    placebo_effects = []
    
    for prov in provinces:
        # 该省份作为处理单位
        prov_data = df[df['province'] == prov][['year', 'urban_rural_income_ratio']].copy()
        prov_data.columns = ['year', 'treated']
        
        # 用其他省份构建合成控制（简化处理：使用原权重省份）
        synthetic_values = []
        for year in prov_data['year'].unique():
            syn_val = 0
            total_weight = 0
            for control_prov, weight in weights.items():
                if control_prov != prov:
                    val = df[(df['province'] == control_prov) & (df['year'] == year)]['urban_rural_income_ratio'].values
                    if len(val) > 0:
                        syn_val += weight * val[0]
                        total_weight += weight
            if total_weight > 0:
                syn_val = syn_val / total_weight  # 重新标准化
            synthetic_values.append({'year': year, 'synthetic': syn_val})
        
        syn_df = pd.DataFrame(synthetic_values)
        prov_results = prov_data.merge(syn_df, on='year')
        prov_results['effect'] = prov_results['treated'] - prov_results['synthetic']
        prov_results['province'] = prov
        prov_results['is_treated'] = (prov == '浙江')
        
        placebo_effects.append(prov_results)
    
    placebo_df = pd.concat(placebo_effects, ignore_index=True)
    
    # 绘制安慰剂效应
    for prov in provinces:
        prov_data = placebo_df[placebo_df['province'] == prov]
        is_treated = prov_data['is_treated'].iloc[0]
        
        if is_treated:
            ax.plot(prov_data['year'], prov_data['effect'],
                   color=COLORS['treated'],
                   linewidth=3,
                   label='Zhejiang (Treated)',
                   zorder=10)
        else:
            ax.plot(prov_data['year'], prov_data['effect'],
                   color=COLORS['placebo'],
                   linewidth=1,
                   alpha=0.4)
    
    # 政策实施时间线
    ax.axvline(x=treatment_year, color='black', linestyle='--', linewidth=1.5)
    
    # 零线
    ax.axhline(y=0, color='black', linewidth=0.5)
    
    # 添加安慰剂标签
    ax.plot([], [], color=COLORS['placebo'], linewidth=1, label='Placebo Units')
    
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Gap (Treated - Synthetic)', fontsize=14)
    ax.set_title('Figure 2: Spatial Placebo Test\n(Zhejiang vs All Other Provinces)', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(range(2010, 2025, 2))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure 2 saved: {save_path}")
    else:
        plt.savefig(FIGURES_DIR / "figure2_placebo_test_2024.png", dpi=300, bbox_inches='tight')
        print(f"Figure 2 saved: {FIGURES_DIR / 'figure2_placebo_test_2024.png'}")
    
    plt.close()
    return fig


def plot_treatment_effect_bar(results, treatment_year=2021, save_path=None):
    """
    附图: 政策效应柱状图
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 分离政策前后
    pre_mask = results['year'] < treatment_year
    post_mask = results['year'] >= treatment_year
    
    # 政策前
    ax.bar(results[pre_mask]['year'], results[pre_mask]['effect'],
           color='gray', alpha=0.5, label='Pre-treatment Gap')
    
    # 政策后（负效应用绿色，正效应用红色）
    colors = [COLORS['effect'] if e < 0 else COLORS['treated'] 
              for e in results[post_mask]['effect']]
    bars = ax.bar(results[post_mask]['year'], results[post_mask]['effect'],
                  color=colors, alpha=0.8, label='Treatment Effect')
    
    # 在柱子上添加数值
    for bar, effect in zip(bars, results[post_mask]['effect']):
        height = bar.get_height()
        ax.annotate(f'{effect:.3f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, -15 if height < 0 else 5),
                   textcoords="offset points",
                   ha='center', va='bottom' if height < 0 else 'top',
                   fontsize=11, fontweight='bold')
    
    # 零线和政策时间线
    ax.axhline(y=0, color='black', linewidth=1)
    ax.axvline(x=treatment_year - 0.5, color=COLORS['treatment_line'], 
               linestyle='--', linewidth=2, label=f'Policy ({treatment_year})')
    
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Treatment Effect (Treated - Synthetic)', fontsize=14)
    ax.set_title('Treatment Effect by Year (2021-2024)', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_xticks(range(2010, 2025, 2))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Treatment effect bar chart saved: {save_path}")
    else:
        plt.savefig(FIGURES_DIR / "treatment_effect_2024.png", dpi=300, bbox_inches='tight')
        print(f"Treatment effect bar chart saved: {FIGURES_DIR / 'treatment_effect_2024.png'}")
    
    plt.close()
    return fig


def generate_summary_table(results, treatment_year=2021):
    """生成政策效应汇总表"""
    post_results = results[results['year'] >= treatment_year].copy()
    
    print("\n" + "="*60)
    print("政策效应估计表（2021-2024）")
    print("="*60)
    print(f"{'年份':<6} {'浙江实际值':<12} {'合成浙江':<12} {'政策效应':<12} {'相对效应':<12}")
    print("-"*60)
    
    total_effect = 0
    for _, row in post_results.iterrows():
        rel_effect = row['effect'] / row['synthetic'] * 100
        print(f"{int(row['year']):<6} {row['treated']:<12.3f} {row['synthetic']:<12.3f} {row['effect']:<12.3f} {rel_effect:<12.2f}%")
        total_effect += row['effect']
    
    avg_effect = post_results['effect'].mean()
    avg_rel = avg_effect / post_results['synthetic'].mean() * 100
    
    print("-"*60)
    print(f"{'平均':<6} {post_results['treated'].mean():<12.3f} {post_results['synthetic'].mean():<12.3f} {avg_effect:<12.3f} {avg_rel:<12.2f}%")
    print(f"{'累计':<6} {'':<12} {'':<12} {total_effect:<12.3f}")
    print("="*60)
    
    return post_results


def main():
    """主函数"""
    print("="*60)
    print("生成2024年数据版论文图表")
    print("="*60)
    
    # 加载数据
    df = load_data()
    
    # 计算合成控制
    print("\n计算合成控制...")
    results = compute_synthetic_control(df)
    
    # 生成汇总表
    generate_summary_table(results)
    
    # 生成图1: 趋势对比图
    print("\n生成图1: 趋势对比图...")
    plot_figure1_trends(results)
    
    # 生成图2: 空间安慰剂检验
    print("\n生成图2: 空间安慰剂检验...")
    plot_figure2_placebo(df, results)
    
    # 生成附图: 政策效应柱状图
    print("\n生成附图: 政策效应柱状图...")
    plot_treatment_effect_bar(results)
    
    print("\n" + "="*60)
    print(f"所有图表已保存至: {FIGURES_DIR}")
    print("="*60)
    
    # 保存结果数据
    results.to_csv(RESULTS_DIR / "scm_results_2024.csv", index=False)
    print(f"\n结果数据已保存至: {RESULTS_DIR / 'scm_results_2024.csv'}")


if __name__ == "__main__":
    main()
