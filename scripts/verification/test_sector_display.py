#!/usr/bin/env python3
"""
真正的扇形显示测试 - 使用DynamicSectorDisplayWidget
参考老版本main.py的实现方式
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
test_logger = logging.getLogger(__name__)

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QSlider, QCheckBox,
    QGroupBox, QProgressBar, QTextEdit, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot as pyqtSlot
from PySide6.QtGui import QFont, QColor

# 项目导入 - 使用真正的扇形显示组件
from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from src.controllers.main_window_controller import MainWindowController


class RealSectorDisplayTest(QMainWindow):
    """真正的扇形显示测试 - 参考main.py实现"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("真正的扇形显示测试 - DynamicSectorDisplayWidget")
        self.setGeometry(100, 100, 1400, 900)
        
        # 数据
        self.hole_collection = None
        self.main_controller = None
        
        # DXF文件路径
        self.dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        # 设置UI
        self._setup_ui()
        
        # 应用样式
        self._apply_theme()
        
        test_logger.info("🚀 真正的扇形显示测试界面初始化完成")
    
    def _setup_ui(self):
        """设置用户界面 - 参考main.py布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 水平分割
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧 - 真正的扇形显示区域（参考main.py）
        sector_container = QWidget()
        sector_container_layout = QVBoxLayout(sector_container)
        sector_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 动态扇形区域显示（主要显示区域）- 直接填满整个可用空间
        self.dynamic_sector_display = DynamicSectorDisplayWidget()
        self.dynamic_sector_display.setMinimumSize(800, 700)  # 参考main.py设置
        
        # 直接添加主视图，让它填满整个容器
        sector_container_layout.addWidget(self.dynamic_sector_display)
        
        splitter.addWidget(sector_container)
        
        # 设置分割比例：控制面板30%，扇形显示70%
        splitter.setSizes([400, 1000])
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("🎯 真正的扇形显示测试")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 加载控制组
        load_group = QGroupBox("🔄 加载控制")
        load_layout = QVBoxLayout(load_group)
        
        self.load_button = QPushButton("加载CAP1000.dxf到扇形显示")
        self.load_button.clicked.connect(self._load_dxf_data)
        load_layout.addWidget(self.load_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        load_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("状态: 未加载")
        load_layout.addWidget(self.status_label)
        
        layout.addWidget(load_group)
        
        # 扇形控制组
        sector_group = QGroupBox("🎨 扇形控制")
        sector_layout = QVBoxLayout(sector_group)
        
        # 扇形切换按钮
        sector1_btn = QPushButton("扇形1")
        sector2_btn = QPushButton("扇形2") 
        sector3_btn = QPushButton("扇形3")
        sector4_btn = QPushButton("扇形4")
        
        for btn in [sector1_btn, sector2_btn, sector3_btn, sector4_btn]:
            sector_layout.addWidget(btn)
        
        layout.addWidget(sector_group)
        
        # 日志显示
        log_group = QGroupBox("📝 日志信息")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        return panel
    
    def _apply_theme(self):
        """应用主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #999;
            }
        """)
    
    def _load_dxf_data(self):
        """加载DXF数据到扇形显示"""
        test_logger.info("🔍 开始加载DXF数据到扇形显示...")
        
        if not os.path.exists(self.dxf_path):
            self._log_message(f"❌ DXF文件不存在: {self.dxf_path}")
            return
        
        self.status_label.setText("状态: 加载中...")
        self.load_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        try:
            # 使用主控制器加载数据
            from src.controllers.main_window_controller import MainWindowController
            if not self.main_controller:
                self.main_controller = MainWindowController()
                test_logger.info("✅ MainWindowController创建成功")
            
            # 选择CAP1000产品
            success = self.main_controller.select_product("CAP1000")
            if not success:
                self._log_message("❌ 选择CAP1000产品失败")
                return
                
            test_logger.info("✅ CAP1000产品选择成功")
            
            # 获取孔位集合
            self.hole_collection = self.main_controller.get_hole_collection()
            if self.hole_collection:
                hole_count = len(self.hole_collection.holes)
                test_logger.info(f"✅ 获取到 {hole_count} 个孔位")
                
                # 将数据加载到扇形显示组件
                self.dynamic_sector_display.set_hole_collection(self.hole_collection)
                
                self.status_label.setText(f"状态: 已加载 {hole_count} 个孔位")
                self._log_message(f"✅ 成功加载 {hole_count} 个孔位到扇形显示")
            else:
                self._log_message("❌ 未获取到孔位数据")
                
        except Exception as e:
            test_logger.error(f"❌ 加载失败: {e}")
            self._log_message(f"❌ 加载失败: {e}")
            import traceback
            test_logger.error(f"详细错误: {traceback.format_exc()}")
        finally:
            self.load_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _log_message(self, message: str):
        """添加日志消息"""
        self.log_text.append(message)
        test_logger.info(message)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("真正的扇形显示测试")
    app.setApplicationVersion("1.0")
    
    try:
        window = RealSectorDisplayTest()
        window.show()
        
        test_logger.info("🎬 真正的扇形显示测试界面启动完成")
        
        return app.exec()
    except Exception as e:
        test_logger.error(f"❌ 应用程序启动失败: {e}")
        import traceback
        test_logger.error(f"详细错误: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())