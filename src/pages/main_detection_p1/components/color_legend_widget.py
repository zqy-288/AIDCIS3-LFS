"""
颜色图例组件
显示孔位状态的颜色图例，用于视图模式按钮旁边的说明
"""

import logging
from typing import List, Dict, Any

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPalette

# 导入孔位状态定义
try:
    from src.shared.models.hole_data import HoleStatus
    from src.pages.main_detection_p1.graphics.core.hole_item import HoleGraphicsItem
    HAS_HOLE_STATUS = True
except ImportError:
    HAS_HOLE_STATUS = False


class ColorLegendItem(QWidget):
    """单个颜色图例项"""
    
    def __init__(self, color: str, label: str, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.label_text = label
        self.setFixedSize(80, 20)
        self.setToolTip(f"{label}: {color}")
        
    def paintEvent(self, event):
        """绘制颜色方块和标签"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制颜色方块
        color_rect_size = 12
        color_rect = self.rect().adjusted(2, 4, -self.width() + color_rect_size + 2, -4)
        
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRoundedRect(color_rect, 2, 2)
        
        # 绘制标签文字
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QPen(Qt.black))
        
        text_rect = self.rect().adjusted(color_rect_size + 6, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.label_text)
        
        painter.end()


class ColorLegendWidget(QWidget):
    """颜色图例组件"""
    
    def __init__(self, parent=None, layout_direction="horizontal"):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.layout_direction = layout_direction
        self.hole_statuses = []
        
        self.setup_ui()
        self.load_hole_statuses()
        self.create_legend_items()
        
    def setup_ui(self):
        """设置UI布局"""
        if self.layout_direction == "horizontal":
            self.layout = QHBoxLayout(self)
        else:
            self.layout = QVBoxLayout(self)
            
        self.layout.setContentsMargins(5, 2, 5, 2)
        self.layout.setSpacing(8)
        
        # 添加标题
        title_label = QLabel("图例:")
        title_font = QFont("Arial", 9, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #333333;")
        self.layout.addWidget(title_label)
        
    def load_hole_statuses(self):
        """加载孔位状态配置"""
        try:
            if HAS_HOLE_STATUS:
                # 使用项目中已定义的状态颜色
                status_colors = HoleGraphicsItem.STATUS_COLORS
                
                # 定义状态显示名称
                status_names = {
                    HoleStatus.PENDING: "待检",
                    HoleStatus.PROCESSING: "检测中", 
                    HoleStatus.QUALIFIED: "合格",
                    HoleStatus.DEFECTIVE: "异常",
                    HoleStatus.BLIND: "盲孔",
                    HoleStatus.TIE_ROD: "拉杆孔"
                }
                
                self.hole_statuses = []
                for status, color in status_colors.items():
                    self.hole_statuses.append({
                        "status": status,
                        "display_name": status_names.get(status, status.value),
                        "color": f"#{color.red():02X}{color.green():02X}{color.blue():02X}",
                        "qcolor": color
                    })
                    
                self.logger.info(f"✅ 加载了 {len(self.hole_statuses)} 个孔位状态")
            else:
                self.logger.warning("⚠️ 无法导入孔位状态定义，使用默认状态")
                self._create_default_statuses()
                
        except Exception as e:
            self.logger.error(f"❌ 加载孔位状态失败: {e}")
            self._create_default_statuses()
            
    def _create_default_statuses(self):
        """创建默认的孔位状态"""
        self.hole_statuses = [
            {"display_name": "待检", "color": "#C8C8C8"},
            {"display_name": "检测中", "color": "#6496FF"},
            {"display_name": "合格", "color": "#32C832"},
            {"display_name": "异常", "color": "#FF3232"},
            {"display_name": "盲孔", "color": "#FFC832"},
            {"display_name": "拉杆孔", "color": "#64FF64"}
        ]
        
    def create_legend_items(self):
        """创建图例项"""
        try:
            # 只显示前4个主要状态，避免图例过长
            main_statuses = self.hole_statuses[:4]
            
            for status_info in main_statuses:
                color = status_info.get("color", "#808080")
                label = status_info.get("display_name", "未知")
                
                legend_item = ColorLegendItem(color, label, self)
                self.layout.addWidget(legend_item)
                    
            # 添加弹性空间
            self.layout.addStretch()
            
            self.logger.info(f"✅ 创建了 {len(main_statuses)} 个状态图例项")
            
        except Exception as e:
            self.logger.error(f"❌ 创建图例项失败: {e}")
            
    def update_statuses(self, statuses: List[Dict[str, Any]]):
        """更新孔位状态"""
        self.hole_statuses = statuses
        
        # 清除现有的图例项
        for i in reversed(range(self.layout.count())):
            child = self.layout.itemAt(i).widget()
            if isinstance(child, ColorLegendItem):
                child.setParent(None)
                
        # 重新创建图例项
        self.create_legend_items()


class CompactColorLegendWidget(QWidget):
    """紧凑型颜色图例组件 - 适合按钮旁边显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.setFixedHeight(40)  # 进一步增加高度
        self.hole_statuses = []
        
        self.setup_ui()
        self.load_hole_statuses()
        
    def setup_ui(self):
        """设置UI布局"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)  # 更大的边距
        self.layout.setSpacing(12)  # 更大的间距
        
        # 添加图例标题
        title_label = QLabel("状态:")
        title_font = QFont("Arial", 11, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #FFFFFF; 
            background: transparent;
            margin-right: 5px;
        """)
        self.layout.addWidget(title_label)
        
    def load_hole_statuses(self):
        """加载孔位状态配置"""
        try:
            if HAS_HOLE_STATUS:
                # 使用项目中已定义的状态颜色
                status_colors = HoleGraphicsItem.STATUS_COLORS
                
                # 定义状态显示名称
                status_names = {
                    HoleStatus.PENDING: "待检",
                    HoleStatus.PROCESSING: "检测中", 
                    HoleStatus.QUALIFIED: "合格",
                    HoleStatus.DEFECTIVE: "异常",
                    HoleStatus.BLIND: "盲孔",
                    HoleStatus.TIE_ROD: "拉杆孔"
                }
                
                # 只取前3个主要状态，保持紧凑
                main_statuses = list(status_colors.items())[:3]
                
                for status, color in main_statuses:
                    self.create_compact_item(
                        f"#{color.red():02X}{color.green():02X}{color.blue():02X}",
                        status_names.get(status, status.value)
                    )
                        
                self.logger.info(f"✅ 创建了紧凑图例，显示 {len(main_statuses)} 个状态")
                
            else:
                self.logger.warning("⚠️ 使用默认状态")
                self._create_default_items()
                
        except Exception as e:
            self.logger.error(f"❌ 加载紧凑图例失败: {e}")
            self._create_default_items()
            
    def _create_default_items(self):
        """创建默认图例项"""
        default_items = [
            ("#C8C8C8", "待检"),
            ("#6496FF", "检测中"),
            ("#32C832", "合格")
        ]
        
        for color, label in default_items:
            self.create_compact_item(color, label)
            
    def create_compact_item(self, color: str, label: str):
        """创建清晰的图例项"""
        # 创建一个容器widget
        item_container = QWidget()
        item_layout = QHBoxLayout(item_container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(6)
        
        # 创建颜色方块label
        color_label = QLabel()
        color_label.setFixedSize(18, 18)  # 稍微调整大小
        color_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border: 2px solid #FFFFFF;
                border-radius: 3px;
            }}
        """)
        color_label.setToolTip(f"{label}: {color}")
        
        # 创建文字label - 确保白色文字可见
        text_label = QLabel(label)
        text_label.setFont(QFont("Arial", 9, QFont.Bold))
        
        # 设置强制白色文字
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        
        # 额外设置调色板确保文字可见
        palette = text_label.palette()
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        text_label.setPalette(palette)
        text_label.setAutoFillBackground(False)
        
        text_label.setToolTip(f"{label}: {color}")
        
        item_layout.addWidget(color_label)
        item_layout.addWidget(text_label)
        
        self.layout.addWidget(item_container)


if __name__ == "__main__":
    """测试组件"""
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("颜色图例测试")
    window.resize(400, 200)
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # 测试标准图例
    legend1 = ColorLegendWidget(layout_direction="horizontal")
    layout.addWidget(legend1)
    
    # 测试紧凑图例
    legend2 = CompactColorLegendWidget()
    layout.addWidget(legend2)
    
    window.setCentralWidget(central_widget)
    window.show()
    
    sys.exit(app.exec())