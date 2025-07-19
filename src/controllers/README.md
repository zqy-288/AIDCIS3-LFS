# 控制器系统文档

本目录包含用于管理侧边栏UI和检测流程的控制器系统。

## 架构概述

控制器系统采用协调器模式，通过事件总线实现松耦合通信：

```
MainDetectionCoordinator (主协调器)
├── SidebarController (侧边栏控制器)
├── DetectionController (检测控制器)
└── EventBus (事件总线)
```

## 核心组件

### 1. SidebarController (侧边栏控制器)

负责管理侧边栏的各个面板：

**功能特性：**
- 文件信息显示和管理
- 检测统计信息实时更新
- 孔位详情显示
- 状态过滤器管理

**主要信号：**
- `hole_info_requested(str)` - 请求孔位信息
- `status_filter_changed(str)` - 状态过滤器变更
- `file_info_updated(dict)` - 文件信息更新
- `statistics_updated(dict)` - 统计信息更新

**主要方法：**
- `update_hole_info(hole_data)` - 更新孔位信息
- `update_statistics(force_update=False)` - 更新统计信息
- `set_status_filter(filter_type)` - 设置状态过滤器

### 2. DetectionController (检测控制器)

负责管理整个检测流程：

**功能特性：**
- 检测状态管理 (空闲/运行/暂停/完成/错误)
- 检测进度跟踪和报告
- 时间统计和预估
- 检测结果管理

**主要信号：**
- `detection_started(dict)` - 检测开始
- `detection_paused(dict)` - 检测暂停
- `detection_resumed(dict)` - 检测恢复
- `detection_completed(dict)` - 检测完成
- `detection_progress(dict)` - 检测进度
- `detection_error(dict)` - 检测错误

**主要方法：**
- `start_detection(holes, config)` - 开始检测
- `pause_detection()` - 暂停检测
- `resume_detection()` - 恢复检测
- `stop_detection()` - 停止检测

### 3. MainDetectionCoordinator (主协调器)

协调各个控制器之间的交互：

**功能特性：**
- 子控制器生命周期管理
- 跨控制器事件协调
- 业务逻辑流程编排
- 全局状态管理

**主要信号：**
- `coordination_started()` - 协调开始
- `coordination_error(str, str)` - 协调错误

**主要方法：**
- `start_coordination(config)` - 启动协调器
- `stop_coordination()` - 停止协调器
- `execute_coordinated_detection(holes, config)` - 执行协调检测

## 使用方法

### 1. 基本初始化

```python
from src.controllers import MainDetectionCoordinator
from src.core.application import EventBus, DependencyContainer

# 创建协调器
coordinator = MainDetectionCoordinator(event_bus, container)

# 启动协调器
coordinator.start_coordination({
    "detection": {
        "interval": 100,
        "hole_detection_time": 50,
        "success_rate": 0.9
    }
})
```

### 2. 执行检测

```python
from src.core_business.models.hole_data import HoleData, HoleStatus

# 创建孔位数据
holes = [
    HoleData("H001", 10.0, 20.0, 2.5, HoleStatus.PENDING),
    HoleData("H002", 15.0, 25.0, 2.5, HoleStatus.PENDING),
    # ... 更多孔位
]

# 执行协调检测
coordinator.execute_coordinated_detection(holes, {
    "interval": 100,
    "success_rate": 0.85
})
```

### 3. 监听事件

```python
# 连接检测控制器信号
detection_controller = coordinator.detection_controller
detection_controller.detection_started.connect(on_detection_started)
detection_controller.detection_progress.connect(on_detection_progress)
detection_controller.detection_completed.connect(on_detection_completed)

# 连接侧边栏控制器信号
sidebar_controller = coordinator.sidebar_controller
sidebar_controller.statistics_updated.connect(on_statistics_updated)
sidebar_controller.status_filter_changed.connect(on_filter_changed)
```

### 4. 手动控制

```python
# 暂停检测
coordinator.detection_controller.pause_detection()

# 恢复检测
coordinator.detection_controller.resume_detection()

# 停止检测
coordinator.detection_controller.stop_detection()

# 设置过滤器
coordinator.sidebar_controller.set_status_filter("pending")
```

## 事件系统

控制器系统使用事件总线进行通信：

### 发布的事件

**侧边栏控制器：**
- `STATUS_FILTER_CHANGED` - 状态过滤器变更
- `HOLE_INFO_REQUESTED` - 孔位信息请求

**检测控制器：**
- `DETECTION_STARTED` - 检测开始
- `DETECTION_PAUSED` - 检测暂停
- `DETECTION_RESUMED` - 检测恢复
- `DETECTION_COMPLETED` - 检测完成
- `DETECTION_PROGRESS` - 检测进度
- `DETECTION_ERROR` - 检测错误
- `HOLE_DETECTION_STARTED` - 孔位检测开始
- `HOLE_DETECTION_COMPLETED` - 孔位检测完成

**主协调器：**
- `COORDINATION_STARTED` - 协调开始
- `COORDINATION_STOPPED` - 协调停止
- `COORDINATED_DETECTION_COMPLETED` - 协调检测完成

### 订阅的事件

**侧边栏控制器：**
- `HOLE_SELECTED` - 孔位选择
- `DETECTION_COMPLETED` - 检测完成
- `FILE_LOADED` - 文件加载
- `DETECTION_STATUS_CHANGED` - 检测状态变更

**检测控制器：**
- `DETECTION_REQUEST` - 检测请求
- `DETECTION_CONTROL` - 检测控制
- `HOLE_DETECTION_COMPLETED` - 孔位检测完成

**主协调器：**
- `APPLICATION_SHUTDOWN` - 应用程序关闭
- `FILE_LOADED` - 文件加载
- `BATCH_CHANGED` - 批次变更
- `USER_ACTION` - 用户操作

## 配置参数

### 检测配置

```python
detection_config = {
    "interval": 100,           # 检测间隔(ms)
    "hole_detection_time": 50, # 单孔检测时间(ms)
    "success_rate": 0.9,       # 成功率
    "timeout": 30000,          # 超时时间(ms)
    "retry_count": 3           # 重试次数
}
```

### 协调器配置

```python
coordination_config = {
    "detection": detection_config,
    "sidebar": {
        "update_interval": 2000,  # 统计更新间隔(ms)
        "auto_filter": True       # 自动过滤
    }
}
```

## 注意事项

1. **线程安全**：所有控制器都在主线程中运行，使用Qt的信号槽机制确保线程安全。

2. **资源管理**：使用完毕后必须调用`cleanup()`方法清理资源。

3. **错误处理**：所有方法都包含完整的错误处理和日志记录。

4. **事件顺序**：某些事件有依赖关系，确保按正确顺序处理。

5. **内存管理**：使用弱引用和定时清理避免内存泄漏。

## 完整示例

参考 `usage_example.py` 文件查看完整的使用示例。

## 依赖关系

- `PySide6` - Qt框架
- `src.core.application` - 应用程序核心
- `src.core.dependency_injection` - 依赖注入
- `src.core_business.models` - 业务模型
- `src.models` - 数据模型