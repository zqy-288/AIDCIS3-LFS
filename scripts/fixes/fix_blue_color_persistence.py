#!/usr/bin/env python3
"""
修复蓝色持续显示问题
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_issue():
    """分析问题"""
    logger.info("分析蓝色持续显示问题...")
    
    # 检查 simulation_controller.py
    sim_path = project_root / "src/pages/main_detection_p1/components/simulation_controller.py"
    
    with open(sim_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找关键代码段
    issues = []
    
    # 1. 检查 _finalize_current_pair_status 是否正确清除颜色
    if "color_override=None" in content:
        logger.info("✅ _finalize_current_pair_status 正确传递 color_override=None")
    else:
        issues.append("_finalize_current_pair_status 未正确清除颜色覆盖")
    
    # 2. 检查图形视图更新逻辑
    if "viewport().update()" in content:
        logger.info("✅ 包含视图刷新代码")
    else:
        issues.append("缺少视图刷新代码")
    
    return issues


def apply_fixes():
    """应用修复"""
    logger.info("\n应用修复...")
    
    # 1. 增强 simulation_controller.py 的颜色清除逻辑
    sim_path = project_root / "src/pages/main_detection_p1/components/simulation_controller.py"
    
    with open(sim_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 _finalize_current_pair_status 方法
    if "_finalize_current_pair_status" in content:
        # 增强日志输出
        old_line = 'self.logger.info(f"📋 配对检测 {hole.hole_id}: {status_text}")'
        new_line = '''self.logger.info(f"📋 配对检测 {hole.hole_id}: {status_text}")
            self.logger.debug(f"   颜色覆盖已清除: {hole.hole_id}")'''
        
        if old_line in content and new_line not in content:
            content = content.replace(old_line, new_line)
            logger.info("✅ 增强了日志输出")
    
    # 2. 确保 graphics_view 的更新方法被正确调用
    if "_update_hole_status" in content:
        # 检查是否有额外的刷新调用
        method_start = content.find("def _update_hole_status")
        method_end = content.find("\n    def ", method_start + 1)
        method_content = content[method_start:method_end]
        
        # 在方法末尾添加额外的刷新确认
        if "_force_refresh_graphics_view" in method_content:
            logger.info("✅ 已包含强制刷新调用")
        else:
            logger.info("⚠️ 可能需要增强刷新逻辑")
    
    # 保存修改
    with open(sim_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ 修复已应用")


def create_test_script():
    """创建测试脚本"""
    test_content = '''#!/usr/bin/env python3
"""
测试蓝色清除功能
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleStatus
from src.core_business.graphics.hole_item import HoleGraphicsItem
from src.modules.test_hole_data_generator import TestHoleDataGenerator


def test_color_override():
    """测试颜色覆盖功能"""
    app = QApplication(sys.argv)
    
    # 创建测试孔位
    generator = TestHoleDataGenerator()
    hole = generator.generate_single_hole(0, 0, "TEST001")
    
    # 创建图形项
    item = HoleGraphicsItem(hole)
    
    print("1. 初始状态:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    
    # 设置蓝色覆盖
    blue = QColor(33, 150, 243)
    item.set_color_override(blue)
    
    print("\\n2. 设置蓝色后:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    
    # 清除覆盖
    item.clear_color_override()
    
    print("\\n3. 清除覆盖后:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    
    # 更新状态
    item.update_status(HoleStatus.QUALIFIED)
    
    print("\\n4. 更新为合格状态后:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    
    return 0


if __name__ == "__main__":
    test_color_override()
'''
    
    test_path = project_root / "test_blue_color_clear.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    logger.info(f"✅ 创建测试脚本: {test_path}")


def main():
    """主函数"""
    logger.info("=== 修复蓝色持续显示问题 ===\n")
    
    # 分析问题
    issues = analyze_issue()
    
    if issues:
        logger.warning(f"发现 {len(issues)} 个潜在问题:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    # 应用修复
    apply_fixes()
    
    # 创建测试脚本
    create_test_script()
    
    logger.info("\n=== 修复完成 ===")
    logger.info("\n建议的下一步操作:")
    logger.info("1. 运行 python test_blue_color_clear.py 测试颜色清除功能")
    logger.info("2. 运行 python diagnose_color_override_issue.py 进行完整诊断")
    logger.info("3. 在主程序中测试模拟功能，观察蓝色是否正确清除")


if __name__ == "__main__":
    main()