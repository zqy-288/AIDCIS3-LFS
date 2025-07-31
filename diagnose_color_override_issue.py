#!/usr/bin/env python3
"""
诊断颜色覆盖问题 - 检查蓝色为什么不会消失
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'color_override_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)


class ColorOverrideDiagnosisWindow(QMainWindow):
    """颜色覆盖诊断窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
        self.load_components()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("颜色覆盖问题诊断")
        self.setGeometry(100, 100, 800, 600)
        
        # 主widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 布局
        layout = QVBoxLayout(main_widget)
        
        # 控制按钮
        self.start_btn = QPushButton("开始诊断")
        self.start_btn.clicked.connect(self.start_diagnosis)
        layout.addWidget(self.start_btn)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
    def load_components(self):
        """加载必要组件"""
        try:
            # 加载图形视图
            from src.core_business.graphics.graphics_view import OptimizedGraphicsView
            self.graphics_view = OptimizedGraphicsView()
            
            # 加载孔位数据
            from src.core_business.models.hole_data import HoleCollection
            from src.modules.test_hole_data_generator import TestHoleDataGenerator
            
            generator = TestHoleDataGenerator()
            self.hole_collection = generator.generate_partial_holes(20)  # 生成20个测试孔
            
            # 加载数据到视图
            self.graphics_view.load_hole_collection(self.hole_collection)
            
            self.log("✅ 组件加载成功")
            
        except Exception as e:
            self.log(f"❌ 组件加载失败: {e}")
            
    def start_diagnosis(self):
        """开始诊断"""
        self.log("\n=== 开始颜色覆盖诊断 ===")
        
        # 选择第一个孔进行测试
        test_hole = list(self.hole_collection.holes.values())[0]
        hole_id = test_hole.hole_id
        
        self.log(f"测试孔位: {hole_id}")
        
        # 步骤1：设置蓝色覆盖
        self.log("\n1. 设置蓝色覆盖...")
        blue_color = QColor(33, 150, 243)
        
        # 尝试不同的更新方法
        if hasattr(self.graphics_view, 'update_hole_status'):
            self.graphics_view.update_hole_status(hole_id, test_hole.status, blue_color)
            self.log("   使用 update_hole_status 方法")
        
        # 检查孔项状态
        self.check_hole_item_state(hole_id, "设置蓝色后")
        
        # 步骤2：2秒后清除覆盖
        QTimer.singleShot(2000, lambda: self.clear_color_override(hole_id))
        
    def clear_color_override(self, hole_id):
        """清除颜色覆盖"""
        self.log("\n2. 清除颜色覆盖...")
        
        # 获取孔位数据
        hole_data = self.hole_collection.holes[hole_id]
        
        # 尝试清除覆盖
        if hasattr(self.graphics_view, 'update_hole_status'):
            # 传递 None 作为 color_override
            self.graphics_view.update_hole_status(hole_id, hole_data.status, None)
            self.log("   使用 update_hole_status(color_override=None)")
        
        # 检查状态
        self.check_hole_item_state(hole_id, "清除覆盖后")
        
        # 步骤3：强制刷新
        QTimer.singleShot(1000, lambda: self.force_refresh(hole_id))
        
    def force_refresh(self, hole_id):
        """强制刷新"""
        self.log("\n3. 强制刷新视图...")
        
        # 强制刷新视图
        if self.graphics_view:
            self.graphics_view.viewport().update()
            if hasattr(self.graphics_view, 'scene'):
                scene = self.graphics_view.scene
                if scene:
                    scene.update()
                    self.log("   场景已更新")
        
        # 最终检查
        self.check_hole_item_state(hole_id, "强制刷新后")
        
    def check_hole_item_state(self, hole_id, phase):
        """检查孔项状态"""
        self.log(f"\n检查 {phase}:")
        
        # 获取图形项
        if hasattr(self.graphics_view, 'hole_items') and hole_id in self.graphics_view.hole_items:
            hole_item = self.graphics_view.hole_items[hole_id]
            
            # 检查颜色覆盖状态
            if hasattr(hole_item, '_color_override'):
                override = hole_item._color_override
                if override:
                    self.log(f"   ⚠️ 颜色覆盖仍存在: {override.name()}")
                else:
                    self.log(f"   ✅ 颜色覆盖已清除")
            
            # 检查当前画刷颜色
            if hasattr(hole_item, 'brush'):
                brush = hole_item.brush()
                color = brush.color()
                self.log(f"   当前颜色: RGB({color.red()}, {color.green()}, {color.blue()})")
                
                # 判断是否为蓝色
                if color.red() == 33 and color.green() == 150 and color.blue() == 243:
                    self.log("   ❌ 仍然是蓝色!")
                else:
                    self.log("   ✅ 颜色已恢复")
                    
    def log(self, message):
        """添加日志"""
        self.logger.info(message)
        self.log_display.append(message)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = ColorOverrideDiagnosisWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()