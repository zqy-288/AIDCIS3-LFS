#!/usr/bin/env python3
"""
测试重复日志问题是否解决
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

def test_no_duplicate_logs():
    """测试是否还有重复日志"""
    try:
        logger.info("🧪 测试重复日志修复...")
        
        # 导入组件
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData
        
        # 创建少量测试数据
        holes = []
        for i in range(5):  # 只创建5个孔位
            hole = HoleData(f"BC{i:03d}R001", 0, i*10, i*5, 2.5)
            holes.append(hole)
        
        hole_collection = HoleCollection(holes)
        
        # 创建控制器
        logger.info("📝 创建模拟控制器...")
        controller = SimulationController()
        
        # 加载数据 - 这里应该只输出一次日志
        logger.info("📝 加载孔位集合...")
        controller.load_hole_collection(hole_collection)
        
        # 开始模拟 - 这里应该只输出一次蛇形路径相关日志
        logger.info("📝 开始模拟...")
        controller.start_simulation()
        
        logger.info("✅ 测试完成 - 检查上面的日志是否有重复")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 开始重复日志测试...")
    success = test_no_duplicate_logs()
    if success:
        logger.info("🎉 重复日志测试完成！")
    else:
        logger.error("💥 重复日志测试失败")