#!/usr/bin/env python3
"""
快速测试模拟控制器修复
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simulation_start():
    """测试模拟开始功能"""
    try:
        logger.info("🧪 测试模拟控制器...")
        
        # 导入组件
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData
        
        # 创建测试数据
        holes = [HoleData(f"BC{i:03d}R001", 0, i*10, 0) for i in range(20)]
        hole_collection = HoleCollection(holes)
        
        # 创建控制器
        controller = SimulationController()
        logger.info("✅ 控制器创建成功")
        
        # 加载数据
        controller.load_hole_collection(hole_collection)
        logger.info("✅ 数据加载成功")
        
        # 测试开始模拟
        controller.start_simulation()
        logger.info("✅ 开始模拟调用成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_coordinator():
    """测试协调器修复"""
    try:
        logger.info("🧪 测试协调器...")
        
        from src.pages.main_detection_p1.components.panorama_sector_coordinator import PanoramaSectorCoordinator
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        coordinator = PanoramaSectorCoordinator()
        logger.info("✅ 协调器创建成功")
        
        # 测试select_sector方法
        coordinator.select_sector(SectorQuadrant.SECTOR_1)
        logger.info("✅ select_sector方法调用成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 协调器测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 开始快速测试...")
    
    results = {
        "simulation": test_simulation_start(),
        "coordinator": test_coordinator()
    }
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    if all(results.values()):
        logger.info("🎉 所有测试通过！")
    else:
        logger.error("💥 部分测试失败")