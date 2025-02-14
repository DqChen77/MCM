import pandas as pd
import networkx as nx
import ast
import json

class NetworkBuilder:
    def __init__(self):
        self.nodes_dict = {}
        self.G = nx.DiGraph()
        
    def parse_node_list(self, node_str):
        """解析节点列表字符串，处理可能的集合和列表形式"""
        try:
            if isinstance(node_str, (int, str)):
                return {node_str}
            # 移除多余的空格和引号
            node_str = node_str.strip().strip('"')
            # 解析节点列表
            node_list = ast.literal_eval(node_str)
            if isinstance(node_list, (set, list)):
                return set(node_list)
            return {node_list}
        except:
            return set()
        
    def load_nodes_data(self, file_path):
        nodes_df = pd.read_csv(file_path)
        nodes = set()
        for _, row in nodes_df.iterrows():
            node_list = self.parse_node_list(row['Nodes'])
            nodes.update(node_list)
        
        # 为每个节点分配随机坐标
        import random
        lat_range = (39.1, 39.4)  # Baltimore 纬度范围
        lon_range = (-76.8, -76.4)  # Baltimore 经度范围
        
        self.nodes_dict = {node: (
            random.uniform(lat_range[0], lat_range[1]),
            random.uniform(lon_range[0], lon_range[1])
        ) for node in nodes}
        
        print(f"Loaded {len(self.nodes_dict)} nodes")
        
    def build_network(self, traffic_data_path, nodes_file_path):
        # 加载节点数据
        self.load_nodes_data(nodes_file_path)
        
        # 加载交通数据
        traffic_df = pd.read_csv(traffic_data_path)
        
        # 创建边
        for _, row in traffic_df.iterrows():
            try:
                start_nodes = self.parse_node_list(row['node start']) if pd.notna(row['node start']) else set()
                end_nodes = self.parse_node_list(row['node(s) end']) if pd.notna(row['node(s) end']) else set()
                
                # 添加所有节点
                for node in start_nodes | end_nodes:
                    if node not in self.G:
                        if node in self.nodes_dict:
                            self.G.add_node(node, pos=self.nodes_dict[node])
                
                # 创建边
                for start in start_nodes:
                    for end in end_nodes:
                        if start in self.nodes_dict and end in self.nodes_dict:
                            # 添加边属性
                            edge_data = {
                                'road_name': row['Road Name'],
                                'station_id': row['Station ID'],
                                'aadt': row['AADT 2022'] if 'AADT 2022' in row else None,
                                'lanes': row['Number of Lanes'] if 'Number of Lanes' in row else None,
                                'description': row['Station Description'] if 'Station Description' in row else None
                            }
                            
                            # 特别标记 Francis Scott Key Bridge
                            if 'Francis Scott Key Bridge' in str(row['Station Description']):
                                edge_data['is_key_bridge'] = True
                            
                            self.G.add_edge(start, end, **edge_data)
            except (ValueError, SyntaxError) as e:
                continue
        
        print(f"Network built with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges")
        
        # 分析网络连通性
        components = list(nx.strongly_connected_components(self.G))
        print(f"Number of strongly connected components: {len(components)}")
        print(f"Largest component size: {len(max(components, key=len))}")
        
        # 分析节点度数
        degrees = [d for n, d in self.G.degree()]
        avg_degree = sum(degrees) / len(degrees)
        print(f"Average degree: {avg_degree:.2f}")
        print(f"Maximum degree: {max(degrees)}")
        print(f"Minimum degree: {min(degrees)}")
        
        # 保存网络
        nx.write_graphml(self.G, "data/processed/traffic_network.graphml")

if __name__ == "__main__":
    builder = NetworkBuilder()
    builder.build_network(
        "data/processed/processed_mdot_data.csv",
        "data/raw/Edge_Names_With_Nodes.csv"
    ) 