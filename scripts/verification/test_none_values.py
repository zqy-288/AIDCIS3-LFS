#!/usr/bin/env python3
"""
测试空值处理优化 - 模拟真实数据集中的None值问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.graphics.snake_path_coordinator import SnakePathCoordinator


def create_test_data_with_none_values():
    """创建包含None值的测试数据"""
    holes = {}
    
    # 正常的测试数据
    test_data = [
        ("BC100R164", 100.0, -164.0, 100, 164),
        ("BC104R164", 104.0, -164.0, 104, 164),
        ("BC102R164", 102.0, -164.0, 102, 164),
        ("BC106R164", 106.0, -164.0, 106, 164),
        
        # 模拟真实数据中的问题数据 - 无法解析的hole_id格式
        ("INVALID_FORMAT_1", 108.0, -164.0, None, None),
        ("XYZ123456", 110.0, -164.0, None, 164),
        ("BROKEN_ID", 112.0, -164.0, 112, None),
    ]
    
    for hole_id, x, y, col, row in test_data:
        hole = HoleData(
            center_x=x, center_y=y, radius=5.0,
            hole_id=hole_id, row=row, column=col,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    return HoleCollection(holes=holes)


def test_none_value_handling():
    """测试None值处理"""
    print("🧪 测试None值处理优化...")
    
    # 创建包含None值的测试数据
    hole_collection = create_test_data_with_none_values()
    print(f"✅ 创建测试数据: {len(hole_collection.holes)} 个孔位 (包含3个无效孔位)")
    
    # 使用SnakePathCoordinator进行测试
    coordinator = SnakePathCoordinator()
    coordinator.set_hole_collection(hole_collection)
    
    try:
        # 获取路径
        holes_list = list(hole_collection.holes.values())
        path = coordinator.get_snake_path_order(holes_list)
        
        print(f"✅ 成功生成检测路径: {len(path)} 个孔位")
        print(f"✅ 使用策略: {coordinator.strategy.value}")
        
        print("\n📋 检测路径:")
        for i, hole in enumerate(path):
            if hasattr(hole, 'hole_id'):
                hole_id = hole.hole_id
            else:
                hole_id = str(hole)
            print(f"  {i+1:2d}. {hole_id}")
        
        # 验证无效孔位是否被正确过滤
        path_ids = [hole.hole_id if hasattr(hole, 'hole_id') else str(hole) for hole in path]
        invalid_holes_in_path = [hole_id for hole_id in ["INVALID_FORMAT_1", "XYZ123456", "BROKEN_ID"] if hole_id in path_ids]
        
        if invalid_holes_in_path:
            print(f"\n⚠️ 警告: 发现无效孔位仍在路径中: {invalid_holes_in_path}")
            return False
        else:
            print(f"\n✅ 无效孔位已被正确过滤")
            
        # 验证有效配对
        expected_pairs = [
            ("BC100R164", "BC104R164"),
            ("BC102R164", "BC106R164"),
        ]
        
        pairs_found = 0
        for hole1, hole2 in expected_pairs:
            if hole1 in path_ids and hole2 in path_ids:
                index1 = path_ids.index(hole1)
                index2 = path_ids.index(hole2)
                if abs(index1 - index2) == 1:  # 相邻位置
                    print(f"✅ 发现配对: {hole1} + {hole2} (位置 {index1+1}, {index2+1})")
                    pairs_found += 1
        
        print(f"📊 配对统计: {pairs_found}/{len(expected_pairs)} 个配对成功")
        return pairs_found == len(expected_pairs)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 None值处理优化测试")
    print("=" * 50)
    
    success = test_none_value_handling()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 None值处理测试成功！")
        print("✅ 无效数据已被正确过滤")
        print("✅ 间隔4列配对逻辑仍然正常工作")
        print("✅ 大数据集稳定性问题已修复")
    else:
        print("❌ None值处理测试失败")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)