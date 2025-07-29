"""
中间可视化面板组件 - 独立高内聚模块
负责显示管孔检测视图，包括视图模式切换、扇形导航、图形显示等
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QGroupBox, QGraphicsView,
    QGraphicsScene, QGraphicsTextItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class CenterVisualizationPanel(QWidget):
    """中间可视化面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    hole_selected = Signal(str)
    view_mode_changed = Signal(str)
    sector_navigation_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.current_view_mode = "macro"
        self.current_sector = None
        self.graphics_view = None
        self.workpiece_diagram = None  # 兼容性引用
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        # 主组框 (old版本样式)
        panel = QGroupBox("管孔检测视图")
        
        # 设置组标题字体
        center_panel_font = QFont()
        center_panel_font.setPointSize(12)
        center_panel_font.setBold(True)
        panel.setFont(center_panel_font)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 1. 状态图例已移除 (按用户要求删除)

        # 2. 视图控制 (old版本的层级化显示控制)
        view_controls_frame = self._create_view_controls()
        layout.addWidget(view_controls_frame)

        # 3. 主显示区域 (old版本: DynamicSectorDisplayWidget, 800×700px)
        main_display_widget = self._create_main_display_area()
        layout.addWidget(main_display_widget)

        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(panel)

    def _create_view_controls(self):
        """创建视图控制 - old版本的层级化显示控制"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # 视图模式标签
        view_label = QLabel("视图模式:")
        view_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(view_label)
        
        # 宏观区域视图按钮 (old版本样式)
        self.macro_view_btn = QPushButton("📊 宏观区域视图")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)
        self.macro_view_btn.setMinimumHeight(35)
        self.macro_view_btn.setMinimumWidth(140)
        self.macro_view_btn.setToolTip("显示整个管板的全貌，适合快速浏览和状态概览")
        
        # 微观孔位视图按钮
        self.micro_view_btn = QPushButton("🔍 微观孔位视图")
        self.micro_view_btn.setCheckable(True)
        self.micro_view_btn.setMinimumHeight(35)
        self.micro_view_btn.setMinimumWidth(140)
        self.micro_view_btn.setToolTip("显示孔位的详细信息，适合精确检测和分析")
        
        # 全景总览视图按钮
        self.panorama_view_btn = QPushButton("🌍 全景总览视图")
        self.panorama_view_btn.setCheckable(True)
        self.panorama_view_btn.setMinimumHeight(35)
        self.panorama_view_btn.setMinimumWidth(140)
        self.panorama_view_btn.setToolTip("显示完整的管板全景图，适合整体分析")
        
        layout.addWidget(self.macro_view_btn)
        layout.addWidget(self.micro_view_btn)
        layout.addWidget(self.panorama_view_btn)
        
        layout.addSpacing(20)
        
        # 扇形导航控制 (old版本样式)
        nav_label = QLabel("扇形导航:")
        nav_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(nav_label)
        
        self.prev_sector_btn = QPushButton("◀ 上一扇形")
        self.prev_sector_btn.setMinimumHeight(35)
        self.prev_sector_btn.setMinimumWidth(100)
        
        self.next_sector_btn = QPushButton("下一扇形 ▶")
        self.next_sector_btn.setMinimumHeight(35)
        self.next_sector_btn.setMinimumWidth(100)
        
        layout.addWidget(self.prev_sector_btn)
        layout.addWidget(self.next_sector_btn)
        
        layout.addStretch()
        return control_frame

    def _create_main_display_area(self):
        """创建主显示区域 - 初始为空白，等待加载CAP1000 DXF"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建空白的图形视图，准备加载CAP1000数据
        self.graphics_view = self._create_graphics_view()
        main_layout.addWidget(self.graphics_view)
        
        return main_widget
    
    def _create_graphics_view(self):
        """创建图形视图"""
        view = QGraphicsView()
        scene = QGraphicsScene()
        view.setScene(scene)
        view.setMinimumSize(800, 700)
        
        # 显示初始提示信息
        text_item = QGraphicsTextItem("请选择产品型号 (CAP1000) 或加载DXF文件")
        font = QFont()
        font.setPointSize(14)
        text_item.setFont(font)
        text_item.setPos(250, 350)
        scene.addItem(text_item)
        
        return view

    def set_graphics_view(self, graphics_view):
        """设置外部图形视图组件"""
        if self.graphics_view:
            # 移除旧视图
            layout = self.graphics_view.parent().layout()
            layout.removeWidget(self.graphics_view)
            self.graphics_view.deleteLater()
            
        self.graphics_view = graphics_view
        
        # 添加新视图
        main_widget = self.findChild(QWidget, "")
        if main_widget and main_widget.layout():
            main_widget.layout().addWidget(self.graphics_view)
            
        self.logger.info("✅ 图形视图已设置")

    def setup_connections(self):
        """设置信号连接"""
        # 视图模式按钮连接
        self.macro_view_btn.clicked.connect(lambda: self._on_view_mode_changed("macro"))
        self.micro_view_btn.clicked.connect(lambda: self._on_view_mode_changed("micro"))
        self.panorama_view_btn.clicked.connect(lambda: self._on_view_mode_changed("panorama"))
        
        # 扇形导航按钮连接
        self.prev_sector_btn.clicked.connect(lambda: self.sector_navigation_requested.emit("previous"))
        self.next_sector_btn.clicked.connect(lambda: self.sector_navigation_requested.emit("next"))

    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        # 更新按钮状态
        self.macro_view_btn.setChecked(mode == "macro")
        self.micro_view_btn.setChecked(mode == "micro")
        self.panorama_view_btn.setChecked(mode == "panorama")
        
        self.current_view_mode = mode
        self.view_mode_changed.emit(mode)
        self.logger.info(f"🔄 视图模式切换到: {mode}")

    def _on_hole_clicked(self, hole_id, status):
        """处理孔位点击事件"""
        self.logger.info(f"孔位点击: {hole_id}, 状态: {status}")
        # 发射信号给上层
        self.hole_selected.emit(hole_id)

    def get_graphics_view(self):
        """获取图形视图组件"""
        return self.graphics_view

    def get_scene(self):
        """获取图形场景"""
        if self.graphics_view:
            if hasattr(self.graphics_view, 'scene'):
                return self.graphics_view.scene
            else:
                return self.graphics_view.scene()
        return None

    def update_sector_display(self, sector):
        """更新扇形显示"""
        self.current_sector = sector
        self.logger.info(f"扇形显示已更新: {sector}")

    def clear_display(self):
        """清空显示"""
        scene = self.get_scene()
        if scene:
            scene.clear()
            
            # 重新显示提示信息
            text_item = QGraphicsTextItem("请选择产品型号 (CAP1000) 或加载DXF文件")
            font = QFont()
            font.setPointSize(14)
            text_item.setFont(font)
            text_item.setPos(250, 350)
            scene.addItem(text_item)