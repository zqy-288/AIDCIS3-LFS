# 实时监控P2模块 - 按照高内聚低耦合原则重新组织的重构前代码

# 导入重构前的现有功能模块
from .components.realtime_chart import RealtimeChart
from .components.endoscope_view import EndoscopeView
from .components.camera_preview import CameraPreviewWidget
from .components.video_display_widget import VideoDisplayWidget
from .workers.automation_worker import AutomationWorker
from .monitors.data_monitor import DataFolderMonitor
from .monitors.memory_monitor import MemoryMonitor

# 主界面类别名（基于重构前的主要组件）
RealtimeMonitoringPage = RealtimeChart
