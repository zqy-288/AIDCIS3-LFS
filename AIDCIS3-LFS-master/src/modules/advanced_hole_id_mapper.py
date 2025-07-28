"""
高级孔位编号映射器
将DXF标准编号系统映射为用户定义的编号系统
支持函数映射和神经网络映射两种方案

映射规则：
- C007R001 → C001R001 (中心点)  
- C008R001 → C001R003 (右边点)
- 左边孔位 → A标签，右边孔位 → B标签
"""

import numpy as np
import json
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import math

try:
    # 尝试导入TensorFlow用于MLP神经网络
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    tf = None


@dataclass
class HoleMappingRule:
    """孔位映射规则"""
    original_id: str
    target_id: str
    label: str  # A或B标签
    x_coord: float
    y_coord: float
    distance_from_center: float


class AdvancedHoleIdMapper:
    """高级孔位编号映射器"""
    
    def __init__(self, mapping_mode: str = "function"):
        """
        初始化映射器
        
        Args:
            mapping_mode: 映射模式，"function" 或 "neural_network"
        """
        self.mapping_mode = mapping_mode
        self.center_x = 0.0  # DXF中心点X坐标
        self.center_y = 0.0  # DXF中心点Y坐标
        self.mapping_rules: List[HoleMappingRule] = []
        self.mlp_model = None
        
        # 基础映射参数（从分析得出）
        self.center_column = 7  # C007为中心列
        self.column_spacing = 43.11  # 列间距(mm)
        self.row_spacing = 12.45   # 行间距(mm)
        
    def load_training_data(self, json_file_path: str):
        """
        从DXF数据文件加载训练数据
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        holes_data = data.get('holes', [])
        self.mapping_rules.clear()
        
        for hole in holes_data:
            original_id = hole['hole_id']
            x_coord = hole['coordinates']['x_mm']
            y_coord = hole['coordinates']['y_mm']
            
            # 计算到中心的距离
            distance = math.sqrt(x_coord**2 + y_coord**2)
            
            # 应用映射规则生成目标编号和标签
            target_id, label = self._apply_mapping_rules(original_id, x_coord, y_coord)
            
            rule = HoleMappingRule(
                original_id=original_id,
                target_id=target_id,
                label=label,
                x_coord=x_coord,
                y_coord=y_coord,
                distance_from_center=distance
            )
            self.mapping_rules.append(rule)
            
        print(f"✅ 已加载 {len(self.mapping_rules)} 个孔位的映射数据")
    
    def _apply_mapping_rules(self, original_id: str, x_coord: float, y_coord: float) -> Tuple[str, str]:
        """
        应用映射规则生成目标编号
        
        基于分析的规律：
        - C007R001 → C001R001 (中心点)
        - C008R001 → C001R003 (右边点)
        """
        # 解析原始编号
        col_str = original_id[1:4]  # 提取C后面的数字
        row_str = original_id[5:8]  # 提取R后面的数字
        col_num = int(col_str)
        row_num = int(row_str)
        
        # 目标列号（统一为C001）
        target_col = "C001"
        
        # 目标行号计算
        target_row_num = self._calculate_target_row(col_num, row_num, x_coord, y_coord)
        target_row = f"R{target_row_num:03d}"
        
        # A/B标签分配 - 使用优化的分界线使A/B标签更平衡
        # 通过分析发现，x < 0.1 的分界线能最大化标签平衡性
        label = "A" if x_coord < 0.1 else "B"
        
        target_id = f"{target_col}{target_row}"
        return target_id, label
    
    def _calculate_target_row(self, col_num: int, row_num: int, x_coord: float, y_coord: float) -> int:
        """
        计算目标行号
        
        基于观察到的规律：
        - C007R001 → R001 (中心列保持行号)
        - C008R001 → R003 (右边列行号变为奇数，跳跃)
        """
        if col_num == self.center_column:  # 中心列 C007
            return row_num
        elif col_num == self.center_column + 1:  # 右边第一列 C008
            # 映射为奇数行，间隔为2
            return row_num * 2 + 1
        elif col_num == self.center_column - 1:  # 左边第一列 C006  
            # 映射为偶数行
            return row_num * 2
        else:
            # 其他列的映射规律 - 基于距离中心的偏移
            distance_from_center = abs(col_num - self.center_column)
            
            if col_num > self.center_column:  # 右边列
                # 右边列映射为更大的奇数行号
                return row_num * 2 + distance_from_center * 2 - 1
            else:  # 左边列
                # 左边列映射为更大的偶数行号
                return row_num * 2 + distance_from_center * 2
    
    def build_neural_network(self, hidden_layers: List[int] = [64, 32, 16]):
        """
        构建MLP神经网络进行映射
        """
        if not HAS_TENSORFLOW:
            raise ImportError("需要安装TensorFlow来使用神经网络映射: pip install tensorflow")
            
        if not self.mapping_rules:
            raise ValueError("需要先加载训练数据，调用 load_training_data()")
        
        # 准备训练数据
        X_train, y_train_row, y_train_label = self._prepare_neural_network_data()
        
        # 构建模型
        input_dim = X_train.shape[1]
        
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(hidden_layers[0], activation='relu', input_shape=(input_dim,)))
        
        for hidden_size in hidden_layers[1:]:
            model.add(tf.keras.layers.Dense(hidden_size, activation='relu'))
            model.add(tf.keras.layers.Dropout(0.2))  # 添加Dropout防止过拟合
        
        # 输出层 - 预测行号和标签
        model.add(tf.keras.layers.Dense(2, activation='linear'))  # [行号, 标签(0或1)]
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # 训练模型
        y_combined = np.column_stack([y_train_row, y_train_label])
        history = model.fit(X_train, y_combined, 
                           epochs=200, batch_size=64, 
                           validation_split=0.2,
                           verbose=1)
        
        self.mlp_model = model
        print(f"✅ 神经网络模型已构建并训练完成，使用 {len(self.mapping_rules)} 个样本")
        return history
    
    def _prepare_neural_network_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        准备神经网络训练数据
        """
        features = []
        target_rows = []
        target_labels = []
        
        for rule in self.mapping_rules:
            # 解析原始编号
            original_col = int(rule.original_id[1:4])
            original_row = int(rule.original_id[5:8])
            
            # 特征: [原始列号, 原始行号, X坐标, Y坐标, 距离中心距离, 角度]
            angle = math.atan2(rule.y_coord, rule.x_coord)  # 添加角度特征
            feature = [
                original_col,
                original_row, 
                rule.x_coord / 1000.0,  # 标准化坐标
                rule.y_coord / 1000.0,
                rule.distance_from_center / 1000.0,  # 标准化距离
                angle
            ]
            features.append(feature)
            
            # 目标行号
            target_row = int(rule.target_id[5:8])
            target_rows.append(target_row)
            
            # 目标标签 (A=0, B=1)
            label_numeric = 0 if rule.label == 'A' else 1
            target_labels.append(label_numeric)
        
        return np.array(features), np.array(target_rows), np.array(target_labels)
    
    def map_hole_id(self, original_id: str, x_coord: float, y_coord: float) -> Tuple[str, str]:
        """
        映射孔位编号
        
        Args:
            original_id: 原始编号 (如 "C007R001")
            x_coord: X坐标
            y_coord: Y坐标
            
        Returns:
            (target_id, label): 目标编号和A/B标签
        """
        if self.mapping_mode == "function":
            return self._apply_mapping_rules(original_id, x_coord, y_coord)
        elif self.mapping_mode == "neural_network":
            return self._neural_network_mapping(original_id, x_coord, y_coord)
        else:
            raise ValueError(f"不支持的映射模式: {self.mapping_mode}")
    
    def _neural_network_mapping(self, original_id: str, x_coord: float, y_coord: float) -> Tuple[str, str]:
        """
        使用神经网络进行映射
        """
        if self.mlp_model is None:
            raise ValueError("神经网络模型未初始化，请先调用 build_neural_network()")
        
        # 解析原始编号
        original_col = int(original_id[1:4])
        original_row = int(original_id[5:8])
        distance = math.sqrt(x_coord**2 + y_coord**2)
        angle = math.atan2(y_coord, x_coord)
        
        # 准备输入特征（与训练时保持一致的标准化）
        features = np.array([[
            original_col, 
            original_row, 
            x_coord / 1000.0, 
            y_coord / 1000.0, 
            distance / 1000.0,
            angle
        ]])
        
        # 预测
        predictions = self.mlp_model.predict(features, verbose=0)
        predicted_row = max(1, int(round(predictions[0][0])))  # 确保行号至少为1
        predicted_label_num = int(round(predictions[0][1]))
        
        # 构建结果
        target_id = f"C001R{predicted_row:03d}"
        label = "A" if predicted_label_num == 0 else "B"
        
        return target_id, label
    
    def evaluate_mapping_accuracy(self, test_cases: List[Tuple[str, float, float, str, str]]) -> Dict:
        """
        评估映射准确性
        
        Args:
            test_cases: 测试用例列表 [(original_id, x, y, expected_target, expected_label), ...]
            
        Returns:
            Dict: 准确性统计
        """
        if not test_cases:
            return {}
            
        correct_id = 0
        correct_label = 0
        total = len(test_cases)
        
        for original_id, x, y, expected_target, expected_label in test_cases:
            predicted_target, predicted_label = self.map_hole_id(original_id, x, y)
            
            if predicted_target == expected_target:
                correct_id += 1
            if predicted_label == expected_label:
                correct_label += 1
        
        return {
            "total_cases": total,
            "id_accuracy": correct_id / total,
            "label_accuracy": correct_label / total,
            "overall_accuracy": (correct_id + correct_label) / (total * 2)
        }
    
    def get_mapping_statistics(self) -> Dict:
        """
        获取映射统计信息
        """
        if not self.mapping_rules:
            return {}
            
        a_labels = sum(1 for rule in self.mapping_rules if rule.label == 'A')
        b_labels = sum(1 for rule in self.mapping_rules if rule.label == 'B')
        
        target_rows = [int(rule.target_id[5:8]) for rule in self.mapping_rules]
        
        # 分析原始编号分布
        original_cols = [int(rule.original_id[1:4]) for rule in self.mapping_rules]
        original_rows = [int(rule.original_id[5:8]) for rule in self.mapping_rules]
        
        return {
            "total_holes": len(self.mapping_rules),
            "a_labels": a_labels,
            "b_labels": b_labels,
            "min_target_row": min(target_rows) if target_rows else 0,
            "max_target_row": max(target_rows) if target_rows else 0,
            "original_col_range": (min(original_cols), max(original_cols)) if original_cols else (0, 0),
            "original_row_range": (min(original_rows), max(original_rows)) if original_rows else (0, 0),
            "mapping_mode": self.mapping_mode
        }
    
    def export_mapping_table(self, output_file: str):
        """
        导出映射表到JSON文件
        """
        mapping_data = {
            "mapping_mode": self.mapping_mode,
            "center_reference": {
                "center_column": self.center_column,
                "column_spacing_mm": self.column_spacing,
                "row_spacing_mm": self.row_spacing
            },
            "statistics": self.get_mapping_statistics(),
            "mappings": [
                {
                    "original_id": rule.original_id,
                    "target_id": rule.target_id,
                    "label": rule.label,
                    "coordinates": {
                        "x_mm": rule.x_coord,
                        "y_mm": rule.y_coord
                    },
                    "distance_from_center": rule.distance_from_center
                }
                for rule in self.mapping_rules
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 映射表已导出到: {output_file}")
    
    def test_key_mappings(self):
        """
        测试关键映射案例
        """
        key_test_cases = [
            # (original_id, x_coord, y_coord, description)
            ("C007R001", 0.0, 2111.25, "中心顶点"),
            ("C008R001", 43.11, 2111.25, "右边第一个点"),  
            ("C006R001", -43.11, 2111.25, "左边第一个点"),
            ("C007R002", 0.0, 2098.8, "中心第二行"),
            ("C008R002", 43.11, 2098.8, "右边第二行")
        ]
        
        print("🧪 关键映射测试:")
        for original_id, x, y, desc in key_test_cases:
            target_id, label = self.map_hole_id(original_id, x, y)
            print(f"  {original_id} → {target_id} (标签: {label}) - {desc}")
        
        return key_test_cases


# 使用示例和测试函数
if __name__ == "__main__":
    print("🚀 高级孔位编号映射器测试\n")
    
    # 函数映射示例
    print("=" * 50)
    print("📊 函数映射测试")
    print("=" * 50)
    
    mapper_func = AdvancedHoleIdMapper(mapping_mode="function")
    mapper_func.test_key_mappings()
    
    # 如果有实际数据文件，加载并测试
    json_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid.json"
    try:
        print(f"\n📁 加载训练数据: {json_file}")
        mapper_func.load_training_data(json_file)
        
        stats = mapper_func.get_mapping_statistics()
        print(f"📈 映射统计: {stats}")
        
        # 导出映射表
        mapper_func.export_mapping_table("hole_mapping_table.json")
        
    except FileNotFoundError:
        print("⚠️ 数据文件未找到，跳过数据加载测试")
    
    # 神经网络映射示例
    if HAS_TENSORFLOW:
        print("\n" + "=" * 50)
        print("🧠 神经网络映射测试")
        print("=" * 50)
        
        mapper_nn = AdvancedHoleIdMapper(mapping_mode="neural_network")
        
        try:
            mapper_nn.load_training_data(json_file)
            print("🏋️ 训练神经网络模型...")
            history = mapper_nn.build_neural_network([128, 64, 32])
            
            print("\n🧪 神经网络映射测试:")
            mapper_nn.test_key_mappings()
            
        except FileNotFoundError:
            print("⚠️ 数据文件未找到，跳过神经网络测试")
        except Exception as e:
            print(f"❌ 神经网络测试失败: {e}")
    else:
        print("\n⚠️ 未安装TensorFlow，跳过神经网络映射测试")
        print("💡 安装命令: pip install tensorflow")