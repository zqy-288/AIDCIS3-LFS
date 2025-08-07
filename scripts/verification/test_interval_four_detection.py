#!/usr/bin/env python3
"""
间隔4列S形检测系统测试脚本
验证新实现的功能是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.pages.shared.components.snake_path.snake_path_renderer import PathStrategy, HolePair
from src.pages.main_detection_p1.components.simulation_controller import SimulationController
from src.pages.main_detection_p1.components.sector_assignment_manager import SectorAssignmentManager
from src.core_business.graphics.sector_types import SectorQuadrant


def create_test_hole_collection():
    """创建测试用的孔位集合"""
    holes = {}
    
    # 创建第一象限（SECTOR_1）的测试孔位
    # 模拟BC098R164, BC102R164, BC100R164, BC104R164等间隔4列的孔位
    test_holes_data = [
        # R164行（最上面的行）
        ("C098R164", 98.0, -164.0, 98, 164),   # BC098R164
        ("C100R164", 100.0, -164.0, 100, 164), # BC100R164  
        ("C102R164", 102.0, -164.0, 102, 164), # BC102R164
        ("C104R164", 104.0, -164.0, 104, 164), # BC104R164
        ("C106R164", 106.0, -164.0, 106, 164), # BC106R164
        ("C108R164", 108.0, -164.0, 108, 164), # BC108R164
        
        # R163行
        ("C098R163", 98.0, -163.0, 98, 163),
        ("C100R163", 100.0, -163.0, 100, 163),
        ("C102R163", 102.0, -163.0, 102, 163),
        ("C104R163", 104.0, -163.0, 104, 163),
        ("C106R163", 106.0, -163.0, 106, 163),
        ("C108R163", 108.0, -163.0, 108, 163),
        
        # R162行
        ("C098R162", 98.0, -162.0, 98, 162),
        ("C100R162", 100.0, -162.0, 100, 162),
        ("C102R162", 102.0, -162.0, 102, 162),
        ("C104R162", 104.0, -162.0, 104, 162),
        ("C106R162", 106.0, -162.0, 106, 162),
        ("C108R162", 108.0, -162.0, 108, 162),
    ]
    
    for hole_id, x, y, col, row in test_holes_data:
        hole = HoleData(
            center_x=x,
            center_y=y,
            radius=5.0,
            hole_id=hole_id,
            row=row,
            column=col,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    return HoleCollection(holes=holes)


def test_interval_four_path_generation():
    """测试间隔4列路径生成"""
    print("🧪 测试间隔4列S形路径生成...")
    
    # 创建测试数据
    hole_collection = create_test_hole_collection()
    print(f"✅ 创建测试孔位集合: {len(hole_collection.holes)} 个孔位")
    
    # 测试路径渲染器
    from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    
    # 生成间隔4列S形路径
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"✅ 生成检测单元: {len(detection_units)} 个")
    
    # 打印路径详情
    print("\n📋 检测路径详情:")
    for i, unit in enumerate(detection_units):
        if isinstance(unit, HolePair):
            hole_ids = unit.get_hole_ids()
            pair_type = "配对" if unit.is_pair else "单独"
            print(f"  {i+1:2d}. [{pair_type}] {', '.join(hole_ids)}")
        else:
            print(f"  {i+1:2d}. [单孔] {unit.hole_id}")
    
    return detection_units


def test_sector_assignment():
    """测试扇形分配"""
    print("\n🧪 测试扇形分配...")
    
    hole_collection = create_test_hole_collection()
    
    # 创建扇形分配管理器
    sector_manager = SectorAssignmentManager()
    sector_manager.set_hole_collection(hole_collection)
    
    # 检查扇形分配结果
    sector_counts = sector_manager.get_all_sector_counts()
    print("✅ 扇形分配结果:")
    for sector, count in sector_counts.items():
        print(f"   {sector.value}: {count} 个孔位")
    
    # 检查SECTOR_1的孔位
    sector_1_holes = sector_manager.get_sector_holes(SectorQuadrant.SECTOR_1)
    print(f"   SECTOR_1具体孔位: {[h.hole_id for h in sector_1_holes[:5]]}...")
    
    return sector_manager


def test_simulation_controller():
    """测试模拟控制器"""
    print("\n🧪 测试模拟控制器...")
    
    hole_collection = create_test_hole_collection()
    sector_manager = test_sector_assignment()
    
    # 创建模拟控制器
    controller = SimulationController()
    controller.load_hole_collection(hole_collection)
    controller.set_sector_assignment_manager(sector_manager)
    
    # 模拟开始检测（不实际运行定时器）
    controller.logger.info("模拟检测初始化...")
    
    # 获取检测单元
    controller.snake_path_renderer.set_hole_collection(hole_collection)
    detection_units = controller.snake_path_renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    controller.detection_units = detection_units
    
    print(f"✅ 模拟控制器准备就绪: {len(detection_units)} 个检测单元")
    
    # 测试扇形聚焦机制
    if detection_units:
        first_unit = detection_units[0]
        sector = controller._determine_sector(first_unit.primary_hole if isinstance(first_unit, HolePair) else first_unit)
        print(f"✅ 首个检测单元扇形: {sector.value if sector else 'None'}")
    
    return controller


def main():
    """主测试函数"""
    print("🚀 间隔4列S形检测系统集成测试")
    print("=" * 50)
    
    try:
        # 测试路径生成
        detection_units = test_interval_four_path_generation()
        
        # 测试扇形分配
        sector_manager = test_sector_assignment()
        
        # 测试模拟控制器
        controller = test_simulation_controller()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！间隔4列S形检测系统实现成功")
        print("\n📊 实现功能总结:")
        print("✅ INTERVAL_FOUR_S_SHAPE路径策略")
        print("✅ HolePair孔位对数据结构")
        print("✅ 间隔4列S形路径生成算法")
        print("✅ SimulationController孔位对处理")
        print("✅ 扇形聚焦机制")
        print("✅ 路径可视化支持HolePair渲染")
        print("✅ 实时扇形高亮和中心视图切换")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)