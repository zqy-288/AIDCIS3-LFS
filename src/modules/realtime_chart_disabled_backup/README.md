# 实时图表模块重构

## 模块结构

```
realtime_chart/
├── README.md           # 本文档
├── __init__.py        # 模块导出
├── main.py            # 主类 RealtimeChart
├── components/        # 核心组件
│   ├── __init__.py
│   ├── chart_widget.py     # 纯图表渲染组件
│   ├── data_manager.py     # 数据管理组件
│   ├── csv_processor.py    # CSV处理组件
│   ├── anomaly_detector.py # 异常检测组件
│   ├── endoscope_manager.py # 内窥镜管理组件
│   └── process_controller.py # 进程控制组件
├── ui/                # UI相关组件
│   ├── __init__.py
│   ├── status_panel.py     # 状态面板
│   ├── control_panel.py    # 控制面板
│   └── anomaly_panel.py    # 异常显示面板
└── utils/             # 工具函数
    ├── __init__.py
    ├── font_config.py      # 字体配置
    └── constants.py        # 常量定义
```

## 设计原则

1. **单一职责原则**: 每个组件只负责一个功能
2. **依赖注入**: 组件之间通过接口通信
3. **事件驱动**: 使用信号/槽机制解耦组件
4. **可测试性**: 每个组件都可以独立测试
5. **向后兼容**: 保持原有API接口

## 组件职责

### ChartWidget
- 纯matplotlib图表渲染
- 处理缩放、平移交互
- 绘制数据点和误差线

### DataManager
- 管理深度和直径数据缓冲
- 计算统计信息
- 提供数据访问接口

### CSVProcessor
- CSV文件读取和解析
- 实时监控CSV文件变化
- 数据格式转换

### AnomalyDetector
- 检测异常数据点
- 管理异常历史记录
- 计算异常统计

### EndoscopeManager
- 管理内窥镜图像
- 根据进度切换图像
- 图像缓存和预加载

### ProcessController
- 启动/停止外部进程
- 监控进程状态
- 处理进程输出

## 使用方式

重构后的使用方式与原有相同：

```python
from src.modules.realtime_chart import RealtimeChart

chart = RealtimeChart(parent)
chart.show()
```

## 测试策略

使用Playwright进行端到端测试，覆盖：
- 图表交互（缩放、平移）
- 数据实时更新
- CSV文件监控
- 异常检测功能
- 内窥镜图像切换
- 进程控制功能