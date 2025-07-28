# 实时图表包集成指南

## 概述

本指南说明如何将重构后的实时图表包集成到主应用程序中。

## 包结构

```
src/modules/realtime_chart_package/
├── __init__.py              # 包入口，导出所有公共接口
├── setup.py                 # 包安装配置
├── README.md               # 包文档
├── realtime_chart.py       # 主集成类
├── components/             # 功能组件目录
│   ├── __init__.py
│   ├── chart_widget.py     # 图表渲染组件
│   ├── data_manager.py     # 数据管理组件
│   ├── csv_processor.py    # CSV处理组件
│   ├── anomaly_detector.py # 异常检测组件
│   ├── endoscope_manager.py # 内窥镜管理组件
│   └── process_controller.py # 进程控制组件
└── utils/                  # 工具模块目录
    ├── __init__.py
    ├── constants.py        # 常量定义
    └── font_config.py      # 字体配置
```

## 集成步骤

### 1. 基本导入

在主应用程序中导入实时图表包：

```python
# 方式1：从包导入主类
from src.modules.realtime_chart_package import RealtimeChart

# 方式2：导入整个包
import src.modules.realtime_chart_package as rtc_package
chart = rtc_package.RealtimeChart()

# 方式3：导入特定组件
from src.modules.realtime_chart_package.components import DataManager, ChartWidget
```

### 2. 在主窗口中集成

```python
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from src.modules.realtime_chart_package import RealtimeChart

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建实时图表实例
        self.realtime_chart = RealtimeChart()
        layout.addWidget(self.realtime_chart)
        
        # 初始化配置
        self.realtime_chart.set_standard_diameter(17.6, 0.2)
```

### 3. 在选项卡中集成

```python
from PySide6.QtWidgets import QTabWidget
from src.modules.realtime_chart_package import RealtimeChart

class MainTabs(QTabWidget):
    def __init__(self):
        super().__init__()
        
        # 添加实时图表选项卡
        self.realtime_chart = RealtimeChart()
        self.addTab(self.realtime_chart, "实时监测")
        
        # 添加其他选项卡...
```

### 4. 与现有代码兼容

包保持了向后兼容性：

```python
# 旧代码（仍然有效）
from modules.realtime_chart import RealTimeChart
chart = RealTimeChart()

# 新代码（推荐）
from src.modules.realtime_chart_package import RealtimeChart
chart = RealtimeChart()
```

## 高级集成

### 1. 自定义组件配置

```python
from src.modules.realtime_chart_package import RealtimeChart

class CustomRealtimeChart(RealtimeChart):
    def __init__(self):
        super().__init__()
        
        # 自定义配置
        self.set_update_interval(500)  # 更新间隔500ms
        self.set_max_display_points(1000)  # 最大显示1000个点
        
        # 自定义异常检测
        self.anomaly_detector.set_detection_method('statistical')
        self.anomaly_detector.set_statistical_parameters(
            window_size=30,
            sigma_multiplier=2.5
        )
```

### 2. 信号连接

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.realtime_chart = RealtimeChart()
        
        # 连接信号
        self.realtime_chart.data_updated.connect(self.on_data_updated)
        self.realtime_chart.anomaly_detected.connect(self.on_anomaly_detected)
        
    def on_data_updated(self, depths, diameters):
        # 处理数据更新
        self.statusBar().showMessage(f"数据点: {len(depths)}")
        
    def on_anomaly_detected(self, index, depth, diameter):
        # 处理异常检测
        QMessageBox.warning(
            self,
            "异常检测",
            f"在深度 {depth}mm 处检测到异常直径: {diameter}mm"
        )
```

### 3. 菜单集成

```python
def create_realtime_menu(menubar, realtime_chart):
    """创建实时监测菜单"""
    menu = menubar.addMenu("实时监测")
    
    # 开始/停止监测
    start_action = menu.addAction("开始监测")
    start_action.triggered.connect(realtime_chart.start_monitoring)
    
    stop_action = menu.addAction("停止监测")
    stop_action.triggered.connect(realtime_chart.stop_monitoring)
    
    menu.addSeparator()
    
    # 数据操作
    clear_action = menu.addAction("清除数据")
    clear_action.triggered.connect(realtime_chart.clear_data)
    
    export_action = menu.addAction("导出数据")
    export_action.triggered.connect(realtime_chart.export_data)
    
    return menu
```

### 4. 工具栏集成

```python
def create_realtime_toolbar(toolbar, realtime_chart):
    """创建实时监测工具栏"""
    # 开始按钮
    start_action = toolbar.addAction("▶️ 开始")
    start_action.triggered.connect(realtime_chart.start_monitoring)
    
    # 停止按钮
    stop_action = toolbar.addAction("⏹️ 停止")
    stop_action.triggered.connect(realtime_chart.stop_monitoring)
    
    toolbar.addSeparator()
    
    # 缩放重置
    reset_action = toolbar.addAction("🔍 重置缩放")
    reset_action.triggered.connect(
        realtime_chart.chart_widget.reset_zoom
    )
```

## 配置选项

### 1. 通过配置文件

```python
import json

# 加载配置
with open('config/realtime_chart.json', 'r') as f:
    config = json.load(f)

# 应用配置
chart = RealtimeChart()
chart.set_standard_diameter(
    config['standard_diameter'],
    config['tolerance']
)
chart.set_detection_method(config['detection_method'])
chart.set_update_interval(config['update_interval'])
```

### 2. 通过环境变量

```python
import os

chart = RealtimeChart()

# 从环境变量读取配置
diameter = float(os.getenv('STANDARD_DIAMETER', '17.6'))
tolerance = float(os.getenv('TOLERANCE', '0.2'))
chart.set_standard_diameter(diameter, tolerance)
```

## 最佳实践

### 1. 延迟加载

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.realtime_chart = None
        
    def load_realtime_module(self):
        """按需加载实时图表模块"""
        if self.realtime_chart is None:
            from src.modules.realtime_chart_package import RealtimeChart
            self.realtime_chart = RealtimeChart()
            self.central_layout.addWidget(self.realtime_chart)
```

### 2. 错误处理

```python
try:
    from src.modules.realtime_chart_package import RealtimeChart
    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False
    print("实时图表模块不可用")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        if REALTIME_AVAILABLE:
            self.add_realtime_chart()
        else:
            self.show_module_unavailable_message()
```

### 3. 资源管理

```python
class MainWindow(QMainWindow):
    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        if hasattr(self, 'realtime_chart'):
            # 停止所有活动
            self.realtime_chart.stop_monitoring()
            
            # 停止进程
            if self.realtime_chart.process_controller.is_running():
                self.realtime_chart.process_controller.stop_process()
                
        event.accept()
```

## 故障排除

### 导入错误

如果遇到导入错误：

```python
# 确保路径正确
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 然后导入
from src.modules.realtime_chart_package import RealtimeChart
```

### 依赖问题

确保所有依赖都已安装：

```bash
pip install PySide6 matplotlib numpy pandas psutil
```

### 性能优化

对于大数据集：

```python
# 限制显示点数
chart.set_max_display_points(500)

# 降低更新频率
chart.set_update_interval(500)  # 500ms

# 使用数据采样
chart.data_manager.enable_sampling(sample_rate=10)
```

## 示例项目

完整的集成示例可以参考 `example_main_with_package.py` 文件。