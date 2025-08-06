"""
P2 内窥镜图像显示组件
整合自 modules/endoscope_view.py，专为P2实时监控页面优化
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QToolButton,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QSlider,
    QGroupBox, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer, Slot
from PySide6.QtGui import QPainter, QFont, QPixmap, QImage, QColor
import logging
from pathlib import Path


class EndoscopeView(QWidget):
    """P2专用内窥镜视图组件"""
    
    # 信号定义
    image_captured = Signal(str)  # 图像捕获信号
    view_mode_changed = Signal(str)  # 视图模式改变信号
    brightness_changed = Signal(int)  # 亮度改变信号
    contrast_changed = Signal(int)  # 对比度改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 视图状态
        self.view_mode = "simulation"  # simulation/real
        self.current_image_path = None
        self.brightness = 50
        self.contrast = 50
        
        # 设置UI
        self.setup_ui()
        
        # 模拟更新定时器（仅在模拟模式下使用）
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._update_simulation)
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建内窥镜标题栏
        header_widget = self._create_header()
        layout.addWidget(header_widget)
        
        # 图像显示区域
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setMinimumHeight(300)
        self.graphics_view.setMinimumWidth(400)

        # 设置视图属性
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.graphics_view.setStyleSheet("""
            QGraphicsView {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 5px;
            }
        """)

        # 设置对齐方式
        self.graphics_view.setAlignment(Qt.AlignCenter)

        # 添加占位符文本
        self._setup_placeholder()
        
        layout.addWidget(self.graphics_view)
        
        # 控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

    def _create_header(self):
        """创建标题栏"""
        header = QWidget()
        header.setObjectName("PanelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(10)

        title = QLabel("内窥镜实时图像")
        title.setObjectName("PanelHeaderText")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")

        # 工具按钮
        self.snapshot_button = QToolButton()
        self.snapshot_button.setText("📷")
        self.snapshot_button.setToolTip("保存当前快照")
        self.snapshot_button.clicked.connect(self._save_snapshot)

        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("🔍")
        self.fullscreen_button.setToolTip("全屏查看")
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.fullscreen_button)
        header_layout.addWidget(self.snapshot_button)

        return header

    def _create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("控制面板")
        panel.setMaximumHeight(120)
        layout = QVBoxLayout(panel)
        
        # 第一行：模式选择和捕获
        row1 = QHBoxLayout()
        
        # 视图模式选择
        mode_label = QLabel("模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["模拟视图", "实时图像"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # 捕获按钮
        self.capture_button = QPushButton("捕获图像")
        self.capture_button.clicked.connect(self._capture_image)
        
        row1.addWidget(mode_label)
        row1.addWidget(self.mode_combo)
        row1.addStretch()
        row1.addWidget(self.capture_button)
        
        # 第二行：亮度和对比度控制
        row2 = QHBoxLayout()
        
        # 亮度控制
        brightness_label = QLabel("亮度:")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(self.brightness)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        
        # 对比度控制
        contrast_label = QLabel("对比度:")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 100)
        self.contrast_slider.setValue(self.contrast)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        
        row2.addWidget(brightness_label)
        row2.addWidget(self.brightness_slider)
        row2.addWidget(contrast_label)
        row2.addWidget(self.contrast_slider)
        
        layout.addLayout(row1)
        layout.addLayout(row2)
        
        return panel

    def _setup_placeholder(self):
        """设置占位符文本"""
        self.placeholder_text = QGraphicsTextItem("等待内窥镜图像输入...\n(内表面展开图)")
        self.placeholder_text.setFont(QFont("Arial", 12))
        self.placeholder_text.setDefaultTextColor(Qt.gray)
        self.graphics_scene.addItem(self.placeholder_text)

    def update_image(self, image_data):
        """
        更新图像显示
        
        Args:
            image_data: 图像数据 (QPixmap, QImage, 或文件路径)
        """
        try:
            # 清除占位符
            if self.placeholder_text.scene() == self.graphics_scene:
                self.graphics_scene.removeItem(self.placeholder_text)

            pixmap = self._convert_to_pixmap(image_data)
            if not pixmap or pixmap.isNull():
                self.logger.warning("图像数据无效")
                return

            # 应用亮度和对比度调整
            adjusted_pixmap = self._apply_adjustments(pixmap)
            
            # 清除场景并添加新图像
            self.graphics_scene.clear()
            
            # 缩放图像以适应视图
            scaled_pixmap = self._scale_image(adjusted_pixmap)
            pixmap_item = self.graphics_scene.addPixmap(scaled_pixmap)
            
            # 设置场景矩形
            from PySide6.QtCore import QRectF
            scene_rect = QRectF(scaled_pixmap.rect())
            self.graphics_scene.setSceneRect(scene_rect)
            
            self.logger.debug(f"内窥镜图像更新成功，尺寸: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
        except Exception as e:
            self.logger.error(f"更新内窥镜图像失败: {e}")

    def _convert_to_pixmap(self, image_data):
        """转换图像数据为QPixmap"""
        if isinstance(image_data, QPixmap):
            return image_data
        elif isinstance(image_data, QImage):
            return QPixmap.fromImage(image_data)
        elif isinstance(image_data, str):
            return QPixmap(image_data)
        else:
            self.logger.warning(f"不支持的图像数据类型: {type(image_data)}")
            return None

    def _scale_image(self, pixmap):
        """缩放图像以适应视图"""
        view_size = self.graphics_view.size()
        if view_size.width() > 50 and view_size.height() > 50:
            return pixmap.scaled(
                view_size.width() - 20,
                view_size.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        return pixmap

    def _apply_adjustments(self, pixmap):
        """应用亮度和对比度调整"""
        # 简化的图像调整实现
        # 在实际应用中，这里可以使用更复杂的图像处理算法
        return pixmap

    @Slot(str)
    def _on_mode_changed(self, mode_text):
        """处理模式改变"""
        if mode_text == "模拟视图":
            self.view_mode = "simulation"
            self.simulation_timer.start(1000)  # 1秒更新一次
        else:
            self.view_mode = "real"
            self.simulation_timer.stop()
        
        self.view_mode_changed.emit(self.view_mode)
        self.logger.info(f"内窥镜视图模式切换到: {self.view_mode}")

    @Slot(int)
    def _on_brightness_changed(self, value):
        """处理亮度改变"""
        self.brightness = value
        self.brightness_changed.emit(value)
        # TODO: 重新应用当前图像的亮度调整

    @Slot(int)
    def _on_contrast_changed(self, value):
        """处理对比度改变"""
        self.contrast = value
        self.contrast_changed.emit(value)
        # TODO: 重新应用当前图像的对比度调整

    @Slot()
    def _save_snapshot(self):
        """保存当前快照"""
        try:
            # 创建保存目录
            save_dir = Path("snapshots")
            save_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"endoscope_snapshot_{timestamp}.png"
            filepath = save_dir / filename
            
            # 保存图像
            if self.graphics_scene.items():
                # 从场景渲染图像
                scene_rect = self.graphics_scene.sceneRect()
                pixmap = QPixmap(int(scene_rect.width()), int(scene_rect.height()))
                pixmap.fill(Qt.white)
                
                painter = QPainter(pixmap)
                self.graphics_scene.render(painter)
                painter.end()
                
                if pixmap.save(str(filepath)):
                    self.image_captured.emit(str(filepath))
                    self.logger.info(f"快照已保存: {filepath}")
                else:
                    self.logger.error("快照保存失败")
            else:
                self.logger.warning("没有图像可保存")
                
        except Exception as e:
            self.logger.error(f"保存快照失败: {e}")

    @Slot()
    def _toggle_fullscreen(self):
        """切换全屏显示"""
        # TODO: 实现全屏显示功能
        self.logger.info("全屏功能待实现")

    @Slot()
    def _capture_image(self):
        """捕获图像"""
        if self.view_mode == "simulation":
            self._generate_test_image()
        else:
            # TODO: 从实际设备捕获图像
            self.logger.info("实时图像捕获功能待实现")

    def _update_simulation(self):
        """更新模拟视图"""
        if self.view_mode == "simulation":
            self._generate_test_image()

    def _generate_test_image(self):
        """生成测试图像"""
        try:
            import random
            
            # 创建测试图像
            pixmap = QPixmap(400, 300)
            pixmap.fill(QColor(50, 50, 80))  # 深蓝色背景
            
            painter = QPainter(pixmap)
            
            # 绘制模拟的内窥镜视图
            # 圆形视野
            painter.setBrush(QColor(30, 30, 50))
            painter.setPen(QColor(100, 100, 150))
            center_x, center_y = 200, 150
            radius = 120
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            
            # 随机绘制一些模拟缺陷或特征
            painter.setBrush(QColor(200, 50, 50))
            for _ in range(3):
                x = center_x + random.randint(-80, 80)
                y = center_y + random.randint(-80, 80)
                size = random.randint(5, 15)
                painter.drawEllipse(x - size//2, y - size//2, size, size)
            
            # 添加时间戳
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 10))
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            painter.drawText(10, 20, f"模拟时间: {timestamp}")
            
            painter.end()
            
            self.update_image(pixmap)
            
        except Exception as e:
            self.logger.error(f"生成测试图像失败: {e}")

    def clear_image(self):
        """清除图像并恢复占位符"""
        self.graphics_scene.clear()
        self._setup_placeholder()

    def set_hole_id(self, hole_id):
        """设置当前检测的孔ID"""
        # 可以在UI中显示当前孔位信息
        self.logger.debug(f"设置当前孔位: {hole_id}")

    def start_acquisition(self):
        """开始图像采集"""
        self.logger.info("开始内窥镜图像采集")
        if self.view_mode == "simulation":
            self.simulation_timer.start(1000)

    def stop_acquisition(self):
        """停止图像采集"""
        self.logger.info("停止内窥镜图像采集")
        self.simulation_timer.stop()

    def get_view_mode(self):
        """获取当前视图模式"""
        return self.view_mode

    def set_view_mode(self, mode):
        """设置视图模式"""
        if mode in ["simulation", "real"]:
            index = 0 if mode == "simulation" else 1
            self.mode_combo.setCurrentIndex(index)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 设置日志
    logging.basicConfig(level=logging.DEBUG)
    
    view = EndoscopeView()
    view.show()
    
    # 启动模拟模式
    view.set_view_mode("simulation")
    view.start_acquisition()
    
    sys.exit(app.exec())