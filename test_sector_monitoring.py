#!/usr/bin/env python3
"""监控扇形显示的所有缩放变化"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import QTimer, Qt
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant
from aidcis2.graphics.graphics_view import OptimizedGraphicsView

# 保存原始方法
_original_scale = OptimizedGraphicsView.scale
_original_fitInView = OptimizedGraphicsView.fitInView
_original_resetTransform = OptimizedGraphicsView.resetTransform
_original_centerOn = OptimizedGraphicsView.centerOn
_original_fit_to_window_width = OptimizedGraphicsView.fit_to_window_width

# 日志输出
log_output = None

def log_message(msg):
    """记录消息"""
    print(msg)
    if log_output:
        log_output.append(msg)

# 装饰器方法
def monitored_scale(self, sx, sy):
    """监控scale调用"""
    import traceback
    caller = traceback.extract_stack()[-2]
    log_message(f"🔍 scale({sx:.3f}, {sy:.3f}) called from {caller.filename}:{caller.lineno}")
    return _original_scale(self, sx, sy)

def monitored_fitInView(self, rect, aspectRatioMode=Qt.KeepAspectRatio):
    """监控fitInView调用"""
    import traceback
    caller = traceback.extract_stack()[-2]
    log_message(f"🔍 fitInView() called from {caller.filename}:{caller.lineno}")
    return _original_fitInView(self, rect, aspectRatioMode)

def monitored_resetTransform(self):
    """监控resetTransform调用"""
    import traceback
    caller = traceback.extract_stack()[-2]
    log_message(f"🔍 resetTransform() called from {caller.filename}:{caller.lineno}")
    return _original_resetTransform(self)

def monitored_centerOn(self, *args):
    """监控centerOn调用"""
    import traceback
    caller = traceback.extract_stack()[-2]
    log_message(f"🔍 centerOn() called from {caller.filename}:{caller.lineno}")
    return _original_centerOn(self, *args)

def monitored_fit_to_window_width(self):
    """监控fit_to_window_width调用"""
    import traceback
    caller = traceback.extract_stack()[-2]
    disable_auto_fit = getattr(self, 'disable_auto_fit', False)
    log_message(f"🔍 fit_to_window_width() called from {caller.filename}:{caller.lineno}, disable_auto_fit={disable_auto_fit}")
    return _original_fit_to_window_width(self)

# 替换方法
OptimizedGraphicsView.scale = monitored_scale
OptimizedGraphicsView.fitInView = monitored_fitInView
OptimizedGraphicsView.resetTransform = monitored_resetTransform
OptimizedGraphicsView.centerOn = monitored_centerOn
OptimizedGraphicsView.fit_to_window_width = monitored_fit_to_window_width

class MonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形缩放监控")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建动态扇形显示
        self.dynamic_display = DynamicSectorDisplayWidget()
        self.dynamic_display.setStyleSheet("background-color: white; border: 2px solid #333;")
        self.dynamic_display.setFixedHeight(500)
        layout.addWidget(self.dynamic_display)
        
        # 创建日志输出
        global log_output
        log_output = QTextEdit()
        log_output.setReadOnly(True)
        log_output.setMaximumHeight(300)
        layout.addWidget(log_output)
        
    def load_and_test(self):
        """加载并测试"""
        log_message("\n" + "="*60)
        log_message("开始监控扇形显示")
        log_message("="*60 + "\n")
        
        # 加载DXF
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        loader = LegacyDXFLoader()
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            log_message(f"✅ 加载了 {len(hole_collection)} 个孔位")
            self.dynamic_display.set_hole_collection(hole_collection)
            
            # 延迟切换到扇形4
            QTimer.singleShot(1000, lambda: self.test_sector_4())
    
    def test_sector_4(self):
        """测试扇形4"""
        log_message("\n" + "="*60)
        log_message("切换到扇形4")
        log_message("="*60 + "\n")
        
        self.dynamic_display.switch_to_sector(SectorQuadrant.SECTOR_4)
        
        # 3秒后报告最终状态
        QTimer.singleShot(3000, self.report_final_state)
    
    def report_final_state(self):
        """报告最终状态"""
        log_message("\n" + "="*60)
        log_message("最终状态")
        log_message("="*60)
        
        view = self.dynamic_display.graphics_view
        scale = view.transform().m11()
        view_size = view.viewport().size()
        scene_rect = view.sceneRect()
        
        log_message(f"最终缩放: {scale:.3f}x")
        log_message(f"视图大小: {view_size.width()}x{view_size.height()}")
        log_message(f"场景矩形: {scene_rect}")
        log_message("="*60 + "\n")

def main():
    app = QApplication(sys.argv)
    
    window = MonitorWindow()
    window.show()
    
    # 开始测试
    QTimer.singleShot(100, window.load_and_test)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()