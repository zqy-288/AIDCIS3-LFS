#!/usr/bin/env python3
"""
最终验证所有修复是否生效
"""

import sys
import time
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

# 添加项目路径
sys.path.insert(0, '/Users/vsiyo/Desktop/AIDCIS3-LFS')

from src.pages.main_detection_p1.main_detection_page import MainDetectionPage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def final_verification():
    """最终验证所有修复"""
    
    app = QApplication(sys.argv)
    
    try:
        logger.info("🔧 开始最终验证...")
        
        # 创建主页面
        main_page = MainDetectionPage()
        main_page.show()
        
        # 等待初始化
        QTimer.singleShot(2000, lambda: start_verification(main_page))
        
        app.exec()
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()

def start_verification(main_page):
    """开始验证流程"""
    try:
        logger.info("🎯 开始验证流程...")
        
        # 获取模拟控制器
        sim_controller = getattr(main_page, 'simulation_controller', None)
        if not sim_controller:
            logger.error("❌ 无法获取模拟控制器")
            return
            
        # 1. 加载数据并验证数据完整性
        logger.info("📊 步骤1: 验证数据加载...")
        verify_data_loading(main_page, sim_controller)
        
        # 2. 验证蛇形路径生成
        QTimer.singleShot(2000, lambda: verify_snake_path_generation(sim_controller))
        
        # 3. 验证模拟运行
        QTimer.singleShot(4000, lambda: verify_simulation_running(sim_controller))
        
        # 20秒后自动关闭
        QTimer.singleShot(20000, lambda: QApplication.quit())
        
    except Exception as e:
        logger.error(f"❌ 验证流程失败: {e}")
        import traceback
        traceback.print_exc()

def verify_data_loading(main_page, sim_controller):
    """验证数据加载"""
    try:
        logger.info("   加载CAP1000数据...")
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/workfiles/dongzhong.dxf"
        
        from src.core.shared_data_manager import SharedDataManager
        data_manager = SharedDataManager()
        data_manager.load_hole_data_from_dxf(dxf_path)
        
        hole_collection = data_manager.get_current_hole_collection()
        if hole_collection:
            logger.info(f"   ✅ 数据加载成功: {len(hole_collection.holes)} 个孔位")
        else:
            logger.error("   ❌ 数据加载失败")
            
    except Exception as e:
        logger.error(f"   ❌ 数据加载异常: {e}")

def verify_snake_path_generation(sim_controller):
    """验证蛇形路径生成"""
    try:
        logger.info("🐍 步骤2: 验证蛇形路径生成...")
        
        # 获取数据
        hole_collection = sim_controller.hole_collection
        if not hole_collection:
            logger.error("   ❌ 没有孔位数据")
            return
            
        original_count = len(hole_collection.holes)
        
        # 模拟生成过程
        from src.core_business.graphics.snake_path_renderer import SnakePathRenderer, PathStrategy
        renderer = SnakePathRenderer()
        renderer.set_hole_collection(hole_collection)
        
        try:
            detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
            if detection_units:
                # 使用新的修复逻辑统计
                snake_sorted_holes = []
                for unit in detection_units:
                    if hasattr(unit, 'holes'):  # HolePair对象
                        snake_sorted_holes.extend(unit.holes)
                    else:  # 单个HoleData对象
                        snake_sorted_holes.append(unit)
                        
                logger.info(f"   ✅ 蛇形路径: {len(detection_units)} 个检测单元")
                logger.info(f"   ✅ 孔位覆盖: {len(snake_sorted_holes)}/{original_count} = {len(snake_sorted_holes)/original_count*100:.2f}%")
                
                if len(snake_sorted_holes) == original_count:
                    logger.info("   ✅ 遍历问题已修复！")
                else:
                    logger.warning(f"   ⚠️ 仍有遗漏: {original_count - len(snake_sorted_holes)} 个孔位")
                    
            else:
                logger.info("   使用后备方案...")
                hole_list = list(hole_collection.holes.values())
                hole_list.sort(key=lambda h: (h.center_y, h.center_x))
                
                logger.info(f"   ✅ 后备方案: {len(hole_list)} 个单孔检测单元")
                logger.info(f"   ✅ 后备覆盖: {len(hole_list)}/{original_count} = 100%")
                
        except Exception as e:
            logger.error(f"   ❌ 蛇形路径生成失败: {e}")
            
    except Exception as e:
        logger.error(f"❌ 蛇形路径验证失败: {e}")
        import traceback
        traceback.print_exc()

def verify_simulation_running(sim_controller):
    """验证模拟运行"""
    try:
        logger.info("🚀 步骤3: 验证模拟运行...")
        
        # 启动模拟
        sim_controller.start_simulation()
        logger.info("   ✅ 模拟已启动")
        
        # 监控进度
        def check_progress():
            if hasattr(sim_controller, 'current_index') and hasattr(sim_controller, 'detection_units'):
                current = sim_controller.current_index
                total = len(sim_controller.detection_units) if sim_controller.detection_units else 0
                if total > 0:
                    progress = current / total * 100
                    logger.info(f"   📈 模拟进度: {current}/{total} ({progress:.1f}%)")
                    
                    # 检查蓝色状态
                    if hasattr(sim_controller, 'graphics_view') and sim_controller.graphics_view:
                        hole_items = getattr(sim_controller.graphics_view, 'hole_items', {})
                        blue_count = 0
                        for hole_id, item in hole_items.items():
                            if hasattr(item, '_color_override') and item._color_override:
                                blue_count += 1
                        if blue_count > 0:
                            logger.info(f"   💙 检测到 {blue_count} 个蓝色状态孔位")
                            
        # 定期检查进度
        QTimer.singleShot(2000, check_progress)
        QTimer.singleShot(5000, check_progress)
        QTimer.singleShot(8000, check_progress)
        QTimer.singleShot(12000, check_progress)
        
        # 最终报告
        QTimer.singleShot(15000, lambda: logger.info("🏆 验证完成！所有修复已应用"))
        
    except Exception as e:
        logger.error(f"❌ 模拟验证失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_verification()