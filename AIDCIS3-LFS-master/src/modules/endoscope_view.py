"""
内窥镜图像显示组件
(此部分已留白，用于集成外部图像处理算法)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QToolButton,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont


class EndoscopeView(QWidget):
    """内窥镜视图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建内窥镜标题栏
        endo_header = QWidget()
        endo_header.setObjectName("PanelHeader")
        endo_header_layout = QHBoxLayout(endo_header)
        endo_header_layout.setContentsMargins(15, 0, 15, 0)  # 左右留边距
        endo_header_layout.setSpacing(10)

        endo_title = QLabel("内窥镜实时图像 - 内表面展开图")
        endo_title.setObjectName("PanelHeaderText")

        # 添加工具按钮
        save_snapshot_button = QToolButton()
        save_snapshot_button.setObjectName("HeaderToolButton")
        save_snapshot_button.setText("📷")  # 使用emoji作为图标
        save_snapshot_button.setToolTip("保存当前快照")

        fullscreen_button = QToolButton()
        fullscreen_button.setObjectName("HeaderToolButton")
        fullscreen_button.setText("🔍")  # 使用emoji作为图标
        fullscreen_button.setToolTip("全屏查看")

        endo_header_layout.addWidget(endo_title)
        endo_header_layout.addStretch()
        endo_header_layout.addWidget(fullscreen_button)
        endo_header_layout.addWidget(save_snapshot_button)

        # 将标题栏添加到布局
        layout.addWidget(endo_header)
        
        # 图像显示区域 - 增大尺寸以获得更好的视觉效果
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setMinimumHeight(400)  # 增加最小高度
        self.graphics_view.setMinimumWidth(600)   # 设置最小宽度

        # 设置视图属性
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.SmoothPixmapTransform)  # 平滑图像变换
        self.graphics_view.setStyleSheet("""
                QGraphicsView {
        background-color: #ffffff;  // 白色背景
        border: 2px solid #555;
        border-radius: 5px;
                    }
                                """)

        # 设置对齐方式 - 图像左对齐以增强动感
        self.graphics_view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 添加提示信息
        self.placeholder_text = QGraphicsTextItem("等待内窥镜图像输入...\n(内表面展开图)")
        self.placeholder_text.setFont(QFont("Arial", 14))
        self.placeholder_text.setDefaultTextColor(Qt.gray)
        self.graphics_scene.addItem(self.placeholder_text)
        
        layout.addWidget(self.graphics_view)
        
        # 控制面板已被移除
        # 不再显示控制面板按钮
        


    def update_image(self, image_data):
        """
        更新图像显示的公共接口。
        外部算法应调用此方法来显示新的图像。

        Args:
            image_data: 图像数据 (例如, QPixmap, QImage, or a numpy array).
        """
        # 清除占位符文本
        if self.placeholder_text.scene() == self.graphics_scene:
            self.graphics_scene.removeItem(self.placeholder_text)

        # 处理和显示图像数据
        from PySide6.QtGui import QPixmap, QImage

        try:
            if isinstance(image_data, QPixmap):
                pixmap = image_data
            elif isinstance(image_data, QImage):
                pixmap = QPixmap.fromImage(image_data)
            elif isinstance(image_data, str):
                # 如果是文件路径
                pixmap = QPixmap(image_data)
            else:
                print(f"⚠️ 不支持的图像数据类型: {type(image_data)}")
                return

            if not pixmap.isNull():
                # 清除场景并添加新图像
                self.graphics_scene.clear()

                # 缩放图像以获得更好的显示效果
                view_size = self.graphics_view.size()
                # 确保视图大小有效
                if view_size.width() > 50 and view_size.height() > 50:
                    scaled_pixmap = pixmap.scaled(
                        view_size.width() - 20,  # 留一些边距
                        view_size.height() - 20,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                else:
                    # 如果视图尺寸无效，使用原始图像
                    scaled_pixmap = pixmap

                pixmap_item = self.graphics_scene.addPixmap(scaled_pixmap)

                # 设置场景矩形以确保左对齐
                from PySide6.QtCore import QRectF
                scene_rect = QRectF(scaled_pixmap.rect())
                self.graphics_scene.setSceneRect(scene_rect)

                # 确保图像左对齐显示，增强动感效果
                self.graphics_view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.graphics_view.ensureVisible(scene_rect, 0, 0)  # 确保左上角可见

                print(f"✅ 内窥镜图像更新成功，尺寸: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            else:
                print("❌ 图像数据无效")

        except Exception as e:
            print(f"❌ 更新内窥镜图像失败: {e}")

    def load_image_from_file(self, file_path):
        """从文件加载图像"""
        self.update_image(file_path)
        
    def clear_image(self):
        """清除图像并恢复占位符"""
        self.graphics_scene.clear()
        self.placeholder_text = QGraphicsTextItem("等待内窥镜图像输入...\n(内表面展开图)")
        self.placeholder_text.setFont(QFont("Arial", 14))
        self.placeholder_text.setDefaultTextColor(Qt.gray)
        self.graphics_scene.addItem(self.placeholder_text)

    def set_hole_id(self, hole_id):
        """设置当前检测的孔ID"""
        # 可以在此更新UI以反映当前正在处理的孔
        pass
        
    def start_acquisition(self):
        """开始图像采集"""
        print("📸 开始内窥镜图像采集")
        # 实际的图像采集逻辑可以在这里实现
        pass
        
    def stop_acquisition(self):
        """停止图像采集"""
        print("⏹️ 停止内窥镜图像采集")
        # 停止图像采集的逻辑
        pass

    def test_image_display(self):
        """测试图像显示功能"""
        print("🧪 测试图像显示功能")

        # 创建一个简单的测试图像
        from PySide6.QtGui import QPixmap, QPainter, QColor
        from PySide6.QtCore import QRect

        # 创建一个200x200的测试图像
        test_pixmap = QPixmap(200, 200)
        test_pixmap.fill(QColor(100, 150, 200))  # 蓝色背景

        # 在图像上绘制一些内容
        painter = QPainter(test_pixmap)
        painter.setPen(QColor(255, 255, 255))  # 白色文字
        painter.drawText(QRect(0, 0, 200, 200), Qt.AlignCenter, "测试图像\nTest Image")
        painter.end()

        # 显示测试图像
        self.update_image(test_pixmap)
        print("✅ 测试图像已发送到显示组件")




if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    view = EndoscopeView()
    view.show()
    sys.exit(app.exec())