# 实时图表模块迁移指南

## 概述

本指南帮助开发者从旧版单文件 `realtime_chart.py` 迁移到新的模块化结构。

## 快速开始

### 1. 导入变更

旧代码：
```python
from modules.realtime_chart import RealTimeChart
```

新代码（向后兼容）：
```python
from modules.realtime_chart import RealTimeChart  # 仍然有效
# 或使用新名称
from modules.realtime_chart import RealtimeChart
```

### 2. 基本使用（无需修改）

```python
# 创建实例
chart = RealTimeChart()  # 或 RealtimeChart()

# 设置标准直径
chart.set_standard_diameter(17.6, 0.2)

# 设置CSV文件
chart.set_csv_file('data.csv')

# 开始/停止监测
chart.start_monitoring()
chart.stop_monitoring()

# 清除数据
chart.clear_data()

# 导出数据
chart.export_data()
```

## 高级使用

### 访问独立组件

新架构允许直接访问各个组件：

```python
# 创建图表实例
chart = RealtimeChart()

# 访问数据管理器
data_manager = chart.data_manager
data_manager.add_data_point(10, 17.6)
data_manager.add_data_batch(depths, diameters)
stats = data_manager.get_statistics()

# 访问异常检测器
detector = chart.anomaly_detector
detector.set_detection_method('statistical')
detector.set_statistical_parameters(window_size=20, sigma_multiplier=3.0)
anomalies = detector.detect_anomalies(depths, diameters)

# 访问CSV处理器
csv_proc = chart.csv_processor
csv_proc.set_csv_file('data.csv')
csv_proc.archive_current_file()
archive_list = csv_proc.get_archive_list()

# 访问图表组件
chart_widget = chart.chart_widget
chart_widget.export_chart('output.png')
chart_widget.reset_zoom()

# 访问内窥镜管理器
endoscope = chart.endoscope_manager
endoscope.set_current_position('A1')
endoscope.set_current_probe(2)
endoscope.start_auto_switch(interval=1000)

# 访问进程控制器
process = chart.process_controller
process.start_process('python script.py')
process.stop_process()
status = process.get_status()
```

### 使用独立组件

如果只需要特定功能，可以单独导入组件：

```python
from modules.realtime_chart.components import DataManager, AnomalyDetector

# 独立使用数据管理器
data_mgr = DataManager()
data_mgr.add_data_batch([1, 2, 3], [17.5, 17.6, 17.7])

# 独立使用异常检测器
detector = AnomalyDetector()
detector.set_tolerance_parameters(17.6, 0.2)
anomalies = detector.detect_anomalies(depths, diameters)
```

## 新功能和改进

### 1. 增强的数据管理

```python
# 获取缓冲区信息
buffer_info = chart.data_manager.get_buffer_info()
print(f"缓冲区大小: {buffer_info['buffer_size']}")
print(f"丢弃的数据点: {buffer_info['discarded_points']}")

# 获取特定范围的数据
depths, diameters = chart.data_manager.get_data_range(
    start_depth=100, 
    end_depth=200
)

# 查找最近的数据点
result = chart.data_manager.find_nearest_point(target_depth=150)
if result:
    index, depth, diameter = result
```

### 2. 多种异常检测方法

```python
# 公差检测（默认）
chart.anomaly_detector.set_detection_method('tolerance')
chart.anomaly_detector.set_tolerance_parameters(17.6, 0.2)

# 统计检测
chart.anomaly_detector.set_detection_method('statistical')
chart.anomaly_detector.set_statistical_parameters(
    window_size=20, 
    sigma_multiplier=3.0
)

# 梯度检测
chart.anomaly_detector.set_detection_method('gradient')
chart.anomaly_detector.set_gradient_threshold(0.5)

# 获取异常统计
stats = chart.anomaly_detector.get_anomaly_statistics()
```

### 3. CSV高级功能

```python
# 文件归档
archive_path = chart.csv_processor.archive_current_file()

# 清理旧归档
chart.csv_processor.clean_old_archives(days=30)

# 获取CSV信息
info = chart.csv_processor.get_csv_info()
print(f"文件大小: {info['size']}")
print(f"行数: {info['rows']}")
```

### 4. 进程管理

```python
# 启动进程并捕获输出
chart.process_controller.set_output_callback(
    lambda line: print(f"输出: {line}")
)
chart.process_controller.start_process('python script.py')

# 发送输入到进程
chart.process_controller.send_input('test command')

# 获取进程列表
processes = chart.process_controller.get_process_list('python')
```

## 信号和事件

新架构使用Qt信号进行组件通信：

```python
# 监听数据更新
chart.data_updated.connect(on_data_updated)

# 监听异常检测
chart.anomaly_detected.connect(on_anomaly_detected)

# 监听进程状态变化
chart.process_status_changed.connect(on_process_status_changed)

def on_data_updated(depths, diameters):
    print(f"数据更新: {len(depths)} 个点")

def on_anomaly_detected(index, depth, diameter):
    print(f"检测到异常: 索引={index}, 深度={depth}, 直径={diameter}")

def on_process_status_changed(status):
    print(f"进程状态: {status}")
```

## 配置和常量

所有配置现在集中在常量文件中：

```python
from modules.realtime_chart.utils.constants import (
    CHART_UPDATE_INTERVAL,
    MAX_DATA_POINTS,
    ANOMALY_THRESHOLD,
    CSV_CHECK_INTERVAL
)

# 修改配置
chart.set_update_interval(200)  # 毫秒
chart.set_max_display_points(500)
```

## 常见问题

### Q: 旧代码能否直接运行？
A: 是的，通过向后兼容层，旧代码无需修改即可运行。

### Q: 如何只使用部分功能？
A: 可以单独导入需要的组件，无需加载整个模块。

### Q: 性能有提升吗？
A: 是的，模块化设计减少了不必要的依赖加载，提升了启动速度和运行效率。

### Q: 如何扩展功能？
A: 可以继承任何组件类并重写方法，或通过信号/槽机制添加新功能。

## 示例代码

### 完整示例

```python
from modules.realtime_chart import RealtimeChart

# 创建实例
chart = RealtimeChart()

# 配置
chart.set_standard_diameter(17.6, 0.2)
chart.set_detection_method('statistical')
chart.set_csv_file('measurement_data.csv')

# 监听事件
chart.data_updated.connect(lambda d, dia: print(f"更新: {len(d)} 点"))
chart.anomaly_detected.connect(
    lambda i, d, dia: print(f"异常: 深度={d}, 直径={dia}")
)

# 开始监测
chart.start_monitoring()

# 手动添加数据
chart.data_manager.add_data_point(100, 17.65)

# 导出结果
chart.export_data()
```

### 自定义异常检测

```python
from modules.realtime_chart.components import AnomalyDetector

class CustomDetector(AnomalyDetector):
    def detect_anomalies(self, depths, diameters):
        # 自定义检测逻辑
        anomalies = []
        for i, d in enumerate(diameters):
            if self.custom_check(d):
                anomalies.append(i)
        return anomalies
    
    def custom_check(self, diameter):
        # 实现自定义检测算法
        return abs(diameter - 17.6) > 0.3

# 使用自定义检测器
chart = RealtimeChart()
chart.anomaly_detector = CustomDetector()
```

## 总结

新的模块化架构提供了更大的灵活性和可扩展性，同时保持了向后兼容。通过独立的组件和清晰的接口，开发者可以更容易地定制和扩展功能。