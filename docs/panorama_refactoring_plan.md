# 全景图组件重构方案

## 一、现状分析

`CompletePanoramaWidget` 当前承担了过多职责：
1. UI渲染和布局管理
2. 数据模型管理（孔位集合）
3. 几何计算（中心点、半径）
4. 状态更新管理（批量更新）
5. 扇区高亮交互
6. 蛇形路径渲染
7. 主题管理
8. 事件处理

## 二、拆分架构设计

### 1. 核心组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                     PanoramaWidget (UI层)                    │
│  职责：纯UI展示，不包含业务逻辑                               │
└────────────────────┬────────────────────────────────────────┘
                     │ 依赖注入
┌────────────────────▼────────────────────────────────────────┐
│                 PanoramaViewController                       │
│  职责：协调各组件，处理用户交互                                │
└─────┬──────────────┬──────────────┬─────────────┬──────────┘
      │              │              │             │
┌─────▼────┐ ┌──────▼─────┐ ┌─────▼────┐ ┌─────▼──────┐
│ Panorama │ │  Geometry  │ │  Status  │ │ SnakePath │
│DataModel │ │ Calculator │ │ Manager  │ │ Renderer  │
└──────────┘ └────────────┘ └──────────┘ └───────────┘
```

### 2. 组件职责划分

#### 2.1 PanoramaDataModel（数据模型）
- 管理孔位数据
- 提供数据查询接口
- 发布数据变更事件

#### 2.2 PanoramaGeometryCalculator（几何计算）
- 计算中心点
- 计算半径
- 计算孔位布局
- 自适应缩放算法

#### 2.3 PanoramaStatusManager（状态管理）
- 批量更新优化
- 状态变更追踪
- 更新队列管理

#### 2.4 PanoramaRenderer（渲染器）
- 孔位项渲染
- 扇区分隔线渲染
- 主题样式应用

#### 2.5 SectorInteractionHandler（扇区交互）
- 鼠标事件处理
- 扇区高亮管理
- 点击事件分发

#### 2.6 SnakePathRenderer（蛇形路径）
- 路径计算
- 路径渲染
- 路径样式管理

#### 2.7 PanoramaViewController（视图控制器）
- 组件生命周期管理
- 组件间协调
- 对外接口暴露

#### 2.8 PanoramaWidget（UI组件）
- 纯UI布局
- 视图容器管理
- 基础事件转发

## 三、接口设计

### 3.1 数据模型接口

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal

class IPanoramaDataModel(ABC):
    """全景图数据模型接口"""
    
    @abstractmethod
    def get_holes(self) -> Dict[str, 'HoleData']:
        """获取所有孔位数据"""
        pass
    
    @abstractmethod
    def get_hole(self, hole_id: str) -> Optional['HoleData']:
        """获取指定孔位"""
        pass
    
    @abstractmethod
    def update_hole_status(self, hole_id: str, status: 'HoleStatus'):
        """更新孔位状态"""
        pass

class PanoramaDataModel(QObject, IPanoramaDataModel):
    """全景图数据模型实现"""
    
    # 信号
    hole_status_changed = Signal(str, object)  # hole_id, status
    data_loaded = Signal()
    
    def __init__(self):
        super().__init__()
        self._holes: Dict[str, HoleData] = {}
```

### 3.2 几何计算接口

```python
class IPanoramaGeometryCalculator(ABC):
    """几何计算接口"""
    
    @abstractmethod
    def calculate_center(self, holes: Dict[str, 'HoleData']) -> QPointF:
        """计算中心点"""
        pass
    
    @abstractmethod
    def calculate_radius(self, holes: Dict[str, 'HoleData'], center: QPointF) -> float:
        """计算半径"""
        pass
    
    @abstractmethod
    def calculate_hole_display_size(self, hole_count: int, radius: float) -> float:
        """计算孔位显示大小"""
        pass
```

### 3.3 状态管理接口

```python
class IPanoramaStatusManager(ABC):
    """状态管理接口"""
    
    @abstractmethod
    def queue_status_update(self, hole_id: str, status: 'HoleStatus'):
        """队列化状态更新"""
        pass
    
    @abstractmethod
    def flush_updates(self):
        """刷新所有待处理更新"""
        pass
```

## 四、事件总线设计

使用事件总线解耦组件间通信：

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any

class PanoramaEvent(Enum):
    """全景图事件类型"""
    DATA_LOADED = "data_loaded"
    HOLE_STATUS_CHANGED = "hole_status_changed"
    SECTOR_CLICKED = "sector_clicked"
    GEOMETRY_CHANGED = "geometry_changed"
    RENDER_REQUESTED = "render_requested"

@dataclass
class EventData:
    """事件数据"""
    event_type: PanoramaEvent
    data: Any

class PanoramaEventBus(QObject):
    """全景图事件总线"""
    
    event_published = Signal(EventData)
    
    def publish(self, event_type: PanoramaEvent, data: Any = None):
        """发布事件"""
        self.event_published.emit(EventData(event_type, data))
    
    def subscribe(self, callback):
        """订阅事件"""
        self.event_published.connect(callback)
```

## 五、重构实施步骤

### 第一阶段：创建新组件结构
1. 创建接口定义文件
2. 实现数据模型组件
3. 实现几何计算组件
4. 实现状态管理组件

### 第二阶段：迁移核心功能
1. 迁移数据管理逻辑
2. 迁移几何计算逻辑
3. 迁移状态更新逻辑
4. 迁移渲染逻辑

### 第三阶段：实现控制器
1. 创建视图控制器
2. 实现组件协调逻辑
3. 设置依赖注入

### 第四阶段：重构UI层
1. 简化PanoramaWidget为纯UI组件
2. 移除业务逻辑
3. 实现事件转发

### 第五阶段：集成测试
1. 单元测试各组件
2. 集成测试
3. 性能测试
4. 回归测试

## 六、依赖注入配置

```python
class PanoramaDIContainer:
    """全景图依赖注入容器"""
    
    def __init__(self):
        self.event_bus = PanoramaEventBus()
        self.data_model = PanoramaDataModel()
        self.geometry_calculator = PanoramaGeometryCalculator()
        self.status_manager = PanoramaStatusManager(self.data_model)
        self.renderer = PanoramaRenderer()
        
    def create_panorama_widget(self, parent=None) -> PanoramaWidget:
        """创建全景图组件"""
        controller = PanoramaViewController(
            data_model=self.data_model,
            geometry_calculator=self.geometry_calculator,
            status_manager=self.status_manager,
            renderer=self.renderer,
            event_bus=self.event_bus
        )
        
        widget = PanoramaWidget(controller, parent)
        return widget
```

## 七、优势总结

1. **高内聚**：每个组件只负责单一职责
2. **低耦合**：通过接口和事件总线通信
3. **可测试**：每个组件可独立测试
4. **可扩展**：易于添加新功能
5. **可维护**：清晰的职责划分