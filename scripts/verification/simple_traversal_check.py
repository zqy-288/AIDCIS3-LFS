#!/usr/bin/env python3
"""
简化的遍历完整性检查
"""

import sys
import logging

# 添加项目路径
sys.path.insert(0, '/Users/vsiyo/Desktop/AIDCIS3-LFS')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_traversal():
    """检查遍历完整性"""
    
    try:
        from src.core.shared_data_manager import SharedDataManager
        from src.core_business.graphics.snake_path_renderer import SnakePathRenderer, PathStrategy
        
        logger.info("🔍 开始简化的遍历检查...")
        
        # 1. 加载数据
        logger.info("📂 加载CAP1000数据...")
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/workfiles/dongzhong.dxf"
        
        data_manager = SharedDataManager()
        data_manager.load_hole_data_from_dxf(dxf_path)
        
        hole_collection = data_manager.get_current_hole_collection()
        if not hole_collection:
            logger.error("❌ 无法获取孔位集合")
            return
            
        original_count = len(hole_collection.holes)
        logger.info(f"📊 原始数据: {original_count} 个孔位")
        
        # 2. 测试蛇形路径生成
        logger.info("🐍 测试蛇形路径生成...")
        renderer = SnakePathRenderer()
        renderer.set_hole_collection(hole_collection)
        
        try:
            detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
            if detection_units:
                # 计算总孔位数
                total_holes = 0
                for unit in detection_units:
                    if hasattr(unit, 'holes'):
                        total_holes += len(unit.holes)
                    else:
                        total_holes += 1
                
                logger.info(f"✅ 蛇形路径: {len(detection_units)} 个检测单元 -> {total_holes} 个孔位")
                logger.info(f"覆盖率: {total_holes/original_count*100:.2f}%")
                
                if total_holes < original_count:
                    logger.warning(f"⚠️ 遗漏了 {original_count - total_holes} 个孔位")
                    
            else:
                logger.warning("⚠️ 蛇形路径生成失败，使用后备方案")
                
                # 后备方案
                hole_list = list(hole_collection.holes.values())
                hole_list.sort(key=lambda h: (h.center_y, h.center_x))
                detection_units = hole_list
                
                logger.info(f"✅ 后备方案: {len(detection_units)} 个单孔检测单元")
                
        except Exception as e:
            logger.error(f"❌ 蛇形路径生成失败: {e}")
            return
            
        # 3. 模拟检测单元转换
        logger.info("🔄 模拟检测单元转换...")
        snake_sorted_holes = []
        for unit in detection_units:
            if hasattr(unit, 'holes'):
                snake_sorted_holes.extend(unit.holes)
            else:
                snake_sorted_holes.append(unit)
                
        final_count = len(snake_sorted_holes)
        logger.info(f"📈 最终孔位列表: {final_count} 个孔位")
        logger.info(f"完整性: {final_count/original_count*100:.2f}%")
        
        if final_count == original_count:
            logger.info("✅ 遍历完整性正常")
        else:
            logger.error(f"❌ 遍历不完整，缺少 {original_count - final_count} 个孔位")
            
        return final_count == original_count
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_traversal()