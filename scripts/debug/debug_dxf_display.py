#!/usr/bin/env python3
"""
调试DXF显示问题
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from aidcis2.dxf_parser import DXFParser
from aidcis2.graphics.graphics_view import OptimizedGraphicsView

class DebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DXF显示调试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置日志
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # 创建DXF解析器
        self.dxf_parser = DXFParser()
        
        # 创建UI
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("准备加载DXF文件...")
        layout.addWidget(self.status_label)
        
        # 加载按钮
        load_btn = QPushButton("加载测试DXF文件")
        load_btn.clicked.connect(self.load_test_dxf)
        layout.addWidget(load_btn)
        
        # 图形视图
        self.graphics_view = OptimizedGraphicsView()
        layout.addWidget(self.graphics_view)
        
    def load_test_dxf(self):
        """加载测试DXF文件"""
        test_files = [
            "测试管板.dxf",
            "DXF Graph/东重管板.dxf"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                self.status_label.setText(f"正在加载: {test_file}")
                try:
                    # 解析DXF文件
                    self.logger.info(f"开始解析: {test_file}")
                    hole_collection = self.dxf_parser.parse_file(test_file)
                    
                    if hole_collection and len(hole_collection) > 0:
                        self.status_label.setText(f"成功解析 {len(hole_collection)} 个孔位")
                        self.logger.info(f"解析成功，孔位数量: {len(hole_collection)}")
                        
                        # 显示孔位信息
                        for i, hole in enumerate(hole_collection):
                            if i < 5:  # 只显示前5个
                                self.logger.info(f"孔位 {i}: ID={hole.hole_id}, 位置=({hole.center_x:.3f}, {hole.center_y:.3f}), 半径={hole.radius:.3f}")
                        
                        # 加载到图形视图
                        self.graphics_view.load_holes(hole_collection)
                        self.status_label.setText(f"已加载 {len(hole_collection)} 个孔位到图形视图")
                        return
                    else:
                        self.status_label.setText(f"文件 {test_file} 中未找到孔位")
                        self.logger.warning(f"文件 {test_file} 中未找到孔位")
                        
                except Exception as e:
                    error_msg = f"加载 {test_file} 失败: {str(e)}"
                    self.status_label.setText(error_msg)
                    self.logger.error(error_msg, exc_info=True)
            else:
                self.logger.info(f"文件不存在: {test_file}")
        
        self.status_label.setText("未找到可用的测试DXF文件")

def main():
    app = QApplication(sys.argv)
    
    window = DebugWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
