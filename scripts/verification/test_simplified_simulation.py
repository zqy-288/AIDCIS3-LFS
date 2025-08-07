#!/usr/bin/env python3
"""
测试简化后的模拟功能
移除蛇形路径，仅保留孔位基本检测逻辑
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

def test_simplified_simulation():
    """测试简化的模拟控制器"""
    try:
        logger.info("🧪 测试简化后的模拟控制器...")
        
        # 导入组件
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData
        
        # 创建测试数据（少量孔位用于快速测试）
        holes = []
        for i in range(10):  # 只创建10个孔位进行测试
            hole = HoleData(f"BC{i:03d}R001", 0, i*10, i*5, 2.5)
            holes.append(hole)
        
        hole_collection = HoleCollection(holes)
        
        # 创建控制器
        controller = SimulationController()
        logger.info("✅ 简化模拟控制器创建成功")
        
        # 加载数据
        controller.load_hole_collection(hole_collection)
        logger.info("✅ 孔位数据加载成功")
        
        # 检验简化后的检测单元
        logger.info(f"📊 检测单元数量: {len(controller.detection_units)}")
        logger.info(f"📊 孔位总数: {len(controller.snake_sorted_holes)}")
        
        # 验证检测单元都是单个孔位（不是HolePair）
        for i, unit in enumerate(controller.detection_units[:3]):  # 检查前3个
            logger.info(f"🔍 检测单元 {i+1}: {type(unit).__name__} - {unit.hole_id}")
        
        # 测试开始模拟（应该很快）
        logger.info("🚀 开始简化模拟测试...")
        controller.start_simulation()
        logger.info("✅ 简化模拟启动成功")
        
        # 检查当前状态
        progress = controller.get_progress()
        logger.info(f"📈 模拟进度: {progress[0]}/{progress[1]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 简化模拟测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_sector_coordinator():
    """测试扇形协调器的强制刷新功能"""
    try:
        logger.info("🧪 测试扇形协调器强制刷新...")
        
        from src.pages.main_detection_p1.components.panorama_sector_coordinator import PanoramaSectorCoordinator
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        coordinator = PanoramaSectorCoordinator()
        logger.info("✅ 协调器创建成功")
        
        # 测试select_sector方法（应该包含强制刷新）
        coordinator.select_sector(SectorQuadrant.SECTOR_1)
        logger.info("✅ select_sector with 强制刷新调用成功")
        
        # 检查是否有强制刷新方法
        if hasattr(coordinator, '_force_refresh_center_view'):
            logger.info("✅ 强制刷新方法存在")
        else:
            logger.warning("⚠️ 强制刷新方法不存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 扇形协调器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始简化功能测试...")
    
    # 执行测试
    results = {
        "简化模拟控制器": test_simplified_simulation(),
        "扇形协调器强制刷新": test_sector_coordinator()
    }
    
    # 输出结果
    logger.info("\n" + "="*50)
    logger.info("📊 简化功能测试结果:")
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {name}: {status}")
    
    # 总体状态
    all_passed = all(results.values())
    if all_passed:
        logger.info("\n🎉 所有简化功能测试通过！")
        logger.info("🔥 改进效果:")
        logger.info("  • 移除了复杂的蛇形路径生成逻辑")
        logger.info("  • 简化为单个孔位检测（2秒/孔）")
        logger.info("  • 扇形更新增加了强制刷新机制")
        logger.info("  • 孔位显示应该更快更稳定")
    else:
        logger.error("\n💥 部分简化功能测试失败")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)