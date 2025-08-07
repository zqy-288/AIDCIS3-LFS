#!/usr/bin/env python3
"""
监控模拟检测的时序，确保严格的10秒间隔
"""

import sys
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QObject, Slot
from src.pages.main_detection_p1.components.simulation_controller import SimulationController
from src.core_business.models.hole_data import HoleCollection

class TimingMonitor(QObject):
    """时序监控器"""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.start_time = None
        self.event_log = []
        self.last_process_time = None
        self.last_finalize_time = None
        
    def log_event(self, event_type, details=""):
        """记录事件和时间"""
        if self.start_time is None:
            self.start_time = time.time()
            
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 计算间隔
        interval_info = ""
        current_time = time.time()
        
        if event_type == "PROCESS_NEXT":
            if self.last_process_time:
                interval = current_time - self.last_process_time
                interval_info = f" [间隔: {interval:.1f}秒]"
            self.last_process_time = current_time
            
        elif event_type == "FINALIZE":
            if self.last_finalize_time:
                interval = current_time - self.last_finalize_time
                interval_info = f" [间隔: {interval:.1f}秒]"
            self.last_finalize_time = current_time
        
        log_entry = f"[{elapsed:6.1f}s] {timestamp} - {event_type}: {details}{interval_info}"
        self.event_log.append(log_entry)
        self.text_widget.append(log_entry)
        
        # 分析时序问题
        if len(self.event_log) > 10 and event_type == "PROCESS_NEXT":
            self.analyze_timing()
    
    def analyze_timing(self):
        """分析时序是否正确"""
        # 检查最近的几个PROCESS_NEXT事件
        process_events = [e for e in self.event_log if "PROCESS_NEXT" in e]
        if len(process_events) >= 3:
            # 提取时间戳
            recent = process_events[-3:]
            self.text_widget.append("\n=== 时序分析 ===")
            for event in recent:
                self.text_widget.append(event)
            self.text_widget.append("================\n")

class MonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("模拟检测时序监控")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 控制按钮
        self.start_btn = QPushButton("开始监控模拟")
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)
        
        # 创建监控器
        self.monitor = TimingMonitor(self.log_text)
        
        # 创建模拟控制器
        self.sim_controller = SimulationController()
        
        # 拦截关键方法来监控时序
        self.hook_methods()
        
    def hook_methods(self):
        """钩子方法来监控时序"""
        # 保存原始方法
        self.original_process_next = self.sim_controller._process_next_pair
        self.original_finalize = self.sim_controller._finalize_current_pair_status
        self.original_start_detection = self.sim_controller._start_pair_detection
        
        # 替换为监控版本
        def monitored_process_next():
            unit_index = self.sim_controller.current_index + 1
            self.monitor.log_event("PROCESS_NEXT", f"处理单元 {unit_index}")
            return self.original_process_next()
            
        def monitored_finalize():
            self.monitor.log_event("FINALIZE", "状态确定（9.5秒定时器）")
            return self.original_finalize()
            
        def monitored_start_detection(hole_pair):
            holes = [h.hole_id for h in hole_pair.holes]
            self.monitor.log_event("START_DETECT", f"开始检测 {holes}")
            return self.original_start_detection(hole_pair)
        
        self.sim_controller._process_next_pair = monitored_process_next
        self.sim_controller._finalize_current_pair_status = monitored_finalize
        self.sim_controller._start_pair_detection = monitored_start_detection
        
    def start_monitoring(self):
        """开始监控"""
        self.log_text.clear()
        self.monitor.log_event("START", "开始模拟检测监控")
        
        # 创建测试数据
        from src.services.dxf_service import DXFService
        dxf_service = DXFService()
        
        # 使用较小的测试文件
        test_file = project_root / "test_data" / "cap1000.dxf"
        if not test_file.exists():
            self.monitor.log_event("ERROR", "找不到测试文件")
            return
            
        hole_collection = dxf_service.load_dxf_file(str(test_file))
        if not hole_collection:
            self.monitor.log_event("ERROR", "加载DXF文件失败")
            return
            
        self.monitor.log_event("INFO", f"加载了 {len(hole_collection.holes)} 个孔位")
        
        # 启动模拟
        self.sim_controller.load_hole_collection(hole_collection)
        self.sim_controller.start_simulation()
        
        self.monitor.log_event("INFO", "模拟已启动，监控时序...")

def main():
    app = QApplication(sys.argv)
    window = MonitorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()