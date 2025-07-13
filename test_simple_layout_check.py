#!/usr/bin/env python3
"""
简化的布局检查脚本
快速验证布局修改效果
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication, QSplitter
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from main_window.main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

class SimpleLayoutCheck:
    """简化的布局检查类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def check_layout(self):
        """检查布局"""
        self.logger.info("🚀 开始简化布局检查")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(3000)
        
        # 2. 查找所有分割器
        self.logger.info("\\n🔍 查找分割器组件")
        
        splitters = self.window.findChildren(QSplitter)
        self.logger.info(f"📊 找到 {len(splitters)} 个分割器")
        
        for i, splitter in enumerate(splitters):
            sizes = splitter.sizes()
            orientation = "水平" if splitter.orientation() == Qt.Horizontal else "垂直"
            self.logger.info(f"  分割器 {i+1} ({orientation}): {sizes}")
        
        # 3. 检查主要组件尺寸
        self.logger.info("\\n📐 检查主要组件尺寸")
        
        # 主显示区域
        if hasattr(self.window, 'dynamic_sector_display'):
            main_size = self.window.dynamic_sector_display.size()
            self.logger.info(f"📏 主显示区域: {main_size.width()} x {main_size.height()}")
        
        # 全景预览
        if hasattr(self.window, 'sidebar_panorama'):
            panorama_size = self.window.sidebar_panorama.size()
            self.logger.info(f"📏 全景预览容器: {panorama_size.width()} x {panorama_size.height()}")
            
            panorama_view_size = self.window.sidebar_panorama.panorama_view.size()
            self.logger.info(f"📏 全景预览内容: {panorama_view_size.width()} x {panorama_view_size.height()}")
        
        # 4. 加载数据测试缩放效果
        self.logger.info("\\n🔄 加载数据测试效果")
        
        # 创建简单测试数据
        hole_collection = self._create_simple_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(4000)
        
        # 5. 检查全景预览缩放
        self.logger.info("\\n🎯 检查全景预览缩放效果")
        
        panorama_view = self.window.sidebar_panorama.panorama_view
        scene = panorama_view.scene
        
        if scene and len(scene.items()) > 0:
            transform = panorama_view.transform()
            scale_factor = transform.m11()
            self.logger.info(f"📏 全景预览缩放比例: {scale_factor:.3f}")
            
            if scale_factor <= 0.5:
                self.logger.info("✅ 全景预览DXF内容缩放适中")
            else:
                self.logger.info("❌ 全景预览DXF内容仍然较大")
        
        return True
    
    def _create_simple_test_data(self):
        """创建简单测试数据"""
        test_holes = {}
        
        # 创建一个简单的圆形分布
        import math
        center_x, center_y = 400, 400
        
        for ring in range(1, 4):  # 3个圆
            radius = ring * 80 + 120
            holes_count = ring * 16
            
            for i in range(holes_count):
                angle = (2 * math.pi * i) / holes_count
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                hole_id = f"H{len(test_holes)+1:05d}"
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
            metadata={
                'source_file': 'simple_layout_test',
                'total_holes': len(test_holes)
            }
        )
        
        self.logger.info(f"🧪 创建简单测试数据: {len(test_holes)} 个孔位")
        return hole_collection

def main():
    """主函数"""
    test = SimpleLayoutCheck()
    
    try:
        success = test.check_layout()
        
        if test.window:
            test.logger.info("\\n👁️ 请观察以下效果：")
            test.logger.info("  1. 中间白色区域是否变大了")
            test.logger.info("  2. 左下角全景预览中的圆形是否变小了")
            test.logger.info("  3. 右侧面板是否变窄了")
            test.logger.info("\\n窗口将在15秒后关闭...")
            QTest.qWait(15000)
        
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