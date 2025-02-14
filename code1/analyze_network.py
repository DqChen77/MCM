import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple
import matplotlib.pyplot as plt
from collections import defaultdict

class NetworkAnalyzer:
    def __init__(self, network_path: str):
        """初始化网络分析器"""
        self.G = nx.read_graphml(network_path)
        print(f"加载网络完成。节点数: {self.G.number_of_nodes()}, 边数: {self.G.number_of_edges()}")
        
    def analyze_centrality(self) -> Dict:
        """分析节点中心性"""
        print("\n计算节点中心性...")
        
        # 计算不同的中心性指标
        degree_centrality = nx.degree_centrality(self.G)
        betweenness_centrality = nx.betweenness_centrality(self.G)
        closeness_centrality = nx.closeness_centrality(self.G)
        
        # 找出最重要的节点
        top_nodes = {
            'degree': sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10],
            'betweenness': sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10],
            'closeness': sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
        print("\n=== 重要节点分析 ===")
        for metric, nodes in top_nodes.items():
            print(f"\n{metric.capitalize()} 中心性最高的节点:")
            for node, value in nodes:
                print(f"节点 {node}: {value:.4f}")
        
        return {
            'degree': degree_centrality,
            'betweenness': betweenness_centrality,
            'closeness': closeness_centrality
        }
    
    def analyze_shortest_paths(self, sample_size: int = 100) -> None:
        """分析最短路径"""
        print("\n=== 最短路径分析 ===")
        
        # 获取最大连通分量
        largest_cc = max(nx.strongly_connected_components(self.G), key=len)
        print(f"最大连通分量大小: {len(largest_cc)}")
        
        # 在最大连通分量中随机选择节点对
        nodes = list(largest_cc)
        if len(nodes) < 2:
            print("连通分量太小，无法进行路径分析")
            return
        
        # 随机选择节点对进行分析
        np.random.seed(42)
        pairs = []
        for _ in range(min(sample_size, len(nodes) * (len(nodes) - 1) // 2)):
            i, j = np.random.choice(len(nodes), 2, replace=False)
            pairs.append((nodes[i], nodes[j]))
        
        # 计算路径统计
        path_lengths = []
        congestion_levels = defaultdict(int)
        
        print("\n计算最短路径...")
        for source, target in pairs:
            try:
                path = nx.shortest_path(self.G, source, target, weight='distance')
                length = sum(float(self.G[path[i]][path[i+1]]['distance']) for i in range(len(path)-1))
                path_lengths.append(length)
                
                # 统计路径上的拥堵等级
                for i in range(len(path)-1):
                    congestion_level = self.G[path[i]][path[i+1]]['congestion_level']
                    congestion_levels[congestion_level] += 1
                
            except nx.NetworkXNoPath:
                continue
        
        if path_lengths:
            print(f"\n路径长度统计:")
            print(f"平均长度: {np.mean(path_lengths):.2f} km")
            print(f"最短长度: {min(path_lengths):.2f} km")
            print(f"最长长度: {max(path_lengths):.2f} km")
            
            print("\n路径拥堵等级分布:")
            total = sum(congestion_levels.values())
            for level, count in sorted(congestion_levels.items()):
                print(f"{level}: {count/total*100:.1f}%")
    
    def analyze_vulnerability(self) -> None:
        """分析网络脆弱性"""
        print("\n=== 网络脆弱性分析 ===")
        
        # 获取最大连通分量
        largest_cc = max(nx.strongly_connected_components(self.G), key=len)
        original_size = len(largest_cc)
        
        # 分析重要边的移除对网络的影响
        print("\n分析关键边的影响...")
        edge_importance = {}
        
        # 获取拥堵等级为"严重拥堵"的边
        congested_edges = [(u, v) for u, v, d in self.G.edges(data=True)
                          if d['congestion_level'] == '严重拥堵']
        
        for edge in congested_edges[:10]:  # 只分析前10条最拥堵的边
            # 临时移除边
            self.G.remove_edge(*edge)
            
            # 计算新的最大连通分量大小
            new_largest_cc = len(max(nx.strongly_connected_components(self.G), key=len))
            
            # 计算影响程度
            impact = (original_size - new_largest_cc) / original_size
            edge_importance[edge] = impact
            
            # 恢复边
            attrs = {'distance': '0', 'congestion_level': '严重拥堵'}  # 添加必要的属性
            self.G.add_edge(*edge, **attrs)
        
        # 输出结果
        print("\n移除边对网络连通性的影响:")
        for edge, impact in sorted(edge_importance.items(), key=lambda x: x[1], reverse=True):
            road_name = self.G[edge[0]][edge[1]]['road_name']
            print(f"道路: {road_name}, 边 {edge}: 影响度 {impact:.4f}")
    
    def save_analysis_results(self, output_path: str) -> None:
        """保存分析结果"""
        # 将结果保存为JSON格式
        results = {
            'network_stats': {
                'nodes': self.G.number_of_nodes(),
                'edges': self.G.number_of_edges()
            }
        }
        
        # 保存结果
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n分析结果已保存到 {output_path}")

def main():
    # 创建分析器实例
    analyzer = NetworkAnalyzer('traffic_network.graphml')
    
    # 运行分析
    analyzer.analyze_centrality()
    analyzer.analyze_shortest_paths()
    analyzer.analyze_vulnerability()
    
    # 保存结果
    analyzer.save_analysis_results('network_analysis_results.json')

if __name__ == "__main__":
    main() 