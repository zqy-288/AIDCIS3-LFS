"""
人工复检工具
提供图片浏览功能，点击人工复检后进入缺陷标注界面
"""

import os
from typing import List, Optional
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                               QLabel, QMessageBox, QFrame, QSizePolicy, QTabWidget,
                               QGroupBox, QSplitter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont

from .image_browser import ImageBrowser
from .defect_annotation_tool import DefectAnnotationTool


class DefectAnnotationWithBrowser(QWidget):
    """人工复检工具 - 浏览图片并可启动缺陷标注"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.image_browser = None
        self.annotation_tool = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化子组件
        self.init_components()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("人工复检 - 图片浏览")
        self.setMinimumSize(1400, 900)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 直接使用单一界面，不使用选项卡
        self.main_widget = None
        main_layout.addWidget(QLabel())  # 占位符，稍后替换
        
    def init_components(self):
        """初始化子组件"""
        try:
            # 只创建图片浏览界面（人工复检界面）
            print("🔧 初始化人工复检界面...")
            self.image_browser = ImageBrowser()
            print("✅ 人工复检界面初始化完成")
            
            # 创建缺陷标注工具（隐藏，仅在需要时使用）
            print("🔧 初始化缺陷标注工具...")
            self.annotation_tool = DefectAnnotationTool()
            print("✅ 缺陷标注工具初始化完成")
            
            # 连接信号：图片浏览器的人工复检请求 -> 切换到缺陷标注工具
            self.image_browser.manual_review_requested.connect(self.start_manual_review)
            
            # 设置默认显示图片浏览界面
            self._switch_to_browser()
            
            print("✅ 人工复检工具初始化完成")
            
        except Exception as e:
            print(f"❌ 初始化子组件失败: {e}")
            # 创建错误显示组件
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"初始化失败: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px;")
            error_layout.addWidget(error_label)
            
            # 替换主布局中的占位符
            layout = self.layout()
            layout.removeWidget(layout.itemAt(0).widget())
            layout.addWidget(error_widget)
    
    def _switch_to_browser(self):
        """切换到图片浏览界面"""
        layout = self.layout()
        # 移除当前组件
        if self.main_widget:
            layout.removeWidget(self.main_widget)
            self.main_widget.setParent(None)
        
        # 添加图片浏览界面
        self.main_widget = self.image_browser
        layout.addWidget(self.main_widget)
        
    def _switch_to_annotation(self):
        """切换到缺陷标注界面"""
        layout = self.layout()
        # 移除当前组件
        if self.main_widget:
            layout.removeWidget(self.main_widget)
            self.main_widget.setParent(None)
        
        # 添加标注工具，并添加返回按钮
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加返回按钮
        back_button = QPushButton("← 返回人工复检")
        back_button.clicked.connect(self._switch_to_browser)
        back_button.setMaximumWidth(150)
        container_layout.addWidget(back_button)
        
        # 添加标注工具
        container_layout.addWidget(self.annotation_tool)
        
        self.main_widget = container
        layout.addWidget(self.main_widget)
            
    def start_manual_review(self, image_path: str):
        """启动人工复检，切换到缺陷标注界面并加载图片"""
        try:
            # 切换到缺陷标注界面
            self._switch_to_annotation()
            
            # 将图片加载到缺陷标注界面
            success = self.annotation_tool.load_single_image_for_review(image_path)
            
            if success:
                # 显示确认消息
                QMessageBox.information(
                    self, "人工复检", 
                    f"已成功进入缺陷标注模式\n"
                    f"正在复检图片: {os.path.basename(image_path)}\n\n"
                    f"提示：\n"
                    f"• 直接拖拽绘制缺陷框\n"
                    f"• 右键点击缺陷框可删除\n"
                    f"• 完成后点击'保存标注'\n"
                    f"• 点击'返回人工复检'按钮继续浏览"
                )
            else:
                QMessageBox.warning(self, "警告", "加载图片到缺陷标注界面失败")
                self._switch_to_browser()  # 失败时返回浏览界面
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动人工复检失败: {str(e)}")
            self._switch_to_browser()  # 错误时返回浏览界面
            
    def refresh_image_browser(self):
        """刷新图片浏览器"""
        if self.image_browser:
            self.image_browser.refresh_images()
            
    def get_current_mode(self) -> str:
        """获取当前模式名称"""
        if self.main_widget == self.image_browser:
            return "人工复检"
        elif self.annotation_tool and self.annotation_tool.parent() == self.main_widget:
            return "缺陷标注"
        else:
            return "未知"
            
    def load_data_for_hole(self, hole_id: str):
        """
        为指定孔位加载数据 - P3界面兼容方法
        
        Args:
            hole_id: 孔位ID
        """
        try:
            print(f"📊 缺陷标注工具（含图片浏览）: 加载孔位 {hole_id} 的数据")
            
            # 如果当前在标注模式，且标注工具有load_data_for_hole方法，调用之
            if (hasattr(self, 'annotation_tool') and self.annotation_tool and 
                hasattr(self.annotation_tool, 'load_data_for_hole')):
                self.annotation_tool.load_data_for_hole(hole_id)
                
            # 如果图片浏览器有相关方法，也可以调用
            if (hasattr(self, 'image_browser') and self.image_browser and
                hasattr(self.image_browser, 'load_data_for_hole')):
                self.image_browser.load_data_for_hole(hole_id)
            else:
                # 默认行为：刷新图片浏览器
                self.refresh_image_browser()
                
        except Exception as e:
            print(f"❌ 加载孔位数据失败 {hole_id}: {e}")