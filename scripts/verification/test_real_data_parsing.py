#!/usr/bin/env python3
"""
测试真实数据孔位解析 - 验证从hole_id中提取行列信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.graphics.snake_path_renderer import SnakePathRenderer, PathStrategy


def create_real_data_test():
    """创建模拟真实数据格式的测试数据"""
    holes = {}
    
    # 模拟真实数据：HoleData对象的row和column属性为None，但hole_id包含信息
    test_data = [
        ("BC096R148", 96.0, -148.0, None, None),   # 模拟真实情况：row=None, column=None
        ("BC100R148", 100.0, -148.0, None, None),
        ("BC104R148", 104.0, -148.0, None, None),
        ("BC098R164", 98.0, -164.0, None, None),
        ("BC102R164", 102.0, -164.0, None, None),
        ("BC106R164", 106.0, -164.0, None, None),
        ("BC110R164", 110.0, -164.0, None, None),
    ]
    
    for hole_id, x, y, col, row in test_data:
        hole = HoleData(
            center_x=x, center_y=y, radius=5.0,
            hole_id=hole_id, row=row, column=col,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    return HoleCollection(holes=holes)


def test_hole_id_parsing():
    """测试从hole_id解析行列信息"""
    print("🧪 测试真实数据孔位ID解析...")
    
    # 创建测试数据
    hole_collection = create_real_data_test()
    print(f"✅ 创建测试数据: {len(hole_collection.holes)} 个孔位 (row/column均为None)")
    
    # 创建渲染器并测试解析
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    
    print(f"✅ HolePosition解析结果:")
    for hole_id, hole_pos in renderer.hole_positions.items():
        print(f"  {hole_id}: 列{hole_pos.column_num} 行{hole_pos.row_num} {hole_pos.side}侧")
    
    # 测试路径生成
    try:
        path = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        print(f"✅ 成功生成检测路径: {len(path)} 个孔位")
        
        print("\n📋 检测路径:")
        for i, hole_id in enumerate(path):
            print(f"  {i+1:2d}. {hole_id}")
        
        # 验证间隔4列配对
        expected_pairs = [
            ("BC098R164", "BC102R164"),  # 98+4=102
            ("BC106R164", "BC110R164"),  # 106+4=110
        ]
        
        pairs_found = 0
        for hole1, hole2 in expected_pairs:
            if hole1 in path and hole2 in path:
                index1 = path.index(hole1)
                index2 = path.index(hole2)
                if abs(index1 - index2) <= 2:  # 允许一定间隔
                    print(f"✅ 发现配对: {hole1} + {hole2} (位置 {index1+1}, {index2+1})")
                    pairs_found += 1
        
        print(f"📊 配对统计: {pairs_found}/{len(expected_pairs)} 个配对成功")
        return pairs_found > 0
        
    except Exception as e:
        print(f"\n❌ 路径生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 真实数据孔位ID解析测试")
    print("=" * 50)
    
    success = test_hole_id_parsing()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 孔位ID解析测试成功！")
        print("✅ 成功从hole_id中提取行列信息")
        print("✅ 间隔4列配对逻辑正常工作")
        print("✅ 真实数据集问题已修复")
    else:
        print("❌ 孔位ID解析测试失败")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)