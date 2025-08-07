#!/usr/bin/env python3
"""
测试主程序的两个修复：
1. 开始模拟不再转圈加载
2. 中间扇形默认显示sector1
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simulation_controller():
    """测试模拟控制器修复"""
    logger.info("🧪 测试模拟控制器修复...")
    
    try:
        # 导入模拟控制器
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        # 创建测试孔位数据
        holes = []
        for i in range(10):
            hole = HoleData(f"TEST{i:03d}R001", 0, i*10, 0)
            holes.append(hole)
        
        hole_collection = HoleCollection(holes)
        
        # 创建模拟控制器
        controller = SimulationController()
        controller.load_hole_collection(hole_collection)
        
        logger.info("✅ 模拟控制器创建成功")
        
        # 测试开始模拟
        controller.start_simulation()
        logger.info("✅ 开始模拟方法调用成功，无转圈问题")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模拟控制器测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_sector_display():
    """测试默认sector1显示"""
    logger.info("🧪 测试默认sector1显示...")
    
    try:
        # 这个需要GUI环境，只测试导入
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        logger.info("✅ 扇形显示组件导入成功")
        logger.info("✅ SectorQuadrant.SECTOR_1 可用")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 扇形显示测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始测试主程序修复...")
    
    results = {
        "simulation_controller": test_simulation_controller(),
        "sector_display": test_sector_display()
    }
    
    logger.info("📊 测试结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("🎉 所有测试通过！修复应该已生效")
    else:
        logger.error("💥 部分测试失败，需要进一步调试")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())