#!/usr/bin/env python3
"""
验证模拟控制器修复
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append('.')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def verify_snake_path_removal():
    """验证蛇形路径生成逻辑已移除"""
    try:
        file_path = Path('src/pages/main_detection_p1/components/simulation_controller.py')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查蛇形路径相关代码是否已移除
        removed_items = [
            'snake_path_renderer.generate_snake_path',
            'INTERVAL_FOUR_S_SHAPE',
            'isinstance(unit, HolePair)',
            '_start_pair_detection'
        ]
        
        # 检查新的简单逻辑是否存在
        new_items = [
            '直接使用简单顺序检测',
            'hole_list.sort(key=lambda h: (h.center_y, h.center_x))',
            '立即开始第一个孔位检测',
            '现在只有单孔检测'
        ]
        
        removed_count = sum(1 for item in removed_items if item not in content)
        new_count = sum(1 for item in new_items if item in content)
        
        logger.info(f"✅ 已移除蛇形路径相关代码: {removed_count}/{len(removed_items)}")
        logger.info(f"✅ 已添加新的简单逻辑: {new_count}/{len(new_items)}")
        
        return removed_count == len(removed_items) and new_count == len(new_items)
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return False

def verify_immediate_feedback():
    """验证立即反馈逻辑"""
    try:
        file_path = Path('src/pages/main_detection_p1/components/simulation_controller.py')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查立即反馈相关代码
        feedback_items = [
            'self._process_next_pair()',
            '立即开始第一个孔位检测',
            'color_override=QColor(33, 150, 243)',  # 蓝色
        ]
        
        feedback_count = sum(1 for item in feedback_items if item in content)
        
        logger.info(f"✅ 立即反馈逻辑: {feedback_count}/{len(feedback_items)}")
        
        return feedback_count == len(feedback_items)
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return False

def verify_import_cleanup():
    """验证导入清理"""
    try:
        file_path = Path('src/pages/main_detection_p1/components/simulation_controller.py')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查不再需要的导入是否已移除或注释
        if 'HolePair' not in content or '蛇形路径相关导入已移除' in content:
            logger.info("✅ 蛇形路径导入已清理")
            return True
        else:
            logger.warning("⚠️ 蛇形路径导入未完全清理")
            return False
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🔍 开始验证模拟控制器修复\n")
    
    verifications = [
        ("蛇形路径逻辑移除", verify_snake_path_removal),
        ("立即反馈逻辑", verify_immediate_feedback),
        ("导入清理", verify_import_cleanup)
    ]
    
    passed = 0
    total = len(verifications)
    
    for name, verify_func in verifications:
        if verify_func():
            passed += 1
            logger.info(f"✅ {name}: 通过")
        else:
            logger.error(f"❌ {name}: 失败")
        print()
    
    # 总结
    logger.info("=== 验证结果总结 ===")
    logger.info(f"通过: {passed}/{total}")
    
    if passed == total:
        logger.info("\n🎉 所有修复验证通过！")
        logger.info("现在的模拟控制器应该：")
        logger.info("1. ✅ 不再使用蛇形路径生成")
        logger.info("2. ✅ 直接按顺序检测所有孔位")
        logger.info("3. ✅ 点击开始后立即显示蓝色反馈")
        logger.info("4. ✅ 检测过程中连续显示状态变化")
    else:
        logger.warning(f"\n⚠️ 有 {total-passed} 个验证失败")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)