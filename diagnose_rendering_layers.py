#!/usr/bin/env python3
"""
诊断渲染层级问题 - 检查是否有多个图形项重叠
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RenderingLayersDiagnosis(QMainWindow):
    """诊断渲染层级问题"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.components = {}
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("渲染层级诊断")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("加载组件")
        self.load_btn.clicked.connect(self.load_components)
        button_layout.addWidget(self.load_btn)
        
        self.diagnose_btn = QPushButton("开始诊断")
        self.diagnose_btn.clicked.connect(self.start_diagnosis)
        self.diagnose_btn.setEnabled(False)
        button_layout.addWidget(self.diagnose_btn)
        
        main_layout.addLayout(button_layout)
        
        # 图形视图容器
        self.view_container = QWidget()
        self.view_container.setMinimumHeight(400)
        main_layout.addWidget(self.view_container)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        main_layout.addWidget(self.log_display)
        
    def log(self, message):
        """添加日志"""
        logger.info(message)
        self.log_display.append(message)
        
    def load_components(self):
        """加载所有相关组件"""
        self.log("=== 加载组件 ===")
        
        try:
            # 1. 加载图形视图（中间放大视图）
            from src.core_business.graphics.graphics_view import OptimizedGraphicsView
            graphics_view = OptimizedGraphicsView()
            self.components['graphics_view'] = graphics_view
            self.log("✅ 图形视图加载成功")
            
            # 2. 加载全景图（左侧缩略图）
            from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
            panorama_widget = CompletePanoramaWidget()
            self.components['panorama_widget'] = panorama_widget
            self.log("✅ 全景图组件加载成功")
            
            # 3. 加载孔位数据
            from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
            hole_collection = HoleCollection()
            
            # 创建几个测试孔位
            test_holes = [
                HoleData(0, 0, 10, "C001R001", "管孔"),
                HoleData(50, 0, 10, "C002R001", "管孔"),
                HoleData(100, 0, 10, "C003R001", "管孔"),
            ]
            
            for hole in test_holes:
                hole.status = HoleStatus.PENDING
                hole_collection.add_hole(hole)
                
            self.components['hole_collection'] = hole_collection
            self.log(f"✅ 创建 {len(test_holes)} 个测试孔位")
            
            # 4. 加载数据到视图
            graphics_view.load_hole_collection(hole_collection)
            panorama_widget.load_hole_collection(hole_collection)
            self.log("✅ 数据加载到视图完成")
            
            # 5. 将视图添加到界面
            layout = QHBoxLayout(self.view_container)
            layout.addWidget(panorama_widget, 1)
            layout.addWidget(graphics_view, 2)
            
            self.diagnose_btn.setEnabled(True)
            self.log("\n✅ 所有组件加载成功！")
            
        except Exception as e:
            self.log(f"❌ 组件加载失败: {e}")
            import traceback
            self.log(traceback.format_exc())
            
    def start_diagnosis(self):
        """开始诊断"""
        self.log("\n=== 开始渲染层级诊断 ===")
        
        if not self.components:
            self.log("❌ 请先加载组件")
            return
            
        # 获取组件
        graphics_view = self.components.get('graphics_view')
        panorama_widget = self.components.get('panorama_widget')
        hole_collection = self.components.get('hole_collection')
        
        # 选择第一个孔进行测试
        test_hole = list(hole_collection.holes.values())[0]
        hole_id = test_hole.hole_id
        
        self.log(f"\n测试孔位: {hole_id}")
        
        # 步骤1：检查初始状态
        self.log("\n1. 检查初始状态:")
        self.check_all_views(hole_id)
        
        # 步骤2：设置蓝色（模拟检测中）
        QTimer.singleShot(1000, lambda: self.set_blue_color(hole_id))
        
        # 步骤3：清除蓝色（模拟检测完成）
        QTimer.singleShot(3000, lambda: self.clear_blue_color(hole_id))
        
        # 步骤4：检查蛇形路径渲染器
        QTimer.singleShot(4000, lambda: self.check_snake_path_renderer())
        
    def check_all_views(self, hole_id):
        """检查所有视图中的孔位状态"""
        graphics_view = self.components.get('graphics_view')
        panorama_widget = self.components.get('panorama_widget')
        
        # 检查图形视图
        if graphics_view and hasattr(graphics_view, 'hole_items'):
            if hole_id in graphics_view.hole_items:
                item = graphics_view.hole_items[hole_id]
                color = item.brush().color()
                self.log(f"   图形视图: RGB({color.red()}, {color.green()}, {color.blue()})")
                self.log(f"   颜色覆盖: {item._color_override is not None}")
            else:
                self.log(f"   图形视图: 未找到孔位 {hole_id}")
                
        # 检查全景图
        if panorama_widget:
            self.check_panorama_holes(panorama_widget, hole_id)
            
    def check_panorama_holes(self, panorama_widget, hole_id):
        """检查全景图中的孔位"""
        # 检查场景中的所有项
        if hasattr(panorama_widget, 'scene'):
            scene = panorama_widget.scene
            items = scene.items()
            hole_items = []
            
            for item in items:
                # 检查是否是孔位项
                if hasattr(item, 'hole_data') and hasattr(item, '_color_override'):
                    if item.hole_data.hole_id == hole_id:
                        hole_items.append(item)
                        
            self.log(f"   全景图: 找到 {len(hole_items)} 个匹配的孔位项")
            
            for i, item in enumerate(hole_items):
                color = item.brush().color()
                self.log(f"     项{i+1}: RGB({color.red()}, {color.green()}, {color.blue()})")
                self.log(f"     颜色覆盖: {item._color_override is not None}")
                self.log(f"     Z值: {item.zValue()}")
                
    def set_blue_color(self, hole_id):
        """设置蓝色"""
        self.log(f"\n2. 设置蓝色覆盖:")
        
        graphics_view = self.components.get('graphics_view')
        panorama_widget = self.components.get('panorama_widget')
        hole_collection = self.components.get('hole_collection')
        
        blue_color = QColor(33, 150, 243)
        
        # 更新图形视图
        if graphics_view:
            graphics_view.update_hole_status(hole_id, HoleStatus.PENDING, blue_color)
            self.log("   已更新图形视图")
            
        # 更新全景图
        if panorama_widget and hasattr(panorama_widget, 'update_hole_status'):
            panorama_widget.update_hole_status(hole_id, HoleStatus.PENDING, blue_color)
            self.log("   已更新全景图")
            
        # 检查更新后的状态
        QTimer.singleShot(500, lambda: self.check_all_views(hole_id))
        
    def clear_blue_color(self, hole_id):
        """清除蓝色"""
        self.log(f"\n3. 清除蓝色覆盖:")
        
        graphics_view = self.components.get('graphics_view')
        panorama_widget = self.components.get('panorama_widget')
        hole_collection = self.components.get('hole_collection')
        
        # 更新为合格状态，清除颜色覆盖
        if graphics_view:
            graphics_view.update_hole_status(hole_id, HoleStatus.QUALIFIED, None)
            self.log("   已更新图形视图（合格状态）")
            
        if panorama_widget and hasattr(panorama_widget, 'update_hole_status'):
            panorama_widget.update_hole_status(hole_id, HoleStatus.QUALIFIED, None)
            self.log("   已更新全景图（合格状态）")
            
        # 检查更新后的状态
        QTimer.singleShot(500, lambda: self.check_all_views(hole_id))
        
    def check_snake_path_renderer(self):
        """检查蛇形路径渲染器"""
        self.log(f"\n4. 检查蛇形路径渲染器:")
        
        graphics_view = self.components.get('graphics_view')
        
        # 检查场景中是否有蛇形路径项
        if graphics_view and hasattr(graphics_view, 'scene'):
            scene = graphics_view.scene
            path_items = []
            
            for item in scene.items():
                # 查找路径相关的图形项
                class_name = type(item).__name__
                if 'path' in class_name.lower() or 'line' in class_name.lower():
                    path_items.append(item)
                    
            self.log(f"   找到 {len(path_items)} 个路径相关项")
            
            # 检查是否有蛇形路径渲染器实例
            if hasattr(graphics_view, 'snake_path_renderer'):
                self.log("   ✅ 图形视图包含蛇形路径渲染器")
            else:
                self.log("   ℹ️ 图形视图不包含蛇形路径渲染器")
                
        # 检查全景图
        panorama_widget = self.components.get('panorama_widget')
        if panorama_widget and hasattr(panorama_widget, 'scene'):
            scene = panorama_widget.scene
            # 检查 Z 值层级
            z_values = {}
            for item in scene.items():
                z = item.zValue()
                class_name = type(item).__name__
                if z not in z_values:
                    z_values[z] = []
                z_values[z].append(class_name)
                
            self.log("\n   场景层级分析:")
            for z in sorted(z_values.keys(), reverse=True):
                self.log(f"     Z={z}: {', '.join(set(z_values[z]))}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = RenderingLayersDiagnosis()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()