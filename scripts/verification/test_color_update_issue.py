#!/usr/bin/env python3
"""
测试Qt图形项颜色更新问题
用于诊断和验证颜色更新机制
"""

import sys
import logging
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class TestHoleItem(QGraphicsEllipseItem):
    """测试用的孔位图形项"""
    
    def __init__(self, x, y, radius, hole_id):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.setPos(x, y)
        self.hole_id = hole_id
        self._color = QColor(200, 200, 200)  # 默认灰色
        self._paint_count = 0
        self.update_appearance()
        
    def update_appearance(self):
        """更新外观"""
        logger.debug(f"[{self.hole_id}] update_appearance() 调用, 颜色: {self._color.name()}")
        pen = QPen(self._color.darker(120), 1.0)
        brush = QBrush(self._color)
        self.setPen(pen)
        self.setBrush(brush)
        self.update()
        
    def set_color(self, color):
        """设置颜色"""
        logger.info(f"[{self.hole_id}] set_color() 调用: {self._color.name()} -> {color.name()}")
        if self._color.rgb() != color.rgb():
            self._color = color
            self.update_appearance()
            
    def paint(self, painter, option, widget=None):
        """重写绘制方法以记录绘制调用"""
        self._paint_count += 1
        actual_color = self.brush().color()
        logger.debug(f"[{self.hole_id}] paint() 第{self._paint_count}次调用, 实际颜色: {actual_color.name()}")
        super().paint(painter, option, widget)
        
        # 绘制调试信息
        painter.setPen(QPen(Qt.white))
        painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self._paint_count))


class TestWidget(QWidget):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.test_items = []
        self.current_test = None
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Qt颜色更新测试")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 图形视图
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, False)
        layout.addWidget(self.view)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.btn_create = QPushButton("创建测试项")
        self.btn_create.clicked.connect(self.create_test_items)
        button_layout.addWidget(self.btn_create)
        
        self.btn_test1 = QPushButton("测试1: 基本颜色更新")
        self.btn_test1.clicked.connect(self.test_basic_color_update)
        button_layout.addWidget(self.btn_test1)
        
        self.btn_test2 = QPushButton("测试2: 快速颜色切换")
        self.btn_test2.clicked.connect(self.test_rapid_color_change)
        button_layout.addWidget(self.btn_test2)
        
        self.btn_test3 = QPushButton("测试3: 定时器颜色更新")
        self.btn_test3.clicked.connect(self.test_timer_color_update)
        button_layout.addWidget(self.btn_test3)
        
        self.btn_test4 = QPushButton("测试4: 强制刷新")
        self.btn_test4.clicked.connect(self.test_force_refresh)
        button_layout.addWidget(self.btn_test4)
        
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def create_test_items(self):
        """创建测试图形项"""
        # 清空现有项
        self.scene.clear()
        self.test_items.clear()
        
        # 创建4个测试项
        positions = [
            (100, 100, "Item1"),
            (200, 100, "Item2"),
            (100, 200, "Item3"),
            (200, 200, "Item4")
        ]
        
        for x, y, item_id in positions:
            item = TestHoleItem(x, y, 30, item_id)
            self.scene.addItem(item)
            self.test_items.append(item)
            
        self.status_label.setText("创建了4个测试项")
        logger.info("测试项创建完成")
        
    def test_basic_color_update(self):
        """测试基本颜色更新"""
        if not self.test_items:
            self.status_label.setText("请先创建测试项")
            return
            
        logger.info("=== 测试1: 基本颜色更新 ===")
        
        # 更新第一个项为蓝色
        self.test_items[0].set_color(QColor(100, 150, 255))
        
        # 检查颜色是否正确设置
        actual_color = self.test_items[0].brush().color()
        logger.info(f"设置后的颜色: {actual_color.name()}")
        
        self.status_label.setText("测试1完成：第一个项应该变为蓝色")
        
    def test_rapid_color_change(self):
        """测试快速颜色切换"""
        if not self.test_items:
            self.status_label.setText("请先创建测试项")
            return
            
        logger.info("=== 测试2: 快速颜色切换 ===")
        
        # 快速切换颜色
        colors = [
            QColor(255, 0, 0),    # 红
            QColor(0, 255, 0),    # 绿
            QColor(0, 0, 255),    # 蓝
            QColor(255, 255, 0),  # 黄
        ]
        
        for i, color in enumerate(colors):
            self.test_items[1].set_color(color)
            QApplication.processEvents()  # 强制处理事件
            
        self.status_label.setText("测试2完成：第二个项应该最终显示黄色")
        
    def test_timer_color_update(self):
        """测试定时器颜色更新（模拟实际场景）"""
        if not self.test_items:
            self.status_label.setText("请先创建测试项")
            return
            
        logger.info("=== 测试3: 定时器颜色更新 ===")
        
        # 模拟检测过程
        item = self.test_items[2]
        
        # 立即设置为蓝色（检测中）
        item.set_color(QColor(33, 150, 243))
        
        # 9.5秒后设置为绿色（完成）
        QTimer.singleShot(2000, lambda: self._finalize_color(item))
        
        self.status_label.setText("测试3运行中：第三个项应该先变蓝，2秒后变绿")
        
    def _finalize_color(self, item):
        """完成颜色更新"""
        logger.info(f"=== 定时器触发：更新{item.hole_id}为绿色 ===")
        item.set_color(QColor(50, 200, 50))
        
        # 多种刷新尝试
        item.update()
        self.scene.update(item.sceneBoundingRect())
        self.view.viewport().update()
        QApplication.processEvents()
        
        logger.info("定时器更新完成")
        
    def test_force_refresh(self):
        """测试强制刷新方法"""
        if not self.test_items:
            self.status_label.setText("请先创建测试项")
            return
            
        logger.info("=== 测试4: 强制刷新 ===")
        
        item = self.test_items[3]
        
        # 设置颜色
        item.set_color(QColor(255, 0, 255))  # 紫色
        
        # 尝试各种刷新方法
        logger.info("尝试方法1: update()")
        item.update()
        
        logger.info("尝试方法2: scene.update()")
        self.scene.update(item.sceneBoundingRect())
        
        logger.info("尝试方法3: viewport().update()")
        self.view.viewport().update()
        
        logger.info("尝试方法4: processEvents()")
        QApplication.processEvents()
        
        logger.info("尝试方法5: repaint()")
        self.view.viewport().repaint()
        
        logger.info("尝试方法6: scene.invalidate()")
        self.scene.invalidate(item.sceneBoundingRect())
        
        self.status_label.setText("测试4完成：第四个项应该显示紫色")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    widget = TestWidget()
    widget.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()