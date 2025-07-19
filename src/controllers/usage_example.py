"""
控制器使用示例
展示如何在主窗口中集成和使用控制器系统
"""

from typing import Optional
import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer

from ..core.application import ApplicationCore, EventBus, ApplicationEvent
from ..core.dependency_injection import DependencyContainer
from ..core_business.models.hole_data import HoleData, HoleStatus
from .main_detection_coordinator import MainDetectionCoordinator


class ExampleMainWindow(QMainWindow):
    """
    示例主窗口类
    展示如何集成和使用控制器系统
    """
    
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        self.app_core = app_core
        self.event_bus = app_core.event_bus
        self.container = app_core.container
        self.logger = logging.getLogger(__name__)
        
        # 主检测协调器
        self.detection_coordinator: Optional[MainDetectionCoordinator] = None
        
        # 初始化UI
        self._setup_ui()
        
        # 初始化控制器系统
        self._setup_controllers()
        
        # 设置事件连接
        self._setup_event_connections()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 控制按钮
        self.start_btn = QPushButton("开始检测")
        self.start_btn.clicked.connect(self._start_detection)
        layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("暂停检测")
        self.pause_btn.clicked.connect(self._pause_detection)
        layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("恢复检测")
        self.resume_btn.clicked.connect(self._resume_detection)
        layout.addWidget(self.resume_btn)
        
        self.stop_btn = QPushButton("停止检测")
        self.stop_btn.clicked.connect(self._stop_detection)
        layout.addWidget(self.stop_btn)
        
        # 进度标签
        self.progress_label = QLabel("进度: 0%")
        layout.addWidget(self.progress_label)
        
        # 统计标签
        self.stats_label = QLabel("统计信息: 无")
        layout.addWidget(self.stats_label)
    
    def _setup_controllers(self):
        """设置控制器系统"""
        try:
            # 创建主检测协调器
            self.detection_coordinator = MainDetectionCoordinator(
                self.event_bus, 
                self.container,
                self
            )
            
            # 启动协调器
            self.detection_coordinator.start_coordination({
                "detection": {
                    "interval": 50,  # 50ms检测间隔
                    "hole_detection_time": 25,  # 25ms单孔检测时间
                    "success_rate": 0.85  # 85%成功率
                }
            })
            
            self.logger.info("控制器系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化控制器系统失败: {e}")
            self.status_label.setText(f"初始化失败: {e}")
    
    def _setup_event_connections(self):
        """设置事件连接"""
        if not self.detection_coordinator:
            return
        
        # 连接协调器信号
        self.detection_coordinator.coordination_started.connect(
            lambda: self.status_label.setText("协调器已启动")
        )
        
        self.detection_coordinator.coordination_error.connect(
            lambda error_type, message: self.status_label.setText(f"协调器错误: {error_type} - {message}")
        )
        
        # 连接检测控制器信号
        detection_controller = self.detection_coordinator.detection_controller
        if detection_controller:
            detection_controller.detection_started.connect(
                lambda info: self.status_label.setText(f"检测开始: {info.get('total_holes', 0)} 个孔位")
            )
            
            detection_controller.detection_progress.connect(
                self._update_progress
            )
            
            detection_controller.detection_completed.connect(
                lambda info: self.status_label.setText(f"检测完成: 成功率 {info.get('success_rate', 0):.1f}%")
            )
            
            detection_controller.detection_paused.connect(
                lambda info: self.status_label.setText("检测已暂停")
            )
            
            detection_controller.detection_resumed.connect(
                lambda info: self.status_label.setText("检测已恢复")
            )
        
        # 连接侧边栏控制器信号
        sidebar_controller = self.detection_coordinator.sidebar_controller
        if sidebar_controller:
            sidebar_controller.statistics_updated.connect(
                self._update_statistics
            )
            
            sidebar_controller.hole_info_requested.connect(
                lambda hole_id: self.status_label.setText(f"请求孔位信息: {hole_id}")
            )
    
    def _start_detection(self):
        """开始检测"""
        try:
            # 创建模拟孔位数据
            holes = self._create_sample_holes()
            
            if self.detection_coordinator:
                success = self.detection_coordinator.execute_coordinated_detection(holes, {
                    "interval": 100,
                    "hole_detection_time": 50,
                    "success_rate": 0.9
                })
                
                if success:
                    self.status_label.setText("检测启动成功")
                else:
                    self.status_label.setText("检测启动失败")
            
        except Exception as e:
            self.logger.error(f"开始检测失败: {e}")
            self.status_label.setText(f"开始检测失败: {e}")
    
    def _pause_detection(self):
        """暂停检测"""
        if self.detection_coordinator and self.detection_coordinator.detection_controller:
            self.detection_coordinator.detection_controller.pause_detection()
    
    def _resume_detection(self):
        """恢复检测"""
        if self.detection_coordinator and self.detection_coordinator.detection_controller:
            self.detection_coordinator.detection_controller.resume_detection()
    
    def _stop_detection(self):
        """停止检测"""
        if self.detection_coordinator and self.detection_coordinator.detection_controller:
            self.detection_coordinator.detection_controller.stop_detection()
    
    def _update_progress(self, progress_info: dict):
        """更新进度显示"""
        progress_percent = progress_info.get("progress_percent", 0)
        completed = progress_info.get("completed_holes", 0)
        total = progress_info.get("total_holes", 0)
        
        self.progress_label.setText(f"进度: {progress_percent:.1f}% ({completed}/{total})")
    
    def _update_statistics(self, stats: dict):
        """更新统计信息显示"""
        status_counts = stats.get("status_counts", {})
        total_holes = stats.get("total_holes", 0)
        
        stats_text = f"统计: 总计{total_holes}, 合格{status_counts.get('qualified', 0)}, 异常{status_counts.get('defective', 0)}"
        self.stats_label.setText(stats_text)
    
    def _create_sample_holes(self) -> list:
        """创建示例孔位数据"""
        holes = []
        
        # 创建20个示例孔位
        for i in range(20):
            hole = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=float(i * 10),
                center_y=float(i * 5),
                radius=2.5,
                status=HoleStatus.PENDING,
                row=i // 5,
                column=i % 5
            )
            holes.append(hole)
        
        return holes
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 清理控制器资源
            if self.detection_coordinator:
                self.detection_coordinator.cleanup()
            
            self.logger.info("主窗口关闭，资源清理完成")
            
        except Exception as e:
            self.logger.error(f"关闭窗口时清理资源失败: {e}")
        
        super().closeEvent(event)


def main():
    """主函数示例"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建应用程序核心
    try:
        from ..core.application import get_application
        app_core = get_application()
        
        # 初始化应用程序核心
        if app_core.initialize():
            # 创建主窗口
            window = ExampleMainWindow(app_core)
            window.show()
            
            # 运行应用程序
            sys.exit(app.exec())
        else:
            print("应用程序核心初始化失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()