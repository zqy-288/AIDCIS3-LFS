# 实时图表包 (Realtime Chart Package)

模块化的实时图表组件包，用于管孔直径实时监测和数据可视化。

## 特性

- 📊 **实时图表渲染** - 基于Matplotlib的高性能图表
- 📈 **数据管理** - 智能数据缓冲和统计分析
- 🔍 **异常检测** - 多种异常检测算法
- 📁 **CSV处理** - 自动文件监控和数据导入
- 🔬 **内窥镜管理** - 多探头图像管理
- ⚙️ **进程控制** - 外部进程管理和监控

## 安装

### 从源码安装

```bash
cd src/modules/realtime_chart_package
pip install -e .
```

### 开发模式安装（包含测试依赖）

```bash
pip install -e .[dev]
```

## 快速开始

```python
from realtime_chart_package import RealtimeChart

# 创建实时图表
chart = RealtimeChart()

# 设置标准直径和公差
chart.set_standard_diameter(17.6, 0.2)

# 设置CSV数据源
chart.set_csv_file('measurement_data.csv')

# 开始监测
chart.start_monitoring()
```

## 组件使用

### 独立使用组件

```python
from realtime_chart_package.components import DataManager, AnomalyDetector

# 数据管理
data_manager = DataManager()
data_manager.add_data_batch([0, 10, 20], [17.5, 17.6, 17.7])
stats = data_manager.get_statistics()

# 异常检测
detector = AnomalyDetector()
detector.set_tolerance_parameters(17.6, 0.2)
anomalies = detector.detect_anomalies(depths, diameters)
```

### 访问子组件

```python
chart = RealtimeChart()

# 访问各个组件
chart.data_manager      # 数据管理器
chart.chart_widget      # 图表组件
chart.csv_processor     # CSV处理器
chart.anomaly_detector  # 异常检测器
chart.endoscope_manager # 内窥镜管理器
chart.process_controller # 进程控制器
```

## 包结构

```
realtime_chart_package/
├── __init__.py              # 包入口
├── realtime_chart.py        # 主集成类
├── components/              # 功能组件
│   ├── __init__.py
│   ├── chart_widget.py      # 图表渲染
│   ├── data_manager.py      # 数据管理
│   ├── csv_processor.py     # CSV处理
│   ├── anomaly_detector.py  # 异常检测
│   ├── endoscope_manager.py # 内窥镜管理
│   └── process_controller.py # 进程控制
└── utils/                   # 工具模块
    ├── __init__.py
    ├── constants.py         # 常量定义
    └── font_config.py       # 字体配置
```

## API文档

### RealtimeChart 主类

```python
class RealtimeChart(QWidget):
    """实时监测图表主窗口"""
    
    # 主要方法
    def start_monitoring(self)
    def stop_monitoring(self)
    def clear_data(self)
    def export_data(self)
    def set_csv_file(self, file_path: str)
    def set_standard_diameter(self, diameter: float, tolerance: float)
    def set_detection_method(self, method: str)
    
    # 信号
    data_updated = Signal(list, list)
    anomaly_detected = Signal(int, float, float)
    process_status_changed = Signal(str)
```

### 组件API

详细的组件API文档请参考各组件的源代码文档字符串。

## 测试

运行单元测试：

```bash
pytest tests/
```

运行集成测试：

```bash
python test_refactored_components.py
```

运行Playwright E2E测试：

```bash
pytest tests/e2e/
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！