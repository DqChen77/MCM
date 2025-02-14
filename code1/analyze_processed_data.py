import pandas as pd
import numpy as np

def analyze_data():
    # 读取处理后的数据
    df = pd.read_csv('processed_mdot_data.csv')
    
    # 基本统计信息
    print("=== 数据基本统计 ===")
    print(f"总路段数: {len(df)}")
    print(f"总车道数: {df['Number of Lanes'].sum()}")
    
    # 流量和容量统计
    print("\n=== 流量和容量统计 ===")
    stats = df[['Daily_Volume', 'Peak_Hour_Volume', 'Hourly_Capacity', 'VC_Ratio']].describe()
    print(stats)
    
    # 道路分布
    print("\n=== 道路分布 ===")
    print("\n车道数分布:")
    print(df['Number of Lanes'].value_counts().sort_index())
    
    # 拥堵等级分布
    print("\n拥堵等级分布:")
    print(df['Congestion_Level'].value_counts())
    
    # 主要道路的拥堵情况
    print("\n=== 主要道路的拥堵情况 ===")
    road_stats = df.groupby('Road Name').agg({
        'VC_Ratio': ['mean', 'max', 'count'],
        'Daily_Volume': 'mean',
        'Peak_Hour_Volume': 'mean',
        'Hourly_Capacity': 'mean'
    }).round(2)
    
    # 重命名列
    road_stats.columns = ['平均V/C比', '最大V/C比', '路段数', '日均流量', '高峰小时流量', '小时容量']
    
    # 按日均流量排序
    road_stats = road_stats.sort_values('日均流量', ascending=False)
    
    print("\n交通量最大的10条道路:")
    print(road_stats.head(10))
    
    # 输出到CSV文件
    road_stats.to_csv('road_statistics.csv')
    print("\n详细统计已保存到 road_statistics.csv")

if __name__ == "__main__":
    analyze_data() 