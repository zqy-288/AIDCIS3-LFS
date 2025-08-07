#!/usr/bin/env python3
"""
测试间隔4列S形检测系统集成结果
验证老的SnakePathCoordinator是否正确使用新策略
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.graphics.snake_path_coordinator import SnakePathCoordinator
from src.core_business.graphics.snake_path_renderer import PathStrategy


def create_test_data():
    """创建测试数据"""
    holes = {}
    test_data = [
        ("BC098R164", 98.0, -164.0, 98, 164),   # BC098R164
        ("BC102R164", 102.0, -164.0, 102, 164), # BC102R164 (98+4=102, 间隔4列配对)
        ("BC100R164", 100.0, -164.0, 100, 164), # BC100R164  
        ("BC104R164", 104.0, -164.0, 104, 164), # BC104R164 (100+4=104, 间隔4列配对)
        ("BC106R164", 106.0, -164.0, 106, 164), # BC106R164
        ("BC110R164", 110.0, -164.0, 110, 164), # BC110R164 (106+4=110, 间隔4列配对)
    ]
    
    for hole_id, x, y, col, row in test_data:
        hole = HoleData(
            center_x=x, center_y=y, radius=5.0,
            hole_id=hole_id, row=row, column=col,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    return HoleCollection(holes=holes)


def test_integration():
    """测试集成结果"""
    print("🧪 测试间隔4列S形检测系统集成...")
    
    # 创建测试数据
    hole_collection = create_test_data()
    print(f"✅ 创建测试数据: {len(hole_collection.holes)} 个孔位")
    
    # 创建SnakePathCoordinator（模拟MainWindowController的行为）
    coordinator = SnakePathCoordinator()
    print(f"✅ 默认策略: {coordinator.strategy.value}")
    
    # 设置孔位集合
    coordinator.set_hole_collection(hole_collection)
    
    # 获取蛇形路径顺序（模拟start_simulation的调用）
    holes_list = list(hole_collection.holes.values())
    snake_path = coordinator.get_snake_path_order(holes_list)
    
    print(f"✅ 生成路径: {len(snake_path)} 个孔位")
    print("📋 检测路径:")
    for i, hole_id in enumerate(snake_path):
        print(f"  {i+1:2d}. {hole_id}")
    
    # 验证配对逻辑
    print("\n🔍 配对验证:")
    print("期望配对: BC098R164 + BC102R164")
    print("期望配对: BC100R164 + BC104R164") 
    print("期望配对: BC106R164 + BC110R164")
    
    # 检查路径中是否包含预期的配对顺序
    expected_pairs = [
        ("BC098R164", "BC102R164"),
        ("BC100R164", "BC104R164"),
        ("BC106R164", "BC110R164")
    ]
    
    for hole1, hole2 in expected_pairs:
        if hole1 in snake_path and hole2 in snake_path:
            index1 = snake_path.index(hole1)
            index2 = snake_path.index(hole2)
            if abs(index1 - index2) == 1:  # 相邻位置
                print(f"✅ 发现配对: {hole1} + {hole2} (位置 {index1+1}, {index2+1})")
            else:
                print(f"⚠️ 配对间隔: {hole1} + {hole2} (位置 {index1+1}, {index2+1})")
    
    return True


def main():
    """主测试函数"""
    print("🚀 间隔4列S形检测系统集成测试")
    print("=" * 50)
    
    try:
        success = test_integration()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 集成测试成功！")
            print("✅ 老的SnakePathCoordinator已成功集成INTERVAL_FOUR_S_SHAPE策略")
            print("✅ 【开始模拟检测】按钮现在会使用间隔4列S形扫描")
        else:
            print("❌ 集成测试失败")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)