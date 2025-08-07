# P2实时监控模块

## 概述
此模块是将重构前的实时监控代码按照高内聚、低耦合原则重新组织的结果。**所有功能均来自重构前的现有代码，未添加任何新功能。**

## 模块结构

### 高内聚设计
每个模块内部的功能紧密相关，职责明确：

- **components/**: UI组件模块
  - `realtime_chart.py` - 实时图表组件 (114,956字节)
  - `endoscope_view.py` - 内窥镜视图组件 (7,287字节)

- **workers/**: 工作器模块  
  - `automation_worker.py` - 自动化工作器 (13,066字节)

- **monitors/**: 监控器模块
  - `data_monitor.py` - 数据监控器 (9,206字节)
  - `memory_monitor.py` - 内存监控器 (14,642字节)

- **utils/**: 工具模块
  - `remote_launcher.py` - 远程启动器 (7,709字节)

### 低耦合设计
- 模块间通过import语句实现依赖管理
- 避免了紧密耦合的直接调用
- 每个模块可以独立修改和维护

## 使用方法

```python
# 导入整个P2模块
from pages.realtime_monitoring_p2 import *

# 或者按需导入具体组件
from pages.realtime_monitoring_p2.components.realtime_chart import RealtimeChart
from pages.realtime_monitoring_p2.workers.automation_worker import AutomationWorker
from pages.realtime_monitoring_p2.monitors.data_monitor import DataMonitor
```

## 迁移说明

这次迁移：
- ✅ **直接复制**了重构前的所有代码
- ✅ **重新组织**了文件结构以符合高内聚低耦合原则
- ✅ **修复了**模块间的导入路径
- ✅ **保持了**所有原有功能不变
- ✅ **未添加**任何新功能或重写现有逻辑

## 总计
- **文件数量**: 11个文件
- **代码总量**: 约167KB
- **来源**: 100%来自重构前现有代码
- **架构**: 高内聚、低耦合模块化设计