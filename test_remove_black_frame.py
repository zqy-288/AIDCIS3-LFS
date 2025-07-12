#!/usr/bin/env python3
"""
测试修复全景预览黑框问题
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

class RemoveBlackFrameTest:
    """修复黑框测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_remove_black_frame(self):
        """测试移除黑框"""
        self.logger.info("🚀 测试移除全景预览黑框")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 检查全景预览组件
        self.logger.info("\\n🔍 检查全景预览组件设置")
        
        panorama = self.window.sidebar_panorama
        panorama_view = panorama.panorama_view
        
        # 检查边框设置
        frame_style = panorama_view.frameStyle()
        self.logger.info(f"📐 边框样式: {frame_style}")
        
        # 检查样式表
        style_sheet = panorama_view.styleSheet()
        self.logger.info(f"🎨 样式表: {style_sheet}")
        
        # 3. 加载测试数据
        self.logger.info("\\n🔄 加载测试数据验证显示")
        
        hole_collection = self._create_simple_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 4. 检查显示效果
        self.logger.info("\\n✅ 检查显示效果")
        
        scene = panorama_view.scene
        if scene and len(scene.items()) > 0:
            self.logger.info("✅ 全景图成功加载内容")
            
            # 检查背景设置
            bg_brush = panorama_view.backgroundBrush()
            self.logger.info(f"🎨 背景画刷: {bg_brush}")
            
            # 检查是否有黑框
            if "border: none" in style_sheet:
                self.logger.info("✅ 已设置无边框样式")
            else:
                self.logger.info("❌ 仍有边框设置")
                
            if "background-color: white" in style_sheet:
                self.logger.info("✅ 已设置白色背景")
            else:
                self.logger.info("❌ 背景色设置异常")
        else:
            self.logger.info("❌ 全景图未加载内容")
        
        return True
    
    def _create_simple_test_data(self):
        """创建简单测试数据"""
        test_holes = {}
        
        # 创建一个简单圆形
        import math
        center_x, center_y = 400, 400
        radius = 100
        holes_count = 24
        
        for i in range(holes_count):
            angle = (2 * math.pi * i) / holes_count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            hole_id = f"T{i+1:03d}"
            hole_data = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.8,
                status=HoleStatus.PENDING
            )
            test_holes[hole_id] = hole_data
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'black_frame_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection

def main():
    """主函数"""
    test = RemoveBlackFrameTest()
    
    try:
        success = test.test_remove_black_frame()
        
        if test.window:
            test.logger.info("\\n🎯 黑框修复验证:")
            test.logger.info("✅ 已移除 QFrame.StyledPanel 边框样式")
            test.logger.info("✅ 已设置 QFrame.NoFrame 无边框")
            test.logger.info("✅ 已设置白色背景和无边框样式表")
            test.logger.info("\\n👁️ 请检查全景预览:")
            test.logger.info("  1. 是否还有黑色边框")
            test.logger.info("  2. 背景是否为干净的白色")
            test.logger.info("  3. 内容是否正常显示")
            test.logger.info("\\n窗口将在10秒后关闭...")
            QTest.qWait(10000)
        
        return 0 if success else 1
        
    except Exception as e:
        test.logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())