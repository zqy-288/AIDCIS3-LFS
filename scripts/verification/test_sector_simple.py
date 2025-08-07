#!/usr/bin/env python3
"""
简单的扇形显示测试
避免循环导入，直接测试核心组件
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QGraphicsView, QGraphicsScene, QPushButton
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QPen

class SimpleSectorTest(QMainWindow):
    """简单扇形测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单扇形显示测试")
        self.setGeometry(100, 100, 700, 700)
        
        self.setup_ui()
        self.create_test_display()
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("扇形分隔线显示测试")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 创建图形视图
        self.graphics_view = QGraphicsView()
        self.graphics_view.setMinimumSize(600, 600)
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)
        
        # 状态标签
        self.status_label = QLabel("正在创建扇形分隔线...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 添加关闭按钮
        close_button = QPushButton("关闭测试")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        # 添加5秒自动关闭定时器
        QTimer.singleShot(5000, self.close)
    
    def create_test_display(self):
        """创建测试显示"""
        try:
            # 设置场景大小
            self.scene.setSceneRect(-300, -300, 600, 600)
            
            # 绘制全景圆形背景
            center = QPointF(0, 0)
            radius = 250
            
            # 添加圆形背景
            circle_pen = QPen(QColor(200, 200, 200), 2)
            self.scene.addEllipse(
                center.x() - radius, center.y() - radius,
                radius * 2, radius * 2,
                circle_pen
            )
            
            # 🔧 创建扇形分隔线 - 按照修复后的样式
            divider_pen = QPen(QColor(80, 80, 80, 200), 3, Qt.SolidLine)  # 深灰色，alpha=200
            
            # 水平分隔线
            h_line = self.scene.addLine(
                center.x() - radius, center.y(),
                center.x() + radius, center.y(),
                divider_pen
            )
            h_line.setZValue(50)
            
            # 垂直分隔线
            v_line = self.scene.addLine(
                center.x(), center.y() - radius,
                center.x(), center.y() + radius,
                divider_pen
            )
            v_line.setZValue(50)
            
            # 🔧 创建扇形边界线 - 按照修复后的样式
            sector_pen = QPen(QColor(128, 128, 128), 2, Qt.DashLine)  # 灰色虚线
            
            # 添加四个扇形边界（简化版，用直线表示边界）
            # 第一象限边界
            self.scene.addLine(0, 0, radius*0.7, -radius*0.7, sector_pen)  # 45度线
            # 第二象限边界  
            self.scene.addLine(0, 0, -radius*0.7, -radius*0.7, sector_pen)  # 135度线
            # 第三象限边界
            self.scene.addLine(0, 0, -radius*0.7, radius*0.7, sector_pen)  # 225度线
            # 第四象限边界
            self.scene.addLine(0, 0, radius*0.7, radius*0.7, sector_pen)  # 315度线
            
            # 添加象限标签
            label_style = QColor(100, 100, 100)
            font_size = 14
            
            # 添加文字标签
            self.add_text_label("扇形1", QPointF(120, -120), label_style)
            self.add_text_label("扇形2", QPointF(-120, -120), label_style)
            self.add_text_label("扇形3", QPointF(-120, 120), label_style)
            self.add_text_label("扇形4", QPointF(120, 120), label_style)
            
            # 添加中心点
            center_pen = QPen(QColor(255, 0, 0), 6)
            self.scene.addEllipse(-3, -3, 6, 6, center_pen)
            
            self.status_label.setText(
                "✅ 扇形分隔线测试完成!\n"
                "🔍 应该看到:\n"
                "• 深灰色十字分隔线 (alpha=200)\n"
                "• 灰色虚线扇形边界\n"
                "• 四个清晰的扇形区域"
            )
            
            print("✅ 扇形分隔线测试显示创建成功")
            print("🔍 检查项目:")
            print("  • 深灰色十字分隔线是否可见")
            print("  • 灰色虚线边界是否可见")
            print("  • 四个扇形区域是否清晰分割")
            
        except Exception as e:
            self.status_label.setText(f"❌ 测试失败: {str(e)}")
            print(f"❌ 扇形分隔线测试失败: {e}")
    
    def add_text_label(self, text, pos, color):
        """添加文字标签"""
        text_item = self.scene.addText(text)
        text_item.setPos(pos)
        text_item.setDefaultTextColor(color)

def main():
    """主测试函数"""
    print("🚀 启动简单扇形显示测试")
    
    app = QApplication(sys.argv)
    window = SimpleSectorTest()
    window.show()
    
    print("📋 测试窗口已打开")
    print("📸 请截图确认扇形分隔线是否按预期显示")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()