import pandas as pd
import numpy as np

def analyze_unmatched():
    # 读取未匹配的数据
    unmatched = pd.read_csv('unmatched_streets.csv')
    
    # 创建详细分析报告
    with open('unmatched_analysis.txt', 'w', encoding='gbk') as f:
        # 1. 总体统计
        f.write("=== 未匹配街道分析报告 ===\n\n")
        f.write(f"总未匹配记录数: {len(unmatched)}\n\n")
        
        # 2. 最常见的未匹配街道名称
        f.write("=== 最常见的未匹配街道名称 (前50个) ===\n\n")
        for name, count in unmatched['Original_MDOT_Name'].value_counts().head(50).items():
            f.write(f"{count:3d} 次: {name}\n")
        
        # 3. 详细样本
        f.write("\n=== 未匹配街道详细信息 (随机30个样本) ===\n\n")
        sample = unmatched.sample(n=min(30, len(unmatched)))
        for _, row in sample.iterrows():
            f.write(f"原始名称: {row['Original_MDOT_Name']}\n")
            f.write(f"标准化名称: {row['Standardized_Name']}\n")
            f.write(f"位置描述: {row['Station_Description']}\n")
            f.write("-" * 80 + "\n")
        
        # 4. 模式分析
        f.write("\n=== 特殊模式分析 ===\n\n")
        
        # 分析包含特定关键词的街道
        keywords = ['RAMP', 'EXPWY', 'COUPLET', 'NO NAME', 'IS', 'MD', 'US']
        for keyword in keywords:
            count = unmatched['Original_MDOT_Name'].str.contains(keyword, na=False).sum()
            f.write(f"包含 '{keyword}' 的街道数量: {count}\n")
            if count > 0:
                f.write("示例:\n")
                examples = unmatched[unmatched['Original_MDOT_Name'].str.contains(keyword, na=False)]['Original_MDOT_Name'].head(3)
                for ex in examples:
                    f.write(f"  - {ex}\n")
                f.write("\n")

if __name__ == "__main__":
    analyze_unmatched() 